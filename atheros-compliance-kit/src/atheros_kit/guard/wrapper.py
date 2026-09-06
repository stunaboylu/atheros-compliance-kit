"""`GuardedClient` — the isolation layer between an application and an external LLM.

Provider-agnostic on purpose: it wraps a **callable**, not an SDK. Every provider
has a different client object and they all change; `str -> str` does not.

    def call(prompt: str) -> str:                  # or -> (text, prompt_tokens, completion_tokens)
        return openai_client.responses.create(...).output_text

    client = GuardedClient(call=call, policy=GuardPolicy.strict())
    result = client.invoke("Summarise the case for ali@acme.com")

Order of operations, and why:

    documents ──▶ injection scan   (a poisoned chunk is the likeliest attack)
    prompt ─────▶ injection scan   (block BEFORE spending a token)
           └────▶ PII mask         (mask AFTER scanning: the scanner should see
                                    the real text, and masking never introduces
                                    an injection but can hide one)
    budget check                   (before the call — after is a report, not a control)
    provider call  ──▶ retry ──▶ secondary ──▶ static fallback
    response ───▶ output gate      (overclaim/refusal/empty)
           └────▶ unmask           (last: the gate should read placeholders, not
                                    restored identities, so a BLOCK never has to
                                    handle real PII)
    ledger append                  (always, including on the failure paths)
"""
from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from ..core.errors import BudgetExceeded, GuardBlocked
from ..core.findings import Action, Finding, Severity, worst
from . import fallback as fb
from . import injection
from .ledger import GuardLedger, InvocationRecord, TokenUsage, estimate_tokens
from .pii import Anonymizer
from .policy import DEFAULT_FALLBACK_TEXT, GuardPolicy


@dataclass
class GuardResult:
    """What the application gets back. `text` is always safe to use or None."""

    text: str | None
    findings: list[Finding] = field(default_factory=list)
    masked_entities: dict[str, int] = field(default_factory=dict)
    degraded: bool = False
    fallback_trigger: str | None = None
    #: primary | retry | secondary | static — what produced `text`.
    answered_by: str = "primary"
    attempts: int = 1
    usage: TokenUsage = field(default_factory=TokenUsage)
    latency_ms: float = 0.0
    session_id: str = "-"
    blocked: bool = False

    @property
    def ok(self) -> bool:
        return self.text is not None and not self.blocked

    @property
    def worst_severity(self) -> Severity | None:
        return worst(self.findings)

    def __str__(self) -> str:
        return self.text or ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blocked": self.blocked,
            "degraded": self.degraded,
            "fallback_trigger": self.fallback_trigger,
            "answered_by": self.answered_by,
            "attempts": self.attempts,
            "masked_entities": self.masked_entities,
            "findings": [f.to_dict() for f in self.findings],
            "tokens": self.usage.total,
            "latency_ms": round(self.latency_ms, 2),
            "session_id": self.session_id,
        }


class GuardedClient:
    def __init__(
        self,
        call: Callable[[str], Any],
        *,
        policy: GuardPolicy | None = None,
        model_name: str = "unspecified",
        session_id: str | None = None,
        ledger: GuardLedger | None = None,
    ):
        self.call = call
        self.policy = policy or GuardPolicy.standard()
        self.model_name = model_name
        self.ledger = ledger or GuardLedger(session_id=session_id)
        self.anonymizer = Anonymizer(
            custom_entities=self.policy.custom_entities,
            categories=self.policy.categories,
            reversible=self.policy.reversible,
        )

    @property
    def session_id(self) -> str:
        return self.ledger.session_id

    # ── the one public entry point ───────────────────────────────────────────
    def invoke(self, prompt: str, *, documents: dict[str, str] | None = None) -> GuardResult:
        started = time.perf_counter()
        findings: list[Finding] = []
        masked_counts: dict[str, int] = {}
        signatures: list[str] = []

        # 1. Retrieved documents first — the likeliest carrier of an injection.
        if documents and self.policy.scan_documents and self.policy.scan_injection:
            doc_scan = injection.scan_documents(documents)
            findings.extend(doc_scan.findings)
            signatures.extend(f.check for f in doc_scan.findings)

        # 2. The prompt, scanned as written.
        if self.policy.scan_injection:
            scan = injection.scan(prompt, source="user", scan_encoded=self.policy.scan_encoded)
            findings.extend(scan.findings)
            signatures.extend(f.check for f in scan.findings)

        # 3. Mask. After scanning, so the scanner reads the real text.
        outbound = prompt
        if self.policy.mask_pii:
            mask = self.anonymizer.mask(prompt)
            outbound = mask.text
            masked_counts = mask.entities
            if mask.secrets_found:
                sev = Severity.CRITICAL if self.policy.block_on_secret else Severity.HIGH
                act = Action.BLOCK if self.policy.block_on_secret else Action.FLAG
                findings.append(Finding(
                    "secret_in_prompt", sev,
                    f"credential-shaped values present in the prompt: {', '.join(mask.secrets_found)}",
                    "guard", act, article="ISO 42001 §8.3",
                    evidence={"categories": mask.secrets_found},
                    remediation="Remove the credential at the source and rotate it; masking is not rotation.",
                    params={"categories": ", ".join(mask.secrets_found)},
                ))
            elif masked_counts:
                findings.append(Finding(
                    "pii_masked", Severity.INFO,
                    f"personal-data categories masked before egress: "
                    f"{', '.join(sorted(masked_counts))}",
                    "guard", Action.PASS, article="GDPR Art. 5(1)(c)",
                    evidence={"entities": masked_counts},
                    params={"categories": ", ".join(sorted(masked_counts))},
                ))

        input_action = self._decide(findings)

        # 4. Blocked input: no token is spent, and the record still lands.
        #
        # `pass_through` is the exception and the reason observe-mode exists: the
        # detection is recorded, the call proceeds untouched. Diverting here would
        # make the "measure, never interfere" policy interfere — the one thing it
        # promises not to do, and the reason a team is willing to switch it on in
        # production before they trust the blocking policies.
        if input_action is Action.BLOCK and self.policy.on_block != "pass_through":
            return self._blocked(prompt, findings, masked_counts, signatures, started)

        # 5. Budget, before the call.
        projected = estimate_tokens(outbound)
        try:
            breach = self.ledger.enforce_budget(self.policy, projected)
        except BudgetExceeded:
            self._record(findings, masked_counts, signatures, TokenUsage(), True,
                         (time.perf_counter() - started) * 1000, "pass", "block",
                         True, fb.Trigger.BUDGET_EXCEEDED.value, error="budget exceeded",
                         answered_by="static", attempts=0)
            raise
        if breach and self.policy.on_budget_exceeded == "fallback":
            return self._fallback_result(
                fb.Trigger.BUDGET_EXCEEDED, findings, masked_counts, signatures, started,
                detail=f"{breach} exhausted",
            )
        if breach:
            findings.append(Finding(
                "budget_warning", Severity.MEDIUM, f"{breach} exceeded; call proceeded (policy=warn)",
                "guard", Action.FLAG, evidence={"budget": breach},
            ))

        # 6. The provider call, with retry then secondary.
        text, usage, estimated, trigger, attempts, source = self._call_with_retry(outbound)

        # 7. Output gate — on the still-masked text.
        if text is not None and self.policy.scan_output:
            out_findings = fb.check_output(
                text,
                detect_refusal=self.policy.detect_refusal,
                detect_overclaim=self.policy.detect_overclaim,
            )
            findings.extend(out_findings)
            signatures.extend(f.check for f in out_findings)
            if any(f.action is Action.BLOCK for f in out_findings):
                trigger = fb.Trigger.OUTPUT_BLOCKED
                text = None
            elif text is not None and fb.is_refusal(text) and self.policy.static_fallback is not None:
                trigger = fb.Trigger.REFUSAL
                text = None

        degraded = trigger is not None
        if text is None:
            text = self.policy.static_fallback or DEFAULT_FALLBACK_TEXT
            source = "static"
        elif source == "primary" and degraded:
            # The provider answered, but the OUTPUT gate rejected it and a
            # fallback took its place — recording that as "primary" would say a
            # model produced text it did not produce.
            source = "static"

        # 8. Unmask last, so the output gate never handled real identities.
        if self.policy.unmask_response and not degraded:
            leaked = self.anonymizer.leaked_placeholders(text)
            if leaked:
                findings.append(Finding(
                    "placeholder_hallucination", Severity.MEDIUM,
                    f"the response contains {len(leaked)} placeholder(s) this session never issued",
                    "guard", Action.FLAG, evidence={"count": len(leaked)},
                    remediation="Do not resolve invented placeholders; treat the answer as unreliable.",
                    params={"count": len(leaked)},
                ))
            text = self.anonymizer.unmask(text)

        latency = (time.perf_counter() - started) * 1000
        self._record(findings, masked_counts, signatures, usage, estimated, latency,
                     input_action.value, self._decide(findings).value, degraded,
                     trigger.value if trigger else None, answered_by=source, attempts=attempts)

        return GuardResult(
            text=text, findings=findings, masked_entities=masked_counts,
            degraded=degraded, fallback_trigger=trigger.value if trigger else None,
            answered_by=source, attempts=attempts,
            usage=usage, latency_ms=latency, session_id=self.session_id,
        )

    # ── internals ────────────────────────────────────────────────────────────
    def _decide(self, findings: Sequence[Finding]) -> Action:
        if any(f.action is Action.BLOCK for f in findings):
            return Action.BLOCK
        if any(f.action is Action.FLAG for f in findings):
            return Action.FLAG
        return Action.PASS

    def _normalise(self, raw: Any) -> tuple[str, TokenUsage, bool]:
        """Accept `str`, `(text, prompt_tokens, completion_tokens)`, or a dict.

        Providers report usage in mutually incompatible shapes and none of them
        is worth making the caller adapt to; a plain string is always allowed and
        the tokens are then estimated and marked as such.
        """
        if isinstance(raw, tuple) and len(raw) == 3:
            return str(raw[0]), TokenUsage(int(raw[1]), int(raw[2])), False
        if isinstance(raw, dict) and "text" in raw:
            u = raw.get("usage") or {}
            if u:
                return str(raw["text"]), TokenUsage(
                    int(u.get("prompt_tokens", 0)), int(u.get("completion_tokens", 0))
                ), False
            text = str(raw["text"])
            return text, TokenUsage(0, estimate_tokens(text)), True
        text = str(raw)
        return text, TokenUsage(0, estimate_tokens(text)), True

    def _call_with_retry(self, prompt: str):
        attempts, last_error = 0, None
        for attempt in range(self.policy.retries + 1):
            attempts = attempt + 1
            try:
                text, usage, estimated = self._normalise(self.call(prompt))
                if not text.strip():
                    last_error = "empty response"
                    continue
                usage = TokenUsage(usage.prompt_tokens or estimate_tokens(prompt),
                                   usage.completion_tokens)
                trigger = fb.Trigger.PROVIDER_ERROR if attempt > 0 else None
                return text, usage, estimated, trigger, attempts, (
                    "retry" if attempt > 0 else "primary"
                )
            except Exception as exc:  # provider SDKs raise anything at all
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt < self.policy.retries:
                    time.sleep(self.policy.retry_backoff_seconds * (2 ** attempt))

        if self.policy.secondary_call is not None:
            try:
                text, usage, estimated = self._normalise(self.policy.secondary_call(prompt))
                if text.strip():
                    return (text, usage, estimated, fb.Trigger.PROVIDER_ERROR,
                            attempts + 1, "secondary")
            except Exception as exc:
                last_error = f"secondary failed: {type(exc).__name__}: {exc}"

        trigger = fb.Trigger.EMPTY_RESPONSE if last_error == "empty response" else fb.Trigger.PROVIDER_ERROR
        return None, TokenUsage(estimate_tokens(prompt), 0), True, trigger, attempts, "static"

    def _blocked(self, prompt, findings, masked, signatures, started) -> GuardResult:
        latency = (time.perf_counter() - started) * 1000
        self._record(findings, masked, signatures, TokenUsage(estimate_tokens(prompt), 0),
                     True, latency, "block", "block", True, fb.Trigger.INPUT_BLOCKED.value,
                     answered_by="static", attempts=0)
        blockers = [f for f in findings if f.action is Action.BLOCK]
        if self.policy.on_block == "raise":
            raise GuardBlocked(
                f"Guard blocked the request: {'; '.join(f.check for f in blockers)}",
                result=findings,
            )
        text = self.policy.static_fallback or DEFAULT_FALLBACK_TEXT if self.policy.on_block == "fallback" else None
        return GuardResult(
            text=text, findings=findings, masked_entities=masked, degraded=True,
            fallback_trigger=fb.Trigger.INPUT_BLOCKED.value, latency_ms=latency,
            session_id=self.session_id, blocked=True,
        )

    def _fallback_result(self, trigger, findings, masked, signatures, started, detail) -> GuardResult:
        latency = (time.perf_counter() - started) * 1000
        findings.append(Finding(
            f"fallback_{trigger.value}", Severity.MEDIUM, detail, "guard", Action.FLAG,
            remediation="The answer is a fallback, not a model response. Do not treat it as one.",
        ))
        self._record(findings, masked, signatures, TokenUsage(), True, latency,
                     "pass", "flag", True, trigger.value, answered_by="static", attempts=0)
        return GuardResult(
            text=self.policy.static_fallback or DEFAULT_FALLBACK_TEXT,
            findings=findings, masked_entities=masked, degraded=True,
            fallback_trigger=trigger.value, answered_by="static", attempts=0,
            latency_ms=latency, session_id=self.session_id,
        )

    def _record(self, findings, masked, signatures, usage, estimated, latency,
                input_action, output_action, degraded, trigger, error=None,
                answered_by="primary", attempts=1) -> None:
        self.ledger.record(
            InvocationRecord(
                session_id=self.session_id,
                call_index=self.ledger.call_count + 1,
                model=self.model_name,
                usage=usage,
                usage_estimated=estimated,
                latency_ms=latency,
                input_action=input_action,
                output_action=output_action,
                masked_entities=masked,
                signatures=sorted(set(signatures)),
                degraded=degraded,
                fallback_reason=trigger,
                answered_by=answered_by,
                attempts=attempts,
                error=error,
            ),
            log=self.policy.log_to_ledger,
        )

    # ── convenience ──────────────────────────────────────────────────────────
    def summary(self) -> dict[str, Any]:
        return self.ledger.summary()

    def __call__(self, prompt: str, **kw) -> GuardResult:
        return self.invoke(prompt, **kw)

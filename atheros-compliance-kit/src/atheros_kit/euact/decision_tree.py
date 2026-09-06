"""The intake flow that produces a `SystemSpec`.

A parameterised question tree, not a fixed form: each question declares when it
is `relevant`, so a team answers eight questions instead of forty. The tree is
data, so the CLI wizard, the Console wizard and a customer's own intake form all
render the same questions and cannot drift apart.

Every question names the article it exists to resolve. An intake question that
cannot say which legal determination it feeds is a question nobody should be
made to answer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .classifier import SystemSpec


@dataclass
class Question:
    key: str
    prompt: str
    kind: str = "text"                    # text | list | bool | choice
    choices: list[str] = field(default_factory=list)
    why: str = ""                         # which determination this feeds
    relevant: Callable[[dict], bool] = lambda _a: True
    required: bool = False
    default: Any = None


QUESTIONS: list[Question] = [
    Question("name", "What is the AI system called?", "text",
             why="Identifies the subject of the assessment record.", required=True),
    Question("sector", "Which sector is it deployed in?", "text",
             why="Art. 6(2) — sector raises the prior for Annex III use cases.", required=True),
    Question("use_cases", "What does it decide, score, rank, or generate? (one per line)", "list",
             why="Annex III — the use case, not the technology, determines high risk.",
             required=True),
    Question("description", "Describe the system in two or three sentences.", "text",
             why="Widens the text the indicator lexicons match against."),
    Question("deployment_context", "Who uses it and where?", "choice",
             choices=["internal tool", "customer-facing", "public sector", "public-facing eu"],
             why="Art. 2 territorial scope and Art. 26 deployer duties."),
    Question("affected_persons", "Whose interests are affected by its output? (one per line)", "list",
             why="Art. 27 — fundamental-rights impact assessment trigger."),
    Question("autonomy", "How autonomous is it in production?", "choice",
             choices=["assistive", "human_in_the_loop", "autonomous"],
             why="Art. 14 — scales the human-oversight obligation.", default="assistive"),
    Question("human_oversight", "What human oversight exists today?", "choice",
             choices=["none", "review", "approval", "unknown"],
             why="Art. 14 — evidence of oversight, and the confidence penalty when absent.",
             default="unknown"),
    Question("generates_content", "Does it generate text, image, audio or video for people to see?", "bool",
             why="Art. 50(2) — machine-readable marking of synthetic content.", default=False),
    Question("processes_biometrics", "Does it process biometric data?", "bool",
             why="Annex III(1) and Art. 5 — biometric identification and categorisation.",
             default=False),
    Question("infers_emotions", "Does it infer emotions or affective state?", "bool",
             why="Art. 5(1)(f) at work or school; Art. 50(3) elsewhere.", default=False),
    Question("safety_component", "Is it a safety component of a regulated product?", "bool",
             why="Art. 6(1) + Annex I — the other route to high risk.", default=False),
    Question("is_gpai", "Are you the provider of a general-purpose AI model?", "bool",
             why="Chapter V — duties that apply in addition to any system tier.", default=False),
    Question("gpai_systemic_risk", "Was it trained above 10^25 FLOP or designated systemic-risk?", "bool",
             why="Art. 55 — systemic-risk obligations.", default=False,
             relevant=lambda a: bool(a.get("is_gpai"))),
    Question("eu_market", "Is it placed on the market or used in the EU?", "bool",
             why="Art. 2 — territorial scope.", default=True),
]


def relevant_questions(answers: dict[str, Any]) -> list[Question]:
    return [q for q in QUESTIONS if q.relevant(answers)]


def missing_required(answers: dict[str, Any]) -> list[str]:
    return [q.key for q in relevant_questions(answers)
            if q.required and not answers.get(q.key)]


def to_spec(answers: dict[str, Any]) -> SystemSpec:
    """Coerce raw answers into a `SystemSpec`.

    Tolerant on purpose: a list question answered as a comma-separated string,
    or a bool answered "yes", is a human filling in a form correctly. Rejecting
    it is the tool being pedantic at the exact moment someone is trying to use it.
    """
    def as_list(v: Any) -> list[str]:
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        if not v:
            return []
        sep = "\n" if "\n" in str(v) else ","
        return [p.strip() for p in str(v).split(sep) if p.strip()]

    def as_bool(v: Any, default: bool = False) -> bool:
        if isinstance(v, bool):
            return v
        if v is None:
            return default
        return str(v).strip().lower() in ("y", "yes", "true", "1", "evet", "on")

    return SystemSpec(
        name=str(answers.get("name") or "unnamed-system"),
        sector=str(answers.get("sector") or ""),
        use_cases=as_list(answers.get("use_cases")),
        description=str(answers.get("description") or ""),
        deployment_context=str(answers.get("deployment_context") or ""),
        autonomy=str(answers.get("autonomy") or "assistive"),
        human_oversight=str(answers.get("human_oversight") or "unknown"),
        affected_persons=as_list(answers.get("affected_persons")),
        is_gpai=as_bool(answers.get("is_gpai")),
        gpai_systemic_risk=as_bool(answers.get("gpai_systemic_risk")),
        generates_content=as_bool(answers.get("generates_content")),
        processes_biometrics=as_bool(answers.get("processes_biometrics")),
        infers_emotions=as_bool(answers.get("infers_emotions")),
        safety_component=as_bool(answers.get("safety_component")),
        eu_market=as_bool(answers.get("eu_market"), default=True),
    )


def as_schema() -> list[dict[str, Any]]:
    """JSON form of the tree, for the Console wizard and third-party intake forms."""
    return [
        {"key": q.key, "prompt": q.prompt, "kind": q.kind, "choices": q.choices,
         "why": q.why, "required": q.required, "default": q.default,
         "depends_on": "is_gpai" if q.key == "gpai_systemic_risk" else None}
        for q in QUESTIONS
    ]

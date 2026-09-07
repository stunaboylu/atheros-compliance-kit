"""Collect the ledger into one document an ISO/IEC 42001 auditor can read.

Three decisions shape this module.

**It generates nothing.** Every line traces to an entry already in the chain. A
clause with no entries renders as `no records` and is counted against the pack,
never quietly omitted — an evidence pack whose gaps are invisible is the artefact
this product exists to prevent.

**It is a pure function of the ledger.** No generation timestamp, no run id: two
exports of the same chain are byte-identical, so an auditor who doubts the
document can re-run the command and diff it. The period the pack covers comes
from the entries themselves, which is the date range that actually matters.

**A pack from a broken chain is still written, and still says so.** Refusing
would destroy the one artefact that shows *which* entries were altered. The
warning is the first thing in the document, the JSON carries
`chain_intact: false`, and the command exits 1. There is deliberately no flag to
silence it: a flag to suppress the warning would become the way the warning is
suppressed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ..core.audit import AuditTrail, default_trail
from . import clauses as K

Status = Literal["evidenced", "input_only", "no_records"]

#: Records listed per clause before the tail is summarised. The remainder is
#: always stated — a cap that is not reported reads as "that was all of them".
MAX_LISTED = 25


@dataclass
class ClauseCoverage:
    clause: K.Clause
    entries: list[dict[str, Any]] = field(default_factory=list)

    @property
    def status(self) -> Status:
        if not self.entries:
            return "no_records"
        return "input_only" if self.clause.kind == "input" else "evidenced"

    @property
    def period(self) -> tuple[str, str] | None:
        if not self.entries:
            return None
        stamps = sorted(e.get("timestamp", "") for e in self.entries)
        return stamps[0][:10], stamps[-1][:10]

    @property
    def event_types(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self.entries:
            counts[e.get("event_type", "?")] = counts.get(e.get("event_type", "?"), 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


@dataclass
class EvidencePack:
    ledger: str
    chain_intact: bool
    violations: list[str]
    coverage: list[ClauseCoverage]
    total_entries: int
    chain_head: str | None
    version: str
    #: Entries whose module is not in the clause map. Reported rather than
    #: dropped: a module the export does not know about is a gap in this file,
    #: and silently discarding its entries would hide that.
    unattributed: int = 0

    @property
    def evidenced(self) -> int:
        return sum(1 for c in self.coverage if c.status == "evidenced")

    @property
    def fit_to_hand_over(self) -> bool:
        """Whether this pack can be given to an auditor as it stands.

        False on a broken chain (the records cannot be trusted) and on an empty
        ledger (there are no records). Both cases exit 1, because a command that
        succeeds while producing an empty evidence pack has told the operator
        nothing at the moment it mattered most.
        """
        return self.chain_intact and self.total_entries > 0

    # ── render ───────────────────────────────────────────────────────────────
    def to_dict(self, locale: str = "en") -> dict[str, Any]:
        return {
            "schema": "atheros.iso42001-evidence/v1",
            "standard": "ISO/IEC 42001:2023",
            "kit_version": self.version,
            "ledger": self.ledger,
            "chain_intact": self.chain_intact,
            "chain_head": self.chain_head,
            "violations": self.violations,
            "total_entries": self.total_entries,
            "unattributed_entries": self.unattributed,
            "fit_to_hand_over": self.fit_to_hand_over,
            "clauses": [
                {
                    "number": c.clause.number,
                    "title": K.title(c.clause.number, locale),
                    "kind": c.clause.kind,
                    "status": c.status,
                    "asks": K.asks(c.clause.number, locale),
                    "produced_by": K.produced_by(c.clause.number, locale),
                    "records": len(c.entries),
                    "period": list(c.period) if c.period else None,
                    "event_types": c.event_types,
                    "modules": list(c.clause.modules),
                }
                for c in self.coverage
            ],
            "not_covered": list(K.NOT_COVERED[locale if locale in K.NOT_COVERED else "en"]),
            "note": T[_lo(locale)]["not_a_statement"],
        }

    def to_markdown(self, locale: str = "en") -> str:
        lo = _lo(locale)
        t = T[lo]
        out: list[str] = [f"# {t['title']}", "", f"> {t['subtitle']}", ""]

        if not self.chain_intact:
            out += [f"> **⚠ {t['chain_broken_banner']}**", ""]
            for v in self.violations[:20]:
                out.append(f"> - {v}")
            if len(self.violations) > 20:
                out.append(f"> - … {len(self.violations) - 20} {t['more']}")
            out.append("")
        elif self.total_entries == 0:
            out += [f"> **⚠ {t['empty_banner']}**", ""]

        out += [f"## {t['what_this_is']}", "", t["what_this_is_body"], "", t["not_a_statement"], ""]

        head = self.chain_head[:16] + "…" if self.chain_head else "—"
        out += [
            f"## {t['the_ledger']}", "",
            "| | |", "|---|---|",
            f"| {t['source']} | `{self.ledger}` |",
            f"| {t['entries']} | {self.total_entries} |",
            f"| {t['chain_head']} | `{head}` |",
            f"| {t['integrity']} | {t['intact'] if self.chain_intact else t['violated']} |",
            f"| {t['kit_version']} | {self.version} |",
            "",
            t["reverify"].format(ledger=self.ledger),
            "",
        ]
        if self.unattributed:
            out += [t["unattributed"].format(n=self.unattributed), ""]

        out += [f"## {t['coverage']}", "",
                f"| {t['clause']} | {t['status']} | {t['records']} | {t['period']} |",
                "|---|---|---:|---|"]
        for c in self.coverage:
            period = " → ".join(c.period) if c.period else "—"
            out.append(f"| **{c.clause.number}** {K.title(c.clause.number, lo)} "
                       f"| {t[c.status]} | {len(c.entries)} | {period} |")
        out += ["", t["summary"].format(n=self.evidenced, total=len(self.coverage)), ""]

        for c in self.coverage:
            out += [f"### {c.clause.number} — {K.title(c.clause.number, lo)}", "",
                    f"**{t['clause_asks']}** {K.asks(c.clause.number, lo)}", "",
                    f"**{t['kit_contributes']}** {K.produced_by(c.clause.number, lo)}", ""]
            if c.clause.kind == "input":
                out += [f"> {t['input_only_note']}", ""]
            if not c.entries:
                out += [f"**{t['no_records_here']}**", "", t['no_records_body'], ""]
                continue
            out += [f"| {t['timestamp']} | {t['module']} | {t['event']} | {t['digest']} |",
                    "|---|---|---|---|"]
            for e in c.entries[:MAX_LISTED]:
                out.append(f"| {e.get('timestamp', '')[:19]} | `{e.get('module', '')}` "
                           f"| {e.get('event_type', '')} | `{e.get('hash', '')[:12]}` |")
            if len(c.entries) > MAX_LISTED:
                out.append(f"| … | | {t['and_more'].format(n=len(c.entries) - MAX_LISTED)} | |")
            out.append("")

        out += [f"## {t['not_covered']}", "", t["not_covered_body"], ""]
        out += [f"- {item}" for item in K.NOT_COVERED[lo]]
        out += ["", f"## {t['how_to_verify']}", "", t["how_to_verify_body"].format(
            ledger=self.ledger), ""]
        return "\n".join(out)


def build_pack(trail: AuditTrail | None = None, *, version: str | None = None) -> EvidencePack:
    """Read the ledger once and attribute every entry to the clause it evidences."""
    from .. import __version__
    from ..core import license

    license.require("iso.export")
    trail = trail or default_trail()
    coverage = {c.number: ClauseCoverage(c) for c in K.CLAUSES}
    total = 0
    unattributed = 0
    head: str | None = None
    for entry in trail.entries():
        total += 1
        head = entry.get("hash") or head
        number = K.MODULE_CLAUSE.get(entry.get("module", ""))
        if number is None:
            unattributed += 1
            continue
        coverage[number].entries.append(entry)
    intact, violations = trail.verify_chain()
    return EvidencePack(
        ledger=str(trail.path), chain_intact=intact, violations=violations,
        coverage=[coverage[c.number] for c in K.CLAUSES], total_entries=total,
        chain_head=head, version=version or __version__, unattributed=unattributed,
    )


def write_pack(pack: EvidencePack, out_dir: str | Path, locale: str = "en",
               *, formats: tuple[str, ...] = ("md", "json")) -> list[Path]:
    import json

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    stem = "iso-42001-evidence"
    if "md" in formats:
        p = out / f"{stem}.md"
        p.write_text(pack.to_markdown(locale), encoding="utf-8")
        written.append(p)
    if "json" in formats:
        p = out / f"{stem}.json"
        p.write_text(json.dumps(pack.to_dict(locale), indent=2, ensure_ascii=False) + "\n",
                     encoding="utf-8")
        written.append(p)
    return written


def _lo(locale: str) -> str:
    return "tr" if locale == "tr" else "en"


T: dict[str, dict[str, str]] = {
    "en": {
        "title": "ISO/IEC 42001 — evidence pack",
        "subtitle": "Records held in a hash-chained ledger, attributed to the clauses they "
                    "evidence. Produced by AtherosAI Compliance Kit from your own ledger.",
        "chain_broken_banner": "The audit chain does not verify. The records below cannot be "
                               "relied on until this is resolved. Do not hand this document over "
                               "in this state.",
        "empty_banner": "The ledger is empty. This pack contains no evidence.",
        "what_this_is": "What this document is",
        "what_this_is_body":
            "An extract of the audit ledger the Kit maintains, grouped by the ISO/IEC 42001 "
            "clause each record evidences. It contains nothing that was not already in the "
            "chain: no narrative was generated, no gap was filled, and every row can be traced "
            "to a ledger line by its digest.",
        "not_a_statement":
            "It is not a statement of compliance and not a certification. The Kit produces "
            "records for the five clauses listed below and for no others; the clauses it does "
            "not touch are listed in full at the end, so that this document cannot be read as "
            "broader than it is.",
        "the_ledger": "The ledger",
        "source": "Source", "entries": "Entries", "chain_head": "Chain head",
        "integrity": "Integrity", "kit_version": "Kit version",
        "intact": "**verified** — every digest recomputed",
        "violated": "**FAILED** — see the warning above",
        "reverify": "Verify this independently, without trusting this document:\n\n"
                    "```\natheros-kit audit verify --file {ledger}\n```",
        "unattributed": "> {n} ledger entry/entries come from a module this export does not map "
                        "to a clause. They are counted above but appear under no clause below. "
                        "This is a gap in the export, not in the ledger.",
        "coverage": "Clause coverage",
        "clause": "Clause", "status": "Status", "records": "Records", "period": "Period",
        "evidenced": "records held", "input_only": "input only — see below",
        "no_records": "**no records**",
        "summary": "{n} of {total} clauses hold records that evidence the clause itself.",
        "clause_asks": "The clause asks:", "kit_contributes": "What the Kit contributes:",
        "input_only_note":
            "These records are an **input** to this clause, not a discharge of it. An EU AI Act "
            "risk classification is a regulatory categorisation; the clause asks for the "
            "organisation's own AI risk criteria, analysis and evaluation, which no tool "
            "running inside a CI pipeline performs on its behalf.",
        "no_records_here": "No records.",
        "no_records_body": "Nothing in the ledger evidences this clause. This is a gap in the "
                           "evidence, not a finding about the clause — the modules that would "
                           "produce these records have not been run, or have not been run since "
                           "this ledger was started.",
        "timestamp": "Timestamp", "module": "Module", "event": "Event", "digest": "Digest",
        "and_more": "{n} further record(s), in the ledger and the JSON export",
        "more": "further violation(s)",
        "not_covered": "Not covered",
        "not_covered_body":
            "The following are requirements of ISO/IEC 42001 for which this product produces "
            "nothing. They are management-system work, and their absence here is a scope "
            "decision rather than an omission:",
        "how_to_verify": "How to verify this document",
        "how_to_verify_body":
            "1. Recompute the chain: `atheros-kit audit verify --file {ledger}`. Any altered or "
            "deleted line is reported with its number.\n"
            "2. Match any row above to the ledger by its digest: "
            "`atheros-kit audit show --file {ledger} --json`.\n"
            "3. Re-run this export against the same ledger. The document is a function of the "
            "ledger alone — no generation timestamp, no run id — so an unchanged ledger "
            "produces a byte-identical file, and a diff is evidence of change.",
    },
    "tr": {
        "title": "ISO/IEC 42001 — kanıt paketi",
        "subtitle": "Zincir özetli defterde tutulan kayıtlar, kanıtladıkları maddelere göre "
                    "gruplanmıştır. AtherosAI Compliance Kit tarafından kendi defterinizden "
                    "üretilmiştir.",
        "chain_broken_banner": "Denetim zinciri doğrulanmıyor. Aşağıdaki kayıtlara, bu durum "
                               "çözülene kadar güvenilemez. Belgeyi bu haliyle teslim etmeyin.",
        "empty_banner": "Defter boş. Bu paket hiçbir kanıt içermiyor.",
        "what_this_is": "Bu belge nedir",
        "what_this_is_body":
            "Aracın tuttuğu denetim defterinin, her kaydın kanıtladığı ISO/IEC 42001 maddesine "
            "göre gruplanmış bir dökümüdür. Zincirde zaten bulunmayan hiçbir şey içermez: "
            "hiçbir anlatı üretilmemiş, hiçbir boşluk doldurulmamıştır ve her satır özeti "
            "üzerinden bir defter satırına kadar izlenebilir.",
        "not_a_statement":
            "Bir uygunluk beyanı ya da belgelendirme değildir. Araç aşağıda listelenen beş madde "
            "için kayıt üretir, başka hiçbir madde için üretmez; dokunmadığı maddeler, bu belge "
            "olduğundan geniş okunamasın diye sonda eksiksiz listelenmiştir.",
        "the_ledger": "Defter",
        "source": "Kaynak", "entries": "Kayıt", "chain_head": "Zincir başı",
        "integrity": "Bütünlük", "kit_version": "Araç sürümü",
        "intact": "**doğrulandı** — her özet yeniden hesaplandı",
        "violated": "**BAŞARISIZ** — yukarıdaki uyarıya bakın",
        "reverify": "Bu belgeye güvenmeden, bağımsız olarak doğrulayın:\n\n"
                    "```\natheros-kit audit verify --file {ledger}\n```",
        "unattributed": "> {n} defter kaydı, bu dışa aktarımın bir maddeye eşlemediği bir "
                        "modülden geliyor. Yukarıdaki toplamda sayılıyor ancak aşağıda hiçbir "
                        "maddenin altında görünmüyor. Bu, defterdeki değil dışa aktarımdaki bir "
                        "eksikliktir.",
        "coverage": "Madde kapsamı",
        "clause": "Madde", "status": "Durum", "records": "Kayıt", "period": "Dönem",
        "evidenced": "kayıt mevcut", "input_only": "yalnızca girdi — aşağıya bakın",
        "no_records": "**kayıt yok**",
        "summary": "{total} maddenin {n} tanesinde, maddenin kendisini kanıtlayan kayıt var.",
        "clause_asks": "Madde ne ister:", "kit_contributes": "Aracın katkısı:",
        "input_only_note":
            "Bu kayıtlar bu madde için bir **girdidir**, maddenin karşılanması değildir. EU AI "
            "Act risk sınıflandırması düzenleyici bir kategorilendirmedir; madde ise kuruluşun "
            "kendi yapay zekâ risk ölçütlerini, analizini ve değerlendirmesini ister — bunu bir "
            "CI hattının içinde çalışan hiçbir araç kuruluş adına yapmaz.",
        "no_records_here": "Kayıt yok.",
        "no_records_body": "Defterde bu maddeyi kanıtlayan hiçbir şey yok. Bu, madde hakkında "
                           "bir bulgu değil, kanıttaki bir boşluktur — bu kayıtları üretecek "
                           "modüller ya hiç çalıştırılmamış ya da bu defter açıldığından beri "
                           "çalıştırılmamıştır.",
        "timestamp": "Zaman damgası", "module": "Modül", "event": "Olay", "digest": "Özet",
        "and_more": "{n} kayıt daha; defterde ve JSON dışa aktarımında",
        "more": "ihlal daha",
        "not_covered": "Kapsanmayanlar",
        "not_covered_body":
            "Aşağıdakiler, ISO/IEC 42001'in bu ürünün hiçbir şey üretmediği gereklilikleridir. "
            "Bunlar yönetim sistemi işidir ve burada yer almamaları bir ihmal değil, bir kapsam "
            "kararıdır:",
        "how_to_verify": "Bu belge nasıl doğrulanır",
        "how_to_verify_body":
            "1. Zinciri yeniden hesaplayın: `atheros-kit audit verify --file {ledger}`. "
            "Değiştirilmiş ya da silinmiş her satır numarasıyla bildirilir.\n"
            "2. Yukarıdaki herhangi bir satırı özeti üzerinden deftere eşleyin: "
            "`atheros-kit audit show --file {ledger} --json`.\n"
            "3. Bu dışa aktarımı aynı deftere karşı yeniden çalıştırın. Belge yalnızca defterin "
            "bir fonksiyonudur — üretim zaman damgası ya da koşu kimliği yoktur — dolayısıyla "
            "değişmemiş bir defter bayt bayt aynı dosyayı üretir ve bir fark, değişikliğin "
            "kanıtıdır.",
    },
}

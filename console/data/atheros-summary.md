## AtherosAI compliance gate — FAILED

| | Check | Value | Threshold | Detail |
|---|---|---|---|---|
| ❌ | `fairness_score` | 0.0 | 70 | 0.0 < 70 |
| ❌ | `quality_score` | 24.5 | 70 | 24.5 < 70 |
| ✅ | `corpus_drift` | stable | ['shifted'] |  |
| ✅ | `eu_ai_act_tier` | high | ['unacceptable'] |  |
| ✅ | `vendor_score.openai` | 83.3 | 60 |  |
| ✅ | `residency.openai` | requires_scc | ['non_compliant'] |  |
| ✅ | `vendor_score.mistral` | 64.4 | 60 |  |
| ✅ | `residency.mistral` | compliant | ['non_compliant'] |  |
| ❌ | `guard_blocks` | 2 | 0 | 2 blocked invocation(s) exceed the configured cap of 0 |
| ✅ | `audit_chain` | intact | intact |  |

_Produced by the AtherosAI Compliance Kit._
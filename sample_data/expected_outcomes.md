# Expected outcomes (for self-grading)

These are the verdicts a well-built HireGraph should produce. Use them as a sanity check before you submit. A failing match does not automatically lose points (LLM outputs vary), but a wildly different verdict probably points to a bug.

| Resume | JD | Expected seniority classification | Expected recommendation | Should pause for human review? |
| :--- | :--- | :--- | :--- | :---: |
| `resume_priya.md` | `jd_senior_backend.md` | senior | advance | no |
| `resume_eitan.md` | `jd_senior_backend.md` | mid (with senior potential) | borderline | yes |
| `resume_mira.md` | `jd_senior_backend.md` | senior (frontend) | reject | no |
| `resume_priya.md` | `jd_junior_data.md` | senior | reject (overqualified) | no |
| `resume_eitan.md` | `jd_junior_data.md` | mid | borderline | yes |
| `resume_mira.md` | `jd_junior_data.md` | senior (frontend) | reject (skill mismatch) | no |

The clean signals are intentional. Priya is the strong senior backend candidate, Eitan is the always-borderline case that triggers your `interrupt()` path, Mira is the obvious skill mismatch that exercises your rejection branch.

If you only show one demo, show **Eitan against the senior backend JD**. That run exercises classification, parallel scoring, the orchestrator and worker over JD-required skills, the critic loop on the email, and the human review interrupt. It is the most teachable scenario.

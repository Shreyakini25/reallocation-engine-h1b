# Data Source & Provenance

`SEC_DOL_H1b_data_mapped.csv` is real data, but its origin needs to be
stated plainly rather than left implicit.

**Where it came from:** this file lives inside my fork of Professor Brown's
own `the-reallocation-engine` course repository, under
`data/80-days-to-stay/data/`. It is not something I independently scraped
or downloaded from Data.gov, Kaggle, or HuggingFace — it is a resource
already present in the course tooling I forked for an earlier, separate
assignment (the mode-file exercise).

**What it actually is, as best I can tell from the file itself:** a
company-level join of two real source types —
1. SEC/startup-style company metadata (incorporation year, funding rounds,
   executives) — the kind of data available from public company filings
   and startup-funding trackers, and
2. DOL H-1B LCA disclosure outcomes (Total Approvals, Total Denials,
   Approval_Rate, median_salary_offered) — the same public disclosure
   program documented in DOL's own LCA Record Layout
   (dol.gov/agencies/eta/foreign-labor/performance).

I did not write the join/mapping logic that produced this CSV — that
appears to have been built into the course repo's own tooling before I
forked it. What I did independently: the GIGO gate, the engine logic, the
bias audit, the causal analysis, the adversarial test, and the delegation
map are all built fresh for this assignment and run directly against this
file's actual columns and values — none of the validation work reuses any
professor-authored analysis code.

**Why this is disclosed here rather than presented as an independently-
sourced dataset:** the assignment's honesty standard (Component 2, GIGO
gate; the "What NOT to Do" section) is about not hiding inconvenient facts
about your inputs. Where the data physically came from is exactly that
kind of fact.

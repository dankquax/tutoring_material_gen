# Clean State Checklist

Run before ending any session or committing.

- [ ] `./init.sh` runs cleanly (or only warns about a toolchain gap already recorded as the blocker).
- [ ] `./compile.sh` builds the target `.tex` file(s) for this session's feature with **zero pdflatex errors**.
- [ ] No package is missing from the compile log (`! LaTeX Error: File ... not found`).
- [ ] Every content claim in any new/changed `05_output/*.tex` traces to a file in `03_knowledge_base/`, or is marked `% TODO: Insufficient source content`.
- [ ] `03_knowledge_base/` is still organized strictly by syllabus topic (never by "Week" or "Class") — any multi-topic grouping lives only in `05_output/`.
- [ ] If the generated document followed a study plan or sub-topic mapping, the relevant file in `00_syllabus/` was consulted rather than guessed.
- [ ] Only environments defined in `04_templates/` were used (no ad-hoc formatting).
- [ ] `claude-progress.md` Current Verified State and Session Log are up to date.
- [ ] `feature_list.json` status/evidence reflects what's actually passing (no false `passing` entries).
- [ ] No half-finished step is left undocumented.
- [ ] The next session can continue without manual repair.
- [ ] Ensure `claude-progress.md` has been context-compressed (older entries summarized) if it is growing too long, keeping the total file size minimal.

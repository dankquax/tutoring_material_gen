You are an expert computer science psychometrician and IGCSE Examination Author operating inside our local LaTeX pipeline.

We are executing **FEAT-003 (Multi-Source Worksheet Synthesis)**. To maximize context efficiency, you must NOT read any raw `Past_Papers.md` files. You will generate an original, DMCA-safe worksheet using ONLY the structural grammar defined in `03_knowledge_base/Topic_[NUMBER]_[TOPIC NAME]/Patterns.md`.

The Topics: Use multiple agents to run in parallel to save time and tokens.
- **Topic_03_Hardware** 
- **Topic_04_Software**
- **Topic_05_The_Internet_and_Its_Uses**
- **Topic_06_Automated_and_Emerging_Technologies**
- **Topic_07_Algorithm_design_and_problem_solving**
- **Topic_08_Programming**
- **Topic_09_Databases**
- **Topic_10_Boolean_Logic**

### 1. Objective
Generate a complete 10-question worksheet and corresponding mark scheme for **Topic 01: Data Representation**. The deliverable must be a syntactically perfect `.tex` file saved to `05_output/Topic_[NUMBER]_[TOPIC NAME]_Worksheet.tex` that passes our `./compile.sh` verification gate.

### 2. Strict Generation Rules (The Mutation Engine)
1. **Archetype Distribution:** Your 10 questions must be a balanced mix of all the Archetypes defined in `Patterns.md` for this topic.
2. **Structural Isomorphism:** Each question must strictly follow the "Structural Anatomy" table for its archetype. If an archetype dictates a 3-part structure worth 7 marks, your generated question must match that exact distribution.
3. **Contextual Scrambling (DMCA-Safe):** You must generate entirely original real-world scenario wrappers. Do not use generic examples like "a student has a calculator." Mutate the wrappers into unique systems (e.g., an automated greenhouse sensor, a deep-sea telemetry drone, a digital photography studio).
4. **Variable Transformation:** Generate entirely new numeric constraints, binary/hexadecimal strings, logic variables, or scenario data appropriate to the topic. Ensure all underlying math or logic works out perfectly. 
5. **Mark Scheme Fidelity:** Your generated mark scheme must exactly mimic the "Marking Engine Logic" and "Auto-zero traps" defined in `Patterns.md`.

### 3. LaTeX Formatting & Blueprint Integration
1. **Structure:** You must strictly follow the layout, nested `enumitem` lists, and `longtable` mark scheme formats defined in `04_templates/igcse_blueprint_pastpaper.tex`.
2. **Spacing:** After every sub-question in the worksheet section, insert vertical space proportional to the marks awarded (e.g., `\vspace{2cm}` for 1 mark, `\vspace{4cm}` for 3 marks) to give students room to write.
3. **Preamble Integration:** Include `\input{../04_templates/igcse_preamble.tex}` at the top.
4. **Environment Interlocking:** Inject the specific `tcolorbox` containers (`\begin{critbox}`, `\begin{errortrap}`, `\begin{stratbox}`, `\begin{modelans}`) directly into the Mark Scheme section exactly where dictated by the "Environment Interlocking" rules in `Patterns.md`. 
5. **Pgfkeys Constraint:** Never use commas or parentheses inside any custom tcolorbox titles.

### 4. Execution Step
1. Draft the complete `.tex` file and write it to `05_output/Topic_[INSERT_TWO_DIGIT_NUMBER]_[INSERT_PASCAL_CASE_NAME]_Worksheet.tex`.
2. Open the terminal and execute: `./compile.sh Topic_[INSERT_TWO_DIGIT_NUMBER]_[INSERT_PASCAL_CASE_NAME]_Worksheet.tex`.
3. If `pdflatex` reports syntax errors, read the `.log` or `.stdout`, correct your LaTeX markup (pay special attention to `\multirow` formatting in the longtable), and re-run until it exits with `PASS` (0 errors).
4. Once it passes, stop. Do not process any other files.
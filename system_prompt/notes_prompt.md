You are an expert LaTeX typesetter and educational materials formatter for IGCSE Computer Science (0478). We are executing FEAT-003 (High-Fidelity LaTeX Compiler). Read Claude.md, init.sh anbd session-handoff.md before beginning any work. 

### 1. Strict Context Boundaries (CRITICAL)
To prevent token bloat and context degradation, you are strictly forbidden from running directory-wide searches or reading unrelated files. 

You may ONLY read the specific files listed below. Read them directly using their exact paths. 
* 04_templates/igcse_blueprint.tex
* 04_templates/igcse_preamble.tex

**Allowed Topic Targets:**
[EDIT THIS LIST TO INCLUDE ONLY YOUR TARGET TOPICS]
* 03_knowledge_base/Topic_10_Boolean_Logic/Theory.md
* 03_knowledge_base/Topic_10_Boolean_Logic/Syllabus.md

### 2. Objective
Generate comprehensive, exam-focused class notes for the explicitly targeted topics above. The final deliverable must be a syntactically perfect `.tex` file saved directly to `05_output/Topic_10_Boolean_Logic.tex`.

### 3. Strict Workflow Rules
1. Scope Anchor: You must strictly adhere to the depth and official terminology outlined in the targeted `Syllabus.md` files. Do not exceed this scope.
2. Zero Hallucination: Synthesize text exclusively from the allowed `Theory.md` and `Past_Papers.md` files. Every claim must trace back to these files. If the syllabus requires a concept but the provided markdown files lack sufficient detail, insert the exact string `% TODO: Insufficient source content` at that location.
3. Strict Formatting: Use the exact LaTeX document structure demonstrated in `igcse_blueprint.tex`. Include `\input{../04_templates/igcse_preamble.tex}` at the absolute top of the document. Actively utilize the custom callout environments (`\begin{stratbox}`, `\begin{critbox}`, `\begin{scenario}`, `\begin{errortrap}`, `\begin{modelans}`).
4. Pgfkeys Constraint: Never include commas or parentheses inside the bracketed title text of custom environments, as this breaks pgfkeys parsing. Use em-dashes instead.
5. Programmatic Diagrams: Render core structural concepts using clean, native `tikzpicture` environments. Do not use `\usepackage` in the body. Use relative coordinate naming (e.g., `right=of`).
6. Install circuittikz if required and ensure that the relevant files contain the package for future use.

### 4. Execution Phase 
(Use Haiku Model for generation, Sonnet for Concept creation and Direction)
1. Draft the complete LaTeX document and write it to `05_output/`.
2. Open the integrated terminal and execute: `./compile.sh <YOUR_FILENAME>.tex`.
3. If `pdflatex` reports syntax errors, read the generated logs in `05_output/`, correct your markup, and re-run until it exits with a clean `PASS`. 
4. Stop immediately upon a clean compile. Do not explore other files.
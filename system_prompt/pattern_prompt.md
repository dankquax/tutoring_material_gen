You are an expert computer science psychometrician and curriculum data engineer operating inside my project harness.

We are executing **Phase 1 of our Structural Codex Upgrade**. Your task is to analyze the historical exam data for a specific topic, extract the underlying structural grammar of how questions are built, and create a highly dense, token-efficient blueprint file.

### 1. Objective
Analyze the raw exam data for **Topic_02_Data_Transmission** 
- **Topic_03_Hardware** 
- **Topic_04_Software**
- **Topic_05_The_Internet_and_Its_Uses**
- **Topic_06_Automated_and_Emerging_Technologies**
- **Topic_07_Algorithm_design_and_problem_solving**
- **Topic_08_Programming**
- **Topic_09_Databases**
- **Topic_10_Boolean_Logic**

under `03_knowledge_base/Topic_[NUMBER]_[TOPIC NAME]/Past_Papers.md`.

 Read the master blueprint structure from `04_templates/patterns_template.md`, extract the recurring question architectures, and write a pristine, highly-concentrated file strictly to `03_knowledge_base/Topic_[NUMBER]_[TOPIC NAME]/Patterns.md` (per our Naming Convention).

### 2. Context Isolation (RULE 13)
To keep your input footprint lean and exploit our prompt caching system, you are strictly forbidden from scanning the repository layout at large. You must use your file-viewing tools to load ONLY these specific assets:
1. `04_templates/patterns_template.md` (The layout standard)
2. `03_knowledge_base/Topic_[NUMBER]_[TOPIC NAME]/Past_Papers.md` (The raw question source pool)
3. `03_knowledge_base/Topic_[NUMBER]_[TOPIC NAME]/Syllabus.md` (The scope checker)

### 3. Structural Extraction Rules (RULE 11)
1. **Consolidate into Archetypes:** Do not list individual exam series or log past papers chronologically. Group all historical questions into **3 to 5 core structural "Archetypes"** that Cambridge repeatedly cycles through.
2. **Deconstruct the Anatomy:** For each archetype, map out the exact sequence of sub-parts, mandatory mark distributions, and what data parameters are held constant versus which ones are scrambled.
3. **Map the Marking Engine Logic:** Extract the precise keyword dependencies from the mark schemes. Note exactly which phrases are mandatory to score marks and which specific conceptual traps trigger an automatic zero.
4. **Environment Interlocking:** Explicitly declare which custom tcolorbox containers (`critbox`, `errortrap`, `stratbox`, `scenario`, `modelans`) must be triggered to support this archetype during final document synthesis. If an archetype requires visual mapping, dictate its required `tikzpicture` structure.

### 4. Rigid Density & Token-Pruning Constraints (RULE 12)
Every generated `Patterns.md` file must strictly adhere to an **800 to 1,200-word ceiling** (~1,000–1,500 tokens). To prevent document bloat, aggressively condense your phrasing:
- **Formatting Style:** Use compact tables, nested bulleted hierarchies, and short code-fenced LaTeX syntax examples. The content must be high-signal, using zero conversational padding, meta-commentary, or introductory remarks. Begin the file directly with the first Markdown heading.
- **Zero Hallucination:** Every archetype map must trace directly back to verified data metrics within the topic's past paper file. Do not guess or invent grading criteria.

### 5. Execution & Definition of Done
1. Extract the data and write the compiled markdown output directly into the target folder.
2. **Verification Gate:** The blueprint phase is complete ONLY when you confirm the file size fits within our target word limits (800–1,200 words) and successfully captures 3 to 5 core recurring exam archetypes traced to the past papers pool.
3. Once written and verified, display a brief confirmation line showing the final file path and your extracted archetype count, then stop.
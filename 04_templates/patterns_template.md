

## Token & Word Limit Budgets
To keep these files sitting safely within Claude’s premium, lightning-fast Prompt Cache layer, you must enforce a strict budget per topic file.

Target Word Count: 800 to 1,200 words per topic Patterns.md file.

Target Token Footprint: ~1,000 to 1,500 input tokens.

To guarantee that Claude reproduces the exact structural logic (Isomorphism) without copying the text, each topic's pattern file should be broken down by Question Archetypes.

Here is the exact structural template to use for your Patterns.md files, this is only a reference and the content must be derived entirely from the source documents, not this template.:

# Topic 04: Software --- Exam Question Patterns

## Archetype 1: Comprehensive System vs Application Contrast
- **Syllabus Target:** 4.1 Types of Software
- **Historical Frequency:** High (Appears across multiple paper variants)
- **Total Marks:** 4 Marks

### Structural Anatomy
- **Part (a) [2 Marks]:** Core operational distinction. Requires a definitive contrast statement matching the "Computer vs User" service rules.
- **Part (b) [2 Marks]:** Dual-domain verification. Requires 1 explicit system software example and 1 explicit application software example mapped out in a localized layout.

### The Marking Engine Logic
- **Marking Constraints:** Do not accept vague descriptions like "helps the computer run." Mark schemes strictly demand the keyword "computer requires" for system and "user requires" for application.
- **Insulated Guardrails:** Bake a `\begin{critbox}` container into the solution text to explicitly warn students against using empty filler phrases.

---

## Archetype 2: Process Cycle Tracing (e.g., Interrupt Handling)
- **Syllabus Target:** 4.1 Interrupt Handling Sequence
- **Total Marks:** 5 Marks

### Structural Anatomy
- **Monolithic Multi-Step List:** Requires a sequential, 5-point mechanical explanation of an event loop (e.g., hardware trigger event).

### The Marking Engine Logic
- **Marking Constraints:** Points must follow the exact chronological trajectory: Priority Evaluation $\to$ Safe Register State Storage on Stack $\to$ ISR Execution $\to$ State Restoration $\to$ Task Resume. Leaving out the priority or stack metrics automatically drops the response ceiling by 2 marks.
- **Visual Mapping:** This archetype requires an accompanying vector flowchart built using a native `tikzpicture` wrapper demonstrating the loop cycle.
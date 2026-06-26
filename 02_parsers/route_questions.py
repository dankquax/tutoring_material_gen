#!/usr/bin/env python3
"""
Route parsed past paper questions to their semantic syllabus topic using local Ollama.
"""

import os
import re
import json
import argparse
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
KB_DIR = ROOT_DIR / "03_knowledge_base"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Note: Update if your local Ollama tag differs (e.g. "llama3.2:3b")
MODEL_NAME = "llama3.2" 

TOPICS = [
    "Topic_01_Data_Representation",
    "Topic_02_Data_Transmission",
    "Topic_03_Hardware",
    "Topic_04_Software",
    "Topic_05_The_Internet_and_its_uses",
    "Topic_06_Automated_and_emerging_technologies",
    "Topic_07_Algorithm_design_and_problem_solving",
    "Topic_08_Programming",
    "Topic_09_Databases",
    "Topic_10_Boolean_logic"
]

def parse_past_paper(file_path: Path) -> list:
    """Splits a PastPaper_*.md file into individual Question/Mark Scheme chunks."""
    content = file_path.read_text(encoding="utf-8")
    
    # Split using multiline regex lookahead for '## Question '
    chunks = re.split(r'(?m)^(?=## Question )', content)
    
    questions = []
    source_file = file_path.name
    
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk.startswith("## Question "):
            continue
        
        # Extract the question label (e.g., "1(a)")
        match = re.search(r'^## Question (.+)', chunk)
        q_label = match.group(1).strip() if match else "Unknown"
        
        questions.append({
            "label": q_label,
            "content": chunk,
            "source_file": source_file
        })
        
    return questions

def classify_question(chunk_content: str) -> dict:
    """Uses local Ollama to classify the chunk into a syllabus topic."""
    prompt = f"""You are an IGCSE 0478 Computer Science expert. Analyze the following Question and Mark Scheme chunk and classify it into one of the official syllabus topics.

Official Topics:
{json.dumps(TOPICS, indent=2)}

Question Chunk:
{chunk_content}

Extract the following information and return ONLY a raw JSON object (no markdown formatting, no code blocks).
You MUST follow this schema exactly:
{{
  "topic_folder": "Exact name of the destination folder from the list above",
  "tags": ["3-5", "ultra-lean", "strings", "representing", "concepts"],
  "total_marks": 6, 
  "syllabus_ref": "A short breadcrumb string (e.g. '3.2 Input/Output')"
}}
"""
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "format": "json",  # Forces strict JSON output in Ollama
            "stream": False
        }, timeout=90) # Give local model time to process long context
        response.raise_for_status()
        
        result_json = response.json().get("response", "")
        parsed = json.loads(result_json)
        
        # Guardrail against hallucinated folder names
        if parsed.get("topic_folder") not in TOPICS:
            print(f"    [!] Warning: Model hallucinated topic '{parsed.get('topic_folder')}'. Defaulting to Topic_01.")
            parsed["topic_folder"] = TOPICS[0]
            
        return parsed
        
    except requests.exceptions.RequestException as e:
        print(f"    [!] Network/API error communicating with Ollama: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"    [!] Error parsing JSON from model output: {e}\nRaw Output: {result_json}")
        return None

def process_file(file_path: Path):
    print(f"\nProcessing {file_path.name}...")
    questions = parse_past_paper(file_path)
    
    if not questions:
        print("  No questions found. Skipping.")
        return

    for q in questions:
        print(f"  Routing Question {q['label']}...")
        classification = classify_question(q['content'])
        
        if not classification:
            print(f"  -> Failed to classify {q['label']}, skipping.")
            continue
            
        topic_folder = classification.get("topic_folder")
        tags = classification.get("tags", [])
        total_marks = classification.get("total_marks", 0)
        syllabus_ref = classification.get("syllabus_ref", "")
        
        # Build YAML frontmatter block
        yaml_frontmatter = f"""---
source_file: "{q['source_file']}"
question_label: "{q['label']}"
topic_folder: "{topic_folder}"
tags: {json.dumps(tags)}
total_marks: {total_marks}
syllabus_ref: "{syllabus_ref}"
---
"""
        # Prepend the requested metadata tag
        metadata_tag = f"> Source: {q['source_file']}, Q{q['label']}\n\n"
        
        # Construct final chunk
        final_chunk = yaml_frontmatter + metadata_tag + q['content'] + "\n\n"
        
        # Append to target normalized file
        target_dir = KB_DIR / topic_folder
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "Past_Papers.md"
        
        with open(target_file, "a", encoding="utf-8") as f:
            f.write(final_chunk)
            
        print(f"  -> Appended to {topic_folder}/Past_Papers.md")

def main():
    parser = argparse.ArgumentParser(description="Route past paper questions to topic folders via local Ollama.")
    parser.add_argument("files", nargs="*", help="Specific PastPaper_*.md files to process (processes all if empty)")
    args = parser.parse_args()
    
    if not KB_DIR.exists():
        print(f"Error: {KB_DIR} does not exist.")
        return

    files_to_process = []
    if args.files:
        for f in args.files:
            file_path = Path(f)
            if not file_path.is_absolute():
                file_path = KB_DIR / file_path
            if file_path.exists():
                files_to_process.append(file_path)
            else:
                print(f"Warning: File {file_path} not found.")
    else:
        files_to_process = list(KB_DIR.glob("PastPaper_*.md"))

    if not files_to_process:
        print("No PastPaper_*.md files found to process.")
        return

    for file_path in files_to_process:
        process_file(file_path)
        
    print("\nRouting complete.")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Migrates 03_knowledge_base/Topic_XX_Name.md to Topic_XX_Name/Theory.md and Past_Papers.md"""

import glob
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = ROOT_DIR / "03_knowledge_base"

def migrate():
    # Find all Topic_*.md files (excluding PastPaper_*.md)
    topic_files = glob.glob(str(KNOWLEDGE_BASE_DIR / "Topic_*.md"))
    
    for file_path in topic_files:
        path = Path(file_path)
        topic_dir_name = path.stem  # e.g., Topic_01_Data_Representation
        topic_dir_path = KNOWLEDGE_BASE_DIR / topic_dir_name
        
        # Create the new directory
        topic_dir_path.mkdir(parents=True, exist_ok=True)
        
        theory_path = topic_dir_path / "Theory.md"
        past_papers_path = topic_dir_path / "Past_Papers.md"
        
        content = path.read_text(encoding="utf-8")
            
        # Split by a known past paper heading if it exists
        split_heading = "## Past Paper Questions"
        if split_heading in content:
            theory_content, past_paper_content = content.split(split_heading, 1)
            past_paper_content = split_heading + past_paper_content
        else:
            theory_content = content
            past_paper_content = "# Past Paper Questions\n\n"
            
        # Write to new files
        theory_path.write_text(theory_content.strip() + "\n", encoding="utf-8")
        past_papers_path.write_text(past_paper_content.strip() + "\n", encoding="utf-8")
            
        # Remove the old monolithic file
        path.unlink()
        print(f"Migrated {path.name} -> {topic_dir_name}/")

if __name__ == "__main__":
    migrate()
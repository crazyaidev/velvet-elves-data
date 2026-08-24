"""Render AUDRI_UPDATED_TASK_LIST_QUESTIONS.md to a branded .docx."""
from __future__ import annotations

from pathlib import Path

from generate_docs import _create_markdown_doc

SOURCE_FILE = "AUDRI_UPDATED_TASK_LIST_QUESTIONS.md"
OUTPUT_FILE = "AUDRI_UPDATED_TASK_LIST_QUESTIONS.docx"


def create_audri_updated_task_list_questions_doc() -> None:
    _create_markdown_doc(SOURCE_FILE, OUTPUT_FILE)


if __name__ == "__main__":
    create_audri_updated_task_list_questions_doc()
    print(f"Wrote {Path(__file__).resolve().parent / OUTPUT_FILE}")

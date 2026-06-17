"""
Orchestrate taxonomy-guided CSDS extraction improvements end-to-end.

Run:
    python -m src.postpoll.improve_taxonomy_extraction
"""

from __future__ import annotations

import subprocess
import sys


STEPS = [
    "src.postpoll.csds_table_label_miner",
    "src.postpoll.taxonomy_guided_search",
    "src.postpoll.taxonomy_guided_extract",
    "src.postpoll.validate_taxonomy_candidates",
    "src.postpoll.approve_taxonomy_candidates",
    "src.postpoll.render_taxonomy_review_pages",
]


def main() -> None:
    for step in STEPS:
        print(f"\n>>> python -m {step}")
        result = subprocess.run([sys.executable, "-m", step], check=False)
        if result.returncode != 0:
            raise SystemExit(result.returncode)
    print("\nTaxonomy extraction improvement pipeline complete.")


if __name__ == "__main__":
    main()

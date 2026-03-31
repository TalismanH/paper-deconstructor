#!/usr/bin/env python3
"""Sync paper metadata and deconstructed notes to Zotero via API."""

import sys
import json
import re
import argparse
from pathlib import Path

# .env file is at the skill root (one level above this scripts/ directory)
_ENV_PATH = Path(__file__).parent.parent / ".env"


def load_env_file() -> dict:
    """Read variables exclusively from the skill's .env file.

    Uses dotenv_values() which returns a plain dict and never modifies
    os.environ, so the calling process stays unaffected.
    Falls back to a minimal built-in parser if python-dotenv is absent.
    """
    try:
        from dotenv import dotenv_values
        return dotenv_values(_ENV_PATH)
    except ImportError:
        pass

    # Built-in fallback parser
    if not _ENV_PATH.exists():
        return {}
    env: dict = {}
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def get_credentials(env: dict) -> tuple[str, str]:
    user_id = env.get("ZOTERO_USER_ID", "").strip()
    api_key = env.get("ZOTERO_API_KEY", "").strip()
    return user_id, api_key


def parse_authors(author_str: str) -> list:
    """Parse an author string into Zotero creator objects."""
    if not author_str:
        return []
    creators = []
    for name in re.split(r"[;,]", author_str):
        name = name.strip()
        if not name:
            continue
        # Try "Last, First" format first
        if "," in name:
            parts = name.split(",", 1)
            creators.append({
                "creatorType": "author",
                "lastName": parts[0].strip(),
                "firstName": parts[1].strip(),
            })
        else:
            # Try splitting on last space: "First Last"
            parts = name.rsplit(" ", 1)
            if len(parts) == 2:
                creators.append({
                    "creatorType": "author",
                    "firstName": parts[0].strip(),
                    "lastName": parts[1].strip(),
                })
            else:
                creators.append({"creatorType": "author", "name": name})
    return creators


def sync_to_zotero(pdf_path: str, output_dir: str, metadata: dict) -> dict:
    try:
        from pyzotero import zotero as pyzotero
    except ImportError:
        return {"error": "pyzotero not installed. Run: pip install pyzotero"}

    env = load_env_file()
    user_id, api_key = get_credentials(env)

    try:
        zot = pyzotero.Zotero(user_id, "user", api_key)
    except Exception as e:
        return {"error": f"Failed to connect to Zotero: {e}"}

    # Build item template
    template = zot.item_template("journalArticle")
    template["title"] = metadata.get("title") or Path(pdf_path).stem
    template["abstractNote"] = metadata.get("subject", "")
    template["extra"] = metadata.get("keywords", "")
    template["creators"] = parse_authors(metadata.get("author", ""))

    # Create the item
    try:
        result = zot.create_items([template])
    except Exception as e:
        return {"error": f"Failed to create Zotero item: {e}"}

    successful = result.get("successful", {})
    if not successful:
        return {"error": "Zotero returned no successful item", "raw": result}

    item_key = successful["0"]["key"]

    # Attach the PDF (best-effort)
    try:
        zot.attachment_simple([pdf_path], item_key)
    except Exception:
        pass

    # Attach deconstructed markdown files as child notes
    output_path = Path(output_dir)
    note_files = ["summary.md", "method.md", "picture.md", "qa.md", "code.md"]
    attached_notes = []

    for fname in note_files:
        fpath = output_path / fname
        if not fpath.exists():
            continue
        try:
            content = fpath.read_text(encoding="utf-8")
            note_template = zot.item_template("note")
            note_template["note"] = (
                f"<h2>{fname}</h2>"
                f"<pre style='white-space:pre-wrap'>{content}</pre>"
            )
            note_template["parentItem"] = item_key
            zot.create_items([note_template])
            attached_notes.append(fname)
        except Exception:
            pass  # Notes are best-effort

    zotero_url = f"https://www.zotero.org/users/{user_id}/items/{item_key}"
    return {
        "success": True,
        "item_key": item_key,
        "zotero_url": zotero_url,
        "attached_notes": attached_notes,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sync a paper and its deconstructed files to Zotero."
    )
    parser.add_argument("pdf_path", help="Path to the original PDF file")
    parser.add_argument("output_dir", help="Directory containing the deconstructed .md files")
    parser.add_argument(
        "--metadata", default="{}",
        help="JSON string of paper metadata (title, author, etc.)",
    )
    args = parser.parse_args()

    metadata = json.loads(args.metadata)
    result = sync_to_zotero(args.pdf_path, args.output_dir, metadata)
    print(json.dumps(result, ensure_ascii=False, indent=2))

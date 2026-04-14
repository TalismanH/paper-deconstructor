#!/usr/bin/env python3
"""
Optional sync: push deconstructed paper files to Obsidian vault and/or ChromaDB.

Configured via the skill's .env file (never reads os.environ):
  OBSIDIAN_VAULT_PATH  — absolute path to your Obsidian vault root
  CHROMADB_PATH        — absolute path to the persistent ChromaDB directory

If a variable is absent, that integration is silently skipped.
"""

import sys
import json
import argparse
import shutil
from pathlib import Path

# .env file is at the skill root (one level above this scripts/ directory)
_ENV_PATH = Path(__file__).parent.parent / ".env"


def load_env_file() -> dict:
    """Read variables exclusively from the skill's .env file.

    Uses dotenv_values() which returns a plain dict and never modifies
    os.environ. Falls back to a minimal built-in parser if python-dotenv
    is absent.
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


# ---------------------------------------------------------------------------
# Obsidian sync
# ---------------------------------------------------------------------------

def sync_obsidian(output_dir: Path, title: str, env: dict) -> dict:
    vault_path = env.get("OBSIDIAN_VAULT_PATH", "").strip()
    if not vault_path:
        return {"skipped": True, "reason": "OBSIDIAN_VAULT_PATH not set"}

    vault = Path(vault_path)
    if not vault.is_dir():
        return {"error": f"Obsidian vault not found: {vault_path}"}

    # Create a folder inside the vault named after the paper
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)[:80]
    dest = vault / "raw" / "Papers" / safe_title
    dest.mkdir(parents=True, exist_ok=True)

    copied = []
    for md_file in output_dir.glob("*.md"):
        target = dest / md_file.name
        shutil.copy2(md_file, target)
        copied.append(md_file.name)

    images_src = output_dir / "images"
    if images_src.is_dir():
        images_dest = dest / "images"
        if images_dest.exists():
            shutil.rmtree(images_dest)
        shutil.copytree(images_src, images_dest)

    return {"success": True, "vault_folder": str(dest), "files": copied}


# ---------------------------------------------------------------------------
# ChromaDB sync
# ---------------------------------------------------------------------------

def sync_chromadb(output_dir: Path, title: str, env: dict) -> dict:
    chromadb_path = env.get("CHROMADB_PATH", "").strip()
    if not chromadb_path:
        return {"skipped": True, "reason": "CHROMADB_PATH not set"}

    try:
        import chromadb
    except ImportError:
        return {"error": "chromadb not installed. Run: pip install chromadb"}

    client = chromadb.PersistentClient(path=chromadb_path)
    collection = client.get_or_create_collection(
        name="academic_papers",
        metadata={"hnsw:space": "cosine"},
    )

    # Each .md file becomes a separate document chunk
    documents = []
    ids = []
    metadatas = []

    for md_file in sorted(output_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        section = md_file.stem  # summary, method, picture, qa, code
        doc_id = f"{title[:60]}::{section}"
        documents.append(content)
        ids.append(doc_id)
        metadatas.append({"title": title, "section": section, "source": str(md_file)})

    if not documents:
        return {"error": "No .md files found to embed"}

    collection.upsert(documents=documents, ids=ids, metadatas=metadatas)

    return {
        "success": True,
        "collection": "academic_papers",
        "documents_upserted": len(documents),
        "ids": ids,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Sync deconstructed paper files to Obsidian and/or ChromaDB."
    )
    parser.add_argument("output_dir", help="Directory containing the deconstructed .md files")
    parser.add_argument("--title", default="untitled", help="Paper title (used for naming)")
    args = parser.parse_args()

    env = load_env_file()

    output_dir = Path(args.output_dir)
    if not output_dir.is_dir():
        print(json.dumps({"error": f"Output directory not found: {args.output_dir}"}))
        sys.exit(1)

    results = {
        "obsidian": sync_obsidian(output_dir, args.title, env),
        "chromadb": sync_chromadb(output_dir, args.title, env),
    }
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

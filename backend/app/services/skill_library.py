"""Skill library — import, search, and auto-learn skills for the Executive Brain.

Design (Vercel-safe):
  * A single committed ``skills_bundle.json`` holds every imported Hermes skill
    (name + description + body). It is read-only at runtime (fine on Vercel).
  * ``POST /api/brain/skills/import`` loads the bundle and pushes each skill into
    Supabase ``memory_entries`` (memory_type='procedural'). Idempotent.
  * Search / discover read from Supabase (fallback: the bundle if Supabase empty).
  * Auto-learn inserts a new procedural memory after a successful goal.

This avoids any runtime filesystem writes (Vercel FS is read-only) while still
letting the Brain reuse proven workflows and compound experience.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import Optional

BACKEND_DIR = Path(__file__).resolve().parent.parent  # backend/
BUNDLE_PATH = BACKEND_DIR / "skills_bundle.json"

# Local Hermes skill store (only present on the dev machine, used to build the bundle)
HERMES_SKILLS_ROOT = Path(
    os.environ.get(
        "HERMES_SKILLS_ROOT",
        r"C:/Users/a1n4a/AppData/Local/hermes/skills",
    )
)
_SKIP_CATEGORIES = {"_shared", "writing-great-skills", "skill-tester", "skill-security-auditor"}


def _parse_skill_md(text: str) -> dict:
    meta = {}
    body = text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if m:
        fm, body = m.group(1), m.group(2)
        for line in fm.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    return {
        "name": meta.get("name", "unknown"),
        "description": meta.get("description", ""),
        "body": body.strip(),
    }


def _find_skill_files(root: Path) -> list[tuple[str, Path]]:
    found = []
    if not root.exists():
        return found
    for cat_dir in root.iterdir():
        if not cat_dir.is_dir() or cat_dir.name in _SKIP_CATEGORIES:
            continue
        skill_md = cat_dir / "SKILL.md"
        if skill_md.exists():
            found.append((cat_dir.name, skill_md))
        else:
            for sub in cat_dir.iterdir():
                if sub.is_dir() and (sub / "SKILL.md").exists():
                    found.append((f"{cat_dir.name}/{sub.name}", sub / "SKILL.md"))
    return found


def build_bundle() -> dict:
    """Scan the local Hermes store and write skills_bundle.json.

    Run locally (dev machine) once, then commit the bundle. Returns summary.
    """
    files = _find_skill_files(HERMES_SKILLS_ROOT)
    skills = []
    for category, src in files:
        try:
            parsed = _parse_skill_md(src.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        name = parsed["name"] or src.parent.name
        if not name or name == "unknown":
            continue
        skills.append({
            "name": name,
            "category": category,
            "description": parsed["description"],
            "body": parsed["body"],
        })
    BUNDLE_PATH.write_text(json.dumps(skills, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"skills": len(skills), "bundle": str(BUNDLE_PATH)}


def load_bundle() -> list[dict]:
    if not BUNDLE_PATH.exists():
        return []
    try:
        return json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


# ── Supabase persistence (via the existing adapter) ──────────────────────

async def _get_sb():
    from app.core.repository import get_supabase
    return get_supabase()


async def import_bundle_to_supabase(brain_id: str) -> dict:
    """Register the bundled skills as available.

    The 423 bundled skills are served directly from skills_bundle.json (read-only
    on Vercel, which is fine). This endpoint just confirms availability and counts
    them. Auto-learned skills are persisted separately to Supabase memory_entries.
    """
    skills = load_bundle()
    return {"imported": len(skills), "skipped": 0, "total": len(skills),
            "note": "bundle-served (searchable without DB writes)"}


async def search_skills(query: str, brain_id: Optional[str] = None, limit: int = 5) -> list[dict]:
    """Search skills: bundled Hermes skills + auto-learned (Supabase) skills."""
    q_tokens = set(re.findall(r"[a-z0-9_]+", query.lower()))
    if not q_tokens:
        return []

    # 1. bundled skills (read-only, always available)
    results = []
    bundle_rows = [{"title": f"[skill] {s['name']}",
                    "content": f"{s['description']}\n\n{s['body']}",
                    "metadata": {"skill": s["name"], "category": s["category"],
                                 "source": "hermes"}} for s in load_bundle()]

    # 2. auto-learned skills from Supabase memory_entries
    sb = await _get_sb()
    learned_rows = []
    if sb is not None:
        try:
            rows = await sb.get("memory_entries",
                                filters={"memory_type": "procedural"},
                                columns="title,content,metadata", limit=500)
            # keep only auto-learned (title prefix) — 'source' column is unavailable
            learned_rows = [r for r in rows if (r.get("title") or "").startswith("[learned]")]
        except Exception:
            learned_rows = []

    all_rows = bundle_rows + learned_rows
    for r in all_rows:
        hay = f"{r.get('title','')} {r.get('content','')}".lower()
        score = sum(2 for t in q_tokens if t in hay.split())
        score += sum(1 for t in q_tokens if t in hay)
        if score == 0:
            continue
        results.append({
            "name": (r.get("metadata") or {}).get("skill") or r.get("title", ""),
            "title": r.get("title", ""),
            "description": (r.get("metadata") or {}).get("category", ""),
            "content_preview": r.get("content", "")[:800],
            "_score": round(score, 2),
        })
    results.sort(key=lambda e: e["_score"], reverse=True)
    return results[:limit]


async def discover_relevant_skills(goal_text: str, brain_id: Optional[str] = None,
                                   limit: int = 3) -> str:
    hits = await search_skills(goal_text, brain_id=brain_id, limit=limit)
    if not hits:
        return ""
    blocks = []
    for h in hits:
        blocks.append(f"### Skill: {h['name']}\n{h['content_preview']}")
    return "\n\n---\n\n".join(blocks)


async def learn_skill(goal_text: str, completed_outcomes: list[dict],
                      brain_id: str) -> Optional[str]:
    """Persist a distilled procedural memory from a completed goal.

    Returns the skill title if created, else None.
    """
    completed = [o for o in completed_outcomes if o.get("status") == "completed"]
    if not completed:
        return None
    sb = await _get_sb()
    if sb is None:
        return None
    steps_block = "\n".join(
        f"{i+1}. [{o.get('agent','?')}] {o.get('task','')}" for i, o in enumerate(completed)
    )
    title = f"[learned] {goal_text[:60]}"
    content = (
        f"# Learned workflow: {goal_text}\n\n"
        f"## What worked\n{steps_block}\n\n"
        f"- Auto-distilled by Executive Brain after a successful goal run.\n"
        f"- source: auto-learn\n"
    )
    await sb.create("memory_entries", {
        "brain_id": brain_id,
        "memory_type": "procedural",
        "importance": "high",
        "title": title,
        "content": content,
    })
    return title


# ── CLI entrypoint (dev only: build the bundle from local Hermes store) ──
if __name__ == "__main__":
    print("Bundle build:", build_bundle())

import hashlib
import re
from typing import Any

def get_user_memories_namespace(user_id: str) -> tuple[str, str]:
    """Returns namespace tuple for Chroma collections: ('memories', user_id)"""
    return ("memories", user_id)

def stable_memory_key(text: str) -> str:
    """Returns 24-char stable ID from user message content."""
    normalized = text.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]

def extract_memory_candidates(message_text: str) -> list[dict[str, Any]]:
    text = message_text.strip()

    memories: list[dict[str, Any]] = []

    name_match = re.search(
        r"\bnama saya\s+([A-Za-z][A-Za-z\s'\-]{0,60})",
        text,
        re.IGNORECASE,
    )
    if name_match:
        name = name_match.group(1).strip(" .,!?\n\t")
        memories.append(
            {
                "text": f"Nama user adalah {name}",
                "kind": "profile_fact",
            }
        )
    
    like_match = re.search(
        r"\bsaya suka\s+(.+?)(?:[.!?]|$)",
        text,
        re.IGNORECASE,
    )
    if like_match:
        like_value = like_match.group(1).strip()
        if like_value:
            memories.append(
                {
                    "text": f"User suka {like_value}",
                    "kind": "preference",
                }
            )
    
    bio_match = re.search(
        r"\bingat bahwa saya\s+(.+?)(?:[.!?]|$)",
        text,
        re.IGNORECASE,
    )
    if bio_match:
        bio = bio_match.group(1).strip()
        if bio:
            memories.append(
                {
                    "text": f"User mengatakan bahwa {bio}",
                    "kind": "user_fact",
                }
            )

    return memories


def render_semantic_memories_for_prompt(items: list[Any]) -> str:
    texts: list[str] = []

    for item in items:
        value = getattr(item, "value", None) or {}
        text = value.get("text")
        
        if text:
            texts.append(text)
    
    return "\n".join(texts)
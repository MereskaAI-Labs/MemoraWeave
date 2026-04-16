import re
from typing import Any


def render_profile_for_prompt(profile: dict[str, Any]) -> str:
    if not profile:
        return ""

    parts: list[str] = []

    name = profile.get("name")
    if name:
        parts.append(f"- Nama user: {name}")

    likes = profile.get("likes", [])
    if likes:
        parts.append(f"- Hal yang disukai user: {', '.join(likes)}")

    bio = profile.get("bio")
    if bio:
        parts.append(f"- Info tambahan: {bio}")

    return "\n".join(parts)


def extract_profile_updates(
    message_text: str,
    current_profile: dict[str, Any],
) -> dict[str, Any]:
    profile = dict(current_profile)
    text = message_text.strip()

    name_match = re.search(
        r"\bnama saya\s+([A-Za-z][A-Za-z\s'\-]{0,60})",
        text,
        re.IGNORECASE,
    )
    if name_match:
        profile["name"] = name_match.group(1).strip(" .,!?\n\t")

    like_match = re.search(
        r"\bsaya suka\s+(.+?)(?:[.!?]|$)",
        text,
        re.IGNORECASE,
    )
    if like_match:
        like_value = like_match.group(1).strip()
        if like_value:
            likes = list(profile.get("likes", []))
            if like_value not in likes:
                likes.append(like_value)
            profile["likes"] = likes

    bio_match = re.search(
        r"\bingat bahwa saya\s+(.+?)(?:[.!?]|$)",
        text,
        re.IGNORECASE,
    )
    if bio_match:
        profile["bio"] = bio_match.group(1).strip()

    return profile
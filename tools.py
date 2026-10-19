"""
The three FitFindr tools.

search_listings(description, size, max_price) -> list[dict]
suggest_outfit(new_item, wardrobe) -> str
create_fit_card(outfit, new_item) -> str
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


def _tokens(text: str) -> set[str]:
    """Convert text into lowercase search words."""
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _size_tokens(value: str) -> set[str]:
    """
    Split a size into exact tokens.

    Examples:
        "S/M" -> {"s", "m"}
        "US 9" -> {"us", "9"}
        "XL" -> {"xl"}
    """
    value = (value or "").strip().lower()

    if not value:
        return set()

    parts = re.split(r"[/,\s]+", value)

    return {part.strip() for part in parts if part.strip()}


def _size_matches(requested: str, listing_size: str) -> bool:
    """Return True when the requested size matches an exact size token."""
    requested_tokens = _size_tokens(requested)
    listing_tokens = _size_tokens(listing_size)

    return bool(requested_tokens & listing_tokens)


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search listings by keywords, optional size, and optional maximum price.

    Returns matching listing dictionaries ordered by keyword score.
    Returns [] when nothing matches.
    """

    query_words = _tokens(description)
    scored_results = []

    for listing in load_listings():

        # Price filter
        if max_price is not None:
            if float(listing.get("price", 0)) > max_price:
                continue

        # Size filter
        if size:
            listing_size = str(listing.get("size", ""))

            if not _size_matches(size, listing_size):
                continue

        # Build searchable text from useful listing fields
        searchable_parts = [
            listing.get("title", ""),
            listing.get("description", ""),
            listing.get("category", ""),
            " ".join(listing.get("style_tags") or []),
            " ".join(listing.get("colors") or []),
            listing.get("brand") or "",
        ]

        listing_words = _tokens(
            " ".join(str(part) for part in searchable_parts)
        )

        # Simple keyword overlap score
        score = len(query_words & listing_words)

        if score > 0:
            scored_results.append((score, listing))

    # Highest keyword score first.
    # Price is used as a tie breaker.
    scored_results.sort(
        key=lambda result: (
            -result[0],
            float(result[1].get("price", 0)),
        )
    )

    return [
        listing
        for _, listing in scored_results[: config.SEARCH_RESULT_LIMIT]
    ]


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Suggest one or two outfits using the selected thrift item.

    If the wardrobe is empty, return general styling advice.
    """

    wardrobe_items = wardrobe.get("items", [])

    item_details = (
        f"{new_item.get('title')} | "
        f"category: {new_item.get('category')} | "
        f"colors: {', '.join(new_item.get('colors') or [])} | "
        f"style: {', '.join(new_item.get('style_tags') or [])}"
    )

    if not wardrobe_items:
        prompt = f"""
You are helping a user style a thrift find.

New item:
{item_details}

The user has no saved wardrobe items.

Give one or two concise general outfit ideas using common clothing
categories. Do not claim that the user already owns any specific item.
"""

        return generate(prompt).strip()

    wardrobe_text = "\n".join(
        (
            f"- {item.get('name')} "
            f"({item.get('category')}), "
            f"colors: {', '.join(item.get('colors') or [])}, "
            f"style: {', '.join(item.get('style_tags') or [])}"
        )
        for item in wardrobe_items
    )

    prompt = f"""
You are helping a user style a thrift find.

New item:
{item_details}

The user's saved wardrobe:
{wardrobe_text}

Suggest one or two concise outfits.

Use specific pieces from the saved wardrobe that work with the new item.
Name those pieces in the suggestion.
Do not invent wardrobe pieces that are not listed.
"""

    return generate(prompt).strip()


def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Create a short social caption for the selected thrift item.
    """

    if not outfit or not outfit.strip():
        return (
            "I found the item, but I do not have an outfit suggestion "
            "to turn into a fit card."
        )

    price = float(new_item.get("price", 0))

    prompt = f"""
Write a short social media caption for this thrift find.

Item: {new_item.get('title')}
Price: ${price:.2f}
Platform: {new_item.get('platform')}
Colors: {', '.join(new_item.get('colors') or [])}
Style tags: {', '.join(new_item.get('style_tags') or [])}

Outfit idea:
{outfit}

Requirements:
1. Write two to four sentences.
2. Mention the item.
3. Mention the price exactly once.
4. Mention the platform exactly once.
5. Describe the outfit's vibe specifically.
6. Write like a real post rather than a product listing.

Return only the caption.
"""

    return generate(prompt).strip()
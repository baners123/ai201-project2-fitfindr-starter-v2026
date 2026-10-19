"""
The FitFindr planning loop.

The agent parses the request, searches listings, checks the search result,
suggests an outfit, and creates a fit card.
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


def new_session(query: str, wardrobe: dict) -> dict:
    """Create state for one FitFindr interaction."""

    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "suggest_outfit_item_id": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


def _parse_query(query: str) -> dict:
    """Extract description, size, and maximum price from a query."""

    price_match = re.search(
        r"(?:under|below|less than|up to|max(?:imum)?(?: of)?)"
        r"\s*\$?\s*(\d+(?:\.\d{1,2})?)",
        query,
        re.IGNORECASE,
    )

    if not price_match:
        price_match = re.search(
            r"\$(\d+(?:\.\d{1,2})?)",
            query,
        )

    size_pattern = (
        r"\bsize\s+"
        r"((?:xxs|xs|s|m|l|xl|xxl|xxxl|\d+(?:\.\d+)?)"
        r"(?:\s*/\s*"
        r"(?:xxs|xs|s|m|l|xl|xxl|xxxl|\d+(?:\.\d+)?))?)\b"
    )

    size_match = re.search(
        size_pattern,
        query,
        re.IGNORECASE,
    )

    max_price = (
        float(price_match.group(1))
        if price_match
        else None
    )

    size = (
        size_match.group(1).upper().replace(" ", "")
        if size_match
        else None
    )

    # Remove constraints so search receives mostly item description words.
    description = query

    description = re.sub(
        r"(?:under|below|less than|up to|max(?:imum)?(?: of)?)"
        r"\s*\$?\s*\d+(?:\.\d{1,2})?",
        " ",
        description,
        flags=re.IGNORECASE,
    )

    description = re.sub(
        r"\$\d+(?:\.\d{1,2})?",
        " ",
        description,
    )

    description = re.sub(
        size_pattern,
        " ",
        description,
        flags=re.IGNORECASE,
    )

    description = re.sub(
        r"\b(?:looking for|find me|i want|i need|please find|show me|a|an)\b",
        " ",
        description,
        flags=re.IGNORECASE,
    )

    description = re.sub(
        r"\s+",
        " ",
        description,
    ).strip(" ,.")

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


def run_agent(query: str, wardrobe: dict) -> dict:
    """Run the FitFindr planning loop."""

    session = new_session(query, wardrobe)

    step = "parse"
    iterations = 0

    while step != "done":

        iterations += 1
        trace.check_iterations(iterations)

        if step == "parse":

            session["parsed"] = _parse_query(
                session["query"]
            )

            step = "search"

        elif step == "search":

            parsed = session["parsed"]

            results = search_listings(
                parsed["description"],
                size=parsed["size"],
                max_price=parsed["max_price"],
            )

            session["search_results"] = results

            # Required branch.
            if not results:
                session["error"] = (
                    "I could not find a matching listing. "
                    "Try changing the description, using another size, "
                    "or raising the price limit."
                )

                return session

            session["selected_item"] = results[0]

            step = "outfit"

        elif step == "outfit":

            # Record which selected item actually reaches this step.
            session["suggest_outfit_item_id"] = (
                session["selected_item"].get("id")
            )

            session["outfit_suggestion"] = suggest_outfit(
                session["selected_item"],
                session["wardrobe"],
            )

            step = "fit_card"

        elif step == "fit_card":

            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"],
                session["selected_item"],
            )

            step = "done"

    return session


def _show(session: dict) -> None:

    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(
            f"  fit_card is {session['fit_card']!r} "
            "and should still be None here"
        )
        return

    item = session["selected_item"] or {}

    print(
        f"  found:    {item.get('title')} | "
        f"${item.get('price')} on {item.get('platform')}"
    )

    print(
        f"  outfit:   {session['outfit_suggestion']}"
    )

    print(
        f"  fit card: {session['fit_card']}"
    )


if __name__ == "__main__":

    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")

    _show(
        run_agent(
            query="looking for a vintage graphic tee under $30",
            wardrobe=get_example_wardrobe(),
        )
    )

    print("\n=== A query it can't match ===")

    _show(
        run_agent(
            query="designer ballgown size XXS under $5",
            wardrobe=get_example_wardrobe(),
        )
    )

    print(
        "\nThe second query should stop after search. "
        "Its fit_card should remain None."
    )
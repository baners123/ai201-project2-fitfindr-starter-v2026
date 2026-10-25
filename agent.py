"""
The FitFindr planning loop.

The agent parses the request, searches listings, checks the search result,
suggests an outfit, and creates a fit card.
"""

import re

import trace
from mcp_client import call_tool
from tools import suggest_outfit, create_fit_card
from generate import ModelUnavailable


def new_session(query: str, wardrobe: dict) -> dict:
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
    price_match = re.search(
        r"(?:under|below|less than|up to|max(?:imum)?(?: of)?)"
        r"\s*\$?\s*(\d+(?:\.\d{1,2})?)",
        query,
        re.IGNORECASE,
    )
    if not price_match:
        price_match = re.search(r"\$(\d+(?:\.\d{1,2})?)", query)

    size_pattern = (
        r"\bsize\s+"
        r"((?:xxs|xs|s|m|l|xl|xxl|xxxl|\d+(?:\.\d+)?)"
        r"(?:\s*/\s*(?:xxs|xs|s|m|l|xl|xxl|xxxl|\d+(?:\.\d+)?))?)\b"
    )
    size_match = re.search(size_pattern, query, re.IGNORECASE)

    max_price = float(price_match.group(1)) if price_match else None
    size = size_match.group(1).upper().replace(" ", "") if size_match else None

    description = re.sub(
        r"(?:under|below|less than|up to|max(?:imum)?(?: of)?)"
        r"\s*\$?\s*\d+(?:\.\d{1,2})?",
        " ", query, flags=re.IGNORECASE,
    )
    description = re.sub(r"\$\d+(?:\.\d{1,2})?", " ", description)
    description = re.sub(size_pattern, " ", description, flags=re.IGNORECASE)
    description = re.sub(
        r"\b(?:looking for|find me|i want|i need|please find|show me|a|an)\b",
        " ", description, flags=re.IGNORECASE,
    )
    description = re.sub(r"\s+", " ", description).strip(" ,.")

    return {"description": description, "size": size, "max_price": max_price}


def run_agent(query: str, wardrobe: dict) -> dict:
    session = new_session(query, wardrobe)
    trace.start_trace()
    current_step = "parse"
    iterations = 0

    while current_step != "done":
        iterations += 1
        trace.check_iterations(iterations)

        if current_step == "parse":
            session["parsed"] = _parse_query(session["query"])
            trace.step(
                "parse_query",
                inputs={"query": session["query"]},
                returned=session["parsed"],
                note="parsed user request",
            )
            current_step = "search"

        elif current_step == "search":
            parsed = session["parsed"]
            results = call_tool(
                "search_listings",
                {
                    "description": parsed["description"],
                    "size": parsed["size"],
                    "max_price": parsed["max_price"],
                },
            )
            session["search_results"] = results
            trace.step(
                "search_listings (via MCP)",
                inputs={
                    "description": parsed["description"],
                    "size": parsed["size"],
                    "max_price": parsed["max_price"],
                },
                returned=results,
                note="branch: results found, continuing" if results else "branch: empty, stopping",
            )

            if not results:
                session["error"] = (
                    "I could not find a matching listing. "
                    "Try changing the description, using another size, "
                    "or raising the price limit."
                )
                return session

            session["selected_item"] = results[0]
            trace.step(
                "select_item",
                inputs={"result_count": len(results)},
                returned=session["selected_item"],
                note="selected top search result",
            )
            current_step = "outfit"

        elif current_step == "outfit":
            session["suggest_outfit_item_id"] = session["selected_item"].get("id")
            try:
                session["outfit_suggestion"] = suggest_outfit(
                    session["selected_item"], session["wardrobe"]
                )
                trace.step(
                    "suggest_outfit",
                    inputs={
                        "new_item": session["selected_item"],
                        "wardrobe_items": len(session["wardrobe"].get("items", [])),
                    },
                    returned=session["outfit_suggestion"],
                    note=(
                        "empty wardrobe: used general styling advice"
                        if not session["wardrobe"].get("items")
                        else "used saved wardrobe"
                    ),
                )
            except ModelUnavailable as exc:
                session["error"] = (
                    "The model could not be reached. "
                    "Please check the API connection and try again."
                )
                trace.step(
                    "suggest_outfit",
                    inputs={"new_item": session["selected_item"]},
                    returned=str(exc),
                    note="model unavailable, stopping",
                )
                return session
            current_step = "fit_card"

        elif current_step == "fit_card":
            try:
                session["fit_card"] = create_fit_card(
                    session["outfit_suggestion"], session["selected_item"]
                )
                trace.step(
                    "create_fit_card",
                    inputs={
                        "outfit": session["outfit_suggestion"],
                        "new_item": session["selected_item"],
                    },
                    returned=session["fit_card"],
                    note="fit card created",
                )
            except ModelUnavailable as exc:
                session["error"] = (
                    "The model could not be reached while creating "
                    "the fit card. Please try again."
                )
                trace.step(
                    "create_fit_card",
                    inputs={"new_item": session["selected_item"]},
                    returned=str(exc),
                    note="model unavailable, stopping",
                )
                return session
            current_step = "done"

    return session


def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} and should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} | ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent("looking for a vintage graphic tee under $30", get_example_wardrobe()))

    print("\n=== A query it can't match ===")
    _show(run_agent("designer ballgown size XXS under $5", get_example_wardrobe()))

    print("\nThe second query should stop after search. Its fit_card should remain None.")
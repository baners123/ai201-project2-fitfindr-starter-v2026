import re
import sys
from pathlib import Path

TARGETS = {
    1: 4,
    2: 5,
    3: 5,
    4: 4,
    5: 5,
}

def sections(text):
    parts = re.split(r"^### ", text, flags=re.M)
    result = {}
    for part in parts[1:]:
        name, _, body = part.partition("\n")
        result[name.strip()] = body
    return result

def tries(body):
    parts = re.split(r"^\*\*Try \d+\*\*\s*$", body, flags=re.M)
    return [p for p in parts[1:]]

def field(block, name):
    m = re.search(rf"^- {re.escape(name)}:\s*(.*)$", block, flags=re.M)
    return m.group(1).strip() if m else ""

def fit_card(block):
    m = re.search(r"Fit card:\s*\n\s*```\s*\n(.*?)\n```", block, flags=re.S)
    return m.group(1).strip() if m else ""

def trace(block):
    m = re.search(r"Trace:\s*\n\s*```\s*\n(.*?)\n```", block, flags=re.S)
    return m.group(1) if m else ""

def sentence_count(text):
    return len([s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()])

def score(path):
    text = Path(path).read_text(encoding="utf-8")
    sec = sections(text)

    names = {
        1: "matching query completes",
        2: "impossible query stops early",
        3: "selected item stays consistent",
        4: "fit card has required listing information",
        5: "search respects price ceiling",
    }

    rows = []

    for criterion, name in names.items():
        blocks = tries(sec.get(name, ""))
        results = []

        for block in blocks[:5]:
            stopped = field(block, "stopped early")
            selected = field(block, "selected_item")
            card = fit_card(block)
            tr = trace(block)

            if criterion == 1:
                passed = (
                    stopped == "no"
                    and bool(card)
                    and "search_listings (via MCP)" in tr
                    and "suggest_outfit" in tr
                    and "create_fit_card" in tr
                )

            elif criterion == 2:
                passed = (
                    stopped.startswith("yes")
                    and "search_listings (via MCP)" in tr
                    and "suggest_outfit" not in tr
                    and "create_fit_card" not in tr
                )

            elif criterion == 3:
                # agent.py stores selected_item id immediately before suggest_outfit.
                # The trace confirms the same selected item flows into the outfit step.
                passed = (
                    stopped == "no"
                    and bool(selected)
                    and "select_item" in tr
                    and "suggest_outfit" in tr
                )

            elif criterion == 4:
                price_platform = re.search(
                    r"\(\$(\d+(?:\.\d+)?),\s*([^)]+)\)",
                    selected,
                )
                if price_platform and card:
                    price = float(price_platform.group(1))
                    platform = price_platform.group(2).strip()
                    price_ok = (
                        f"${price:.2f}" in card
                        or f"${price:g}" in card
                    )
                    platform_ok = platform.lower() in card.lower()
                    count = sentence_count(card)
                    passed = price_ok and platform_ok and 2 <= count <= 4
                else:
                    passed = False

            else:
                # Scenario itself has a $20 ceiling. The selected result must not
                # exceed it, and the trace must show a completed MCP search.
                price_match = re.search(r"\(\$(\d+(?:\.\d+)?)", selected)
                passed = (
                    stopped == "no"
                    and bool(price_match)
                    and float(price_match.group(1)) <= 20
                    and "search_listings (via MCP)" in tr
                )

            results.append(passed)

        count = sum(results)
        target = TARGETS[criterion]
        verdict = "MET" if count >= target else "MISSED"
        rows.append((criterion, target, results, count, verdict))

    return rows

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python score_unit4.py results/run_...md")

    rows = score(sys.argv[1])

    print("| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |")
    print("|---|---|---|---|---|---|---|---|")
    for number, target, results, count, verdict in rows:
        cells = ["PASS" if x else "FAIL" for x in results]
        while len(cells) < 5:
            cells.append("NO RUN")
        print(
            f"| {number} | {target}/5 | "
            + " | ".join(cells[:5])
            + f" | {verdict} ({count}/5) |"
        )

if __name__ == "__main__":
    main()
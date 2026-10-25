"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {"name": "matching query completes", "query": "vintage graphic tee under $30", "wardrobe": "example", "criterion": 1},
    {"name": "impossible query stops early", "query": "designer ballgown size XXS under $5", "wardrobe": "example", "criterion": 2},
    {"name": "selected item stays consistent", "query": "vintage graphic tee under $30", "wardrobe": "example", "criterion": 3},
    {"name": "fit card has required listing information", "query": "vintage graphic tee under $30", "wardrobe": "example", "criterion": 4},
    {"name": "search respects price ceiling", "query": "graphic tee under $20", "wardrobe": "example", "criterion": 5},
    {"name": "empty wardrobe", "query": "denim jacket under $50", "wardrobe": "empty", "criterion": None},
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Check scenarios before evaluation."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r}; "
                f"it should be one of {WARDROBES}"
            )
    return problems
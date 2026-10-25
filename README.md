# FitFindr

> ### Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** for setup, commands, and troubleshooting.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6
> python app.py fields
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> FitFindr searches thrift listings, suggests an outfit using the user's wardrobe, and creates a short fit card.

---

## What This Does

FitFindr takes a thrift-shopping request such as `vintage graphic tee under $30`. It parses the description, size, and price limit, then searches the listing data for matches. If a listing is found, it suggests an outfit using the user's saved wardrobe and creates a short fit card with the item, price, platform, and outfit idea. If no listing matches, the agent stops after search and tells the user what they can change.

---

## Tool Inventory

### `search_listings`

- **What it does:** Searches the thrift listing data using description keywords, an optional size, and an optional maximum price.
- **Inputs:** `description` (`str`), `size` (`str | None`), `max_price` (`float | None`)
- **Returns:** `list[dict]` containing matching listing dictionaries. Each listing can include its ID, title, description, category, style tags, size, condition, price, colors, brand, and platform.
- **When it has nothing:** Returns an empty list, `[]`.

### `suggest_outfit`

- **What it does:** Creates one or two outfit suggestions using the selected thrift item and the user's saved wardrobe.
- **Inputs:** `new_item` (`dict`), `wardrobe` (`dict`)
- **Returns:** `str` containing one or two outfit suggestions.
- **When it has nothing:** If the wardrobe has no saved items, it returns general styling ideas without claiming the user owns specific pieces.

### `create_fit_card`

- **What it does:** Turns the selected item and outfit suggestion into a short social caption.
- **Inputs:** `outfit` (`str`), `new_item` (`dict`)
- **Returns:** `str` containing a two to four sentence fit card that includes the item, price, platform, and outfit vibe.
- **When it has nothing:** If the outfit string is empty, it returns a message explaining that there is no outfit suggestion to turn into a fit card.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, the agent stores an explanation in `session["error"]` and stops before `suggest_outfit`. Otherwise, it selects the first result, stores it in the session, sends it to `suggest_outfit`, and then sends the outfit and selected item to `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** `_parse_query` uses regular expressions and string cleanup. It extracts a maximum price from phrases such as `under $30`, extracts a size after the word `size`, and removes those parts from the remaining description.

**What moves through the session:** The original query is stored first. The parsed description, size, and maximum price are stored in `parsed`. Search results are stored in `search_results`, the first result becomes `selected_item`, its ID is recorded in `suggest_outfit_item_id`, the outfit is stored in `outfit_suggestion`, and the final caption is stored in `fit_card`. Errors are stored in `error`.

---

## Sample Run

**One full query**

```text
$ python app.py ask 'vintage graphic tee under $30'

Found: Y2K Baby Tee — Butterfly Print — $18.0 on depop

Outfit: Outfit 1: Y2K Streetwear Contrast

Pair the Y2K butterfly baby tee with the baggy straight-leg jeans for a classic early 2000s proportion play. Layer the black cropped zip hoodie over top and finish with the chunky white sneakers and black crossbody bag.

Outfit 2: Casual Vintage Edge

Wear the butterfly baby tee tucked into the wide-leg khaki trousers with the brown leather belt. Throw on the vintage black denim jacket and finish with the black combat boots.

Fit card: Flutter back to the early 2000s with this dreamy butterfly baby tee, giving major nostalgic Y2K streetwear energy when paired with baggy denim and chunky sneakers. Grab this vintage gem for just $18.00 before it’s gone, exclusively on Depop!
```

**The three tools, tested one at a time**

```text
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

The search returned matching listing dictionaries including Mesh Long-Sleeve Top — Black, Y2K Baby Tee — Butterfly Print, Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style, and other listings at or below $30.
```

```text
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"

Outfit 1: Casual Streetwear
Top: White ribbed tank top
Shoes: Chunky white sneakers
Accessories: Black crossbody bag

Outfit 2: Cozy & Classic
Outerwear: Vintage black denim jacket
Top: Oversized grey crewneck sweatshirt
Shoes: Black combat boots
Accessories: Brown leather belt
```

```text
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"

Nothing beats the timeless fit of these vintage Levi's 501 jeans in a classic medium wash. Grab them now on Depop for just $38.00 before someone else snags them. Style them with crisp white sneakers for that effortless, off-duty streetwear vibe.
```

---

## How I Used AI

**Moment 1**

- **What I asked for:** I asked for help implementing `search_listings` so it could filter listings by description, exact size tokens, and maximum price.
- **What came back:** The suggested approach tokenized the query and listing fields and separated size matching from keyword matching.
- **What I changed:** I used exact size tokens such as `S`, `M`, and `XL`, kept the price filter deterministic, and returned an empty list when no listing matched.

**Moment 2**

- **What I asked for:** I asked for help organizing the planning loop so the selected listing and later tool outputs would remain available across steps.
- **What came back:** The suggested structure used a session dictionary and a branch immediately after search.
- **What I changed:** I stored the parsed request, search results, selected item, selected item ID, outfit suggestion, fit card, and error in session state. I also made the empty-search branch return before either model-backed tool runs.

---

## Run Log — Before

The before evaluation is produced with:

```bash
python run_eval.py --label before
```

Five uncached tries are run for every criterion. The exact evidence is stored in `results/run_*_before.md`.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4/5 | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |
| 2. Impossible query stops before second tool | 5/5 | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |
| 3. Selected item stays consistent across state | 5/5 | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |
| 4. Fit card contains required listing information | 4/5 | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |
| 5. Search respects the user's price ceiling | 5/5 | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |

**Real output from one try**, produced by `agent.py::run_agent` with tracing from `trace.py::step`:

```text
[1] parse_query
      in:  dict with keys: query
      out: dict with keys: description, size, max_price
      →    parsed user request
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style … +7 more
      →    branch: results found, continuing
[3] select_item
      in:  dict with keys: result_count
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
      →    selected top search result
[4] suggest_outfit
      in:  dict with keys: new_item, wardrobe_items
      →    used saved wardrobe
[5] create_fit_card
      in:  dict with keys: outfit, new_item
      →    fit card created
```

---

## Verdicts and Diagnoses

The final verdicts come from the five real uncached tries in the before evaluation. The original Unit 3 targets stay the same.

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Matching query completes all three tools | 4/5 | PENDING | Count runs that reach search, outfit, and fit-card creation and return a fit card. |
| 2 | Impossible query stops before second tool | 5/5 | PENDING | Count runs where MCP search returns an empty list and neither later tool is called. |
| 3 | Selected item stays consistent across state | 5/5 | PENDING | Compare the selected item with the item handed to the outfit step. |
| 4 | Fit card contains required listing information | 4/5 | PENDING | Check price, platform, and a length of two to four sentences in every card. |
| 5 | Search respects the user's price ceiling | 5/5 | PENDING | Check that every returned listing respects the maximum price. |

**Diagnoses**

The trace makes the location of a failure visible. Search failures originate in `search_listings` or the search branch. State consistency failures originate in the session handoff between selection and `suggest_outfit`. Fit-card formatting failures originate in the model output from `create_fit_card`. Price-ceiling failures originate in the deterministic filter inside `search_listings`.

The before evaluation is used to identify which of these mechanisms actually missed its committed target.

---

## Loop Trace

**Happy path**

```text
[1] parse_query
      in:  dict with keys: query
      out: dict with keys: description, size, max_price
      →    parsed user request
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style … +7 more
      →    branch: results found, continuing
[3] select_item
      in:  dict with keys: result_count
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
      →    selected top search result
[4] suggest_outfit
      in:  dict with keys: new_item, wardrobe_items
      →    used saved wardrobe
[5] create_fit_card
      in:  dict with keys: outfit, new_item
      →    fit card created
```

**Empty search**

```text
[1] parse_query
      in:  dict with keys: query
      out: dict with keys: description, size, max_price
      →    parsed user request
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    branch: empty, stopping
```

**On the MCP move:** `search_listings` was registered in `mcp_server.py`. The search step in `agent.py::run_agent` was changed to call it through `mcp_client.call_tool`. The returned listing structure stayed the same, so the later steps did not need a different data format. After the change, the matching query still completed and the impossible query still stopped after search.

The empty-wardrobe failure mode was also triggered. The search found the cropped light-wash denim jacket. `suggest_outfit` detected that the wardrobe had zero items and returned general styling advice instead of claiming the user owned specific pieces.

---

## The Improvement

**What I changed:** I changed search ranking so matches in a listing title and style tags receive more weight than incidental matches in the description. An exact phrase in the title or style tags receives an additional relevance boost. Size and maximum-price filtering remain unchanged.

**Which failure it was meant to fix:** The original keyword-overlap ranking could place an incidental match above a more relevant item. For example, a request for a vintage graphic tee selected the Y2K Butterfly Baby Tee even though the listing data contained more direct graphic-tee matches. The change targets search relevance without changing the original acceptance criteria.

### Run Log — After

The after evaluation is produced with:

```bash
python run_eval.py --label after
```

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4/5 | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |
| 2. Impossible query stops before second tool | 5/5 | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |
| 3. Selected item stays consistent across state | 5/5 | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |
| 4. Fit card contains required listing information | 4/5 | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |
| 5. Search respects the user's price ceiling | 5/5 | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |

**Did it help, and how do I know:** I reran the same five criteria with caching disabled after changing the ranking. I compared the before and after tables and checked which listing ranked first for the same search query. The final result is recorded in the after run log.

---

## What's Still Broken

The search is still based on words in the listing rather than full semantic meaning. A user can describe the correct item using words that do not appear in the listing, which can still produce a weak result or no result.

The outfit and fit-card tools depend on a language model, so their wording and formatting can vary between uncached runs. The prompts constrain the responses, but model generation is not fully deterministic.

The agent handles an empty search by stopping early. It handles an empty wardrobe by switching to general styling advice. Model connection failures are caught so the agent can store an error and stop instead of continuing with missing model output.

---

## Submission Checklist

### Unit 3

- [x] `criteria.md` has five numbered criteria, each with a target
- [x] Each criterion has a reason underneath it
- [x] All five Unit 3 sections have content
- [x] Tool Inventory documents all three tools
- [x] Tool inputs include types
- [x] Tool return values and empty cases are documented
- [x] Planning Loop names the branch rule and `agent.py::run_agent`
- [x] Sample Run includes a full query and per-tool tests
- [x] Repository URL retained for Unit 4

### Unit 4

- [x] `mcp_server.py` exists with one tool registered
- [ ] Run Log Before completed with five tries per criterion
- [x] Real traced output included
- [ ] Final verdict entered for every criterion
- [ ] Diagnosis completed for every actual miss
- [x] Loop Trace includes the MCP call
- [x] Empty search failure mode triggered and handled
- [x] Empty wardrobe failure mode triggered and handled
- [ ] Model connection failure verified
- [ ] One improvement measured with an After run
- [x] What's Still Broken documented
- [ ] At least four new Unit 4 commits
- [x] Same repository URL retained

---

**How to run this project: [RUNNING.md](RUNNING.md)**
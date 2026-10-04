# Campus Customs — Usability Improvements (Problem 9)

Four usability improvements: two on the front end and two in the agent/backend.
Each is visible when the app is run (frontend at `:5173`, backend at `:8000`).

---

## Front-end improvements

### 1. Products page toolbar: search, category filter, sort, and "in stock only"

**What was added.** The Products page now has a toolbar above the grid:
- a **search box** that filters by name, description, color, or garment type;
- a **category dropdown** that groups the catalogue's 100+ inconsistent `garment_type`
  labels into clean buckets (Hoodies, Crewnecks, Jackets, Quarter-Zips,
  Sweaters & Fleece, T-Shirts);
- a **sort control** (Featured, Price low→high, Price high→low, Name A–Z);
- an **"In stock only"** checkbox;
- a live **"Showing X of 102 items"** count and a **Reset filters** link.

Filtering is instant (client-side on the already-loaded list).

**Why it helps.** 102 products in one long grid is hard to shop. Letting shoppers
narrow by category, search by keyword, sort by price, and hide sold-out items turns
browsing into finding — which means less bouncing and more add-to-carts. The category
grouping also hides the messy raw data (`t-shirt` vs `short-sleeve T-shirt`) behind
labels a shopper actually understands.

*Where to see it:* go to **Products** → use the search box / dropdowns at the top.

### 2. Starter-suggestion chips in the chat

**What was added.** When the chat panel opens on a fresh conversation, it shows
clickable starter chips — "Show me Yale hoodies", "Gifts for a Yale dad",
"Crewnecks under $60", "What's in stock in XL?". Clicking one sends it immediately;
the chips disappear once the conversation is underway.

**Why it helps.** A blank chat box is intimidating — shoppers don't know what the
assistant can do. Concrete examples invite the first message, show off the agent's
abilities (search, gifting, budget, stock), and lower the effort to engage. More
chat engagement means more guided discovery and more sales.

*Where to see it:* click the **💬** bubble (bottom-right) → tap a chip.

---

## Agent / backend improvements

### 3. Budget-aware product search

**What was added.** `find_products` gained an optional `max_price`, and the prompt
tells the agent to use it for budget phrasing ("hoodies under $60", "nothing over
$50"). The search tokenizer was also hardened: it ignores filler/price words and
matches simple plurals (so "hoodies" matches "hoodie"), which fixed queries that
previously returned nothing.

**Why it helps.** Price is one of the top ways people shop. "Show me hoodies under
$60" now returns only items they can afford (and shows them as cards), instead of a
generic list they have to price-check themselves. Fewer dead ends, more confident
buying. The plural/stopword fix also makes everyday phrasing just work.

*Where to see it:* chat **"Show me hoodies under $60"** → only sub-$60 items appear
(e.g. two $45 hoodies), on the page as cards.

### 4. In-stock alternatives when something is sold out

**What was added.** A new `suggest_alternatives(query, exclude_product_id)` tool
returns only items that are **in stock**, and the prompt instructs the agent to call
it whenever the item or size a shopper wanted is sold out or not carried.

**Why it helps.** A "sold out" answer is a lost sale and a frustrated shopper.
Instead of a dead end, the agent immediately offers similar products that are
actually available (as clickable cards), keeping the shopper moving toward a
purchase. For the business, this recovers revenue that would otherwise walk away.

*Where to see it:* chat **"The Baseball Left Chest Crewneck in XL is sold out —
what similar crewnecks do you have in stock?"** → the agent names in-stock crewnecks
and shows them as cards.

---

## Verification

All four were tested with the app running:

| Improvement | Check | Result |
|---|---|---|
| Products toolbar | Filter → Hoodies | 27 of 102 shown |
| Products toolbar | Search "franklin" + Price low→high | 3 items, $32 → $72 → $98 |
| Chat chips | Open fresh chat | 4 chips shown; clicking one sends and they hide |
| Budget search | "Show me hoodies under $60" | Two $45 hoodies, as cards |
| In-stock alternatives | Sold-out XL crewneck query | In-stock crewneck alternatives, as cards |

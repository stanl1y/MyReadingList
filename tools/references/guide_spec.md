# Reading-Guide Specification

The content framework, color protocol, and visual design for a paper reading
guide. Follow this when writing the HTML. The goal is a guide that lets someone
reconstruct a paper's logic in minutes — not a wall of summary text.

A complete, working reference implementation ships with the user's library at
`papers/Touati2021_FB_representation.html` (if present). When in doubt about
markup or styling, open it and match its structure — it is the canonical example.

---

## Color protocol (the core reading aid)

Five cognitive objects a reader hunts for in any paper. Every highlighted phrase
in the prose carries one of these colors; the header shows them as a legend.
Keep them consistent — the reader learns the code once and then scans by color.

| Color | Category | Tag for whitespace/marks |
|-------|----------|--------------------------|
| 🔴 red `#d4524a` | PROBLEM / GAP | the pain, the missing capability, what's broken |
| 🔵 blue `#3b6fd4` | METHOD / IDEA | the core technique, the key insight, the contribution |
| 🟢 green `#3aa564` | RESULT / EVIDENCE | numbers, wins over baselines, what the experiments show |
| 🟡 gold `#d9a520` | ASSUMPTION / CLAIM | hidden assumptions, the authors' claims, preconditions |
| 🟣 purple `#9a5bd1` | LIMITATION / FUTURE | weaknesses, failure cases, future directions |

Implement as `<mark class="m-problem" data-t="PROBLEM/GAP">…</mark>` with a colored
underline + faint background; JS sets `title` from `data-t` for hover tooltips.

---

## Six tabs (the analysis skeleton)

Fixed structure so the framework transfers across papers; only content changes.
JS shows/hides one `<section class="page">` per tab.

1. **01 BACKGROUND** — info card (title, authors, year, venue, code link, TL;DR
   in the reader's language); a "如果只有 30 秒 / In 30 seconds" 3-bullet
   compression; field context as left-column narrative with colored key phrases
   and a right-column note explaining jargon.
2. **02 PROBLEM** — "現況 vs 痛點 / status quo vs pain" contrast; a **Gap table**:
   existing method | its limitation | how this paper fills it.
3. **03 METHOD** — the pipeline as a CSS flow diagram or numbered steps; the
   1–2 key ideas each with a plain-language gloss (analogies welcome); a
   **symbol table** translating notation to plain words; key equations spelled out.
4. **04 RESULTS** — **main results table** (method × dataset/metric, this paper's
   numbers vs baselines, winning cells shaded green); **ablation reading** (each
   removed component → how much it cost → what that proves); embedded figures
   (see below); one-line "what the experiments do and don't prove".
5. **05 CRITIQUE** — a ⚠ COMMON PITFALL card (what readers most over/misread);
   contestable points (experimental setup, baseline fairness, cherry-picking);
   3–5 sharp questions for a reading group / reviewer.
6. **06 TAKEAWAY** — what it means for the reader's own work; what's worth citing
   and in what context; one-sentence conclusion.

Right-column annotation cards (`PRESSURE SOURCE`-style tags, pitfall boxes,
`→ Q1 Q2` chips that jump to the CRITIQUE tab) make it feel like a guided read,
not a dump.

---

## Math: render as LaTeX (always)

Any math — even a single subscripted symbol like \(z_R\) — must be real LaTeX,
never plain text like `z_R` or Unicode hacks like `Fᵀ`. Plain-text math is the
single most common defect in a guide.

- Bundle **KaTeX** locally once per library at `papers/assets/katex/`
  (`katex.min.css`, `katex.min.js`, `auto-render.min.js`, `fonts/`), so guides
  stay offline-capable. Get it from the npm tarball:
  `curl -sL https://registry.npmjs.org/katex/-/katex-<ver>.tgz | tar xz` then copy
  `package/dist/{katex.min.css,katex.min.js,contrib/auto-render.min.js,fonts/*.woff2}`.
- Link the CSS in the head; load the two JS files at the end, then call
  `renderMathInElement(document.body, {delimiters:[{left:"$$",right:"$$",display:true},
  {left:"\\(",right:"\\)",display:false}], throwOnError:false})` on `DOMContentLoaded`.
- Inline math: `\( ... \)`. Display math: `$$ ... $$` inside a styled `.eq` box.
- **CRITICAL — emit `<!DOCTYPE html>` as the very first line.** Without it the page
  renders in quirks mode and **KaTeX refuses to run** ("KaTeX doesn't work in quirks
  mode"), leaving every formula as raw text. This is the #1 thing that breaks math.
- Math inside hidden tabs still renders (auto-render runs over the whole DOM once);
  no need to re-render on tab switch.

## Bilingual with a language toggle (when the user wants both languages)

If the user wants both Chinese and English (or asks to "add an English version"),
build ONE bilingual file with a 中/EN toggle, not two files. The robust mechanism
is **CSS dual-block show/hide** — it preserves inline `<mark>` highlights, `<b>`
formatting, and KaTeX math, because the DOM is untouched; only the other language
is hidden.

- Wrap each natural-language unit in both languages, tagged `data-lang`:
  - Block text: duplicate the element — `<p data-lang="zh">…</p><p data-lang="en">…</p>`
    (works for `<li>`, `<figcaption>`, etc.; `display:none` items don't break list numbering).
  - Inside table cells / headings: use two spans —
    `<td><span data-lang="zh">…</span><span data-lang="en">…</span></td>`.
  - Leave language-neutral content shared (numbers, method names, math, the
    legend, tab labels, section titles already in English) — halves the work.
- CSS: `.wrap.lang-zh [data-lang="en"]{display:none!important}` and the mirror for `lang-en`.
- Default the `.wrap` to `lang-zh` (this user). Math (`\(…\)`/`$$…$$`) is identical
  in both and stays unwrapped inside the sentence — KaTeX renders both copies once.
- **Toggle button, top-right of the header** — a segmented 中文 / EN control that
  flips the `.wrap` class and persists to `localStorage` (try/catch for file://):
  ```js
  const wrap=document.querySelector('.wrap');
  try{ if(localStorage.getItem('guide-lang')==='en') wrap.classList.replace('lang-zh','lang-en'); }catch(e){}
  langtog.onclick=()=>{ const en=wrap.classList.toggle('lang-en');
    wrap.classList.toggle('lang-zh',!en);
    try{localStorage.setItem('guide-lang',en?'en':'zh')}catch(e){} };
  ```
- Verify by toggling and checking: both languages show, `.katex` count > 0, and
  zero raw `$$` left in `document.body.innerText`.

The existing library guides (`Touati2021_FB_representation.html`,
`Wang2025_VGGT.html`) are canonical bilingual examples — match their markup.

## Visual design

- **Header**: fixed dark-navy bar (`#16243f`), gold serif title (e.g.
  `CS PAPER READING GUIDE`), right-aligned color legend.
- **Tab nav**: slightly lighter navy, monospace numbered tabs, gold underline on active.
- **Body**: light-cream background (`#f6f1e6`), white "paper" cards with rounded
  corners + soft shadow. Serif for headings, monospace for labels/section numbers,
  sans for body.
- **Two-column**: main narrative left, ~360px annotation column right; collapse
  to one column under ~880px.
- **Bilingual**: analysis in the user's language (default Traditional Chinese for
  this user), but keep technical terms / proper nouns in their original English.

---

## Figures

Figures are often the real content — embed the real ones, don't just describe them.
See `figures.md` for the extraction mechanics. Placement:

- Main result plots → 04 RESULTS, under the results table.
- Ablation / dimension-sweep plots → next to the ablation reading.
- Architecture / method diagrams → 03 METHOD.
- Representation / qualitative visualizations → 04 RESULTS qualitative area.

Each `<figure class="fig">` gets a short caption in the reader's language that
says *what to notice*, not just what it is. Reference them by relative path
(`figs/<PaperKey>/figN.png`) so the library stays clean and diff-able.

---

## Integrity rules

- Every fact, number, and claim must come from the paper. The guide's value is
  trust — a plausible-but-wrong summary is worse than none.
- Mark the guide-writer's own inferences or additions with a visible tag
  (e.g. `[導讀補充]` / `[guide note]`) so they're never confused with the paper.
- The CRITIQUE tab should contain *real* critique (fairness, scope, unproven
  claims), not polite filler. That section is where the guide earns its keep.

---

## Library meta tag (required for the index)

Embed this near the top of every guide so `build_index.py` can list it:

```html
<meta name="paper-meta" content='{"title":"…","authors":"…","year":"2021",
      "venue":"NeurIPS","tags":["…","…"],"tldr":"one sentence"}'>
```

JSON must use double quotes inside; wrap the attribute in single quotes.
**Escape any apostrophe as `&#39;`** — a raw `'` in the content closes the
single-quoted attribute and silently breaks that paper's index card (the JSON
fails to parse, so the card falls back to title-only and loses its tags/tldr).
For bilingual guides also include a `tldr_en` key (English one-liner).

---
name: paper-reading-guide
description: >-
  Turn an academic paper (a PDF file or an arXiv/URL link) into a polished,
  interactive single-page HTML reading guide — color-coded prose, a six-tab
  analysis framework (background → problem → method → results → critique →
  takeaway), structured comparison tables, and the paper's REAL figures cropped
  and embedded. Also maintains a searchable library index of all guides. Use
  this whenever the user wants to read, digest, understand, summarize, or do a
  導讀 / 領讀 of a paper; shares an arXiv link or a PDF and wants help making
  sense of it; is doing a literature review or reading group; or wants to build
  a personal paper library. Trigger even if they don't say the word "guide" —
  "help me read this paper", "summarize this arXiv link", "整理這篇論文",
  "做個導讀" all qualify.
---

# Paper Reading Guide

Produce a beautiful, trustworthy HTML reading guide for a research paper, and
file it in a searchable library. The guide turns a dense paper into something a
reader can absorb in minutes: the logic chain color-coded, the key tables
rebuilt, the real figures embedded, and an honest critique.

## How the work splits

- **Scripts do the deterministic, fiddly parts** (`scripts/pdf_tools.py`):
  fetching, text extraction, page rendering, locating figure captions, cropping
  figure regions. And `scripts/build_index.py` regenerates the library homepage.
- **You do the judgment** — actually reading the paper (prose *and* rendered
  figures), deciding what matters, writing the analysis, picking and placing
  figures, and writing real critique. Don't outsource understanding to captions.

## Workflow

Create a todo list from these steps so none is skipped.

### 1. Get the PDF
- If given an arXiv link or URL: `python scripts/pdf_tools.py fetch <url> -o paper.pdf`
  (it normalizes arXiv `abs`/`pdf` links automatically).
- If given a local PDF, use it directly. Work in a scratch dir; the guide and its
  figures go in the user's library (see step 6).
- Ensure PyMuPDF is available: `python -c "import fitz" || pip3 install pymupdf`.

### 2. Extract text and survey the figures
- `python scripts/pdf_tools.py text paper.pdf -o paper.txt` — read this for the prose.
- `python scripts/pdf_tools.py images paper.pdf` — see which pages have figures,
  and whether they're raster or vector (matters for extraction — see figures.md).

### 3. READ it — including the figures
Read `paper.txt` for the argument. Then **render and actually look at** the pages
holding important figures/tables:
`python scripts/pdf_tools.py render paper.pdf --pages <range> --zoom 2 -o pages/`
and open the PNGs. Seeing Figure 2 yourself beats guessing from its caption — it
is how you verify the results you're about to summarize. This step is the
difference between a guide you can trust and one you can't.

### 4. Write the guide
Follow `references/guide_spec.md` exactly: the five-color protocol, the six-tab
skeleton, the visual design, the integrity rules, and the required `paper-meta`
tag. If the user's library already has a guide, open it as the canonical example
and match its markup. Default the analysis language to the user's (Traditional
Chinese for this user) while keeping technical terms in English.

Write the HTML to `<library>/papers/<AuthorYear_ShortName>.html`.

### 5. Extract and embed the real figures
Follow `references/figures.md`: locate captions, crop page regions (this catches
vector plots that can't be extracted as images), **verify each crop by reading it
back**, then embed by relative path into the right tab. Save crops under
`<library>/papers/figs/<PaperKey>/`. 3–6 well-chosen figures is plenty.

### 6. Update the library index
`python scripts/build_index.py <library>/papers` — regenerates `index.html` as a
searchable card grid from every guide's `paper-meta` tag. Run this after every
new guide.

### 7. Show the result
Tell the user the guide path and the index path, and offer to open them. If a
preview panel is available the guide shows there; otherwise `open` it. To preview
locally over HTTP (needed if `file://` is blocked): serve the `papers/` dir with
`python -m http.server` and load the page, then stop the server.

## Where the library lives
Default to a `papers/` folder in the user's current project (create it if absent).
One guide per paper; one `figs/<PaperKey>/` folder per paper; one shared
`index.html`. If the user already has a `papers/` library, add to it.

## Reference files
- `references/guide_spec.md` — content framework, color protocol, visual design, integrity rules. **Read before writing the guide.**
- `references/figures.md` — figure extraction & embedding mechanics. **Read before doing figures.**
- `scripts/pdf_tools.py` — `fetch | text | render | captions | images | crop`. Run with `-h` for args.
- `scripts/build_index.py` — regenerate the library homepage.

## Scope & honesty
- Facts, numbers, and claims come from the paper; mark your own additions (`[導讀補充]`).
- Make the CRITIQUE tab genuinely critical — fairness of baselines, scope of
  experiments, unproven claims. That section is where the guide earns trust.
- Scale effort to the ask: a quick digest needs fewer figures and a lighter
  critique than a reading-group deep dive.

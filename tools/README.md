# 🛠️ tools — the generator behind the reading list

These are the scripts + spec that build every guide and the clustered homepage in
[`../papers/`](../papers/). Clone the repo and you can regenerate / extend it yourself.

The workflow is designed to be driven by an AI assistant (it originated as a Claude Code
skill — see [`SKILL.md`](SKILL.md)), but the scripts are plain-Python CLIs you can run by hand.

## Contents

| File | What it does |
|------|--------------|
| `scripts/pdf_tools.py` | PDF utilities: `fetch · text · render · captions · images · crop` |
| `scripts/build_index.py` | Regenerates `papers/index.html` — the clustered "grape-bunch" homepage. Clusters/lineages are curated in the `CLUSTERS` list at the top of this file. |
| `references/guide_spec.md` | The content framework: 5-color protocol, 6 tabs, visual design, the 中/EN bilingual toggle, "math = LaTeX + `<!DOCTYPE html>`" rules. **Read before writing a guide.** |
| `references/figures.md` | Figure extraction mechanics (raster vs vector, the crop→verify loop). |
| `SKILL.md` | The end-to-end orchestration (how the pieces fit together). |

## Requirements

```bash
pip3 install pymupdf        # the only dependency (PDF text/render/crop)
```

KaTeX is vendored once in `papers/assets/katex/` (offline math, no CDN) and shared by
every guide — no need to re-download it.

## Add a paper (end-to-end, run from the repo root)

```bash
P=/tmp/paper.pdf

# 1. fetch + read the paper
python3 tools/scripts/pdf_tools.py fetch https://arxiv.org/pdf/XXXX.XXXXX -o $P
python3 tools/scripts/pdf_tools.py text     $P -o /tmp/paper.txt   # read this
python3 tools/scripts/pdf_tools.py images   $P                     # raster vs vector survey
python3 tools/scripts/pdf_tools.py captions $P --pages 1-12        # figure-caption anchors

# 2. see + crop the key figures (repeat per figure; verify each crop by opening it)
python3 tools/scripts/pdf_tools.py render $P --pages 3 --zoom 2 -o /tmp/pages
python3 tools/scripts/pdf_tools.py crop   $P --page 3 --box X0,Y0,X1,Y1 --zoom 2.2 \
        -o papers/figs/<AuthorYear>/fig1_name.png

# 3. write papers/<AuthorYear>_<slug>.html  — follow tools/references/guide_spec.md
#    (bilingual, <!DOCTYPE html> first line, KaTeX at assets/katex/, paper-meta tag with tldr+tldr_en)

# 4. regenerate the homepage
python3 tools/scripts/build_index.py papers

# 5. publish (GitHub Pages redeploys automatically on push to main)
git add -A && git commit -m "add <AuthorYear> guide" && git push
```

## Re-thread the homepage

Grouping is a semantic judgement, so it's curated (not auto-inferred). Edit the `CLUSTERS`
list at the top of `scripts/build_index.py`:

- add a paper's `PaperKey` (the filename prefix before `_`) into a cluster's `lineages[].chain`
- add a new cluster dict for a new thread
- a paper present on disk but not placed anywhere falls into an **"Other"** bunch automatically
- a page with `"kind":"synthesis"` in its `paper-meta` is skipped from the grid and linked as a
  gold **Synthesis** banner at the top of the cluster that names it (via the cluster's `synthesis` field)

Then rerun `build_index.py papers`.

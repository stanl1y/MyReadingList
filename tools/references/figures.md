# Extracting & embedding figures

Figures (result curves, heatmaps, architecture diagrams, t-SNE plots) are often
the most information-dense part of a paper. A text-only guide misses them. This
is the mechanical loop for getting *real* figures into the guide.

## The one thing that trips people up: raster vs vector

`scripts/pdf_tools.py images <pdf>` reports two things:

- **raster images** — photos, heatmaps, screenshots. These *can* be pulled
  straight out of the PDF.
- **vector-heavy pages** — these usually hold matplotlib/TikZ plots
  (line charts, contour plots, diagrams). `get_images()` **cannot** extract
  these; they only come out by **rendering a page region to PNG**.

The trap: a paper's most important figure (the main results curve) is very often
a vector plot. If you only "extract embedded images" you silently drop it. So the
robust method below crops **page regions**, which captures raster and vector alike.

## The loop

1. **Locate.** Run `pdf_tools.py captions <pdf> --pages 1-12`. It returns the
   pixel/point position of each `Figure N:` caption. In most papers the figure
   sits *just above* its caption (occasionally below, in single-column layouts —
   the render in step 2 tells you which).

2. **See it.** Render the figure's page: `pdf_tools.py render <pdf> --pages 7-8
   --zoom 2 -o pages/`. Then actually **read the PNG** (open it with your image
   tool). You can now see the figure — describe it from what you see, not from
   the caption text. This is also how you sanity-check your reading of the results.

3. **Crop.** Using the caption's `y` as the bottom anchor, crop the band above it:
   `pdf_tools.py crop <pdf> --page 8 --box x0,y0,x1,y1 --zoom 2.2 -o figs/<Key>/figN.png`
   where the box is in PDF points. For side-by-side sub-figures, split on x
   (left half / right half of the content width, typically x≈108–504 on Letter).

4. **Verify before embedding.** Read the cropped PNG back. The usual defect is a
   line of body text bleeding in at the top — nudge `y0` down ~12–16 pt and
   re-crop. Don't embed a crop you haven't looked at; one verification read saves
   a sloppy-looking guide. Expect 1–2 nudges per figure — that's normal, not failure.

5. **Embed.** Reference by relative path so the library stays clean:
   ```html
   <figure class="fig"><img src="figs/<Key>/figN.png" alt="Figure N">
     <figcaption><b>Fig.N</b> — what to notice here (in the reader's language).</figcaption>
   </figure>
   ```
   Put figures where they support the argument (see `guide_spec.md` → Figures).

## Tips

- Render/crop at zoom 2–2.5 for crisp images without huge files; result crops
  land around 20–80 KB each, which is fine for a local library.
- Store crops under `papers/figs/<PaperKey>/` (one folder per paper) so guides
  never clash and the index folder stays tidy.
- If you truly want a single portable file (email-able, no folder), embed images
  as base64 `data:` URIs instead of paths — at the cost of a much larger, harder-
  to-edit HTML. Default to relative paths for a library; switch to base64 only on
  request.
- Don't over-invest: 3–6 well-chosen figures (main result, ablation, key diagram,
  one qualitative) beats cropping every figure in a 45-page paper.

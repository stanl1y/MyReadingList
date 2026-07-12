#!/usr/bin/env python3
"""
build_index.py — regenerate the reading-guide library homepage as a
bilingual (中/EN), searchable "grape-bunch" of research threads.

Instead of a flat grid, papers are organised into CLUSTERS (bunches), and within
a cluster into LINEAGES (vines): chronological chains of papers connected by
labelled edges (e.g. "extends"). Each cluster carries a short synthesis blurb —
that blurb is where the cross-paper "統整/脈絡" lives.

Card content (title, authors, year, venue, tags, tldr/tldr_en) is read from each
guide's <meta name="paper-meta"> tag, so cards stay data-driven. Only the
cluster membership + blurbs + edge labels are curated here (that grouping is a
semantic judgement a script can't infer). Papers present on disk but not placed
in any cluster fall into an "Other" bunch, so nothing is ever silently dropped.

Usage:  python build_index.py /path/to/papers        # writes papers/index.html
"""
import sys, os, re, json, html, glob

# ------------------------------------------------------------------ curated map
# PaperKey = the filename prefix before the first "_" (e.g. Wang2025_VGGT.html -> Wang2025).
# To re-thread the library, edit CLUSTERS; everything else is automatic.
CLUSTERS = [
    {
        "id": "force", "emoji": "🖐️", "accent": "#3b6fd4",
        "synthesis": "Synthesis_ForceManipulation.html",
        "synthesis_note_zh": "：兩條線的橫向比較表 + 演進脈絡 →",
        "synthesis_note_en": ": head-to-head table + evolution of the two lines →",
        "title_zh": "力覺 × 接觸豐富操作",
        "title_en": "Force-Aware Contact-Rich Manipulation",
        "blurb_zh": ("這串的共同敵人:<b>力訊號稀疏又吵</b>——大多數時間接觸力≈0,天真地把力丟進 policy 只會讓它更黏視覺、甚至更糟。"
                     "上位的立場文章(Karcini)主張機器人缺的是把<b>力/具身/獎勵「接地」</b>的機制;底下兩條線各自出招。"
                     "<b>SJTU · Cewu Lu 線</b>走「控制與架構」:手持力捕捉+混合力位控制(ForceMimic)→ 用接觸預測 gate 掉噪音(FoAR)→ 用 Interaction Frame 拆出力控/位控子空間(Force Policy)。"
                     "<b>CMU · Pathak 線</b>走「訓練與感測」:視覺模糊 curriculum 逼 policy 先學力(FACTR)→ 讓廉價手臂免感測器也能估力(FACTR 2)。"),
        "blurb_en": ("The shared enemy of this bunch: <b>force is sparse and noisy</b>—contact force is ≈0 most of the time, so naively feeding force to a policy makes it lean on vision even more, or worse. "
                     "The umbrella position paper (Karcini) argues robots lack mechanisms to <b>ground force / embodiment / reward</b>; two lines answer it. "
                     "The <b>SJTU · Cewu Lu line</b> evolves control &amp; architecture: handheld force capture + hybrid force-position control (ForceMimic) → gating noise via contact prediction (FoAR) → splitting force/motion subspaces with an Interaction Frame (Force Policy). "
                     "The <b>CMU · Pathak line</b> evolves training &amp; sensing: a vision-blur curriculum that forces the policy to learn force first (FACTR) → sensorless force estimation for commodity arms (FACTR 2)."),
        "context": "Karcini2026",
        "context_note_zh": "↓ 這篇立場文章framing了「為何需要力/接地」,下面兩條線是具體實作",
        "context_note_en": "↓ this position paper frames \"why force/grounding is needed\"; the two lines below are concrete instances",
        "lineages": [
            {"label_zh": "SJTU · Cewu Lu 線", "label_en": "SJTU · Cewu Lu line",
             "chain": ["Liu2024", "He2025", "Fang2026"],
             "edges_zh": ["同組延伸", "同組延伸"], "edges_en": ["extends", "extends"]},
            {"label_zh": "CMU · Pathak 線", "label_en": "CMU · Pathak line",
             "chain": ["Liu2025", "Oh2026"],
             "edges_zh": ["同組延伸"], "edges_en": ["extends"]},
        ],
    },
    {
        "id": "sam", "emoji": "✂️", "accent": "#0f9b8e",
        "synthesis": "Synthesis_SegmentAnything.html",
        "synthesis_note_zh": "：四代橫向比較表 + 不變的配方 →",
        "synthesis_note_en": ": the four-generation comparison + the invariant recipe →",
        "title_zh": "Segment Anything 系列",
        "title_en": "The Segment Anything Series",
        "blurb_zh": ("主線是把「分割」做成<b>可提示的 foundation model</b>,然後一代一代<b>擴張「可提示 / 可輸出」的維度</b>——"
                     "SAM 用空間提示(點/框/遮罩)在單張影像分割任意物體(靠 SA-1B 資料引擎);SAM 2 加<b>時間</b>(streaming memory 推廣到影片);"
                     "SAM 3 加<b>語意</b>(文字概念/範例提示,一次找出並追蹤某概念的所有實例 PCS);SAM 3D 加<b>維度</b>(單張影像生成完整 per-object 3D:形狀+紋理+layout)。"
                     "共同配方:每一代都配一個 model-in-the-loop 資料引擎,讓模型自產大部分標註。SAM 3D 與下面「3D 視覺」串的 VGGT 是姊妹——前者生成完整物體 3D,後者回復可視場景幾何。"),
        "blurb_en": ("The throughline: make segmentation a <b>promptable foundation model</b>, then <b>widen the promptable / output space</b> generation by generation—"
                     "SAM segments any object in one image via spatial prompts (points/boxes/masks), powered by the SA-1B data engine; SAM 2 adds <b>time</b> (streaming memory extends it to video); "
                     "SAM 3 adds <b>semantics</b> (text-concept / exemplar prompts that find &amp; track every instance of a concept — PCS); SAM 3D adds <b>dimension</b> (full per-object 3D — shape+texture+layout — from one image). "
                     "Shared recipe: every generation pairs with a model-in-the-loop data engine so the model annotates most of its own data. SAM 3D is a sibling to VGGT in the 3D-vision thread below — the former generates full object 3D, the latter recovers visible scene geometry."),
        "context": None,
        "lineages": [
            {"label_zh": "Meta FAIR / Superintelligence Labs", "label_en": "Meta FAIR / Superintelligence Labs",
             "chain": ["SAMv1", "SAMv2", "SAMv3", "SAM3D"],
             "edges_zh": ["+影片・記憶", "+概念・文字", "+3D 維度"],
             "edges_en": ["+video · memory", "+concepts · text", "+3D lifting"]},
        ],
    },
    {
        "id": "vision3d", "emoji": "🧊", "accent": "#9a5bd1",
        "title_zh": "3D 視覺與重建",
        "title_en": "3D Vision &amp; Reconstruction",
        "blurb_zh": "把 3D 重建從「迭代幾何優化」改寫成「<b>大模型一次前饋回歸</b>」:一個 transformer 同時吐相機、深度、point map、點軌跡。",
        "blurb_en": "Rewrites 3D reconstruction from \"iterative geometric optimization\" into \"<b>one feed-forward regression by a large model</b>\": a single transformer predicts cameras, depth, point maps and tracks at once.",
        "context": None, "lineages": [
            {"label_zh": "", "label_en": "", "chain": ["Wang2025"], "edges_zh": [], "edges_en": []},
        ],
    },
    {
        "id": "rl", "emoji": "🎯", "accent": "#3aa564",
        "title_zh": "Unsupervised / Zero-shot RL",
        "title_en": "Unsupervised / Zero-shot RL",
        "blurb_zh": "先無監督學一個表徵,<b>事後任給 reward 都能不重訓、不規劃</b>即時求最優策略——zero-shot RL 這條線的奠基。",
        "blurb_en": "Learn one representation unsupervised, then <b>for any reward given later, get the optimal policy instantly—no retraining, no planning</b>. A foundation of the zero-shot RL line.",
        "context": None, "lineages": [
            {"label_zh": "", "label_en": "", "chain": ["Touati2021"], "edges_zh": [], "edges_en": []},
        ],
    },
]
OTHER_ACCENT = "#6b6f76"

def extract_meta(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        head = f.read(8000)
    meta = {}
    m = re.search(r'<meta\s+name=["\']paper-meta["\']\s+content=([\'"])(.*?)\1', head, re.S)
    if m:
        try:
            meta = json.loads(html.unescape(m.group(2)))
        except json.JSONDecodeError:
            meta = {}
    if not meta.get("title"):
        t = re.search(r"<title>(.*?)</title>", head, re.S | re.I)
        meta["title"] = t.group(1).strip() if t else os.path.splitext(os.path.basename(path))[0]
    meta["_file"] = os.path.basename(path)
    meta["_key"] = os.path.basename(path).split("_")[0]
    return meta

def gcard(m, accent, ctx=False):
    tags = m.get("tags", []) or []
    tldr_zh = str(m.get("tldr", "")); tldr_en = str(m.get("tldr_en", "") or tldr_zh)
    search = " ".join([str(m.get("title", "")), str(m.get("authors", "")),
                       tldr_zh, tldr_en, " ".join(map(str, tags))]).lower()
    venue = (" · " + html.escape(str(m["venue"]))) if m.get("venue") else ""
    tagspans = "".join(f'<span class="tg" data-tag="{html.escape(str(t),quote=True)}">{html.escape(str(t))}</span>' for t in tags)
    ribbon = ('<div class="ribbon"><span data-lang="zh">脈絡起點 · 動機</span><span data-lang="en">Context · motivation</span></div>' if ctx else "")
    return (
        f'<a class="gcard{" ctx" if ctx else ""}" style="border-top-color:{accent}" '
        f'href="{html.escape(m["_file"])}" data-search="{html.escape(search, quote=True)}">'
        f'{ribbon}'
        f'<div class="yr">{html.escape(str(m.get("year","")))}{venue}</div>'
        f'<h3>{html.escape(str(m.get("title","")))}</h3>'
        f'<div class="auth">{html.escape(str(m.get("authors","")))}</div>'
        f'<p class="tl"><span data-lang="zh">{html.escape(tldr_zh)}</span>'
        f'<span data-lang="en">{html.escape(tldr_en)}</span></p>'
        f'<div class="tags">{tagspans}</div></a>'
    )

def vine(edge_zh, edge_en):
    return (f'<div class="vine"><span class="vlabel">'
            f'<span data-lang="zh">{html.escape(edge_zh)}</span>'
            f'<span data-lang="en">{html.escape(edge_en)}</span></span>'
            f'<span class="varrow">→</span></div>')

def render_clusters(by_key, present=frozenset()):
    used = set()
    out = []
    for c in CLUSTERS:
        acc = c["accent"]
        # collect members that actually exist on disk
        members = ([c["context"]] if c.get("context") else []) + [k for ln in c["lineages"] for k in ln["chain"]]
        if not any(k in by_key for k in members):
            continue  # nothing from this cluster is present; skip
        used.update(members)
        parts = [f'<section class="cluster" data-cluster="{c["id"]}">']
        parts.append(f'<div class="chead"><span class="cemoji">{c["emoji"]}</span>'
                     f'<h2 class="serif"><span data-lang="zh">{c["title_zh"]}</span>'
                     f'<span data-lang="en">{c["title_en"]}</span></h2></div>')
        parts.append(f'<p class="blurb"><span data-lang="zh">{c["blurb_zh"]}</span>'
                     f'<span data-lang="en">{c["blurb_en"]}</span></p>')
        if c.get("synthesis") and c["synthesis"] in present:
            note_zh = c.get("synthesis_note_zh", "：橫向比較表 + 演進脈絡 →")
            note_en = c.get("synthesis_note_en", ": head-to-head comparison + lineage evolution →")
            parts.append(f'<a class="synbanner" href="{html.escape(c["synthesis"])}">'
                         '<span class="sb-emoji">🧵</span><span class="sb-txt">'
                         '<b><span data-lang="zh">綜合導讀</span><span data-lang="en">Synthesis</span></b> '
                         f'<span data-lang="zh">{note_zh}</span>'
                         f'<span data-lang="en">{note_en}</span>'
                         '</span></a>')
        if c.get("context") and c["context"] in by_key:
            parts.append('<div class="ctxwrap">')
            parts.append(gcard(by_key[c["context"]], acc, ctx=True))
            parts.append(f'<div class="branchnote"><span data-lang="zh">{c.get("context_note_zh","")}</span>'
                         f'<span data-lang="en">{c.get("context_note_en","")}</span></div>')
            parts.append('</div>')
        parts.append('<div class="vines">')
        for ln in c["lineages"]:
            chain = [k for k in ln["chain"] if k in by_key]
            if not chain:
                continue
            parts.append('<div class="lineage">')
            if ln.get("label_zh") or ln.get("label_en"):
                parts.append(f'<div class="llabel mono"><span data-lang="zh">{ln["label_zh"]}</span>'
                             f'<span data-lang="en">{ln["label_en"]}</span></div>')
            parts.append('<div class="chain">')
            for i, k in enumerate(chain):
                parts.append(gcard(by_key[k], acc))
                if i < len(chain) - 1:
                    ez = ln["edges_zh"][i] if i < len(ln.get("edges_zh", [])) else "→"
                    ee = ln["edges_en"][i] if i < len(ln.get("edges_en", [])) else "→"
                    parts.append(vine(ez, ee))
            parts.append('</div></div>')
        parts.append('</div></section>')
        out.append("".join(parts))
    # leftovers -> Other bunch
    leftover = [m for k, m in by_key.items() if k not in used]
    if leftover:
        leftover.sort(key=lambda m: str(m.get("year", "")), reverse=True)
        cards = "".join(gcard(m, OTHER_ACCENT) for m in leftover)
        out.append('<section class="cluster" data-cluster="other">'
                   '<div class="chead"><span class="cemoji">🍇</span>'
                   '<h2 class="serif"><span data-lang="zh">其他</span><span data-lang="en">Other</span></h2></div>'
                   f'<div class="vines"><div class="lineage"><div class="chain">{cards}</div></div></div></section>')
    return "\n".join(out)

PAGE = """<!DOCTYPE html>
<meta charset="utf-8">
<title>論文導讀庫 · Paper Reading Library</title>
<link rel="stylesheet" href="assets/katex/katex.min.css">
<style>
  :root{--navy:#16243f;--gold:#c9a44c;--paper:#f6f1e6;--card:#fffdf8;--ink:#23262b;--muted:#6b6f76;--line:#e6dfce}
  *{box-sizing:border-box} body{margin:0;background:var(--paper);color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Noto Sans TC",sans-serif;line-height:1.6}
  .serif{font-family:Georgia,"Songti TC",serif}
  .mono{font-family:ui-monospace,Menlo,Consolas,monospace;letter-spacing:.04em}
  .wrap.lang-zh [data-lang="en"]{display:none !important}
  .wrap.lang-en [data-lang="zh"]{display:none !important}
  header{background:var(--navy);color:#fff;padding:28px}
  .hwrap{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;
    flex-wrap:wrap;max-width:1120px;margin:0 auto}
  header h1{margin:0;color:var(--gold);letter-spacing:.08em;font-size:23px}
  header p{margin:6px 0 0;color:#aeb8cc;font-size:13px}
  .langtog{display:inline-flex;align-items:center;border:1px solid rgba(255,255,255,.28);
    border-radius:20px;overflow:hidden;cursor:pointer;background:transparent;padding:0;font-family:inherit;flex-shrink:0}
  .langtog span{padding:5px 13px;font-size:12px;color:#aeb8cc;line-height:1.1}
  .wrap.lang-zh .langtog .lg-zh{background:var(--gold);color:var(--navy);font-weight:700}
  .wrap.lang-en .langtog .lg-en{background:var(--gold);color:var(--navy);font-weight:700}
  .bar{max-width:1120px;margin:20px auto 0;padding:0 22px}
  #q{width:100%;padding:12px 16px;border:1px solid var(--line);border-radius:10px;font-size:15px;background:var(--card)}
  main{max-width:1120px;margin:0 auto;padding:14px 22px 60px}
  .cluster{margin:30px 0 10px}
  .chead{display:flex;align-items:center;gap:10px;margin:0 0 6px}
  .cemoji{font-size:24px}
  .chead h2{margin:0;font-size:22px}
  .blurb{font-size:13.5px;color:#54585f;background:var(--card);border:1px solid var(--line);
    border-left:4px solid var(--gold);border-radius:10px;padding:12px 16px;margin:0 0 16px;max-width:900px}
  .blurb b{color:var(--navy)}
  .synbanner{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--navy);
    background:linear-gradient(180deg,#fff8e6,#f7edcf);border:1px solid var(--gold);border-radius:10px;
    padding:11px 16px;margin:0 0 16px;max-width:900px;transition:.15s;box-shadow:0 2px 8px rgba(201,164,76,.15)}
  .synbanner:hover{transform:translateY(-2px);box-shadow:0 8px 18px rgba(201,164,76,.28)}
  .sb-emoji{font-size:20px;flex-shrink:0}
  .sb-txt{font-size:13.5px} .sb-txt b{color:var(--navy)}
  .ctxwrap{margin-bottom:8px}
  .branchnote{font-size:12px;color:var(--muted);margin:8px 0 2px;padding-left:4px}
  .vines{display:flex;flex-direction:column;gap:16px}
  .lineage{}
  .llabel{font-size:11px;color:var(--gold);font-weight:700;margin:0 0 8px;letter-spacing:.06em}
  .chain{display:flex;align-items:stretch;gap:0;flex-wrap:wrap}
  .gcard{width:264px;flex-shrink:0;background:var(--card);border:1px solid var(--line);border-top:3px solid var(--gold);
    border-radius:12px;padding:15px 17px;text-decoration:none;color:inherit;
    box-shadow:0 3px 12px rgba(40,30,10,.05);transition:.15s;position:relative;display:flex;flex-direction:column}
  .gcard:hover{transform:translateY(-3px);box-shadow:0 10px 22px rgba(40,30,10,.12)}
  .gcard.ctx{width:auto;max-width:900px;border-top-width:3px;background:linear-gradient(180deg,#fffdf6,#fbf6ea)}
  .ribbon{position:absolute;top:-1px;right:14px;transform:translateY(-50%);background:var(--navy);color:var(--gold);
    font-size:9.5px;letter-spacing:.1em;padding:3px 9px;border-radius:10px;font-family:ui-monospace,Menlo,monospace}
  .yr{font-family:ui-monospace,Menlo,monospace;font-size:10.5px;color:var(--gold);letter-spacing:.06em}
  .gcard h3{font-family:Georgia,serif;font-size:15.5px;margin:5px 0 4px;line-height:1.3}
  .auth{font-size:11.5px;color:var(--muted);margin-bottom:7px}
  .tl{font-size:12px;line-height:1.5;margin:0 0 10px;color:#3f434a;
    display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
  .gcard.ctx .tl{-webkit-line-clamp:3}
  .tags{display:flex;gap:5px;flex-wrap:wrap;margin-top:auto}
  .tg{font-size:9.5px;background:#efe9da;color:#5a5238;padding:2px 8px;border-radius:11px;border:1px solid var(--line)}
  .tg:hover{background:var(--gold);color:var(--navy)}
  .vine{flex-shrink:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
    min-width:78px;padding:0 4px;align-self:center}
  .vlabel{font-size:10px;color:var(--muted);text-align:center;margin-bottom:2px;line-height:1.2}
  .varrow{color:var(--gold);font-size:22px;line-height:1}
  .wrap.searching .vine{display:none}
  .empty{text-align:center;color:var(--muted);padding:50px}
  footer{text-align:center;color:var(--muted);font-size:12px;padding:22px}
  @media(max-width:720px){
    .gcard,.gcard.ctx{width:100%}
    .chain{flex-direction:column}
    .vine{min-width:0;padding:6px 0}.varrow{transform:rotate(90deg)}
  }
</style>
<div class="wrap lang-zh">
<header>
  <div class="hwrap">
    <div>
      <h1 class="serif"><span data-lang="zh">論文導讀庫 · PAPER READING LIBRARY</span><span data-lang="en">Paper Reading Library · 論文導讀庫</span></h1>
      <p><span data-lang="zh">__COUNT__ 篇導讀 · __NC__ 串研究脈絡 · 點 tag 可篩選</span><span data-lang="en">__COUNT__ guides · __NC__ threads · click a tag to filter</span></p>
    </div>
    <button class="langtog" id="langtog" title="切換中／英 · Toggle language">
      <span class="lg-zh">中文</span><span class="lg-en">EN</span>
    </button>
  </div>
</header>
<div class="bar"><input id="q" placeholder="搜尋標題 / 作者 / 標籤 / 關鍵字…"></div>
<main id="grid">
__CLUSTERS__
  <div class="empty" id="empty" style="display:none"><span data-lang="zh">找不到符合的論文</span><span data-lang="en">No matching papers</span></div>
</main>
<footer class="serif"><span data-lang="zh">cd papers/ &nbsp;·&nbsp; 新增導讀後重跑 build_index.py;分群脈絡編在腳本的 CLUSTERS 設定裡</span><span data-lang="en">cd papers/ &nbsp;·&nbsp; re-run build_index.py after adding a guide; threads are curated in the script's CLUSTERS config</span></footer>
</div>
<script>
  const wrap=document.querySelector('.wrap');
  const q=document.getElementById('q'), empty=document.getElementById('empty');
  const cards=[...document.querySelectorAll('.gcard')];
  const clusters=[...document.querySelectorAll('.cluster')];
  function setLang(en){
    wrap.classList.toggle('lang-en',en); wrap.classList.toggle('lang-zh',!en);
    q.placeholder = en ? 'Search title / author / tags / keywords…' : '搜尋標題 / 作者 / 標籤 / 關鍵字…';
    try{ localStorage.setItem('guide-lang', en?'en':'zh'); }catch(e){}
  }
  try{ setLang(localStorage.getItem('guide-lang')==='en'); }catch(e){ setLang(false); }
  document.getElementById('langtog').onclick=()=>setLang(!wrap.classList.contains('lang-en'));
  function filter(){
    const t=q.value.toLowerCase().trim(); let n=0;
    wrap.classList.toggle('searching', t.length>0);
    cards.forEach(c=>{const hit=c.dataset.search.includes(t); c.style.display=hit?'':'none'; if(hit)n++;});
    clusters.forEach(cl=>{const any=[...cl.querySelectorAll('.gcard')].some(c=>c.style.display!=='none'); cl.style.display=any?'':'none';});
    empty.style.display=n?'none':'block';
  }
  q.addEventListener('input',filter);
  document.querySelectorAll('.tg').forEach(t=>t.addEventListener('click',e=>{
    e.preventDefault(); e.stopPropagation(); q.value=t.dataset.tag; filter(); window.scrollTo({top:0,behavior:'smooth'});
  }));
</script>
"""

def build(folder):
    files = sorted(f for f in glob.glob(os.path.join(folder, "*.html"))
                   if os.path.basename(f) != "index.html")
    present = {os.path.basename(f) for f in files}
    by_key = {}
    for f in files:
        m = extract_meta(f)
        if m.get("kind") == "synthesis":
            continue  # synthesis pages are linked as cluster banners, not listed as grapes
        by_key[m["_key"]] = m
    clusters_html = render_clusters(by_key, present)
    # count threads shown = configured clusters present + (Other if any)
    n_threads = clusters_html.count('<section class="cluster"')
    page = (PAGE.replace("__CLUSTERS__", clusters_html)
                .replace("__COUNT__", str(len(by_key)))
                .replace("__NC__", str(n_threads)))
    out = os.path.join(folder, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(json.dumps({"index": out, "papers": len(by_key), "threads": n_threads,
                      "keys": sorted(by_key)}, ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python build_index.py /path/to/papers")
    build(sys.argv[1])

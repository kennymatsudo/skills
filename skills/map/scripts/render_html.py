#!/usr/bin/env python3
"""Render a map file as one self-contained HTML page for a browser.

Usage: render_html.py <repo-root> <map.json> <out.html>

The page draws one level at a time, left to right, with Pele, a Mermaid
renderer: callers on the left, and the datastores, queues, and outside systems
they call on the right. The drawing stays monochrome and shows each box's kind
by its shape, so the only colour on it is the issue tag clipped to a box that
holds bugs or risks. Clicking a box shows its connections and issues in the
side panel; double-clicking it, or its Open button, goes one level down.
Citations open the cited line in VS Code. Everything but Pele and one web font
is inline, so the file opens straight from disk.
"""

import json
import sys
from pathlib import Path

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ map</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --sheet: #f3f4f6; --card: #ffffff; --ink: #23272d; --pencil: #5d6570; --faint: #6f7781;
  --rule: #d6dae0; --wire: #8a929c; --line: #9aa2ab;
  --link: #2457c5; --link-wash: #e8eefb;
  --bug: #c9321c; --risk: #8f5a08; --gap: #5d6570;
  --panel: #fbfbfc; --font: Archivo, system-ui, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --sheet: #1a1d21; --card: #23272c; --ink: #e7eaee; --pencil: #a7afb8; --faint: #8d959e;
    --rule: #343a41; --wire: #6c757f; --line: #59616a;
    --link: #8fb0f5; --link-wash: #24324d;
    --bug: #f2765e; --risk: #e3a948; --gap: #a7afb8;
    --panel: #1f2226;
  }
}
* { box-sizing: border-box; }
html, body { height: 100%; }
body { margin: 0; background: var(--sheet); color: var(--ink);
  font: 14px/1.5 var(--font); display: grid; grid-template-rows: auto 1fr; }
button { font: inherit; color: inherit; }
code { font: 12.5px/1.4 ui-monospace, Menlo, monospace; }

header { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 14px; padding: 12px 18px;
  border-bottom: 1px solid var(--rule); background: var(--panel); min-width: 0; }
#back { width: 32px; height: 32px; flex: none; border-radius: 4px; border: 1px solid var(--rule);
  background: var(--card); cursor: pointer; font-size: 16px; }
#back:disabled { visibility: hidden; }
#crumbs { display: flex; flex-wrap: wrap; gap: 4px 8px; align-items: baseline; font-size: 20px;
  font-weight: 700; letter-spacing: -.01em; min-width: 0; }
#crumbs button { font-weight: 500; color: var(--pencil); background: none; border: 0; padding: 0; cursor: pointer; }
#crumbs button:hover { color: var(--link); }
#crumbs .sep { color: var(--faint); font-weight: 400; }
#legend { margin-left: auto; display: flex; flex-wrap: wrap; gap: 4px 16px; align-items: center;
  color: var(--pencil); font-size: 12.5px; }
#legend span { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }
#legend svg { overflow: visible; }
#legend .hint { color: var(--ink); font-weight: 500; padding-right: 16px; border-right: 1px solid var(--rule); }
@media (max-width: 860px) { #legend { margin-left: 0; flex-basis: 100%; } }

main { display: grid; grid-template-columns: minmax(0, 1fr) 380px; min-height: 0; }
@media (max-width: 860px) { main { grid-template-columns: 1fr; grid-template-rows: 62vh auto; } }

#stage { position: relative; overflow: hidden; min-height: 0; cursor: grab; touch-action: none; outline: none; }
#stage.dragging { cursor: grabbing; }
#tools { position: absolute; right: 14px; bottom: 14px; display: flex; border: 1px solid var(--rule);
  border-radius: 4px; overflow: hidden; background: var(--card); }
#tools button { min-width: 36px; height: 32px; border: 0; background: none; cursor: pointer; padding: 0 10px; font-size: 13px; }
#tools button + button { border-left: 1px solid var(--rule); }
#tools button:hover { color: var(--link); }

/* Pele's drawing, themed to the page */
#canvas { position: absolute; left: 0; top: 0; transform-origin: 0 0; }
#canvas svg.pele { --pele-bg: var(--sheet); --pele-fg: var(--ink); --pele-muted: var(--pencil); --pele-line: var(--wire);
  --pele-surface: var(--card); --pele-surface-alt: var(--panel); --pele-border: var(--line); --pele-accent: var(--link);
  --pele-font: var(--font); --pele-radius: 3px; display: block; overflow: visible; }
#canvas .pele-edge path:not(.pele-marker) { stroke-width: 1.25; }
#canvas .pele-edge-label text { fill: var(--pencil); }
.box { cursor: pointer; }
.box :is(rect, path, polygon, ellipse) { stroke: var(--line); stroke-width: 1.25; }
.box.kexternal :is(rect, path, polygon) { stroke-dasharray: 5 3; fill: var(--sheet); }
.box.unverified :is(rect, path, polygon, ellipse) { stroke-dasharray: 2 3; }
.box text.pele-label tspan:first-child { font-weight: 600; fill: var(--ink); }
.box text.pele-label tspan:not(:first-child) { fill: var(--pencil); }
/* Only the box's own outline, not the stacked card or the issue tag inside it. */
.box:hover > :is(rect, path, polygon, ellipse):not(.stack) { stroke: var(--ink); }
.box.selected > :is(rect, path, polygon, ellipse):not(.stack) { stroke: var(--link); stroke-width: 2; fill: var(--link-wash); }
.box:focus { outline: none; }
.box:focus-visible { outline: 2px solid var(--link); outline-offset: 5px; }
.box .stack { fill: var(--card) !important; stroke-width: 1 !important; stroke-dasharray: none !important; }
.tag rect { stroke: none !important; }
.tag.bug rect { fill: var(--bug); } .tag.risk rect { fill: var(--risk); } .tag.gap rect { fill: var(--gap); }
.tag circle { fill: var(--card); stroke: none !important; }
.tag text { fill: #fff; font-size: 11px; font-weight: 700; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .tag text { fill: #1a1d21; } }
.wire.lit path:not(.pele-marker) { stroke: var(--link); stroke-width: 2; }
.wire.lit path.pele-marker { fill: var(--link); }
.focus .wire:not(.lit) { opacity: .4; }
.focus .box:not(.near) { opacity: .65; }
@media (prefers-reduced-motion: no-preference) { .wire, .box { transition: opacity .12s; } }

/* Panel */
aside { background: var(--panel); border-left: 1px solid var(--rule); overflow: auto; padding: 22px 22px 48px; }
@media (max-width: 860px) { aside { border-left: 0; border-top: 1px solid var(--rule); } }
aside h2 { font-size: 20px; line-height: 1.2; margin: 0; letter-spacing: -.01em; }
aside h3 { font-size: 14px; color: var(--ink); margin: 26px 0 8px; font-weight: 600;
  padding-bottom: 6px; border-bottom: 1px solid var(--rule); }
aside p { margin: 6px 0; }
.meta { color: var(--pencil); font-size: 13px; margin-top: 4px; }
.lede { font-size: 15px; line-height: 1.5; margin-top: 12px; }
.counts { color: var(--pencil); font-size: 13px; margin-top: 10px; }
.primary { margin-top: 14px; font-weight: 600; color: var(--link); background: var(--card);
  border: 1px solid var(--link); border-radius: 4px; padding: 6px 12px; cursor: pointer; }
.primary:hover { background: var(--link-wash); }
.issue { border-left: 3px solid var(--risk); padding: 2px 0 2px 12px; margin: 18px 0; font-size: 13.5px; }
.issue.bug { border-color: var(--bug); } .issue.gap { border-color: var(--gap); }
.issue .head { display: flex; flex-wrap: wrap; gap: 2px 8px; align-items: baseline; margin-bottom: 2px; }
.issue .sev { font-size: 12.5px; font-weight: 700; color: var(--risk); }
.issue.bug .sev { color: var(--bug); } .issue.gap .sev { color: var(--gap); }
.issue .on { font-size: 12.5px; font-weight: 500; background: none; border: 0; padding: 0; cursor: pointer;
  color: var(--pencil); text-align: left; text-decoration: underline; text-decoration-color: var(--rule); text-underline-offset: 3px; }
.issue .on:hover { color: var(--link); }
.issue.flash { background: var(--link-wash); }
@media (prefers-reduced-motion: no-preference) { .issue { transition: background .6s; } }
.row { padding: 7px 0; border-bottom: 1px solid var(--rule); font-size: 13.5px; }
.row:last-child { border-bottom: 0; }
.row .who { font-weight: 600; background: none; border: 0; padding: 0; cursor: pointer; text-align: left; }
.row .who:hover { color: var(--link); }
.row .what { color: var(--pencil); }
.cites { display: flex; flex-wrap: wrap; gap: 0 12px; margin-top: 2px; }
a.cite { color: var(--link); text-decoration: none; font-size: 12.5px; font-variant-numeric: tabular-nums; }
a.cite:hover { text-decoration: underline; }
.meta .cites { margin-top: 4px; }
details { margin-top: 22px; }
details summary { cursor: pointer; font-size: 13px; font-weight: 600; }
details p { font-size: 13.5px; color: var(--pencil); }
.empty-note { color: var(--pencil); font-size: 13.5px; }
.empty-note button { background: none; border: 0; padding: 0; cursor: pointer; color: var(--link); font-weight: 500; }

/* Call paths */
#paths { position: absolute; inset: 0; overflow: auto; padding: 32px 28px; cursor: default; }
.path { max-width: 760px; margin: 0 auto 36px; }
.path h2 { font-size: 17px; margin: 0 0 6px; letter-spacing: -.01em; }
.path ol { list-style: none; margin: 0; padding: 0; counter-reset: s; border-left: 1px solid var(--line); margin-left: 13px; }
.path li { counter-increment: s; position: relative; padding: 9px 0 9px 28px; font-size: 14.5px; }
.path li::before { content: counter(s); position: absolute; left: -13px; top: 9px; width: 26px; height: 26px;
  border-radius: 50%; background: var(--sheet); border: 1px solid var(--line); color: var(--pencil);
  font-size: 12px; font-weight: 600; display: grid; place-items: center; line-height: 1; }
.path li .call { display: block; padding-top: 2px; }
.flag { display: inline-block; font-size: 11.5px; font-weight: 700; color: #fff; border: 0; border-radius: 2px; padding: 1px 6px;
  background: var(--risk); cursor: pointer; }
.path .cites { align-items: center; gap: 2px 8px; }
.path .cites .flag + a.cite { margin-left: 4px; }
.flag:hover { text-decoration: underline; }
.flag.bug { background: var(--bug); } .flag.gap { background: var(--gap); }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .flag { color: #1a1d21; } }
.empty { position: absolute; inset: 0; display: grid; place-items: center; padding: 24px; color: var(--pencil); text-align: center; cursor: default; }
.empty code { user-select: all; background: var(--card); border: 1px solid var(--rule); border-radius: 3px; padding: 2px 6px; color: var(--ink); }
:focus-visible { outline: 2px solid var(--link); outline-offset: 2px; }
</style>
</head>
<body>
<header>
  <button id="back" title="Up one level (Esc)" aria-label="Up one level">←</button>
  <nav id="crumbs" aria-label="Level"></nav>
  <div id="legend"></div>
</header>
<main>
  <div id="stage" tabindex="-1"></div>
  <aside id="panel" aria-live="polite"></aside>
</main>
<script id="map-data" type="application/json">__DATA__</script>
<script src="https://cdn.jsdelivr.net/npm/pele@1.8.0/dist/pele.global.js"></script>
<script>
const MAP = JSON.parse(document.getElementById('map-data').textContent);
const ROOT = MAP.__root;
const nodes = MAP.nodes || [], edges = MAP.edges || [], paths = MAP.paths || [];
const findings = MAP.findings || [], unknowns = MAP.unknowns || [];
const byId = new Map(nodes.map(n => [n.id, n]));
const KIND = { service: 'service', datastore: 'datastore', queue: 'queue', external: 'outside system',
  group: 'group', component: 'component' };
const SEVERITY = ['bug', 'risk', 'gap'];
const SEV_LABEL = { bug: 'Bug', risk: 'Risk', gap: 'Gap' };

let trail = [], selected = null, view = { x: 0, y: 0, k: 1 }, graph = null;

const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const childrenOf = id => nodes.filter(n => (n.parent ?? null) === id);
const pathsOf = id => paths.filter(p => p.node === id);
const canOpen = n => childrenOf(n.id).length > 0 || pathsOf(n.id).length > 0;
const current = () => (trail.length ? byId.get(trail[trail.length - 1]) : null);
const sevOf = f => (SEVERITY.includes(f.severity) ? f.severity : 'risk');
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
const sentence = list => (list.length < 2 ? list.join('') : list.slice(0, -1).join(', ') + ' and ' + list[list.length - 1]);
// A component's tech already says what it is ("Service object"), and the bare word says nothing.
const kindLine = n => (n.kind === 'component' ? n.tech || '' : [n.tech, KIND[n.kind] || n.kind].filter(Boolean).join(' '));

// A box's issue count covers everything inside it, so a parent signals what its levels hold.
function subtree(id) {
  const out = new Set([id]);
  for (const c of childrenOf(id)) for (const d of subtree(c.id)) out.add(d);
  return out;
}
const issuesUnder = id => { const s = subtree(id); return findings.filter(f => s.has(f.node)); };
const worst = list => SEVERITY.find(s => list.some(f => sevOf(f) === s));

function parseCite(c) {
  const m = /^(.+?):(\d+)(?:-(\d+))?$/.exec(c);
  return m && { file: m[1], from: +m[2], to: +(m[3] || m[2]) };
}
function cite(c) {
  const r = parseCite(c);
  if (!r) return `<span class="cite">${esc(c)}</span>`;
  const short = r.file.split('/').pop() + ':' + r.from + (r.to !== r.from ? '-' + r.to : '');
  return `<a class="cite" href="vscode://file${encodeURI(ROOT + '/' + r.file)}:${r.from}" title="${esc(c)}">${esc(short)}</a>`;
}
const cites = list => (list && list.length ? `<span class="cites">${list.map(cite).join('')}</span>` : '');
// A finding belongs to a call path step when they cite overlapping lines of the same file.
const overlaps = (a, b) => (a || []).some(x => (b || []).some(y => {
  const p = parseCite(x), q = parseCite(y);
  return p && q && p.file === q.file && p.from <= q.to && q.from <= p.to;
}));

function go(id) { trail.push(id); selected = null; render(); document.getElementById('stage').focus({ preventScroll: true }); }
// Going up selects and focuses the box you came out of, so you keep your place.
function up(depth) {
  const from = trail[depth];
  trail = trail.slice(0, depth); selected = null; render();
  const box = from && document.querySelector(`#canvas .box[data-id="${CSS.escape(from)}"]`);
  if (box) box.focus({ preventScroll: true });
}

const tagKey = (sev, text) => `<span><svg width="20" height="12"><rect x="0" y="0" width="20" height="12" rx="2" fill="var(--${sev})"/>` +
  `<circle cx="4" cy="6" r="1.5" fill="var(--card)"/></svg>${text}</span>`;
function legend(onPaths) {
  const el = document.getElementById('legend');
  if (onPaths) {
    el.innerHTML = `<span class="hint">Click a flag to find its issue in the panel</span>` +
      tagKey('bug', 'bug: wrong today') + tagKey('risk', 'risk: could go wrong') + tagKey('gap', 'gap: missing or unknown');
    return;
  }
  const ln = 'stroke="var(--line)" fill="var(--card)" stroke-width="1.25"';
  el.innerHTML =
    `<span class="hint">Double-click a box to open it</span>` +
    `<span><svg width="16" height="12"><rect x="3" y="3" width="13" height="9" rx="1.5" ${ln}/><rect x="0" y="0" width="13" height="9" rx="1.5" ${ln}/></svg>has a level inside</span>` +
    `<span><svg width="12" height="14"><path d="M1 3v8c0 2.5 10 2.5 10 0V3" ${ln}/><ellipse cx="6" cy="3" rx="5" ry="2" ${ln}/></svg>datastore</span>` +
    `<span><svg width="16" height="11"><path d="M4 1h11l-3 9H1z" ${ln}/></svg>queue</span>` +
    `<span><svg width="18" height="11"><rect x="1" y="1" width="16" height="9" rx="4.5" ${ln} stroke-dasharray="3 2" fill="none"/></svg>outside system</span>` +
    tagKey('bug', 'has a bug inside') + tagKey('risk', 'risks, no bugs') + tagKey('gap', 'gaps only') +
    `<span><svg width="22" height="6"><path d="M0 3h22" stroke="var(--wire)" stroke-width="1.5" stroke-dasharray="1.5 3.5" stroke-linecap="round"/></svg>inferred call</span>`;
}

function render() {
  const here = current();
  document.getElementById('back').disabled = !trail.length;
  const crumbs = document.getElementById('crumbs');
  const parts = [MAP.repo || 'Map', ...trail.map(id => byId.get(id)?.name)];
  crumbs.innerHTML = parts.map((p, i) => i === parts.length - 1
    ? `<span aria-current="page">${esc(p)}</span>`
    : `<button data-depth="${i}">${esc(p)}</button><span class="sep">/</span>`).join('');
  crumbs.querySelectorAll('button').forEach(b => (b.onclick = () => up(+b.dataset.depth)));

  const stage = document.getElementById('stage');
  const boxes = childrenOf(here ? here.id : null);
  graph = null;
  legend(!boxes.length && here && pathsOf(here.id).length > 0);
  if (!boxes.length && here && pathsOf(here.id).length) {
    stage.innerHTML = '<div id="paths">' + pathsOf(here.id).map(p =>
      `<section class="path"><h2>${esc(p.title || 'Call path')}</h2><ol>` +
      p.steps.map(s => {
        const hits = findings.filter(f => overlaps(f.cites, s.cites));
        const flags = SEVERITY.map(sev => {
          const mine = hits.filter(f => sevOf(f) === sev);
          if (!mine.length) return '';
          return `<button class="flag ${sev}" data-findings="${mine.map(f => findings.indexOf(f)).join(' ')}" title="${esc(mine.map(f => f.text).join('\n\n'))}">` +
            `${mine.length > 1 ? plural(mine.length, sev) : SEV_LABEL[sev]}</button>`;
        }).join('');
        return `<li><span class="call">${esc(s.call)}</span><span class="cites">${flags}${(s.cites || []).map(cite).join('')}</span></li>`;
      }).join('') + '</ol></section>').join('') + '</div>';
    stage.querySelectorAll('.flag').forEach(b => (b.onclick = () => flash(b.dataset.findings.split(' '))));
  } else if (!boxes.length) {
    stage.innerHTML = `<p class="empty">${here?.loaded ? `Nothing inside ${esc(here.name)} is big enough for its own box.`
      : `${esc(here?.name || 'This level')} isn't mapped yet. To map it, run <code>/map more detail on ${esc(here?.name || '')}</code>`}</p>`;
  } else if (!window.pele) {
    stage.innerHTML = '<p class="empty">The diagram needs Pele from cdn.jsdelivr.net. Check your connection, then reload.</p>';
  } else {
    draw(stage, boxes);
  }
  panel();
}

// ---------- Drawing ----------

// One wire per pair and direction, its labels joined, so parallel arrows never stack.
function wiresFor(ids) {
  const byPair = new Map();
  for (const e of edges) {
    if (!ids.has(e.from) || !ids.has(e.to) || e.from === e.to) continue;
    const key = e.from + '>' + e.to;
    const w = byPair.get(key) || { from: e.from, to: e.to, labels: [], inferred: true };
    if (e.label && !w.labels.includes(e.label)) w.labels.push(e.label);
    w.inferred = w.inferred && e.evidence === 'inferred';
    byPair.set(key, w);
  }
  return [...byPair.values()];
}
const clip = (s, max) => (s.length > max ? s.slice(0, max - 1) + '…' : s);

// Pele lays out and draws Mermaid flowchart text left to right; callers land on the left and
// what they call (datastores, queues, outside systems) on the right. The page then adds what
// Mermaid cannot say: issue tags, selection, and clicks.
function draw(stage, boxes) {
  const key = new Map(boxes.map((b, i) => [b.id, 'n' + i]));
  const back = new Map([...key].map(([id, k]) => [k, id]));
  // Mermaid reads quotes and backticks inside a label as syntax.
  const text = s => String(s || '').replace(/"/g, "'").replace(/`/g, "'");
  const shape = { datastore: ['[(', ')]'], queue: ['[/', '/]'], external: ['([', '])'] };
  const lines = ['flowchart LR'];
  for (const b of boxes) {
    const [open, close] = shape[b.kind] || ['[', ']'];
    const label = text(b.name) + (b.summary ? '\n' + text(clip(b.summary, 70)) : '');
    lines.push(`  ${key.get(b.id)}${open}"${label}"${close}:::k${b.kind}`);
  }
  const wires = wiresFor(new Set(boxes.map(b => b.id)));
  for (const w of wires) {
    const label = w.labels.length ? clip(w.labels[0], 24) + (w.labels.length > 1 ? ` +${w.labels.length - 1}` : '') : '';
    lines.push(`  ${key.get(w.from)} ${w.inferred ? '-.->' : '-->'}${label ? `|"${text(label)}"|` : ''} ${key.get(w.to)}`);
  }
  const { svg } = pele.render(lines.join('\n'), {
    responsive: false, fontSize: 13, fontFamily: 'Archivo, system-ui, sans-serif', idPrefix: 'map',
  });
  stage.innerHTML = `<div id="canvas">${svg}</div>` +
    '<div id="tools"><button data-z="-1" aria-label="Zoom out">−</button><button data-z="fit" title="Fit to screen">Fit</button><button data-z="1" aria-label="Zoom in">+</button></div>';
  const el = stage.querySelector('#canvas svg');
  el.querySelectorAll('g.pele-node').forEach(g => {
    const id = back.get(g.dataset.id), n = byId.get(id);
    g.classList.add('box');
    g.dataset.id = id;
    g.setAttribute('tabindex', '0');
    g.setAttribute('role', 'button');
    g.setAttribute('aria-pressed', String(selected === id));
    if (selected === id) g.classList.add('selected');
    decorate(g, n);
  });
  el.querySelectorAll('g.pele-edge').forEach(g => {
    const [, from, to] = g.dataset.id.split('_');
    g.classList.add('wire');
    g.dataset.from = back.get(from);
    g.dataset.to = back.get(to);
    const w = wires.find(x => x.from === g.dataset.from && x.to === g.dataset.to);
    if (w && w.labels.length) g.insertAdjacentHTML('afterbegin', `<title>${esc(w.labels.join('\n'))}</title>`);
  });
  graph = { canvas: stage.querySelector('#canvas'), width: +el.getAttribute('width'), height: +el.getAttribute('height') };
  fit();
  interact(stage, el);
}

// The issue tag and the stacked card go on after the SVG is in the page,
// since they are placed from each box's measured size.
function decorate(g, n) {
  const issues = issuesUnder(n.id);
  const inside = childrenOf(n.id).length ? plural(childrenOf(n.id).length, 'part') : plural(pathsOf(n.id).length, 'call path');
  g.setAttribute('aria-label', [n.name, issues.length ? plural(issues.length, 'issue') : '',
    canOpen(n) ? `${inside} inside, press Enter to open` : ''].filter(Boolean).join(', '));
  g.insertAdjacentHTML('afterbegin', `<title>${esc(`${n.name}${n.tech ? ` (${n.tech})` : ''}: ${n.summary || ''}`)}</title>`);
  g._decorate = () => {
    const box = g.getBBox();
    if (n.verified === false) g.classList.add('unverified');
    // The tag clips onto the box's top edge, clear of the wires that meet its sides.
    if (issues.length) {
      const label = String(issues.length), w = 18 + label.length * 7, x = box.x + box.width - w - 12, y = box.y - 8;
      g.insertAdjacentHTML('beforeend', `<g class="tag ${worst(issues)}"><rect x="${x}" y="${y}" width="${w}" height="16" rx="2"/>` +
        `<circle cx="${x + 5}" cy="${y + 8}" r="1.6"/><text x="${x + 11}" y="${y + 12}">${label}</text></g>`);
    }
    // A box with a level inside draws as a stack of cards.
    const shape = g.querySelector('rect, path, polygon, ellipse');
    if (canOpen(n) && shape) {
      const card = shape.cloneNode();
      card.classList.add('stack');
      card.setAttribute('transform', `${shape.getAttribute('transform') || ''} translate(4 4)`);
      g.insertBefore(card, shape);
    }
  };
}

function apply() { graph.canvas.style.transform = `translate(${view.x}px, ${view.y}px) scale(${view.k})`; }
// A level opens no smaller than readable, starting at its left edge if it is wider than that.
// The Fit button shows the whole level, however small that makes it.
function fit(whole = false) {
  const r = document.getElementById('stage').getBoundingClientRect(), pad = 32;
  const k = Math.max(whole ? 0 : 0.75, Math.min(1.15, (r.width - pad * 2) / graph.width, (r.height - pad * 2) / graph.height));
  view = { k, x: Math.max(pad, (r.width - graph.width * k) / 2), y: Math.max(pad, (r.height - graph.height * k) / 2) };
  apply();
}
function zoomAt(factor, cx, cy) {
  const k = Math.min(2.5, Math.max(0.3, view.k * factor));
  view.x = cx - (cx - view.x) * (k / view.k); view.y = cy - (cy - view.y) * (k / view.k); view.k = k;
  apply();
}

// Highlight one box's wires and neighbors and fade the rest.
function light(svg, id) {
  svg.classList.toggle('focus', !!id);
  const near = new Set([id]);
  svg.querySelectorAll('.wire').forEach(w => {
    const on = !!id && (w.dataset.from === id || w.dataset.to === id);
    w.classList.toggle('lit', on);
    if (on) { near.add(w.dataset.from); near.add(w.dataset.to); }
  });
  svg.querySelectorAll('.box').forEach(b => b.classList.toggle('near', near.has(b.dataset.id)));
}

function interact(stage, svg) {
  svg.querySelectorAll('.box').forEach(b => {
    b._decorate();
    const id = b.dataset.id, n = byId.get(id);
    b.addEventListener('click', ev => { ev.stopPropagation(); select(id); });
    b.addEventListener('dblclick', () => canOpen(n) && go(id));
    b.addEventListener('mouseenter', () => light(svg, id));
    b.addEventListener('mouseleave', () => light(svg, selected));
    b.addEventListener('focus', () => select(id));
    b.addEventListener('keydown', ev => { if (ev.key === 'Enter' && canOpen(n)) go(id); });
  });
  light(svg, selected);
  stage.querySelectorAll('#tools button').forEach(z => (z.onclick = () => {
    if (z.dataset.z === 'fit') return fit(true);
    const r = stage.getBoundingClientRect();
    zoomAt(z.dataset.z === '1' ? 1.2 : 1 / 1.2, r.width / 2, r.height / 2);
  }));
  stage.onwheel = ev => {
    ev.preventDefault();
    const r = stage.getBoundingClientRect();
    if (ev.ctrlKey || ev.metaKey) zoomAt(Math.exp(-ev.deltaY * 0.01), ev.clientX - r.left, ev.clientY - r.top);
    else { view.x -= ev.deltaX; view.y -= ev.deltaY; apply(); }
  };
  let drag = null;
  stage.onpointerdown = ev => {
    if (ev.target.closest('.box, #tools')) return;
    drag = { x: ev.clientX, y: ev.clientY, vx: view.x, vy: view.y, moved: false };
    stage.classList.add('dragging');
  };
  stage.onpointermove = ev => {
    if (!drag) return;
    view.x = drag.vx + ev.clientX - drag.x; view.y = drag.vy + ev.clientY - drag.y;
    drag.moved = drag.moved || Math.abs(ev.clientX - drag.x) + Math.abs(ev.clientY - drag.y) > 3;
    apply();
  };
  stage.onpointerup = stage.onpointerleave = () => {
    if (drag && !drag.moved && selected) select(null);
    drag = null; stage.classList.remove('dragging');
  };
}

function select(id) {
  selected = id;
  const svg = document.querySelector('#canvas svg');
  if (svg) {
    svg.querySelectorAll('.box').forEach(b => {
      b.classList.toggle('selected', b.dataset.id === id);
      b.setAttribute('aria-pressed', String(b.dataset.id === id));
    });
    light(svg, id);
  }
  panel();
}

// ---------- Side panel ----------

// The owner link on a card jumps to the box that holds the finding and points at the card there.
function issueCard(f, showOwner, holder) {
  const n = byId.get(f.node), sev = sevOf(f), i = findings.indexOf(f);
  const owner = holder && holder.id !== n?.id
    ? `<button class="on" data-pick="${esc(n?.id)}" data-finding="${i}">in ${esc(holder.name)} › ${esc(n?.name || '')}</button>`
    : showOwner && n ? `<button class="on" data-pick="${esc(n.id)}" data-finding="${i}">in ${esc(n.name)}</button>` : '';
  return `<div class="issue ${sev}" data-finding="${i}"><div class="head"><span class="sev">${SEV_LABEL[sev]}</span>${owner}</div>` +
    `<div>${esc(f.text)}</div>${cites(f.cites)}</div>`;
}
const bySeverity = list => [...list].sort((a, b) => SEVERITY.indexOf(sevOf(a)) - SEVERITY.indexOf(sevOf(b)));

function panel() {
  const el = document.getElementById('panel');
  el.scrollTop = 0;
  const here = current();
  const n = selected ? byId.get(selected) : null;

  if (!n) {
    const levelBoxes = childrenOf(here ? here.id : null);
    const atLevel = new Set([here?.id, ...levelBoxes.map(b => b.id)]);
    // Bugs are wrong today, so one deep inside a box still surfaces at the level that shows the box.
    const holderOf = new Map();
    levelBoxes.forEach(b => issuesUnder(b.id).forEach(f => f.node !== b.id && sevOf(f) === 'bug' && holderOf.set(f, b)));
    // A call path level also lists findings elsewhere that cite lines its steps run through.
    const steps = here ? pathsOf(here.id).flatMap(p => p.steps) : [];
    const onSteps = bySeverity(findings.filter(f => steps.some(s => overlaps(f.cites, s.cites))));
    const issues = bySeverity([...findings.filter(f => atLevel.has(f.node) && !onSteps.includes(f)), ...holderOf.keys()]);
    const deeper = levelBoxes.map(b => [b, issuesUnder(b.id).filter(f => f.node !== b.id && !holderOf.has(f)).length])
      .filter(([, c]) => c > 0);
    const gaps = unknowns.filter(u => (u.node ?? null) === (here?.id ?? null) || levelBoxes.some(b => b.id === u.node));
    const kinds = {};
    levelBoxes.forEach(b => (kinds[b.kind] = (kinds[b.kind] || 0) + 1));
    const counts = sentence(Object.entries(kinds).map(([k, c]) => plural(c, KIND[k] || k)));
    el.innerHTML = (here
      ? `<h2>${esc(here.name)}</h2><div class="meta">${esc(kindLine(here))}${cites(here.cites)}</div>
         <p class="lede">${esc(here.summary || '')}</p>`
      : (MAP.summary ? `<p class="lede" style="margin-top:0">${esc(MAP.summary)}</p>` : '')) +
      (counts ? `<p class="counts">${esc(counts[0].toUpperCase() + counts.slice(1))}.</p>` : '') +
      (onSteps.length ? `<h3>${plural(onSteps.length, 'issue')} on these call paths</h3>` +
        onSteps.map(f => issueCard(f, f.node !== here?.id)).join('') : '') +
      (issues.length ? `<h3>${onSteps.length ? `${plural(issues.length, 'other issue')} in ${esc(here.name)}` : plural(issues.length, 'issue')}</h3>` +
        issues.map(f => issueCard(f, f.node !== here?.id, holderOf.get(f))).join('') : '') +
      (deeper.length ? `<p class="empty-note">More issues inside ` + sentence(deeper.map(([b, c]) =>
        `<button data-open="${esc(b.id)}">${esc(b.name)} (${c})</button>`)) + '</p>' : '') +
      (!issues.length && !onSteps.length && !deeper.length ? '<h3>No issues found here</h3>' : '') +
      (gaps.length ? `<details><summary>${plural(gaps.length, 'open question')}</summary>` +
        gaps.map(u => `<p>${u.node ? `<strong>${esc(byId.get(u.node)?.name)}</strong>: ` : ''}${esc(u.text)}</p>`).join('') + '</details>' : '');
  } else {
    const into = edges.filter(e => e.to === n.id), out = edges.filter(e => e.from === n.id);
    const row = (e, dir) => {
      const other = byId.get(dir === 'out' ? e.to : e.from);
      return `<div class="row"><button class="who" data-pick="${esc(other?.id)}">${esc(other?.name)}</button>
        <span class="what">${esc(e.label || '')}${e.evidence === 'inferred' ? ' (inferred)' : ''}</span>${cites(e.cites)}</div>`;
    };
    const own = bySeverity(issuesUnder(n.id));
    const kids = childrenOf(n.id).length, ps = pathsOf(n.id).length;
    el.innerHTML = `<h2>${esc(n.name)}</h2>
      <div class="meta">${esc([kindLine(n), n.verified === false ? 'not yet checked' : ''].filter(Boolean).join(', '))}${cites(n.cites)}</div>
      <p class="lede">${esc(n.summary || '')}</p>` +
      (canOpen(n) ? `<button class="primary" id="open">Open ${kids ? plural(kids, 'part') : plural(ps, 'call path')}</button>` : '') +
      (own.length ? `<h3>${plural(own.length, 'issue')}</h3>` + own.map(f => issueCard(f, f.node !== n.id)).join('') : '') +
      (into.length ? '<h3>Called by</h3>' + into.map(e => row(e, 'in')).join('') : '') +
      (out.length ? '<h3>Calls</h3>' + out.map(e => row(e, 'out')).join('') : '') +
      (unknowns.some(u => u.node === n.id) ? `<details><summary>Open questions</summary>` +
        unknowns.filter(u => u.node === n.id).map(u => `<p>${esc(u.text)}</p>`).join('') + '</details>' : '');
    document.getElementById('open')?.addEventListener('click', () => go(n.id));
  }
  el.querySelectorAll('[data-pick]').forEach(b => (b.onclick = () => pick(b.dataset.pick, b.dataset.finding)));
  el.querySelectorAll('[data-open]').forEach(b => (b.onclick = () => go(b.dataset.open)));
}

// Jump to a box from the panel: open the level that holds it, select it, and point at the finding if one was clicked.
function pick(id, finding) {
  const chain = [];
  for (let p = byId.get(id)?.parent; p; p = byId.get(p)?.parent) chain.unshift(p);
  if (chain.join('/') !== trail.join('/')) { trail = chain; selected = id; render(); }
  else select(id);
  if (finding != null) flash([finding]);
}
// Scroll the panel to the cards for these findings and mark them briefly.
function flash(ids) {
  const cards = ids.map(i => document.querySelector(`#panel .issue[data-finding="${i}"]`)).filter(Boolean);
  cards[0]?.scrollIntoView({ block: 'nearest' });
  cards.forEach(c => { c.classList.add('flash'); setTimeout(() => c.classList.remove('flash'), 1200); });
}

document.getElementById('back').onclick = () => trail.length && up(trail.length - 1);
document.addEventListener('keydown', ev => {
  if (ev.key !== 'Escape') return;
  if (selected) select(null); else if (trail.length) up(trail.length - 1);
});
window.addEventListener('resize', () => graph && fit());
// Pele measures label text to size boxes, so it waits for the web font.
Promise.all(['400 13px Archivo', '600 13px Archivo'].map(f => document.fonts?.load(f))).catch(() => {}).then(render);
</script>
</body>
</html>
"""


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    repo, map_path, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), Path(sys.argv[3])
    data = json.loads(map_path.read_text())
    data["__root"] = str(repo)
    # Keep the embedded JSON from closing its own script tag.
    payload = json.dumps(data).replace("</", "<\\/")
    title = data.get("repo") or repo.name
    html = TEMPLATE.replace("__DATA__", payload).replace(
        "__TITLE__", title.replace("&", "&amp;").replace("<", "&lt;")
    )
    out.write_text(html)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

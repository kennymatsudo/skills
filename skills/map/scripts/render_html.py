#!/usr/bin/env python3
"""Render a map file as one self-contained HTML page for a browser.

Usage: render_html.py <repo-root> <map.json> <out.html>

The page draws one level at a time, left to right, with Pele, a Mermaid
renderer: callers on the left, and the datastores, queues, and outside systems
they call on the right. Each box shows its name and role, so a level reads
without clicking. Clicking a box shows its connections and issues in the side
panel; double-clicking it, or its Open button, goes one level down. Citations
open the cited line in VS Code. Everything but Pele and two web fonts is
inline, so the file opens straight from disk.
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
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
  --canvas: #f4f5f2; --dot: #dcdfd8; --box: #ffffff; --ink: #191c1a; --soft: #5f6661; --faint: #8c938e;
  --rule: #dfe2dc; --wire: #a9b0aa; --accent: #0f6e66; --accent-wash: #e1f0ec;
  --data: #2f5d8a; --data-wash: #e6eef6; --async: #7a5a12; --async-wash: #f5eedd;
  --ext: #6b6f6c; --ext-wash: #eeefec;
  --bug: #c2361f; --bug-wash: #fbe9e5; --risk: #b26a00; --risk-wash: #fbf0dc; --gap: #5f6661; --gap-wash: #eceeea;
  --panel: #fbfbf9; --shadow: 0 1px 2px rgba(20,30,25,.06), 0 2px 8px rgba(20,30,25,.05);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --canvas: #121514; --dot: #1f2422; --box: #1b201e; --ink: #e6ebe8; --soft: #a0aaa5; --faint: #78827d;
    --rule: #2a312e; --wire: #4f5a55; --accent: #5cc4b6; --accent-wash: #173230;
    --data: #82b1de; --data-wash: #182634; --async: #d9b45f; --async-wash: #2c2414;
    --ext: #a3a8a5; --ext-wash: #202523;
    --bug: #f07a63; --bug-wash: #3a1d17; --risk: #f0b04a; --risk-wash: #33270f; --gap: #a0aaa5; --gap-wash: #232826;
    --panel: #161a19; --shadow: 0 1px 2px rgba(0,0,0,.4);
  }
}
* { box-sizing: border-box; }
html, body { height: 100%; }
body { margin: 0; background: var(--canvas); color: var(--ink);
  font: 14px/1.5 Inter, system-ui, sans-serif; display: grid; grid-template-rows: auto 1fr; }
.mono, .cite { font-family: "JetBrains Mono", ui-monospace, monospace; }
button { font: inherit; color: inherit; }

header { display: flex; align-items: center; gap: 12px; padding: 10px 16px;
  border-bottom: 1px solid var(--rule); background: var(--panel); min-width: 0; }
#back { width: 30px; height: 30px; flex: none; border-radius: 8px; border: 1px solid var(--rule);
  background: var(--box); cursor: pointer; }
#back:disabled { opacity: .3; cursor: default; }
#crumbs { display: flex; flex-wrap: wrap; gap: 6px; align-items: baseline; font-size: 16px; font-weight: 600; min-width: 0; }
#crumbs button { font-weight: 400; color: var(--soft); background: none; border: 0; padding: 0; cursor: pointer; }
#crumbs button:hover { color: var(--accent); }
#crumbs .sep { color: var(--faint); font-weight: 400; }
#legend { margin-left: auto; display: flex; gap: 14px; color: var(--soft); font-size: 12px; flex-wrap: wrap; }
#legend span { display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; }
#legend i { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
@media (max-width: 860px) { #legend { display: none; } }

main { display: grid; grid-template-columns: minmax(0, 1fr) 380px; min-height: 0; }
@media (max-width: 860px) { main { grid-template-columns: 1fr; grid-template-rows: 60vh auto; } }

#stage { position: relative; overflow: hidden; min-height: 0; cursor: grab; touch-action: none;
  background-image: radial-gradient(var(--dot) 1px, transparent 1px); background-size: 18px 18px; }
#stage.dragging { cursor: grabbing; }
#tools { position: absolute; right: 14px; bottom: 14px; display: flex; border: 1px solid var(--rule);
  border-radius: 8px; overflow: hidden; background: var(--box); box-shadow: var(--shadow); }
#tools button { min-width: 34px; height: 30px; border: 0; background: none; cursor: pointer; padding: 0 8px; font-size: 13px; }
#tools button + button { border-left: 1px solid var(--rule); }

/* Pele's drawing, themed to the page */
#canvas { position: absolute; left: 0; top: 0; transform-origin: 0 0; }
#canvas svg.pele { --pele-bg: var(--canvas); --pele-fg: var(--ink); --pele-muted: var(--soft); --pele-line: var(--wire);
  --pele-surface: var(--box); --pele-surface-alt: var(--panel); --pele-border: var(--rule); --pele-accent: var(--accent);
  --pele-font: Inter, system-ui, sans-serif; --pele-radius: 8px; display: block; overflow: visible; }
.box { cursor: pointer; }
.box :is(rect, path, polygon, ellipse) { stroke-width: 1.25; }
.box.kservice :is(rect, path, polygon), .box.kgroup :is(rect, path, polygon), .box.kcomponent :is(rect, path, polygon) { stroke: var(--accent) !important; }
.box.kdatastore :is(rect, path, polygon, ellipse) { stroke: var(--data) !important; fill: var(--data-wash); }
.box.kqueue :is(rect, path, polygon) { stroke: var(--async) !important; fill: var(--async-wash); }
.box.kexternal :is(rect, path, polygon) { stroke: var(--wire) !important; stroke-dasharray: 4 3; fill: var(--ext-wash); }
.box.unverified :is(rect, path, polygon, ellipse) { stroke-dasharray: 2 3; }
.box text.pele-label tspan:first-child { font-weight: 600; }
.box text.pele-label tspan:not(:first-child) { fill: var(--soft); }
.box:hover :is(rect, path, polygon, ellipse), .box.selected :is(rect, path, polygon, ellipse) { stroke-width: 2.5; }
.box:focus { outline: none; }
.box .stack { fill: var(--box) !important; stroke-width: 1 !important; stroke-dasharray: none !important; opacity: .9; }
.box .pill.bug rect { fill: var(--bug); } .box .pill.risk rect { fill: var(--risk); } .box .pill.gap rect { fill: var(--gap); }
.box .pill text { fill: #fff; font-size: 10.5px; font-weight: 600; }
.wire.lit path { stroke: var(--accent); stroke-width: 2; }
.wire.lit path.pele-marker { fill: var(--accent); }
.focus .wire:not(.lit) { opacity: .15; }
.focus .box:not(.near) { opacity: .4; }
@media (prefers-reduced-motion: no-preference) { .wire, .box { transition: opacity .12s; } }

/* Panel */
aside { background: var(--panel); border-left: 1px solid var(--rule); overflow: auto; padding: 20px 20px 40px; }
@media (max-width: 860px) { aside { border-left: 0; border-top: 1px solid var(--rule); } }
aside h2 { font-size: 18px; line-height: 1.25; margin: 0; }
aside h3 { font-size: 11.5px; text-transform: uppercase; letter-spacing: .06em; color: var(--faint);
  margin: 22px 0 6px; font-weight: 600; }
aside p { margin: 6px 0; }
.meta { color: var(--soft); font-size: 12.5px; margin-top: 2px; }
.lede { font-size: 14px; margin-top: 10px; }
.primary { margin-top: 12px; font-weight: 600; color: #fff; background: var(--accent); border: 0;
  border-radius: 7px; padding: 6px 12px; cursor: pointer; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .primary { color: #0b1514; } }
.issue { border-left: 3px solid var(--risk); background: var(--risk-wash); border-radius: 0 6px 6px 0;
  padding: 7px 10px; margin: 6px 0; font-size: 13px; }
.issue.bug { border-color: var(--bug); background: var(--bug-wash); }
.issue.gap { border-color: var(--gap); background: var(--gap-wash); }
.issue .sev { font-size: 10.5px; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; color: var(--risk); }
.issue.bug .sev { color: var(--bug); } .issue.gap .sev { color: var(--gap); }
.issue .on { font-size: 12px; font-weight: 600; background: none; border: 0; padding: 0; cursor: pointer; color: var(--ink); }
.issue .on:hover { color: var(--accent); }
.row { display: grid; grid-template-columns: 16px minmax(0, 1fr) auto; gap: 6px; align-items: baseline;
  padding: 5px 0; border-bottom: 1px solid var(--rule); font-size: 13px; }
.row:last-child { border-bottom: 0; }
.row .dir { color: var(--faint); }
.row .who { font-weight: 500; background: none; border: 0; padding: 0; cursor: pointer; text-align: left; }
.row .who:hover { color: var(--accent); }
.row .what { color: var(--soft); }
.cites { display: inline-flex; flex-wrap: wrap; gap: 2px 8px; }
a.cite { color: var(--accent); text-decoration: none; font-size: 11.5px; white-space: nowrap; }
a.cite:hover { text-decoration: underline; }
details { margin-top: 18px; }
details summary { cursor: pointer; font-size: 11.5px; text-transform: uppercase; letter-spacing: .06em; color: var(--faint); font-weight: 600; }
details p { font-size: 13px; color: var(--soft); }
.counts { display: flex; flex-wrap: wrap; gap: 6px 14px; color: var(--soft); font-size: 12.5px; margin-top: 10px; }
.empty-note { color: var(--soft); font-size: 13px; }

/* Call paths */
#paths { position: absolute; inset: 0; overflow: auto; padding: 28px; cursor: default; background: var(--canvas); }
.path { max-width: 820px; margin: 0 auto 28px; background: var(--box); border: 1px solid var(--rule);
  border-radius: 10px; box-shadow: var(--shadow); }
.path h2 { font-size: 15px; margin: 0; padding: 12px 16px; border-bottom: 1px solid var(--rule); }
.path ol { list-style: none; margin: 0; padding: 6px 0; counter-reset: s; }
.path li { counter-increment: s; display: grid; grid-template-columns: 28px minmax(0, 1fr) auto; gap: 8px;
  padding: 7px 16px; align-items: baseline; font-size: 13.5px; }
.path li::before { content: counter(s); color: var(--faint); font-size: 12px; text-align: right; }
.path li + li { border-top: 1px dashed var(--rule); }
.empty { position: absolute; inset: 0; display: grid; place-items: center; padding: 24px; color: var(--soft); text-align: center; cursor: default; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
</style>
</head>
<body>
<header>
  <button id="back" title="Up one level (Esc)" aria-label="Up one level">←</button>
  <nav id="crumbs" aria-label="Level"></nav>
  <div id="legend" aria-hidden="true"></div>
</header>
<main>
  <div id="stage"></div>
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
const KIND = { service: 'Service', datastore: 'Datastore', queue: 'Queue', external: 'Outside system',
  group: 'Group', component: 'Component' };
const SEVERITY = ['bug', 'risk', 'gap'];

let trail = [], selected = null, view = { x: 0, y: 0, k: 1 }, graph = null;

const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const childrenOf = id => nodes.filter(n => (n.parent ?? null) === id);
const pathsOf = id => paths.filter(p => p.node === id);
const canOpen = n => childrenOf(n.id).length > 0 || pathsOf(n.id).length > 0;
const current = () => (trail.length ? byId.get(trail[trail.length - 1]) : null);
const sevOf = f => (SEVERITY.includes(f.severity) ? f.severity : 'risk');
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;

// A box's issue count covers everything inside it, so a parent signals what its levels hold.
function subtree(id) {
  const out = new Set([id]);
  for (const c of childrenOf(id)) for (const d of subtree(c.id)) out.add(d);
  return out;
}
const issuesUnder = id => { const s = subtree(id); return findings.filter(f => s.has(f.node)); };
const worst = list => SEVERITY.find(s => list.some(f => sevOf(f) === s));

function cite(c) {
  const m = /^(.+?):(\d+)(?:-(\d+))?$/.exec(c);
  if (!m) return `<span class="cite">${esc(c)}</span>`;
  const short = m[1].split('/').pop() + ':' + m[2] + (m[3] ? '-' + m[3] : '');
  return `<a class="cite" href="vscode://file${encodeURI(ROOT + '/' + m[1])}:${m[2]}" title="${esc(c)}">${esc(short)}</a>`;
}
const cites = list => (list && list.length ? `<span class="cites">${list.map(cite).join('')}</span>` : '');

function go(id) { trail.push(id); selected = null; render(); }
function up(depth) { trail = trail.slice(0, depth); selected = null; render(); }

function legend() {
  document.getElementById('legend').innerHTML =
    `<span><i style="background:var(--accent)"></i>service</span><span><i style="background:var(--async)"></i>queue</span>` +
    `<span><i style="background:var(--data)"></i>datastore</span><span><i style="border:1px dashed var(--wire);background:var(--ext-wash)"></i>outside</span>` +
    `<span><svg width="22" height="6"><path d="M0 3h22" stroke="var(--wire)" stroke-dasharray="1.5 3.5" stroke-linecap="round"/></svg>inferred</span>`;
}

function render() {
  const here = current();
  document.getElementById('back').disabled = !trail.length;
  const crumbs = document.getElementById('crumbs');
  const parts = [MAP.repo || 'Map', ...trail.map(id => byId.get(id)?.name)];
  crumbs.innerHTML = parts.map((p, i) => i === parts.length - 1
    ? `<span>${esc(p)}</span>`
    : `<button data-depth="${i}">${esc(p)}</button><span class="sep">/</span>`).join('');
  crumbs.querySelectorAll('button').forEach(b => (b.onclick = () => up(+b.dataset.depth)));

  const stage = document.getElementById('stage');
  const boxes = childrenOf(here ? here.id : null);
  if (!boxes.length && here && pathsOf(here.id).length) {
    stage.innerHTML = '<div id="paths">' + pathsOf(here.id).map(p =>
      `<section class="path"><h2>${esc(p.title || 'Call path')}</h2><ol>` +
      p.steps.map(s => `<li><span>${esc(s.call)}</span>${cites(s.cites)}</li>`).join('') + '</ol></section>').join('') + '</div>';
  } else if (!boxes.length) {
    stage.innerHTML = `<p class="empty">${here?.loaded ? `Nothing inside ${esc(here.name)} is worth a box.`
      : `Not mapped yet. Run <span class="mono">/map more detail on ${esc(here?.name || '')}</span>.`}</p>`;
  } else if (!window.pele) {
    stage.innerHTML = '<p class="empty">The diagram draws with Pele from cdn.jsdelivr.net. Check the connection and reload.</p>';
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
// Mermaid cannot say: issue counts, selection, and clicks.
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
    responsive: false, fontSize: 13, fontFamily: 'Inter, system-ui, sans-serif', idPrefix: 'map',
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
    g.setAttribute('aria-label', n.name);
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

// The issue count and the open mark go on after the SVG is in the page,
// since they are placed from each box's measured size.
function decorate(g, n) {
  const issues = issuesUnder(n.id);
  const tip = `${n.name}${n.tech ? ` (${n.tech})` : ''}: ${n.summary || ''}` +
    (issues.length ? `\n${plural(issues.length, 'issue')}` : '') + (canOpen(n) ? '\nDouble-click to open' : '');
  g.insertAdjacentHTML('afterbegin', `<title>${esc(tip)}</title>`);
  g._decorate = () => {
    const box = g.getBBox();
    let extra = '';
    if (issues.length) {
      extra += `<g class="pill ${worst(issues)}"><rect x="${box.x + box.width - 14}" y="${box.y - 8}" width="${issues.length > 9 ? 26 : 20}" height="16" rx="8"/>` +
        `<text x="${box.x + box.width - 14 + (issues.length > 9 ? 13 : 10)}" y="${box.y + 3.5}" text-anchor="middle">${issues.length}</text></g>`;
    }
    if (n.verified === false) g.classList.add('unverified');
    g.insertAdjacentHTML('beforeend', extra);
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
function fit() {
  const r = document.getElementById('stage').getBoundingClientRect(), pad = 32;
  // Never shrink below readable; a level wider than that starts at its left edge and pans.
  const k = Math.max(0.72, Math.min(1.15, (r.width - pad * 2) / graph.width, (r.height - pad * 2) / graph.height));
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
    if (z.dataset.z === 'fit') return fit();
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
    svg.querySelectorAll('.box').forEach(b => b.classList.toggle('selected', b.dataset.id === id));
    light(svg, id);
  }
  panel();
}

// ---------- Side panel ----------

function issueCard(f, showOwner) {
  const n = byId.get(f.node), sev = sevOf(f);
  return `<div class="issue ${sev}"><span class="sev">${sev}</span>` +
    (showOwner && n ? ` · <button class="on" data-pick="${esc(n.id)}">${esc(n.name)}</button>` : '') +
    `<div>${esc(f.text)}</div>${cites(f.cites)}</div>`;
}
const bySeverity = list => [...list].sort((a, b) => SEVERITY.indexOf(sevOf(a)) - SEVERITY.indexOf(sevOf(b)));

function panel() {
  const el = document.getElementById('panel');
  const here = current();
  const n = selected ? byId.get(selected) : null;

  if (!n) {
    const levelBoxes = childrenOf(here ? here.id : null);
    const atLevel = new Set([here?.id, ...levelBoxes.map(b => b.id)]);
    const issues = bySeverity(findings.filter(f => atLevel.has(f.node)));
    const deeper = levelBoxes.map(b => [b, issuesUnder(b.id).length - findings.filter(f => f.node === b.id).length])
      .filter(([, c]) => c > 0);
    const gaps = unknowns.filter(u => (u.node ?? null) === (here?.id ?? null) || levelBoxes.some(b => b.id === u.node));
    const kinds = {};
    levelBoxes.forEach(b => (kinds[b.kind] = (kinds[b.kind] || 0) + 1));
    const counts = Object.entries(kinds).map(([k, c]) => plural(c, (KIND[k] || k).toLowerCase())).join(' · ');
    el.innerHTML = (here
      ? `<h2>${esc(here.name)}</h2><div class="meta">${esc([KIND[here.kind], here.tech].filter(Boolean).join(' · '))} ${cites(here.cites)}</div>
         <p class="lede">${esc(here.summary || '')}</p>`
      : (MAP.summary ? `<p class="lede" style="margin-top:0">${esc(MAP.summary)}</p>` : '')) +
      (counts ? `<div class="counts">${esc(counts)}</div>` : '') +
      (issues.length ? `<h3>${plural(issues.length, 'issue')}</h3>` + issues.map(f => issueCard(f, f.node !== here?.id)).join('') : '') +
      (deeper.length ? `<p class="empty-note">More inside ` + deeper.map(([b, c]) =>
        `<button class="on" data-open="${esc(b.id)}">${esc(b.name)} (${c})</button>`).join(', ') + '</p>' : '') +
      (!issues.length && !deeper.length ? '<h3>No issues found</h3>' : '') +
      (gaps.length ? `<details><summary>${plural(gaps.length, 'open question')}</summary>` +
        gaps.map(u => `<p>${u.node ? `<strong>${esc(byId.get(u.node)?.name)}</strong>: ` : ''}${esc(u.text)}</p>`).join('') + '</details>' : '');
  } else {
    const into = edges.filter(e => e.to === n.id), out = edges.filter(e => e.from === n.id);
    const row = (e, dir) => {
      const other = byId.get(dir === 'out' ? e.to : e.from);
      return `<div class="row"><span class="dir">${dir === 'out' ? '→' : '←'}</span>
        <span><button class="who" data-pick="${esc(other?.id)}">${esc(other?.name)}</button> <span class="what">${esc(e.label || '')}${e.evidence === 'inferred' ? ' (inferred)' : ''}</span></span>${cites(e.cites)}</div>`;
    };
    const own = bySeverity(issuesUnder(n.id));
    const kids = childrenOf(n.id).length, ps = pathsOf(n.id).length;
    el.innerHTML = `<h2>${esc(n.name)}</h2>
      <div class="meta">${esc([KIND[n.kind] || n.kind, n.tech, n.verified === false ? 'not yet checked' : null].filter(Boolean).join(' · '))} ${cites(n.cites)}</div>
      <p class="lede">${esc(n.summary || '')}</p>` +
      (canOpen(n) ? `<button class="primary" id="open">Open · ${kids ? plural(kids, 'part') : plural(ps, 'call path')}</button>` : '') +
      (own.length ? `<h3>${plural(own.length, 'issue')}</h3>` + own.map(f => issueCard(f, f.node !== n.id)).join('') : '') +
      (into.length ? '<h3>Called by</h3>' + into.map(e => row(e, 'in')).join('') : '') +
      (out.length ? '<h3>Calls</h3>' + out.map(e => row(e, 'out')).join('') : '') +
      (unknowns.some(u => u.node === n.id) ? `<details><summary>Open questions</summary>` +
        unknowns.filter(u => u.node === n.id).map(u => `<p>${esc(u.text)}</p>`).join('') + '</details>' : '');
    document.getElementById('open')?.addEventListener('click', () => go(n.id));
  }
  el.querySelectorAll('[data-pick]').forEach(b => (b.onclick = () => pick(b.dataset.pick)));
  el.querySelectorAll('[data-open]').forEach(b => (b.onclick = () => go(b.dataset.open)));
}

// Jump to a box from the panel: open the level that holds it, then select it.
function pick(id) {
  const chain = [];
  for (let p = byId.get(id)?.parent; p; p = byId.get(p)?.parent) chain.unshift(p);
  if (chain.join('/') !== trail.join('/')) { trail = chain; selected = id; render(); }
  else select(id);
}

document.getElementById('back').onclick = () => trail.length && up(trail.length - 1);
document.addEventListener('keydown', ev => {
  if (ev.key !== 'Escape') return;
  if (selected) select(null); else if (trail.length) up(trail.length - 1);
});
window.addEventListener('resize', () => graph && document.querySelector('#canvas') && fit());
legend();
render();
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

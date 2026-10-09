/* PerformApp : interface. Trois onglets : Séance (saisie), Progrès (graphique), Données (export / import). */
(function () {
'use strict';
const { uid, todayStr, dayNum, dayStr, parseNum, fmt, METRICS, doneSets, isDone, getSeries, getPrev } = PA;
const KEY = 'performapp.v1', UIKEY = 'performapp.ui', PREVKEY = 'performapp.prev';
const $ = (s, r = document) => r.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

/* ------------------------------------------------------------ état */
function load() {
  try { const raw = localStorage.getItem(KEY); if (raw) return PA.normalizeDb(JSON.parse(raw)); } catch (e) { /* base vide */ }
  return PA.emptyDb();
}
let db = load();
let saved = {}; try { saved = JSON.parse(localStorage.getItem(UIKEY) || '{}'); } catch (e) { /* ignore */ }
const ui = Object.assign({ tab: 'seance', currentId: null, sel: [], colors: {}, metric: 'max_weight', period: '365', pct: false, stepW: 0.5, stepR: 1 }, saved);
ui.view = null; ui.point = null; ui.newDate = null; ui.rest = null;
if (ui.currentId && !db.sessions.some(s => s.id === ui.currentId)) ui.currentId = null;

let saveTimer = 0;
function persistUi() { try { localStorage.setItem(UIKEY, JSON.stringify({ tab: ui.tab, currentId: ui.currentId, sel: ui.sel, colors: ui.colors, metric: ui.metric, period: ui.period, pct: ui.pct, stepW: ui.stepW, stepR: ui.stepR })); } catch (e) { /* ignore */ } }
function save(immediate) {
  db.meta.changes = (db.meta.changes || 0) + 1;
  const run = () => { try { localStorage.setItem(KEY, JSON.stringify(db)); persistUi(); } catch (e) { toast('Enregistrement impossible : espace de stockage plein.'); } };
  clearTimeout(saveTimer);
  if (immediate) run(); else saveTimer = setTimeout(run, 300);
  if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(() => {});
}
window.addEventListener('pagehide', () => { clearTimeout(saveTimer); try { localStorage.setItem(KEY, JSON.stringify(db)); persistUi(); } catch (e) { /* ignore */ } });

/* --------------------------------------------------------- helpers */
const exById = id => db.exercises.find(e => e.id === id);
const curSession = () => db.sessions.find(s => s.id === ui.currentId) || null;
const mmss = s => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, '0')}`;
function dateLabel(str, long) {
  if (str === todayStr()) return "Aujourd'hui";
  if (str === dayStr(dayNum(todayStr()) - 1)) return 'Hier';
  const d = new Date(str + 'T12:00:00');
  return d.toLocaleDateString('fr-FR', long ? { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' } : { weekday: 'short', day: 'numeric', month: 'short' });
}
const dShort = str => new Date(str + 'T12:00:00').toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
const dFull = str => new Date(str + 'T12:00:00').toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
const compactSet = s => `${s.w != null ? fmt(s.w) + '×' : ''}${fmt(s.r)}`;
const RPE = [['😫', 'À bout'], ['😕', 'Fatigué'], ['😐', 'Moyen'], ['🙂', 'Bien'], ['😄', 'Au top']];
function lastUsed(exId) { let d = ''; for (const s of db.sessions) if (s.date > d && s.entries.some(e => e.exercise_id === exId)) d = s.date; return d; }
const sortedExercises = () => [...db.exercises].sort((a, b) => lastUsed(b.id).localeCompare(lastUsed(a.id)) || a.name.localeCompare(b.name, 'fr'));

let toastTimer = 0;
function toast(msg) { const t = $('#toast'); t.textContent = msg; t.style.display = 'block'; clearTimeout(toastTimer); toastTimer = setTimeout(() => { t.style.display = 'none'; }, 2600); }

function openSheet(html, mount) {
  $('#sheet .in').innerHTML = '<div class="grab"></div>' + html;
  $('#scrim').style.display = 'block'; $('#sheet').style.display = 'block';
  if (mount) mount($('#sheet .in'));
}
function closeSheet() { $('#scrim').style.display = 'none'; $('#sheet').style.display = 'none'; $('#sheet .in').innerHTML = ''; }
$('#scrim').addEventListener('click', closeSheet);
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSheet(); });
function confirmSheet(title, text, okLabel, onOk, danger = true) {
  openSheet(`<h2>${esc(title)}</h2><p class="muted">${esc(text)}</p><div class="stack"><button class="btn wide ${danger ? 'danger' : 'primary'}" data-ok>${esc(okLabel)}</button><button class="btn wide" data-cancel>Annuler</button></div>`,
    el => { $('[data-ok]', el).onclick = () => { closeSheet(); onOk(); }; $('[data-cancel]', el).onclick = closeSheet; });
}

/* ======================================================== SÉANCE */
function startSession(date) {
  const s = { id: uid(), date: date || ui.newDate || todayStr(), rpe: null, notes: '', entries: [] };
  db.sessions.push(s); db.sessions.sort((a, b) => a.date.localeCompare(b.date));
  ui.currentId = s.id; return s;
}
function newEntry(exId, sessionId) {
  const prev = getPrev(db, exId, sessionId);
  const n = prev ? clamp(doneSets(prev.entry.sets).length, 1, 6) : 3;
  return { id: uid(), exercise_id: exId, showTempo: prev ? prev.entry.showTempo : false,
           sets: Array.from({ length: n }, () => ({ w: null, r: null, tempo: '', rest: null, done: false })) };
}
function addExercise(exId) {
  const s = curSession() || startSession();
  if (s.entries.some(e => e.exercise_id === exId)) { toast('Cet exercice est déjà dans la séance.'); return; }
  s.entries.push(newEntry(exId, s.id));
  save(); render();
  requestAnimationFrame(() => { const cards = document.querySelectorAll('.ex'); if (cards.length) cards[cards.length - 1].scrollIntoView({ block: 'center', behavior: 'smooth' }); });
}

function phFor(entry, i, prev) {
  const ps = prev ? doneSets(prev.entry.sets) : [];
  if (ps[i]) return { w: ps[i].w, r: ps[i].r };
  if (i > 0) { const p = entry.sets[i - 1], pp = phFor(entry, i - 1, prev); return { w: p.w ?? pp.w, r: p.r ?? pp.r }; }
  return ps.length ? { w: ps[ps.length - 1].w, r: ps[ps.length - 1].r } : { w: null, r: null };
}

const CHECK = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';

function entryCard(entry, s) {
  const ex = exById(entry.exercise_id); if (!ex) return '';
  const prev = getPrev(db, entry.exercise_id, s.id);
  const last = prev ? `Dernière fois (${dShort(prev.session.date)}) : ${doneSets(prev.entry.sets).slice(0, 4).map(compactSet).join(' · ')}${doneSets(prev.entry.sets).length > 4 ? ' …' : ''}` : 'Première fois : tes valeurs seront pré-remplies la prochaine fois.';
  const rows = entry.sets.map((st, i) => {
    const ph = phFor(entry, i, prev), done = isDone(st);
    return `<div class="set ${done ? 'done' : ''}" data-i="${i}">
      <span class="n">${i + 1}</span>
      <label class="fld"><span class="sr">Poids de la série ${i + 1}</span><input class="num" inputmode="decimal" autocomplete="off" data-f="w" value="${esc(fmt(st.w))}" placeholder="${esc(fmt(ph.w))}"><small>kg</small></label>
      <label class="fld"><span class="sr">Répétitions de la série ${i + 1}</span><input class="num" inputmode="decimal" autocomplete="off" data-f="r" value="${esc(fmt(st.r))}" placeholder="${esc(fmt(ph.r))}"><small>reps</small></label>
      <button class="chk" type="button" data-act="chk" aria-pressed="${done}" aria-label="${done ? 'Annuler' : 'Valider'} la série ${i + 1}">${CHECK}</button>
      ${entry.showTempo || st.rest != null ? `<div class="extra">
        ${entry.showTempo ? `<label class="fld"><span class="sr">Tempo</span><input class="num" autocomplete="off" data-f="tempo" value="${esc(st.tempo)}" placeholder="3-1-2"><small>tempo</small></label>` : ''}
        ${st.rest != null ? `<span>repos ${mmss(st.rest)}</span>` : ''}</div>` : ''}
    </div>`;
  }).join('');
  return `<section class="ex" data-eid="${entry.id}">
    <header><div><h3>${esc(ex.name)}</h3><div class="last">${esc(last)}</div></div>
      <button class="ico" type="button" data-act="ex-menu" aria-label="Options de ${esc(ex.name)}"><svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="1.2"/><circle cx="12" cy="12" r="1.2"/><circle cx="12" cy="19" r="1.2"/></svg></button></header>
    <div class="sets">${rows}</div>
    <div class="card-foot"><button class="btn small" type="button" data-act="add-set">+ Série</button>${entry.sets.length > 1 ? '<button class="btn small" type="button" data-act="del-set">Retirer la dernière</button>' : ''}</div>
  </section>`;
}

function viewSeance() {
  const s = curSession();
  if (!s) {
    const recent = [...db.sessions].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 3);
    return `<h1>Nouvelle séance</h1>
      <div class="head"><label class="datechip"><span>${esc(dateLabel(ui.newDate || todayStr()))}</span><input type="date" value="${ui.newDate || todayStr()}" data-act="new-date" aria-label="Date de la séance"></label></div>
      <button class="btn primary wide" type="button" data-act="add-ex">Ajouter un exercice</button>
      ${recent.length ? `<h2 style="margin-top:28px">Refaire une séance</h2><ul class="list">${recent.map(r => `<li><button type="button" data-act="redo" data-sid="${r.id}"><span>${esc(dateLabel(r.date))}<br><small>${esc(r.entries.map(e => exById(e.exercise_id)?.name).filter(Boolean).join(', '))}</small></span></button></li>`).join('')}</ul>`
        : `<p class="muted empty" style="margin-top:22px">Choisis un exercice, saisis tes séries et valide-les une à une. Pour reprendre tes anciennes données, va dans l'onglet Données.</p>`}`;
  }
  const nSets = s.entries.reduce((a, e) => a + doneSets(e.sets).length, 0);
  return `<div class="head"><label class="datechip"><span>${esc(dateLabel(s.date))}</span><input type="date" value="${s.date}" data-act="set-date" aria-label="Date de la séance"></label>
      <span class="muted">${s.entries.length} exercice${s.entries.length > 1 ? 's' : ''} · ${nSets} série${nSets > 1 ? 's' : ''}</span></div>
    ${s.entries.map(e => entryCard(e, s)).join('')}
    <div class="stack"><button class="btn wide" type="button" data-act="add-ex">+ Ajouter un exercice</button>
    <button class="btn primary wide" type="button" data-act="finish">Terminer la séance</button></div>`;
}

function pickExercise(cb) {
  openSheet(`<h2>Choisir un exercice</h2><input class="search" id="q" placeholder="Rechercher ou créer un exercice" autocomplete="off" aria-label="Rechercher un exercice"><ul class="list" id="exlist"></ul>`, el => {
    const q = $('#q', el), ul = $('#exlist', el);
    const draw = () => {
      const v = q.value.trim(), low = v.toLowerCase();
      const list = sortedExercises().filter(e => e.name.toLowerCase().includes(low));
      let html = list.map(e => `<li><button type="button" data-id="${e.id}"><span>${esc(e.name)}</span><small>${lastUsed(e.id) ? 'vu ' + esc(dShort(lastUsed(e.id))) : ''}</small></button></li>`).join('');
      if (v && !db.exercises.some(e => e.name.toLowerCase() === low)) html += `<li><button type="button" data-new="1"><span>Créer « ${esc(v)} »</span></button></li>`;
      if (!html) html = '<li class="muted" style="padding:14px 4px">Écris le nom de ton premier exercice (Pompes, Tractions…).</li>';
      ul.innerHTML = html;
    };
    q.addEventListener('input', draw); draw();
    ul.addEventListener('click', ev => {
      const b = ev.target.closest('button'); if (!b) return;
      let id = b.dataset.id;
      if (b.dataset.new) { id = uid(); db.exercises.push({ id, name: q.value.trim(), type: '' }); save(true); }
      closeSheet(); cb(id);
    });
    setTimeout(() => q.focus(), 60);
  });
}

function finishSheet(s) {
  let rpe = s.rpe;
  openSheet(`<h2>Comment était la séance ?</h2>
    <div class="rpe">${RPE.map((r, i) => `<button type="button" data-rpe="${i + 1}" aria-pressed="${rpe === i + 1}" aria-label="${r[1]}">${r[0]}<small>${r[1]}</small></button>`).join('')}</div>
    <textarea class="notes" placeholder="Une note ? (douleur, sensation…)" aria-label="Notes">${esc(s.notes)}</textarea>
    <div class="stack" style="margin-top:14px"><button class="btn primary wide" data-ok>Terminer la séance</button><button class="btn wide" data-cancel>Continuer la séance</button></div>`, el => {
    el.querySelectorAll('[data-rpe]').forEach(b => b.onclick = () => { const v = +b.dataset.rpe; rpe = rpe === v ? null : v; el.querySelectorAll('[data-rpe]').forEach(x => x.setAttribute('aria-pressed', +x.dataset.rpe === rpe)); });
    $('[data-cancel]', el).onclick = closeSheet;
    $('[data-ok]', el).onclick = () => { s.notes = $('textarea', el).value.trim(); s.rpe = rpe; closeSheet(); finishSession(s); };
  });
}
function finishSession(s) {
  for (const e of s.entries) e.sets = e.sets.filter(isDone).filter(x => x.r > 0);
  s.entries = s.entries.filter(e => e.sets.length);
  const ids = s.entries.map(e => e.exercise_id);
  if (!s.entries.length) db.sessions = db.sessions.filter(x => x !== s);
  ui.currentId = null; stopRest();
  save(true);
  if (!ids.length) { toast('Séance vide : rien à enregistrer.'); render(); return; }
  ui.sel = ids.slice(0, 4); ui.point = null; ui.view = null; assignColors();
  toast('Séance enregistrée.'); setTab('progres');
}

/* --- chrono de repos : mesure le temps entre deux séries validées --- */
let restTimer = 0;
function startRest(eid, i) { ui.rest = { eid, i, t0: Date.now() }; $('#rest').style.display = 'block'; clearInterval(restTimer); restTimer = setInterval(tickRest, 500); tickRest(); }
function tickRest() {
  if (!ui.rest) return;
  const el = (Date.now() - ui.rest.t0) / 1000, target = db.settings.rest || 90;
  $('#rest .t').textContent = mmss(el); $('#rest .bar i').style.width = Math.min(100, el / target * 100) + '%';
  $('#rest .lbl').textContent = el >= target ? 'Prêt' : 'Repos';
}
function stopRest() { ui.rest = null; clearInterval(restTimer); $('#rest').style.display = 'none'; }

function toggleSet(entry, i) {
  const st = entry.sets[i], s = curSession(), prev = getPrev(db, entry.exercise_id, s.id);
  if (isDone(st)) { st.done = false; save(); render(); return; }
  const ph = phFor(entry, i, prev), w = st.w ?? ph.w, r = st.r ?? ph.r;
  if (!(r > 0)) {
    const row = document.querySelector(`[data-eid="${entry.id}"] .set[data-i="${i}"]`);
    if (row) { row.classList.add('shake'); const inp = $('[data-f=r]', row); inp && inp.focus(); }
    toast('Indique le nombre de répétitions.'); return;
  }
  st.w = w; st.r = r; st.done = true;
  if (ui.rest && ui.rest.eid === entry.id && ui.rest.i === i - 1 && i > 0) {
    const secs = Math.round((Date.now() - ui.rest.t0) / 1000);
    if (secs <= 900) entry.sets[i - 1].rest = secs;
  }
  if (i === entry.sets.length - 1) entry.sets.push({ w: null, r: null, tempo: '', rest: null, done: false });
  startRest(entry.id, i); save(); render();
}

/* ======================================================= PROGRÈS */
function assignColors() {
  ui.sel = ui.sel.filter(id => exById(id)).slice(0, 4);
  const used = new Set(ui.sel.map(id => ui.colors[id]).filter(Boolean));
  for (const id of ui.sel) if (!ui.colors[id] || [...ui.sel].filter(o => ui.colors[o] === ui.colors[id]).length > 1) {
    for (let k = 1; k <= 4; k++) if (!used.has(k)) { ui.colors[id] = k; used.add(k); break; }
  }
}
const colorOf = id => `var(--s${ui.colors[id] || 1})`;
const SHAPES = [(x, y, r) => `<circle cx="${x}" cy="${y}" r="${r}"/>`,
  (x, y, r) => `<rect x="${x - r}" y="${y - r}" width="${2 * r}" height="${2 * r}" rx="1.5"/>`,
  (x, y, r) => `<path d="M${x} ${y - r - 1}L${x + r + 1.5} ${y + r}L${x - r - 1.5} ${y + r}Z"/>`,
  (x, y, r) => `<path d="M${x} ${y - r - 2}L${x + r + 2} ${y}L${x} ${y + r + 2}L${x - r - 2} ${y}Z"/>`];

function seriesList() {
  const out = [];
  for (const id of ui.sel) {
    const ex = exById(id); if (!ex) continue;
    const pts = getSeries(db, id, ui.metric); const base = pts.find(p => p.v > 0);
    pts.forEach(p => { p.ex = id; p.y = (ui.pct && ui.sel.length > 1 && base) ? p.v / base.v * 100 : p.v; });
    out.push({ id, ex, pts, color: colorOf(id), shape: SHAPES[(ui.colors[id] || 1) - 1] });
  }
  return out;
}
function defaultView(list) {
  const xs = list.flatMap(l => l.pts.map(p => p.x));
  if (!xs.length) { const t = dayNum(todayStr()); return [t - 15, t + 2]; }
  const lo = Math.min(...xs), hi = Math.max(...xs);
  if (ui.period === 'all') { const pad = Math.max(3, (hi - lo) * 0.06); return [lo - pad, hi + pad]; }
  return [hi + 3 - +ui.period, hi + 3];
}
function niceTicks(lo, hi, n) {
  const span = hi - lo || 1, raw = span / n, mag = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / mag;
  const step = (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * mag, out = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(6));
  return out;
}
function xTicks(x0, x1) {
  const span = x1 - x0, out = [];
  if (span <= 45) { const step = [1, 2, 3, 7, 14].find(s => span / s <= 6) || 14; for (let d = Math.ceil(x0 / step) * step; d <= x1; d += step) out.push([d, new Date(d * 864e5).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', timeZone: 'UTC' })]); return out; }
  const months = [1, 2, 3, 6, 12, 24].find(m => span / (m * 30.4) <= 6) || 24;
  const d0 = new Date(x0 * 864e5); let y = d0.getUTCFullYear(), m = d0.getUTCMonth();
  m = Math.ceil(m / months) * months;
  for (; ; m += months) {
    const d = Date.UTC(y + Math.floor(m / 12), m % 12, 1) / 864e5; if (d > x1) break;
    if (d >= x0) out.push([d, new Date(d * 864e5).toLocaleDateString('fr-FR', { month: 'short', year: '2-digit', timeZone: 'UTC' })]);
  }
  return out;
}

let chartState = null;
function drawChart() {
  const svg = $('#chart'); if (!svg) return;
  const list = seriesList();
  if (!ui.view) ui.view = defaultView(list);
  const [x0, x1] = ui.view, W = svg.clientWidth || 360, H = 300, ml = 46, mr = 14, mt = 12, mb = 28;
  const vis = list.flatMap(l => l.pts).filter(p => p.x >= x0 && p.x <= x1);
  const all = vis.length ? vis : list.flatMap(l => l.pts);
  let lo = all.length ? Math.min(...all.map(p => p.y)) : 0, hi = all.length ? Math.max(...all.map(p => p.y)) : 1;
  const pad = (hi - lo) * 0.18 || Math.max(1, Math.abs(hi) * 0.1);
  lo = lo - pad; hi = hi + pad; if (lo < 0 && Math.min(...all.map(p => p.y), 0) >= 0) lo = 0;
  const X = d => ml + (d - x0) / (x1 - x0) * (W - ml - mr), Y = v => mt + (1 - (v - lo) / (hi - lo)) * (H - mt - mb);
  chartState = { X, Y, W, H, ml, mr, list, x0, x1 };
  let g = '';
  for (const v of niceTicks(lo, hi, 4)) g += `<line class="grid" x1="${ml}" x2="${W - mr}" y1="${Y(v)}" y2="${Y(v)}"/><text class="axis" x="${ml - 8}" y="${Y(v) + 4}" text-anchor="end">${fmt(+v.toFixed(1))}</text>`;
  for (const [d, label] of xTicks(x0, x1)) g += `<text class="axis" x="${X(d)}" y="${H - 8}" text-anchor="middle">${esc(label)}</text>`;
  let marks = '';
  for (const l of list) {
    const pts = l.pts; if (!pts.length) continue;
    const vp = pts.filter(p => p.x >= x0 - 5 && p.x <= x1 + 5), dense = vp.length > 40, rad = dense ? 2.8 : 4.5;
    marks += `<polyline fill="none" stroke="${l.color}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" points="${pts.map(p => X(p.x) + ',' + Y(p.y)).join(' ')}"/>`;
    marks += `<g fill="${l.color}" stroke="var(--surface)" stroke-width="${dense ? 1 : 2}">` + vp.map(p => l.shape(X(p.x), Y(p.y), rad).replace('/>', `><title>${esc(l.ex.name)} · ${esc(dShort(p.date))} · ${fmt(+p.v.toFixed(2))} ${METRICS[ui.metric].unit}</title>`).replace(/^<(\w+)(.*?)>(<title>.*)$/, (m, t, a, rest) => `<${t}${a}>${rest}</${t}>`)).join('') + '</g>';
    marks += (dense ? vp.filter(p => p.record).slice(-3) : vp.filter(p => p.record)).map(p => `<circle cx="${X(p.x)}" cy="${Y(p.y)}" r="10" fill="none" stroke="var(--gold)" stroke-width="2"/>`).join('');
    if (list.length > 1) { const last = pts[pts.length - 1]; marks += `<text class="axis" x="${Math.min(W - mr, X(last.x) + 8)}" y="${Y(last.y) - 10}" text-anchor="${X(last.x) > W - 90 ? 'end' : 'start'}" style="fill:var(--ink2);font-weight:700">${esc(l.ex.name)}</text>`; }
  }
  if (ui.point) { const p = list.flatMap(l => l.pts).find(q => q.ex === ui.point.ex && q.session.id === ui.point.sid);
    if (p) marks += `<line x1="${X(p.x)}" x2="${X(p.x)}" y1="${mt}" y2="${H - mb}" stroke="var(--ink)" stroke-width="1.5" opacity=".5"/><circle cx="${X(p.x)}" cy="${Y(p.y)}" r="15" fill="var(--ink)" opacity=".16"/>`; }
  const empty = !all.length ? `<text x="${W / 2}" y="${H / 2}" text-anchor="middle" class="axis" style="font-size:15px">Aucune donnée pour cet exercice</text>` : '';
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.innerHTML = `<defs><clipPath id="clip"><rect x="${ml - 6}" y="0" width="${W - ml - mr + 12}" height="${H - mb + 4}"/></clipPath></defs>${g}<g clip-path="url(#clip)">${marks}</g>${empty}`;
}

function bindChart() {
  const svg = $('#chart'); if (!svg) return;
  const ptrs = new Map(); let down = null, pinch = null;
  const px = e => { const r = svg.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
  const setView = (a, b) => { const span = clamp(b - a, 3, 3650); const c = (a + b) / 2; ui.view = [c - span / 2, c + span / 2]; };
  svg.addEventListener('pointerdown', e => { svg.setPointerCapture(e.pointerId); ptrs.set(e.pointerId, px(e)); down = { p: px(e), t: Date.now(), moved: 0, view: ui.view.slice() };
    if (ptrs.size === 2) { const [a, b] = [...ptrs.values()]; pinch = { d: Math.hypot(a[0] - b[0], a[1] - b[1]), view: ui.view.slice(), cx: (a[0] + b[0]) / 2 }; } });
  svg.addEventListener('pointermove', e => {
    if (!ptrs.has(e.pointerId)) return; const cur = px(e); ptrs.set(e.pointerId, cur);
    const { ml, W, mr } = chartState, perDay = (W - ml - mr) / (ui.view[1] - ui.view[0]);
    if (ptrs.size === 2 && pinch) {
      const [a, b] = [...ptrs.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]) || 1;
      const [v0, v1] = pinch.view, anchor = v0 + (pinch.cx - ml) / ((W - ml - mr) / (v1 - v0)), k = pinch.d / d;
      setView(anchor - (anchor - v0) * k, anchor + (v1 - anchor) * k); if (down) down.moved = 99; drawChart();
    } else if (ptrs.size === 1 && down) {
      const dx = cur[0] - down.p[0]; down.moved = Math.max(down.moved, Math.abs(dx) + Math.abs(cur[1] - down.p[1]));
      if (down.moved > 6) { const dd = dx / ((W - ml - mr) / (down.view[1] - down.view[0])); ui.view = [down.view[0] - dd, down.view[1] - dd]; drawChart(); }
    }
  });
  const end = e => {
    if (!ptrs.has(e.pointerId)) return; const wasOne = ptrs.size === 1; ptrs.delete(e.pointerId); if (ptrs.size < 2) pinch = null;
    if (e.type === 'pointerup' && wasOne && down && down.moved <= 6 && Date.now() - down.t < 600) { if (e.detail >= 2) { ui.view = defaultView(seriesList()); drawChart(); } else tapAt(down.p); }
    if (!ptrs.size) down = null;
  };
  svg.addEventListener('pointerup', end); svg.addEventListener('pointercancel', end);
  svg.addEventListener('dblclick', () => { ui.view = defaultView(seriesList()); drawChart(); });
  svg.addEventListener('wheel', e => { e.preventDefault(); const { ml, W, mr } = chartState, [v0, v1] = ui.view, anchor = v0 + (px(e)[0] - ml) / ((W - ml - mr) / (v1 - v0)), k = e.deltaY > 0 ? 1.15 : 1 / 1.15;
    setView(anchor - (anchor - v0) * k, anchor + (v1 - anchor) * k); drawChart(); }, { passive: false });
}
function tapAt([tx, ty]) {
  const { X, Y, list } = chartState; let best = null, bd = 36;
  for (const l of list) for (const p of l.pts) { const d = Math.hypot(X(p.x) - tx, Y(p.y) - ty); if (d < bd) { bd = d; best = p; } }
  ui.point = best ? { ex: best.ex, sid: best.session.id } : null;
  const keep = window.scrollY; renderProgres(); window.scrollTo(0, keep);
}

function detailCard(list) {
  if (!ui.point) return '';
  const p = list.flatMap(l => l.pts).find(q => q.ex === ui.point.ex && q.session.id === ui.point.sid); if (!p) return '';
  const ex = exById(p.ex), m = METRICS[ui.metric], s = p.session, rpe = s.rpe ? RPE[s.rpe - 1] : null;
  return `<div class="detail" id="detail"><div class="row" style="justify-content:space-between;align-items:flex-start"><div><h3>${esc(ex.name)}</h3><div class="sub">${esc(dFull(s.date))}${rpe ? ' · ' + rpe[0] + ' ' + rpe[1] : ''}</div></div>
    ${p.record ? '<span class="badge"><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3 6.5 7 .9-5.1 4.9 1.3 7L12 17.8 5.8 21.3l1.3-7L2 9.4l7-.9z"/></svg>Record</span>' : ''}</div>
    <p><strong>${esc(m.label)} : ${fmt(+p.v.toFixed(2))} ${m.unit}</strong></p>
    <ol>${doneSets(p.entry.sets).map(st => `<li>${st.w != null ? fmt(st.w) + ' kg × ' : ''}${fmt(st.r)}${st.w == null ? ' reps' : ''}${st.tempo ? ' · tempo ' + esc(st.tempo) : ''}${st.rest != null ? ' · repos ' + mmss(st.rest) : ''}</li>`).join('')}</ol>
    ${s.notes ? `<p class="muted">« ${esc(s.notes)} »</p>` : ''}
    <div class="card-foot"><button class="btn small" type="button" data-act="edit-session">Modifier</button><button class="btn small danger" type="button" data-act="del-session">Supprimer</button></div></div>`;
}

function viewProgres() {
  assignColors();
  if (!db.sessions.length) return `<h1>Progrès</h1><div class="empty"><p>Ton graphique apparaîtra ici dès ta première séance enregistrée.</p><button class="btn primary" type="button" data-tab="seance">Commencer une séance</button><p class="muted" style="margin-top:18px">Tu as déjà des données ? Importe-les depuis l'onglet Données.</p></div>`;
  if (!ui.sel.length) ui.sel = sortedExercises().slice(0, 1).map(e => e.id), assignColors();
  const list = seriesList(), main = list[0], pts = main ? main.pts : [], m = METRICS[ui.metric];
  const last = pts[pts.length - 1], prev = pts[pts.length - 2], best = pts.length ? pts.reduce((a, b) => b.y > a.y ? b : a) : null;
  let hero = '<p class="sub">Aucune séance pour cet exercice.</p>';
  if (last) {
    const unit = ui.pct && list.length > 1 ? '%' : m.unit, dv = prev ? last.y - prev.y : null;
    hero = `<div class="hero"><span class="big">${fmt(+last.y.toFixed(1))}</span><span class="unit">${unit}</span>${dv !== null ? `<span class="delta" style="color:${dv > 0 ? 'var(--ok)' : dv < 0 ? 'var(--danger)' : 'var(--ink3)'}">${dv > 0 ? '▲ +' : dv < 0 ? '▼ ' : '= '}${dv ? fmt(+dv.toFixed(1)) : 'stable'}</span>` : ''}</div>
      <div class="sub">${esc(main.ex.name)} · ${esc(m.long)} · séance du ${esc(dShort(last.date))}${best && pts.length > 1 ? ` · record ${fmt(+best.y.toFixed(1))} ${unit}` : ''}</div>`;
  }
  const chips = sortedExercises().map(e => { const on = ui.sel.includes(e.id); return `<button class="chipb" type="button" data-act="toggle-ex" data-ex="${e.id}" aria-pressed="${on}">${on ? `<i style="background:${colorOf(e.id)}"></i>` : ''}${esc(e.name)}</button>`; }).join('');
  const periods = [['30', '30 j'], ['90', '90 j'], ['365', '1 an'], ['all', 'Tout']];
  const rows = [...pts].reverse().map(p => { const S = doneSets(p.entry.sets), ws = new Set(S.map(x => x.w));
    const txt = ws.size <= 1 ? `${S.map(x => fmt(x.r)).join(' · ')}${S[0].w != null ? ' × ' + fmt(S[0].w) + ' kg' : ' reps'}` : S.map(compactSet).join(' · ');
    return `<tr data-act="pick-row" data-sid="${p.session.id}" aria-selected="${!!ui.point && ui.point.sid === p.session.id}"><td>${esc(dShort(p.date))}</td><td>${esc(txt)}</td><td>${fmt(+p.y.toFixed(1))}</td></tr>`; }).join('');
  return `<h1>Progrès</h1>
    <div class="chips" role="group" aria-label="Exercices à afficher">${chips}</div>
    <div class="seg" role="group" aria-label="Indicateur">${Object.entries(METRICS).map(([k, v]) => `<button type="button" data-act="metric" data-m="${k}" aria-pressed="${ui.metric === k}">${v.label}</button>`).join('')}</div>
    ${hero}
    <div class="chartwrap"><svg class="chart" id="chart" role="img" aria-label="Graphique de progression"></svg></div>
    <div class="chips" role="group" aria-label="Période">${periods.map(([k, l]) => `<button class="chipb" type="button" data-act="period" data-p="${k}" aria-pressed="${ui.period === k}">${l}</button>`).join('')}${list.length > 1 ? `<button class="chipb" type="button" data-act="pct" aria-pressed="${ui.pct}">En % du départ</button>` : ''}</div>
    <p class="hint">Glisse pour te déplacer, pince pour zoomer, double tape pour revenir. Touche un point pour voir la séance. Un cercle doré marque un record.</p>
    ${detailCard(list)}
    ${pts.length ? `<h2>Séances de ${esc(main.ex.name)}</h2><table class="hist"><thead><tr><th>Date</th><th>Séries</th><th>${esc(m.label)}</th></tr></thead><tbody>${rows}</tbody></table>` : ''}`;
}
function renderProgres() { $('#app').innerHTML = viewProgres(); drawChart(); bindChart(); }

/* ======================================================= DONNÉES */
function viewDonnees() {
  const meta = db.meta, changes = meta.changes || 0;
  const status = meta.lastExport ? `Dernière sauvegarde : ${new Date(meta.lastExport).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })}` : 'Aucune sauvegarde pour l\'instant';
  const exRows = sortedExercises().map(e => { const n = db.sessions.filter(s => s.entries.some(x => x.exercise_id === e.id)).length;
    return `<div class="kv"><span>${esc(e.name)}<br><small class="muted">${n} séance${n > 1 ? 's' : ''}</small></span><span class="row"><button class="btn small" type="button" data-act="ex-rename" data-ex="${e.id}">Renommer</button><button class="btn small danger" type="button" data-act="ex-delete" data-ex="${e.id}">Supprimer</button></span></div>`; }).join('');
  return `<h1>Données</h1>
    <div class="panel"><h2>Sauvegarde</h2>
      <p class="muted">Tes données restent sur cet appareil. Exporte-les pour les garder en sécurité ou les retrouver sur un autre téléphone.</p>
      <p class="${meta.lastExport && !changes ? '' : 'warn'}">${esc(status)}${changes && db.sessions.length ? ` · ${changes} modification${changes > 1 ? 's' : ''} non sauvegardée${changes > 1 ? 's' : ''}` : ''}</p>
      <div class="stack"><button class="btn primary wide" type="button" data-act="export-json">Exporter (JSON)</button>
      <button class="btn wide" type="button" data-act="import">Importer un fichier</button></div>
      <p class="muted" style="margin:12px 0 0;font-size:14px">L'import accepte le JSON de PerformApp et le CSV de l'ancienne application. Il peut fusionner avec tes données sans créer de doublon.</p></div>
    <div class="panel"><h2>Exercices</h2>${exRows || '<p class="muted">Aucun exercice pour l\'instant. Tu peux en créer depuis l\'onglet Séance.</p>'}</div>
    <div class="panel"><h2>Réglages</h2><div class="kv"><label for="rest-sel">Repos visé entre deux séries</label><select class="sel" id="rest-sel" data-act="rest-set">${[45, 60, 90, 120, 180, 240].map(v => `<option value="${v}" ${db.settings.rest === v ? 'selected' : ''}>${mmss(v)}</option>`).join('')}</select></div>
      <div class="kv"><span>Export pour tableur</span><button class="btn small" type="button" data-act="export-csv">CSV</button></div>
      ${localStorage.getItem(PREVKEY) ? '<div class="kv"><span>Avant le dernier import</span><button class="btn small" type="button" data-act="restore">Restaurer</button></div>' : ''}
      <div class="kv"><span>Tout effacer<br><small class="muted">Supprime les données de cet appareil</small></span><button class="btn small danger" type="button" data-act="wipe">Effacer</button></div></div>
    <p class="muted" style="font-size:14px">Pour installer l'app : menu du navigateur, puis « Ajouter à l'écran d'accueil ».</p>`;
}

async function exportFile(kind) {
  const text = kind === 'json' ? PA.toJSON(db) : PA.toCSV(db), name = `performapp-${todayStr()}.${kind}`;
  const file = new File([text], name, { type: kind === 'json' ? 'application/json' : 'text/csv' });
  const mark = () => { if (kind === 'json') { db.meta.lastExport = new Date().toISOString(); db.meta.changes = 0; save(true); } render(); };
  if (window.claude && window.claude.use) {
    try {
      const dl = await window.claude.use('downloads');
      if (dl) { await dl.save({ filename: name, data: text }); toast(`${name} enregistré.`); mark(); return; }
    } catch (e) { if (e && e.code === 'declined') return; toast("L'enregistrement a échoué."); return; }
  }
  if (matchMedia('(pointer:coarse)').matches && navigator.canShare && navigator.canShare({ files: [file] })) {
    try { await navigator.share({ files: [file], title: name }); mark(); return; } catch (e) { if (e.name === 'AbortError') return; }
  }
  const a = document.createElement('a'); a.href = URL.createObjectURL(file); a.download = name; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000); toast(`${name} téléchargé.`); mark();
}

function handleImport(text, filename) {
  let inc;
  try { inc = /\.csv$/i.test(filename) ? PA.csvToDb(text) : PA.parseBackup(text); }
  catch (e) { openSheet(`<h2>Import impossible</h2><p>${esc(e.message)}</p><button class="btn wide" data-cancel>Fermer</button>`, el => { $('[data-cancel]', el).onclick = closeSheet; }); return; }
  const dates = inc.sessions.map(s => s.date).sort(), merge = PA.mergeDb(db, inc, false).stats;
  openSheet(`<h2>Importer « ${esc(filename)} »</h2>
    <p>${inc.sessions.length} séance${inc.sessions.length > 1 ? 's' : ''}, ${inc.exercises.length} exercice${inc.exercises.length > 1 ? 's' : ''}${dates.length ? `, du ${esc(dFull(dates[0]))} au ${esc(dFull(dates[dates.length - 1]))}` : ''}.</p>
    <p class="muted">Fusionner ajoute ${merge.newSessions} nouvelle${merge.newSessions > 1 ? 's' : ''} séance${merge.newSessions > 1 ? 's' : ''}${merge.skipped ? ` et ignore ${merge.skipped} exercice${merge.skipped > 1 ? 's' : ''} déjà présent${merge.skipped > 1 ? 's' : ''}` : ''}. Remplacer efface tes données actuelles (tu pourras les restaurer).</p>
    <div class="stack"><button class="btn primary wide" data-merge ${merge.newEntries ? '' : 'disabled'}>Fusionner avec mes données</button><button class="btn danger wide" data-replace>Remplacer mes données</button><button class="btn wide" data-cancel>Annuler</button></div>`, el => {
    $('[data-cancel]', el).onclick = closeSheet;
    $('[data-merge]', el).onclick = () => { stash(); PA.mergeDb(db, inc, true); ui.currentId = null; save(true); closeSheet(); toast(`${merge.newSessions} séance${merge.newSessions > 1 ? 's' : ''} ajoutée${merge.newSessions > 1 ? 's' : ''}.`); ui.sel = []; ui.view = null; render(); };
    $('[data-replace]', el).onclick = () => { stash(); const keep = db.settings; db = inc; db.settings = Object.assign({}, db.settings, keep); db.meta.changes = 0; ui.currentId = null; ui.sel = []; ui.view = null; save(true); closeSheet(); toast('Données remplacées.'); render(); };
  });
}
function stash() { try { localStorage.setItem(PREVKEY, JSON.stringify(db)); } catch (e) { /* ignore */ } }

/* ===================================================== ROUTEUR */
function render() {
  document.querySelectorAll('#tabbar [data-tab]').forEach(b => b.setAttribute('aria-selected', b.dataset.tab === ui.tab));
  hideDock();
  if (ui.tab === 'progres') { renderProgres(); return; }
  $('#app').innerHTML = ui.tab === 'seance' ? viewSeance() : viewDonnees();
}
function setTab(t) { ui.tab = t; ui.point = t === 'progres' ? ui.point : null; persistUi(); render(); window.scrollTo(0, 0); }

/* ===================================================== CLAVIER +/- */
let dockInput = null;
const STEPS = { w: [0.5, 1, 2.5, 5], r: [1, 0.5] };
function showDock(inp) {
  const f = inp.dataset.f; if (f !== 'w' && f !== 'r') { hideDock(); return; }
  dockInput = inp; $('#dock').style.display = 'block'; dockRefresh();
}
function hideDock() { dockInput = null; $('#dock').style.display = 'none'; }
function dockRefresh() {
  if (!dockInput) return; const f = dockInput.dataset.f, step = f === 'w' ? ui.stepW : ui.stepR;
  $('#dock-label').textContent = f === 'w' ? 'Poids (kg)' : 'Répétitions';
  $('#dock-val').textContent = dockInput.value || dockInput.placeholder || '0';
  $('#dock-chips').innerHTML = STEPS[f].map(s => `<button class="chip" type="button" data-act="dock-step" data-s="${s}" aria-pressed="${s === step}">${fmt(s)}</button>`).join('');
}
function dockBump(dir) {
  if (!dockInput) return; const f = dockInput.dataset.f, step = f === 'w' ? ui.stepW : ui.stepR;
  const cur = parseNum(dockInput.value) ?? parseNum(dockInput.placeholder) ?? 0;
  dockInput.value = fmt(Math.max(0, +(cur + dir * step).toFixed(2))); dockInput.dispatchEvent(new Event('input', { bubbles: true }));
}
$('#dock').addEventListener('pointerdown', e => e.preventDefault());
if (window.visualViewport) { const upd = () => { const kb = Math.max(0, window.innerHeight - visualViewport.height - visualViewport.offsetTop); document.documentElement.style.setProperty('--kb', kb + 'px'); $('#dock').classList.toggle('kb', kb > 80); };
  visualViewport.addEventListener('resize', upd); visualViewport.addEventListener('scroll', upd); }

/* ===================================================== ÉVÉNEMENTS */
function entryOf(el) { const card = el.closest('[data-eid]'), s = curSession(); return card && s ? s.entries.find(e => e.id === card.dataset.eid) : null; }
const actions = {
  'add-ex': () => pickExercise(addExercise),
  'new-date': el => { ui.newDate = el.value || null; render(); },
  'set-date': el => { const s = curSession(); if (s && el.value) { s.date = el.value; db.sessions.sort((a, b) => a.date.localeCompare(b.date)); save(); render(); } },
  redo: el => { const src = db.sessions.find(s => s.id === el.dataset.sid); if (!src) return; const s = startSession(); src.entries.forEach(e => s.entries.push(newEntry(e.exercise_id, s.id))); save(); render(); },
  chk: el => { const e = entryOf(el); if (e) toggleSet(e, +el.closest('.set').dataset.i); },
  'add-set': el => { const e = entryOf(el); if (e) { e.sets.push({ w: null, r: null, tempo: '', rest: null, done: false }); save(); render(); } },
  'del-set': el => { const e = entryOf(el); if (e && e.sets.length > 1) { e.sets.pop(); save(); render(); } },
  'ex-menu': el => { const e = entryOf(el), ex = e && exById(e.exercise_id); if (!e) return;
    openSheet(`<h2>${esc(ex.name)}</h2><div class="stack"><button class="btn wide" data-t>${e.showTempo ? 'Masquer le tempo' : 'Saisir le tempo'}</button><button class="btn wide danger" data-r>Retirer de la séance</button><button class="btn wide" data-c>Fermer</button></div>`, sh => {
      $('[data-c]', sh).onclick = closeSheet; $('[data-t]', sh).onclick = () => { e.showTempo = !e.showTempo; save(); closeSheet(); render(); };
      $('[data-r]', sh).onclick = () => { const s = curSession(); s.entries = s.entries.filter(x => x !== e); save(); closeSheet(); render(); }; }); },
  finish: () => { const s = curSession(); if (!s) return; if (!s.entries.some(e => e.sets.some(isDone))) { confirmSheet('Séance vide', 'Aucune série n\'est validée. Abandonner cette séance ?', 'Abandonner', () => finishSession(s)); return; } finishSheet(s); },
  'rest-off': stopRest,
  'dock-minus': () => dockBump(-1), 'dock-plus': () => dockBump(1),
  'dock-step': el => { if (!dockInput) return; if (dockInput.dataset.f === 'w') ui.stepW = +el.dataset.s; else ui.stepR = +el.dataset.s; persistUi(); dockRefresh(); },
  'toggle-ex': el => { const id = el.dataset.ex; if (ui.sel.includes(id)) { if (ui.sel.length === 1) { toast('Garde au moins un exercice.'); return; } ui.sel = ui.sel.filter(x => x !== id); } else { if (ui.sel.length >= 4) { toast('4 exercices au maximum.'); return; } ui.sel.push(id); delete ui.colors[id]; } ui.view = null; ui.point = null; persistUi(); renderProgres(); },
  metric: el => { ui.metric = el.dataset.m; ui.point = null; persistUi(); renderProgres(); },
  period: el => { ui.period = el.dataset.p; ui.view = null; persistUi(); renderProgres(); },
  pct: () => { ui.pct = !ui.pct; ui.view = null; persistUi(); renderProgres(); },
  'pick-row': el => { ui.point = { ex: ui.sel[0], sid: el.dataset.sid }; renderProgres(); const d = $('#detail'); if (d) d.scrollIntoView({ block: 'center', behavior: 'smooth' }); },
  'edit-session': () => { if (!ui.point) return; ui.currentId = ui.point.sid; setTab('seance'); },
  'del-session': () => { const p = ui.point; if (!p) return; confirmSheet('Supprimer cette séance ?', `${exById(p.ex).name}, ${dFull(db.sessions.find(s => s.id === p.sid).date)}. Cette action est définitive.`, 'Supprimer', () => {
    const s = db.sessions.find(x => x.id === p.sid); s.entries = s.entries.filter(e => e.exercise_id !== p.ex); if (!s.entries.length) db.sessions = db.sessions.filter(x => x !== s);
    if (ui.currentId === p.sid) ui.currentId = null; ui.point = null; save(true); render(); toast('Séance supprimée.'); }); },
  'export-json': () => exportFile('json'), 'export-csv': () => exportFile('csv'),
  import: () => { const f = $('#file'); f.value = ''; f.click(); },
  'ex-rename': el => { const ex = exById(el.dataset.ex);
    openSheet(`<h2>Renommer l'exercice</h2><input class="search" id="nm" value="${esc(ex.name)}" aria-label="Nouveau nom"><div class="stack" style="margin-top:14px"><button class="btn primary wide" data-ok>Renommer</button><button class="btn wide" data-c>Annuler</button></div>`, sh => {
      $('[data-c]', sh).onclick = closeSheet;
      $('[data-ok]', sh).onclick = () => { const v = $('#nm', sh).value.trim(); if (!v) { toast('Le nom ne peut pas être vide.'); return; }
        if (db.exercises.some(x => x.id !== ex.id && x.name.toLowerCase() === v.toLowerCase())) { toast('Ce nom existe déjà.'); return; }
        ex.name = v; save(true); closeSheet(); render(); }; }); },
  'ex-delete': el => { const ex = exById(el.dataset.ex), n = db.sessions.filter(s => s.entries.some(e => e.exercise_id === ex.id)).length;
    confirmSheet(`Supprimer « ${ex.name} » ?`, `${n} séance${n > 1 ? 's' : ''} contenant cet exercice perdr${n > 1 ? 'ont' : 'a'} ces séries. Pense à exporter avant.`, 'Supprimer', () => {
      db.exercises = db.exercises.filter(e => e !== ex); db.sessions.forEach(s => { s.entries = s.entries.filter(e => e.exercise_id !== ex.id); }); db.sessions = db.sessions.filter(s => s.entries.length);
      ui.sel = ui.sel.filter(x => x !== ex.id); if (ui.currentId && !curSession()) ui.currentId = null; save(true); render(); }); },
  restore: () => confirmSheet('Restaurer les données ?', 'Les données d\'avant le dernier import reviennent. Les données actuelles seront remplacées.', 'Restaurer', () => { try { db = PA.normalizeDb(JSON.parse(localStorage.getItem(PREVKEY))); ui.currentId = null; ui.sel = []; save(true); toast('Données restaurées.'); render(); } catch (e) { toast('Restauration impossible.'); } }, false),
  wipe: () => confirmSheet('Tout effacer ?', 'Toutes les séances et tous les exercices de cet appareil seront supprimés. Exporte d\'abord si tu veux les garder.', 'Tout effacer', () => { stash(); db = PA.emptyDb(); ui.currentId = null; ui.sel = []; save(true); toast('Données effacées.'); render(); })
};
document.addEventListener('click', e => {
  const tab = e.target.closest('[data-tab]'); if (tab) { setTab(tab.dataset.tab); return; }
  const t = e.target.closest('[data-act]'); if (t && actions[t.dataset.act] && t.tagName !== 'INPUT' && t.tagName !== 'SELECT') actions[t.dataset.act](t, e);
});
document.addEventListener('change', e => {
  const t = e.target;
  if (t.dataset.act === 'new-date' || t.dataset.act === 'set-date') actions[t.dataset.act](t);
  if (t.dataset.act === 'rest-set') { db.settings.rest = +t.value; save(true); }
});
$('#file').addEventListener('change', e => { const f = e.target.files[0]; if (!f) return; const r = new FileReader(); r.onload = () => handleImport(String(r.result), f.name); r.readAsText(f); });
document.addEventListener('input', e => {
  const t = e.target; if (!t.matches || !t.matches('.set .num')) return;
  const entry = entryOf(t), st = entry && entry.sets[+t.closest('.set').dataset.i]; if (!st) return;
  const f = t.dataset.f; if (f === 'tempo') st.tempo = t.value; else st[f] = parseNum(t.value);
  save(); if (t === dockInput) dockRefresh();
});
document.addEventListener('focusin', e => { if (e.target.matches && e.target.matches('.set .num')) { showDock(e.target); setTimeout(() => e.target.select && e.target.select(), 0); } });
document.addEventListener('focusout', e => { if (e.target.matches && e.target.matches('.set .num')) setTimeout(() => { if (!document.activeElement || !document.activeElement.matches('.set .num')) hideDock(); }, 120); });
window.addEventListener('resize', () => { if (ui.tab === 'progres' && $('#chart')) drawChart(); });

if (ui.rest) stopRest();
render();
if ('serviceWorker' in navigator && location.protocol.startsWith('http')) navigator.serviceWorker.register('sw.js').catch(() => {});
window.__pa = { get db() { return db; }, ui, render, setTab };
})();

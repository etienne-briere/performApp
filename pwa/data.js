/* PerformApp : modèle de données, métriques, import / export. Aucune dépendance au DOM. */
(function (root) {
  'use strict';

  const FORMAT = 'performapp';
  const VERSION = 1;
  const RPE_ICONS = { 'emoticon-dead-outline': 1, 'emoticon-sad-outline': 2, 'emoticon-neutral-outline': 3,
                      'emoticon-happy-outline': 4, 'emoticon-excited-outline': 5 };

  const uid = () => (root.crypto && crypto.randomUUID) ? crypto.randomUUID()
    : 'id' + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);

  const pad = n => String(n).padStart(2, '0');
  const todayStr = () => { const d = new Date(); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; };
  const dayNum = s => { const [y, m, d] = s.split('-').map(Number); return Math.floor(Date.UTC(y, m - 1, d) / 864e5); };
  const dayStr = n => { const d = new Date(n * 864e5); return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`; };

  function parseNum(v) {
    if (v === null || v === undefined || v === '') return null;
    const n = parseFloat(String(v).replace(',', '.'));
    return Number.isFinite(n) ? n : null;
  }
  const fmt = n => n === null || n === undefined ? '' : String(+Number(n).toFixed(2)).replace('.', ',');

  /* ------------------------------------------------------------ base */
  function emptyDb() {
    return { format: FORMAT, version: VERSION, exercises: [], sessions: [], bodyweight: [],
             settings: { rest: 90 }, meta: { lastExport: null, exportedSessions: 0 } };
  }

  const cleanBw = v => { const n = parseNum(v); return n > 0 ? Math.min(1, +n.toFixed(2)) : 0; };   /* part du poids du corps comptée (0 = aucune) */
  /** Poids du corps (kg) à une date : dernière pesée avant, sinon la plus ancienne ; 0 si aucune. */
  function bodyweightAt(db, date) {
    const L = db.bodyweight || []; if (!L.length) return 0;
    let best = null; for (const b of L) if (b.date <= date) best = b;
    return (best || L[0]).kg;
  }

  function normalizeSet(s) {
    return { w: parseNum(s.w), r: parseNum(s.r), tempo: s.tempo ? String(s.tempo) : '',
             rest: parseNum(s.rest), done: s.done !== false };
  }

  /** Remet n'importe quelle base (ancienne, partielle) au format courant. */
  function normalizeDb(d) {
    const db = emptyDb();
    d = d || {};
    db.exercises = (d.exercises || []).filter(e => e && e.name).map(e => ({ id: e.id || uid(), name: String(e.name).trim(), type: e.type || '', bw: cleanBw(e.bw) }));
    db.sessions = (d.sessions || []).filter(s => s && s.date).map(s => ({
      id: s.id || uid(), date: String(s.date).slice(0, 10),
      rpe: (s.rpe >= 1 && s.rpe <= 5) ? Math.round(s.rpe) : null, notes: s.notes || '',
      entries: (s.entries || []).map(e => ({
        id: e.id || uid(), exercise_id: e.exercise_id, showTempo: !!e.showTempo,
        sets: (e.sets || []).map(normalizeSet)
      })).filter(e => db.exercises.some(x => x.id === e.exercise_id))
    }));
    db.bodyweight = (Array.isArray(d.bodyweight) ? d.bodyweight : []).map(b => ({ date: String(b && b.date || '').slice(0, 10), kg: parseNum(b && b.kg) })).filter(b => /^\d{4}-\d\d-\d\d$/.test(b.date) && b.kg > 0).sort((a, b) => a.date.localeCompare(b.date));
    db.settings = Object.assign({ rest: 90 }, d.settings || {});
    db.meta = Object.assign({ lastExport: null, exportedSessions: 0 }, d.meta || {});
    return db;
  }

  /* -------------------------------------------------------- métriques */
  const isDone = s => s.done !== false;
  const doneSets = sets => sets.filter(s => isDone(s) && s.r > 0);

  const METRICS = {
    max_weight: { label: 'Poids max', long: 'Poids maximal soulevé', unit: 'kg', fn: S => Math.max(0, ...S.map(s => s.w || 0)) },
    total_reps: { label: 'Reps', long: 'Total de répétitions', unit: 'reps', fn: S => S.reduce((a, s) => a + s.r, 0) },
    volume:     { label: 'Tonnage', long: 'Tonnage (poids × répétitions)', unit: 'kg', fn: S => S.reduce((a, s) => a + (s.w || 0) * s.r, 0) },
    e1rm:       { label: '1RM est.', long: '1RM estimé (Epley)', unit: 'kg', fn: S => Math.max(0, ...S.map(s => (s.w || 0) * (1 + s.r / 30))) }
  };
  const metricOf = (sets, m, extra = 0) => { let S = doneSets(sets); if (extra) S = S.map(s => ({ ...s, w: (s.w || 0) + extra })); return S.length ? METRICS[m].fn(S) : null; };

  /** Points d'un exercice : une valeur par séance, triés par date. `record` marque chaque nouveau record. */
  function getSeries(db, exId, metric) {
    const pts = [], ex = db.exercises.find(x => x.id === exId), coef = ex && ex.bw || 0;
    for (const s of db.sessions) for (const e of s.entries) {
      if (e.exercise_id !== exId) continue;
      const extra = coef ? bodyweightAt(db, s.date) * coef : 0;
      const v = metricOf(e.sets, metric, extra);
      if (v === null) continue;
      pts.push({ x: dayNum(s.date), date: s.date, v, extra, session: s, entry: e });
    }
    pts.sort((a, b) => a.x - b.x);
    let best = -Infinity;
    for (const p of pts) { p.record = best !== -Infinity && p.v > best; best = Math.max(best, p.v); }
    return pts;
  }

  /** Dernière séance contenant l'exercice (hors séance courante) : sert de pré-remplissage. */
  function getPrev(db, exId, excludeSessionId) {
    let best = null;
    for (const s of db.sessions) {
      if (s.id === excludeSessionId) continue;
      const e = s.entries.find(x => x.exercise_id === exId && doneSets(x.sets).length);
      if (e && (!best || s.date >= best.session.date)) best = { session: s, entry: e };
    }
    return best;
  }

  /* ----------------------------------------------------------- CSV */
  function parseCSV(text) {
    const rows = []; let row = [], cur = '', q = false;
    text = text.replace(/^﻿/, '');
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) { if (c === '"') { if (text[i + 1] === '"') { cur += '"'; i++; } else q = false; } else cur += c; }
      else if (c === '"') q = true;
      else if (c === ',') { row.push(cur); cur = ''; }
      else if (c === '\n') { row.push(cur); rows.push(row); row = []; cur = ''; }
      else if (c !== '\r') cur += c;
    }
    if (cur !== '' || row.length) { row.push(cur); rows.push(row); }
    return rows.filter(r => r.some(x => x !== ''));
  }
  const csvCell = v => { v = v === null || v === undefined ? '' : String(v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };

  /** CSV (colonnes date, exercise_name, set_index, reps, weight, tempo, rest, rpe, notes) -> base. */
  function csvToDb(text) {
    const rows = parseCSV(text);
    if (!rows.length) throw new Error('Le fichier CSV est vide.');
    const head = rows[0].map(h => h.trim().toLowerCase());
    const col = n => head.indexOf(n);
    if (col('date') < 0 || col('exercise_name') < 0 || col('reps') < 0) throw new Error('Colonnes attendues : date, exercise_name, reps, weight…');
    const db = emptyDb(); const byDate = {};
    for (const r of rows.slice(1)) {
      const date = (r[col('date')] || '').trim().slice(0, 10), name = (r[col('exercise_name')] || '').trim();
      if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !name) continue;
      let ex = db.exercises.find(e => e.name.toLowerCase() === name.toLowerCase());
      if (!ex) db.exercises.push(ex = { id: uid(), name, type: '' });
      let s = byDate[date];
      if (!s) { s = byDate[date] = { id: uid(), date, rpe: null, notes: '', entries: [] }; db.sessions.push(s); }
      let e = s.entries.find(x => x.exercise_id === ex.id);
      if (!e) s.entries.push(e = { id: uid(), exercise_id: ex.id, showTempo: false, sets: [] });
      const rpeRaw = (r[col('rpe')] || '').trim();
      const rpe = RPE_ICONS[rpeRaw] || (parseNum(rpeRaw) >= 1 && parseNum(rpeRaw) <= 5 ? Math.round(parseNum(rpeRaw)) : null);
      if (rpe) s.rpe = rpe;
      const note = (r[col('notes')] || '').trim();
      if (note && note !== '...') s.notes = note;
      const tempo = (r[col('tempo')] || '').trim();
      if (tempo) e.showTempo = true;
      e.sets.push({ w: parseNum(r[col('weight')]), r: parseNum(r[col('reps')]), tempo, rest: parseNum(r[col('rest')]), done: true });
    }
    db.sessions.sort((a, b) => a.date.localeCompare(b.date));
    return db;
  }

  function toCSV(db) {
    const out = [['date', 'exercise_name', 'set_index', 'reps', 'weight', 'tempo', 'rest', 'rpe', 'notes']];
    for (const s of [...db.sessions].sort((a, b) => a.date.localeCompare(b.date))) for (const e of s.entries) {
      const ex = db.exercises.find(x => x.id === e.exercise_id); if (!ex) continue;
      doneSets(e.sets).forEach((st, i) => out.push([s.date, ex.name, i + 1, st.r, st.w, st.tempo, st.rest, s.rpe, s.notes]));
    }
    return out.map(r => r.map(csvCell).join(',')).join('\n') + '\n';
  }

  /* -------------------------------------------------------- JSON */
  function toJSON(db) {
    const clean = {
      format: FORMAT, version: VERSION, exported_at: new Date().toISOString(),
      exercises: db.exercises,
      sessions: db.sessions.map(s => ({ id: s.id, date: s.date, rpe: s.rpe, notes: s.notes,
        entries: s.entries.map(e => ({ id: e.id, exercise_id: e.exercise_id, showTempo: e.showTempo,
          sets: doneSets(e.sets).map(x => ({ w: x.w, r: x.r, tempo: x.tempo, rest: x.rest })) })).filter(e => e.sets.length) })).filter(s => s.entries.length),
      bodyweight: db.bodyweight
    };
    return JSON.stringify(clean, null, 2);
  }

  function parseBackup(text) {
    let d;
    try { d = JSON.parse(text); } catch (e) { throw new Error('Ce fichier n\'est pas un JSON valide.'); }
    if (!d || d.format !== FORMAT) throw new Error('Ce JSON ne vient pas de PerformApp.');
    if (d.version > VERSION) throw new Error('Ce fichier vient d\'une version plus récente de PerformApp.');
    return normalizeDb(d);
  }

  /** Fusionne `inc` dans `local` sans doublon. Retourne les compteurs pour l'aperçu / le message final. */
  function mergeDb(local, inc, apply) {
    const stats = { newSessions: 0, newEntries: 0, skipped: 0, newExercises: 0 };
    const target = apply ? local : normalizeDb(JSON.parse(JSON.stringify(local)));
    const map = {};
    for (const ex of inc.exercises) {
      let l = target.exercises.find(x => x.id === ex.id) || target.exercises.find(x => x.name.toLowerCase() === ex.name.toLowerCase());
      if (!l) { target.exercises.push(l = { id: target.exercises.some(x => x.id === ex.id) ? uid() : ex.id, name: ex.name, type: ex.type, bw: ex.bw || 0 }); stats.newExercises++; }
      map[ex.id] = l.id;
    }
    for (const s of inc.sessions) {
      let l = target.sessions.find(x => x.id === s.id) || target.sessions.find(x => x.date === s.date);
      let created = false;
      if (!l) { l = { id: s.id, date: s.date, rpe: s.rpe, notes: s.notes, entries: [] }; target.sessions.push(l); created = true; }
      let added = 0;
      for (const e of s.entries) {
        const exId = map[e.exercise_id]; if (!exId) continue;
        if (l.entries.some(x => x.exercise_id === exId)) { stats.skipped++; continue; }
        l.entries.push({ id: e.id, exercise_id: exId, showTempo: e.showTempo, sets: e.sets.map(x => ({ ...x })) });
        added++; stats.newEntries++;
      }
      if (created) { if (added) stats.newSessions++; else target.sessions.pop(); }
    }
    for (const b of inc.bodyweight || []) if (!target.bodyweight.some(x => x.date === b.date)) target.bodyweight.push({ ...b });
    target.bodyweight.sort((a, b) => a.date.localeCompare(b.date));
    target.sessions.sort((a, b) => a.date.localeCompare(b.date));
    return { db: target, stats };
  }

  const api = { FORMAT, VERSION, uid, todayStr, dayNum, dayStr, parseNum, fmt, emptyDb, normalizeDb, METRICS, isDone, doneSets,
                metricOf, bodyweightAt, getSeries, getPrev, parseCSV, csvToDb, toCSV, toJSON, parseBackup, mergeDb };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.PA = api;
})(typeof window !== 'undefined' ? window : globalThis);

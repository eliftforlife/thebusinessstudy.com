// Vote page (11-03, Elijah): people vote on brands, models, years, insurance companies... Same file on lemonindex.com and thebusinessstudy.com
// (<main id="vote" data-site="lemon|bs" data-ts="<Turnstile site key or empty>">). Polls: /assets/votes.json (data/votes.json).
// Two tabs (11-03 v2, "more mobile friendly"):
//   Vote now  one poll at a time, big thumb-size answers; tap -> how everyone voted -> Next. Progress bar; polls you voted on this week are skipped.
//   Results   every poll with a period picker (week, month, 6 months, year, all time, or a past month); top 3 per poll, "See all" opens the rest.
// Votes: the lemon-survey Worker (/a to vote, /v for the counts). One vote per poll per visitor every 7 days; VPN / data-center networks are
// refused by the Worker; when a Turnstile key is set, every vote also carries an invisible human check.
(() => {
  const root = document.getElementById('vote'); if (!root) return;
  const API = 'https://lemon-survey.elift08.workers.dev', SITE = root.dataset.site, TS = root.dataset.ts || '';
  const KEY = 'vote-' + SITE, wk = Math.floor(Date.now() / (7 * 864e5));
  const mine = (() => { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch { return {}; } })();
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(mine)); } catch {} };
  const E = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const MON = m => new Date(m + '-15').toLocaleString('en-US', { month: 'long', year: 'numeric' });
  const PER = [['week', 'Week'], ['month', 'Month'], ['6mo', '6 months'], ['year', 'Year'], ['all', 'All time']];
  const LONG = { week: 'in the last 7 days', month: 'in the last 30 days', '6mo': 'in the last 6 months', year: 'in the last year', all: 'all time' };
  let polls = [], cats = {}, counts = {}, period = 'week', cat = 'all', months = [], voters = 0, busy = false, mode = 'play', open = new Set();
  let queue = [], qi = 0, shown = null;   // Vote now: the polls left this week, the current one, and its result after a tap
  const votedNow = id => mine[id] && mine[id].wk === wk ? mine[id].a : null;
  const buzz = () => { try { navigator.vibrate && navigator.vibrate(8); } catch {} };

  // ---- Turnstile (only when a site key is set): one invisible widget, a fresh token per vote
  let tsReady = null, wid = null, tsRes = null;
  if (TS) tsReady = new Promise(res => {
    window.onTsLoad = () => res(true);
    const s = document.createElement('script'); s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onTsLoad&render=explicit'; s.async = true;
    s.onerror = () => res(false); document.head.appendChild(s);
  });
  const token = async () => {
    if (!TS || !(await tsReady) || !window.turnstile) return '';
    return new Promise(res => {
      tsRes = t => { tsRes = null; res(t || ''); };
      setTimeout(() => tsRes && tsRes(''), 15000);
      const cb = t => tsRes && tsRes(t);
      if (wid === null) wid = turnstile.render('#ts-box', { sitekey: TS, size: 'flexible', appearance: 'interaction-only', execution: 'execute', callback: cb, 'error-callback': () => cb('') });
      else turnstile.reset(wid);
      turnstile.execute(wid);
    });
  };
  const toast = msg => { const t = root.querySelector('.v-toast'); t.textContent = msg; t.hidden = false; clearTimeout(t._h); t._h = setTimeout(() => (t.hidden = true), 6000); };

  // ---- one set of result bars (used by both tabs)
  const bars = (p, c, me, limit) => {
    const tot = p.a.reduce((s, a) => s + (c[a] || 0), 0);
    const order = [...p.a].sort((x, y) => (c[y] || 0) - (c[x] || 0) || p.a.indexOf(x) - p.a.indexOf(y));
    const rows = (limit ? order.slice(0, limit) : order).map((a, i) => { const n = c[a] || 0, pc = tot ? Math.round(n / tot * 100) : 0, lead = tot && i === 0;
      return `<button type="button" class="v-opt${a === me ? ' me' : ''}${lead ? ' lead' : ''}" data-p="${p.id}" data-a="${E(a)}"${me ? ' disabled' : ''}>
<i style="--w:${pc}%"></i><span>${lead ? '<b class="v-1">#1</b> ' : ''}${E(a)}${a === me ? ' <em>· you</em>' : ''}</span><b>${tot ? pc + '%' : ''}</b></button>`; }).join('');
    return { rows, tot };
  };

  // ---- Vote now
  const buildQueue = () => {   // polls not voted this week, categories interleaved so it never feels like 6 brand questions in a row
    const by = {}; polls.filter(p => !votedNow(p.id)).forEach(p => (by[p.cat] ||= []).push(p));
    const lists = Object.values(by); queue = [];
    for (let k = 0; lists.some(l => l[k]); k++) lists.forEach(l => l[k] && queue.push(l[k]));
    qi = 0; shown = null;
  };
  const play = () => {
    const box = root.querySelector('.v-play'), done = polls.length - queue.length + qi, p = queue[qi];
    const n = Math.min(polls.length, done + (shown ? 1 : 0));
    root.querySelector('.v-prog i').style.width = (polls.length ? Math.round(n / polls.length * 100) : 0) + '%';
    root.querySelector('.v-progn').textContent = `${n} of ${polls.length}`;
    if (!p) {
      box.innerHTML = `<div class="v-done"><p class="v-big">✓</p><h2>You voted on every poll this week.</h2><p>Come back next week to vote again, or see what everyone picked.</p>
<button type="button" class="btn v-go" data-go="results">See the results →</button></div>`; return;
    }
    if (!shown) {
      box.innerHTML = `<article class="v-q"><p class="v-cat">${E(cats[p.cat] || '')}</p><h2>${E(p.q)}</h2>
<div class="v-pick">${p.a.map(a => `<button type="button" class="v-ans" data-p="${p.id}" data-a="${E(a)}">${E(a)}</button>`).join('')}</div>
<button type="button" class="v-skip">Skip this one</button></article>`;
    } else {
      const { rows, tot } = bars(p, shown.c, shown.a);
      box.innerHTML = `<article class="v-q v-res"><p class="v-cat">${E(cats[p.cat] || '')}</p><h2>${E(p.q)}</h2><div class="v-opts">${rows}</div>
<p class="v-n">${tot <= 1 ? 'You’re the first to vote on this one.' : `${tot.toLocaleString('en-US')} votes so far`}</p>
<button type="button" class="btn v-next">${queue[qi + 1] ? 'Next question →' : 'Finish →'}</button></article>`;
      requestAnimationFrame(() => requestAnimationFrame(() => box.querySelectorAll('.v-opt i').forEach(i => i.classList.add('go'))));
    }
  };
  // ---- Results
  const card = p => {
    const c = counts[p.id] || {}, me = votedNow(p.id), all = open.has(p.id), { rows, tot } = bars(p, c, me, all ? 0 : 3);
    const more = p.a.length > 3 ? `<button type="button" class="v-more" data-more="${p.id}">${all ? 'Show less' : `See all ${p.a.length}`}</button>` : '';
    const note = tot ? `${tot.toLocaleString('en-US')} vote${tot === 1 ? '' : 's'}` : 'No votes yet';
    return `<article class="v-card"><p class="v-cat">${E(cats[p.cat] || '')}</p><h2>${E(p.q)}</h2><div class="v-opts">${rows}</div>
<div class="v-foot"><span class="v-n">${note}${me ? ' · you voted' : ''}</span>${more}</div></article>`;
  };
  const results = () => {
    const tot = p => Object.values(counts[p.id] || {}).reduce((s, n) => s + n, 0);
    const list = polls.filter(p => cat === 'all' || p.cat === cat).sort((x, y) => tot(y) - tot(x) || polls.indexOf(x) - polls.indexOf(y));
    root.querySelector('.v-grid').innerHTML = list.map(card).join('');
    requestAnimationFrame(() => requestAnimationFrame(() => root.querySelectorAll('.v-grid .v-opt i').forEach(i => i.classList.add('go'))));
    const lbl = LONG[period] || 'in ' + MON(period);
    root.querySelector('.v-sum').textContent = voters ? `${voters.toLocaleString('en-US')} ${voters === 1 ? 'person' : 'people'} voted ${lbl}` : `No votes ${lbl} yet. Be the first.`;
    root.querySelectorAll('.v-per [data-per]').forEach(b => b.classList.toggle('on', b.dataset.per === period));
    const sel = root.querySelector('.v-mon'); sel.innerHTML = '<option value="">Month…</option>' + months.map(m => `<option value="${m}"${m === period ? ' selected' : ''}>${MON(m)}</option>`).join('');
    sel.hidden = !months.length;
    root.querySelectorAll('.v-cats [data-cat]').forEach(b => b.classList.toggle('on', b.dataset.cat === cat));
  };
  const load = async () => {
    root.classList.add('loading');
    try { const j = await fetch(`${API}/v?site=${SITE}&period=${period}`).then(r => r.json()); counts = j.counts || {}; voters = j.voters || 0; if (j.months) months = j.months; }
    catch { counts = {}; voters = 0; }
    root.classList.remove('loading'); results();
  };
  const setMode = (m, scroll = true) => {
    mode = m; root.querySelectorAll('.v-tabs [data-go]').forEach(b => b.setAttribute('aria-selected', b.dataset.go === m));
    root.querySelector('.v-playwrap').hidden = m !== 'play'; root.querySelector('.v-reswrap').hidden = m !== 'results';
    if (m === 'results') load(); else { if (!queue[qi]) buildQueue(); play(); }
    const top = root.getBoundingClientRect().top + scrollY - 70; if (scroll && scrollY > top) scrollTo({ top, behavior: 'smooth' });
  };
  const vote = async (id, a) => {
    if (votedNow(id) || busy) return; busy = true; buzz();
    root.querySelectorAll(`[data-p="${id}"]`).forEach(b => { b.disabled = true; if (b.dataset.a === a) b.classList.add('picked'); });
    let c = null;
    try {
      const t = await token();
      const r = await fetch(API + '/a', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ qid: id, a, page: location.pathname, t }) });
      const j = await r.json().catch(() => ({}));
      if (j.error === 'vpn') toast('Voting is off on VPNs and data-center networks (that keeps the results real). Turn off your VPN or iCloud Private Relay and try again.');
      else if (j.error === 'human') toast('We couldn’t check that you’re a person. Refresh the page and try again.');
      else if (!r.ok) toast('That vote didn’t go through. Try again in a minute.');
      else if (j.limited) toast('That’s a lot of votes for one day. Come back tomorrow.');
      else { mine[id] = { a, wk }; save(); c = j.counts || { [a]: 1 }; if (j.voted) toast('You already voted on this one this week.'); }
    } catch { toast('That vote didn’t go through. Check your connection.'); }
    busy = false;
    if (mode === 'play') { if (c) shown = { a, c }; play(); }
    else if (c) load(); else results();
  };

  root.innerHTML = `<div class="v-tabs" role="tablist"><button type="button" role="tab" data-go="play">Vote now</button><button type="button" role="tab" data-go="results">Results</button></div>
<section class="v-playwrap"><div class="v-progrow"><div class="v-prog"><i></i></div><span class="v-progn"></span></div><div class="v-play"></div></section>
<section class="v-reswrap" hidden><div class="v-bar"><div class="v-per">${PER.map(([k, l]) => `<button type="button" data-per="${k}">${l}</button>`).join('')}</div>
<select class="v-mon" aria-label="Pick a month" hidden></select></div><div class="v-cats"></div><p class="v-sum"></p><div class="v-grid"></div></section>
<div id="ts-box" class="v-ts"></div><p class="v-toast" role="status" hidden></p>
<p class="v-fine">Anonymous: no email, no account. One vote per poll every 7 days. Votes from VPNs and data-center networks don’t count. These are opinions from our visitors, not a scientific survey.</p>`;
  root.addEventListener('click', e => {
    const b = e.target.closest('button'); if (!b || b.disabled) return;
    if (b.dataset.go) return setMode(b.dataset.go);
    if (b.dataset.per) { period = b.dataset.per; return load(); }
    if (b.dataset.cat) { cat = b.dataset.cat; return results(); }
    if (b.dataset.more) { open.has(b.dataset.more) ? open.delete(b.dataset.more) : open.add(b.dataset.more); return results(); }
    if (b.classList.contains('v-skip')) { queue.push(queue.splice(qi, 1)[0]); shown = null; return play(); }
    if (b.classList.contains('v-next')) { qi++; shown = null; return play(); }
    if (b.dataset.p && b.dataset.a) vote(b.dataset.p, b.dataset.a);
  });
  root.querySelector('.v-mon').addEventListener('change', e => { if (e.target.value) { period = e.target.value; load(); } });
  fetch('/assets/votes.json').then(r => r.json()).then(j => {
    polls = j[SITE] || []; cats = j.cats[SITE] || {};
    root.querySelector('.v-cats').innerHTML = `<button type="button" data-cat="all">All</button>` + Object.entries(cats).map(([k, l]) => `<button type="button" data-cat="${k}">${E(l)}</button>`).join('');
    buildQueue(); setMode(queue.length && location.hash !== '#results' ? 'play' : 'results', false);
  }).catch(() => { root.querySelector('.v-play').textContent = 'The polls didn’t load. Refresh to try again.'; });
})();

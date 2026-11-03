// Vote page (11-03, Elijah): people vote on brands, models, years, insurance companies...; a period picker shows what won this week,
// this month, the last 6 months, this year, all time, or any past month. Same file on lemonindex.com and thebusinessstudy.com
// (<main id="vote" data-site="lemon|bs" data-ts="<Turnstile site key or empty>">). Polls: /assets/votes.json (data/votes.json).
// Votes: the lemon-survey Worker (/a to vote, /v for the counts). One vote per poll per visitor every 7 days; VPN / data-center
// networks are refused by the Worker; when a Turnstile key is set, every vote also carries an invisible human check.
(() => {
  const root = document.getElementById('vote'); if (!root) return;
  const API = 'https://lemon-survey.elift08.workers.dev', SITE = root.dataset.site, TS = root.dataset.ts || '';
  const KEY = 'vote-' + SITE, WEEK = 7 * 864e5, wk = Math.floor(Date.now() / WEEK);
  const mine = (() => { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch { return {}; } })();
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(mine)); } catch {} };
  const E = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const MON = m => new Date(m + '-15').toLocaleString('en-US', { month: 'long', year: 'numeric' });
  const PER = [['week', 'Week'], ['month', 'Month'], ['6mo', '6 months'], ['year', 'Year'], ['all', 'All time']];
  const LONG = { week: 'in the last 7 days', month: 'in the last 30 days', '6mo': 'in the last 6 months', year: 'in the last year', all: 'all time' };
  let polls = [], cats = {}, counts = {}, period = 'week', cat = 'all', months = [], voters = 0, busy = {};
  const votedNow = id => mine[id] && mine[id].wk === wk ? mine[id].a : null;

  // ---- Turnstile (only when a site key is set): one invisible widget, a fresh token per vote
  let tsReady = null;
  if (TS) tsReady = new Promise(res => {
    window.onTsLoad = () => res(true);
    const s = document.createElement('script'); s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onTsLoad&render=explicit'; s.async = true;
    s.onerror = () => res(false); document.head.appendChild(s);
  });
  let wid = null, tsRes = null;
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
  const card = p => {
    const c = counts[p.id] || {}, tot = p.a.reduce((s, a) => s + (c[a] || 0), 0), me = votedNow(p.id);
    const order = [...p.a].sort((x, y) => (c[y] || 0) - (c[x] || 0) || p.a.indexOf(x) - p.a.indexOf(y));
    const rows = order.map((a, i) => { const n = c[a] || 0, pc = tot ? Math.round(n / tot * 100) : 0, lead = tot && i === 0;
      return `<button type="button" class="v-opt${a === me ? ' me' : ''}${lead ? ' lead' : ''}" data-p="${p.id}" data-a="${E(a)}"${me ? ' aria-pressed="' + (a === me) + '"' : ''}>
<i style="width:${pc}%"></i><span>${lead ? '<b class="v-1">#1</b> ' : ''}${E(a)}${a === me ? ' <em>· your vote</em>' : ''}</span><b>${tot ? pc + '%' : ''}</b></button>`; }).join('');
    const note = tot ? `${tot.toLocaleString('en-US')} vote${tot === 1 ? '' : 's'}` : 'No votes yet: be the first';
    return `<article class="v-card" data-cat="${p.cat}"><p class="v-cat">${E(cats[p.cat] || '')}</p><h2>${E(p.q)}</h2><div class="v-opts">${rows}</div>
<p class="v-n">${note}${me ? ' · you can vote again next week' : ''}</p></article>`;
  };
  const render = () => {
    const list = polls.filter(p => cat === 'all' || p.cat === cat);
    // the busiest polls of the period first, so the page opens on what people are arguing about
    const tot = p => Object.values(counts[p.id] || {}).reduce((s, n) => s + n, 0);
    list.sort((x, y) => tot(y) - tot(x) || polls.indexOf(x) - polls.indexOf(y));
    root.querySelector('.v-grid').innerHTML = list.map(card).join('');
    const lbl = LONG[period] || 'in ' + MON(period);
    root.querySelector('.v-sum').textContent = voters ? `${voters.toLocaleString('en-US')} ${voters === 1 ? 'person' : 'people'} voted ${lbl}` : `No votes yet ${period === 'all' ? '' : 'in this period '}· be the first`;
    root.querySelectorAll('.v-per [data-per]').forEach(b => b.classList.toggle('on', b.dataset.per === period));
    const sel = root.querySelector('.v-mon'); sel.innerHTML = '<option value="">Pick a month</option>' + months.map(m => `<option value="${m}"${m === period ? ' selected' : ''}>${MON(m)}</option>`).join('');
    sel.hidden = !months.length;
    root.querySelectorAll('.v-cats [data-cat]').forEach(b => b.classList.toggle('on', b.dataset.cat === cat));
  };
  const load = async () => {
    root.classList.add('loading');
    try { const r = await fetch(`${API}/v?site=${SITE}&period=${period}`); const j = await r.json(); counts = j.counts || {}; voters = j.voters || 0; if (j.months) months = j.months; }
    catch { counts = {}; voters = 0; }
    root.classList.remove('loading'); render();
  };
  const vote = async (id, a) => {
    if (votedNow(id) || busy[id]) return; busy[id] = true;
    try {
      const t = await token();
      const r = await fetch(API + '/a', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ qid: id, a, page: location.pathname, t }) });
      const j = await r.json().catch(() => ({}));
      if (j.error === 'vpn') return toast('Voting is off on VPNs and data-center networks (that keeps the results real). Turn off your VPN or iCloud Private Relay and try again.');
      if (j.error === 'human') return toast('We couldn’t check that you’re a person. Refresh the page and try again.');
      if (!r.ok) return toast('That vote didn’t go through. Try again in a minute.');
      if (j.limited) return toast('That’s a lot of votes for one day. Come back tomorrow.');
      mine[id] = { a, wk }; save();
      if (j.voted) toast('You already voted on this one this week.');
      await load();
    } catch { toast('That vote didn’t go through. Check your connection.'); }
    finally { busy[id] = false; }
  };

  root.innerHTML = `<div class="v-bar"><div class="v-per" role="tablist">${PER.map(([k, l]) => `<button type="button" data-per="${k}">${l}</button>`).join('')}</div>
<select class="v-mon" aria-label="Pick a month" hidden></select></div>
<div class="v-cats"></div><p class="v-sum"></p><div class="v-grid"></div><div id="ts-box" class="v-ts"></div><p class="v-toast" role="status" hidden></p>
<p class="v-fine">Anonymous: no email, no account. One vote per poll every 7 days. Votes from VPNs and data-center networks don’t count. These are opinions from our visitors, not a scientific survey.</p>`;
  root.querySelector('.v-per').addEventListener('click', e => { const b = e.target.closest('[data-per]'); if (b) { period = b.dataset.per; load(); } });
  root.querySelector('.v-mon').addEventListener('change', e => { if (e.target.value) { period = e.target.value; load(); } });
  root.querySelector('.v-cats').addEventListener('click', e => { const b = e.target.closest('[data-cat]'); if (b) { cat = b.dataset.cat; render(); } });
  root.querySelector('.v-grid').addEventListener('click', e => { const b = e.target.closest('.v-opt'); if (b) vote(b.dataset.p, b.dataset.a); });
  fetch('/assets/votes.json').then(r => r.json()).then(j => {
    polls = j[SITE] || []; cats = j.cats[SITE] || {};
    root.querySelector('.v-cats').innerHTML = `<button type="button" data-cat="all">All</button>` + Object.entries(cats).map(([k, l]) => `<button type="button" data-cat="${k}">${E(l)}</button>`).join('');
    load();
  }).catch(() => { root.querySelector('.v-sum').textContent = 'The polls didn’t load. Refresh to try again.'; });
})();

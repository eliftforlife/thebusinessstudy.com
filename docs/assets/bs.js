// thebusinessstudy.com v2 (11-08). Everything here is extra: every page reads fine without it (real HTML text and tables), and motion
// stays still for people who ask for reduced motion. Data for the tools: /assets/data/co.json (built from the companies' 10-Ks).
(() => {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let DATA = null;
  const data = () => DATA || (DATA = fetch('/assets/data/co.json').then(r => r.json()));
  const B = v => { const a = Math.abs(v), s = v < 0 ? '-' : ''; return a >= 1e12 ? `${s}$${(a / 1e12).toFixed(2)} trillion` : a >= 1e9 ? `${s}$${(a / 1e9).toFixed(a >= 1e11 ? 0 : 1)} billion` : a >= 1e6 ? `${s}$${Math.round(a / 1e6).toLocaleString('en-US')} million` : `${s}$${Math.round(a).toLocaleString('en-US')}`; };
  const K = v => { const a = Math.abs(v), s = v < 0 ? '-' : ''; return a >= 1e6 ? `${s}$${(a / 1e6).toFixed(2)} million` : `${s}$${Math.round(a).toLocaleString('en-US')}`; };

  // 1. reveals (bars grow, columns rise)
  const show = el => el.classList.add('in');
  if (still || !('IntersectionObserver' in window)) $$('.reveal, .bars, .cols').forEach(show);
  else {
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { show(e.target); io.unobserve(e.target); } }), { rootMargin: '0px 0px -6% 0px', threshold: .06 });
    $$('.reveal, .bars, .cols').forEach(el => io.observe(el));
  }

  // 2. company search (home + companies hub): type, pick, Enter goes to the first match
  $$('.search').forEach(box => {
    const inp = $('input', box), ul = document.createElement('ul'); ul.hidden = true; ul.setAttribute('role', 'listbox'); box.appendChild(ul);
    let hits = [], on = 0;
    const draw = () => { ul.innerHTML = hits.map((c, i) => `<li><a href="/companies/${c.s}/" class="${i === on ? 'on' : ''}">${c.n}<small>${B(c.r)} revenue</small></a></li>`).join(''); ul.hidden = !hits.length; };
    inp.addEventListener('input', async () => {
      const q = inp.value.trim().toLowerCase(); if (!q) { hits = []; draw(); return; }
      const d = await data(); on = 0;
      hits = d.filter(c => (c.n + ' ' + (c.a || '')).toLowerCase().includes(q)).sort((a, b) => a.n.toLowerCase().indexOf(q) - b.n.toLowerCase().indexOf(q) || b.r - a.r).slice(0, 7); draw();
    });
    inp.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); on = Math.max(0, Math.min(hits.length - 1, on + (e.key === 'ArrowDown' ? 1 : -1))); draw(); }
      if (e.key === 'Enter' && hits[on]) { e.preventDefault(); location.href = `/companies/${hits[on].s}/`; }
      if (e.key === 'Escape') { hits = []; draw(); }
    });
    document.addEventListener('click', e => { if (!box.contains(e.target)) ul.hidden = true; });
  });

  // 3. sortable tables + table filter
  $$('table.sort').forEach(t => {
    $$('th[data-k]', t).forEach((th, ci) => {
      const b = document.createElement('button'); b.type = 'button'; b.textContent = th.textContent; th.textContent = ''; th.appendChild(b);
      b.addEventListener('click', () => {
        const idx = [...th.parentNode.children].indexOf(th), desc = th.getAttribute('aria-sort') !== 'descending';
        $$('th', t).forEach(x => x.removeAttribute('aria-sort')); th.setAttribute('aria-sort', desc ? 'descending' : 'ascending');
        const rows = $$('tbody tr', t), v = r => { const c = r.children[idx]; const d = c.dataset.v; return d !== undefined ? (d === '' ? -Infinity : +d) : c.textContent.trim().toLowerCase(); };
        rows.sort((a, b) => { const x = v(a), y = v(b); return (x > y ? 1 : x < y ? -1 : 0) * (desc ? -1 : 1); });
        const tb = $('tbody', t); rows.forEach((r, i) => { tb.appendChild(r); const n = $('td.n', r); if (n) n.textContent = i + 1; });
      });
    });
  });
  $$('[data-filter]').forEach(inp => {
    const t = $(inp.dataset.filter); if (!t) return;
    const run = () => { const q = inp.value.trim().toLowerCase(), sec = $('[data-sector]')?.value || '';
      $$('tbody tr', t).forEach(r => { r.hidden = !(r.textContent.toLowerCase().includes(q) && (!sec || r.dataset.sector === sec)); }); };
    inp.addEventListener('input', run); $('[data-sector]')?.addEventListener('change', run);
  });

  // 4. the $100 card on the home page: cycle through companies
  const k = $('.k100[data-cycle]');
  if (k) {
    const list = JSON.parse(k.dataset.cycle); let i = 0;
    const draw = () => {
      const c = list[i], kept = c.k, loss = kept < 0;
      $('.who span', k).textContent = c.n; $('.who', k).href = `/companies/${c.s}/`;
      $('.say', k).textContent = loss ? `Out of every $100 in sales, ${c.n} lost` : `Out of every $100 in sales, ${c.n} kept`;
      $('.big', k).innerHTML = `$${Math.abs(kept).toFixed(2)}<small>${loss ? 'lost' : 'profit'}</small>`;
      const bar = $('.bar100', k); bar.classList.toggle('loss', loss); bar.classList.toggle('thin', Math.abs(kept) < 16);
      bar.style.setProperty('--w', Math.min(100, Math.abs(kept)) + '%');
      $('.bar100 em span:first-child', k).textContent = loss ? 'Lost' : 'Kept'; $('.bar100 em span:last-child', k).textContent = loss ? '' : `Costs, taxes and everything else: $${(100 - kept).toFixed(2)}`;
      $('.src', k).textContent = `Net income ÷ revenue, ${c.y}. Source: ${c.n}'s annual report (Form 10-K).`;
    };
    $$('.nav button', k).forEach(b => b.addEventListener('click', () => { i = (i + (b.dataset.d === 'next' ? 1 : list.length - 1)) % list.length; draw(); }));
  }

  // 5. click-to-load YouTube (no YouTube cookies until someone presses play)
  $$('.yt').forEach(y => y.addEventListener('click', () => {
    if ($('iframe', y)) return;
    const f = document.createElement('iframe'); f.src = `https://www.youtube-nocookie.com/embed/${y.dataset.id}?autoplay=1&rel=0`; f.title = y.dataset.title || 'Video';
    f.allow = 'autoplay; encrypted-media; picture-in-picture'; f.allowFullscreen = true; y.appendChild(f);
  }));

  // 6. compare tool (/compare/)
  const cmp = $('#cmp');
  if (cmp) data().then(d => {
    const by = Object.fromEntries(d.map(c => [c.s, c])), [sa, sb] = $$('select', cmp), out = $('#cmp-out');
    const opts = d.slice().sort((a, b) => a.n.localeCompare(b.n)).map(c => `<option value="${c.s}">${c.n}</option>`).join('');
    sa.innerHTML = opts; sb.innerHTML = opts;
    const q = new URLSearchParams(location.search); sa.value = by[q.get('a')] ? q.get('a') : 'coca-cola'; sb.value = by[q.get('b')] ? q.get('b') : 'pepsico';
    const ROUNDS = [['Revenue', c => c.r, B, 'Money coming in'], ['Profit', c => c.p, B, 'Net income, after every cost and tax'],
      ['Kept per $100 of sales', c => c.p / c.r * 100, v => `$${v.toFixed(2)}`, 'Profit margin'], ['Employees', c => c.e, v => v.toLocaleString('en-US'), 'As the 10-K states it'],
      ['Revenue per employee', c => c.e ? c.r / c.e : null, K, 'Revenue ÷ employees'], ['Growth over 5 years', c => c.g, v => `${v > 0 ? '+' : ''}${Math.round(v)}%`, 'Revenue change, first to latest year shown']];
    const draw = () => {
      const a = by[sa.value], b = by[sb.value]; let wa = 0, wb = 0;
      history.replaceState(null, '', `?a=${a.s}&b=${b.s}`);
      const rows = ROUNDS.map(([t, f, fm, sub]) => {
        const x = f(a), y = f(b); if (x == null || y == null || isNaN(x) || isNaN(y)) return '';
        const top = Math.max(Math.abs(x), Math.abs(y)) || 1, ax = x >= y, bx = y > x, counts = t !== 'Employees'; if (counts) { ax ? wa++ : wb++; }
        const side = (c, v, win) => `<div class="side${win ? ' win' : ''}${v < 0 ? ' neg' : ''}"><div class="name">${c.n}${win ? `<em>${counts ? 'Wins' : 'More'}</em>` : ''}</div><div class="num">${fm(v)}</div><div class="b"><i style="--w:${Math.max(1, Math.abs(v) / top * 100)}%"></i></div></div>`;
        return `<div class="round"><h3>${t} <small>${sub}</small></h3><div class="duel">${side(a, x, ax)}${side(b, y, bx)}</div></div>`;
      }).join('');
      const page = a.cp && a.cp[b.s] ? `<p class="note">Full breakdown: <a href="/compare/${a.cp[b.s]}/">${a.n} vs ${b.n}</a>.</p>` : '';
      out.innerHTML = `<div class="score"><div><b>${wa}</b><span>${a.n}</span></div><i>–</i><div><b>${wb}</b><span>${b.n}</span></div></div>${rows}
        <p class="note">Latest annual reports: ${a.n} (${a.y}) and ${b.n} (${b.y}). Open each company's page for its sources. ${page}</p>`;
    };
    sa.addEventListener('change', draw); sb.addEventListener('change', draw); $('#cmp-swap')?.addEventListener('click', () => { [sa.value, sb.value] = [sb.value, sa.value]; draw(); }); draw();
  });

  // 7. the higher-or-lower game (/game/)
  const g = $('#game');
  if (g) data().then(d => {
    const MODES = { rev: ['Which company brings in more money a year?', c => c.r, B, 'revenue'], prof: ['Which company made more profit?', c => c.p, B, 'profit'],
      emp: ['Which company makes more per employee?', c => c.e ? c.r / c.e : null, K, 'revenue per employee'], keep: ['Which keeps more of every $100 in sales?', c => c.p / c.r * 100, v => `$${v.toFixed(2)}`, 'kept per $100'] };
    let mode = 'rev', streak = 0, best = 0, pair = [];
    try { best = +localStorage.getItem('bs-best') || 0; } catch (e) {}
    const pool = () => d.filter(c => MODES[mode][1](c) != null && c.r > 2e9);
    const next = () => {
      const p = pool(); let a, b, tries = 0;
      do { a = p[Math.floor(Math.random() * p.length)]; b = p[Math.floor(Math.random() * p.length)]; tries++; }
      while ((a === b || Math.abs(MODES[mode][1](a) - MODES[mode][1](b)) / Math.max(Math.abs(MODES[mode][1](a)), Math.abs(MODES[mode][1](b))) < .04) && tries < 50);
      pair = [a, b]; $('.q', g).textContent = MODES[mode][0]; $('.msg', g).textContent = '';
      $$('.opt', g).forEach((o, i) => { o.disabled = false; o.className = 'opt'; $('.nm', o).textContent = pair[i].n; $('.val', o).textContent = ''; $('.sub', o).textContent = ''; });
      $('#g-next').hidden = true;
    };
    $$('.opt', g).forEach((o, i) => o.addEventListener('click', () => {
      const f = MODES[mode][1], v = pair.map(f), win = v[0] >= v[1] ? 0 : 1, ok = i === win;
      $$('.opt', g).forEach((x, j) => { x.disabled = true; x.classList.add(j === win ? 'right' : (j === i ? 'wrong' : 'x')); $('.val', x).textContent = MODES[mode][2](v[j]); $('.sub', x).textContent = `${MODES[mode][3]}, ${pair[j].y}`; });
      streak = ok ? streak + 1 : 0; if (streak > best) { best = streak; try { localStorage.setItem('bs-best', best); } catch (e) {} }
      $('.msg', g).innerHTML = ok ? `Right. ${pair[win].n} wins by ${MODES[mode][2](Math.abs(v[0] - v[1]))}.` : `Not this time. <a href="/companies/${pair[win].s}/">See how ${pair[win].n} makes its money</a>.`;
      $('#g-streak').textContent = streak; $('#g-best').textContent = best; $('#g-next').hidden = false; $('#g-next').focus();
    }));
    $('#g-next').addEventListener('click', next);
    $$('.modes button', g).forEach(b => b.addEventListener('click', () => { mode = b.dataset.m; $$('.modes button', g).forEach(x => x.setAttribute('aria-pressed', String(x === b))); streak = 0; $('#g-streak').textContent = 0; next(); }));
    $('#g-best').textContent = best; next();
  });
})();

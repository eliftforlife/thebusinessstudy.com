// Site header v7 (11-05): hairline once scrolled, menu / More panel, Esc and outside-click close, reading progress (body.reading),
// and on headers with data-tuck the bar slides away while scrolling down on phones. Master copy: 0 HQ/Tools/site header/gh.js
(() => {
  const h = document.querySelector('.gh'); if (!h) return;
  const btns = h.querySelectorAll('.gh-menu, .gh-more'), bar = h.querySelector('.gh-progress i'), reading = document.body.classList.contains('reading');
  const phone = matchMedia('(max-width: 767px)');
  const set = open => {
    h.style.setProperty('--gh-b', Math.max(0, h.getBoundingClientRect().bottom) + 'px');
    h.classList.toggle('open', open); h.classList.remove('tuck');
    btns.forEach(b => b.setAttribute('aria-expanded', String(open)));
    document.documentElement.classList.toggle('gh-lock', open && phone.matches);
  };
  btns.forEach(b => b.addEventListener('click', e => { e.stopPropagation(); set(!h.classList.contains('open')); }));
  document.addEventListener('click', e => { if (h.classList.contains('open') && !h.contains(e.target)) set(false); });
  addEventListener('keydown', e => { if (e.key === 'Escape' && h.classList.contains('open')) { set(false); (h.querySelector('.gh-menu') || btns[0]).focus(); } });
  h.querySelectorAll('.gh-sheet a').forEach(a => a.addEventListener('click', () => set(false)));
  phone.addEventListener && phone.addEventListener('change', () => set(false));
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches, tuck = h.hasAttribute('data-tuck');
  let last = scrollY, tick = false;
  const onScroll = () => {
    const y = scrollY; h.classList.toggle('sc', y > 4);
    if (tuck && !still && phone.matches && !h.classList.contains('open')) { const d = y - last; if (Math.abs(d) > 6) { h.classList.toggle('tuck', d > 0 && y > 140 && !h.contains(document.activeElement)); last = y; } }
    if (reading && bar) { const m = document.documentElement.scrollHeight - innerHeight; bar.style.transform = `scaleX(${m > 0 ? Math.min(1, y / m) : 0})`; }
    tick = false;
  };
  addEventListener('scroll', () => { if (!tick) { tick = true; requestAnimationFrame(onScroll); } }, { passive: true }); onScroll();
})();

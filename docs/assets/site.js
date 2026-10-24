// elijahwestbrook.com motion. Everything here is extra: the pages read fine without it, and it all stays still for reduced-motion users.
(() => {
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // 1. scroll reveals: .reveal fades/slides up once it enters the screen (charts also grow their bars, big numbers count up)
  const show = el => { el.classList.add('in'); $$('.num', el).forEach(countUp); };
  if (still || !('IntersectionObserver' in window)) $$('.reveal, .shero, .hero').forEach(show);
  else {
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { show(e.target); io.unobserve(e.target); } }), { rootMargin: '0px 0px -8% 0px', threshold: .08 });
    $$('.reveal').forEach(el => io.observe(el));
    requestAnimationFrame(() => $$('.shero, .hero').forEach(show));     // the top of the page animates in right away
  }

  // 2. numbers count up from 0 (keeps decimals, adds thousands commas)
  function countUp(el) {
    if (el.dataset.done) return; el.dataset.done = 1;
    const to = parseFloat(el.dataset.to), dec = +el.dataset.dec || 0, f = n => n.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec });
    if (still) { el.textContent = f(to); return; }
    const t0 = performance.now(), dur = 1200;
    const tick = t => { const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 4); el.textContent = f(to * e); if (k < 1) requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
  }

  // 3. header: shadow once scrolled, reading progress bar on study pages
  const top = document.querySelector('.top'), bar = document.querySelector('.progress i'), reading = document.body.classList.contains('reading');
  const onScroll = () => {
    top.classList.toggle('scrolled', scrollY > 8);
    if (reading && bar) { const h = document.documentElement.scrollHeight - innerHeight; bar.style.transform = `scaleX(${h > 0 ? Math.min(1, scrollY / h) : 0})`; }
  };
  addEventListener('scroll', onScroll, { passive: true }); onScroll();

  // 4. mobile menu
  const btn = document.querySelector('.menu');
  btn && btn.addEventListener('click', () => { const o = top.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
  $$('.sheet a').forEach(a => a.addEventListener('click', () => top.classList.remove('open')));

  // 5. click-to-load YouTube (the player only loads when someone presses play)
  $$('.yt').forEach(box => box.addEventListener('click', () => {
    if (box.classList.contains('on')) return; box.classList.add('on');
    const f = document.createElement('iframe');
    f.src = `https://www.youtube-nocookie.com/embed/${box.dataset.id}?autoplay=1&rel=0`;
    f.title = box.dataset.title; f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen'; f.allowFullscreen = true;
    box.appendChild(f);
  }));

  // 6. table of contents: highlight the section you're reading
  const toc = $$('.toc a');
  if (toc.length && 'IntersectionObserver' in window) {
    const map = new Map(toc.map(a => [a.getAttribute('href').slice(1), a]));
    const so = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { toc.forEach(a => a.classList.remove('on')); map.get(e.target.id)?.classList.add('on'); } }), { rootMargin: '-40% 0px -55% 0px' });
    map.forEach((_, id) => { const s = document.getElementById(id); s && so.observe(s); });
  }
})();

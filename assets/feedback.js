// Feedback box above the footer (11-09, Elijah: "a feedback box on most all pages, just to try to get feedback"). Same file on all 4 sites.
// Sends {page path, message, optional email} to the lemon-survey Worker (/feedback). The site comes from the page's origin, and the
// page path never carries a query string, so calculator inputs can't ride along. Honeypot field + server-side rate limits.
(() => {
  const f = document.querySelector('form.fb-f'); if (!f) return;
  const API = 'https://lemon-survey.elift08.workers.dev/feedback';
  const msg = f.querySelector('textarea'), em = f.querySelector('input[type=email]'), hp = f.querySelector('.fb-hp'), st = f.querySelector('.fb-st'), btn = f.querySelector('button[type=submit]');
  const say = (t, bad) => { st.textContent = t; st.classList.toggle('bad', !!bad); };
  f.addEventListener('submit', async e => {
    e.preventDefault();
    const m = msg.value.trim(), mail = em ? em.value.trim() : '';
    if (m.length < 2) { say('Type a message first.', true); msg.focus(); return; }
    if (mail && !(em.checkValidity && em.checkValidity())) { say('That email doesn’t look right. You can also leave it empty.', true); em.focus(); return; }
    btn.disabled = true; say('Sending…');
    try {
      const r = await fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ page: location.pathname, message: m.slice(0, 1000), email: mail, hp: hp ? hp.value : '' }) });
      if (r.status === 429) { say('Too many messages for now. Try again in a minute.', true); btn.disabled = false; return; }
      if (!r.ok) throw new Error(r.status);
      f.classList.add('sent'); f.querySelectorAll('.fb-in').forEach(x => { x.hidden = true; }); say('Thanks, we read every one.'); st.focus();
    } catch (err) { say('That didn’t send. Please try again.', true); btn.disabled = false; }
  });
})();

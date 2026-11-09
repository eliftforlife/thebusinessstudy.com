// "Send this to a friend" (11-09; same component as lemonindex.com/assets/share.js).
// Phones: the native share sheet (Messages, WhatsApp, IG DMs...). Elsewhere: a small panel with copy link, text, WhatsApp, Facebook, X, Reddit and email.
// Links carry ?utm_source=share so shares show in analytics. Any other query string is dropped, so a share never carries what someone typed.
(() => {
  const btns = document.querySelectorAll('[data-share]'); if (!btns.length) return;
  const url = () => { const u = new URL(location.href); u.search = ''; u.hash = ''; u.searchParams.set('utm_source', 'share'); return u.toString(); };
  const enc = encodeURIComponent;
  let panel, opener;
  const close = () => { if (!panel || panel.hidden) return; panel.hidden = true; if (opener) opener.focus(); };
  const open = (text, from) => {
    const u = url(), msg = `${text} ${u}`; opener = from;
    if (!panel) { panel = document.createElement('div'); panel.className = 'shr'; panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-modal', 'true'); panel.setAttribute('aria-label', 'Send this to a friend'); document.body.appendChild(panel);
      panel.addEventListener('click', e => { if (e.target === panel) close(); }); document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); }); }
    const L = [['Text message', `sms:?&body=${enc(msg)}`], ['WhatsApp', `https://wa.me/?text=${enc(msg)}`], ['Facebook', `https://www.facebook.com/sharer/sharer.php?u=${enc(u)}`],
      ['X', `https://x.com/intent/post?text=${enc(text)}&url=${enc(u)}`], ['Reddit', `https://www.reddit.com/submit?url=${enc(u)}&title=${enc(text)}`], ['Email', `mailto:?subject=${enc(text)}&body=${enc(msg)}`]];
    panel.innerHTML = `<div class="shr-card"><button class="shr-x" type="button" aria-label="Close">×</button><p class="shr-h">Send this to a friend</p><p class="shr-t">${text.replace(/[<>&]/g, '')}</p>
<button class="btn shr-copy" type="button">Copy link</button><div class="shr-l">${L.map(([n, h]) => `<a href="${h}" target="_blank" rel="noopener">${n}</a>`).join('')}</div></div>`;
    panel.querySelector('.shr-x').onclick = close;
    const cp = panel.querySelector('.shr-copy');
    const legacy = () => { const t = document.createElement('textarea'); t.value = u; t.setAttribute('readonly', ''); t.style.cssText = 'position:fixed;opacity:0'; panel.appendChild(t); t.select();
      let ok = false; try { ok = document.execCommand('copy'); } catch {} t.remove(); return ok; };
    cp.onclick = async () => {
      let ok = false; try { await navigator.clipboard.writeText(u); ok = true; } catch { ok = legacy(); }
      if (ok) { cp.textContent = 'Copied ✓'; return; }
      const i = document.createElement('input'); i.className = 'shr-u'; i.readOnly = true; i.value = u; i.setAttribute('aria-label', 'Link to copy'); cp.replaceWith(i); i.focus(); i.select();   // no clipboard (some in-app browsers): show the link selected
    };
    panel.hidden = false; cp.focus();
  };
  btns.forEach(b => b.addEventListener('click', async () => {
    const text = b.dataset.share;
    if (navigator.share && matchMedia('(pointer: coarse)').matches) { try { await navigator.share({ title: document.title, text, url: url() }); return; } catch (e) { if (e && e.name === 'AbortError') return; } }
    open(text, b);
  }));
})();

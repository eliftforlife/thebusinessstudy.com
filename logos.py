# 11-08: one icon per company (its own site icon, 128 px, from Google's public favicon service), saved once to assets/logos/<slug>.png.
# Used only on that company's own page and on compare pages that are about it (rights checklist: logos identify the company the page is about).
#   py logos.py          (skips icons already on disk; keeps only real PNGs of 64 px or more)
import os, sys, struct, urllib.request, time, json
sys.path.insert(0, 'data'); from companies_list import COMPANIES
OUT = os.path.join('assets', 'logos'); os.makedirs(OUT, exist_ok=True); ok = []
for slug, t, legal, short, dom in COMPANIES:
    p = os.path.join(OUT, slug + '.png')
    if not os.path.exists(p):
        try:
            b = urllib.request.urlopen(urllib.request.Request(f'https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://{dom}&size=128', headers={'User-Agent': 'bs-logos/1.0'}), timeout=20).read()
        except Exception as e: print(slug, 'fail', e); continue
        if b[:4] != b'\x89PNG': print(slug, 'not png'); continue
        open(p, 'wb').write(b); time.sleep(.1)
    b = open(p, 'rb').read(); w, h = struct.unpack('>II', b[16:24])
    if w >= 64: ok.append(slug)
    else: os.remove(p); print(slug, 'too small', w)
json.dump(sorted(ok), open(os.path.join(OUT, 'have.json'), 'w'), indent=0); print(len(ok), 'icons')

# 11-08: second pass for companies whose site icon failed in logos.py: tries www., another host, then 64 px; keeps PNGs 48 px or more.
import os, sys, struct, urllib.request, json
sys.path.insert(0, 'data'); from companies_list import COMPANIES
OUT = os.path.join('assets', 'logos'); have = set(json.load(open(os.path.join(OUT, 'have.json'))))
ALT = {'kroger': ['kroger.com', 'www.kroger.com'], 'cvs': ['cvs.com', 'www.cvs.com'], 'carnival': ['www.carnival.com'], 'procter-gamble': ['us.pg.com', 'www.pg.com'], 'hershey': ['www.hersheys.com', 'hersheyland.com'],
       'darden': ['www.darden.com', 'olivegarden.com'], 'unitedhealth': ['www.uhc.com', 'unitedhealthgroup.com'], 'cisco': ['www.cisco.com'], 'qualcomm': ['www.qualcomm.com'], 'monster-energy': ['www.monsterenergy.com'],
       'expedia': ['www.expedia.com'], 'marriott': ['www.marriott.com'], 'dollar-general': ['www.dollargeneral.com'], 'dollar-tree': ['www.dollartree.com']}
for slug, t, legal, short, dom in COMPANIES:
    if slug in have: continue
    for d in ALT.get(slug, ['www.' + dom]):
        got = None
        for size in (128, 64):
            try: b = urllib.request.urlopen(urllib.request.Request(f'https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://{d}&size={size}', headers={'User-Agent': 'bs-logos/1.0'}), timeout=20).read()
            except Exception: continue
            if b[:4] == b'\x89PNG' and struct.unpack('>II', b[16:24])[0] >= 48: got = b; break
        if got: open(os.path.join(OUT, slug + '.png'), 'wb').write(got); have.add(slug); print(slug, 'ok via', d); break
    else: print(slug, 'none')
json.dump(sorted(have), open(os.path.join(OUT, 'have.json'), 'w'), indent=0); print(len(have), 'icons')

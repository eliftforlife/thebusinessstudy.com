# 11-08: print the employee-count sentences from each company's annual report so they can be checked by hand (-> EMPLOYEES in data/curated.py).
import os, re, json, glob, sys, html
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(D, 'companies.json'), encoding='utf-8'))
only = sys.argv[1:]
for slug, c in d.items():
    if only and slug not in only: continue
    f = os.path.join(D, 'sec', 'raw', f"{c['filing']['accn']}_doc.htm")
    if not os.path.exists(f): print(slug, 'NO DOC'); continue
    h = open(f, encoding='utf-8', errors='replace').read()
    h = re.sub(r'(?is)<(script|style|ix:header)[^>]*>.*?</\1>', ' ', h)
    t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h))).replace('’', "'")
    sents = re.split(r'(?<=[.;])\s+(?=[A-Z])', t)
    out = []
    for s in sents:
        if len(s) > 420: continue
        if re.search(r'\b(employ|employees|team members|associates|colleagues|workforce|headcount|people|crew members|full-time)', s, re.I) and re.search(r'\b\d{1,3}(?:,\d{3})+\b|\b\d{4,6}\b(?! *(?:shares|\$))', s) \
           and re.search(r'as of|at the end|at (?:december|january|february|march|june|september|may|august|october|november)|approximately|employed|we had|we have', s, re.I) \
           and not re.search(r'\$|million|billion|percent of revenue|square feet|shares|stores|restaurants|aircraft|vehicles|units|members(?! of our)', s, re.I):
            out.append(s.strip())
    print(f'## {slug}')
    for s in out[:3]: print('  -', s[:330])

# Builds thebusinessstudy.com into docs/ (GitHub Pages serves main /docs).   usage: py build.py
# v2 (11-08, Elijah: "the full treatment ... its own unique site"): the site is now about how companies make money, from their own annual
# reports. Pages: home, /companies/ + one page per company, /compare/ tool + match-up pages, rankings (largest, most profitable, per
# employee), /how-companies-make-money/ (business models), industry pages, /business-statistics/, the higher-or-lower /game/, the
# creator data studies (content.py), /about/, /vote/, 404, sitemap, robots, llms.txt, IndexNow key, data JSON for the tools.
# Rules: every number comes from a 10-K / 20-F on SEC EDGAR (data/sec_pull.py, data/frames_pull.py); nothing is estimated; pages say
# which filing. Look: assets/bs.css (Apple-calm white, blue #2456e8 as a ~10% accent, the "$100 bar" as the signature graphic).
import os, re, json, shutil, html, hashlib, datetime, sys
sys.path.insert(0, 'data')
from content import STUDIES, HERO, VIDEOS as STUDY_VIDEOS, RELATED, SITE
from model import build_model
from companies_list import COMPANIES

OUT = 'docs'; TODAY = datetime.date.today().isoformat(); V = datetime.datetime.now().strftime('%Y%m%d%H%M')
E = lambda s: html.escape(str(s), quote=True)
URL = 'https://thebusinessstudy.com'; YT = 'https://www.youtube.com/@thebusinessstudy'; SUB = YT + '?sub_confirmation=1'
SOCIALS = [('YouTube', YT), ('TikTok', 'https://www.tiktok.com/@thebusinessstudy')]
INDEXNOW_KEY = '6b1f3c2e9a8d4e7f9c0b5a1d2e3f4a5b'
_AN = json.load(open('data/analytics.json')) if os.path.exists('data/analytics.json') else {}   # {"cf": Cloudflare Web Analytics token (public), "ga": GA4 id}
CF_TOKEN, GA_ID = _AN.get('cf'), _AN.get('ga')
M = build_model()
for _slug, _t, _legal, _short, _dom in COMPANIES:
    if _slug in M: M[_slug]['legal'] = _legal
LOGOS = set(json.load(open('assets/logos/have.json'))) if os.path.exists('assets/logos/have.json') else set()
RANK = json.load(open('data/rank_2025.json', encoding='utf-8'))
DATES = json.load(open('data/page_dates.json', encoding='utf-8')) if os.path.exists('data/page_dates.json') else {}
PAGES = []          # (path, title) for sitemap + llms.txt

# ---------- formatting ----------
def B(v, short=False):
    if v is None: return '—'
    a = abs(v); s = '-' if v < 0 else ''
    if a >= 1e12: t = f'{a / 1e12:.2f} trillion'
    elif a >= 1e11: t = f'{a / 1e9:.0f} billion'
    elif a >= 1e9: t = f'{a / 1e9:.1f} billion'
    elif a >= 1e6: t = f'{a / 1e6:,.0f} million'
    else: t = f'{a:,.0f}'
    if short: t = t.replace(' trillion', 'T').replace(' billion', 'B').replace(' million', 'M')
    return f'{s}${t}'
def K(v): return '—' if v is None else (f'${v / 1e6:.2f} million' if abs(v) >= 1e6 else f'${v:,.0f}')
def P(x, d=0): return f'{x * 100:.{d}f}%'
def D(v): return f"{'-' if v < 0 else ''}${abs(v):.2f}"
def per100(m): return None if m['net_income'] is None else m['net_income'] / m['revenue'] * 100
def yr(end): d = datetime.date.fromisoformat(end); return d.year if d.month >= 6 else d.year - 1
def period(m):
    return f"{m['end'][:4]}" if m['end'][5:] in ('12-31',) else f"the year ended {m['end_text']}"
def name(m): return m['name']
def rw(m): return 'net revenue' if m['cur'].get('bank') else 'revenue'
def poss(n): return n + ("'" if n.endswith('s') else "'s")

# ---------- shell ----------
GH_CHEV = '<svg viewBox="0 0 8 8" aria-hidden="true"><path d="M2.5 1 5.5 4 2.5 7" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
GH_DOWN = '<svg viewBox="0 0 8 8" aria-hidden="true"><path d="M1 2.75 4 5.75 7 2.75" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
NAV_TOP = [('/companies/', 'Companies'), ('/compare/', 'Compare'), ('/largest-companies/', 'Rankings'), ('/how-companies-make-money/', 'Business models'), ('/game/', 'Game'), ('/studies/', 'Studies')]
NAV_MORE = [('/most-profitable-companies/', 'Most profitable'), ('/revenue-per-employee/', 'Revenue per employee'), ('/industries/', 'Industries'),
            ('/business-statistics/', 'Statistics'), ('/vote/', 'Vote'), ('/about/', 'About')]
def header(path):
    cur = lambda u: ' aria-current="page"' if path.startswith(u) else ''
    top = ''.join(f'<a href="{u}"{cur(u)}>{t}</a>' for u, t in NAV_TOP)
    sheet = ''.join(f'<a class="gh-x" href="{u}"{cur(u)}>{t}</a>' for u, t in NAV_TOP) + ''.join(f'<a href="{u}"{cur(u)}>{t}</a>' for u, t in NAV_MORE)
    return (f'<header class="gh wide" data-tuck style="--gh-cta: #2456e8;"><div class="gh-in"><a class="gh-brand" href="/"><img src="/assets/logo-128.png" alt="" width="24" height="24">The Business Study</a>'
            f'<nav class="gh-links" aria-label="Main">{top}<button class="gh-more" type="button" aria-expanded="false" aria-controls="gh-sheet">More{GH_DOWN}</button></nav>'
            f'<div class="gh-r"><a class="gh-cta" href="{SUB}" rel="noopener">Subscribe{GH_CHEV}</a>'
            f'<button class="gh-menu" type="button" aria-label="Menu" aria-expanded="false" aria-controls="gh-sheet"><i></i><i></i></button></div></div>'
            f'<nav class="gh-sheet" id="gh-sheet" aria-label="All pages"><div class="gh-sheet-in"><p>More from The Business Study</p>{sheet}</div></nav>'
            f'<div class="gh-progress"><i></i></div></header>')

def footer():
    top = sorted((m for m in M.values()), key=lambda m: -m['revenue'])[:8]
    cos = ''.join(f'<a href="/companies/{m["slug"]}/">How {E(m["name"])} makes money</a>' for m in top)
    tools = ''.join(f'<a href="{u}">{t}</a>' for u, t in [('/compare/', 'Compare two companies'), ('/game/', 'Higher or lower game'), ('/largest-companies/', 'Largest companies'), ('/most-profitable-companies/', 'Most profitable'), ('/revenue-per-employee/', 'Revenue per employee'), ('/business-statistics/', 'Statistics')])
    more = ''.join(f'<a href="{u}">{t}</a>' for u, t in [('/how-companies-make-money/', 'Business models'), ('/industries/', 'Industries'), ('/studies/', 'Creator studies'), ('/about/', 'About and method'), ('/privacy/', 'Privacy'), ('/vote/', 'Vote'), (YT, 'YouTube')])
    return f'''<footer class="foot"><div class="wide"><div class="cols4">
<div><a class="brand" href="/"><img src="/assets/logo-128.png" alt="" width="28" height="28">The Business Study</a><p>How companies make money, from their own annual reports. Free, with every number sourced.</p>
<p><a class="btn sm blue" href="{SUB}" rel="noopener">Subscribe on YouTube</a></p></div>
<nav><b>Companies</b>{cos}<a href="/companies/">All companies</a></nav><nav><b>Tools</b>{tools}</nav><nav><b>More</b>{more}</nav></div>
<p class="fine">© {TODAY[:4]} The Business Study. Numbers come from each company's annual report (Form 10-K, or 20-F for a few foreign companies) on the SEC's EDGAR system. Company names and logos belong to their owners and are used only to identify each company; no company made, sponsors or endorses this site. Not financial advice.</p></div></footer>'''

def csp(extra_connect='', extra_frame='', extra_script=''):
    s = "default-src 'self'; img-src 'self' data: https://i.ytimg.com https://*.google-analytics.com https://*.googletagmanager.com; style-src 'self' 'unsafe-inline'; font-src 'self'; base-uri 'self'; form-action 'self'; object-src 'none'; "
    s += f"script-src 'self' https://static.cloudflareinsights.com https://www.googletagmanager.com {extra_script}; ".replace('  ', ' ')
    s += f"connect-src 'self' https://cloudflareinsights.com https://*.google-analytics.com https://*.analytics.google.com https://*.googletagmanager.com {extra_connect}; ".replace('  ', ' ')
    s += f"frame-src https://www.youtube-nocookie.com {extra_frame}".strip()
    return s

def analytics():
    out = ''
    if CF_TOKEN: out += f'<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon=\'{{"token": "{CF_TOKEN}"}}\'></script>'
    if GA_ID: out += f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script><script src="/assets/ga.js?v=1"></script>'
    return out

def page(path, title, desc, body, ld=None, kind='website', policy=None, scripts='', img=None, noindex=False):
    assert len(title) <= 70, (path, len(title), title)
    if len(desc) > 160: desc = desc[:157].rsplit(' ', 1)[0].rstrip(',;:') + '…'
    url = URL + path
    h = hashlib.md5(re.sub(r'\s+', ' ', body).encode()).hexdigest()
    old = DATES.get(path)
    date = old[1] if old and old[0] == h else TODAY; DATES[path] = [h, date]
    lds = list(ld or [])
    lds.append({'@context': 'https://schema.org', '@type': 'WebPage', 'name': title, 'url': url, 'description': desc, 'dateModified': date, 'inLanguage': 'en',
                'isPartOf': {'@type': 'WebSite', 'name': 'The Business Study', 'url': URL + '/'}})
    ldh = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in lds)
    doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{policy or csp()}">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="{'noindex, follow' if noindex else 'index, follow, max-image-preview:large'}">
<meta name="theme-color" content="#ffffff">
<meta property="og:type" content="{kind}"><meta property="og:site_name" content="The Business Study"><meta property="og:url" content="{url}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:image" content="{URL}{img or '/assets/og.png'}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/icon.png">
<link rel="stylesheet" href="/assets/gh.css?v=2"><link rel="stylesheet" href="/assets/bs.css?v={V}">
<script src="/assets/js.js?v=1"></script>
<script src="/assets/gh.js?v=1" defer></script><script src="/assets/bs.js?v={V}" defer></script>{scripts}
{analytics()}
{ldh}
</head>
<body{' class="reading"' if '/companies/' in path or '/studies/' in path else ''}>
{header(path)}
{body}
{footer()}
</body>
</html>
'''
    f = os.path.join(OUT, path.strip('/'), 'index.html') if path.endswith('/') else os.path.join(OUT, path.strip('/'))
    os.makedirs(os.path.dirname(f) or '.', exist_ok=True); open(f, 'w', encoding='utf-8').write(doc)
    if not noindex and path != '/404.html': PAGES.append((path, title, date))

def crumbs(*items):
    parts = ['<a href="/">Home</a>'] + [f'<a href="{u}">{E(t)}</a>' if u else E(t) for t, u in items]
    return '<p class="crumbs">' + '<span>/</span>'.join(parts) + '</p>'
def bc_ld(*items):
    lst = [('Home', '/')] + list(items)
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': t, 'item': URL + u} for i, (t, u) in enumerate(lst)]}
def faq_ld(qas): return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub('<[^>]+>', '', a)}} for q, a in qas]}

# ---------- components ----------
def logo(slug, sm=False):
    m = M.get(slug); n = m['name'] if m else slug
    if slug in LOGOS: return f'<span class="logo{" sm" if sm else ""}"><img src="/assets/logos/{slug}.png" alt="{E(n)} logo" width="36" height="36"></span>'
    ini = ''.join(w[0] for w in re.findall(r"[A-Za-z0-9]+", n)[:2]).upper()
    return f'<span class="logo mono{" sm" if sm else ""}" aria-hidden="true">{E(ini)}</span>'

def bar100(kept, label=''):
    loss = kept < 0; w = min(100, abs(kept))
    return (f'<div class="bar100{" loss" if loss else ""}{" thin" if w < 16 else ""}" style="--w:{w:.2f}%" role="img" aria-label="{E(label)}"><i></i>'
            f'<em><span>{"Lost" if loss else "Kept"} ${abs(kept):.2f}</span><span>{"" if loss else f"Everything else ${100 - kept:.2f}"}</span></em></div>'
            f'<div class="legend100"><span>$0</span><span>$100 in sales</span></div>')

def bars(rows, big=False, total=None, money=True, link=None):
    """rows = (label, value, note[, hi]) -> label | bar | value (+ share of total)."""
    if not rows: return ''
    top = max(abs(r[1]) for r in rows) or 1
    out = [f'<div class="bars{" big" if big else ""}">']
    for i, r in enumerate(rows):
        lab, v, note = r[0], r[1], (r[2] if len(r) > 2 else '')
        hi = r[3] if len(r) > 3 else (i == 0)
        share = f'<small>{v / total * 100:.0f}% of total</small>' if total and v > 0 else ''
        val = (B(v, True) if money else v) if not callable(money) else money(v)
        lab_h = f'<a href="{link(r)}">{E(lab)}</a>' if link else E(lab)
        out.append(f'<div class="r{" hi" if hi else ""}{" neg" if v < 0 else ""}"><span class="l">{lab_h}{f"<small>{E(note)}</small>" if note else ""}</span>'
                   f'<span class="b"><i style="--w:{max(1.2, abs(v) / top * 100):.1f}%"></i></span><span class="v">{val}{share}</span></div>')
    return ''.join(out) + '</div>'

def cols(m, n=6):
    rev = dict(m['rev_years'][-n:]); ni = dict(m['ni_years'])
    ends = sorted(rev); top = max(rev.values()) or 1
    cs = []
    for i, e in enumerate(ends):
        r = rev[e]; p = ni.get(e); h = r / top * 100
        ph = f'<i class="p{" neg" if p is not None and p < 0 else ""}" style="--h:{max(.5, p / top * 100) if (p or 0) > 0 else .5:.1f}%"></i>' if p is not None else ''
        cs.append(f'<div class="c{" last" if i == len(ends) - 1 else ""}" style="--h:{h:.1f}%"><b>{B(r, True)}</b><div class="pair"><i style="--h:{h:.1f}%"></i>{ph}</div></div>')
    xs = ''.join(f'<span>{yr(e)}<small class="{"neg" if (ni.get(e) or 0) < 0 else "blue"}">{B(ni.get(e), True) if ni.get(e) is not None else ""}</small></span>' for e in ends)
    return f'<div class="cols" role="img" aria-label="{E(m["name"])} revenue and profit by year">{"".join(cs)}</div><div class="cols-x">{xs}</div><div class="key"><span><i></i>Revenue (on top of each bar)</span><span><i class="p"></i>Net profit (under each year)</span></div>'

def yt(vid, title, land=False):
    return f'<div class="yt{" land" if land else ""}" data-id="{vid}" data-title="{E(title)}"><img src="https://i.ytimg.com/vi/{vid}/{"hqdefault" if land else "oar2"}.jpg" alt="{E(title)}" loading="lazy"><button aria-label="Play: {E(title)}"></button></div>'

def qa_block(qas):
    return '<div class="qa">' + ''.join(f'<div class="reveal"><h3>{E(q)}</h3><p>{a}</p></div>' for q, a in qas) + '</div>'

def source(m):
    return (f'<div class="source"><p><b>Source:</b> {E(m["legal"])}, annual report on <a href="{m["url"]}" rel="nofollow noopener">Form {m["form"]}</a> for the fiscal year ended {m["end_text"]}, filed with the SEC on {datetime.date.fromisoformat(m["filed"]).strftime("%B %d, %Y").replace(" 0", " ")}.</p>'
            f'<p>Revenue, profit and the breakdowns are the numbers the company reported in that filing (its XBRL data). Profit means net income; "operating profit" means operating income. Nothing on this page is estimated.</p></div>')

# ---------- data for the tools ----------
VIDEOS = json.load(open('data/videos.json', encoding='utf-8')) if os.path.exists('data/videos.json') else {}
COMPARES = [  # (url slug, a, b, short phrase people search)
    ('coca-cola-vs-pepsico', 'coca-cola', 'pepsico', 'Coke vs Pepsi'), ('nvidia-vs-amd', 'nvidia', 'amd', 'Nvidia vs AMD'), ('uber-vs-lyft', 'uber', 'lyft', 'Uber vs Lyft'),
    ('visa-vs-mastercard', 'visa', 'mastercard', 'Visa vs Mastercard'), ('home-depot-vs-lowes', 'home-depot', 'lowes', "Home Depot vs Lowe's"), ('amazon-vs-walmart', 'amazon', 'walmart', 'Amazon vs Walmart'),
    ('mcdonalds-vs-burger-king', 'mcdonalds', 'restaurant-brands', "McDonald's vs Burger King"), ('netflix-vs-disney', 'netflix', 'disney', 'Netflix vs Disney'),
    ('american-express-vs-visa', 'american-express', 'visa', 'Amex vs Visa'), ('nvidia-vs-intel', 'nvidia', 'intel', 'Nvidia vs Intel'), ('apple-vs-microsoft', 'apple', 'microsoft', 'Apple vs Microsoft'),
    ('google-vs-meta', 'google', 'meta', 'Google vs Meta'), ('walmart-vs-target', 'walmart', 'target', 'Walmart vs Target'), ('fedex-vs-ups', 'fedex', 'ups', 'FedEx vs UPS'),
    ('verizon-vs-att', 'verizon', 'att', 'Verizon vs AT&T'), ('t-mobile-vs-verizon', 't-mobile', 'verizon', 'T-Mobile vs Verizon'), ('delta-vs-united-airlines', 'delta', 'united-airlines', 'Delta vs United'),
    ('exxon-vs-chevron', 'exxon', 'chevron', 'Exxon vs Chevron'), ('marriott-vs-hilton', 'marriott', 'hilton', 'Marriott vs Hilton'), ('booking-vs-expedia', 'booking', 'expedia', 'Booking vs Expedia'),
    ('dollar-general-vs-dollar-tree', 'dollar-general', 'dollar-tree', 'Dollar General vs Dollar Tree'), ('nike-vs-lululemon', 'nike', 'lululemon', 'Nike vs Lululemon'),
    ('uber-vs-doordash', 'uber', 'doordash', 'Uber vs DoorDash'), ('jpmorgan-chase-vs-bank-of-america', 'jpmorgan-chase', 'bank-of-america', 'Chase vs Bank of America'),
    ('amd-vs-intel', 'amd', 'intel', 'AMD vs Intel'), ('apple-vs-amazon', 'apple', 'amazon', 'Apple vs Amazon'), ('apple-vs-google', 'apple', 'google', 'Apple vs Google'),
    ('mcdonalds-vs-starbucks', 'mcdonalds', 'starbucks', "McDonald's vs Starbucks"), ('ford-vs-gm', 'ford', 'gm', 'Ford vs GM'), ('costco-vs-walmart', 'costco', 'walmart', 'Costco vs Walmart'),
    ('tesla-vs-ford', 'tesla', 'ford', 'Tesla vs Ford'), ('spotify-vs-netflix', 'spotify', 'netflix', 'Spotify vs Netflix')]
COMPARES = [c for c in COMPARES if c[1] in M and c[2] in M]

def growth(m):
    ys = m['rev_years'][-6:]
    return (ys[-1][1] / ys[0][1] - 1) * 100 if len(ys) >= 2 and ys[0][1] > 0 else None

def co_json():
    cp = {}
    for s, a, b, _ in COMPARES: cp.setdefault(a, {})[b] = s; cp.setdefault(b, {})[a] = s
    out = []
    for m in sorted(M.values(), key=lambda m: -m['revenue']):
        if m['net_income'] is None: continue
        out.append({'s': m['slug'], 'n': m['name'], 'a': m['legal'] + ' ' + m['ticker'], 'r': round(m['revenue']), 'p': round(m['net_income']), 'e': m['employees'][0] if m['employees'] else None,
                    'g': round(growth(m), 1) if growth(m) is not None else None, 'y': f"FY ended {m['end_text']}", 'cp': cp.get(m['slug'], {})})
    os.makedirs(os.path.join(OUT, 'assets', 'data'), exist_ok=True)
    json.dump(out, open(os.path.join(OUT, 'assets', 'data', 'co.json'), 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
    return out

# ---------- company page ----------
def answer(m):
    n = m['name']; k = per100(m); ni = m['net_income']; st = m['streams']; sp = m['seg_profit']; op = m['operating_income']
    s = [f"{n} brought in <b>{B(m['revenue'])}</b> in {rw(m)} in {period(m)}"]
    if ni is not None: s[0] += f" and {'kept' if ni >= 0 else 'lost'} <b>{B(abs(ni))}</b> as {'profit' if ni >= 0 else 'a net loss'}: {'$' + format(abs(k), '.2f')} of every $100."
    else: s[0] += '.'
    tot = sum(v for _, v, _ in st)
    if st:
        lab, v, _ = st[0]; s.append(f"Its biggest source of money was <b>{E(lab)}</b>, at {B(v)} ({v / max(tot, m['revenue']) * 100:.0f}% of the total).")
    if sp:
        pos = [r for r in sp if r[1] > 0]
        if pos and (not st or pos[0][0] != st[0][0]) and op and op > 0 and pos[0][1] <= op * 1.02:
            s.append(f"But <b>{E(pos[0][0])}</b> made the most operating profit: {B(pos[0][1])}, {pos[0][1] / op * 100:.0f}% of {poss(n)} {B(op)} total.")
        neg = [r for r in sp if r[1] < 0]
        if neg: s.append(f"{E(neg[0][0])} lost {B(-neg[0][1])}.")
    return ' '.join(s)

def quick(m):
    n = m['name']; qas = []; st = m['streams']; ni = m['net_income']; rev = m['revenue']
    qas.append((f'How does {n} make money?', E(m['cur'].get('what', '')) + (f" The biggest line in its latest 10-K is {E(st[0][0])} ({B(st[0][1])})." if st else '')))
    prev = dict(m['rev_years']).get(sorted(dict(m['rev_years']))[-2]) if len(m['rev_years']) >= 2 else None
    chg = f" That's {'up' if rev >= prev else 'down'} {abs(rev / prev - 1) * 100:.0f}% from the year before." if prev else ''
    qas.append((f'How much money does {n} make a year?', f"{B(rev)} in {rw(m)} in {period(m)}, and {B(ni) if ni is not None and ni >= 0 else B(abs(ni or 0))} in {'net profit' if (ni or 0) >= 0 else 'net loss'}.{chg}"))
    if ni is not None:
        losses = [yr(e) for e, v in m['ni_years'][-6:] if v < 0]
        lost = f" It lost money in {', '.join(map(str, losses))}." if losses and ni >= 0 else ''
        qas.append((f'Is {n} profitable?', (f"Yes. {n} made {B(ni)} in net profit in {period(m)}, which is ${per100(m):.2f} of every $100 it took in." if ni >= 0 else f"No. {n} lost {B(-ni)} in {period(m)}.") + lost))
    if m['employees']:
        c, asof, what = m['employees']
        qas.append((f'How many employees does {n} have?', f"About {c:,} {E(what)} as of {E(asof)}. That works out to {K(rev / c)} in {rw(m)} per employee."))
    if m['seg_profit']:
        pos = [r for r in m['seg_profit'] if r[1] > 0]
        if pos: qas.append((f'Which part of {n} makes the most profit?', f"{E(pos[0][0])}, with {B(pos[0][1])} in operating profit in {period(m)}."))
    g = growth(m)
    if g is not None:
        y0 = yr(m['rev_years'][-6:][0][0]); qas.append((f'Is {n} growing?', f"{'Yes' if g > 0 else 'No'}. Revenue went from {B(m['rev_years'][-6:][0][1])} in {y0} to {B(rev)} in {yr(m['end'])}, {'up' if g > 0 else 'down'} {abs(g):.0f}%."))
    return qas

def company_page(m):
    s = m['slug']; n = m['name']; path = f'/companies/{s}/'; k = per100(m); st = m['streams']; tot = sum(v for _, v, _ in st)
    y = yr(m['end'])
    title = f'How {n} Makes Money ({y} Revenue Breakdown)'
    if len(title) > 62: title = f'How {n} Makes Money ({y})'
    desc = re.sub('<[^>]+>', '', answer(m))
    if len(desc) > 160: desc = desc[:157].rsplit(' ', 1)[0] + '…'
    tiles = [('Revenue' if rw(m) == 'revenue' else 'Net revenue', B(m['revenue']), period(m).replace('the year ended ', 'FY ended '), True)]
    if m['operating_income'] is not None: tiles.append(('Operating profit', B(m['operating_income']), f"{m['operating_income'] / m['revenue'] * 100:.1f}% of revenue", False))
    if m['net_income'] is not None: tiles.append(('Net profit', B(m['net_income']), f"${k:.2f} of every $100", False))
    if m['employees']: tiles.append(('Employees', f"{m['employees'][0]:,}", f"{K(m['revenue'] / m['employees'][0])} revenue each", False))
    elif m['rnd']: tiles.append(('Research and development', B(m['rnd']), f"{m['rnd'] / m['revenue'] * 100:.1f}% of revenue", False))
    tile_h = ''.join(f'<div class="tile{" hi" if hi else ""}"><span>{t}</span><b>{v}</b><small>{E(sub)}</small></div>' for t, v, sub, hi in tiles)
    over = tot > m['revenue'] * 1.02
    streams_h = ''
    if st:
        note = ''
        if m.get('gross'): note = f'<p class="note">These are {poss(n)} fees before {B(-m["gross"])} in incentives it pays back to banks and partners, which is why they add up to more than its {B(m["revenue"])} in net revenue.</p>'
        elif over: note = f'<p class="note">These lines include sales between {poss(n)} own businesses, so they add up to a bit more than its {B(m["revenue"])} total.</p>'
        elif tot < m['revenue'] * .97: note = f'<p class="note">The lines shown add up to {B(tot)} of the {B(m["revenue"])} total; the rest is smaller items and adjustments the 10-K does not split out.</p>'
        streams_h = f'''<section class="sec"><div class="wrap"><h2 class="reveal">Where {poss(n)} money comes from. <span>{len(st)} lines in its 10&#8209;K.</span></h2>
{bars([(l, v, nt) for l, v, nt in st], big=True, total=max(tot, m['revenue']) if not m.get('gross') and not over else tot)}{note}</div></section>'''
    prof_h = ''
    if m['seg_profit']:
        sp = m['seg_profit']; neg = any(v < 0 for _, v, _ in sp)
        lead = max(sp, key=lambda r: r[1])
        extra = ''
        if st and lead[0] != st[0][0]:
            rshare = next((v for l, v, _ in st if l == lead[0]), None)
            if rshare and m['operating_income'] and m['operating_income'] > 0 and lead[1] <= m['operating_income']:
                extra = f'<div class="callout reveal"><b>{E(lead[0])}</b> was {rshare / max(tot, m["revenue"]) * 100:.0f}% of {poss(n)} revenue but {lead[1] / m["operating_income"] * 100:.0f}% of its operating profit.</div>'
        prof_h = f'''<section class="sec soft"><div class="wrap"><h2 class="reveal">Where the profit comes from. <span>{'Not every part makes money.' if neg else 'Operating profit by segment.'}</span></h2>
{bars([(l, v, '', l == lead[0]) for l, v, _ in sp], big=True)}{extra}<p class="note">Operating profit (operating income) by the business segments {n} reports, before corporate costs not assigned to a segment.</p></div></section>'''
    mg = ''
    if m['margins']:
        mg_rows = ''.join(f'<div class="tile{" hi" if i == 0 else ""}"><span>{E(lab)}</span><b>{(r - c) / r * 100:.1f}%</b><small>kept after the cost of sales on {B(r)}</small></div>' for i, (lab, r, c, _) in enumerate(sorted(m['margins'], key=lambda x: -x[3])))
        mg = f'<section class="sec tight"><div class="wrap"><h2 class="reveal">Why the smaller line matters. <span>Gross margin by type.</span></h2><div class="tiles" style="grid-template-columns:repeat(2,1fr)">{mg_rows}</div></div></section>'
    hist = f'''<section class="sec"><div class="wrap"><h2 class="reveal">{len(m["rev_years"][-6:])} years of {poss(n)} revenue and profit.</h2>{cols(m)}
<p class="note">Fiscal years as {n} reports them; the latest ended {m["end_text"]}. Profit is net income.</p></div></section>''' if len(m['rev_years']) >= 3 else ''
    vid = VIDEOS.get(s)
    vid_h = f'''<section class="sec soft"><div class="wrap watch">{yt(vid[0], vid[1])}<div><p class="lbl">Watch</p><h2>{E(vid[1])}</h2><p class="lead">The Business Study breaks down {poss(n)} 10-K in under a minute.</p>
<p><a class="btn ghost" href="{SUB}" rel="noopener">Subscribe for more</a></p></div></div></section>''' if vid else ''
    vs = [c for c in COMPARES if s in (c[1], c[2])]
    vs_h = ''.join(f'<a class="card" href="/compare/{c[0]}/"><p class="lbl">Compare</p><h3>{E(M[c[1]]["name"])} vs {E(M[c[2]]["name"])}</h3><p>Revenue, profit, margins and employees, round by round.</p><span class="go">See who wins</span></a>' for c in vs[:3])
    peers = sorted((x for x in M.values() if x['slug'] != s and x['sic'] == m['sic']), key=lambda x: -x['revenue'])[:3]
    if len(vs) < 3: vs_h += ''.join(f'<a class="card" href="/compare/?a={s}&amp;b={p["slug"]}"><p class="lbl">Compare</p><h3>{E(n)} vs {E(p["name"])}</h3><p>Pick any two companies and see who makes more.</p><span class="go">Compare</span></a>' for p in peers[:3 - len(vs)])
    qas = quick(m)
    kept_h = ''
    if k is not None:
        kept_h = f'<div class="k100 reveal" style="margin-top:28px"><p class="say" style="margin-top:0">Out of every $100 {n} took in, it {"kept" if k >= 0 else "lost"}</p><div class="big">${abs(k):.2f}<small>{"profit" if k >= 0 else "lost"}</small></div>{bar100(k, f"{n} kept ${k:.2f} of every $100")}</div>'
    body = f'''<main>
<section class="phead"><div class="wrap">{crumbs(('Companies', '/companies/'), (n, ''))}
<div class="cohead">{logo(s)}<span class="tick">{E(m["legal"])} · {E(m["ticker"])}</span></div>
<h1>How {E(n)} makes money</h1>
<div class="answer" style="margin-top:26px"><p>{answer(m)}</p></div>
<p class="updated">From {poss(n)} <a href="{m["url"]}" rel="nofollow noopener">Form {m["form"]}</a> for the year ended {m["end_text"]}. Page updated {{DATE}}.</p>
<div class="tiles">{tile_h}</div>{kept_h}</div></section>
{streams_h}{prof_h}{mg}{hist}{vid_h}
<section class="sec{"" if vid_h else " soft"}"><div class="wrap"><h2 class="reveal">Quick answers about {E(n)}.</h2>{qa_block(qas)}</div></section>
<section class="sec tight"><div class="wrap"><h2 class="reveal">Compare {E(n)}.</h2><div class="cards">{vs_h}</div>{source(m)}</div></section>
</main>'''
    ld = [bc_ld(('Companies', '/companies/'), (n, path)), faq_ld(qas),
          {'@context': 'https://schema.org', '@type': 'Article', 'headline': f'How {n} makes money', 'description': desc, 'author': {'@type': 'Organization', 'name': 'The Business Study', 'url': URL + '/about/'},
           'publisher': {'@type': 'Organization', 'name': 'The Business Study', 'logo': {'@type': 'ImageObject', 'url': URL + '/assets/icon.png'}}, 'mainEntityOfPage': URL + path,
           'about': {'@type': 'Corporation', 'name': m['legal'], 'tickerSymbol': m['ticker'], 'url': 'https://' + m['domain']}, 'isBasedOn': m['url']}]
    page(path, title, desc, body.replace('{DATE}', '{DATE}'), ld, 'article')
    fix_date(path)

def fix_date(path):
    f = os.path.join(OUT, path.strip('/'), 'index.html'); s = open(f, encoding='utf-8').read()
    d = datetime.date.fromisoformat(DATES[path][1]).strftime('%B %d, %Y').replace(' 0', ' ')
    open(f, 'w', encoding='utf-8').write(s.replace('{DATE}', d))

# ---------- compare pages ----------
ROUNDS = [('Revenue', lambda m: m['revenue'], B, 'Money coming in'), ('Net profit', lambda m: m['net_income'], B, 'After every cost and tax'),
          ('Kept per $100 of sales', per100, lambda v: f'${v:.2f}', 'Profit margin'), ('Employees', lambda m: m['employees'][0] if m['employees'] else None, lambda v: f'{v:,}', 'As each 10-K states it'),
          ('Revenue per employee', lambda m: m['revenue'] / m['employees'][0] if m['employees'] else None, K, 'Revenue ÷ employees'),
          ('Growth over 5 years', growth, lambda v: f'{"+" if v > 0 else ""}{v:.0f}%', 'Revenue, first to latest year shown')]
def duel(a, b, f, fm, word='Wins'):
    x, y = f(a), f(b)
    if x is None or y is None: return None, ''
    top = max(abs(x), abs(y)) or 1; wa = x >= y
    side = lambda m, v, w: f'<div class="side{" win" if w else ""}{" neg" if v < 0 else ""}"><div class="name">{E(m["name"])}{f"<em>{word}</em>" if w else ""}</div><div class="num">{fm(v)}</div><div class="b"><i style="--w:{max(1, abs(v) / top * 100):.1f}%"></i></div></div>'
    return (a if wa else b), f'<div class="duel">{side(a, x, wa)}{side(b, y, not wa)}</div>'

def compare_page(slug, sa, sb, phrase):
    a, b = M[sa], M[sb]; path = f'/compare/{slug}/'; na, nb = a['name'], b['name']
    wins = {sa: 0, sb: 0}; rounds_h = []; facts = []
    for t, f, fm, sub in ROUNDS:
        counts = t != 'Employees'
        w, h = duel(a, b, f, fm, 'Wins' if counts else 'More')
        if not w: continue
        if counts: wins[w['slug']] += 1
        lo = b if w is a else a
        rounds_h.append(f'<div class="round reveal"><h3>{t} <small>{sub}</small></h3>{h}</div>')
        facts.append((t, w, lo, fm(f(w)), fm(f(lo))))
    lead = a if wins[sa] >= wins[sb] else b
    rev_w = a if a['revenue'] >= b['revenue'] else b; rev_l = b if rev_w is a else a
    k_w = a if (per100(a) or -1e9) >= (per100(b) or -1e9) else b
    ans = (f"{rev_w['name']} is bigger: {B(rev_w['revenue'])} in {rw(rev_w)} against {B(rev_l['revenue'])} for {rev_l['name']}, about {rev_w['revenue'] / rev_l['revenue']:.1f} times as much. "
           f"{'It also' if k_w is rev_w else 'But ' + k_w['name']} keeps more of each sale: ${per100(k_w):.2f} of every $100 versus ${per100(b if k_w is a else a):.2f}. "
           f"Across {sum(wins.values())} rounds from their latest annual reports, {lead['name']} wins {max(wins.values())}.")
    def mini(m):
        st = m['streams']; tot = sum(v for _, v, _ in st)
        if not st: return f'<p class="note">{E(m["cur"].get("what", ""))} Its 10-K does not split revenue into separate lines.</p>'
        return bars([(l, v, '') for l, v, _ in st[:5]], total=max(tot, m['revenue']) if not m.get('gross') else tot)
    how = f'''<section class="sec soft"><div class="wrap"><h2 class="reveal">How each one makes its money.</h2><div class="cards two">
<div class="card"><div class="cohead">{logo(sa, True)}<b>{E(na)}</b></div><p>{E(a["cur"].get("what", ""))}</p>{mini(a)}<a class="go" href="/companies/{sa}/">How {E(na)} makes money</a></div>
<div class="card"><div class="cohead">{logo(sb, True)}<b>{E(nb)}</b></div><p>{E(b["cur"].get("what", ""))}</p>{mini(b)}<a class="go" href="/companies/{sb}/">How {E(nb)} makes money</a></div></div></div></section>'''
    qas = [(f'Who makes more money, {na} or {nb}?', f"{rev_w['name']}: {B(rev_w['revenue'])} in revenue against {B(rev_l['revenue'])}."),
           (f'Which is more profitable, {na} or {nb}?', f"{k_w['name']} keeps more of each dollar (${per100(k_w):.2f} of every $100). In total profit, {(a if (a['net_income'] or 0) >= (b['net_income'] or 0) else b)['name']} made more: {B(max(a['net_income'] or 0, b['net_income'] or 0))}.")]
    if a['employees'] and b['employees']:
        big = a if a['employees'][0] >= b['employees'][0] else b
        qas.append((f'Which has more employees, {na} or {nb}?', f"{big['name']}, with about {big['employees'][0]:,} against {(b if big is a else a)['employees'][0]:,}."))
    title = f'{phrase}: Who Makes More Money? ({max(yr(a["end"]), yr(b["end"]))} 10-Ks)'
    if len(title) > 64: title = f'{phrase}: Who Makes More Money?'
    desc = re.sub('<[^>]+>', '', ans)[:158].rsplit(' ', 1)[0] + '…' if len(ans) > 160 else ans
    body = f'''<main><section class="phead"><div class="wrap">{crumbs(('Compare', '/compare/'), (f'{na} vs {nb}', ''))}
<div class="cohead">{logo(sa)}{logo(sb)}</div><h1>{E(na)} vs {E(nb)}: who makes more money?</h1>
<div class="answer" style="margin-top:26px"><p>{ans}</p></div><p class="updated">From each company's latest Form 10-K: {E(na)} (year ended {a["end_text"]}) and {E(nb)} (year ended {b["end_text"]}). Page updated {{DATE}}.</p>
<div class="score"><div><b>{wins[sa]}</b><span>{E(na)}</span></div><i>–</i><div><b>{wins[sb]}</b><span>{E(nb)}</span></div></div></div></section>
<section class="sec tight"><div class="wrap">{"".join(rounds_h)}</div></section>{how}
<section class="sec"><div class="wrap"><h2 class="reveal">Quick answers.</h2>{qa_block(qas)}
<p style="margin-top:30px"><a class="btn ghost" href="/compare/?a={sa}&amp;b={sb}">Swap in another company</a></p>
<div class="source"><p><b>Sources:</b> <a href="{a["url"]}" rel="nofollow noopener">{E(a["legal"])} Form {a["form"]}</a> and <a href="{b["url"]}" rel="nofollow noopener">{E(b["legal"])} Form {b["form"]}</a> on SEC EDGAR. Fiscal years can end in different months, so each side uses its own latest year. Profit means net income.</p></div></div></section></main>'''
    page(path, title, desc, body, [bc_ld(('Compare', '/compare/'), (f'{na} vs {nb}', path)), faq_ld(qas)], 'article'); fix_date(path)

def sams_club_page():
    """Costco vs Sam's Club: Sam's Club is a segment of Walmart, so this uses Walmart's segment numbers against Costco's (operating profit only)."""
    w, c = M['walmart'], M['costco']; path = '/compare/costco-vs-sams-club/'
    from model import member_value, RAW
    sr, _ = member_value(RAW['walmart'], 'SamsClubUSMember'); so, _ = member_value(RAW['walmart'], 'SamsClubUSMember', 'seg_operating')
    if not sr or so is None: return
    cr, co = c['revenue'], c['operating_income']; mem, _ = member_value(RAW['costco'], 'MembershipMember')
    ans = (f"Costco is about {cr / sr:.1f} times the size of Sam's Club: {B(cr)} in sales against {B(sr)} for Sam's Club U.S. "
           f"Costco made {B(co)} in operating profit (${co / cr * 100:.2f} of every $100); Sam's Club made {B(so)} (${so / sr * 100:.2f} of every $100). "
           f"Costco's membership fees alone were {B(mem)}.")
    rows = [('Sales', cr, sr, B), ('Operating profit', co, so, B), ('Operating profit per $100 of sales', co / cr * 100, so / sr * 100, lambda v: f'${v:.2f}')]
    rh = ''
    for t, x, y, fm in rows:
        top = max(x, y); wa = x >= y
        rh += f'''<div class="round reveal"><h3>{t}</h3><div class="duel"><div class="side{" win" if wa else ""}"><div class="name">Costco{"<em>Wins</em>" if wa else ""}</div><div class="num">{fm(x)}</div><div class="b"><i style="--w:{x / top * 100:.1f}%"></i></div></div>
<div class="side{"" if wa else " win"}"><div class="name">Sam's Club (Walmart){"" if wa else "<em>Wins</em>"}</div><div class="num">{fm(y)}</div><div class="b"><i style="--w:{y / top * 100:.1f}%"></i></div></div></div></div>'''
    qas = [("Is Sam's Club bigger than Costco?", f"No. Costco's sales were {B(cr)}; Sam's Club U.S. had {B(sr)}."),
           ("Who owns Sam's Club?", "Walmart. Sam's Club is one of Walmart's three business segments, next to Walmart U.S. and Walmart International."),
           ("Who makes more profit per sale, Costco or Sam's Club?", f"Costco: ${co / cr * 100:.2f} of operating profit per $100 of sales, against ${so / sr * 100:.2f} at Sam's Club U.S.")]
    body = f'''<main><section class="phead"><div class="wrap">{crumbs(('Compare', '/compare/'), ("Costco vs Sam's Club", ''))}<div class="cohead">{logo('costco')}{logo('walmart')}</div>
<h1>Costco vs Sam's Club: who makes more money?</h1><div class="answer" style="margin-top:26px"><p>{ans}</p></div>
<p class="updated">Costco: Form 10-K for the year ended {c["end_text"]}. Sam's Club: the Sam's Club U.S. segment in Walmart's Form 10-K for the year ended {w["end_text"]}. Page updated {{DATE}}.</p></div></section>
<section class="sec tight"><div class="wrap">{rh}<p class="note">Walmart reports Sam's Club as a segment, so this compares operating profit (net profit isn't reported per segment). Sam's Club U.S. only; Walmart doesn't split out its clubs abroad.</p></div></section>
<section class="sec soft"><div class="wrap"><h2>Quick answers.</h2>{qa_block(qas)}<div class="source"><p><b>Sources:</b> <a href="{c["url"]}" rel="nofollow noopener">Costco Form 10-K</a>, <a href="{w["url"]}" rel="nofollow noopener">Walmart Form 10-K</a>.</p></div>
<p style="margin-top:24px"><a class="go" href="/companies/costco/">How Costco makes money</a> &nbsp; <a class="go" href="/companies/walmart/">How Walmart makes money</a></p></div></section></main>'''
    page(path, "Costco vs Sam's Club: Who Makes More Money?", re.sub('<[^>]+>', '', ans)[:158], body, [bc_ld(('Compare', '/compare/'), ("Costco vs Sam's Club", path)), faq_ld(qas)], 'article'); fix_date(path)

def compare_hub():
    pop = ''.join(f'<a class="card" href="/compare/{s}/"><p class="lbl">{E(ph)}</p><h3>{E(M[a]["name"])} vs {E(M[b]["name"])}</h3><span class="go">See who wins</span></a>' for s, a, b, ph in COMPARES[:18])
    pop += '<a class="card" href="/compare/costco-vs-sams-club/"><p class="lbl">Costco vs Sam\'s Club</p><h3>Costco vs Sam\'s Club</h3><span class="go">See who wins</span></a>'
    body = f'''<main><section class="phead"><div class="wrap">{crumbs(('Compare', ''))}<h1>Compare any two companies.</h1>
<p class="lead">Revenue, profit, how much they keep of every $100, employees and growth, straight from each company's annual report. Pick two.</p>
<div id="cmp"><div class="picker"><div><label for="ca">First company</label><select id="ca"></select></div><button id="cmp-swap" class="btn ghost sm vs" type="button" aria-label="Swap">⇄</button><div><label for="cb">Second company</label><select id="cb"></select></div></div>
<div id="cmp-out"><noscript><p class="note">Turn on JavaScript to use the comparer, or pick a match-up below.</p></noscript></div></div></div></section>
<section class="sec soft"><div class="wrap"><h2>Popular match-ups.</h2><div class="cards">{pop}</div></div></section></main>'''
    page('/compare/', 'Compare Companies: Revenue, Profit and Employees Side by Side', 'Compare any two of 100 big companies: revenue, profit, how much they keep of every $100, employees and growth, from their 10-Ks.', body,
         [bc_ld(('Compare', '/compare/')), {'@context': 'https://schema.org', '@type': 'WebApplication', 'name': 'Company comparer', 'applicationCategory': 'BusinessApplication', 'operatingSystem': 'Any', 'url': URL + '/compare/', 'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'}}])

# ---------- hubs and rankings ----------
SECTOR = lambda m: (m['sic'] or 'Other').title()
def companies_hub():
    rows = sorted(M.values(), key=lambda m: -m['revenue'])
    secs = sorted({SECTOR(m) for m in rows})
    tr = ''.join(f'''<tr data-sector="{E(SECTOR(m))}"><td class="n">{i + 1}</td><td><a href="/companies/{m["slug"]}/">{E(m["name"])}</a></td><td data-v="{m["revenue"]:.0f}">{B(m["revenue"], True)}</td>
<td data-v="{m["net_income"] if m["net_income"] is not None else ""}">{B(m["net_income"], True)}</td><td data-v="{per100(m) if per100(m) is not None else ""}">{"—" if per100(m) is None else f"${per100(m):.2f}"}</td>
<td data-v="{m["employees"][0] if m["employees"] else ""}">{f"{m['employees'][0]:,}" if m["employees"] else "—"}</td><td data-v="{m["end"]}">{m["end"][:7]}</td></tr>''' for i, m in enumerate(rows))
    body = f'''<main><section class="phead"><div class="wrap">{crumbs(('Companies', ''))}<h1>How {len(M)} companies make money.</h1>
<p class="lead">Every company here has its own page: where its money comes from, what it keeps, and how it has changed, from its latest annual report.</p>
<div class="search"><input type="search" placeholder="Search a company" aria-label="Search a company" autocomplete="off"></div></div></section>
<section class="sec tight soft"><div class="wide"><div class="filters"><input type="search" placeholder="Filter the table" aria-label="Filter the table" data-filter="#cotbl">
<select data-sector aria-label="Industry"><option value="">All industries</option>{"".join(f"<option>{E(s)}</option>" for s in secs)}</select></div>
<div class="tblwrap"><table class="tbl sort" id="cotbl"><thead><tr><th>#</th><th class="l" data-k>Company</th><th data-k aria-sort="descending">Revenue</th><th data-k>Net profit</th><th data-k>Kept per $100</th><th data-k>Employees</th><th data-k>Year ended</th></tr></thead>
<tbody>{tr}</tbody></table></div><p class="note">Click a column to sort. Latest annual report for each company. Industry = the SEC's industry code for the company.</p></div></section></main>'''
    page('/companies/', 'How Companies Make Money: 100 Big Companies, by Revenue', f'How {len(M)} big companies make money: revenue, profit, what they keep of every $100 and employees, each from its latest 10-K.', body,
         [bc_ld(('Companies', '/companies/')), {'@context': 'https://schema.org', '@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': f'{URL}/companies/{m["slug"]}/', 'name': f'How {m["name"]} makes money'} for i, m in enumerate(rows)]}])

def rname(r, cov):
    s = cov.get(str(r['cik']))
    if s: return M[s]['name']
    n = re.sub(r'\s*/[A-Z]{2,}/?$', '', r['name']).strip()
    n = n.title() if n.isupper() else n
    return n.replace(' Com Inc', '.com').replace("'S ", "'s ").replace(' Llc', ' LLC').replace(' Plc', ' plc')
def largest():
    rows = RANK['rows'][:100]; cov = {m['cik'].lstrip('0'): m['slug'] for m in M.values()}
    tr = ''
    for i, r in enumerate(rows):
        s = cov.get(str(r['cik'])); nm_h = f'<a href="/companies/{s}/">{E(M[s]["name"])}</a>' if s else E(rname(r, cov))
        k = r['net_income'] / r['revenue'] * 100 if r['net_income'] is not None else None
        tr += f'<tr><td class="n">{i + 1}</td><td>{nm_h} <span class="small">{E(r["ticker"])}</span></td><td data-v="{r["revenue"]}">{B(r["revenue"], True)}</td><td data-v="{r["net_income"] if r["net_income"] is not None else ""}">{B(r["net_income"], True)}</td><td data-v="{k if k is not None else ""}">{"—" if k is None else f"${k:.2f}"}</td><td data-v="{r["rev_end"]}">{r["rev_end"][:7]}</td></tr>'
    top10 = sum(r['revenue'] for r in rows[:10]); top100 = sum(r['revenue'] for r in rows)
    ans = (f"The largest U.S. company by revenue is {rname(rows[0], cov)} with {B(rows[0]['revenue'])}, just ahead of {rname(rows[1], cov)} ({B(rows[1]['revenue'])}). "
           f"The top 10 brought in {B(top10)} between them, and the top 100 {B(top100)}.")
    body = f'''<main><section class="phead"><div class="wrap">{crumbs(('Largest companies', ''))}<h1>The 100 largest U.S. companies by revenue.</h1>
<div class="answer" style="margin-top:26px"><p>{ans}</p></div><p class="updated">Each company's fiscal year closest to calendar 2025, as filed with the SEC. Page updated {{DATE}}.</p>
{bars([(rname(r, cov), r['revenue'], '', i == 0) for i, r in enumerate(rows[:10])], big=True, money=lambda v: B(v, True))}</div></section>
<section class="sec tight soft"><div class="wide"><div class="tblwrap"><table class="tbl sort"><thead><tr><th>#</th><th class="l" data-k>Company</th><th data-k aria-sort="descending">Revenue</th><th data-k>Net profit</th><th data-k>Kept per $100</th><th data-k>Year ended</th></tr></thead><tbody>{tr}</tbody></table></div>
<p class="note">Method: U.S.-based companies with a stock ticker that report revenue to the SEC in XBRL (the SEC's "frames" data for 2025), ranked by revenue. Banks are ranked by net revenue. A dash means the profit figure isn't tagged for the same year. Private companies (like Cargill or Publix's owners' peers) and foreign companies aren't included.</p></div></section>
<section class="sec"><div class="wrap"><h2>Go deeper.</h2><div class="cards"><a class="card" href="/most-profitable-companies/"><h3>Most profitable companies</h3><p>Who makes the most profit, and who keeps the most of every $100.</p><span class="go">See the list</span></a>
<a class="card" href="/revenue-per-employee/"><h3>Revenue per employee</h3><p>Which companies make the most for every person they employ.</p><span class="go">See the list</span></a><a class="card" href="/game/"><h3>Higher or lower</h3><p>Guess which company makes more.</p><span class="go">Play</span></a></div></div></section></main>'''
    page('/largest-companies/', 'Largest US Companies by Revenue: Top 100 (2025, SEC Data)', re.sub('<[^>]+>', '', ans)[:158], body,
         [bc_ld(('Largest companies', '/largest-companies/')), {'@context': 'https://schema.org', '@type': 'Dataset', 'name': 'Largest U.S. companies by revenue, 2025', 'description': 'Revenue and net income of the 100 largest U.S. public companies, from SEC XBRL frames.', 'creator': {'@type': 'Organization', 'name': 'The Business Study'}, 'isBasedOn': 'https://www.sec.gov/edgar', 'license': 'https://creativecommons.org/licenses/by/4.0/'}])
    fix_date('/largest-companies/')

def most_profitable():
    cov = {m['cik'].lstrip('0'): m['slug'] for m in M.values()}
    rows = sorted([r for r in RANK['rows'] if r['net_income'] is not None], key=lambda r: -r['net_income'])[:50]
    nm = lambda r: rname(r, cov)
    link = lambda r: f'<a href="/companies/{cov[str(r["cik"])]}/">{E(nm(r))}</a>' if str(r['cik']) in cov else E(nm(r))
    tr = ''.join(f'<tr><td class="n">{i + 1}</td><td>{link(r)}</td><td data-v="{r["net_income"]}">{B(r["net_income"], True)}</td><td data-v="{r["revenue"]}">{B(r["revenue"], True)}</td><td data-v="{r["net_income"] / r["revenue"] * 100}">${r["net_income"] / r["revenue"] * 100:.2f}</td></tr>' for i, r in enumerate(rows))
    big = sorted([m for m in M.values() if m['revenue'] >= 1e10 and m['net_income'] is not None], key=lambda m: -per100(m))
    keep_top = [(m['name'], per100(m), '', i == 0) for i, m in enumerate(big[:12])]
    keep_low = [(m['name'], per100(m), '', False) for m in big[-8:]]
    ans = f"The most profitable U.S. company is {nm(rows[0])}, with {B(rows[0]['net_income'])} in net profit, followed by {nm(rows[1])} ({B(rows[1]['net_income'])}) and {nm(rows[2])} ({B(rows[2]['net_income'])}). Measured by what it keeps of every $100 in sales, {big[0]['name']} leads the big companies at ${per100(big[0]):.2f}."
    vid = VIDEOS.get('_keep100')
    vh = f'<section class="sec soft"><div class="wrap watch">{yt(vid[0], vid[1])}<div><p class="lbl">Watch</p><h2>{E(vid[1])}</h2><p class="lead">The same idea as a 60-second tier list.</p></div></div></section>' if vid else ''
    body = f'''<main><section class="phead"><div class="wrap">{crumbs(('Most profitable companies', ''))}<h1>The most profitable companies.</h1>
<div class="answer" style="margin-top:26px"><p>{ans}</p></div><p class="updated">Net income for each company's fiscal year closest to 2025, from SEC filings. Page updated {{DATE}}.</p>
{bars([(nm(r), r['net_income'], '', i == 0) for i, r in enumerate(rows[:10])], big=True, money=lambda v: B(v, True))}</div></section>
<section class="sec soft"><div class="wrap"><h2>Who keeps the most of every $100? <span>Companies with $10 billion+ in revenue.</span></h2>{bars(keep_top, big=True, money=D)}
<h3 style="margin-top:44px">And who keeps the least.</h3>{bars(keep_low, money=D)}<p class="note">Net income ÷ revenue × 100, latest annual report. Low isn't always bad: grocers and warehouse clubs run on thin margins and huge volume.</p></div></section>{vh}
<section class="sec tight"><div class="wide"><h2>Top 50 by net profit.</h2><div class="tblwrap"><table class="tbl sort"><thead><tr><th>#</th><th class="l" data-k>Company</th><th data-k aria-sort="descending">Net profit</th><th data-k>Revenue</th><th data-k>Kept per $100</th></tr></thead><tbody>{tr}</tbody></table></div>
<p class="note">Method: U.S. public companies in the SEC's XBRL data, fiscal year closest to calendar 2025. One-time gains and losses are included, because net income includes them.</p></div></section></main>'''
    page('/most-profitable-companies/', 'Most Profitable Companies in the US (2025, by Net Income)', re.sub('<[^>]+>', '', ans)[:158], body, [bc_ld(('Most profitable companies', '/most-profitable-companies/'))])
    fix_date('/most-profitable-companies/')

def per_employee():
    rows = sorted([m for m in M.values() if m['employees']], key=lambda m: -(m['revenue'] / m['employees'][0]))
    tr = ''.join(f'<tr><td class="n">{i + 1}</td><td><a href="/companies/{m["slug"]}/">{E(m["name"])}</a></td><td data-v="{m["revenue"] / m["employees"][0]:.0f}">{K(m["revenue"] / m["employees"][0])}</td><td data-v="{(m["net_income"] or 0) / m["employees"][0]:.0f}">{K((m["net_income"] or 0) / m["employees"][0])}</td><td data-v="{m["employees"][0]}">{m["employees"][0]:,}</td><td data-v="{m["revenue"]:.0f}">{B(m["revenue"], True)}</td></tr>' for i, m in enumerate(rows))
    med = sorted(m['revenue'] / m['employees'][0] for m in rows)[len(rows) // 2]
    ans = f"Among {len(rows)} big companies, {rows[0]['name']} makes the most per employee: {K(rows[0]['revenue'] / rows[0]['employees'][0])} in revenue for each of its {rows[0]['employees'][0]:,} employees. The typical company here makes {K(med)}. {rows[-1]['name']} is lowest at {K(rows[-1]['revenue'] / rows[-1]['employees'][0])}, because restaurants and stores need lots of people."
    body = f'''<main><section class="phead"><div class="wrap">{crumbs(('Revenue per employee', ''))}<h1>Revenue per employee: who makes the most per person?</h1>
<div class="answer" style="margin-top:26px"><p>{ans}</p></div><p class="updated">Revenue ÷ the employee count each company states in its latest 10-K. Page updated {{DATE}}.</p>
{bars([(m['name'], m['revenue'] / m['employees'][0], '', i == 0) for i, m in enumerate(rows[:12])], big=True, money=K)}</div></section>
<section class="sec tight soft"><div class="wide"><div class="tblwrap"><table class="tbl sort"><thead><tr><th>#</th><th class="l" data-k>Company</th><th data-k aria-sort="descending">Revenue per employee</th><th data-k>Profit per employee</th><th data-k>Employees</th><th data-k>Revenue</th></tr></thead><tbody>{tr}</tbody></table></div>
<p class="note">Companies count people differently (full-time only, full-time equivalents, or including part-time and seasonal), and franchise chains don't count the people who work at franchised restaurants. Each company page says exactly what its number counts.</p>
<p style="margin-top:20px"><a class="btn blue" href="/game/">Guess who makes more per employee</a></p></div></section></main>'''
    page('/revenue-per-employee/', 'Revenue per Employee by Company: 90+ Big Companies Ranked', re.sub('<[^>]+>', '', ans)[:158], body, [bc_ld(('Revenue per employee', '/revenue-per-employee/'))])
    fix_date('/revenue-per-employee/')

# ---------- business models + industries ----------
MODELS = [
 ('ads', 'Selling ads', 'The product is free; advertisers pay to reach the people using it.', ['google', 'meta', 'snapchat', 'pinterest', 'reddit']),
 ('subscriptions', 'Subscriptions', 'Customers pay every month or year, so money keeps coming in without a new sale each time.', ['netflix', 'spotify', 'microsoft', 'adobe', 'duolingo', 'peloton', 'zoom']),
 ('franchise', 'Franchising', 'Other people own and run the stores; the brand collects royalties, rent and fees.', ['mcdonalds', 'yum-brands', 'restaurant-brands', 'wendys', 'dominos', 'planet-fitness']),
 ('marketplace', 'Taking a cut', 'The company runs the marketplace and keeps a percentage of every ride, stay, order or sale.', ['uber', 'lyft', 'airbnb', 'doordash', 'ebay', 'etsy', 'booking', 'expedia']),
 ('networks', 'Payment networks', 'Every card swipe pays a small fee to the network that moves the money.', ['visa', 'mastercard', 'american-express', 'paypal']),
 ('hotels', 'Fees on other people\'s buildings', 'The hotel company manages or franchises hotels that other people own and charges fees.', ['marriott', 'hilton']),
 ('volume', 'Low prices, huge volume', 'Thin profit on each sale, made up for by selling an enormous amount.', ['walmart', 'costco', 'target', 'kroger', 'dollar-general', 'home-depot', 'lowes']),
 ('hardware', 'Hardware plus services', 'Sell the device once, then keep earning from what people do on it.', ['apple', 'tesla', 'peloton']),
 ('cloud', 'Renting out computers', 'Companies rent servers, storage and AI instead of buying their own.', ['amazon', 'microsoft', 'google', 'oracle']),
 ('chips', 'Selling chips', 'Design the chips that go into phones, PCs, cars and data centers.', ['nvidia', 'amd', 'intel', 'broadcom', 'qualcomm']),
 ('banks', 'Lending and banking', 'Earn interest on loans and fees on accounts, cards, trading and advice.', ['jpmorgan-chase', 'bank-of-america', 'wells-fargo', 'goldman-sachs']),
 ('brands', 'Selling brands', 'Own the brands, make or outsource the product, and sell through stores.', ['coca-cola', 'pepsico', 'procter-gamble', 'nike', 'hershey', 'monster-energy']),
]
def models_page():
    secs = []
    for key, t, d, cos in MODELS:
        cs = [M[c] for c in cos if c in M and M[c]['net_income'] is not None]
        if not cs: continue
        rev = sum(m['revenue'] for m in cs); ni = sum(m['net_income'] for m in cs)
        rows = sorted([(m['name'], per100(m), '', False) for m in cs], key=lambda r: -r[1])
        secs.append(f'''<section class="sec{" soft" if len(secs) % 2 else ""}" id="{key}"><div class="wrap insight"><div><p class="lbl">{len(secs) + 1:02d}</p><h2>{E(t)}.</h2><p class="lead">{E(d)}</p>
<p class="small">Together these {len(cs)} companies took in {B(rev)} and kept {B(ni)}: ${ni / rev * 100:.2f} of every $100.</p></div>
<div>{bars(rows, money=D, link=lambda r: "/companies/" + next(m["slug"] for m in cs if m["name"] == r[0]) + "/")}<p class="note">Kept per $100 of sales, latest annual report.</p></div></div></section>''')
    body = f'''<main><section class="phead"><div class="wrap">{crumbs(('Business models', ''))}<h1>How companies make money: {len(secs)} business models.</h1>
<p class="lead">Almost every big company makes money one of a few ways. Here they are, with real companies and what each one keeps of every $100, from their annual reports.</p></div></section>{"".join(secs)}
<section class="sec"><div class="wrap"><h2>Industries.</h2><p class="lead">How airlines, banks, streaming services and more make money.</p><div class="cards">{"".join(f'<a class="card" href="/{s}/"><h3>{E(q)}</h3><span class="go">Read</span></a>' for s, q, *_ in INDUSTRIES)}</div></div></section></main>'''
    qas = [(f'What are the main business models?', 'Selling ads, subscriptions, franchising, taking a cut of a marketplace, payment networks, low prices at huge volume, hardware plus services, renting out computers (cloud), selling chips, lending, and selling brands.')]
    page('/how-companies-make-money/', 'How Companies Make Money: 12 Business Models, Real Examples', 'The 12 ways big companies make money (ads, subscriptions, franchising, marketplaces, cloud and more), with real numbers from their 10-Ks.', body, [bc_ld(('Business models', '/how-companies-make-money/')), faq_ld(qas)])

INDUSTRIES = [  # (slug, question, companies, plain explanation)
 ('how-do-airlines-make-money', 'How do airlines make money?', ['delta', 'united-airlines', 'southwest'], 'Airlines sell seats, but tickets alone barely cover the cost of fuel, planes and crews. A big share of the profit comes from loyalty programs: banks pay airlines billions for miles they give out with credit cards. Bag and seat fees and cargo add the rest.'),
 ('how-do-banks-make-money', 'How do banks make money?', ['jpmorgan-chase', 'bank-of-america', 'wells-fargo', 'goldman-sachs'], 'Banks pay you a little interest on deposits and lend that money out at a higher rate; the gap is their biggest source of income. On top of that they charge fees for cards, accounts, trading, advice and managing money.'),
 ('how-do-credit-card-companies-make-money', 'How do credit card companies make money?', ['visa', 'mastercard', 'american-express'], "There are two kinds. Visa and Mastercard run the payment network and earn a small fee on every swipe, but they don't lend money. American Express runs a network and also issues cards, so it also earns card fees and interest from members."),
 ('how-do-streaming-services-make-money', 'How do streaming services make money?', ['netflix', 'spotify', 'disney'], "Streaming services charge a monthly subscription, and more of them now sell cheaper plans with ads. Their biggest cost is the content itself: shows and movies for Netflix and Disney, music royalties for Spotify."),
 ('how-do-social-media-companies-make-money', 'How do social media companies make money?', ['meta', 'snapchat', 'pinterest', 'reddit'], 'Social apps are free because advertisers pay to show ads to the people scrolling. The more time people spend and the better the targeting, the more each ad is worth.'),
 ('how-do-fast-food-chains-make-money', 'How do fast food chains make money?', ['mcdonalds', 'yum-brands', 'restaurant-brands', 'wendys', 'dominos', 'chipotle', 'starbucks'], "Most big fast food brands don't run most of their restaurants. Franchisees pay them royalties on sales, rent and ad fees, which is why their profit per $100 is so high. Chipotle and Starbucks run their own U.S. stores instead, so their revenue is the food itself."),
 ('how-do-hotels-make-money', 'How do hotel companies make money?', ['marriott', 'hilton'], 'The biggest hotel companies own very few hotels. They manage or franchise hotels owned by investors and charge fees on room revenue, plus loyalty and credit card money.'),
 ('how-do-phone-companies-make-money', 'How do phone companies make money?', ['verizon', 'att', 't-mobile'], 'Phone carriers make most of their money from monthly plans, plus selling phones (often at little profit) and home internet. The network costs billions to build, then each extra customer is cheap to serve.'),
 ('how-do-car-companies-make-money', 'How do car companies make money?', ['tesla', 'ford', 'gm'], 'Carmakers sell vehicles to dealers (or, like Tesla, straight to buyers), and big trucks and SUVs carry most of the profit. Their finance arms also earn interest on car loans and leases.'),
 ('how-do-grocery-stores-make-money', 'How do grocery stores make money?', ['kroger', 'walmart', 'costco', 'target', 'dollar-general'], 'Grocers keep only pennies per dollar of sales, so they win by volume, store brands, pharmacy, fuel and, at Costco and Sam\'s Club, membership fees.'),
 ('how-do-movie-theaters-make-money', 'How do movie theaters make money?', ['amc'], 'Theaters split ticket money with the studios, often keeping well under half. The popcorn, soda and snacks are where the margin is.'),
]
def industry_page(slug, q, cos, expl):
    cs = [M[c] for c in cos if c in M]; path = f'/{slug}/'
    rows = sorted(cs, key=lambda m: -m['revenue'])
    rev = sum(m['revenue'] for m in cs); ni = sum((m['net_income'] or 0) for m in cs)
    tr = ''.join(f'<tr><td><a href="/companies/{m["slug"]}/">{E(m["name"])}</a></td><td data-v="{m["revenue"]:.0f}">{B(m["revenue"], True)}</td><td data-v="{m["net_income"] or 0}">{B(m["net_income"], True)}</td><td data-v="{per100(m) or 0}">{"—" if per100(m) is None else f"${per100(m):.2f}"}</td><td class="l">{E(m["streams"][0][0]) if m["streams"] else "—"}</td></tr>' for m in rows)
    detail = ''
    for m in rows[:4]:
        st = m['streams']; tot = sum(v for _, v, _ in st)
        if st: detail += f'<div class="card"><div class="cohead">{logo(m["slug"], True)}<b>{E(m["name"])}</b></div>{bars([(l, v, "") for l, v, _ in st[:5]], total=max(tot, m["revenue"]) if not m.get("gross") else tot)}<a class="go" href="/companies/{m["slug"]}/">How {E(m["name"])} makes money</a></div>'
    first = rows[0]
    ans = f"{expl.split('. ')[0]}. " + (f"Together, {', '.join(m['name'] for m in rows[:-1])} and {rows[-1]['name']} took in {B(rev)} in their latest years and kept {B(ni)} in profit, ${ni / rev * 100:.2f} of every $100." if len(rows) > 1 else f"{first['name']} took in {B(rev)} and {'kept' if ni >= 0 else 'lost'} {B(abs(ni))}.")
    body = f'''<main><section class="phead"><div class="wrap">{crumbs(('Industries', '/industries/'), (q.rstrip('?'), ''))}<h1>{E(q)}</h1>
<div class="answer" style="margin-top:26px"><p>{E(ans)}</p></div><p class="updated">From each company's latest Form 10-K. Page updated {{DATE}}.</p></div></section>
<section class="sec tight"><div class="wrap"><p class="lead" style="max-width:70ch">{E(expl)}</p>
<div class="tblwrap"><table class="tbl sort"><thead><tr><th class="l" data-k>Company</th><th data-k aria-sort="descending">Revenue</th><th data-k>Net profit</th><th data-k>Kept per $100</th><th class="l">Biggest line</th></tr></thead><tbody>{tr}</tbody></table></div></div></section>
{f'<section class="sec soft"><div class="wrap"><h2>Where each company\'s money comes from.</h2><div class="cards two">{detail}</div></div></section>' if detail else ''}
<section class="sec tight"><div class="wrap"><div class="source"><p><b>Sources:</b> {", ".join(f'<a href="{m["url"]}" rel="nofollow noopener">{E(m["name"])} Form {m["form"]}</a>' for m in rows)} on SEC EDGAR.</p></div>
<p style="margin-top:20px"><a class="go" href="/how-companies-make-money/">All business models</a></p></div></section></main>'''
    qas = [(q, ans)]
    tq = q[:-1].title().replace("'S", "'s")
    title = f'{tq}? Real Numbers From Their 10-Ks' if len(tq) <= 34 else f'{tq}? (Real Numbers)'
    page(path, title, ans[:158], body, [bc_ld(('Industries', '/industries/'), (q, path)), faq_ld(qas)], 'article'); fix_date(path)

def industries_hub():
    cards = ''.join(f'<a class="card" href="/{s}/"><h3>{E(q)}</h3><p>{E(", ".join(M[c]["name"] for c in cos if c in M))}</p><span class="go">Read</span></a>' for s, q, cos, _ in INDUSTRIES)
    body = f'<main><section class="phead"><div class="wrap">{crumbs(("Industries", ""))}<h1>How whole industries make money.</h1><p class="lead">The biggest companies in each industry, side by side, from their annual reports.</p><div class="cards">{cards}</div></div></section></main>'
    page('/industries/', 'How Industries Make Money: Airlines, Banks, Streaming and More', 'How airlines, banks, credit card companies, streaming services, fast food chains, hotels and more make money, with real 10-K numbers.', body, [bc_ld(('Industries', '/industries/'))])

# ---------- statistics ----------
def stats_page():
    cs = [m for m in M.values() if m['net_income'] is not None]
    rev = sum(m['revenue'] for m in cs); ni = sum(m['net_income'] for m in cs)
    losers = [m for m in cs if m['net_income'] < 0]
    margins = sorted(per100(m) for m in cs); med = margins[len(margins) // 2]
    emp = [m for m in cs if m['employees']]; E_tot = sum(m['employees'][0] for m in emp)
    biggest_emp = max(emp, key=lambda m: m['employees'][0])
    grow = [(m, growth(m)) for m in cs if growth(m) is not None]; fastest = max(grow, key=lambda x: x[1])
    top10 = RANK['rows'][:10]
    facts = [
        (f'{len(cs)} big companies', f'took in {B(rev)} in revenue in their latest years and kept {B(ni)} in net profit.', ''),
        (f'${ni / rev * 100:.2f}', 'is what they kept out of every $100 of sales, all together.', ''),
        (f'${med:.2f}', 'is what the typical (median) company kept of every $100.', ''),
        (f'{len(losers)} of {len(cs)}', f'lost money in their latest year: {", ".join(m["name"] for m in sorted(losers, key=lambda m: m["net_income"]))}.', ''),
        (f'{biggest_emp["employees"][0]:,}', f'people work at {biggest_emp["name"]}, the biggest employer here. All {len(emp)} companies with a stated count employ {E_tot:,} people together.', ''),
        (f'+{fastest[1]:.0f}%', f'is {poss(fastest[0]["name"])} revenue growth over the years shown, the fastest of any company here.', ''),
        (B(sum(r['revenue'] for r in top10)), 'is what the 10 largest U.S. companies brought in between them.', ''),
    ]
    fh = ''.join(f'<div class="tile reveal{" hi" if i == 1 else ""}"><b>{E(a)}</b><small style="font-size:15px;color:var(--ink2)">{E(b)}</small></div>' for i, (a, b, _) in enumerate(facts))
    cite = f'The Business Study, "Business statistics" ({URL}/business-statistics/), from companies\' SEC filings, updated {datetime.date.today().strftime("%B %Y")}.'
    body = f'''<main><section class="phead"><div class="wrap">{crumbs(('Statistics', ''))}<h1>Business statistics: what big companies earn and keep.</h1>
<p class="lead">Numbers worked out from the latest annual reports of {len(cs)} big companies and the SEC's data on every U.S. public company. Free to cite.</p></div></section>
<section class="sec tight soft"><div class="wrap"><div class="tiles" style="grid-template-columns:repeat(2,1fr)">{fh}</div>
<div class="callout"><b>How to cite:</b> {E(cite)}</div><p class="note">Sources: each company's Form 10-K (or 20-F) on SEC EDGAR, and the SEC's XBRL "frames" data for the largest companies. Profit = net income. See each company page for its filing.</p></div></section></main>'''
    page('/business-statistics/', 'Business Statistics 2026: Revenue, Profit and Margins (SEC Data)', f'{len(cs)} big companies took in {B(rev)} and kept ${ni / rev * 100:.2f} of every $100. More business statistics from their 10-Ks, free to cite.', body,
         [bc_ld(('Statistics', '/business-statistics/')), {'@context': 'https://schema.org', '@type': 'Dataset', 'name': 'Business statistics from SEC filings', 'description': 'Revenue, profit, margins and employees of 100 big U.S.-listed companies.', 'creator': {'@type': 'Organization', 'name': 'The Business Study'}, 'license': 'https://creativecommons.org/licenses/by/4.0/', 'isBasedOn': 'https://www.sec.gov/edgar'}])

# ---------- game ----------
def game_page():
    body = f'''<main><section class="phead"><div class="wrap center">{crumbs(('Game', ''))}<h1>Higher or lower: which company makes more?</h1>
<p class="lead">Two companies. Pick the one that makes more. Every answer comes from the companies' own annual reports.</p></div></section>
<section class="sec tight"><div class="wrap"><div class="game" id="game"><div class="modes" role="group" aria-label="What to compare"><button data-m="rev" aria-pressed="true">Revenue</button><button data-m="prof" aria-pressed="false">Profit</button><button data-m="emp" aria-pressed="false">Per employee</button><button data-m="keep" aria-pressed="false">Kept per $100</button></div>
<p class="q">Which company brings in more money a year?</p><div class="pick"><button class="opt" type="button"><span class="nm">…</span><span class="val"></span><span class="sub"></span></button><button class="opt" type="button"><span class="nm">…</span><span class="val"></span><span class="sub"></span></button></div>
<p class="msg" aria-live="polite"></p><div class="bar"><span>Streak <b id="g-streak">0</b> · Best <b id="g-best">0</b></span><button class="btn blue" id="g-next" type="button" hidden>Next pair</button></div>
<noscript><p class="note">This game needs JavaScript. You can browse every company's numbers on <a href="/companies/">the companies page</a>.</p></noscript></div></div></section>
<section class="sec soft"><div class="wrap"><h2>How it works.</h2><p class="lead">Each round picks two of {len(M)} big companies with at least $2 billion in revenue. Revenue and profit are from each company's latest annual report; "per employee" divides revenue by the employee count the report states. Your best streak stays in this browser only.</p>
<div class="cards"><a class="card" href="/compare/"><h3>Compare any two</h3><span class="go">Open the comparer</span></a><a class="card" href="/revenue-per-employee/"><h3>Revenue per employee</h3><span class="go">See the ranking</span></a><a class="card" href="/largest-companies/"><h3>Largest companies</h3><span class="go">See the top 100</span></a></div></div></section></main>'''
    page('/game/', 'Which Company Makes More? Higher or Lower Business Game', 'A free higher-or-lower game: guess which company makes more revenue, profit or money per employee. Real numbers from their 10-Ks.', body,
         [bc_ld(('Game', '/game/')), {'@context': 'https://schema.org', '@type': 'WebApplication', 'name': 'Which company makes more?', 'applicationCategory': 'GameApplication', 'operatingSystem': 'Any', 'url': URL + '/game/', 'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'}}])

# ---------- creator studies (content.py) ----------
SEO = {
 'best-faceless-youtube-niches': ('Best Faceless YouTube Niches: 572 Small Channels Ranked', '572 small faceless YouTube channels ranked by niche. True crime, military history and nostalgia get the most views per video; finance gets the fewest.'),
 'how-long-should-a-youtube-video-be': ('How Long Should a YouTube Video Be? 111,322 Videos Compared', 'How long a YouTube video should be, from 111,322 videos on 3,421 channels: videos under 8 minutes did worst, 30-60 minutes did best.'),
 'how-often-should-you-post-on-youtube': ('How Often Should You Post on YouTube? 1,664 Channels', 'How often to post on YouTube, from 1,664 channels: posting more gets fewer views per video but more total views per week.'),
 'best-time-to-post-on-youtube': ('Best Time to Post on YouTube: 24,918 Uploads Compared', 'The best day and time to post on YouTube from 24,918 uploads: Monday and weekends do a few percent better, and the hour barely matters.'),
 'why-youtube-videos-go-viral': ('Why YouTube Videos Go Viral: 1,019 Outliers Studied', 'Why YouTube videos go viral, from 1,019 viral vs normal videos on the same channels: in 74% of pairs the viral one made a different promise.'),
 'what-makes-a-youtube-thumbnail-work': ('What Makes a YouTube Thumbnail Work? 2,038 Analyzed', '2,038 YouTube thumbnails compared within the same channels: viral ones weren’t brighter or bigger-faced. They showed the promise, not the title.'),
 'youtube-script-study': ('YouTube Script Study: 1,888 Viral vs Normal Scripts', '949 viral and 939 normal YouTube scripts from 294 channels: same pace, same sentence length, same openings. Viral videos were simply longer.'),
 'how-much-youtube-pays': ('How Much Does YouTube Pay Per View? 82 Creators’ Real RPMs', 'How much YouTube pays per view: about $6.19 per 1,000 views on a typical long video (0.6 cents a view) and $0.16 per 1,000 on Shorts, from 82 creators.'),
 'youtube-shorts-vs-long-form': ('YouTube Shorts vs Long Videos: 586 Channels That Post Both', '586 channels that post both: a typical Short got 0.30x the views of a long video, won on only 22% of channels, and paid 39x less per view.'),
 'does-4k-get-more-views': ('Does 4K Get More Views on YouTube? 693 Video Pairs', 'Does 4K, 60 fps or HDR get more views on YouTube? In 693 viral vs normal pairs from the same channels, video quality made no difference.'),
 'is-youtube-killing-small-channels': ('Is YouTube Killing Small Channels? What the Data Says', 'Small channels (1K-10K subscribers) got views equal to 42.7% of their subscribers per video, vs 7.2% for channels over 1M. Breakouts were twice as common.'),
}
def short_title(s): return re.split(r'[?:(]', s['title'])[0].strip().rstrip('.') + ('?' if '?' in s['title'].split(':')[0] else '')
def slug_id(h): return re.sub(r'[^a-z0-9]+', '-', h.lower()).strip('-')[:48]
def schart(c):
    rows = c['rows']; mx = max(r[1] for r in rows); base = c.get('base')
    fmt = lambda v: ('$' + f'{v:,.{c["dec"]}f}') if c['unit'] == '$' else (f'{v:,.{c["dec"]}f}%' if c['unit'] == '%' else (f'{v:,.{c["dec"]}f}×' if c['unit'] == '×' else f'{v:,.{c["dec"]}f}'))
    rng = max(.15, 1.2 * max(abs(r[1] - base) for r in rows)) if base else None
    out = [f'<figure class="chart{" div" if base else ""}"><figcaption>{E(c["title"])}</figcaption><div class="rows">']
    for r in rows:
        lab, v, n = r[0], r[1], (r[2] if len(r) > 2 else None)
        cls = ' hi' if lab == c.get('hi') else ' lo' if lab == c.get('lo') else ''
        if base: d = 50 * abs(v - base) / rng; bar = f'<span style="{"left:50%" if v >= base else "right:50%"};--w:{max(d, .6):.1f}%"></span>'
        else: bar = f'<span style="--w:{max(1.5, 100 * v / mx):.1f}%"></span>'
        out.append(f'<div class="row{cls}"><span class="l">{E(lab)}{f"<i>n={n:,}</i>" if n else ""}</span><span class="b">{bar}</span><span class="v">{fmt(v)}</span></div>')
    out.append('</div>' + (f'<p class="note">{E(c["note"])}</p>' if c.get('note') else '') + '</figure>')
    return ''.join(out)
def study(s):
    path = f'/studies/{s["slug"]}/'; i = STUDIES.index(s); stat, lab = HERO[s['slug']]
    toc = ''.join(f'<a href="#{slug_id(h)}">{E(h)}</a>' for h, _, _ in s['sections'])
    secs = ''.join(f'<section class="ssec" id="{slug_id(h)}"><p class="n">{k + 1:02d}</p><h2>{E(h)}</h2>{"".join(f"<p>{p}</p>" for p in ps)}<div class="sowhat"><b>What to do</b><p>{so}</p></div></section>' for k, (h, ps, so) in enumerate(s['sections']))
    faq = ''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in s['faq'])
    vid = s.get('video') or RELATED.get(s['slug'])
    prv, nxt = STUDIES[i - 1], STUDIES[(i + 1) % len(STUDIES)]
    body = f'''<main class="study"><section class="phead"><div class="narrow">{crumbs(('Studies', '/studies/'), (short_title(s), ''))}<h1>{E(s["title"])}</h1>
<div class="bigstat"><div class="v">{E(stat)}</div><p>{E(lab)}</p></div><p class="byline"><img src="/assets/logo-128.png" alt="" width="28" height="28">By <a href="/about/">The Business Study</a> · {s["date"]}</p></div></section>
<div class="narrow"><div class="answer"><p class="lbl">The short answer</p><p>{s["answer"]}</p></div><nav class="toc"><b>In this study</b>{toc}<a href="#method">How we did it</a></nav>
{schart(s["chart"])}{secs}{schart(s["chart2"]) if s.get("chart2") else ""}
{f'<div class="ssec">{yt(vid, STUDY_VIDEOS.get(vid, s["title"]), True)}</div>' if vid in STUDY_VIDEOS else ""}
<section class="ssec" id="method"><h2>How we did it</h2><p>{s["method"]}</p><h3 style="margin:22px 0 8px">The limits</h3><p>{s["limits"]}</p></section>
<section class="faq ssec"><h2>Questions</h2>{faq}</section>
<nav class="pn"><a href="/studies/{prv["slug"]}/"><small>← Previous</small>{E(short_title(prv))}</a><a href="/studies/{nxt["slug"]}/"><small>Next →</small>{E(short_title(nxt))}</a></nav></div></main>'''
    ld = [{'@context': 'https://schema.org', '@type': 'Article', 'headline': s['title'], 'description': s['desc'], 'datePublished': s['date'], 'author': {'@type': 'Organization', 'name': 'The Business Study', 'url': URL + '/about/'}, 'mainEntityOfPage': URL + path},
          faq_ld(s['faq']), bc_ld(('Studies', '/studies/'), (s['title'], path))]
    st, sd = SEO.get(s['slug'], (s['title'], s['desc']))
    page(path, st, sd, body, ld, 'article')
def studies_hub():
    cards = ''.join(f'<a class="card" href="/studies/{s["slug"]}/"><b class="n">{E(HERO[s["slug"]][0])}</b><h3>{E(short_title(s))}</h3><p>{E(s["short"])}</p><span class="go">Read the study</span></a>' for s in STUDIES)
    body = f'<main><section class="phead"><div class="wrap">{crumbs(("Studies", ""))}<h1>Creator data studies.</h1><p class="lead">What YouTube pays, the best Shorts hooks, video length, posting time and more, from hundreds of thousands of real videos.</p><div class="cards">{cards}</div></div></section></main>'
    page('/studies/', 'YouTube Data Studies: What Pays, What Works, What Doesn’t', 'Free data studies on YouTube: what it pays per view, the best faceless niches, video length, posting frequency, viral videos, thumbnails and Shorts.', body, [bc_ld(('Studies', '/studies/'))])

# ---------- home ----------
def home(data):
    big = sorted([m for m in M.values() if m['revenue'] >= 3e10 and m['net_income'] is not None], key=lambda m: -m['revenue'])
    pick = [s for s in ('apple', 'amazon', 'walmart', 'nvidia', 'visa', 'mcdonalds', 'costco', 'meta', 'tesla', 'coca-cola', 'netflix', 'starbucks') if s in M]
    cyc = [{'s': s, 'n': M[s]['name'], 'k': round(per100(M[s]), 2), 'y': f'year ended {M[s]["end_text"]}'} for s in pick]
    a = M[pick[0]]; k0 = per100(a)
    total_rev = sum(m['revenue'] for m in M.values())
    # surprising facts, computed
    ins = []
    am = M.get('amazon')
    if am and am['seg_profit']:
        aws = next((v for l, v, _ in am['streams'] if l.startswith('AWS')), None); awsp = next((v for l, v, _ in am['seg_profit'] if l.startswith('AWS')), None)
        if aws and awsp: ins.append(('amazon', f'{aws / am["revenue"] * 100:.0f}% → {awsp / am["operating_income"] * 100:.0f}%', 'AWS is a small slice of Amazon\'s sales and most of its profit.', f'Renting out servers was {aws / am["revenue"] * 100:.0f}% of Amazon\'s revenue but {awsp / am["operating_income"] * 100:.0f}% of its operating profit.'))
    mt = M.get('meta')
    if mt and mt['seg_profit']:
        rl = next((v for l, v, _ in mt['seg_profit'] if 'Reality' in l), None)
        if rl and rl < 0: ins.append(('meta', B(rl, True), 'Meta\'s headsets and glasses lost money.', f'Reality Labs lost {B(-rl)} in {period(mt)}, while the apps made {B(next(v for l, v, _ in mt["seg_profit"] if "Family" in l))}.'))
    co = M.get('costco')
    if co:
        from model import member_value, RAW
        mem, _ = member_value(RAW['costco'], 'MembershipMember')
        if mem: ins.append(('costco', f'{mem / co["net_income"] * 100:.0f}%', 'Costco\'s membership fees vs its whole profit.', f'Costco collected {B(mem)} in membership fees, equal to {mem / co["net_income"] * 100:.0f}% of its {B(co["net_income"])} net profit.'))
    v = M.get('visa')
    if v: ins.append(('visa', f'${per100(v):.0f}', 'Visa keeps more of every $100 than almost anyone.', f'Visa kept ${per100(v):.2f} of every $100 in {period(v)}. Walmart kept ${per100(M["walmart"]):.2f}.'))
    ins_h = ''.join(f'<a class="card reveal" href="/companies/{s}/"><b class="n">{E(n)}</b><h3>{E(t)}</h3><p>{E(d)}</p><span class="go">See the breakdown</span></a>' for s, n, t, d in ins[:4])
    keep = sorted(big, key=lambda m: -per100(m))
    keep_rows = [(m['name'], per100(m), '', i == 0) for i, m in enumerate(keep[:6])] + [(m['name'], per100(m), 'among the lowest', False) for m in keep[-3:]]
    vids = [(k, v) for k, v in VIDEOS.items() if not k.startswith('_')][:4]
    vid_h = ''.join(f'<figure>{yt(v[0], v[1])}<figcaption>{E(v[1])}</figcaption></figure>' for k, v in vids)
    popular = [s for s in ('walmart', 'google', 'apple', 'meta', 'amazon', 'tesla', 'costco', 'netflix', 'nvidia', 'mcdonalds', 'uber', 'microsoft', 'starbucks', 'nike', 'doordash', 'paypal', 'spotify', 'airbnb') if s in M]
    pl = ''.join(f'<a href="/companies/{s}/"><b>{E(M[s]["name"])}</b><small>{B(M[s]["revenue"], True)}</small></a>' for s in popular)
    body = f'''<main>
<section class="hero"><div class="wrap grid"><div><h1>How companies really make money.</h1>
<p class="lead">Straight from their annual reports. {len(M)} companies, every number sourced, explained in plain English.</p>
<div class="search"><input type="search" placeholder="Search a company, like Costco or Nvidia" aria-label="Search a company" autocomplete="off"></div>
<p class="hint">Popular: <a href="/companies/apple/">Apple</a>, <a href="/companies/amazon/">Amazon</a>, <a href="/companies/costco/">Costco</a>, <a href="/compare/coca-cola-vs-pepsico/">Coke vs Pepsi</a></p></div>
<div class="k100" data-cycle='{E(json.dumps(cyc))}'><div class="top"><a class="who" href="/companies/{a["slug"]}/"><span>{E(a["name"])}</span></a><div class="nav"><button type="button" data-d="prev" aria-label="Previous company">‹</button><button type="button" data-d="next" aria-label="Next company">›</button></div></div>
<p class="say">Out of every $100 in sales, {E(a["name"])} kept</p><div class="big">${k0:.2f}<small>profit</small></div>{bar100(k0, f"{a['name']} kept ${k0:.2f} of every $100")}
<p class="src">Net income ÷ revenue, year ended {a["end_text"]}. Source: {E(poss(a["name"]))} annual report (Form 10-K).</p></div></div></section>
<div class="wrap"><div class="proof"><div><b>{len(M)}</b><span>companies broken down</span></div><div><b>{B(total_rev, True).replace("$", "$")}</b><span>in revenue covered</span></div><div><b>{len(COMPARES) + 1}</b><span>head-to-head match-ups</span></div><div><b>100%</b><span>from SEC filings</span></div></div></div>
<section class="sec"><div class="wrap"><h2 class="reveal">The surprising part. <span>Where the profit really comes from.</span></h2><div class="cards two">{ins_h}</div></div></section>
<section class="sec soft"><div class="wrap"><h2 class="reveal">Who keeps the most of every $100? <span>Big companies, most to least.</span></h2>{bars(keep_rows, big=True, money=D, link=lambda r: "/companies/" + next(m["slug"] for m in big if m["name"] == r[0]) + "/")}
<p style="margin-top:26px"><a class="go" href="/most-profitable-companies/">The full ranking</a></p></div></section>
<section class="sec"><div class="wrap"><h2 class="reveal">Play with the numbers.</h2><div class="cards">
<a class="card" href="/compare/"><p class="lbl">Tool</p><h3>Compare any two companies</h3><p>Revenue, profit, margin, employees and growth, round by round.</p><span class="go">Compare</span></a>
<a class="card" href="/game/"><p class="lbl">Game</p><h3>Which company makes more?</h3><p>Higher or lower, with real numbers. How long can your streak go?</p><span class="go">Play</span></a>
<a class="card" href="/largest-companies/"><p class="lbl">Ranking</p><h3>The 100 largest U.S. companies</h3><p>By revenue, from the SEC's own data.</p><span class="go">See the list</span></a></div></div></section>
<section class="sec soft"><div class="wrap"><h2 class="reveal">How the biggest names make money.</h2><div class="colist">{pl}</div><p style="margin-top:24px"><a class="go" href="/companies/">All {len(M)} companies</a></p></div></section>
{f'<section class="sec"><div class="wrap"><h2 class="reveal">Watch the breakdowns. <span>Under a minute each.</span></h2><div class="vids">{vid_h}</div><p style="margin-top:24px"><a class="btn blue" href="{SUB}" rel="noopener">Subscribe on YouTube</a></p></div></section>' if vid_h else ''}
<section class="sec soft"><div class="wrap"><h2 class="reveal">Every business model, explained.</h2><p class="lead">Ads, subscriptions, franchising, taking a cut, payment networks and more: the dozen ways big companies make money.</p>
<p style="margin-top:22px"><a class="btn" href="/how-companies-make-money/">See the business models</a></p></div></section>
</main>'''
    ld = [{'@context': 'https://schema.org', '@type': 'WebSite', 'name': 'The Business Study', 'url': URL + '/'},
          {'@context': 'https://schema.org', '@type': 'Organization', 'name': 'The Business Study', 'url': URL + '/', 'logo': URL + '/assets/icon.png', 'sameAs': [u for _, u in SOCIALS], 'founder': {'@type': 'Person', 'name': 'Elijah Westbrook', 'url': 'https://elijahwestbrook.com'}}]
    page('/', 'The Business Study: How Companies Make Money, From Their 10-Ks', f'How {len(M)} big companies make money, straight from their annual reports: where revenue comes from, what they keep of every $100, and who wins head to head.', body, ld)

def about():
    body = f'''<main><section class="phead"><div class="narrow">{crumbs(('About', ''))}<h1>About The Business Study.</h1>
<p class="lead">We read the annual reports so you don't have to, and show how companies really make money: where it comes from, what they keep, and how they compare.</p></div></section>
<section class="sec tight"><div class="narrow">
<h2>Where the numbers come from</h2><p>Every company number on this site comes from that company's own annual report filed with the U.S. Securities and Exchange Commission: Form 10-K for U.S. companies, Form 20-F for a few foreign ones. We read the structured data (XBRL) inside each filing through the SEC's free EDGAR API, so the numbers are exactly what the company reported. Each page links to the filing it used.</p>
<p>Revenue breakdowns use the lines each company reports (products, services or segments). We pick lines that don't overlap, so the parts add up to the whole, and we say so when they don't. Employee counts are read from the "human capital" section of each report and checked by hand. "Kept of every $100" is net income divided by revenue.</p>
<p>The largest-company and most-profitable rankings use the SEC's "frames" data, which holds every U.S. public company's figures for the fiscal year closest to a calendar year.</p>
<h2 style="margin-top:44px">What we don't do</h2><p>We don't estimate, project or round numbers into something they aren't. If a filing doesn't report something (like a private company's revenue), it isn't here. Nothing on this site is investment advice.</p>
<h2 style="margin-top:44px">Who runs it</h2><p>The Business Study is a YouTube channel and website run by <a href="https://elijahwestbrook.com" rel="noopener">Elijah Westbrook</a>. The short videos break down one company at a time; the narration is an AI voice. The site also hosts our earlier <a href="/studies/">creator data studies</a> on YouTube.</p>
<p>No company pays for coverage, and no company made or endorses this site. Logos are used only to identify the company a page is about.</p>
<p style="margin-top:28px"><a class="btn blue" href="{SUB}" rel="noopener">Subscribe on YouTube</a></p></div></section></main>'''
    page('/about/', 'About The Business Study: Method and Sources', 'How The Business Study gets its numbers: each company\'s own 10-K on SEC EDGAR, read from the filing\'s XBRL data. Who runs it and what we don\'t do.', body,
         [bc_ld(('About', '/about/')), {'@context': 'https://schema.org', '@type': 'AboutPage', 'mainEntity': {'@type': 'Organization', 'name': 'The Business Study', 'url': URL, 'sameAs': [u for _, u in SOCIALS]}}])

def privacy():
    body = f'''<main><section class="phead"><div class="narrow">{crumbs(('Privacy', ''))}<h1>Privacy.</h1><p class="lead">Short version: no accounts, no forms that collect personal data, and two kinds of visitor counting.</p></div></section>
<section class="sec tight"><div class="narrow"><h2>Website analytics</h2>
<p>We count visits with Cloudflare Web Analytics, which uses no cookies and doesn't track you across sites, and with Google Analytics 4, which sets first-party cookies to tell visits apart and measure which pages people read. Google Analytics data is used only in aggregate (how many people visited which pages, from which country and which kind of device). You can block it with your browser's tracking protection or Google's opt-out add-on (tools.google.com/dlpage/gaoptout).</p>
<h2 style="margin-top:36px">Videos</h2><p>YouTube videos load only when you press play (through youtube-nocookie.com). Until then no YouTube code runs on the page.</p>
<h2 style="margin-top:36px">Games and votes</h2><p>The higher-or-lower game keeps your best streak in your own browser (local storage); it never leaves your device. Votes on the <a href="/vote/">vote page</a> are counted without names or accounts.</p>
<h2 style="margin-top:36px">Contact</h2><p>Questions: reach us through the <a href="{YT}" rel="noopener">YouTube channel</a>.</p></div></section></main>'''
    page('/privacy/', 'Privacy | The Business Study', 'How The Business Study counts visits (Cloudflare Web Analytics and Google Analytics 4), how videos load, and what the game stores in your browser.', body, [bc_ld(('Privacy', '/privacy/'))])

def vote():
    TS = '0x4AAAAAAFyhvovKDo2j0cLa'
    body = f'''<main><section class="phead"><div class="wrap">{crumbs(('Vote', ''))}<h1>What do people really think?</h1><p class="lead">Money, work, brands and business. Vote, then see what won this week, this month, the last 6 months or all time.</p>
<div id="vote" data-site="bs" data-ts="{TS}"></div></div></section></main>'''
    page('/vote/', 'Vote: Best Side Hustle, Best Franchise, Best Company to Work For', 'Vote on the best side hustle, the best franchise to own, the best company to work for and more. See what won this week, this month or all time.', body,
         policy=csp('https://lemon-survey.elift08.workers.dev https://challenges.cloudflare.com', 'https://challenges.cloudflare.com', 'https://challenges.cloudflare.com'), scripts=f'<script src="/assets/vote.js?v={V}" defer></script>')

# ---------- build ----------
def build():
    os.makedirs(OUT, exist_ok=True)
    for x in os.listdir(OUT):
        p = os.path.join(OUT, x); shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    shutil.copytree('assets', os.path.join(OUT, 'assets'), ignore=shutil.ignore_patterns('site.css', 'site.js', 'icons'))
    open(os.path.join(OUT, 'assets', 'js.js'), 'w').write("document.documentElement.classList.add('js');\n")
    data = co_json()
    for m in M.values(): company_page(m)
    for s, a, b, ph in COMPARES: compare_page(s, a, b, ph)
    sams_club_page(); compare_hub(); companies_hub(); largest(); most_profitable(); per_employee(); models_page()
    for ind in INDUSTRIES: industry_page(*ind)
    industries_hub(); stats_page(); game_page()
    for s in STUDIES: study(s)
    studies_hub(); about(); privacy(); vote(); home(data)
    page('/404.html', 'Page not found | The Business Study', 'Page not found.', f'<main><section class="phead"><div class="wrap"><h1>That page doesn\'t exist.</h1><p class="lead">Try a company instead.</p><div class="search"><input type="search" placeholder="Search a company" aria-label="Search a company" autocomplete="off"></div><p style="margin-top:24px"><a class="btn" href="/companies/">All companies</a></p></div></section></main>', noindex=True)
    pages = sorted(PAGES, key=lambda p: (p[0] != '/', p[0]))
    open(f'{OUT}/sitemap.xml', 'w', encoding='utf-8').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        ''.join(f'<url><loc>{URL}{p}</loc><lastmod>{d}</lastmod></url>\n' for p, t, d in pages) + '</urlset>\n')
    bots = ['Googlebot', 'Bingbot', 'GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User', 'PerplexityBot', 'Perplexity-User', 'Applebot', 'DuckDuckBot']
    open(f'{OUT}/robots.txt', 'w').write(''.join(f'User-agent: {b}\nAllow: /\n\n' for b in bots) + f'User-agent: *\nAllow: /\n\nSitemap: {URL}/sitemap.xml\n')
    co = sorted(M.values(), key=lambda m: -m['revenue'])
    open(f'{OUT}/llms.txt', 'w', encoding='utf-8').write(
        f'# The Business Study\n\n> How companies make money, from their own annual reports (Form 10-K on SEC EDGAR). {len(M)} companies: revenue by line, profit by segment, what each keeps of every $100, employees and 5-year history. Every page links the filing it uses.\n\n'
        '## Key pages\n' + ''.join(f'- [{t}]({URL}{p})\n' for p, t in [('/companies/', 'All companies'), ('/compare/', 'Compare any two companies'), ('/largest-companies/', 'Largest US companies by revenue'), ('/most-profitable-companies/', 'Most profitable companies'), ('/revenue-per-employee/', 'Revenue per employee'), ('/how-companies-make-money/', 'Business models'), ('/business-statistics/', 'Business statistics'), ('/about/', 'Method and sources')]) +
        '\n## How each company makes money\n' + ''.join(f'- [How {m["name"]} makes money]({URL}/companies/{m["slug"]}/): {re.sub("<[^>]+>", "", answer(m))[:200]}\n' for m in co) +
        '\n## Head to head\n' + ''.join(f'- [{M[a]["name"]} vs {M[b]["name"]}]({URL}/compare/{s}/)\n' for s, a, b, _ in COMPARES) +
        '\n## Industries\n' + ''.join(f'- [{q}]({URL}/{s}/)\n' for s, q, *_ in INDUSTRIES) +
        '\n## Creator studies\n' + ''.join(f'- [{s["title"]}]({URL}/studies/{s["slug"]}/): {s["short"]}\n' for s in STUDIES))
    open(f'{OUT}/{INDEXNOW_KEY}.txt', 'w').write(INDEXNOW_KEY)
    open(f'{OUT}/google00cb28bea71f4c18.html', 'w').write('google-site-verification: google00cb28bea71f4c18.html')   # Search Console (11-08)
    open(f'{OUT}/BingSiteAuth.xml', 'w').write('<?xml version="1.0"?>\n<users>\n\t<user>2F84C8106BB577C5860ABE6EC15825EC</user>\n</users>')   # Bing Webmaster (11-08)
    open(f'{OUT}/CNAME', 'w').write('thebusinessstudy.com\n'); open(f'{OUT}/.nojekyll', 'w').write('')
    json.dump(DATES, open('data/page_dates.json', 'w', encoding='utf-8'), indent=0, sort_keys=True)
    print('built', len(PAGES), 'pages into', OUT)

if __name__ == '__main__': build()

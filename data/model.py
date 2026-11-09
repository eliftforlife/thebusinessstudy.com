# 11-08: turns data/companies.json (raw SEC pull) + data/curated.py (hand-checked facts and plain-English notes) into the numbers each
# company page shows. Every number traces back to the company's own annual report; nothing is estimated.
import os, re, json, datetime
from curated import CURATED, EMPLOYEES
D = os.path.dirname(os.path.abspath(__file__))
RAW = json.load(open(os.path.join(D, 'companies.json'), encoding='utf-8'))

GENERIC = re.compile(r'^(?:product|products|service|services|products and services|operating segments?|corporate non segment|reportable segments?|segment reconciling items|intersegment elimination|consolidation eliminations?|all other|other|total)$', re.I)
def clean(label):
    s = re.sub(r'\s*\[Member\]|\bMember\b', '', label or '').strip()
    s = re.sub(r'\s+Segment$', '', s).strip()
    s = s.replace('Homeand', 'Home and').replace(' And ', ' and ').replace(' Of ', ' of ').replace(' The ', ' the ').replace(' For ', ' for ').replace(' To ', ' to ')
    s = re.sub(r'\bI Phone\b', 'iPhone', s); s = re.sub(r'^IPhone', 'iPhone', s); s = re.sub(r'^IPad', 'iPad', s)
    s = {'US': 'United States', 'Non Us': 'Outside the U.S.', 'Non-US': 'Outside the U.S.', 'CN': 'China', 'DE': 'Germany', 'GB': 'United Kingdom', 'JP': 'Japan'}.get(s, s)
    return s

NORM = lambda m: re.sub(r'segment|[^a-z0-9]', '', m.lower())
def member_value(c, member, kind='seg_revenue'):
    for exact in (True, False):
        for ax, rows in c.get(kind, {}).items():
            for r in rows:
                if r['value'] is not None and (r['member'] == member if exact else NORM(r['member']) == NORM(member)): return r['value'], ax
    return None, None

def streams(c, cur):
    """The curated, non-overlapping revenue lines (label, value, note), largest first."""
    out = []
    for mem, lab, note in cur.get('rows', []):
        v, ax = member_value(c, mem)
        if v is not None and v > 0: out.append((lab, v, note))
    return sorted(out, key=lambda r: -r[1])

def seg_profit(c, cur):
    out = []
    for mem, lab in (cur.get('prows') or {}).items():
        v, ax = member_value(c, mem, 'seg_operating')
        if v is not None: out.append((lab, v, ''))
    return sorted(out, key=lambda r: -r[1]) if len(out) >= 2 else []

def margins(c, cur):
    """Gross margin per line where the 10-K gives both the line's revenue and its cost (e.g. Apple Services vs hardware)."""
    out = []
    for mem, lab in cur.get('margins', []):
        r, _ = member_value(c, mem); k, _ = member_value(c, mem, 'seg_cost')
        if r and k is not None: out.append((lab, r, k, (r - k) / r))
    return out

def latest(c, key):
    s = c['series'].get(key) or {}
    return s[max(s)] if s else None

def years(c, key):
    return sorted((c['series'].get(key) or {}).items())

def fy_label(end):
    return datetime.date.fromisoformat(end).strftime('%B %-d, %Y') if os.name != 'nt' else datetime.date.fromisoformat(end).strftime('%B %#d, %Y')

def build_model():
    out = {}
    for slug, c in RAW.items():
        cur = CURATED.get(slug, {})
        rev = latest(c, 'revenue')
        if not rev: continue
        end = max(c['series']['revenue'])
        st = streams(c, cur)
        ni = c['series'].get('net_income', {}).get(end)
        op = c['series'].get('operating_income', {}).get(end)
        gp = c['series'].get('gross_profit', {}).get(end)
        if gp is None and c['series'].get('cost_of_revenue', {}).get(end) is not None and slug not in ('jpmorgan-chase', 'bank-of-america', 'wells-fargo', 'goldman-sachs', 'berkshire-hathaway'):
            gp = rev - c['series']['cost_of_revenue'][end]
        emp = EMPLOYEES.get(slug)
        out[slug] = dict(slug=slug, name=c['name'], legal=c['legal'], ticker=c['ticker'], domain=c['domain'], sic=c.get('sic'), end=end, end_text=fy_label(end),
                         fy=cur.get('fy') or f"fiscal {end[:4]}" , form=c['filing']['form'], filed=c['filing']['filed'], url=c['filing']['url'], cik=c['cik'],
                         revenue=rev, net_income=ni, operating_income=op, gross_profit=gp, rnd=c['series'].get('rnd', {}).get(end),
                         rev_years=years(c, 'revenue'), ni_years=years(c, 'net_income'), op_years=years(c, 'operating_income'),
                         streams=st, seg_profit=seg_profit(c, cur), margins=margins(c, cur), employees=emp, cur=cur,
                         gross=member_value(c, cur['gross'][0])[0] if cur.get('gross') else None)
    return out

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    M = build_model(); only = sys.argv[1:]
    for s, m in M.items():
        if only and s not in only: continue
        b = lambda v: f'{v / 1e9:.1f}' if v is not None else '-'
        print(f"## {s} | {m['form']} {m['end']} | rev {b(m['revenue'])} op {b(m['operating_income'])} ni {b(m['net_income'])} gp {b(m['gross_profit'])} | emp {m['employees'][0] if m['employees'] else '-'}")
        tot = sum(v for _, v, _ in m['streams'])
        print('   streams', f"sum {b(tot)} = {tot / m['revenue']:.0%}" if m['streams'] else '', '|', '; '.join(f'{l} {b(v)}' for l, v, _ in m['streams'][:9]))
        if m['margins']: print('   margins', m['margins'])
        if m['seg_profit']: print('   seg op ', '; '.join(f'{l} {b(v)}' for l, v, _ in m['seg_profit'][:8]))

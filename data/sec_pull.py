# 11-08: pulls every company's real numbers from SEC EDGAR (the 10-K / 20-F / 40-F filings themselves), into data/companies.json.
#   py data/sec_pull.py            (cached raw files in data/sec/raw/, delete them to refresh)
# What comes out per company: 6 fiscal years of revenue, gross profit, operating income, net income, R&D; the latest annual report's
# revenue (and operating income) by segment / product / region, read from that filing's own XBRL; the employee count sentence
# from the report text; and the filing's URL, so every page can name its source.
import os, re, json, time, html, sys, datetime, urllib.request, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from companies_list import COMPANIES
UA = {'User-Agent': 'TheBusinessStudy research admin@thebusinessstudy.com', 'Accept-Encoding': 'identity'}
D = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(D, 'sec', 'raw'); os.makedirs(RAW, exist_ok=True)

def get(url, cache=None, binary=False):
    if cache and os.path.exists(cache): return open(cache, 'rb').read() if binary else open(cache, encoding='utf-8').read()
    for k in range(4):
        try:
            time.sleep(0.15); b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read(); break
        except Exception as e:
            if k == 3: raise
            time.sleep(2 + 3 * k)
    if cache: open(cache, 'wb').write(b)
    return b if binary else b.decode('utf-8', 'replace')

REV = ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'RevenuesNetOfInterestExpense',
       'RevenueFromContractWithCustomerIncludingAssessedTax', 'SalesRevenueGoodsNet', 'Revenue']
TAGS = {'revenue': REV, 'gross_profit': ['GrossProfit'], 'operating_income': ['OperatingIncomeLoss', 'ProfitLossFromOperatingActivities'],
        'net_income': ['NetIncomeLoss', 'ProfitLossAttributableToOwnersOfParent', 'ProfitLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic'], 'rnd': ['ResearchAndDevelopmentExpense', 'ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost'],
        'cost_of_revenue': ['CostOfRevenue', 'CostOfGoodsAndServicesSold', 'CostOfSales'], 'sga': ['SellingGeneralAndAdministrativeExpense']}
ANNUAL = ('10-K', '10-K/A', '20-F', '40-F', '10-KT')

def days(a, b): return (datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days

def annual_series(facts, names):
    """{period_end: (value, accn, filed)} for full-year values reported in annual reports; later filings win (restated numbers)."""
    for ns in ('us-gaap', 'ifrs-full'):
        for n in names:
            f = facts.get(ns, {}).get(n)
            if not f: continue
            units = f['units'].get('USD') or next(iter(f['units'].values()))
            out = {}
            for x in units:
                if x.get('form') not in ANNUAL or 'start' not in x or not 340 <= days(x['start'], x['end']) <= 380: continue
                if x['end'] not in out or x['filed'] > out[x['end']][2]: out[x['end']] = (x['val'], x['accn'], x['filed'])
            if out: yield n, out

def best_series(facts, names):
    """Pick the tag whose series reaches the most recent year (ties: the earlier tag in the list); fill older gaps from the others."""
    cands = list(annual_series(facts, names))
    if not cands: return None, {}
    cands.sort(key=lambda c: (-max(c[1]).__hash__() if False else 0, ))
    latest = max(max(s) for _, s in cands)
    main = next((n, s) for n, s in cands if max(s) == latest)
    merged = dict(main[1])
    for n, s in cands:
        for e, v in s.items(): merged.setdefault(e, v)
    return main[0], merged

def employees(text):
    pats = [r'([\d,]{3,}(?:\.\d+)?)\s+(?:[A-Za-z-]+\s+){0,4}?(?:employees|team members|associates|crew members|people|workers)',
            r'employ(?:ed|s)?\s+(?:approximately|about|over|more than|nearly|roughly)?\s*([\d,]{3,})']
    hits = []
    for p in pats:
        for m in re.finditer(p, text, re.I):
            n = int(m.group(1).replace(',', '').split('.')[0] or 0)
            if 500 <= n <= 3_000_000:
                s = text[max(0, m.start() - 160): m.end() + 120]
                hits.append((n, re.sub(r'\s+', ' ', s)))
    return hits

def doc_text(h):
    h = re.sub(r'(?is)<(script|style|ix:header)[^>]*>.*?</\1>', ' ', h)
    return html.unescape(re.sub(r'<[^>]+>', ' ', h))

def segments(cik, accn, primary, period_end):
    """Revenue and operating income by member of the segment / product / geography axes, for the filing's own fiscal year."""
    folder = f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn.replace("-", "")}/'
    idx = json.loads(get(folder + 'index.json', os.path.join(RAW, f'{accn}_index.json')))
    files = [f['name'] for f in idx['directory']['item']]
    inst = next((f for f in files if f.endswith('_htm.xml')), None) or next((f for f in files if f.endswith('.xml') and not re.search(r'_(cal|def|lab|pre)\.xml$|FilingSummary', f)), None)
    lab = next((f for f in files if f.endswith('_lab.xml')), None)
    if not inst: return {}, {}, {}
    x = get(folder + inst, os.path.join(RAW, f'{accn}_inst.xml'))
    labels = {}
    if lab:
        try:
            L = get(folder + lab, os.path.join(RAW, f'{accn}_lab.xml'))
            attrs = lambda t: dict(re.findall(r'([\w:]+)="([^"]*)"', t))
            loc = {}
            for m in re.finditer(r'<(?:link:)?loc([^>]*)/?>', L):
                a = attrs(m.group(1)); loc[a.get('xlink:label')] = a.get('xlink:href', '').split('#')[-1]
            res = {}
            for m in re.finditer(r'<(?:link:)?label([^>]*)>(.*?)</(?:link:)?label>', L, re.S):
                a = attrs(m.group(1)); res.setdefault(a.get('xlink:label'), {})[a.get('xlink:role', '').rsplit('/', 1)[-1]] = html.unescape(m.group(2)).strip()
            for m in re.finditer(r'<(?:link:)?labelArc([^>]*)/?>', L):
                a = attrs(m.group(1)); el = loc.get(a.get('xlink:from')); t = res.get(a.get('xlink:to'), {})
                if el and t:
                    name = re.sub(r'^[a-z0-9-]+_', '', el)
                    labels[name] = t.get('terseLabel') or t.get('label') or labels.get(name)
        except Exception as e: print('labels failed', e)
    ctx = {}
    for m in re.finditer(r'<(?:xbrli:)?context id="([^"]+)">(.*?)</(?:xbrli:)?context>', x, re.S):
        body = m.group(2)
        st = re.search(r'<(?:xbrli:)?startDate>([^<]+)<', body); en = re.search(r'<(?:xbrli:)?endDate>([^<]+)<', body)
        dims = re.findall(r'<xbrldi:explicitMember dimension="([^"]+)">([^<]+)<', body)
        typed = re.search(r'typedMember', body)
        if st and en and not typed: ctx[m.group(1)] = (st.group(1).strip(), en.group(1).strip(), tuple(dims))
    want = {'GrossProfit', 'CostOfGoodsAndServicesSold', 'CostOfRevenue', 'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'RevenuesNetOfInterestExpense', 'RevenueFromContractWithCustomerIncludingAssessedTax', 'Revenue', 'OperatingIncomeLoss', 'ProfitLossFromOperatingActivities', 'SegmentReportingInformationOperatingIncomeLoss'}
    rev, opi, cost = {}, {}, {}
    for m in re.finditer(r'<(us-gaap|ifrs-full):(\w+)\s+([^>]*?)contextRef="([^"]+)"([^>]*)>([^<]+)</\1:\2>', x):
        tag, cref, val = m.group(2), m.group(4), m.group(6)
        if tag not in want or cref not in ctx: continue
        st, en, dims = ctx[cref]
        dims = tuple(d for d in dims if not (d[0].endswith('ConsolidationItemsAxis') and d[1].endswith('OperatingSegmentsMember')))
        if en != period_end or not 340 <= days(st, en) <= 380 or len(dims) != 1: continue
        axis, mem = dims[0]
        try: v = float(val)
        except ValueError: continue
        sign = -1 if 'sign="-"' in m.group(3) + m.group(5) else 1
        name = mem.split(':')[-1]
        lab_ = labels.get(name) or labels.get(mem.replace(':', '_')) or re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', re.sub(r'Member$', '', name))
        bucket = rev if ('Revenue' in tag and 'Cost' not in tag) else opi if 'Operat' in tag else cost
        bucket.setdefault(axis.split(':')[-1], {}).setdefault(name, {'label': lab_, 'tags': {}})['tags'][tag] = sign * v
    def flat(b):
        out = {}
        for ax, mems in b.items():
            rows = []
            for name, d in mems.items():
                t = d['tags']; v = next((t[k] for k in ('GrossProfit', 'CostOfGoodsAndServicesSold', 'CostOfRevenue', 'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'RevenuesNetOfInterestExpense', 'RevenueFromContractWithCustomerIncludingAssessedTax', 'Revenue', 'OperatingIncomeLoss', 'SegmentReportingInformationOperatingIncomeLoss', 'ProfitLossFromOperatingActivities') if k in t), None)
                rows.append({'member': name, 'label': d['label'], 'value': v})
            out[ax] = sorted(rows, key=lambda r: -abs(r['value'] or 0))
        return out
    return flat(rev), flat(opi), flat(cost)

def main(only=None):
    tick = {v['ticker'].upper(): v for v in json.loads(get('https://www.sec.gov/files/company_tickers.json', os.path.join(RAW, 'company_tickers.json'))).values()}
    out = {}
    path = os.path.join(D, 'companies.json')
    if os.path.exists(path): out = json.load(open(path, encoding='utf-8'))
    for slug, t, legal, short, dom in COMPANIES:
        if only and slug not in only: continue
        try:
            CIK_OVERRIDE = {'exxon': 34088}   # 2026: XOM's ticker moved to a new holding company with no 10-K yet; the 10-Ks are still Exxon Mobil Corp's
            c = {'cik_str': CIK_OVERRIDE[slug]} if slug in CIK_OVERRIDE else tick.get(t.upper()) or tick.get(t.replace('-', '.').upper()) or tick.get(t.replace('-', '').upper())
            if not c: print(slug, 'NO TICKER'); continue
            cik = f'{c["cik_str"]:010d}'
            facts = json.loads(get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json', os.path.join(RAW, f'facts_{cik}.json')))['facts']
            sub = json.loads(get(f'https://data.sec.gov/submissions/CIK{cik}.json', os.path.join(RAW, f'sub_{cik}.json')))
            r = sub['filings']['recent']
            if not any(f in ANNUAL for f in r['form']):                 # very busy filers: older filings live in extra pages
                for extra in sub['filings'].get('files', []):
                    more = json.loads(get('https://data.sec.gov/submissions/' + extra['name'], os.path.join(RAW, extra['name'])))
                    for kk in r: r[kk] = r[kk] + more.get(kk, [])
                    if any(f in ANNUAL for f in more['form']): break
            k = next((i for i, f in enumerate(r['form']) if f in ('10-K', '20-F', '40-F', '10-KT')), None)   # the original report, not a 10-K/A
            if k is None: k = next(i for i, f in enumerate(r['form']) if f in ANNUAL)
            filing = {'form': r['form'][k], 'accn': r['accessionNumber'][k], 'filed': r['filingDate'][k], 'period': r['reportDate'][k], 'doc': r['primaryDocument'][k],
                      'url': f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{r["accessionNumber"][k].replace("-", "")}/{r["primaryDocument"][k]}'}
            series = {}; used = {}
            for key, names in TAGS.items():
                n, s = best_series(facts, names)
                if s and days(max(s), filing['period']) <= 400: series[key] = {e: v[0] for e, v in sorted(s.items())[-7:]}; used[key] = n
            # fiscal-year names as the company uses them (DocumentFiscalYearFocus of the annual report whose period ends there)
            fyname = {}
            dfy = facts.get('dei', {}).get('DocumentFiscalYearFocus', {}).get('units', {})
            for e in set().union(*[set(v) for v in series.values()]) if series else []:
                fyname[e] = None
            for i, f in enumerate(r['form']):
                if f in ANNUAL and r['reportDate'][i]: fyname.setdefault(r['reportDate'][i], None)
            text = doc_text(get(filing['url'], os.path.join(RAW, f'{filing["accn"]}_doc.htm')))
            emp = employees(text)
            fy_m = re.search(r'(?:fiscal\s+year\s+ended|fiscal\s+year\s+ending|for\s+the\s+(?:fiscal\s+)?year\s+ended)\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})', text)
            seg_rev, seg_op, seg_cost = segments(cik, filing['accn'], filing['doc'], filing['period'])
            out[slug] = {'slug': slug, 'ticker': t, 'legal': sub.get('name') or legal, 'name': short, 'domain': dom, 'cik': cik, 'filing': filing,
                         'fy_text': fy_m.group(1) if fy_m else None, 'fiscal_year_end': sub.get('fiscalYearEnd'), 'sic': sub.get('sicDescription'),
                         'series': series, 'tags': used, 'employees_hits': emp[:8], 'seg_revenue': seg_rev, 'seg_operating': seg_op, 'seg_cost': seg_cost}
            lr = series.get('revenue', {}); le = max(lr) if lr else None
            print(f'{slug:24} {filing["form"]} {filing["period"]} rev {lr.get(le, 0) / 1e9 if le else 0:8.1f}B  seg axes {list(seg_rev)[:3]}  emp {emp[0][0] if emp else "-"}')
        except Exception as e:
            print(slug, 'ERROR', repr(e)[:200])
        json.dump(out, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

if __name__ == '__main__': main(sys.argv[1:] or None)

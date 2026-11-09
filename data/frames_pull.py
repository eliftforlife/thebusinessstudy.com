# 11-08: every SEC filer's revenue and net income for the fiscal year closest to calendar 2025 (SEC XBRL "frames" API), limited to
# companies with a stock ticker (so subsidiaries and trusts drop out). -> data/rank_2025.json, used by /largest-companies/ and /most-profitable-companies/.
import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sec_pull import get, RAW, D
YEAR = 'CY2025'
REV = ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'RevenuesNetOfInterestExpense', 'RevenueFromContractWithCustomerIncludingAssessedTax']
def frame(tag):
    j = json.loads(get(f'https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/USD/{YEAR}.json', os.path.join(RAW, f'frame_{tag}_{YEAR}.json')))
    return {d['cik']: d for d in j['data']}
tick = {}
for v in json.loads(get('https://www.sec.gov/files/company_tickers.json', os.path.join(RAW, 'company_tickers.json'))).values():
    tick.setdefault(v['cik_str'], v)
tick.setdefault(34088, {'ticker': 'XOM', 'title': 'EXXON MOBIL CORP'})   # 2026 ticker moved to a holding company; the 10-K filer is still CIK 34088
rev = {}
for t in REV:
    for cik, d in frame(t).items():
        if cik in tick and (cik not in rev or d['val'] > rev[cik]['val']): rev[cik] = d
ni = frame('NetIncomeLoss')
try: assets = {d['cik']: d for d in json.loads(get(f'https://data.sec.gov/api/xbrl/frames/us-gaap/Assets/USD/{YEAR}Q4I.json', os.path.join(RAW, f'frame_Assets_{YEAR}Q4I.json')))['data']}
except Exception: assets = {}
rows = []
for cik, d in rev.items():
    n = ni.get(cik)
    if not str(d.get('loc', '')).startswith('US'): continue                         # US companies only (foreign filers may tag converted figures)
    a = assets.get(cik)
    if a and d['val'] > 15 * a['val']: continue                                     # revenue 15x the company's assets = a tagging slip, skip it
    if n and n['end'] != d['end']: n = None                                         # profit only when it's the same fiscal year
    rows.append({'cik': cik, 'name': tick[cik]['title'], 'ticker': tick[cik]['ticker'], 'loc': d.get('loc'), 'revenue': d['val'], 'rev_end': d['end'], 'rev_accn': d['accn'],
                 'net_income': n['val'] if n else None, 'ni_end': n['end'] if n else None})
rows.sort(key=lambda r: -r['revenue'])
json.dump({'frame': YEAR, 'pulled': __import__('datetime').date.today().isoformat(), 'rows': rows[:400]}, open(os.path.join(D, 'rank_2025.json'), 'w', encoding='utf-8'), indent=0)
for r in rows[:40]: print(f"{r['ticker']:6} {r['name'][:38]:38} {r['revenue']/1e9:8.1f}  {(r['net_income'] or 0)/1e9:7.1f}  {r['rev_end']}")
print(len(rows))

# Tell Bing and the other IndexNow engines which thebusinessstudy.com pages changed. Run after every push.  py indexnow.py [/path/ ...]  (no paths = every URL in the sitemap)
import json, re, sys, urllib.request
KEY = '6b1f3c2e9a8d4e7f9c0b5a1d2e3f4a5b'; HOST = 'thebusinessstudy.com'
urls = [f'https://{HOST}{p}' for p in sys.argv[1:]] or re.findall(r'<loc>([^<]+)</loc>', open('docs/sitemap.xml', encoding='utf-8').read())
assert urllib.request.urlopen(urllib.request.Request(f'https://{HOST}/{KEY}.txt', headers={'User-Agent': 'Mozilla/5.0'}), timeout=20).read().decode().strip() == KEY, 'key file not live'
for i in range(0, len(urls), 9000):
    body = json.dumps({'host': HOST, 'key': KEY, 'keyLocation': f'https://{HOST}/{KEY}.txt', 'urlList': urls[i:i + 9000]}).encode()
    r = urllib.request.urlopen(urllib.request.Request('https://api.indexnow.org/indexnow', data=body, headers={'Content-Type': 'application/json; charset=utf-8'}), timeout=60); print(r.status, len(urls[i:i + 9000]), 'URLs')

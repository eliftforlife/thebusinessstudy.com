# elijahwestbrook.com

Free data studies by Elijah Westbrook. Static site, served by GitHub Pages from `main` → `/docs`.

- `content.py`: every study (numbers come from each study's claim check in the YouTube project folder)
- `build.py`: `py build.py` regenerates `docs/` (pages, sitemap.xml, robots.txt, llms.txt, CNAME)
- `assets/`: `site.css`; `node make_assets.mjs` re-renders `icon.png` and `og.png`
- Preview: `py -m http.server 8812` inside `docs/`, then `node _shots.mjs` for desktop + phone screenshots

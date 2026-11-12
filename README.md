# thebusinessstudy.com

How companies make money, from their own annual reports. Static site, served by GitHub Pages from `main` → `/docs`.

- `data/sec_pull.py`: pulls each company's 10-K numbers from SEC EDGAR (XBRL company facts + the filing's own segment data + the employee sentence) into `data/companies.json`. Raw downloads are cached in `data/sec/raw/` (not committed).
- `data/frames_pull.py`: every U.S. public company's 2025 revenue and profit (SEC frames) into `data/rank_2025.json` for the rankings.
- `data/companies_list.py` (which companies), `data/curated.py` (hand-checked employee counts), `data/curated_rows.py` (which revenue lines to show, labels, one plain sentence per company), `data/model.py` (turns it all into page numbers).
- `content.py`: the older creator data studies. `data/videos.json`: Business Study videos to embed per company.
- `build.py`: `py build.py` regenerates `docs/` (pages, sitemap, robots, llms.txt, IndexNow key, `assets/data/co.json` for the compare tool and game).
- `logos.py` / `logos2.py`: company site icons, shown only on that company's own page and its compare pages.
- Preview: the `businessstudy-v2` config in the project's `.claude/launch.json` (port 8847), then `MSYS_NO_PATHCONV=1 node _shots.mjs /path/` for desktop + phone screenshots.
- After a push: `py indexnow.py` (Bing, Yandex and others).
- `data/filing_updates.json`: written by the EDGAR watch (`0 HQ/Tools/edgar_watch.py`, Windows task "Westbrook EDGAR watch"). When a company files a new 10-K or 10-Q it re-pulls that company, rebuilds, commits only the changed files from its own worktree and pings IndexNow; the company page then says "Updated after the Form X filed <date>".

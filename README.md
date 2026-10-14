# Bay Area Hardware & Mechanical Job Puller

Private application tracker: [Google Sheets](https://docs.google.com/spreadsheets/d/1uy2bZwnVGelp7PbFo7xltleZS1Atpqz648Wc67yDrT4/edit)

## What it searches

- 37 configured employer sources, including startups using Ashby/Greenhouse and major employers: Apple, Tesla, Microsoft, Google, NVIDIA, Intel and Adobe.
- Bay Area full-time mechanical/product design, robotics mechanisms, equipment/process engineering, EV and batteries, NPI/manufacturing and reliability roles.
- New graduate / 0–3 years of required experience; excludes explicit 4+ year requirements, senior titles, HVAC, medical devices, and software-only roles.
- Published **base salary ranges whose upper bound is at least $140,000**. Jobs without disclosed salary remain in review.
- Resume-fit ranking based on manufacturing equipment, Ford/Tesla automotive experience, FSAE EV battery design, robotics, FEA, GD&T and CAD.

## Run and verify

The workflow [Daily Bay Area engineering jobs](https://github.com/aramasubban/job-puller/actions/workflows/daily.yml) automatically scans after source changes, can be launched manually, and is scheduled daily at 14:23 UTC (6:23 a.m. PST / 7:23 a.m. PDT). GitHub scheduled run times are not exact.

1. Inspect a completed Actions run (success should include the **Fetch employer job listings** and **Validate feed and save public results** steps).
2. Open [data/jobs.json](data/jobs.json) and check `sources_checked`, `sources_failed`, `source_status` (per-employer status) and the actual `jobs` array.
3. **Do not assume all companies are covered**: Apple/Tesla/Google/Microsoft HTML search and NVIDIA/Intel/Adobe Workday adapters are experimental and may fail due to website changes, anti-automation measures, or missing jobs. Source status `OK — partial` is **not exhaustive coverage**.
4. When the first public feed exists, open the private [Google Sheet](https://docs.google.com/spreadsheets/d/1uy2bZwnVGelp7PbFo7xltleZS1Atpqz648Wc67yDrT4/edit), choose **Extensions → Apps Script**, replace the code with [google_apps_script/Code.gs](google_apps_script/Code.gs), save, and run `setupTracker` then `activateTracker`. Google will ask you to approve permissions. The latter starts a daily 9 a.m. Pacific sheet sync. ChatGPT cannot install Apps Script directly into your Google account via this connection.
5. Click a posting title in the Jobs or Apply Next tab to open the employer listing. Set YOUR STATUS to Not Applied / Applied / Interviewing / Offer / Rejected / Not Interested. Application notes, date and statuses stay private in the Google Sheet and survive repeated syncs.

**Job listings are not automatically applied to.** The title links lead to the employer career page; an extra Apply action and/or account sign-in may be required.

## Safety

**Do not add resume files, personal contact info, Google authorization secrets, or application status data to this public repository.** Only employer-published job listing metadata belongs in `data/jobs.json`.

Source health is surfaced explicitly. A complete source failure does not erase previously seen rows. An empty valid ATS board can be a legitimate success; a rejected or malformed board is marked as error.

## Development

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m src.puller
```

The standalone job collector does not require paid job data or API keys. Large-employer coverage is **best effort, not comprehensive**, and should be checked against official career pages until validated.

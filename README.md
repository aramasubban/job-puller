# Bay Area Hardware & Mechanical Job Puller

Private application tracker: [Google Sheets](https://docs.google.com/spreadsheets/d/1uy2bZwnVGelp7PbFo7xltleZS1Atpqz648Wc67yDrT4/edit)

## What it searches

- 36 configured employer sources, including startups using Ashby/Greenhouse and major employers: Apple, Microsoft, Google, NVIDIA, Intel and Adobe. **Tesla is intentionally excluded** while its public career feed blocks automation.
- Bay Area full-time mechanical/product design, robotics mechanisms, equipment/process engineering, EV and batteries, NPI/manufacturing and reliability roles.
- New graduate / 0–3 years of required experience; excludes explicit 4+ year requirements, senior titles, HVAC, medical devices, and software-only roles.
- Published **base salary ranges whose upper bound is at least $140,000**. Jobs without disclosed salary remain in review.
- Resume-fit ranking based on manufacturing equipment, Ford/Tesla automotive experience, FSAE EV battery design, robotics, FEA, GD&T and CAD.

## Run and verify

The workflow [Daily Bay Area engineering jobs](https://github.com/aramasubban/job-puller/actions/workflows/daily.yml) automatically scans after source changes, can be launched manually, and is scheduled daily at 14:23 UTC (6:23 a.m. PST / 7:23 a.m. PDT). GitHub scheduled run times are not exact.

1. Inspect a completed Actions run (success should include the **Fetch employer job listings** and **Validate feed and save public results** steps).
2. Open [data/jobs.json](data/jobs.json) and check `sources_checked`, `sources_failed`, `source_status` (per-employer status) and the actual `jobs` array.
3. **Do not assume all companies are covered**: Apple and Microsoft use public JSON career feeds, Google uses its published sitemap and job pages, and NVIDIA/Intel/Adobe use Workday adapters. Results are partial or may fail due to website changes, access restrictions, or limits. Tesla is not scanned. Source status `OK — partial` is **not exhaustive coverage**.
4. When the first public feed exists, open the private [Google Sheet](https://docs.google.com/spreadsheets/d/1uy2bZwnVGelp7PbFo7xltleZS1Atpqz648Wc67yDrT4/edit), choose **Extensions → Apps Script**, replace the code with [google_apps_script/Code.gs](google_apps_script/Code.gs), save, and run `setupTracker` then `activateTracker`. Google will ask you to approve permissions. The latter starts a daily 9 a.m. Pacific sheet sync. ChatGPT cannot install Apps Script directly into your Google account via this connection.
**Apps Script editor error workaround:** If **Extensions → Apps Script** says "Sorry, unable to open the file at this time", verify the Google account matches the Sheet's owner, then open [script.google.com/home/projects/create](https://script.google.com/home/projects/create) in that account to create a **standalone** project. Paste `google_apps_script/Code.gs`, save, run `setupTracker`, approve authorization, then run `activateTracker`. The script uses the explicit Sheet ID and installs the scheduled sync plus an edit trigger in standalone mode. Do not create a new spreadsheet; the script writes to the existing tracker.

5. The private Google Sheet shows **three visible tabs: Jobs, Apply Next, Dashboard**. Demo and Start Here are removed; Run Log and Coverage are hidden to preserve compatibility with the already-authorized daily Apps Script. To inspect the latter, unhide them from Google Sheets' View menu. Click a posting title in the Jobs or Apply Next tab to open the employer listing. Set YOUR STATUS to Not Applied / Applied / Interviewing / Offer / Rejected / Not Interested. Application notes, date and statuses stay private in the Google Sheet and survive repeated syncs.

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

## Microsoft pacing and completeness

Microsoft returns HTTP 429 (too many requests) at times. The Microsoft collector spaces requests by at least six seconds, limits description/detail calls to four per run, and reports a 429 as a failed source (never an empty, successful board). No credentials, rate-limit bypasses, or aggressive retries are used. A successful 0-match result is still marked **OK — partial** because the search only samples specific query terms and pages.


## Mechanical fit scoring (me-v2)

Scores are heuristic prioritization, not hiring probabilities. Pay is screened separately and contributes no fit points. Scoring uses role duties and required qualifications, strips company introductions and preferred-only sections, and bounds discipline (35), mechanical-duty breadth (30), demonstrated tool groups (20), and early-career alignment (15). Scores cap at 95, unknown career level at 79, two-year requirements at 74, three-year requirements at 64, and ECE-dominant work at 25. Incomplete descriptions and graduation-window conflicts stay out of the shortlist. Explicit new-grad exceptions are recognized. Specialist motor roles carry an experience-gap warning. Repetition of keywords never adds points.

Apply Next uses a native numeric filter of 70+ so plausible stretches remain visible with their gaps; all original records remain in Jobs. This filter persists when the existing Apps Script refreshes cell contents. Fit evidence includes missing requirements, not just positive keyword matches. Scores from an old model on a failed source are demoted pending description review, rather than retaining stale 100s. Listings with only employer introductions (some Apple records) remain low-confidence; they are not proof of a technical mismatch.

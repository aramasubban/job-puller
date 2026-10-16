# Bay Area Mechanical Engineering Job Tracker

Private tracker: https://docs.google.com/spreadsheets/d/1uy2bZwnVGelp7PbFo7xltleZS1Atpqz648Wc67yDrT4/edit

## Refresh policy
Collector: Monday, Wednesday and Friday at 14:23 UTC, before the spreadsheet refresh. Manual workflow dispatch remains available. Code pushes do not launch extra scans.
Spreadsheet: Monday, Wednesday and Friday at 9 a.m. America/Los_Angeles, managed by the existing ChatGPT task. No competing Apps Script clock trigger is needed.

Jobs must score **at least 50/100**. The collector filters fresh jobs and retained failed-source records. `filtered_out_job_ids` identifies previously tracked jobs below the cutoff. Reconciliation removes excluded unsubmitted rows while preserving application history in Applied. Match by Job ID, preserve status, applied date, follow-up, notes and first-seen date, and deduplicate across both tabs. Do not recreate Apply Next.

## Search scope
54 sources, including existing employers plus Bedrock Robotics, Skydio, Figure, Zipline, 1X, Astranis, Saronic, Dexterity, Form Energy, Hadrian, Agility Robotics, Zoox, Lucid Motors, Redwood Materials, Nuro, Waymo, Saildrone and Antora Energy.

Bay Area full-time new-grad / 0–3 year mechanical design, mechanisms, equipment, manufacturing, NPI, automotive/battery, thermal hardware, testing and reliability. Exclude Tesla, medical devices, building HVAC, software-only roles, senior titles and explicit 4+ year minimums. Disclosed annual base salary must have an upper band of at least $140,000. Undisclosed pay requires review.

Public company context and career URLs live in the source configuration/feed and are displayed in Coverage. Context explains engineering relevance. Fame, funding and pay add no fit points. Covered companies can have zero qualifying jobs.

## Mechanical fit
The `me-v2` model scores actual duties and required qualifications: discipline (35), mechanical-duty breadth (30), demonstrated tool groups (20), early-career alignment (15). Scores cap at 95, unknown level at 79, two-year requirements at 74, three-year requirements at 64, and ECE-dominant work at 25. Graduation and specialist gaps appear in evidence. Scores prioritize review and are not hiring probabilities.

## Source health
Check generated_at, sources_checked, sources_failed, source_status, minimum_fit_score, filtered_out_job_ids and jobs in data/jobs.json. Failed sources retain eligible previous rows without advancing last_seen. All-source failure retains the previous feed. Missing rows from partial or failed searches are not evidence of closure. Large-employer and HTML coverage is partial. Microsoft is paced; 429 is reported without aggressive retries.

Read live workbook metadata and rows before writes; verify totals, private fields, links, validation, scores and unique IDs afterward. The repository Apps Script source has equivalent safeguards for future installs. Committing it does not deploy the live Google script. The scheduled task reconciles through connected Sheets independently.

## Run locally
```bash
pip install beautifulsoup4
python -m unittest discover -s tests -v
python -m src.puller
```

## Privacy
Only employer-published listing metadata belongs here. Never commit statuses, application notes/dates, resumes, contact information or authorization secrets. Never apply for jobs or contact employers automatically.


## Regional search
Search Bay Area and Greater LA, including LA/Orange County, Ventura and Antelope Valley/Mojave aerospace hubs. Bay Area and LA are live formula views over the Jobs working records; use their Edit status / notes links. Applied and Interviews are combined. Never count regional view rows as additional applications. Keep M/W/F cadence, fit >=50, base-salary upper band >=$140k when disclosed, and existing exclusions. Installing source changes in this repository does not deploy Apps Script.

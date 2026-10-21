#!/usr/bin/env python3
"""Daily, no-key job puller for early-career Bay Area mechanical/hardware roles.

Pulls only employer-published Greenhouse, Ashby and Lever boards. A source can
fail without hiding previously found jobs or falsely labeling them closed.
"""
from __future__ import annotations

import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from src.matching import score_match, VERSION as MATCH_VERSION
from src.enrichment import enrich, SECTOR_COMPANIES, SECTOR_TITLES
from src.direct_employers import fetch_official_html, fetch_workday, fetch_amazon, fetch_icims
from src.enterprise_sources import fetch_apple, fetch_microsoft, fetch_google, fetch_tesla
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "boards.json"
JSON_OUT = ROOT / "data" / "jobs.json"
CSV_OUT = ROOT / "data" / "jobs.csv"
MIN_FIT_SCORE = 50
USER_AGENT = "BayAreaEarlyCareerEngineeringJobs/1.0 (public job feeds; daily refresh)"

# Whole-word and explicit locale matching: 'California', 'United States', and
# bare 'Remote' alone do NOT qualify as Bay Area locations.
BAY_AREA_PATTERNS = [
    r"\bsan francisco\b", r"\bsf bay area\b", r"\bbay area\b", r"\bsouth san francisco\b",
    r"\bsan jose\b", r"\bsanta clara\b", r"\bsunnyvale\b", r"\bmountain view\b",
    r"\bpalo alto\b", r"\bmenlo park\b", r"\bredwood city\b", r"\bsan mateo\b", r"\bsanta cruz\b", r"\bscotts valley\b",
    r"\bfoster city\b", r"\bburlingame\b", r"\bsan bruno\b", r"\bbelmont\b",
    r"\bsan carlos\b", r"\bcupertino\b", r"\bmilpitas\b", r"\bfremont\b",
    r"\bnewark\b", r"\bunion city\b", r"\bhayward\b", r"\boakland\b",
    r"\bberkeley\b", r"\bemeryville\b", r"\balameda\b", r"\bsan leandro\b",
    r"\bpleasanton\b", r"\bdublin\b", r"\blivermore\b", r"\bsan ramon\b",
    r"\bwalnut creek\b", r"\bconcord\b", r"\brichmond\b", r"\bvallejo\b",
    r"\bfairfield\b", r"\bbenicia\b", r"\bsan rafael\b", r"\bsausalito\b",
    r"\bmarin county\b", r"\bnovato\b", r"\bpetaluma\b", r"\bsanta rosa\b",
    r"\bsonoma\b", r"\bnapa\b", r"\bsolano county\b",
    r"\blos altos\b", r"\blos gatos\b", r"\bsaratoga\b", r"\bcampbell\b",
    r"\bhalf moon bay\b", r"\bpacifica\b", r"\beast palo alto\b",
]
BAY_AREA = re.compile("|".join(BAY_AREA_PATTERNS), re.IGNORECASE)
LA_CITIES = ["los angeles", "el segundo", "hawthorne", "torrance", "gardena", "redondo beach", "manhattan beach", "hermosa beach", "long beach", "carson", "inglewood", "culver city", "santa monica", "pasadena", "altadena", "burbank", "glendale", "sylmar", "chatsworth", "canoga park", "woodland hills", "northridge", "san fernando", "santa clarita", "valencia", "palmdale", "lancaster", "mojave", "costa mesa", "irvine", "tustin", "huntington beach", "newport beach", "santa ana", "anaheim", "fullerton", "orange county", "lake forest", "foothill ranch", "seal beach", "cypress", "brea", "thousand oaks", "simi valley", "camarillo", "oxnard", "ventura"]
LA_PATTERNS = [r"\b"+re.escape(city)+r"\b" for city in LA_CITIES]
GREATER_LA = re.compile("|".join(LA_PATTERNS), re.IGNORECASE)
TARGET_AREA = re.compile("|".join(BAY_AREA_PATTERNS + LA_PATTERNS), re.IGNORECASE)
def job_regions(location):
    regions=[]
    for segment in re.split(r";|\n|\s/\s",location or ""):
        if re.search(r"\b(?:New Jersey|New York|Virginia|Texas|Ohio|Massachusetts|NJ|NY|VA|TX|OH|MA)\b",segment,re.I):continue
        if BAY_AREA.search(segment) and 'Bay Area' not in regions:regions.append('Bay Area')
        if GREATER_LA.search(segment) and 'LA' not in regions:regions.append('LA')
    return regions


# Avoid software-only robotics positions: titles need a physical/hardware hook.
ROLE_PATTERN = re.compile(
    r"\b(mechanical|mechatron(?:ic|ics)?|manufactur(?:ing|ability)|npi|"
    r"design engineer|product design engineer|product development engineer|thermal|tooling|"
    r"process engineer|production engineer|industrial engineer|equipment engineer|"
    r"hardware (?:design|test|development|integration|systems?)|"
    r"electromechanical|robotics? (?:engineer|hardware|integration)|"
    r"automation engineer|battery engineer|mechanism(?:s)? engineer|quality engineer|reliability engineer|test engineer|"
    r"propulsion engineer|structures engineer|fluids? engineer|vehicle integration engineer|cad (?:engineer|designer)|structural engineer)\b", re.IGNORECASE
)
NON_ENGINEERING = re.compile(
    r"\b(technician|inspector|planner|temporary|intern(?:ship)?|co[ -]?op|apprentice|contractor|"
    r"recruiter|technologist|research scientist|designer,? ux|product manager|"
    r"software engineer|firmware engineer|front[ -]?end|back[ -]?end|"
    r"data engineer|machine learning engineer|sales engineer|"
    r"engineering manager|program manager|project manager|director|"
    r"vice president|head of|chief of|operations manager)\b", re.IGNORECASE
)
SENIOR = re.compile(r"\b(senior|sr\.?|staff|principal|lead|manager|director|architect|expert|head of)\b", re.IGNORECASE)
ENTRY = re.compile(r"\b(new grad(?:uate)?|graduate|entry.level|early.career|junior|associate|engineer i\b|engineer 1\b)\b", re.IGNORECASE)
EXP = re.compile(r"(?<!\d)(\d{1,2})\s*(?:\+|[-–—]\s*(\d{1,2})|\s+to\s+(\d{1,2}))?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:(?:[A-Za-z][A-Za-z/-]*\s+){0,5})?experience\b", re.IGNORECASE)
EXP_BEFORE = re.compile(r"\b(?:minimum(?: of)?|at least|require[ds]?|have|possess|with)\s+(\d{1,2})\+?\s*(?:years?|yrs?)\b", re.IGNORECASE)

class _StripHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)
    def text(self):
        return re.sub(r"\s+", " ", unescape(" ".join(self.parts))).strip()

def plain(value):
    if not value:
        return ""
    value = unescape(unescape(str(value)))
    if "<" not in value:
        return re.sub(r"\s+", " ", unescape(value)).strip()
    h = _StripHTML()
    h.feed(value)
    return h.text()

def is_bay_area(location):
    return bool(BAY_AREA.search(location or ""))

def required_experience_years(description):
    # Never let an entry-level title override an explicit 4+ year minimum.
    # Only explicit 'years of experience' or 'minimum X years' phrases;
    # does not mistake 'founded 5 years ago' for a requirement.
    text = description[:25000]
    # Preferred/nice-to-have years are not a mandatory minimum. When a board
    # provides heading-style qualification sections, screen the required text.
    text = re.split(r'\b(?:preferred|nice[- ]to[- ]have|bonus)\s+(?:qualifications|requirements|experience)\b',text,maxsplit=1,flags=re.I)[0]
    minima = [int(m.group(1)) for pattern in (EXP, EXP_BEFORE) for m in pattern.finditer(text)]
    minima += [int(m.group(1)) for m in re.finditer(
        r'(?<!\d)(\d{1,2})\+?\s+years?\s+(?:in|of professional|of hands.on|designing|building|developing|working|leading|managing|taking)\b', text, re.I)]
    minima += [int(m.group(1)) for m in re.finditer(r'(?<!\d)(\d{1,2})\s+or more\s+years?\s+(?:of\s+)?(?:[\w/-]+\s+){0,5}experience\b', text, re.I)]
    minima += [int(m.group(1)) for m in re.finditer(r"bachelor.{0,40}?related work experience of\s+(\d+)", description, re.I)]
    return max(minima, default=0)

def experience_fit(title, description):
    minimum = required_experience_years(description)
    if minimum > 3:
        return "EXCLUDE"
    if ENTRY.search(title):
        return "New grad / early career" if not minimum else "0–3 years specified"
    if minimum:
        return "0–3 years specified"
    return "Experience not stated — review"

def role_family(title):
    t = title.lower()
    if re.search(r"manufactur|npi|process engineer|production engineer|industrial engineer|quality engineer|tooling", t):
        return "Manufacturing / NPI"
    if re.search(r"robot|mechatron|automation|electromechanical", t):
        return "Robotics / mechatronics"
    if re.search(r"design|cad|product|mechanical|structural|thermal|hardware", t):
        return "Mechanical / hardware design"
    return "Hardware test / reliability"

def exclusion_reasons(job):
    title = job.get("title", "") or ""
    desc = job.get("description", "") or ""
    location = job.get("location", "") or ""
    etype = (job.get("employment", "") or "").lower().replace(" ", "").replace("-", "")
    reasons = []
    if SECTOR_COMPANIES.search(job.get("company", "")) or SECTOR_TITLES.search(title):
        reasons.append("Excluded sector/company")
    if not job_regions(location):
        reasons.append("Outside Bay Area / Greater LA")
    if not ROLE_PATTERN.search(title) or NON_ENGINEERING.search(title):
        reasons.append("Outside full-time physical engineering scope")
    if SENIOR.search(title):
        reasons.append("Senior/staff/lead title")
    if re.search(r'\b(?:ph\.?d|masters? degree)\b',title,re.I):
        reasons.append('Graduate-degree cohort conflicts with bachelor-level target')
    if etype and etype not in ("fulltime", "regular", "permanent", "unspecified"):
        reasons.append("Not full-time permanent employment")
    # For Greenhouse with no structured employment type, reject explicit
    # internship or temporary wording in the title; full-time is unverified.
    minimum = required_experience_years(desc)
    if minimum > 3:
        reasons.append(f"Requires {minimum}+ years; maximum required experience is 3")
    return reasons

def qualifies(job):
    return not exclusion_reasons(job)

class ScreenedJobs(list):
    """List-compatible result with public evidence explaining filtered roles."""
    def __init__(self, raw_count=0):
        super().__init__()
        self.raw_count = raw_count
        self.excluded_roles = []

    def record_exclusion(self, job, reasons):
        if not job_regions(job.get('location', '')) or not ROLE_PATTERN.search(job.get('title', '')):
            return
        if NON_ENGINEERING.search(job.get('title', '')):
            return
        self.excluded_roles.append({k: job.get(k, '') for k in
            ('id', 'company', 'title', 'location', 'source', 'source_url')} | {'reasons': reasons})

def _download(url, timeout=18):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for retry in range(3):
        try:
            with urlopen(req, timeout=timeout) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError, ValueError) as error:
            if retry == 2 or isinstance(error, HTTPError) and error.code in (400, 401, 403, 404):
                raise
            time.sleep(retry + 1)

def source_key(src):
    return f"{src['provider']}:{src.get('slug') or src.get('tenant') or src['company'].lower()}"

def parse_board(src, payload):
    p, slug = src["provider"], src["slug"]
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else payload
    if not isinstance(jobs, list):
        raise ValueError("Job API did not return a list")
    parsed = ScreenedJobs(len(jobs))
    for j in jobs:
        if not isinstance(j, dict):
            continue
        if p == "ashby":
            if j.get("isListed") is False:
                continue
            locs = [j.get("location", "")]
            locs += [x.get("location", "") for x in j.get("secondaryLocations", []) if isinstance(x, dict)]
            location = "; ".join(dict.fromkeys(x for x in locs if x))
            url = j.get("jobUrl") or j.get("applyUrl") or ""
            ext_id = urlsplit(url).path.strip("/").split("/")[-1] if url else ""
            description = j.get("descriptionPlain") or j.get("descriptionHtml") or ""
            employment = j.get("employmentType") or "Unspecified"
            workstyle = j.get("workplaceType") or ("Remote" if j.get("isRemote") else "Unknown")
            compensation = (j.get("compensation") or {}).get("scrapeableCompensationSalarySummary", "")
            published = j.get("publishedAt", "")
        elif p == "greenhouse":
            loc = j.get("location") or {}
            location = loc.get("name", "") if isinstance(loc, dict) else str(loc)
            url = j.get("absolute_url", "")
            ext_id = str(j.get("id", ""))
            description = j.get("content", "")
            employment = "Unspecified"
            workstyle = "Unknown"
            soup = BeautifulSoup(unescape(unescape(description)), "html.parser")
            pay_blocks = soup.select(".pay-input")
            base_blocks = [b for b in pay_blocks if not re.search(r"total compensation|equity|bonus", b.select_one(".title").get_text(" ", strip=True) if b.select_one(".title") else "", re.I)]
            compensation = " ".join(b.select_one(".pay-range").get_text(" ", strip=True) for b in base_blocks if b.select_one(".pay-range"))
            for block in pay_blocks:
                if block not in base_blocks: block.decompose()
            description = str(soup)
            published = j.get("updated_at", "")
        elif p == "lever":
            categories = j.get("categories") or {}
            locs = [categories.get("location", "")]
            locs += [v for v in categories.get("allLocations", []) if isinstance(v, str)]
            locs += [v for v in j.get("additionalLocations", []) if isinstance(v, str)]
            location = "; ".join(dict.fromkeys(x for x in locs if x))
            url = j.get("hostedUrl") or j.get("applyUrl") or ""
            ext_id = str(j.get("id", ""))
            description = j.get("descriptionPlain") or j.get("description") or ""
            if j.get("lists"):
                description += " " + " ".join(plain(x.get("content", "")) for x in j["lists"] if isinstance(x, dict))
            employment = categories.get("commitment", "Unspecified")
            workstyle = j.get("workplaceType", "Unknown")
            compensation = (j.get("salaryRange") or {}).get("text", "")
            pay_range = j.get("salaryRange") or {}
            if not compensation and pay_range.get("currency") == "USD" and pay_range.get("interval") == "per-year-salary":
                low, high = pay_range.get("min"), pay_range.get("max")
                if isinstance(low, (int, float)) and isinstance(high, (int, float)):
                    compensation = f"${low:,.0f}–${high:,.0f} base / year"
            published = ""
        else:
            raise ValueError("Unexpected provider: " + p)
        title = plain(j.get("title") or j.get("text") or "")
        if not url or not title:
            continue
        ext_id = ext_id or urlsplit(url).path.strip("/")
        description = plain(description)
        record = {
            "id": f"{p}:{slug}:{ext_id}", "company": src["company"],
            "title": title, "category": role_family(title),
            "location": location, "workstyle": workstyle,
            "employment": employment, "experience_fit": experience_fit(title, description),
            "salary": str(compensation or ""), "posted": str(published or ""),
            "apply_url": j.get("applyUrl") or url, "source_url": url,
            "source": source_key(src),
        }
        reasons = exclusion_reasons({**record, "description": description})
        if reasons:
            parsed.record_exclusion(record, reasons)
            continue
        enriched = enrich(record, description)
        if enriched is None:
            parsed.record_exclusion(record, ["Disclosed annual base upper band below $140,000"])
        else:
            parsed.append(enriched)
            if not meets_fit_floor(enriched):
                parsed.record_exclusion(enriched, [f"ME fit {enriched['fit_score']}/100 below 50", enriched['match_reasons']])
    return parsed

def stable_external_id(src, url):
    """Stable posting identifier; don't collapse Apple's distinct job numbers by slug."""
    segments=urlsplit(url).path.strip('/').split('/')
    if src.get('provider')=='apple_api' and 'details' in segments:
        idx=segments.index('details')+1
        if idx<len(segments):
            return segments[idx]
    return segments[-1]

def fetch_source(src):
    p=src["provider"]
    if p in ('apple_api','microsoft_eightfold','google_sitemap','tesla_api'):
        getter={'apple_api':fetch_apple,'microsoft_eightfold':fetch_microsoft,
                'google_sitemap':fetch_google,'tesla_api':fetch_tesla}[p]
        items=getter(src,ROLE_PATTERN,SENIOR,NON_ENGINEERING,TARGET_AREA)
        rows=[]
        for item in items:
            title=item['title'];description=plain(item.get('description',''))
            rec={'id':source_key(src)+':'+stable_external_id(src,item['url']),
                 'company':src['company'],'title':title,'category':role_family(title),
                 'location':item['location'],'workstyle':'Unknown',
                 'employment':item.get('employment','Unspecified'),
                 'experience_fit':experience_fit(title,description),
                 'salary':str(item.get('salary') or ''),'posted':item.get('posted',''),
                 'apply_url':item['url'],'source_url':item['url'],'source':source_key(src)}
            if qualifies({**rec,'description':description}):
                enriched=enrich(rec,description)
                if enriched is not None:rows.append(enriched)
        return rows
    if p in ('workday','official_html','amazon','icims'):
        if p=='workday':
            items,detail=fetch_workday(src,ROLE_PATTERN,SENIOR,NON_ENGINEERING,TARGET_AREA)
        elif p=='official_html':
            items,detail=fetch_official_html(src,ROLE_PATTERN,SENIOR,NON_ENGINEERING,TARGET_AREA)
        else:
            items,detail=({'amazon':fetch_amazon,'icims':fetch_icims}[p])(src,ROLE_PATTERN,SENIOR,NON_ENGINEERING,TARGET_AREA)
        rows=ScreenedJobs(detail.get('candidate_links',len(items)))
        for item in items:
            title=item['title']
            description=plain(item.get('description',''))
            rec={
                'id':source_key(src)+':'+str(item.get('external_id') or urlsplit(item['url']).path.strip('/').split('/')[-1]),
                'company':src['company'],'title':title,'category':role_family(title),
                'location':item['location'],'workstyle':'Unknown',
                'employment':item.get('employment','Unspecified'),
                'experience_fit':experience_fit(title,description),
                'salary':item.get('salary',''),'published_starting_pay':item.get('published_starting_pay'),'posted':item.get('posted',''),
                'apply_url':item['url'],'source_url':item['url'],'source':source_key(src)
            }
            reasons=exclusion_reasons({**rec,'description':description})
            if not reasons:
                rich=enrich(rec,description)
                if rich: rows.append(rich)
            else: rows.record_exclusion(rec,reasons)
        rows[:] = list({j['id']:j for j in rows}.values())
        return rows
    slug=quote(src['slug'],safe='')
    if p=='ashby': url=f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
    elif p=='greenhouse': url=f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    elif p=='lever': url=f"https://api.lever.co/v0/postings/{slug}?mode=json"
    else: raise ValueError('Unsupported provider: '+p)
    return parse_board(src,_download(url))

def meets_fit_floor(job):
    """Apply the same floor to fresh jobs and retained failed-source records."""
    try:
        return float(job.get("fit_score", 0)) >= MIN_FIT_SCORE
    except (TypeError, ValueError):
        return False

def run():
    sources = json.loads(CONFIG.read_text(encoding="utf-8"))
    previous = {}
    if JSON_OUT.exists():
        try:
            previous = json.loads(JSON_OUT.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    found = {}
    successful = []
    failed = []
    source_status = []
    excluded_roles = []
    filtered_out = set()
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fetch_source, src): src for src in sources}
        for fut in as_completed(futures):
            src = futures[fut]
            key = source_key(src)
            try:
                raw_results = fut.result()
                filtered_out.update(j['id'] for j in raw_results if j.get('id') and not meets_fit_floor(j))
                results = [j for j in raw_results if meets_fit_floor(j)]
                audit = getattr(raw_results, 'excluded_roles', [])
                excluded_roles.extend(audit)
                filtered_out.update(j['id'] for j in audit if j.get('id'))
                successful.append(key)
                source_status.append({"source":key,"company":src["company"],"state":"OK — partial" if src["provider"] in ("workday","official_html","amazon","icims","apple_api","microsoft_eightfold","google_sitemap","tesla_api") else "OK","matching":len(results),"company_context":src.get("company_context", ""),"careers_url":src.get("careers_url", "")})
                source_status[-1].update({'raw_postings': getattr(raw_results, 'raw_count', None),
                    'excluded_relevant': len(audit)})
                for job in results:
                    job["company_context"] = src.get("company_context", "")
                    job["careers_url"] = src.get("careers_url", "")
                    job["regions"] = job_regions(job.get("location", ""))
                    job["last_seen"] = now
                    found[job["id"]] = job
                print(f"OK {key}: {len(results)} matching")
            except Exception as e:
                failed.append(key)
                source_status.append({"source":key,"company":src["company"],"state":"ERROR","matching":0,"error":str(e)[:250],"company_context":src.get("company_context", ""),"careers_url":src.get("careers_url", "")})
                print(f"ERROR {key}: {e}", file=sys.stderr)

    # Do not update the sheet when no boards succeeded. Keeps last healthy data.
    if not successful:
        print("No sources succeeded; retaining previous files.", file=sys.stderr)
        return 1

    # Preserve rows from failed boards so the Google Sheet doesn't falsely
    # declare them closed; keep their previous last_seen unchanged.
    for job in previous.get("jobs", []):
        if job.get("source") in failed and job.get("id") not in found:
            # A failed source supplies no fresh duties to rescore. Preserve
            # the last evidence-backed score instead of scoring an empty JD.
            if meets_fit_floor(job):
                found[job["id"]] = job

    output = {
        "generated_at": now,
        "sources_checked": sorted(successful),
        "sources_failed": sorted(failed),
        "source_status": sorted(source_status,key=lambda x:x["company"]),
        "salary_target_usd": 140000,
        "minimum_fit_score": MIN_FIT_SCORE,
        "regions": ["Bay Area", "LA"],
        "filtered_out_job_ids": sorted(filtered_out),
        "excluded_roles": sorted(excluded_roles, key=lambda j: (j['company'], j['title'], j['id'])),
        "jobs": sorted(found.values(), key=lambda j: (j["company"].lower(), j["title"].lower(), j["id"])),
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = ["id", "company", "title", "category", "location", "workstyle", "employment", "experience_fit", "salary", "salary_min", "salary_max", "salary_fit", "fit_score", "match_reasons", "posted", "last_seen", "apply_url", "source_url", "source"]
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output["jobs"])
    print(f"Saved {len(found)} jobs; failed boards {len(failed)}/{len(sources)}")
    return 0

if __name__ == "__main__":
    sys.exit(run())

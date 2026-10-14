"""Employer-published job inventories: Apple search, Microsoft Eightfold, Google sitemap, Tesla state.

These endpoints are best effort. Failures must bubble up so the tracker never calls a
blocked board an empty board. All extracted jobs are filtered again in puller.py.
"""
import json
import re
import time
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BayAreaJobTracker/1.0; public job feeds)",
            "Accept": "application/json,text/html,application/xml"}
def _request(url, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    h = {**_HEADERS, "Content-Type": "application/json"} if body is not None else _HEADERS
    with urlopen(Request(url, data=body, headers=h), timeout=24) as r:
        return r.read(14000000).decode("utf-8","replace")
def _eligible(title, role, senior, noneng):
    return bool(title and role.search(title) and not senior.search(title) and not noneng.search(title))
def _items(page, container, key):
    val=page.get(container)
    if isinstance(val,dict): val=val.get(key)
    if not isinstance(val,list):raise ValueError("Unexpected job listing structure")
    return val
def _apple_location(loc):
    if isinstance(loc,str):return loc
    if not isinstance(loc,dict):return ""
    bits=[loc.get("name"),loc.get("city"),loc.get("stateProvince")]
    return ", ".join(str(z) for z in bits if z)
def _apple_record(job):
    title=job.get("postingTitle") or job.get("title") or job.get("jobTitle") or job.get("name") or ""
    locs=[_apple_location(z) for z in (job.get("locations") or [])]
    position=str(job.get("positionId") or job.get("jobId") or job.get("jobNumber") or "")
    # Apple sometimes uses PIPE- identifiers for generic retail jobs: do not invent a link.
    if not position and re.fullmatch(r"20[0-9]{7}(?:-[0-9]+)?",str(job.get("id",""))):
        position=str(job["id"])
    raw_url=next((str(job[k]) for k in ("jobUrl","detailsUrl","postingUrl","url") if job.get(k)), "")
    if raw_url: url=urljoin("https://jobs.apple.com",raw_url)
    elif position:
        slug=re.sub(r"[^a-z0-9]+","-",title.lower()).strip("-")
        url=f"https://jobs.apple.com/en-us/details/{position}/{slug}"
    else:url=""
    return {"title":title,"location":"; ".join(x for x in locs if x),"url":url,
            "description":str(job.get("jobSummary") or job.get("description") or ""),
            "employment":"Unspecified","posted":str(job.get("postingDate") or "")}
def fetch_apple(src, role, senior, noneng, bay):
    all_jobs={}; checked=0
    terms=src.get("search_terms",["mechanical","manufacturing","robotics","battery"])
    for term in terms:
        # Apple ranks queries, rather than enforcing exact titles. Each term is re-screened locally.
        for page in range(1,int(src.get("pages_per_query",2))+1):
            try:
                data=json.loads(_request("https://jobs.apple.com/api/v1/search",{
                    "query":term,"filters":{},"page":page,"locale":"en-us","sort":"",
                    "format":{"longDate":"MMMM D, YYYY","mediumDate":"MMM D, YYYY"}}))
            except Exception:
                if checked:break
                raise
            result=data.get("res")
            if not isinstance(result,dict) or not isinstance(result.get("searchResults"),list):
                raise ValueError("Apple search API returned no searchResults field")
            matches=result["searchResults"];checked+=1
            for job in matches:
                if not isinstance(job,dict):continue
                rec=_apple_record(job)
                if _eligible(rec["title"],role,senior,noneng) and bay.search(rec["location"]) and rec["url"]:
                    all_jobs[rec["url"]]=rec
            if len(matches)<20:break
            time.sleep(1.25)
    if not checked:raise ValueError("No valid Apple search pages")
    return list(all_jobs.values())

def _ms_location(pos):
    vals=pos.get("standardizedLocations") or pos.get("locations") or []
    return "; ".join(str(x) for x in vals if isinstance(x,str))
def fetch_microsoft(src, role, senior, noneng, bay):
    base="https://apply.careers.microsoft.com"
    collected={}; pages=0
    for term in src.get("search_terms",["mechanical","manufacturing","product design"]):
        for offset in (0,10):
            params=urlencode({"domain":"microsoft.com","query":term,"location":"",
                              "start":offset,"sort_by":"relevance","filter_include_remote":1})
            try:payload=json.loads(_request(base+"/api/pcsx/search?"+params))
            except Exception:
                if pages:break
                raise
            data=payload.get("data")
            if not isinstance(data,dict) or not isinstance(data.get("positions"),list):
                raise ValueError("Microsoft Eightfold did not return positions")
            posts=data["positions"];pages+=1
            for p in posts:
                if not isinstance(p,dict):continue
                title=p.get("name") or "";loc=_ms_location(p)
                if not (_eligible(title,role,senior,noneng) and bay.search(loc)):continue
                ident=str(p.get("id") or "");url=urljoin(base,p.get("positionUrl") or f"/careers/job/{ident}")
                if not ident or not url.startswith(base+"/careers/job/"):continue
                collected[ident]={"title":title,"location":loc,"url":url,
                        "description":str(p.get("jobDescription") or ""),
                        "employment":"Unspecified","posted":str(p.get("postedTs") or "")}
            if len(posts)<10:break
            time.sleep(2)
    if not pages:raise ValueError("Microsoft jobs API returned no valid pages")
    # Details may be throttled even when the search works. Keep the listing and
    # mark qualifications/pay as requiring manual verification in that case.
    for ident,j in list(collected.items())[:12]:
        try:
            q=urlencode({"position_id":ident,"domain":"microsoft.com","hl":"en"})
            data=json.loads(_request(base+"/api/pcsx/position_details?"+q)).get("data",{})
            if isinstance(data,dict):
                detail=data.get("position") if isinstance(data.get("position"),dict) else data
                if isinstance(detail,dict):
                    j["description"]=str(detail.get("jobDescription") or j["description"])
            time.sleep(1)
        except Exception: break
    return list(collected.values())

def google_job_detail(html, url, role):
    """Extract the *selected* job from the server-rendered detail, not the sidebar."""
    soup=BeautifulSoup(html,"html.parser")
    headings=[h.get_text(" ",strip=True) for h in soup.find_all(["h1","h2"])]
    title=next((h for h in headings if role.search(h) and h.lower() not in ("jobs search results","job details")), "")
    if not title:return None
    text=(soup.body or soup).get_text(" ",strip=True)
    # The left sidebar includes other positions. Job details start after its
    # second 'Back to jobs search' link, immediately before the target heading.
    section=text.rsplit("Back to jobs search",1)[-1][:18000]
    at=section.find(title)
    if at<0:return None
    section=section[at:]
    header=re.split(r"Minimum qualifications|About the job",section,1,flags=re.I)[0][:1600]
    m=re.search(r"\bplace\s+(.+?)\s+(?:bar_chart|Mid\b|Early\b|Advanced\b|Apply\b)",header,re.I)
    location=m.group(1).strip() if m else ""
    # If metadata or layout changes, do not invent a Bay Area city from body.
    if not location:return None
    return {"title":title,"location":location,"url":url,"description":section,
            "employment":"Unspecified","posted":""}
def fetch_google(src,role,senior,noneng,bay):
    xml=_request("https://careers.google.com/jobs/sitemap")
    root=ET.fromstring(xml)
    urls=[x.text for x in root.findall(".//{*}loc") if x.text and
           urlsplit(x.text).hostname in ("careers.google.com","www.google.com")]
    if not urls:raise ValueError("Google sitemap has no job URLs")
    terms=src.get("slug_keywords",["mechanical","manufactur","robotics","mechatron","battery","hardware","product-design","npi"])
    candidates=[]
    for url in urls:
        slug=urlsplit(url).path.lower().rsplit("/",2)[-2]
        title_slug=re.sub(r"^\d+-","",slug)
        if not any(w in title_slug for w in terms):continue
        if senior.search(title_slug.replace("-"," ")):continue
        if not role.search(title_slug.replace("-"," ")):continue
        candidates.append(url)
    if not candidates:return []
    jobs={};valid_details=0
    for url in candidates[:int(src.get("max_details",45))]:
        try:
            rec=google_job_detail(_request(url),url,role)
            if rec is None:continue
            valid_details+=1
            if _eligible(rec["title"],role,senior,noneng) and bay.search(rec["location"]):
                jobs[url]=rec
            time.sleep(0.2)
        except Exception:continue
    if not valid_details:raise ValueError("Google sitemap found candidate links but no parsed job details")
    return list(jobs.values())

def fetch_tesla(src,role,senior,noneng,bay):
    state=json.loads(_request("https://www.tesla.com/cua-api/apps/careers/state"))
    lookup=state.get("lookup") or {};posts=state.get("listings")
    if not isinstance(posts,list):raise ValueError("Tesla state API missing listings")
    locations=lookup.get("locations") or {}
    jobs=[]
    for p in posts:
        if not isinstance(p,dict):continue
        title=p.get("t") or "";loc=str(locations.get(str(p.get("l")),""))
        if not (_eligible(title,role,senior,noneng) and bay.search(loc)):continue
        slug=re.sub(r"[^a-z0-9]+","-",title.lower()).strip("-")
        ident=str(p.get("id",""));url=f"https://www.tesla.com/careers/search/job/{slug}-{ident}"
        if ident:jobs.append({"title":title,"location":loc,"url":url,"description":"",
                "employment":"Unspecified","posted":""})
    return jobs

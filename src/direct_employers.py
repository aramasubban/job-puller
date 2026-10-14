"""Best-effort employer-career adapters. Never interpret a parse error as zero jobs."""
import json,re,time
from pathlib import PurePosixPath
from urllib.parse import urljoin,urlsplit,unquote
from urllib.request import Request,urlopen
from bs4 import BeautifulSoup
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; JobSearchTracker/2.0; personal noncommercial daily search)','Accept':'text/html,application/json'}
def get_html(url):
    with urlopen(Request(url,headers=HEADERS),timeout=15) as r:
        if r.status!=200:raise RuntimeError(f'HTTP {r.status}')
        return r.read(3000000).decode('utf-8','replace')
def get_json(url,body=None):
    req=Request(url,data=json.dumps(body).encode() if body is not None else None,headers={**HEADERS,'Content-Type':'application/json','Accept':'application/json'})
    with urlopen(req,timeout=17) as r:return json.load(r)
def _title_from_url(url):
    stem=unquote(PurePosixPath(urlsplit(url).path).name)
    stem=re.sub(r'^\d+[-_]|[-_]\d+$','',stem)
    return ' '.join(w.capitalize() for w in re.sub('[-_]',' ',stem).split())
def extract_links(html,base,fragment):
    soup=BeautifulSoup(html,'html.parser');out={}
    for a in soup.find_all('a',href=True):
        u=urljoin(base,a['href']).split('#')[0]
        if fragment not in urlsplit(u).path or u.rstrip('/')==base.rstrip('/'):continue
        label=a.get_text(' ',strip=True)
        if not label or label.lower() in ('apply','learn more','view details','see full role description'):label=_title_from_url(u)
        if label and u not in out:out[u]=label
    return out
def detail_text(html):
    soup=BeautifulSoup(html,'html.parser')
    for x in soup(['script','style','nav','footer','header']):x.decompose()
    return ' '.join(soup.stripped_strings)[:60000]
def _extract_location(text):
    pats=[r'\bJob Category\b.{0,70}?\bLocation\s+(.{5,110}?)\s+\b(?:Req\.?\s*ID|Job Type|What to Expect)\b',r'\bLocation\s+(.{4,100}?)\s+\b(?:Actions|Role Number|Weekly Hours|Responsibilities|Apply)\b',r'\b(?:locations|Location|place)\s*[:]?\s*((?:US,?\s*CA,?\s*)?(?:Cupertino|Sunnyvale|Fremont|Mountain View|San Jose|San Francisco|Palo Alto|Santa Clara|Menlo Park|San Mateo|Oakland|Berkeley|San Carlos|Redwood City|San Francisco Bay Area|Various Locations within San Francisco Bay Area)[^.;]{0,40})']
    for pat in pats:
        m=re.search(pat,text,re.I)
        if m:return m.group(1).strip(' ,:')
    return ''
def fetch_official_html(src,role_pattern,senior_pattern,noneng_pattern,bay_match):
    names={}
    for listing in src['list_urls']:
        links=extract_links(get_html(listing),listing,src['link_fragment'])
        if not links:raise ValueError('No job links in listing HTML; site may require JavaScript or may have changed')
        names.update(links)
    candidates=[(u,t) for u,t in names.items() if role_pattern.search(t) and not senior_pattern.search(t) and not noneng_pattern.search(t)]
    items=[]
    for url,title in candidates[:50]:
        try:
            txt=detail_text(get_html(url));location=_extract_location(txt)
            if not bay_match.search(location):continue
            items.append({'url':url,'title':title,'location':location,'description':txt,'employment':'Unspecified'})
            time.sleep(.12)
        except Exception:continue
    if candidates and not items:raise ValueError('Matching job links found, but no verifiable Bay Area job details')
    return items,{'candidate_links':len(names),'considered':min(50,len(candidates)),'partial':len(candidates)>50}
def fetch_workday(src,role_pattern,senior_pattern,noneng_pattern,bay_match):
    base=f"https://{src['host']}/wday/cxs/{src['tenant']}/{src['site']}";jobs={}
    for term in src.get('search_terms',['mechanical']):
        for offset in (0,20,40):
            page=get_json(base+'/jobs',{'appliedFacets':{},'limit':20,'offset':offset,'searchText':term})
            listing=page.get('jobPostings',[])
            if not isinstance(listing,list):raise ValueError('Unexpected Workday response')
            for item in listing:
                title=item.get('title','');loc=item.get('locationsText') or (item.get('bulletFields') or [''])[0]
                if not role_pattern.search(title) or senior_pattern.search(title) or noneng_pattern.search(title) or not bay_match.search(str(loc)):continue
                ext=item.get('externalPath')
                if ext:jobs[ext]={'title':title,'location':str(loc),'url':f"https://{src['host']}/en-US/{src['site']}{ext}",'posted':item.get('postedOn','')}
            if not listing or offset+len(listing)>=page.get('total',0):break
    out=[]
    for path,rec in list(jobs.items())[:50]:
        try:
            info=get_json(base+path).get('jobPostingInfo',{})
            rec['description']=info.get('jobDescription','');rec['employment']=info.get('timeType','Unspecified')
            rec['location']=info.get('location') or rec['location'];out.append(rec)
        except Exception:continue
    if jobs and not out:raise ValueError('Workday matching jobs found but no job details retrieved')
    return out,{'candidate_links':len(jobs),'considered':min(len(jobs),50),'partial':len(jobs)>50}

"""Best-effort employer-career adapters. Never interpret a parse error as zero jobs."""
import json,re,time
from pathlib import PurePosixPath
from urllib.parse import urljoin,urlsplit,unquote
from urllib.request import Request,urlopen
from urllib.error import HTTPError
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
            html=get_html(url)
            if src.get('title_selector'):
                heading=BeautifulSoup(html,'html.parser').select_one(src['title_selector'])
                if heading:title=heading.get_text(' ',strip=True)
            txt=detail_text(html);location=_extract_location(txt)
            if not location and src.get('location_pattern'):
                # Employer-specific patterns must match the job header, not
                # cities mentioned elsewhere in a description or footer.
                location_text = txt[:1000]
                if src.get('location_selector'):
                    header = BeautifulSoup(html, 'html.parser').select_one(src['location_selector'])
                    location_text = header.get_text(' ', strip=True) if header else ''
                loc_match=re.search(src['location_pattern'],location_text)
                if loc_match:location=loc_match.group(1)
            if not bay_match.search(location):continue
            items.append({'url':url,'title':title,'location':location,'description':txt,'employment':'Unspecified'})
            time.sleep(.12)
        except Exception:continue
    if candidates and not items:raise ValueError('Matching job links found, but no verifiable Bay Area job details')
    return items,{'candidate_links':len(names),'considered':min(50,len(candidates)),'partial':len(candidates)>50}
def fetch_workday(src,role_pattern,senior_pattern,noneng_pattern,bay_match):
    base=f"https://{src['host']}/wday/cxs/{src['tenant']}/{src['site']}";jobs={}
    for term in src.get('search_terms',['mechanical']):
        for offset in range(0,20*int(src.get("max_pages",3)),20):
            page=get_json(base+'/jobs',{'appliedFacets':src.get('applied_facets',{}),'limit':20,'offset':offset,'searchText':term})
            listing=page.get('jobPostings',[])
            if not isinstance(listing,list):raise ValueError('Unexpected Workday response')
            for item in listing:
                title=item.get('title','');loc=item.get('locationsText') or (item.get('bulletFields') or [''])[0]
                if not role_pattern.search(title) or senior_pattern.search(title) or noneng_pattern.search(title) or not bay_match.search(str(loc)):continue
                ext=item.get('externalPath')
                if ext:jobs[ext]={'title':title,'location':str(loc),'url':f"https://{src['host']}/en-US/{src['site']}{ext}",'posted':item.get('postedOn','')}
            if not listing or offset+len(listing)>=page.get('total',0):break
    for path in src.get('detail_paths',[]):
        jobs.setdefault(path,{'title':'','location':'','url':f"https://{src['host']}/en-US/{src['site']}{path}"})
    out=[]
    for path,rec in list(jobs.items())[:int(src.get('max_details',50))]:
        try:
            info=get_json(base+path).get('jobPostingInfo',{})
            rec['title']=info.get('title') or rec['title'];rec['description']=info.get('jobDescription','');rec['employment']=info.get('timeType','Unspecified')
            rec['location']=info.get('location') or rec['location'];out.append(rec)
        except Exception:continue
    if jobs and not out:raise ValueError('Workday matching jobs found but no job details retrieved')
    return out,{'candidate_links':len(jobs),'considered':min(len(jobs),50),'partial':len(jobs)>50}


def fetch_amazon(src,role,senior,noneng,bay):
    from urllib.parse import urlencode
    jobs={}; checked=0
    for term in src.get('search_terms',['mechanical','hardware development','manufacturing']):
        for offset in range(0,int(src.get('max_pages',3))*100,100):
            query=urlencode({'base_query':term,'offset':offset,'result_limit':100,'country':'USA','region':'California'})
            page=get_json('https://www.amazon.jobs/en/search.json?'+query)
            listings=page.get('jobs')
            if not isinstance(listings,list):raise ValueError('Amazon search has no jobs array')
            checked+=len(listings)
            for j in listings:
                title=j.get('title','');loc=str(j.get('location',''))+'; '+str(j.get('locations',''))
                if not role.search(title) or senior.search(title) or noneng.search(title) or not bay.search(loc):continue
                path=j.get('job_path') or '/en/jobs/'+str(j['id']);match=re.search(r'/jobs/(\d+)',path);ident=match.group(1) if match else str(j['id'])
                desc='Description '+j.get('description','')+' Basic Qualifications '+j.get('basic_qualifications','')+' Preferred Qualifications '+j.get('preferred_qualifications','')
                jobs[ident]={'external_id':ident,'title':title,'location':loc,'url':urljoin('https://www.amazon.jobs',path),'description':desc,'employment':'FullTime','posted':j.get('posted_date','')}
            if offset+len(listings)>=page.get('hits',0) or not listings:break
    for j in jobs.values():
        if 'Cloud Hardware Development Engineer, AWS - Early Career' in j['title']:
            text=BeautifulSoup(get_html(j['url']),'html.parser').get_text(' ',strip=True)
            m=re.search(r'Cupertino, CA, USA\s*[-–]\s*([\d,]+)\.\d+ USD Annually',text)
            if m:
                pay=int(m.group(1).replace(',',''));j['published_starting_pay']=pay
                j['salary']=f'${pay:,} base / year (Cupertino starting pay; ceiling unlisted)'
    return list(jobs.values()),{'candidate_links':checked,'partial':True}

def fetch_icims(src,role,senior,noneng,bay):
    base=src['careers_url'];names={}
    for number in range(int(src.get('max_pages',6))):
        url=base.rstrip('/')+'/search?ss=1&in_iframe=1&pr='+str(number)
        html=get_html(url);soup=BeautifulSoup(html,'html.parser')
        links={}
        for a in soup.select('a[href]'):
            u=urljoin(url,a['href'])
            if re.search(r'/jobs/\d+/[^/]+/job',u):links[u]=a.get_text(' ',strip=True).removeprefix('Title ')
        if not links:
            if number==0:raise ValueError('iCIMS returned no posting links')
            break
        unseen={u:t for u,t in links.items() if u not in names};names.update(links)
        if not unseen:break
        pageinfo=soup.select_one('.iCIMS_SubHeader_Jobs')
        pages=re.search(r'Page \d+ of (\d+)',pageinfo.get_text(' ',strip=True) if pageinfo else '')
        if pages and number+1>=int(pages.group(1)):break
    for u in src.get('detail_urls',[]):
        names.setdefault(u,_title_from_url(u.rstrip('/').rsplit('/job',1)[0]))
    items=[]
    for u,t in names.items():
        if not role.search(t) or senior.search(t) or noneng.search(t):continue
        try:
            soup=BeautifulSoup(get_html(u),'html.parser')
        except HTTPError as error:
            if error.code in (404,410):continue
            raise
        h=soup.select_one('h1');title=h.get_text(' ',strip=True) if h else t
        text=soup.get_text(' ',strip=True)
        text=re.sub(r'\bDesired\b.*?(?=\bAdditional Information\b|$)','',text,flags=re.S)
        loc=re.search(r'Job Locations\s+(.*?)\s+(?:ID|Category|Type)\b',text)
        if not loc:continue
        location=loc.group(1).replace('US-CA-','')
        if not bay.search(location):continue
        items.append({'external_id':re.search(r'/jobs/(\d+)/',u).group(1),'url':u,'title':title,'location':location,'description':text,'employment':'FullTime' if 'Regular Full-Time' in text else 'Unspecified'})
    return items,{'candidate_links':len(names),'partial':True}

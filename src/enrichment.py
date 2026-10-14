"""Published US annual base salary screening and resume-fit scoring."""
import re
TARGET=140_000
MONEY_RANGE=re.compile(r"\$\s*([\d,]{2,9})(?:\.\d+)?\s*(?:-|–|—|to)\s*\$?\s*([\d,]{2,9})(?:\.\d+)?",re.I)
K_RANGE=re.compile(r"\$\s*(\d{2,3}(?:\.\d+)?)\s*[kK]\s*(?:-|–|—|to)\s*\$?\s*(\d{2,3}(?:\.\d+)?)\s*[kK]",re.I)
SECTOR_COMPANIES=re.compile(r"\b(medtronic|stryker|intuitive surgical|intuitive|abbott|dexcom|boston scientific|edwards lifesciences|neuralink|nudge|align technology|illumina)\b",re.I)
SECTOR_TITLES=re.compile(r"\b(hvac|heating,? ventilation|air conditioning|building services|mep engineer|plumbing|refrigeration|medical devices?|surgical devices?|implant devices?)\b",re.I)
KEYWORDS=[(r"\b(equipment|tooling|factory|laser weld|production line|cell manufactur)\b",19,"Tesla manufacturing equipment"),(r"\b(mechanical design|product design|cad|solidworks|gd&t|dfm|fea|structures)\b",18,"Mechanical design / FEA"),(r"\b(robotics?|actuator|quadruped|humanoid|mechanisms?|mechatronics?|linkage)\b",17,"Robotics / mechanisms"),(r"\b(battery|cell|energy storage|ev|vehicle|automotive|powertrain)\b",17,"EV / battery systems"),(r"\b(validation|test engineer|reliability|quality|npi|doe|root cause|process engineer)\b",14,"Validation / NPI")]
def salary_range(text):
    text=str(text or ''); matches=[]
    for m in K_RANGE.finditer(text):
        a,b=(int(float(m.group(i))*1000) for i in (1,2))
        if 45000<=a<=b<=600000:matches.append((a,b))
    for m in MONEY_RANGE.finditer(text):
        a,b=(int(m.group(i).replace(',','')) for i in (1,2))
        context=text[max(0,m.start()-48):min(len(text),m.end()+55)].lower()
        if any(x in context for x in ('/hour','per hour','hourly','/hr','per week')):continue
        if 45000<=a<=b<=600000:matches.append((a,b))
    return max(matches,key=lambda ab:ab[1]) if matches else (None,None)
def enrich(job,description):
    text=f"{job.get('title','')} {description or ''}"[:16000]
    lo,hi=salary_range(job.get('salary') or '')
    if lo is None:lo,hi=salary_range(description or '')
    if hi is not None and hi<TARGET:return None
    job['salary_min']=lo;job['salary_max']=hi
    job['salary_fit']='Target met' if lo is not None and lo>=TARGET else 'Range reaches $140k' if hi is not None else 'Undisclosed — review'
    if hi is not None and not job.get('salary'):job['salary']=f"${lo:,}–${hi:,} base / year"
    if not job.get('salary'):job['salary']='Not disclosed'
    points=25;reasons=[]
    for pat,weight,reason in KEYWORDS:
        if re.search(pat,text,re.I):points+=weight;reasons.append(reason)
    if 'New grad' in job.get('experience_fit',''):points+=10
    points+=10 if job['salary_fit']=='Target met' else 6 if job['salary_fit']=='Range reaches $140k' else 0
    job['fit_score']=min(points,100);job['match_reasons']='; '.join(reasons[:3]) or 'Relevant hardware role'
    return job

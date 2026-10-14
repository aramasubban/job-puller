"""Temporary diagnostics: public official job feed response shapes only."""
import json, traceback
from urllib.request import Request,urlopen
from urllib.parse import urlencode
def probe(name,url,body=None):
    try:
        data=None if body is None else json.dumps(body).encode()
        headers={'User-Agent':'Mozilla/5.0 (compatible; BayAreaJobTracker/1.0)','Accept':'application/json, text/html, application/xml','Content-Type':'application/json'}
        req=Request(url,data=data,headers=headers)
        with urlopen(req,timeout=23) as r:raw=r.read(9000000);status=r.status
        print(f'PROBE {name} HTTP={status} bytes={len(raw)}',flush=True)
        if raw[:1] in (b'{',b'['):
            j=json.loads(raw)
            print(' TOP',list(j.keys())[:15] if isinstance(j,dict) else type(j).__name__,flush=True)
            for key in ('res','data','response','results','jobs','jobPostings','listings','lookup'):
                sub=j.get(key) if isinstance(j,dict) else None
                if isinstance(sub,dict):print(' SUB',key,list(sub.keys())[:15],flush=True)
                elif isinstance(sub,list):print(' ARRAY',key,len(sub),'first',str(sub[0])[:700] if sub else '',flush=True)
            if isinstance(j,dict) and isinstance(j.get('res'),dict):
                for key,sub in j['res'].items():
                    if isinstance(sub,list):print(' RES_LIST',key,len(sub),'first',str(sub[0])[:950] if sub else '',flush=True)
        elif raw[:1]==b'<':print(' TEXT',raw[:400].decode('utf-8','replace'),flush=True)
    except Exception as e:print(f'PROBE {name} ERROR {type(e).__name__}: {e}',flush=True)
probe('TESLA','https://www.tesla.com/cua-api/apps/careers/state')
probe('APPLE','https://jobs.apple.com/api/v1/search',{'query':'mechanical','filters':{},'page':1,'locale':'en-us','sort':'','format':{}})
probe('MICROSOFT','https://apply.careers.microsoft.com/api/pcsx/search?'+urlencode({'query':'mechanical','location':'California','start':'0','size':'20'}))
probe('GOOGLE_SITEMAP','https://careers.google.com/sitemap.xml')


# Short shape diagnostics for the APIs we can read (do not log full descriptions)
import re
from urllib.error import HTTPError
def read(url,body=None):
 req=Request(url,data=None if body is None else json.dumps(body).encode(),headers={'User-Agent':'Mozilla/5.0 (compatible; BayAreaJobTracker/1.0)','Accept':'application/json, text/html, text/plain'})
 try:
  with urlopen(req,timeout=20) as r:return r.status,r.read(9000000).decode('utf-8','replace')
 except HTTPError as e:return e.code,e.read(600).decode('utf-8','replace')
for term in ('mechanical engineer','mechanical'):
 status,body=read('https://jobs.apple.com/api/v1/search',{'query':term,'filters':{},'page':1,'locale':'en-us','sort':'','format':{'longDate':'MMMM D, YYYY','mediumDate':'MMM D, YYYY'}})
 if status==200:
  o=json.loads(body)['res'];print('APPLE_TERM',term,'total',o.get('totalRecords'),'fields',list(o['searchResults'][0]),'first',[(p.get('postingTitle'),p.get('jobTitle'),p.get('title'),p.get('id')) for p in o['searchResults'][:4]])
  if o['searchResults']:
   p=o['searchResults'][0];print('APPLE_JOB',str({k:v for k,v in p.items() if k not in ('jobSummary','jobDescription')})[:1700])
status,body=read('https://apply.careers.microsoft.com/careers')
print('MS_HOME',status,'group',re.findall(r'_EF_GROUP_ID\\s*=\\s*["\\\']([^"\\\']+)',body)[:4],'bytes',len(body))
for grp in ('microsoft.com','microsoft',''):
 params={'start':'0','query':'mechanical','sort_by':'relevance'}
 if grp:params['domain']=grp
 status,body=read('https://apply.careers.microsoft.com/api/pcsx/search?'+urlencode(params))
 print('MS_SEARCH',grp,status,body[:550])
for url in ('https://careers.google.com/jobs/sitemap','https://careers.google.com/sitemap.txt'):
 status,body=read(url)
 print('GOOGLE_MAP',url,status,'bytes',len(body),'head',body[:350].replace('\\n',' '),'count',body.count('https://'))
for u in ('https://www.tesla.com/cua-api/careers/job/273339','https://www.tesla.com/cua-api/apps/careers/state?country=US'):
 status,body=read(u)
 print('TESLA_API',u,status,body[:140])

# One controlled Google detail check and one Apple field check
from xml.etree import ElementTree as ET
from urllib.parse import urlsplit
status,sitemap=read('https://careers.google.com/jobs/sitemap')
if status==200:
 root=ET.fromstring(sitemap)
 urls=[x.text for x in root.findall('.//{*}loc') if x.text]
 needles=('mechanical','manufactur','product-design','robotics','mechatronic','battery')
 eligible=[u for u in urls if any(z in u.lower() for z in needles)]
 print('GOOGLE_CANDIDATE_COUNT',len(eligible),'first',eligible[:4])
 for u in eligible[:2]:
  code,body=read(u)
  print('GOOGLE_DETAIL',code,u,'length',len(body),'head',body[:320].replace('\\n',' '))
code,body=read('https://careers.google.com/robots.txt')
print('GOOGLE_ROBOTS',code,body[:750])
code,body=read('https://jobs.apple.com/api/v1/search',{'query':'mechanical','filters':{},'page':1,'locale':'en-us','sort':'','format':{}})
if code==200:
 p=json.loads(body)['res']; items=p.get('searchResults',[])
 print('APPLE_SHAPE',p.get('totalRecords'),list(items[0]) if items else [],str({k:v for k,v in items[0].items() if k not in ('jobSummary','jobDescription')})[:1600] if items else '')
else:print('APPLE_SHAPE_HTTP',code,body[:250])

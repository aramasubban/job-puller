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

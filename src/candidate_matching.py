"""Evidence-based candidate fit; private profiles are injected at runtime.

Relevance is a prioritization score, never an interview probability. Eligibility
is reported separately. No company prestige, salary or repetition bonuses.
"""
import json
import re
from pathlib import Path
from functools import lru_cache
from src.matching import role_text, has
VERSION = 'evidence-v1'

@lru_cache(maxsize=8)
def load_profile(path):
    p=json.loads(Path(path).read_text())
    if not p.get('domains') or not p.get('duties'):
        raise ValueError('Candidate evidence profile is empty; refusing generic fallback')
    return p

def candidate_score(job, description, baseline, profile_path):
    from src.puller import required_experience_years
    p=load_profile(profile_path)
    core,full=role_text(description)
    title=job.get('title','')
    matches=[d for d in p['duties'] if has(d['pattern'],core)]
    domains=[d for d in p['domains'] if has(d['pattern'],title)]
    domain=max((d['points'] for d in domains),default=8)
    # The share of recognized, transferable responsibilities; require breadth.
    duties=35 if len(matches)>=3 else 29 if len(matches)==2 else 14 if matches else 0
    known=len(set(re.findall(p['tools']['supported'],core,re.I)))
    unknown=sorted(set(re.findall(p['tools']['not_demonstrated'],core,re.I)))
    tools=min(20,14+known*2) if known else 10
    tools=max(0,tools-min(12,4*len(unknown)))
    years=required_experience_years(core)
    junior=has(r'new.grad|early.career|entry.level|junior|engineer (?:i|1)\b',title+' '+core)
    if has(r'new grads?.{0,65}(?:welcome|encouraged|considered)|(?:welcome|encourage|consider).{0,50}new grads?',core) and years<=3: years=0;junior=True
    experience=0 if years>=4 else 10 if years==3 else 13 if years==2 else 17 if years==1 else 20 if junior else 14
    gaps=[]
    if years: gaps.append(f'{years}+ years required; confirm whether internships/projects count')
    else:gaps.append('May 2027 start not confirmed')
    preferred=re.search(r'preferred qualifications[: ]+(.+)',full,re.I)
    if preferred and has(r'\b(?:[2-9]\+? years?|MS degree|master)',preferred.group(1)):
        gaps.append('Preferred graduate degree/industry experience is not fully demonstrated; not a minimum requirement')
    if unknown:gaps.append('Tools/specialties not demonstrated: '+', '.join(unknown))
    safety=[g for g in baseline['match_gaps'] if not any(x in g for x in ['years','Experience/start date','internships','Limited mechanical-duty evidence'])]
    gaps+=safety
    score=min(98,domain+duties+tools+experience)
    # Retain real discipline, degree, start-window and missing-evidence gates.
    if safety and baseline['fit_score']<50:score=min(score,baseline['fit_score'])
    if any('Mixed ME/ECE' in g for g in safety):score=min(score,59)
    if len(matches)<2:score=min(score,49)
    if years>=4:score=min(score,29)
    if has(r'electrochemist|cell chemist|cathode formulation',title):score=min(score,39);gaps.append('Specialist battery chemistry is not demonstrated')
    if has(r'\b(?:electrochemistry|cathode formulation|cell chemistry)\b',core):score=max(0,score-12)
    if has(r'embedded',title) and has(r'hardware.in.the.loop|HIL|telematics|CAN',core):
        score=min(score,74);gaps.append('Adjacent embedded/HIL validation; vehicle networks and embedded stack depth not demonstrated')
    if has(r'PCBA|power module',title) and has(r'soldering|encapsulation|power electronics module',core):
        score=min(score,74);gaps.append('Specialist electronics assembly process depth not demonstrated')
    if has(r'Avionics.*Test|Production Test Engineer|Test Automation Engineer.*Hardware.in.the.Loop',title) and has(r'Linux|firmware|oscilloscope|electrical engineering',core):
        score=min(score,49);gaps.append('Specialist avionics/software test infrastructure depth not established')
    tier='Strong evidence fit' if score>=85 else 'Good evidence fit' if score>=75 else 'Review / stretch' if score>=50 else 'Low fit / eligibility gap'
    components={'domain':domain,'duties':duties,'tools':tools,'experience':experience}
    evidence=[]
    for d in sorted(domains,key=lambda d:-d['points'])[:1]+matches:
        if d['evidence'] not in evidence:evidence.append(d['evidence'])
    reason=tier+' | Evidence: '+'; '.join(evidence[:3])+' | Breakdown: '+', '.join(f'{k} {v}' for k,v in components.items())+' | Checks: '+'; '.join(gaps)
    return dict(fit_score=score,match_reasons=reason,match_version=VERSION,match_tier=tier,match_gaps=gaps,shortlist_eligible=score>=75,match_components=components,match_evidence=evidence,eligibility='Excluded: 4+ years' if years>=4 else 'Experience stretch' if years>=2 else 'Confirm May 2027 availability',profile_version=p['version'])

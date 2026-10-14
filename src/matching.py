"""ME-first heuristic fit, not a probability of an interview or offer.

Pay and industry buzzwords do not contribute. Core-duty/discipline gates precede
bounded skill and experience scores. Preferred skills cannot supply core fit.
"""
import re
from html import unescape
VERSION = 'me-v2'

def has(pattern, text):
    return bool(re.search(pattern, text, re.I))

def role_text(description):
    text = description or ''
    for _ in range(2): text = unescape(text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    start = re.search(r'\b(?:about (?:the|this) (?:role|position)|the role|minimum qualifications|required qualifications|qualifications|what you(?:’|\x27| wi)ll do|responsibilities)\b', text, re.I)
    if start:
        text = text[start.start():]
    text = re.split(r'\b(?:equal opportunity|don[’\x27]t meet every|for us-based roles|compensation at|benefits and perks)\b', text, flags=re.I)[0]
    core = re.sub(r'\b(?:nice to have|preferred qualifications|bonus points|what makes you stand out|it[’\x27]s a plus)\b.*?(?=\b(?:about the job|responsibilities|required qualifications|minimum qualifications)\b|$)', '', text, flags=re.I)
    return core, text

# Distinct evidence groups; repeated words never accumulate points.
ME = [
    (r'\b(?:mechanical design|mechanical engineering|product design|3d cad|solidworks|creo|catia|nx cad)\b', 'mechanical CAD/design'),
    (r'\b(?:gd\s*&\s*t|toleranc\w*|fea|finite element|structural analysis|stress analysis|thermal analysis)\b', 'analysis/tolerances'),
    (r'\b(?:fixtures?|jigs?|tooling|production equipment|manufacturing equipment|automation equipment|test rigs?)\b', 'equipment/fixtures'),
    (r'\b(?:mechanisms?|linkages?|actuators?|gearboxes?|end.effectors?|fasteners?|enclosures?|sheet metal)\b', 'mechanisms/assemblies'),
    (r'\b(?:dfm|design for manufactur\w*|machining|fabricat\w*|rapid prototyp\w*|3d print\w*)\b', 'fabrication/DFM'),
    (r'\b(?:root.cause|doe|design of experiments|spc|process improvement|yield improvement|failure analysis|dfmea|pfmea|vibration|fatigue|durability|thermal testing)\b', 'process/reliability testing'),
]
ECE = [
    (r'\b(?:pcb|pcba|printed circuit|board.level|board bring.up)\b', 'PCB/board engineering'),
    (r'\b(?:schematic\w*|circuit design|analog design|digital electronics|analog electronics|digital/analog)\b', 'circuits/schematics'),
    (r'\b(?:signal integrity|power integrity|high.speed digital|rf design|rf/sensor|fpga|asic|verilog|vhdl)\b', 'specialist electronics'),
    (r'\b(?:firmware development|embedded software|embedded c\+\+|device drivers|bsp|rtos)\b', 'embedded/firmware'),
]

def score_match(job, description):
    title = job.get('title', '')
    core, full = role_text(description)
    me = [label for pat,label in ME if has(pat, core)]
    ee = [label for pat,label in ECE if has(pat, core)]
    direct = has(r'\b(?:mechanical|mechanisms?|thermal|manufacturing|process|equipment|tooling|product design|structural)\b', title)
    related = has(r'\b(?:mechatronic\w*|robotic\w*|test|reliability|quality|integration)\b', title)
    discipline = 35 if direct and len(me)>=2 else 28 if len(me)>=3 else 20 if direct else 15 if related and me else 5
    # Duty breadth, tools/evidence, then career level. No salary bonus.
    duties = min(30, len(me)*6)
    skills = min(20, sum(has(p,core) for p in [
        r'\b(?:solidworks|cad|creo|catia)\b', r'\b(?:fea|finite element|gd&t|toleranc\w*)\b',
        r'\b(?:dfm|fabricat\w*|prototyp\w*|machining)\b', r'\b(?:doe|root.cause|spc|dfmea|pfmea)\b',
        r'\b(?:python|matlab|simulink|simscape|ros\s*2|ros2)\b']) * 4)
    gaps=[]; cap=95
    years=[int(m.group(1)) for m in re.finditer(r'(?<!\d)(\d{1,2})\s*(?:\+|[-–—]\s*\d{1,2})?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:(?:[\w/-]+\s+){0,5})?experience\b',core,re.I)]
    years += [int(m.group(1)) for m in re.finditer(r'(?<!\d)(\d{1,2})\+?\s+years?\s+(?:in|of professional|of hands.on|designing|building|developing|working|leading|managing)\b', core, re.I)]
    minimum=max(years, default=0)
    grad_welcome=has(r'new grads?.{0,65}(?:welcome|encouraged|considered)|(?:welcome|encourage|consider).{0,50}new grads?',core)
    if grad_welcome and minimum<=3: minimum=0
    if minimum>=4:
        exp=0;cap=29;gaps.append(f'{minimum}+ years required')
    elif minimum==3:
        exp=3;cap=64;gaps.append('3+ years: stretch beyond new-grad experience')
    elif minimum==2:
        exp=7;cap=74;gaps.append('2+ years: confirm internships count')
    elif minimum==1:
        exp=11;gaps.append('Confirm internships satisfy experience minimum')
    elif grad_welcome or has(r'new.grad|early.career|entry.level|junior|engineer (?:i|1)\b',title+' '+core):
        exp=15
    else:
        exp=8;cap=min(cap,79);gaps.append('Experience/start date not confirmed')
    if len(ee)>=2 and (len(me)<3 or not direct):
        cap=min(cap,25);gaps.insert(0,'ECE-heavy core: '+', '.join(ee[:2]))
    elif len(ee)>=2:
        cap=min(cap,59);gaps.insert(0,'Mixed ME/ECE: electronics depth not demonstrated')
    elif has(r'\b(?:electrical|computer) engineering\b',core) and not has(r'\b(?:mechanical|mechatronics) engineering\b',core) and ee:
        cap=min(cap,39);gaps.insert(0,'EE/CE-focused requirements; ME fit weak')
    if has(r'\b(?:electrical|firmware|rf|fpga|asic|rtl|physical design)\b',title) or (has(r'\belectronics\b',title) and not direct and len(me)<3):
        cap=min(cap,25);gaps.insert(0,'Electrical/embedded role')
    if has(r'\b(?:december|summer|fall|spring) 2026\b',title) or (has(r'(?:graduat\w*|complet\w*).{0,45}(?:by|end of).{0,20}2026',core) and not has(r'(?:summer|may|spring) 2027',core)):
        cap=min(cap,39);gaps.insert(0,'2026 graduation window conflicts with May 2027')
    if has(r'\b(?:ph\.?d|doctorate)\b.{0,35}(?:required|must)',core) or has(r'(?:require\w*|must have).{0,30}\b(?:ph\.?d|doctorate)\b',core):
        cap=min(cap,39);gaps.insert(0,'Doctorate requirement')
    if has(r'\b(?:motor design|stator|rotor|winding)\b',core) and has(r'\b(?:motor|motors)\b',title):
        cap=min(cap,74);gaps.append('Specialist motor design/manufacturing depth not demonstrated')
    if has(r'generative ai|ai & software|site reliability',title):
        cap=min(cap,39);gaps.insert(0,'Software/ML core outside mechanical target')
    if len(core)<200 or not has(r'responsibilit|qualifications|requirements|you will|you’ll|you\'ll|experience|design and|develop|build',core):
        cap=min(cap,39);gaps.insert(0,'Insufficient description: manual review')
    if len(me)<2:
        cap=min(cap,49);gaps.insert(0,'Limited mechanical-duty evidence')
    score=min(cap,discipline+duties+skills+exp)
    tier='Strong ME fit' if score>=85 else 'Good ME fit' if score>=75 else 'Review / stretch' if score>=50 else 'Low fit / eligibility gap'
    reason=tier+' | '+('Matches: '+', '.join(me[:3]) if me else 'No clear ME duties')
    if gaps:reason+=' | Gaps: '+'; '.join(gaps)
    else:reason+=' | Check: May 2027 start availability'
    return {'fit_score':score,'match_reasons':reason,'match_version':VERSION,'match_tier':tier,
            'match_gaps':gaps,'shortlist_eligible':score>=70}

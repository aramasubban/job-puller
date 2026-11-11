import unittest,tempfile,json
from pathlib import Path
from src.matching import generic_score_match
from src.candidate_matching import candidate_score
from src.enterprise_sources import fetch_apple
from src.puller import ROLE_PATTERN,SENIOR,NON_ENGINEERING,TARGET_AREA
from unittest.mock import patch

class EvidenceRankingTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.path=str(Path(self.temp.name)/'p.json')
  json.dump({'version':'test','domains':[{'pattern':'battery','points':25,'evidence':'battery fixture trials'}], 'duties':[{'pattern':'mechanical','evidence':'mechanical prototypes'},{'pattern':'toleranc','evidence':'tolerance stack'},{'pattern':'testing','evidence':'instrumented test rig'}], 'tools':{'supported':'CAD|Python','not_demonstrated':'Verilog'}},open(self.path,'w'))
 def tearDown(self):self.temp.cleanup()
 def score(self,title,d):return candidate_score({'title':title},d,generic_score_match({'title':title},d),self.path)
 def test_battery_evidence_scores_high_without_preferred_year_penalty(self):
  d='Responsibilities: mechanical engineering design, tolerances and testing with CAD. Develop production test fixtures and validation procedures, run root cause analysis and iterate prototypes to improve mechanical systems. Minimum Qualifications: BS engineering. Preferred Qualifications: MS and 3+ years of experience.'
  r=self.score('Battery Mechanical Engineer',d)
  self.assertGreaterEqual(r['fit_score'],90);self.assertFalse(any('3+' in g for g in r['match_gaps']))
 def test_real_year_requirement_remains_visible(self):
  d='Responsibilities: mechanical design, tolerances and testing with CAD. Requirements: 3 years of experience.'
  r=self.score('Battery Mechanical Engineer',d);self.assertIn('Experience stretch',r['eligibility'])
 def test_ee_cannot_gain_from_battery_title(self):
  self.assertLess(self.score('Battery Hardware Engineer','Responsibilities: PCB layout, schematic circuit design and Verilog. Electrical Engineering degree required.')['fit_score'],50)
 def test_missing_jd_stays_low(self):self.assertLess(self.score('Battery Mechanical Engineer','')['fit_score'],50)
 def test_unavailable_profile_fails_loudly(self):
  with self.assertRaises(FileNotFoundError):candidate_score({},'',{},self.path+'missing')
 def test_apple_retains_required_preferred_labels(self):
  search={'res':{'searchResults':[{'postingTitle':'Battery Mechanical Engineer','positionId':'123','locations':[{'name':'Cupertino'}]}]}}
  detail={'res':{'postingTitle':'Battery Mechanical Engineer','description':'Mechanical design introduction.','responsibilities':'Build fixtures, characterize mechanical cells with DOE and GD&T, and validate designs.','minimumQualifications':'BS and CAD.','preferredQualifications':'3 years of experience.'}}
  with patch('src.enterprise_sources._request',side_effect=[json.dumps(search),json.dumps(detail)]),patch('src.enterprise_sources.time.sleep'):
   d=fetch_apple({'search_terms':['battery'],'pages_per_query':1},ROLE_PATTERN,SENIOR,NON_ENGINEERING,TARGET_AREA)[0]['description']
  self.assertIn('Preferred Qualifications:',d)
  self.assertIn('Build fixtures',d)
  self.assertNotIn('years required',generic_score_match({'title':'Battery Mechanical Engineer'},d)['match_reasons'])

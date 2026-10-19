import unittest
from unittest.mock import patch
from src.puller import job_regions,required_experience_years,fetch_source
from src.matching import score_match
from src.direct_employers import fetch_amazon
class SearchQualityTests(unittest.TestCase):
 def test_semiconductor_npi_physical_systems(self):
  text="Responsibilities: NPI of opto-mechanical wafer stage, vibration isolation, motion control and automated wafer handling systems. Diagnose hardware problems and participate in design reviews. Minimum Qualifications: Master's Level Degree and 0 years related work experience; Bachelor's Level Degree and related work experience of 2 years."
  self.assertEqual(required_experience_years(text),2)
  score=score_match({'title':'NPI Product Engineer'},text)
  self.assertGreaterEqual(score['fit_score'],50)
  self.assertLessEqual(score['fit_score'],74)
 def test_multitrack_is_not_ece_only(self):
  text="We are looking for hardware engineers across a variety of domain expertise, including mechanical design, thermal and heat transfer design, signal integrity, PCB development and circuit design. Responsibilities may include mechanical design and thermal and heat transfer design. Basic Qualifications: Currently has, or is in the process of obtaining, a Bachelor's degree in Mechanical, Electrical or Industrial Engineering."
  self.assertGreaterEqual(score_match({'title':'Cloud Hardware Development Engineer, Early Career'},text)['fit_score'],50)
  text='Responsibilities: PCB circuit design, schematic design, signal integrity, FPGA Verilog and embedded firmware development. Required: electrical engineering degree.'
  self.assertLess(score_match({'title':'Hardware Integration Engineer'},text)['fit_score'],50)
 def test_bachelor_alternative_not_doctorate_zero(self):
  s="Doctorate Degree and 0 years related work experience; Master's Level Degree and related work experience of 3 years; Bachelor's Level Degree and related work experience of 5 years"
  self.assertEqual(required_experience_years(s),5)
 def test_santa_cruz_in_scope(self):
  self.assertEqual(job_regions('Santa Cruz, CA'),['Bay Area'])
 def test_amazon_location_and_stable_identifier(self):
  j={'id':'10530353','title':'Cloud Hardware Development Engineer','location':'USA, WA, Seattle','locations':['USA, CA, Cupertino'],'description':'Mechanical design','job_path':'/en/jobs/10530353/role'}
  with patch('src.direct_employers.get_json',return_value={'jobs':[j],'hits':1}):
   import re
   rows,_=fetch_amazon({'search_terms':['hardware']},re.compile('Hardware'),re.compile('Senior'),re.compile('Intern'),re.compile('Cupertino'))
   self.assertEqual(rows[0]['external_id'],'10530353')
 def test_graduate_cohorts_are_not_bachelor_new_grad(self):
  from src.puller import exclusion_reasons
  for title in ['Mechanical Engineer New College Grad - Masters Degree','New College Grad - Mechanical Engineer III - PhD (2027 Summer Cohort)']:
   self.assertTrue(any('Graduate-degree' in r for r in exclusion_reasons({'title':title,'company':'Applied Materials','location':'Santa Clara, CA'})))

 def test_expected_employers_remain_registered(self):
  import json
  from pathlib import Path
  employers={s['company'] for s in json.loads((Path(__file__).parents[1]/'config/boards.json').read_text())}
  self.assertTrue({'Amazon','KLA','Joby Aviation','Applied Materials','K2 Space'} <= employers)

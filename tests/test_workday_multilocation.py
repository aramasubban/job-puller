import unittest,re
from unittest.mock import patch
from src.direct_employers import fetch_workday
from src.puller import ROLE_PATTERN,SENIOR,NON_ENGINEERING,TARGET_AREA
class WorkdayLocationsTest(unittest.TestCase):
 def test_secondary_la_location_is_verified_and_ca_pay_selected(self):
  cfg={'host':'example.wd5.myworkdayjobs.com','tenant':'example','site':'Jobs','search_terms':['mechanical'],'max_pages':1,'salary_pattern':r'CA applicants is \$([\d,]+\.\d+)\s*[-–]\s*\$([\d,]+\.\d+)'}
  listing={'jobPostings':[{'title':'Mechanical Engineer I','locationsText':'5 Locations','externalPath':'/job/Mechanical_R1'}],'total':1}
  detail={'jobPostingInfo':{'title':'Mechanical Engineer I','location':'Seattle, WA','additionalLocations':['Los Angeles, CA'],'timeType':'Full time','jobDescription':'CA applicants is $81,313.00 - $113,837.85. CO applicants is $74,537 - $104,351.'}}
  with patch('src.direct_employers.get_json',side_effect=[listing,detail]):
   jobs,_=fetch_workday(cfg,ROLE_PATTERN,SENIOR,NON_ENGINEERING,TARGET_AREA)
  self.assertEqual(len(jobs),1)
  self.assertEqual(jobs[0]['location'],'Seattle, WA; Los Angeles, CA')
  self.assertEqual(jobs[0]['salary'],'$81,313.00–$113,837.85 base / year (California)')

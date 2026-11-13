import unittest,json
from unittest.mock import patch
from src.puller import job_regions,qualifies
from src.direct_employers import fetch_smartrecruiters
from src import puller
class ExpansionTests(unittest.TestCase):
 def test_seattle_geography(self):
  for city in ['Seattle, WA','Bellevue, Washington','Redmond, WA','Kirkland, WA','Kent, Washington','Everett, WA']:
   self.assertEqual(job_regions(city),['Seattle'])
  self.assertEqual(job_regions('Redmond, WA; Sunnyvale, CA'),['Seattle','Bay Area'])
  self.assertEqual(job_regions('Redmond, Oregon'),[]) 
 def test_medtech_physical_scope(self):
  for company in ['Intuitive','Neuralink','Nudge','Stryker','Medtronic']:
   self.assertTrue(qualifies(dict(company=company,title='Mechanical Engineer, Surgical Devices',location='Seattle, WA',description="Bachelor in mechanical engineering; design fixtures and mechanisms in CAD.",employment='Full-time')))
  self.assertFalse(qualifies(dict(company='Intuitive',title='Senior Mechanical Engineer',location='Sunnyvale, CA',description='5+ years of experience',employment='Full-time')))
 def test_smartrecruiters_full_detail(self):
  listing={'totalFound':1,'content':[{'id':'123','name':'Mechanical Engineer','location':{'fullLocation':'Sunnyvale, CA'}}]}
  detail={'jobAd':{'sections':{'qualifications':{'title':'Qualifications','text':'Requires 5+ years of experience.'}}},'applyUrl':'https://jobs.smartrecruiters.com/Intuitive/123'}
  with patch('src.direct_employers.get_json',side_effect=[listing,detail]):
   jobs,meta=fetch_smartrecruiters({'slug':'Intuitive'},puller.ROLE_PATTERN,puller.SENIOR,puller.NON_ENGINEERING,puller.TARGET_AREA)
  self.assertIn('5+ years',jobs[0]['description'])
  self.assertFalse(qualifies({**jobs[0],'company':'Intuitive'}))
 def test_missing_smartrecruiters_qualifications_fails(self):
  listing={'totalFound':1,'content':[{'id':'123','name':'Mechanical Engineer','location':{'fullLocation':'Sunnyvale, CA'}}]}
  with patch('src.direct_employers.get_json',side_effect=[listing,{}]):
   with self.assertRaises(ValueError):fetch_smartrecruiters({'slug':'Intuitive'},puller.ROLE_PATTERN,puller.SENIOR,puller.NON_ENGINEERING,puller.TARGET_AREA)

 def test_apple_keyword_filter_and_full_qualifications(self):
  from src.enterprise_sources import fetch_apple
  listing={'res':{'searchResults':[{'positionId':'200123456','postingTitle':'Mechanical Engineer','locations':[{'name':'Cupertino'}]}]}}
  detail={'res':{'postingTitle':'Mechanical Engineer','minimumQualifications':'Requires 5+ years of experience','description':'Solidworks fixtures'}}
  with patch('src.enterprise_sources._request',side_effect=[json.dumps(listing),json.dumps(detail)]) as mock:
   jobs=fetch_apple({'search_terms':['mechanical'],'pages_per_query':1},puller.ROLE_PATTERN,puller.SENIOR,puller.NON_ENGINEERING,puller.TARGET_AREA)
  self.assertEqual(mock.call_args_list[0].args[1]['filters'],{'keywords':['mechanical']})
  self.assertIn('5+ years',jobs[0]['description'])
  self.assertFalse(qualifies({**jobs[0],'company':'Apple'}))

 def test_experience_of_working_is_mandatory(self):
  self.assertEqual(puller.required_experience_years('3+ years of working in mechanical engineering or equivalent experience'),3)
  self.assertFalse(qualifies(dict(company='Amazon',title='Mechanical Engineer',location='Redmond, WA',description='5+ years of working in mechanical engineering or equivalent experience',employment='Full-time')))

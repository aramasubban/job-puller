import unittest
from unittest.mock import patch
from src.enterprise_sources import (
  _apple_record, _ms_location, google_job_detail, fetch_tesla,
  fetch_apple, fetch_microsoft, fetch_google
)
from src.puller import ROLE_PATTERN, SENIOR, NON_ENGINEERING, BAY_AREA, qualifies
class EnterpriseAPITests(unittest.TestCase):
 def test_apple_record_official_link_and_locations(self):
  x={'positionId':'200687631','postingTitle':'Mechanical Product Design Engineer',
     'locations':[{'name':'Cupertino, California','postLocationId':'postLocation-CUP'}],
     'jobSummary':'2 years of relevant experience.'}
  r=_apple_record(x)
  self.assertEqual(r['location'],'Cupertino, California')
  self.assertTrue(r['url'].startswith('https://jobs.apple.com/en-us/details/200687631/'))
 def test_apple_missing_id_does_not_invent_url(self):
  r=_apple_record({'id':'PIPE-2027','postingTitle':'Mechanical Engineer','locations':[]})
  self.assertEqual(r['url'],'')
 def test_microsoft_standardized_location(self):
  self.assertEqual(_ms_location({'standardizedLocations':['Mountain View, CA, US']}),'Mountain View, CA, US')
 def test_google_detail_ignores_sidebar(self):
  html="""<html><body><h2>Jobs search results</h2>
  <div>Random Hardware Engineer San Diego</div>
  Back to jobs search <h2>Mechanical Design Engineer</h2>
  corporate_fare Google place Sunnyvale, CA, USA bar_chart Early
  Minimum qualifications: Bachelor's degree in Mechanical Engineering.
  2 years of experience in mechanical product design.
  US: $140000 - $180000 (USD) + equity.</body></html>"""
  r=google_job_detail(html,'https://careers.google.com/jobs/results/123-mechanical-design-engineer/',ROLE_PATTERN)
  self.assertEqual(r['title'],'Mechanical Design Engineer')
  self.assertEqual(r['location'],'Sunnyvale, CA, USA')
  self.assertTrue(qualifies({**r,'company':'Google'}))
 def test_google_unparsable_detail_is_not_invented(self):
  self.assertIsNone(google_job_detail('<h2>Mechanical Engineer</h2> no location','https://careers.google.com/jobs/results/123/',ROLE_PATTERN))
 def test_tesla_state_fields(self):
  payload={'lookup':{'locations':{'33':'Fremont, California'}},
           'listings':[{'id':'273339','t':'Mechanical Design Engineer, Automation','l':'33'}]}
  with patch('src.enterprise_sources._request',return_value=__import__('json').dumps(payload)):
   out=fetch_tesla({},ROLE_PATTERN,SENIOR,NON_ENGINEERING,BAY_AREA)
  self.assertEqual(len(out),1)
  self.assertTrue(out[0]['url'].endswith('-273339'))
 def test_tesla_refusal_is_error(self):
  with patch('src.enterprise_sources._request',side_effect=PermissionError('HTTP 403')):
   with self.assertRaises(PermissionError):
    fetch_tesla({},ROLE_PATTERN,SENIOR,NON_ENGINEERING,BAY_AREA)
 def test_apple_response_schema_is_checked(self):
  with patch('src.enterprise_sources._request',return_value='{"res":{"searchResults":null}}'):
   with self.assertRaises(ValueError):
    fetch_apple({'search_terms':['mechanical'],'pages_per_query':1},ROLE_PATTERN,SENIOR,NON_ENGINEERING,BAY_AREA)
 def test_microsoft_response_schema_is_checked(self):
  with patch('src.enterprise_sources._request',return_value='{"data":{"positions":null}}'):
   with self.assertRaises(ValueError):
    fetch_microsoft({'search_terms':['mechanical']},ROLE_PATTERN,SENIOR,NON_ENGINEERING,BAY_AREA)
 def test_google_sitemap_requires_entries(self):
  with patch('src.enterprise_sources._request',return_value='<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>'):
   with self.assertRaises(ValueError):
    fetch_google({},ROLE_PATTERN,SENIOR,NON_ENGINEERING,BAY_AREA)
if __name__=='__main__':unittest.main()

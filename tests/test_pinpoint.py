import unittest
from unittest.mock import patch
from src.puller import fetch_source
class PinpointTests(unittest.TestCase):
 def test_posting_id_and_separate_required_qualifications(self):
  job={'id':'internal-123','url':'https://example.pinpointhq.com/en/postings/public-uuid','title':'Mechanical Engineer','location':{'name':'Hawthorne, California'},'employment_type_text':'Full Time','description':'Responsibilities: Mechanical design of spacecraft mechanisms. CAD, FEA, GD&T, tooling, prototyping and hardware testing.','skills_knowledge_expertise_header':'Required qualifications','skills_knowledge_expertise':'Bachelor degree in mechanical engineering. 3+ years of experience in mechanical engineering.','compensation_visible':True,'compensation':'$100,000 - $157,000 / year'}
  cfg={'provider':'pinpoint','slug':'example','company':'Example','postings_url':'https://example.pinpointhq.com/postings.json'}
  with patch('src.direct_employers.get_json',return_value={'data':[job]}):
   rows=fetch_source(cfg);self.assertEqual(rows.raw_count,1);self.assertEqual(rows[0]['id'],'pinpoint:example:public-uuid');self.assertGreaterEqual(rows[0]['fit_score'],50)
  job['skills_knowledge_expertise']='Bachelor degree. 5+ years of experience in mechanical engineering.'
  with patch('src.direct_employers.get_json',return_value={'data':[job]}):
   rows=fetch_source(cfg);self.assertEqual(len(rows),0);self.assertIn('5+',str(rows.excluded_roles))
 def test_invalid_payload_is_failure(self):
  with patch('src.direct_employers.get_json',return_value={'error':'bad'}):
   with self.assertRaises(ValueError):fetch_source({'provider':'pinpoint','slug':'test','company':'Test','postings_url':'https://example.test/postings.json'})

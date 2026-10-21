import unittest
from src import puller
from src.enrichment import salary_range,enrich
from src.direct_employers import extract_links
class CoreTests(unittest.TestCase):
    def test_target_salary_band(self):
        self.assertEqual(salary_range('$105,000–$175,000'),(105000,175000))
        self.assertIsNotNone(enrich({'title':'Mechanical Design Engineer','experience_fit':'0–3 years specified','salary':'$110,000–$190,000'},'SolidWorks and FEA'))
    def test_low_pay_is_flagged_not_discarded(self):
        self.assertEqual(enrich({'title':'Mechanical Engineer','experience_fit':'New grad / early career','salary':'$80,000–$110,000'},'CAD')['salary_fit'],'Below $140k preference — review')
    def test_unknown_pay_for_review(self):
        self.assertEqual(enrich({'title':'Equipment Engineer','experience_fit':'New grad / early career','salary':''},'Tesla manufacturing')['salary_fit'],'Undisclosed — review')
    def test_bay_area_only(self):
        self.assertTrue(puller.is_bay_area('Fremont, CA'))
        self.assertFalse(puller.is_bay_area('Los Angeles, CA'))
    def test_experience_requirement(self):
        self.assertEqual(puller.experience_fit('Mechanical Engineer, New Grad','Requires at least 5 years experience'),'EXCLUDE')
    def test_medical_and_hvac_excluded(self):
        job={'title':'HVAC Mechanical Engineer','company':'ACME','location':'Sunnyvale, CA','description':'','employment':'Full-time'}
        self.assertFalse(puller.qualifies(job))
        job['title']='Mechanical Engineer';job['company']='Medtronic'
        self.assertFalse(puller.qualifies(job))
    def test_link_parser(self):
        links=extract_links('<a href="/careers/search/job/test-mechanical-engineer-123">Mechanical Engineer</a>','https://www.tesla.com/careers/search','/careers/search/job/')
        self.assertEqual(len(links),1)
if __name__=='__main__':unittest.main()

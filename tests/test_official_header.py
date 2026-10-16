import unittest
from unittest.mock import patch
from src.direct_employers import fetch_official_html
from src.puller import ROLE_PATTERN,SENIOR,NON_ENGINEERING,BAY_AREA

class OfficialHeaderTests(unittest.TestCase):
    def test_job_header_location_survives_navigation_cleanup(self):
        source={'list_urls':['https://example.com/careers'],'link_fragment':'/job/',
                'location_pattern':r'(San Francisco, CA)\s*·\s*On-site',
                'location_selector':'header:has(h1)','title_selector':'h1'}
        listing='<a href="/job/mechanical">Mechanical Engineer San Francisco, CA</a>'
        detail='<header><h1>Mechanical Engineer</h1><p>San Francisco, CA · On-site</p></header><main>Design fixtures in CAD.</main>'
        with patch('src.direct_employers.get_html',side_effect=[listing,detail]),patch('src.direct_employers.time.sleep'):
            records,_=fetch_official_html(source,ROLE_PATTERN,SENIOR,NON_ENGINEERING,BAY_AREA)
        self.assertEqual(records[0]['location'],'San Francisco, CA')

    def test_employer_header_supplies_location_and_title(self):
        source={'list_urls':['https://example.com/careers'],'link_fragment':'/job/',
                'location_pattern':r'\b(San Jose, CA)\s+Apply\b','title_selector':'h1'}
        listing='<a href="/job/mechanical">Mechanical Engineer San Jose, CA</a>'
        detail='<h1>Mechanical Engineer</h1><p>San Jose, CA Apply</p><p>Mechanical design with 2 years experience.</p>'
        with patch('src.direct_employers.get_html',side_effect=[listing,detail]),patch('src.direct_employers.time.sleep'):
            records,_=fetch_official_html(source,ROLE_PATTERN,SENIOR,NON_ENGINEERING,BAY_AREA)
        self.assertEqual(records[0]['title'],'Mechanical Engineer')
        self.assertEqual(records[0]['location'],'San Jose, CA')

    def test_body_city_cannot_substitute_for_header_location(self):
        source={'list_urls':['https://example.com/careers'],'link_fragment':'/job/',
                'location_pattern':r'\b(San Jose, CA)\s+Apply\b'}
        listing='<a href="/job/mechanical">Mechanical Engineer</a>'
        detail='<h1>Mechanical Engineer</h1>'+'x'*1000+'San Jose, CA Apply'
        with patch('src.direct_employers.get_html',side_effect=[listing,detail]):
            with self.assertRaises(ValueError):
                fetch_official_html(source,ROLE_PATTERN,SENIOR,NON_ENGINEERING,BAY_AREA)

if __name__=='__main__':unittest.main()

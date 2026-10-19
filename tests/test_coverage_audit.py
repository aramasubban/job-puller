import json
import unittest
from pathlib import Path
from src import puller
from src.matching import score_match


class CoverageAuditTests(unittest.TestCase):
    def test_or_more_years_is_an_experience_requirement(self):
        desc = 'Requirements: 2 or more years of hands-on experience developing mechanical products using SolidWorks, FEA, fixtures and GD&T.'
        self.assertEqual(puller.required_experience_years(desc), 2)
        self.assertLessEqual(score_match({'title': 'Mechanical Engineer'}, desc)['fit_score'], 74)
        self.assertEqual(puller.experience_fit('Mechanical Engineer', desc.replace('2 or more', '5 or more')), 'EXCLUDE')

    def payload(self, title, description):
        return {'jobs': [{'title': title, 'location': 'Palo Alto',
            'jobUrl': 'https://jobs.ashbyhq.com/test/abc',
            'employmentType': 'FullTime', 'descriptionPlain': description}]}

    def test_integration_role_is_checked_and_explained_not_silently_lost(self):
        desc = ('Responsibilities: mechanical design in SolidWorks, fixtures, '
                'FEA and machining. Qualifications: 5+ years of experience '
                'in mechanical design and integration for vehicles.')
        result = puller.parse_board({'provider': 'ashby', 'slug': 'test',
            'company': 'Test'}, self.payload('Mechanical Systems Integration Engineer', desc))
        self.assertEqual(result, [])
        self.assertEqual(result.raw_count, 1)
        self.assertIn('Requires 5+ years', result.excluded_roles[0]['reasons'][0])

    def test_actual_junior_projects_are_not_confused_with_staff_or_ee_roles(self):
        desc = ('Responsibilities: mechanical engineering test fixtures, durability '
                'testing, DAQs and Python. Qualifications: Demonstrated hands-on '
                'experience through academic, personal, or internship projects '
                'involving physical testing. Salary: $100,000 to $215,000 per year.')
        job = {'title': 'Mechanical Hardware Test & Validation Engineer (All Levels)'}
        score = score_match(job, desc)
        self.assertGreaterEqual(score['fit_score'], 50)
        self.assertNotIn('Experience/start date not confirmed', score['match_gaps'])
        result = puller.parse_board({'provider': 'ashby', 'slug': 'test',
            'company': 'Test'}, self.payload(job['title'], desc))
        self.assertEqual(len(result), 1)
        staff = puller.parse_board({'provider': 'ashby', 'slug': 'test',
            'company': 'Test'}, self.payload('Staff Mechanical Engineer', desc))
        self.assertEqual(staff, [])

    def test_years_without_word_experience_still_exclude_and_three_years_are_stretch(self):
        self.assertEqual(puller.experience_fit('Mechanical Engineer',
            'Requirements: 5+ years designing mechanical parts that made it into production.'), 'EXCLUDE')
        desc = ('Responsibilities: SolidWorks mechanical design, fixtures, FEA, '
                'machining. Requirements: 3+ years taking products into manufacturing.')
        self.assertEqual(puller.experience_fit('Mechanical Engineer', desc), '0–3 years specified')
        self.assertLessEqual(score_match({'title': 'Mechanical Engineer'}, desc)['fit_score'], 64)

    def test_employer_coverage_includes_verified_missing_sources(self):
        sources = json.loads((Path(__file__).parents[1] / 'config/boards.json').read_text())
        keys = {(s['provider'], s.get('slug')) for s in sources}
        self.assertIn(('ashby', 'Ridealso'), keys)
        self.assertIn(('ashby', 'bedrock-robotics'), keys)
        self.assertIn(('greenhouse', 'freeformfuturecorp'), keys)


if __name__ == '__main__':
    unittest.main()

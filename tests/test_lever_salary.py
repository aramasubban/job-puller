import unittest
from src.puller import parse_board


class LeverSalaryTest(unittest.TestCase):
    def test_supervisor_is_excluded_from_early_career_search(self):
        from src.puller import SENIOR
        self.assertIsNotNone(SENIOR.search('Avionics Manufacturing Supervisor'))

    def test_explicit_2026_start_is_different_from_a_2026_title(self):
        from src.puller import exclusion_reasons
        role = {'title': '2026 Early Career Mechanical Engineer', 'location': 'Costa Mesa, CA', 'description': 'Able to start full time in 2026'}
        self.assertTrue(any('Required 2026' in r for r in exclusion_reasons(role)))
        role['description'] = 'Bachelor degree; internships count'
        self.assertFalse(exclusion_reasons(role))

    def test_future_opportunities_is_not_a_specific_open_role(self):
        from src.puller import exclusion_reasons
        self.assertTrue(any('Talent pool' in r for r in exclusion_reasons({'title':'Future Opportunities - Mechanical Engineering','location':'Torrance, CA'})))

    def test_structured_annual_salary_is_retained_below_preference(self):
        rows = parse_board({'provider': 'lever', 'slug': 'example', 'company': 'Example'}, [{
            'id': 'new-grad', 'text': 'Manufacturing Engineer, New Grad',
            'hostedUrl': 'https://jobs.lever.co/example/new-grad',
            'categories': {'location': 'Los Angeles, CA', 'commitment': 'Full-time'},
            'descriptionPlain': 'Bachelor degree in Mechanical Engineering. Design CAD tooling and fixtures, GD&T, DFM, manufacturing processes and mechanical testing. Internships and student projects welcome.',
            'salaryRange': {'min': 91800, 'max': 112200, 'currency': 'USD', 'interval': 'per-year-salary'},
        }])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['salary_min'], 91800)
        self.assertEqual(rows[0]['salary_max'], 112200)
        self.assertIn('Below $140k', rows[0]['salary_fit'])


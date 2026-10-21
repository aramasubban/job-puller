import unittest
from src.puller import parse_board


class LeverSalaryTest(unittest.TestCase):
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


import unittest

from src.puller import exclusion_reasons, required_experience_years


class EmploymentLabelTests(unittest.TestCase):
    def reasons(self, employment):
        return exclusion_reasons({
            'title': 'Mechanical Engineer',
            'company': 'Example Hardware',
            'location': 'Palo Alto, CA',
            'employment': employment,
            'description': 'Design mechanical fixtures and battery enclosures. Bachelor degree in Mechanical Engineering. 0-2 years experience.',
        })

    def test_payroll_classification_does_not_exclude_full_time(self):
        for label in ('Full-time (Exempt)', 'Full-time (Non-Exempt)', 'Full-time'):
            with self.subTest(label=label):
                self.assertNotIn('Not full-time permanent employment', self.reasons(label))

    def test_temporary_and_contract_labels_still_excluded(self):
        for label in ('Full-time (Contract)', 'Part-time (Exempt)', 'Temporary', 'Contract'):
            with self.subTest(label=label):
                self.assertIn('Not full-time permanent employment', self.reasons(label))

    def test_spelled_out_experience_minimums_are_enforced(self):
        self.assertEqual(required_experience_years('Qualifications: Three or more years of hands-on battery, environmental, abuse, reliability, or aerospace hardware testing experience.'), 3)
        self.assertEqual(required_experience_years('Required qualifications: Five years of mechanical engineering experience.'), 5)
        self.assertEqual(required_experience_years('Required qualifications: Three to five years of mechanical engineering experience.'), 3)

    def test_spelled_out_company_age_and_preferred_years_are_not_requirements(self):
        self.assertEqual(required_experience_years('Founded five years ago. Basic qualifications: Bachelor degree. Preferred qualifications: Eight years of engineering experience.'), 0)

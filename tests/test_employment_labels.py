import unittest

from src.puller import exclusion_reasons


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

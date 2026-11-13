import unittest
from src.puller import exclusion_reasons
class WinterAvailability(unittest.TestCase):
 def test_winter_cohort_with_completed_degree_requirement(self):
  j=dict(title='Manufacturing Engineer, Machining Associate (Winter 2027)',company='Astranis',location='San Francisco, CA',description="Requirements Currently hold a Bachelor's of science in Mechanical Engineering.")
  self.assertIn('Winter 2027 cohort requires completed bachelor degree before May 2027 availability',exclusion_reasons(j))

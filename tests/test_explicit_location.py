import unittest
from src.puller import exclusion_reasons
class ExplicitWorkLocationTests(unittest.TestCase):
 def test_mandatory_foreign_location_overrides_california_portal_metadata(self):
  j={'company':'Applied Materials','title':'Process Engineer','location':'Santa Clara,CA; Singapore','employment':'FullTime','description':'Work Location : This position is based in Bangalore, India. Minimum 2+ years of relevant experience.'}
  self.assertTrue(any('Required work location outside' in x for x in exclusion_reasons(j)))
 def test_generic_foreign_office_reference_does_not_exclude_california_role(self):
  j={'company':'Example','title':'Mechanical Engineer','location':'Santa Clara, CA','employment':'FullTime','description':'We collaborate with colleagues in India. Minimum 2+ years of experience.'}
  self.assertEqual(exclusion_reasons(j),[])

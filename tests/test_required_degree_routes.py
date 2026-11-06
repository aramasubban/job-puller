import unittest
from src.puller import exclusion_reasons, required_experience_years
class RequiredDegreeRoutes(unittest.TestCase):
 def test_masters_only_formal_minimum(self):
  for apostrophe in ["'",'’']:
   role={'title':'System Product Design Engineer','company':'Apple','location':'Cupertino','employment':'FullTime','minimum_qualifications':f'Master{apostrophe}s degree or foreign equivalent in Mechanical Engineering. Experience and/or education must include CAD.'}
   self.assertIn('Required graduate degree; no bachelor route stated',exclusion_reasons(role))
 def test_bachelor_alternative_allowed(self):
  role={'title':'Mechanical Engineer','company':'Apple','location':'Cupertino','employment':'FullTime','minimum_qualifications':"Master's degree or Bachelor's degree with 2 years experience."}
  self.assertNotIn('Required graduate degree; no bachelor route stated',exclusion_reasons(role))
 def test_post_baccalaureate_progressive_minimum(self):
  self.assertEqual(required_experience_years("Bachelor's degree and 5 years of progressive, post-baccalaureate experience. 3 years of experience with CAD."),5)

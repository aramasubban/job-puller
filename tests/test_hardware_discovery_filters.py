import unittest
from src.puller import exclusion_reasons,ROLE_PATTERN
class HardwareDiscoveryFilters(unittest.TestCase):
 def test_permanent_lever_employment_label(self):
  j=dict(title='Engineer I, Mechanical Hardware Test',company='Shield AI',location='Seattle, Washington',employment='Full Time Employee',description='B.S. Mechanical Engineering; 0-2 years relevant experience, academic projects may count. CAD design and mechanical test systems.')
  self.assertNotIn('Not full-time permanent employment',exclusion_reasons(j))
 def test_contract_stays_excluded(self):
  j=dict(title='Mechanical Engineer',company='Example',location='Seattle, WA',employment='Contract')
  self.assertIn('Not full-time permanent employment',exclusion_reasons(j))
 def test_battery_supplier_title_reaches_duty_screen(self):
  self.assertTrue(ROLE_PATTERN.search('Supplier Development Engineer, Battery'))
 def test_additional_lever_requirements_are_screened(self):
  from src.puller import parse_board
  source=dict(provider='lever',company='Example',slug='example')
  raw=[dict(id='test',text='Mechanical Engineer',hostedUrl='https://example.com/test',categories={'commitment':'Full Time Employee','location':'Seattle, WA'},descriptionPlain='Mechanical design, CAD, FEA and prototyping.',additionalPlain='Minimum 5 years of mechanical engineering experience required.')]
  out=parse_board(source,raw)
  self.assertFalse(out)
  self.assertTrue(any('Requires 5+' in r for j in out.excluded_roles for r in j['reasons']))

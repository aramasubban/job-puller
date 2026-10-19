import unittest
from html import escape
from src.puller import job_regions,parse_board,plain
class RegionsPayTests(unittest.TestCase):
 def test_regions(self):
  self.assertEqual(job_regions('Long Beach, CA'),['LA'])
  self.assertEqual(job_regions('San Francisco, CA; Torrance, CA'),['Bay Area','LA'])
  for s in ['California','Remote','San Diego, CA','Newark, NJ','Pasadena, Texas']:self.assertEqual(job_regions(s),[])
 def test_encoded_html(self):
  self.assertEqual(plain(escape('<p>$90,000 <span>&mdash;</span> $140,000</p>')),'$90,000 — $140,000')
 def test_equity_is_not_base_salary(self):
  desc='<h2>Responsibilities</h2><p>Develop mechanical engineering designs in Solidworks. Perform FEA and tolerances. Design fixtures and tooling with machining and DFM. Requirements: 1 year experience.</p>'
  desc+='<div class="pay-input"><div class="title">Total Compensation (base and equity)</div><div class="pay-range">$140,000 — $180,000</div></div>'
  desc+='<div class="pay-input"><div class="title">Base Salary</div><div class="pay-range">$87,000 — $109,000</div></div>'
  payload={'jobs':[{'id':1,'title':'Mechanical Engineer I','location':{'name':'Long Beach, CA'},'absolute_url':'https://example.com/jobs/1','content':escape(desc)}]}
  job=parse_board({'provider':'greenhouse','slug':'test','company':'Test'},payload)[0]
  self.assertEqual(job['salary_max'],109000)
  self.assertEqual(job['salary_fit'],'Below $140k preference — review')

import unittest
from src.puller import parse_board
class GreenhousePostedDate(unittest.TestCase):
 def record(self,**dates):
  return parse_board({'provider':'greenhouse','slug':'test','company':'Test'},{'jobs':[dict(id=12,title='Mechanical Engineer',absolute_url='https://example.com/12',location={'name':'San Francisco, CA'},content='Bachelor degree in Mechanical Engineering. CAD mechanical design and testing. Entry level.',**dates)]})[0]
 def test_edit_date_is_not_posting_date(self):
  self.assertEqual(self.record(updated_at='2026-11-09T12:00:00Z')['posted'],'')
 def test_explicit_publication_date_survives(self):
  self.assertEqual(self.record(first_published='2026-11-01T12:00:00Z',updated_at='2026-11-09T12:00:00Z')['posted'],'2026-11-01T12:00:00Z')

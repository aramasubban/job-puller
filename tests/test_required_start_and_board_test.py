import unittest
from datetime import datetime,timezone
from src.puller import requires_start_before_may_2027
from src.matching import score_match
class RequiredStartAndBoardTest(unittest.TestCase):
 def test_near_term_completed_degree_window(self):
  d='Candidates should have completed their degree requirements and be available to begin full-time employment within 30–60 days of applying.'
  self.assertTrue(requires_start_before_may_2027(d,datetime(2026,11,11,tzinfo=timezone.utc)))
  self.assertFalse(requires_start_before_may_2027(d,datetime(2027,4,1,tzinfo=timezone.utc)))
 def test_circuit_board_test_core_is_not_mechanical_manufacturing(self):
  r=score_match({'title':'Manufacturing Engineer, AWS Board Core Design Team'},'Develop PCBA test fixtures and processes; CAD and equipment design, DFM, DOE, root cause. Electrical Engineering degree. Experience with DFT (Design for Testability), boundary scan (JTAG), schematic/layout design reviews. 2 years of experience.')
  self.assertLess(r['fit_score'],50)

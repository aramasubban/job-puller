import unittest
from src.matching import score_match
from src.enrichment import enrich

ME='About the role: Design mechanical assemblies using SolidWorks and CAD. Build fixtures, enclosures and actuators. Use FEA, GD&T, rapid prototyping and DFM. Perform root cause analysis, DOE and Python data analysis. '
class MatchingTests(unittest.TestCase):
    def test_ece_new_grad_cannot_be_top_match(self):
        d='About the role: Design schematics and PCB layouts. Board-level bring-up and circuit design. Electrical Engineering or Computer Engineering degree. Validate embedded systems. Nice to have: automotive robotics and DFM.'
        r=score_match({'title':'Hardware Integration Engineer - New Grad (2027)'},d)
        self.assertLessEqual(r['fit_score'],25)
        self.assertFalse(r['shortlist_eligible'])
    def test_mechatronics_with_me_duties_is_retained(self):
        r=score_match({'title':'Mechatronics Engineer - New Grad'},ME+'Use low voltage wiring and a multimeter.')
        self.assertGreaterEqual(r['fit_score'],85)
    def test_pay_does_not_raise_fit(self):
        a=enrich({'title':'Mechanical Engineer - New Grad','salary':'$110,000–$150,000'},ME)
        b=enrich({'title':'Mechanical Engineer - New Grad','salary':'$180,000–$300,000'},ME)
        self.assertEqual(a['fit_score'],b['fit_score'])
    def test_company_buzzwords_do_not_raise_fit(self):
        a=score_match({'title':'Mechanical Engineer'},ME)
        b=score_match({'title':'Mechanical Engineer'},'We build robotics, batteries, PCBs and vehicles. '+ME)
        self.assertEqual(a,b)
    def test_2026_graduation_and_three_years_demoted(self):
        self.assertLess(score_match({'title':'Mechanical Engineer - New Grad (December 2026)'},ME)['fit_score'],50)
        self.assertLess(score_match({'title':'Mechanical Engineer'},ME+'Requires 3+ years of professional experience.')['fit_score'],75)
    def test_missing_description_not_recommended(self):
        self.assertLess(score_match({'title':'Mechanical Engineer - New Grad'},'')['fit_score'],40)
    def test_preferred_electronics_not_core_requirement(self):
        self.assertGreaterEqual(score_match({'title':'Mechanical Engineer - New Grad'},ME+'Nice to have: PCB and schematic design.')['fit_score'],85)

    def test_years_without_word_experience(self):
        self.assertLess(score_match({'title':'Mechanical Engineer'},ME+'3+ years designing and building mechanical systems.')['fit_score'],70)
        self.assertLess(score_match({'title':'Hardware Test Engineer'},ME+'4+ years in hardware test and validation.')['fit_score'],40)
    def test_requirements_before_responsibilities_not_lost(self):
        d='Minimum qualifications: 3 years of experience in mechanical engineering. Preferred qualifications: PCB layouts. About the job: '+ME+' Responsibilities: Build test fixtures.'
        self.assertLess(score_match({'title':'Mechanical Engineer'},d)['fit_score'],70)
    def test_explicit_new_grad_exception(self):
        r=score_match({'title':'Mechanical Engineer'},ME+'1-4 years of experience; exceptional new grads with strong projects are welcome to apply.')
        self.assertGreaterEqual(r['fit_score'],85)

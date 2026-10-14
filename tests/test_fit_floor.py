import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from src import puller

class FitFloorTests(unittest.TestCase):
    def test_threshold_is_inclusive(self):
        self.assertFalse(puller.meets_fit_floor({'fit_score':49}))
        self.assertTrue(puller.meets_fit_floor({'fit_score':50}))
        self.assertFalse(puller.meets_fit_floor({'fit_score':None}))

    def test_failed_source_retains_healthy_jobs_but_not_low_fit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); config=root/'boards.json'; out=root/'jobs.json'
            config.write_text(json.dumps([
                {'provider':'ashby','company':'Healthy','slug':'healthy'},
                {'provider':'ashby','company':'Failed','slug':'failed'}]))
            previous=[{'id':str(score),'source':'ashby:failed','fit_score':score,
                       'match_version':puller.MATCH_VERSION,'company':'Failed',
                       'title':'Mechanical Engineer','last_seen':'original'} for score in [49,50]]
            out.write_text(json.dumps({'jobs':previous}))
            def fetch(src):
                if src['slug']=='failed':raise RuntimeError('source unavailable')
                return [{'id':'fresh-low','company':'Healthy','title':'Test','fit_score':49},
                        {'id':'fresh-good','company':'Healthy','title':'Test','fit_score':60}]
            with patch.object(puller,'CONFIG',config),patch.object(puller,'JSON_OUT',out),patch.object(puller,'CSV_OUT',root/'jobs.csv'),patch.object(puller,'fetch_source',fetch):
                self.assertEqual(puller.run(),0)
            result=json.loads(out.read_text()); by_id={j['id']:j for j in result['jobs']}
            self.assertEqual(set(by_id),{'50','fresh-good'})
            self.assertEqual(by_id['50']['last_seen'],'original')
            self.assertEqual(result['minimum_fit_score'],50)
            self.assertEqual(result['filtered_out_job_ids'],['fresh-low'])

if __name__=='__main__':unittest.main()

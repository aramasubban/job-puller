import io,json,unittest
from http.client import IncompleteRead
from unittest.mock import patch,MagicMock
from src.puller import _download
class TruncatedFeedRetryTests(unittest.TestCase):
 def test_truncated_official_feed_is_retried_before_failure(self):
  first=MagicMock();first.__enter__.return_value=first
  first.read.side_effect=IncompleteRead(b'{"jobs":',7)
  second=io.BytesIO(b'{"jobs":[{"id":123}]}')
  with patch('src.puller.urlopen',side_effect=[first,second]) as get,patch('src.puller.time.sleep'):
   result=_download('https://example.com/jobs')
  self.assertEqual(result,{'jobs':[{'id':123}]})
  self.assertEqual(get.call_count,2)

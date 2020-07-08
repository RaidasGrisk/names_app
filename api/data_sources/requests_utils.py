import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def requests_retry_session(retries=5):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
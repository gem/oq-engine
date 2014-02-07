from concurrent.futures import ThreadPoolExecutor
from openquakeserver.settings import CONCURRENT_JOBS

executor = ThreadPoolExecutor(max_workers=CONCURRENT_JOBS)

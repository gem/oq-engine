from concurrent.futures import ThreadPoolExecutor
from openquake.server.settings import CONCURRENT_JOBS

executor = ThreadPoolExecutor(max_workers=CONCURRENT_JOBS)

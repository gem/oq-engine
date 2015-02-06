from concurrent.futures import ThreadPoolExecutor

# recommended setting for development
executor = ThreadPoolExecutor(max_workers=1)

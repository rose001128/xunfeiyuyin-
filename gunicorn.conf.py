import multiprocessing, os

bind = f"{os.getenv('HOST','0.0.0.0')}:{os.getenv('PORT','8000')}"
workers = max(2, multiprocessing.cpu_count())
accesslog = '-'
errorlog = '-'
loglevel = os.getenv('LOG_LEVEL','info')
timeout = 60

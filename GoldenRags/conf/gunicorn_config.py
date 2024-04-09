from decouple import config

bind=config('BIND')
workers=config('WORKERS')
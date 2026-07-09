# Gunicorn configuration file
import os
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "djankit"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = "root"
group = "root"
tmp_upload_dir = None

# Application
wsgi_module = "config.wsgi:application"
pythonpath = "/app"

# SSL (uncomment for HTTPS)
# keyfile = "/path/to/ssl/private.key"
# certfile = "/path/to/ssl/certificate.crt"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Worker timeout
graceful_timeout = 30

# Preload application
preload_app = True

# Worker tmp dir
worker_tmp_dir = "/tmp"

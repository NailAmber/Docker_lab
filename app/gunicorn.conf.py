bind = "0.0.0.0:8000"
workers = 2
threads = 2
timeout = 30
preload_app = True


def post_worker_init(worker):
    import os

    os.environ["WORKER_ID"] = str(worker.pid)

from rq import Worker
from .handler import r_conn, q

worker = Worker([q], connection=r_conn)
worker.work()
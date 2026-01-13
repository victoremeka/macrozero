web: gunicorn server:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 1 --preload
worker: python -u -m router.worker

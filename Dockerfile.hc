FROM python:2.7
WORKDIR /app
RUN groupadd appusers && \
    useradd appuser -G appusers && \
    chown -R appuser:appusers /app && \
    cd /app && pip install -r requirements.txt && \
    mkdir instance && \
    touch instance/hc_config.py
COPY requirements.txt gunicorn.conf hc_app.py hc_config.py /app/
COPY celery_app_config.py.example /app/celery_app_config.py
USER appuser:appusers
EXPOSE 4001
ENTRYPOINT ["/usr/local/bin/gunicorn", "--config", "/app/gunicorn.conf", "-b", ":4001", "hc_app:app"]
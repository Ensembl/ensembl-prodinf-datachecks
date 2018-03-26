FROM python:2.7
WORKDIR /app
COPY requirements.txt gunicorn.conf hc_app.py hc_config.py /app/
COPY email_celery_app_config.py.example /app/email_celery_app_config.py
RUN useradd appuser -u 1000 -g 0 && \
    chown -R 1000:0 /app && \
    cd /app && pip install -r requirements.txt && \
    mkdir instance && \
    touch instance/hc_config.py
USER 1000:0
EXPOSE 4001
ENTRYPOINT ["/usr/local/bin/gunicorn", "--config", "/app/gunicorn.conf", "-b", ":4001", "hc_app:app"]
FROM python:3.9

RUN useradd --create-home appuser
RUN mkdir -p /home/appuser/datachecks
WORKDIR /home/appuser/datachecks/
RUN chown appuser:appuser /home/appuser/datachecks
USER appuser

WORKDIR /home/appuser/datachecks
#copy datachecks app
COPY --chown=appuser:appuser . /home/appuser/datachecks

#Install dependenciesls

RUN python -m venv /home/appuser/datachecks/venv
ENV PATH="/home/appuser/datachecks/venv/bin:$PATH"
RUN pip install -r requirements.txt
RUN pip install .

#clone datacheck app
ENV DATACHECK_CONFIG_PATH="/home/appuser/datachecks/config.yaml"
RUN git clone https://github.com/Ensembl/ensembl-datacheck.git
EXPOSE 5001
CMD  ["gunicorn", "--config", "/home/appuser/datachecks/gunicorn_config.py", "-b", "0.0.0.0:5001", "ensembl.production.datacheck.app.main:app"]


FROM python:3.7.10
WORKDIR /app

#copy datacheck app
COPY . /app
#install core - till core repo is private uncomment below lines to install it 
#RUN cd /app/ensembl-prodinf-core && pip install . 
#WORKDIR /app

#Install datacheck app dependencies
RUN pip install -r requirements.txt
RUN pip install .

#clone datacheck app
RUN git clone https://github.com/Ensembl/ensembl-datacheck.git

#datacheck config
ENV DATACHECK_CONFIG_PATH="/app/config.yaml"


EXPOSE 5000
CMD  ["/usr/local/bin/gunicorn", "--config", "/app/gunicorn_config.py", "-b", "0.0.0.0:5000", "ensembl.datacheck.app.main:app"]


***************************
Bulk Healthcheck submission
***************************

Overview
########

The Production infrastructure interface allows to run healthchecks on databases using the `HC endpoint <https://github.com/Ensembl/ensembl-prodinf-srv/README_hc.rst>`_. This document describes how to use the `<HcClient ../ensembl_prodinf/hc_client.py>`_ class to interact with the endpoint and bulk check databases.

Create file with list of databases to healthcheck
#################################################

Create file with list of databases to healthcheck, e.g: ``db_hc.txt``
::

  cavia_porcellus_funcgen_91_4
  homo_sapiens_funcgen_91_38
  mus_musculus_funcgen_91_38
  pan_troglodytes_funcgen_91_3

Or for all the database of a given division:

EG:
===
Please find below the list of EG divisions short names:

* Bacteria - EB
* Protists - EPr
* Fungi	- EF
* Metazoa - EM
* Plants - EPl
* Pan - EG

To get the list of databases for Fungi:

.. code-block:: bash

  RELEASE=38
  perl ensembl-metadata/misc_scripts/get_list_databases_for_division.pl $(mysql-ens-meta-prod-1 details script) -division fungi -release $RELEASE > fungi_db_hc.txt



Ensembl:
========

.. code-block:: bash

  RELEASE=91
  perl ensembl-metadata/misc_scripts/get_list_databases_for_division.pl $(mysql-ens-meta-prod-1 details script) -division vertebrates -release $RELEASE > vertebrates_db_hc.txt

Submit the jobs using REST endpoint:
####################################

Clone the ensembl-prodinf-core repo:

.. code-block:: bash

  git clone https://github.com/Ensembl/ensembl-prodinf-core
  cd ensembl-prodinf-core

To Submit the job via the REST enpoint for Ensembl

.. code-block:: bash

  SERVER=$(mysql-ens-vertannot-staging details url) #e.g: mysql://ensro@mysql-ens-vertannot-staging:4573/
  GROUP=CoreHandover
  COMPARA_MASTER=$(mysql-ens-compara-prod-1 details url)
  LIVE=$(mysql-ensembl-mirror details url)
  STAGING=$(mysql-ens-sta-1 details url)
  PRODUCTION=$(mysql-ens-sta-1 details url)
  ENDPOINT=http://ens-prod-1.ebi.ac.uk:8000/hc/
  DATA_FILE_PATH=/nfs/panda/ensembl/production/ensemblftp/data_files/
  RELEASE=91
  TAG=my_hc_run
  
  cd $BASE_DIR/ensembl-prodinf-core 
  for db in $(cat vertebrates_db_hc.txt);
  do python ensembl_prodinf/hc_client.py --uri $ENDPOINT --db_uri "${SERVER}${db}" --production_uri "${PRODUCTION}ensembl_production_${RELEASE}" --staging_uri $STAGING --live_uri $LIVE --compara_uri "${COMPARA_MASTER}ensembl_compara_master" --hc_groups $GROUP --data_files_path $DATA_FILE_PATH --tag $TAG  --action submit
  done
  
To Submit the job via the REST enpoint for EG

.. code-block:: bash

  SERVER=$(mysql-eg-staging-1 details url)
  GROUP=EGCoreHandover
  COMPARA_MASTER=$(mysql-eg-pan-prod details url)
  LIVE=$(mysql-eg-publicsql details url)
  STAGING=$(mysql-eg-staging-1 details url)
  PRODUCTION=$(mysql-eg-pan-prod details url)
  ENDPOINT=http://ens-prod-1.ebi.ac.uk:7000/hc/
  DATA_FILE_PATH=/nfs/panda/ensembl/production/ensemblftp/data_files/
  TAG=my_hc_run
  
  cd $BASE_DIR/ensembl-prodinf-core 
  for db in $(cat fungi_db_hc.txt);
  do python ensembl_prodinf/hc_client.py --uri $ENDPOINT --db_uri "${SERVER}${db}" --production_uri "${PRODUCTION}ensembl_production" --staging_uri $STAGING --live_uri $LIVE --compara_uri "${COMPARA_MASTER}ensembl_compara_master" --hc_groups $GROUP --data_files_path $DATA_FILE_PATH --tag $TAG  --action submit 
  done
  
To run multiple hcs and groups
##############################

To run multiple hcs, you need to list each healthchecks name with a space between each name, e.g:
::

  --hc_names CoreForeignKeys AutoIncrement

You can also run individual healthchecks and healthcheck groups at the same time, e.g:
::

  --hc_groups CoreXrefs --hc_names CoreForeignKeys

Script usage:
#############

The script accept the following arguments:
::

    usage: hc_client.py [-h] -u URI -a {submit,retrieve,list,delete,collate}
                    [-i JOB_ID] [-v] [-o OUTPUT_FILE] [-d DB_URI]
                    [-p PRODUCTION_URI] [-c COMPARA_URI] [-s STAGING_URI]
                    [-l LIVE_URI] [-dfp DATA_FILES_PATH]
                    [-n [HC_NAMES [HC_NAMES ...]]]
                    [-g [HC_GROUPS [HC_GROUPS ...]]] [-r DB_PATTERN] [-f]
                    [-e EMAIL] [-t TAG]

    Run HCs via a REST service

    optional arguments:
      -h, --help            show this help message and exit
      -u URI, --uri URI     HC REST service URI
      -a {submit,retrieve,list,delete,collate}, --action {submit,retrieve,list,delete,collate}
                            Action to take
      -i JOB_ID, --job_id JOB_ID
                            HC job identifier to retrieve
      -v, --verbose         Verbose output
      -o OUTPUT_FILE, --output_file OUTPUT_FILE
                            File to write output as JSON
      -d DB_URI, --db_uri DB_URI
                            URI of database to test
      -p PRODUCTION_URI, --production_uri PRODUCTION_URI
                            URI of production database
      -c COMPARA_URI, --compara_uri COMPARA_URI
                            URI of compara master database
      -s STAGING_URI, --staging_uri STAGING_URI
                            URI of current staging server
      -l LIVE_URI, --live_uri LIVE_URI
                            URI of live server for comparison
      -dfp DATA_FILES_PATH, --data_files_path DATA_FILES_PATH
                            Data files path
      -n [HC_NAMES [HC_NAMES ...]], --hc_names [HC_NAMES [HC_NAMES ...]]
                            List of healthcheck names to run
      -g [HC_GROUPS [HC_GROUPS ...]], --hc_groups [HC_GROUPS [HC_GROUPS ...]]
                            List of healthcheck groups to run
      -r DB_PATTERN, --db_pattern DB_PATTERN
                            Pattern of DB URIs to restrict by
      -f, --failure_only    Show failures only
      -e EMAIL, --email EMAIL
                            User email
      -t TAG, --tag TAG     Tag use to collate result and facilitate filtering

Check job status
################

You can check job status either on the production interface: `<http://ens-prod-1.ebi.ac.uk:8000/#!/hc_list>`_ or `<http://eg-prod-01.ebi.ac.uk:7000/#!/hc_list>`_ for EG

or using the Python client:

.. code-block:: bash

  ensembl_prodinf/db_copy_client.py --action list --uri http://ens-prod-1.ebi.ac.uk:8000/hc
  ensembl_prodinf/db_copy_client.py --action list --uri http://eg-prod-01.ebi.ac.uk:7000/hc

Collate results
###############

If you have run the healthchecks on a large number of databases, you can collate all the results in one file using the tag:

.. code-block:: bash

  python ensembl-prodinf-core/ensembl_prodinf/hc_client.py --uri http://ens-prod-1.ebi.ac.uk:8000/hc --action collate --tag "my_hc_run" --output_file results.json

Convert results in readable form
################################

Convert Json result file in readable text format:

.. code-block:: bash

  cat results.json | json_reformat > results.txt

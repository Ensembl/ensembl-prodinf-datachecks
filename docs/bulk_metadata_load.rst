******************
Bulk Metadata Load
******************

Overview
########

The Production infrastructure interface allows the update if the metadata database using the `metadata endpoint <https://github.com/Ensembl/ensembl-prodinf-srv/README_metadata.rst>`_.
This document describes how to use the `MetadataClient <../ensembl_prodinf/metadata_client.py>`_ class to interact with the endpoint and bulk update the database.

List of databases to load
#########################

Create file with list of databases to load, e.g: metadata_load.txt

.. code-block:: bash

  cavia_porcellus_funcgen_91_4
  homo_sapiens_funcgen_91_38
  mus_musculus_funcgen_91_38
  pan_troglodytes_funcgen_91_3

Or for all the database of a given division:

EG:
===

.. code-block:: bash

  EG_VERSION=38
  SERVER=mysql-eg-staging-2
  mysql --batch --raw --skip-column-names $($SERVER details mysql) information_schema -e "SELECT schema_name from SCHEMATA where schema_name not in ('performance_schema','mysql','information_schema','PERCONA_SCHEMA') and schema_name not like 'master_schema%'" > eg_metadata_load.txt

Ensembl:
========

.. code-block:: bash

  ENS_VERSION=91
  SERVER=mysql-ensembl-mirror
  mysql --batch --raw --skip-column-names $($SERVER details mysql) information_schema -e "SELECT schema_name from SCHEMATA where schema_name not in ('performance_schema','mysql','information_schema','PERCONA_SCHEMA') and schema_name not like 'master_schema%'" > metadata_load.txt

Submit the jobs using Python REST db copy endpoint:
###################################################

Clone the ensembl-prodinf-core repo:

.. code-block:: bash

  git clone https://github.com/Ensembl/ensembl-prodinf-core
  cd ensembl-prodinf-core

To Submit the job via the REST enpoint

For Ensembl:

.. code-block:: bash

  DATABASE_SERVER=$(mysql-ens-general-prod-1 details url)
  ENDPOINT=http://ens-prod-1.ebi.ac.uk:8000/metadata
  ENS_VERSION=91
  RELEASE_DATE="2017-12-06"
  CURRENT_RELEASE=1
  EMAIL=john.doe@ebi.ac.uk
  UPDATE_TYPE="Other"
  COMMENT="Loading database for release 91"
  SOURCE="Pre release load"

  cd $BASE_DIR/ensembl-prodinf-core 
  for db in $(cat metadata_load.txt); 
  do ensembl_prodinf/metadata_client.py --action submit --uri ${ENDPOINT} --database_uri "${DATABASE_SERVER}${db}" --e_release ${ENS_VERSION} --release_date ${RELEASE_DATE} --current_release ${CURRENT_RELEASE} --email "${EMAIL}" --update_type "${UPDATE_TYPE}" --comment "${COMMENT}" --source "${SOURCE}";
  done

For EG:

.. code-block:: bash

  DATABASE_SERVER=$(mysql-eg-staging-2 details url)
  ENDPOINT=http://eg-prod-01.ebi.ac.uk:7000/metadata
  ENS_VERSION=91
  RELEASE_DATE="2017-12-13"
  EG_VERSION=38
  CURRENT_RELEASE=1
  EMAIL=john.doe@ebi.ac.uk
  UPDATE_TYPE="Other"
  COMMENT="Loading database for release 91"
  SOURCE="Pre release load"

  cd $BASE_DIR/ensembl-prodinf-core 
  for db in $(cat eg_metadata_load.txt); 
  do ensembl_prodinf/metadata_client.py --action submit --uri ${ENDPOINT} --database_uri "${DATABASE_SERVER}${db}" --e_release ${ENS_VERSION} --release_date ${RELEASE_DATE} --current_release ${CURRENT_RELEASE} --eg_release ${EG_VERSION} --email "${EMAIL}" --update_type "${UPDATE_TYPE}" --comment "${COMMENT}" --source "${SOURCE}";
  done


Script usage:
#############

The script accept the following arguments:

::

  usage: metadata_client.py [-h] -u URI -a
                          {submit,retrieve,list,delete,email,kill_job}
                          [-i JOB_ID] [-v] [-o OUTPUT_FILE] [-f INPUT_FILE]
                          [-m METADATA_URI] [-d DATABASE_URI] [-s E_RELEASE]
                          [-r RELEASE_DATE] [-c CURRENT_RELEASE]
                          [-g EG_RELEASE] [-e EMAIL] [-t UPDATE_TYPE]
                          [-n COMMENT] [-b SOURCE]

  Metadata load via a REST service

  optional arguments:
  -h, --help            show this help message and exit
  -u URI, --uri URI     Metadata database REST service URI
  -a {submit,retrieve,list,delete,email,kill_job}, --action {submit,retrieve,list,delete,email,kill_job}
                        Action to take
  -i JOB_ID, --job_id JOB_ID
                        Metadata job identifier to retrieve
  -v, --verbose         Verbose output
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        File to write output as JSON
  -f INPUT_FILE, --input_file INPUT_FILE
                        File containing list of metadata and database URIs
  -m METADATA_URI, --metadata_uri METADATA_URI
                        URI of metadata database
  -d DATABASE_URI, --database_uri DATABASE_URI
                        URI of database to load
  -s E_RELEASE, --e_release E_RELEASE
                        Ensembl release number
  -r RELEASE_DATE, --release_date RELEASE_DATE
                        Release date
  -c CURRENT_RELEASE, --current_release CURRENT_RELEASE
                        Is this the current release
  -g EG_RELEASE, --eg_release EG_RELEASE
                        EG release number
  -e EMAIL, --email EMAIL
                        Email where to send the report
  -t UPDATE_TYPE, --update_type UPDATE_TYPE
                        Update type, e.g: New assembly
  -n COMMENT, --comment COMMENT
                        Comment
  -b SOURCE, --source SOURCE
                        Source of the database, eg: Handover, Release load

Check job status
################

You can check job status either on the production interface: `http://ens-prod-1.ebi.ac.uk:8000/#!/metadata_list` or `http://eg-prod-01.ebi.ac.uk:7000/#!/metadata_list` for EG

or using the Python client:

.. code-block:: bash

  ensembl_prodinf/metadata_client.py --action list --uri http://ens-prod-1.ebi.ac.uk:8000/metadata
  ensembl_prodinf/metadata_client.py --action list --uri http://eg-prod-01.ebi.ac.uk:7000/metadata
  
  

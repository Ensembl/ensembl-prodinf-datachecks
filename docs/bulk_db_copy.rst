******************
Bulk Database Copy
******************

Overview
########

The Production infrastructure interface allows the copy of database using the FLASK endpoint in the background.  This document describes how to use the `<DbCopyClient ../ensembl_prodinf/db_copy_client.py>`_ class to interact with the endpoint and bulk copy databases.

List of databases to copy
#########################

Create file with list of databases to copy, e.g: ``db_to_copy.txt``

::

  cavia_porcellus_funcgen_91_4
  homo_sapiens_funcgen_91_38
  mus_musculus_funcgen_91_38
  pan_troglodytes_funcgen_91_3

Or for all the database of a given division:

1. EG:
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
  ./ensembl-production/scripts/process_division.sh EF mysql-eg-pan-prod ensembl_production $RELEASE > fungi_db_to_copy.txt

2. Ensembl:

.. code-block:: bash

  RELEASE=91
  ./ensembl-production/scripts/process_division.sh ens mysql-ens-sta-1 ensembl_production_${RELEASE} $RELEASE > db_to_copy.txt

Submit the jobs using Python REST db copy endpoint:
###################################################

Clone the ensembl-prodinf-core repo:
.. code-block:: bash

  git clone https://github.com/Ensembl/ensembl-prodinf-core
  cd ensembl-prodinf-core

To submit the job via the REST enpoint

.. code-block:: bash

  SOURCE_SERVER=$(mysql-ens-vertannot-staging details url) #e.g: mysql://ensro@mysql-ens-vertannot-staging:4573/
  TARGET_SERVER=$(mysql-ens-general-prod-1-ensadmin details url)
  ENDPOINT=http://ens-prod-1.ebi.ac.uk:8000/dbcopy/ #or http://eg-prod-01.ebi.ac.uk:7000/dbcopy/ for EG

  cd $BASE_DIR/ensembl-prodinf-core 
  for db in $(cat db_to_copy.txt); 
  do ensembl_prodinf/db_copy_client.py --action submit --uri ${ENDPOINT} --source_db_uri "${SOURCE_SERVER}${db}" --target_db_uri "${TARGET_SERVER}${db}" --drop 1;
  done

Script usage:
#############

The script accept the following arguments:
::

    usage: db_copy_client.py [-h] -u URI -a
                             {submit,retrieve,list,delete,email,kill_job}
                             [-i JOB_ID] [-v] [-o OUTPUT_FILE] [-f INPUT_FILE]
                             [-s SOURCE_DB_URI] [-t TARGET_DB_URI]
                             [-y ONLY_TABLES] [-n SKIP_TABLES] [-p UPDATE]
                             [-d DROP] [-e EMAIL]

    Copy HCs via a REST service

    arguments:
      -h, --help            show this help message and exit
      -u URI, --uri URI     REST service URI
      -a {submit,retrieve,list,delete,email,kill_job}, --action {submit,retrieve,list,delete,email,kill_job}
                            Action to take
      -i JOB_ID, --job_id JOB_ID
                            HC job identifier to retrieve
      -v, --verbose         Verbose output
      -o OUTPUT_FILE, --output_file OUTPUT_FILE
                            File to write output as JSON
      -f INPUT_FILE, --input_file INPUT_FILE
                            File containing list of source and target URIs
      -s SOURCE_DB_URI, --source_db_uri SOURCE_DB_URI
                            URI of database to copy from
      -t TARGET_DB_URI, --target_db_uri TARGET_DB_URI
                            URI of database to copy to
      -y ONLY_TABLES, --only_tables ONLY_TABLES
                            List of tables to copy
      -n SKIP_TABLES, --skip_tables SKIP_TABLES
                            List of tables to skip
      -p UPDATE, --update UPDATE
                            Incremental database update using rsync checksum
      -d DROP, --drop DROP  Drop database on Target server before copy
      -e EMAIL, --email EMAIL
                            Email where to send the report

Check job status
################

You can check job status either on the production interface: `<http://ens-prod-1.ebi.ac.uk:8000/#!/copy_list>`_ or `<http://eg-prod-01.ebi.ac.uk:7000/#!/copy_list>`_ for EG:

or using the Python client:

.. code-block:: bash

  ensembl_prodinf/db_copy_client.py --action list --uri http://ens-prod-1.ebi.ac.uk:8002
  ensembl_prodinf/db_copy_client.py --action list --uri http://eg-prod-01.ebi.ac.uk:7002
  
  

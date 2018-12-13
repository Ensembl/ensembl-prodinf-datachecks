******************
Bulk database handover
******************

Overview
########

The Production infrastructure interface contains a handover service `handover endpoint <https://github.com/Ensembl/ensembl-prodinf-srv/README_handover.rst>`_.
This document describes how to use the `HandoverClient <../ensembl_prodinf/handover_client.py>`_ class to interact with the endpoint and bulk database handover.

List of databases to handover
#########################

Create file with list of databases to handover, e.g: handover_databases.txt

.. code-block:: bash

  cavia_porcellus_funcgen_91_4
  homo_sapiens_funcgen_91_38
  mus_musculus_funcgen_91_38
  pan_troglodytes_funcgen_91_3

Or for all the database of a given division:

EG:
===

* Bacteria - EB
* Protists - EPr
* Fungi	- EF
* Metazoa - EM
* Plants - EPl
* Pan - EG

To get the list of databases for Fungi:

.. code-block:: bash

  RELEASE=41
  ./ensembl-production/scripts/process_division.sh EF mysql-eg-pan-prod ensembl_production $RELEASE > eg_handover_databases.txt

Ensembl:
========

.. code-block:: bash

  RELEASE=94
  ./ensembl-production/scripts/process_division.sh EV mysql-ens-sta-1 ensembl_production_${RELEASE} $RELEASE > handover_databases.txt

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
  ENDPOINT=http://ens-prod-1.ebi.ac.uk:8000/handover
  EMAIL=john.doe@ebi.ac.uk
  DESCRIPTION="handover new Leopard database"

  cd $BASE_DIR/ensembl-prodinf-core 
  for db in $(cat handover_databases.txt); 
  do ensembl_prodinf/handover_client.py --action submit --uri ${ENDPOINT} --src_uri "${DATABASE_SERVER}${db}" --email "${EMAIL}" --description "${DESCRIPTION}";
  done

For EG:

.. code-block:: bash

  DATABASE_SERVER=$(mysql-ens-general-prod-1 details url)
  ENDPOINT=http://eg-prod-01.ebi.ac.uk:7000/handover
  EMAIL=john.doe@ebi.ac.uk
  DESCRIPTION="handover new Leopard database"

  cd $BASE_DIR/ensembl-prodinf-core 
  for db in $(cat handover_databases.txt); 
  do ensembl_prodinf/handover_client.py --action submit --uri ${ENDPOINT} --src_uri "${DATABASE_SERVER}${db}" --email "${EMAIL}" --description "${DESCRIPTION}";
  done


Script usage:
#############

The script accept the following arguments:

::


  usage: handover_client.py [-h] -u URI -a
                          {submit,retrieve,list,delete,events,processes} [-v]
                          -s SRC_URI -e EMAIL -t
                          {new_genome,new_genebuild,new_assembly,other} -c
                          DESCRIPTION [-n EMAIL_NOTIFICATION]

  Handover via a REST service

  optional arguments:
    -h, --help            show this help message and exit
    -u URI, --uri URI     HC REST service URI
    -a {submit,retrieve,list,delete,events,processes}, --action {submit,retrieve,list,delete,events,processes}
                          Action to take
    -v, --verbose         Verbose output
    -s SRC_URI, --src_uri SRC_URI
                          URI of database to hand over
    -e EMAIL, --email EMAIL
                          Email address
    -c DESCRIPTION, --description DESCRIPTION
                          Description
    -n EMAIL_NOTIFICATION, --email_notification EMAIL_NOTIFICATION
                          Get email notification of handover progress

Check job status
################

You can check job status either on the production interface: `http://ens-prod-1.ebi.ac.uk:8000/#!/database_handover_list` or `http://eg-prod-01.ebi.ac.uk:7000/#!/database_handover_list` for EG

or using the Python client:

.. code-block:: bash

  ensembl_prodinf/handover_client.py --action list --uri http://ens-prod-1.ebi.ac.uk:8000/handover
  ensembl_prodinf/handover_client.py --action list --uri http://eg-prod-01.ebi.ac.uk:7000/handover
  
  

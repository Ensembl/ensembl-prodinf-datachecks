************************
Bulk Database Copy
************************

Overview
########

The Production infrastructure interface allows the copy of database using the FLASK endpoint in the background. The following documentation explain how to copy databases using the Flask REST database copy endpoint.
This method is really useful for copying a large number of databases.

List of databases to copy
############

Create file with list of databases to copy, e.g: db_to_copy.txt
::
  cavia_porcellus_funcgen_91_4
  homo_sapiens_funcgen_91_38
  mus_musculus_funcgen_91_38
  pan_troglodytes_funcgen_91_3

Or for all the database of a given division:

1. EG:
::
  RELEASE=38
  ./ensembl-production/scripts/process_division.sh EM mysql-eg-pan-prod ensembl_production $RELEASE > fungi_db_to_copy.txt

2. Ensembl:
::
  RELEASE=91
  ./ensembl-production/scripts/process_division.sh ens mysql-ens-sta-1 ensembl_production_${RELEASE} $RELEASE > db_to_copy.txt

Submit the jobs using Python REST db copy endpoint:
#####

To Submit the job via the REST enpoint
::
  SOURCE_SERVER=$(mysql-ens-vertannot-staging details url) #e.g: mysql://ensro@mysql-ens-vertannot-staging:4573/
  TARGET_SERVER=$(mysql-ens-sta-1-ensadmin details url)
  SERVER_URL=http://ens-prod-1.ebi.ac.uk:8000/dbcopy/ #or http://eg-prod-01.ebi.ac.uk:7000/dbcopy/ for EG
  EMAIL=john.doe@ebi.ac.uk

  cd $BASE_DIR/ensembl-prodinf-core 
  for db in $(cat db_to_copy.txt); 
  do ensembl_prodinf/db_copy_client.py -a submit -u ${SERVER_URL} -s "${SOURCE_SERVER}${db}" -t "${TARGET_SERVER}${db}" -d 1 -e $EMAIL;
  done

Check job status
#####

You can check job status either on the production interface: `http://ens-prod-1.ebi.ac.uk:8000/#!/copylist` or `http://eg-prod-01.ebi.ac.uk:7000/#!/copylist` for EG

or using the Python REST API:

  ensembl_prodinf/db_copy_client.py -a list -u http://ens-prod-1.ebi.ac.uk:8000/dbcopy/
  
  or for EG:
  
  ensembl_prodinf/db_copy_client.py -a list -u http://eg-prod-01.ebi.ac.uk:7000/dbcopy/
  
  

************************
Bulk Healthcheck submission
************************

Overview
########

The Production infrastructure interface allows to run healthecks on databases using the FLASK endpoint in the background. The following documentation explain how to run healthchecks using the Flask REST hc endpoint.
This method is really useful for running healthchecks on a large number of databases.

Create file with list of databases to healthcheck
############

Create file with list of databases to healthcheck, e.g: db_hc.txt
::
  cavia_porcellus_funcgen_91_4
  homo_sapiens_funcgen_91_38
  mus_musculus_funcgen_91_38
  pan_troglodytes_funcgen_91_3

Or for all the database of a given division:

1. EG:
::
  RELEASE=38
  ./ensembl-production/scripts/process_division.sh EM mysql-eg-pan-prod ensembl_production $RELEASE > fungi_db_hc.txt

2. Ensembl:
::
  RELEASE=91
  ./ensembl-production/scripts/process_division.sh ens mysql-ens-sta-1 ensembl_production_${RELEASE} $RELEASE > db_hc.txt

Submit the jobs using Python REST hc endpoint:
#####

To Submit the job via the REST enpoint
::

  SERVER=$(mysql-ens-vertannot-staging details url) #e.g: mysql://ensro@mysql-ens-vertannot-staging:4573/
  GROUP=CoreHandover
  COMPARA_MASTER=$(mysql-ens-compara-prod-1 details url)
  LIVE=$(mysql-ensembl-mirror details url)
  STAGING=$(mysql-ens-sta-1 details url)
  PRODUCTION=$(mysql-ens-sta-1 details url)
  ENDPOINT=http://ens-prod-1.ebi.ac.uk:8000/hc/ #or http://eg-prod-01.ebi.ac.uk:7000/hc/ for EG
  DATA_FILE_PATH=/nfs/panda/ensembl/production/ensemblftp/data_files/
  RELEASE=91
  
  cd $BASE_DIR/ensembl-prodinf-core 
  for db in $(cat db_hc.txt); do
    echo "Submitting HC check for $db"
    output=`python ensembl_prodinf/hc_client.py --uri $ENDPOINT --db_uri "${SERVER}${db}" --production_uri "${PRODUCTION}ensembl_production_${RELEASE}" --staging_uri $STAGING --live_uri $LIVE --compara_uri "${COMPARA_MASTER}ensembl_compara_master" --hc_groups $GROUP --data_files_path $DATA_FILE_PATH  --action submit` || {
          echo "Cannot submit $db" 1>&2
          exit 2
    }
  done
  
To run multiple hcs and groups
#####

To run multiple hcs, you need to list each healthchecks name with a space between each name, e.g:
::
  --hc_names CoreForeignKeys AutoIncrement

You can also run individual healthchecks and healthcheck groups at the same time, e.g:
  --hc_groups CoreXrefs --hc_names CoreForeignKeys

Check job status
#####

You can check job status either on the production interface: `http://ens-prod-1.ebi.ac.uk:8000/#!/hc_list` or `http://eg-prod-01.ebi.ac.uk:7000/#!/hc_list` for EG

or using the Python REST API:

  ensembl_prodinf/db_copy_client.py --action list --uri http://ens-prod-1.ebi.ac.uk:8000/hc/
  
  or for EG:
   
  ensembl_prodinf/db_copy_client.py --action list --uri http://eg-prod-01.ebi.ac.uk:7000/hc/

Collate results
#####
If you have run the healthchecks on a large number of databases, you can collate all the results in one file:
::
  python ensembl-prodinf-core/ensembl_prodinf/hc_client.py --uri http://ens-prod-1.ebi.ac.uk:8000/hc/ --action collate --db_pattern ".*core_38_91.*" --output_file results.json

Convert results in readable form
#####
Convert Json result file in readable text format:
::
  cat results.json | json_reformat > results.txt

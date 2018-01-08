************************
Bulk Healthcheck submission
************************

Overview
########

The Production infrastructure interface allows to run healthecks on databases using the FLASK endpoint in the background. The following documentation explain how to run healthchecks using the Flask REST hc endpoint.
This method is really useful for running healthchecks on a large number of databases.

Create file with list of databases to healthcheck
############

Create file with list of databases to copy, e.g: db_hc.txt
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

  SERVER=$(mysql-ens-vertannot-staging details url)
  GROUP=CoreHandover
  COMPARA=$(mysql-ens-compara-prod-1 details url)
  LIVE=$(mysql-ensembl-mirror details url)
  STAGING=$(mysql-ens-sta-1 details url)
  PRODUCTION=$(mysql-ens-sta-1 details url)
  ENDPOINT=http://ens-prod-1:8000/hc/
  DATA_FILE_PATH=/nfs/panda/ensembl/production/ensemblftp/data_files/
  
  cd $BASE_DIR/ensembl-prodinf-core 
  for db in $(cat db_hc.txt); do
    echo "Submitting HC check for $db"
    output=`python ensembl_prodinf/hc_client.py -u $ENDPOINT -d "${SERVER}${db}" -p "${PRODUCTION}ensembl_production" -s $STAGING -l $LIVE -c "${COMPARA}ensembl_compara_master" -g $GROUP -dfp $DATA_FILE_PATH  -a submit` || {
          echo "Cannot submit $db" 1>&2
          exit 2
    }
  done

Check job status
#####

You can check job status either on the production interface: `http://ens-prod-1.ebi.ac.uk:8000/#!/hc_list`

or using the Python REST API:

  ensembl_prodinf/db_copy_client.py -a list -u http://ens-prod-1:8000/hc/

Collate results
#####
If you have run the healthchecks on a large number of databases, you can collate all the results in one file:
::
  python ensembl-prodinf-core/ensembl_prodinf/hc_client.py -u http://ens-prod-1:8000/hc/ -a collate -r ".*core_38_91.*" -o results.json

Convert results in readable form
#####
Convert Json result file in readable text format:
::
  cat results.json | json_reformat > results.txt

************************
Bulk Database Copy
************************

Overview
########

The Production infrastructure interface allows the load of database into the metadata database using the FLASK endpoint in the background. The following documentation explain how to load a database using the Flask REST database metadata endpoint.
This method is really useful for copying a large number of databases.

List of databases to load
############

Create file with list of databases to load, e.g: metadata_load.txt
::
  cavia_porcellus_funcgen_91_4
  homo_sapiens_funcgen_91_38
  mus_musculus_funcgen_91_38
  pan_troglodytes_funcgen_91_3

Or for all the database of a given division:

1. EG:
::
  EG_VERSION=38
  SERVER=mysql-eg-staging-2
  mysql --batch --raw --skip-column-names $($SERVER details mysql) information_schema -e "select schema_name from SCHEMATA where (schema_name like '%core%' or schema_name like '%otherfeatures%' or schema_name like '%rnaseq%' or schema_name like '%cdna%' or schema_name like '%funcgen%%' or schema_name like '%variation%' or schema_name like '%compara%' or schema_name like '%mart%') and ( schema_name like '%${EG_VERSION}_{ENS_VERSION}_%' or  schema_name like '%${EG_VERSION}' ) and schema_name not like 'master_schema%'" > eg_metadata_load.txt

2. Ensembl:
::
  ENS_VERSION=91
  SERVER=mysql-ensembl-mirror
  mysql --batch --raw --skip-column-names $($SERVER details mysql) information_schema -e "select schema_name from SCHEMATA where (schema_name like '%core%' or schema_name like '%otherfeatures%' or schema_name like '%rnaseq%' or schema_name like '%cdna%' or schema_name like '%funcgen%%' or schema_name like '%variation%' or schema_name like '%compara%' or schema_name like '%ontology%' or schema_name like '%mart%') and ( schema_name like '%_${ENS_VERSION}_%'  or  schema_name like '%${ENS_VERSION}' ) and schema_name not like 'master_schema%'" > metadata_load.txt
Submit the jobs using Python REST db copy endpoint:
#####

Clone the ensembl-prodinf-core repo:
::
  git clone https://github.com/Ensembl/ensembl-prodinf-core
  cd ensembl-prodinf-core

To Submit the job via the REST enpoint

For Ensembl:
::
  METADATA_SERVER=$(mysql-ens-meta-prod-1-ensprod details url) #e.g: mysql://ensprod:pass@mysql-ens-meta-prod-1:4483/
  DATABASE_SERVER=$(mysql-ens-general-prod-1 details url)
  ENDPOINT=http://ens-prod-1.ebi.ac.uk:8000/dbcopy/ #or http://eg-prod-01.ebi.ac.uk:7000/dbcopy/ for EG
  METADATA=ensembl_metadata
  ENS_VERSION=91
  RELEASE_DATE="2017-12-06"
  CURRENT_RELEASE=1
  EMAIL=john.doe@ebi.ac.uk
  UPDATE_TYPE="Other"
  COMMENT="Loading database for release 91"
  SOURCE="Pre release load"

  cd $BASE_DIR/ensembl-prodinf-core 
  for db in $(cat metadata_load.txt); 
  do ensembl_prodinf/metadata_client.py --action submit --uri ${ENDPOINT} --metadata_uri "${METADATA_SERVER}${METADATA}" --database_uri "${DATABASE_SERVER}${db}" --e_release ${ENS_VERSION} --release_date ${RELEASE_DATE} --current_release ${CURRENT_RELEASE} --email "${EMAIL}" --update_type "${UPDATE_TYPE}" --comment "${COMMENT}" --source "${SOURCE}";
  done

For EG:
::
  METADATA_SERVER=$(mysql-ens-meta-prod-1-ensprod details url) #e.g: mysql://ensprod:pass@mysql-ens-meta-prod-1:4483/
  DATABASE_SERVER=$(mysql-eg-staging-2 details url)
  ENDPOINT=http://ens-prod-1.ebi.ac.uk:8000/dbcopy/ #or http://eg-prod-01.ebi.ac.uk:7000/dbcopy/ for EG
  METADATA=ensembl_metadata
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
  do ensembl_prodinf/metadata_client.py --action submit --uri ${ENDPOINT} --metadata_uri "${METADATA_SERVER}${METADATA}" --database_uri "${DATABASE_SERVER}${db}" --e_release ${ENS_VERSION} --release_date ${RELEASE_DATE} --current_release ${CURRENT_RELEASE} --eg_release ${EG_VERSION} --email "${EMAIL}" --update_type "${UPDATE_TYPE}" --comment "${COMMENT}" --source "${SOURCE}";
  done


Script usage:
#####

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
#####

You can check job status either on the production interface: `http://ens-prod-1.ebi.ac.uk:8000/#!/metadata_list` or `http://eg-prod-01.ebi.ac.uk:7000/#!/metadata_list` for EG

or using the Python REST API:

  ensembl_prodinf/metadata_client.py --action list --uri http://ens-prod-1.ebi.ac.uk:8002
  
  or for EG:
  
  ensembl_prodinf/metadata_client.py --action list --uri http://eg-prod-01.ebi.ac.uk:7002
  
  

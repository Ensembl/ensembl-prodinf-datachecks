from ensembl_prodinf import HiveInstance
import time
import logging
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

parser = argparse.ArgumentParser(description='Copy a database')
parser.add_argument('--source_db_uri', metavar='s', type=str, nargs=1, required=True,
                    help='URI of database to copy from')
parser.add_argument('--target_db_uri', metavar='t', type=str, nargs=1, required=True,
                    help='URI of database to copy to')
parser.add_argument('--hive_uri', metavar='H', type=str, nargs=1, required=True,
                    help='URI of hive database')
parser.add_argument('--only_tables', metavar='o', type=str, nargs=1,
                    help='List of tables to copy')
parser.add_argument('--skip_tables', metavar='n', type=str, nargs=1,
                    help='List of tables to skip')
parser.add_argument('--update', action='store_true',
                    help='Incremental database update using rsync checksum')
parser.add_argument('--drop', action='store_true',
                    help='Drop database on Target server before copy')
parser.add_argument('--sleep', metavar='s', type=int, nargs='?', default=30,
                    help='Time to wait between polling for results')

args = parser.parse_args()
logging.debug(args)

logging.info("Connecting to hive")
hive = HiveInstance(args.hive_uri[0])

input = {"source_db_uri":args.source_db_uri[0] }
if args.target_db_uri != None:
    input['target_db_uri'] = args.target_db_uri[0]
if args.only_tables != None:
    input['only_tables'] = args.only_tables[0]
if args.skip_tables != None:
    input['skip_tables'] = args.skip_tables[0]
if args.update != None:
    input['update'] = args.update
if args.drop != None:
    input['drop'] = args.drop

logging.info("Submitting job with arguments "+str(input))
job = hive.create_job('copy_database',input)

logging.info("Job submitted with ID "+str(job.job_id))

output = None
while True:
    logging.info("Sleeping for %ds" % args.sleep)
    time.sleep(args.sleep)
    output = hive.get_result_for_job_id(job.job_id)        
    if output['status'] != 'incomplete':
        logging.debug("Job finished with status "+output['status'])
        break

if output['status'] == 'failed':
    msg = hive.get_job_failure_msg(job)
    logging.error("Job failed with error "+msg.msg)
else:
    print "Status: %s\n" % output['status']

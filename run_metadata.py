from ensembl_prodinf import HiveInstance
import time
import logging
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

parser = argparse.ArgumentParser(description='Load a database into metadata')
parser.add_argument('--metadata_uri', metavar='m', type=str, nargs=1, required=True,
                    help='URI of metadata database')
parser.add_argument('--database_uri', metavar='d', type=str, nargs=1, required=True,
                    help='URI of database to load')
parser.add_argument('--hive_uri', metavar='H', type=str, nargs=1, required=True,
                    help='URI of hive database')
parser.add_argument('--e_release', metavar='l', type=int, nargs=1,
                    help='Ensembl release number')
parser.add_argument('--release_date', metavar='r', type=str, nargs=1,
                    help='Release date')
parser.add_argument('--eg_release', metavar='g', type=int, nargs=1,
                    help='Ensembl Genomes release number')
parser.add_argument('--current_release', metavar='s', type=int, nargs=1,
                    help='Is this the current release')
parser.add_argument('--sleep', metavar='s', type=int, nargs='?', default=30,
                    help='Time to wait between polling for results')


args = parser.parse_args()
logging.debug(args)

logging.info("Connecting to hive")
hive = HiveInstance(args.hive_uri[0])

input = {"metadata_uri":args.metadata_uri[0] }
if args.database_uri != None:
    input['database_uri'] = args.database_uri[0]
if args.e_release != None:
    input['e_release'] = args.e_release[0]
if args.release_date != None:
    input['release_date'] = args.release_date[0]
if args.eg_release != None:
    input['eg_release'] = args.eg_release[0]
if args.current_release != None:
    input['current_release'] = args.current_release[0]

logging.info("Submitting job with arguments "+str(input))
job = hive.create_job('metadata_updater_processdb',input)

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
    msg = hive.get_job_failure_msg_by_id(job.job_id)
    logging.error("Job failed with error "+msg.msg)
else:
    print "Status: %s\n" % output['status']

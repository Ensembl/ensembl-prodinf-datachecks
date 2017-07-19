from ensembl_prodinf import HiveInstance
import time
import logging
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

parser = argparse.ArgumentParser(description='Run healthchecks on a database')
parser.add_argument('--db_uri', metavar='d', type=str, nargs=1, required=True,
                    help='URI of database to check')
parser.add_argument('--hive_uri', metavar='H', type=str, nargs=1, required=True,
                    help='URI of hive database')
parser.add_argument('--compara_uri', metavar='c', type=str, nargs=1,
                    help='URI of compara master database')
parser.add_argument('--prod_uri', metavar='p', type=str, nargs=1,
                    help='URI of production database')
parser.add_argument('--live_uri', metavar='l', type=str, nargs=1,
                    help='URI of live server')
parser.add_argument('--test', metavar='t', type=str, nargs='+',
                    help='Test(s) to run')
parser.add_argument('--group', metavar='g', type=str, nargs='+',
                    help='Test group(s) to run')
parser.add_argument('--sleep', metavar='s', type=int, nargs='?', default=30,
                    help='Time to wait between polling for results')

args = parser.parse_args()
logging.debug(args)

logging.info("Connecting to hive")
hive = HiveInstance(args.hive_uri[0])

input = {"db_uri":args.db_uri[0] }
if args.test != None:
    input['hc_names'] = args.test
if args.group != None:
    input['hc_groups'] = args.group

logging.info("Submitting job with arguments "+str(input))
job = hive.create_job('run_standalone_healthcheck',input)

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
    logging.error("Healthchecks could not be run")
else:
    print "Status: %s\n" % output['output']['status']
    if output['output']['failures']!=None:
        for db,fails in output['output']['failures'].items():
            for test,msg in fails.items():
                print "%s:\n %s" % (test, "\n".join(msg))


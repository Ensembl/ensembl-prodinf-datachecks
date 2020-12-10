#!/usr/bin/env python3


import argparse
from collections import namedtuple
import json
from ensembl_prodinf.db_copy_client import DbCopyClient


Job = namedtuple('Job',
                 'source_db_uri target_db_uri only_tables skip_tables update drop convert_innodb skip_optimize email')


ALL_DIVISIONS = ['vertebrates', 'protists', 'plants', 'fungi', 'metazoa', 'bacteria']


NONVERT_DIVISIONS = set(['plants', 'metazoa', 'fungi', 'protists'])


STATUSES = [
    'new_genomes',
    'updated_assemblies',
    'renamed_genomes',
    'updated_annotations'
]


def parse_arguments():
    parser = argparse.ArgumentParser(description='Submit Copy Jobs form Report Updates')
    parser.add_argument('-u', '--uri', required=True,
                        help='Copy database REST service URI')
    parser.add_argument('-f', '--report_file', type=argparse.FileType('r'), required=True,
                        help='Report file in JSON format')
    parser.add_argument('-s', '--source_server', required=True,
                        help='Source type (e.g. sta-a, sta-b) or server name (e.g. mysql-ens-general-prod-1:4525)')
    parser.add_argument('-t', '--target_server', required=True,
                        help='Source type (e.g. sta-a, sta-b) or server name (e.g. mysql-ens-general-prod-1:4525)')
    parser.add_argument('-e', '--email', required=True,
                        help='Email where to send the report')
    parser.add_argument('-c', '--config_file', type=argparse.FileType('r'), required=True,
                        help='Config file containing staging servers')
    parser.add_argument('--include_divisions', nargs='+', choices=ALL_DIVISIONS,
                        help='Divisions to include in the copy')
    parser.add_argument('--exclude_divisions', nargs='+', choices=ALL_DIVISIONS,
                        help='Divisions to exclude from the copy')
    parser.add_argument('--statuses', nargs='+', choices=STATUSES,
                        help='Copy only some types or reported databases')
    parser.add_argument('-I', '--convert_innodb',
                        help='Convert InnoDB tables to MyISAM after copy')
    parser.add_argument('-K', '--skip_optimize',
                        help='Skip the database optimization step after the copy. Useful for very large databases')
    parser.add_argument('-D', '--dry_run', action='store_true',
                        help='Prints copy jobs without submitting them.')
    args = parser.parse_args()
    return args


def select_serv(servers, division, name):
    division = 'nonvertebrates' if division in NONVERT_DIVISIONS else division
    server = servers[division].get(name.lower())
    return server if server else name


def select_divisions(include_divisions, exclude_divisions):
    divisions = NONVERT_DIVISIONS | set(ALL_DIVISIONS)
    if include_divisions:
        divisions = divisions & set(include_divisions)
    if exclude_divisions:
        divisions = divisions - set(exclude_divisions)
    return divisions


def make_jobs(report, divisions, statuses, servers, args):
    jobs = set()
    for division in divisions:
        for status in statuses:
            for elem in report[division][status].values():
                dbname = elem['database']
                src_serv = select_serv(servers, division, args.source_server)
                tgt_serv = select_serv(servers, division, args.target_server)
                job = Job(
                    source_db_uri='{}/{}'.format(src_serv, dbname),
                    target_db_uri='{}/{}'.format(tgt_serv, dbname),
                    only_tables=None,
                    skip_tables=None,
                    update=None,
                    drop=None,
                    convert_innodb=args.convert_innodb,
                    skip_optimize=args.skip_optimize,
                    email=args.email
                )
                jobs.add(job)
    return jobs


def submit_jobs(client, jobs, args):
    for job in jobs:
        if args.dry_run:
            print(job)
        else:
            client.submit_job(*job)


def main():
    args = parse_arguments()
    divisions = select_divisions(args.include_divisions, args.exclude_divisions)
    statuses = args.statuses if args.statuses else STATUSES
    servers = json.load(args.config_file)
    report = json.load(args.report_file)
    copy_client = DbCopyClient(args.uri)
    jobs = make_jobs(report, divisions, statuses, servers, args)
    submit_jobs(copy_client, jobs, args)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3


import argparse
from collections import namedtuple
import json
import os
import sqlalchemy as sa
from ensembl_prodinf.db_copy_client import DbCopyClient
from ensembl_prodinf.db_utils import validate_mysql_url


CopyJob = namedtuple('CopyJob',
    'source_db_uri target_db_uri only_tables skip_tables update drop convert_innodb skip_optimize email')


Database = namedtuple('Database', 'name division')


ALL_DIVISIONS = ['vertebrates', 'protists', 'plants', 'fungi', 'metazoa', 'bacteria']


DB_TYPES = ['core', 'funcgen', 'variation', 'otherfeatures', 'rnaseq', 'cdna', 'vega']


NONVERT_DIVISIONS = {'plants', 'metazoa', 'fungi', 'protists'}


ENS_DIVISION_MAP = {
    'EnsemblVertebrates': 'vertebrates',
    'EnsemblProtists': 'nonvertebrates',
    'EnsemblFungi': 'nonvertebrates',
    'EnsemblMetazoa': 'nonvertebrates',
    'EnsemblPlants': 'nonvertebrates',
    'EnsemblPan': 'nonvertebrates',
    'EnsemblBacteria': 'bacteria'
}


STATUSES = [
    'new_genomes',
    'updated_assemblies',
    'renamed_genomes',
    'updated_annotations'
]


def parse_arguments():
    parser = argparse.ArgumentParser(description='Submit Copy Jobs form Report Updates')
    parser.add_argument('-f', '--report-file', type=argparse.FileType('r'), required=True,
                        help='Report file in JSON format')
    parser.add_argument('-s', '--source-server', required=True,
                        help='Source type (e.g. sta-a, sta-b) or server name (e.g. mysql://user[:password]@server:port)')
    parser.add_argument('-t', '--target-server', required=True,
                        help='Source type (e.g. sta-a, sta-b) or server name (e.g. mysql://user[:password]@server:port))')
    parser.add_argument('-e', '--email', required=True,
                        help='Email where to send the report')
    parser.add_argument('-c', '--config-file', type=argparse.FileType('r'), required=True,
                        help='Config file containing staging servers')
    parser.add_argument('-v', '--ens-version', required=True,
                        help='ENSEMBL version from where to compute the changes')
    parser.add_argument('--dbcopy-url',
                        help='Copy database REST service URL')
    parser.add_argument('--metadata-url',
                        help='Metadata database MySQL URL')
    parser.add_argument('--include-divisions', nargs='+', choices=ALL_DIVISIONS,
                        help='Divisions to include in the copy')
    parser.add_argument('--exclude-divisions', nargs='+', choices=ALL_DIVISIONS,
                        help='Divisions to exclude from the copy')
    parser.add_argument('--include-dbtypes', nargs='+', choices=DB_TYPES,
                        help='Database types to include in the copy')
    parser.add_argument('--exclude-dbtypes', nargs='+', choices=DB_TYPES,
                        help='Database types to exclude from the copy')
    parser.add_argument('--statuses', nargs='+', choices=STATUSES,
                        help='Copy only some types or reported databases')
    parser.add_argument('-I', '--convert-innodb',
                        help='Convert InnoDB tables to MyISAM after copy')
    parser.add_argument('-K', '--skip-optimize',
                        help='Skip the database optimization step after the copy. Useful for very large databases')
    parser.add_argument('-D', '--dry-run', action='store_true',
                        help='Prints copy jobs without submitting them.')
    args = parser.parse_args()
    return args


def select_serv(servers, ens_division, name):
    division = ENS_DIVISION_MAP[ens_division]
    server = servers[division].get(name.lower())
    return server if server else name


def select_divisions(include_divisions, exclude_divisions):
    divisions = NONVERT_DIVISIONS | set(ALL_DIVISIONS)
    if include_divisions:
        divisions = divisions & set(include_divisions)
    if exclude_divisions:
        divisions = divisions - set(exclude_divisions)
    return divisions


def select_dbtypes(include_dbtypes, exclude_dbtypes):
    dbtypes = set(DB_TYPES)
    if include_dbtypes:
        dbtypes = dbtypes & set(include_dbtypes)
    if exclude_dbtypes:
        dbtypes = dbtypes - set(exclude_dbtypes)
    return dbtypes


def parse_species(report, args):
    divisions = select_divisions(args.include_divisions, args.exclude_divisions)
    statuses = args.statuses if args.statuses else STATUSES
    species = set()
    for division in divisions:
        for status in statuses:
            for name in report[division][status]:
                species.add(name)
    return species


def get_databases(metadata_engine, species, args):
    sql = """
        SELECT gd.dbname, d.name
        FROM genome g
        JOIN organism o ON g.organism_id = o.organism_id
        JOIN data_release dr ON g.data_release_id = dr.data_release_id
        JOIN genome_database gd ON g.genome_id = gd.genome_id
        JOIN division d on g.division_id = d.division_id
        WHERE dr.ensembl_version = :ens_version
        AND gd.type IN :db_types
        AND o.name IN :species;
    """
    dbtypes = select_dbtypes(args.include_dbtypes, args.exclude_dbtypes)
    with metadata_engine.connect() as conn:
        query = conn.execute(sa.text(sql),
                             ens_version=args.ens_version,
                             db_types=tuple(dbtypes),
                             species=tuple(species))
        result = query.fetchall()
    return set(map(lambda x: Database(x[0], x[1]), result))


def make_jobs(databases, servers, args):
    jobs = set()
    for database in databases:
        src_serv = select_serv(servers, database.division, args.source_server)
        tgt_serv = select_serv(servers, database.division, args.target_server)
        job = CopyJob(
            source_db_uri=os.path.join(src_serv, database.name),
            target_db_uri=os.path.join(tgt_serv, database.name),
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
    config = json.load(args.config_file)
    report = json.load(args.report_file)
    servers = config['servers']
    dbcopy_url = args.dbcopy_url or config['dbcopy_url']
    metadata_url = args.metadata_url or config['metadata_url']
    metadata_url = validate_mysql_url(metadata_url)
    metadata_engine = sa.create_engine(metadata_url)
    copy_client = DbCopyClient(dbcopy_url)
    species = parse_species(report, args)
    databases = get_databases(metadata_engine, species, args)
    jobs = make_jobs(databases, servers, args)
    submit_jobs(copy_client, jobs, args)


if __name__ == '__main__':
    main()

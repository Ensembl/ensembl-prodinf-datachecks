from collections import namedtuple
import unittest
from ensembl_prodinf.copy_from_report import make_jobs, parse_species, CopyJob, Database


SpeciesArgs = namedtuple('SpeciesArgs',
                         'include_divisions exclude_divisions statuses')
JobArgs = namedtuple('JobArgs',
                     'source_server target_server convert_innodb skip_optimize email')


class TestCopyFromReport(unittest.TestCase):
    def test_parse_species(self):
        report = {
           "metazoa" : {
              "new_genomes" : {
                 "bemisia_tabaci_ssa1ug" : {
                    "database" : "bemisia_tabaci_ssa1ug_core_50_103_1",
                 },
                 "bemisia_tabaci_sweetpotug" : {
                    "database" : "bemisia_tabaci_sweetpotug_core_50_103_1",
                 }
              },
              "updated_assemblies" : {
                 "drosophila_grimshawi" : {
                    "database" : "drosophila_grimshawi_core_50_103_2",
                 },
                 "drosophila_virilis" : {
                    "database" : "drosophila_virilis_core_50_103_2",
                 },
              },
              "renamed_genomes" : {},
              "updated_annotations" : {}
           },
           "plants" : {
              "new_genomes" : {},
              "updated_assemblies" : {},
              "renamed_genomes" : {
                 "panicum_hallii" : {
                    "database" : "panicum_hallii_core_50_103_1",
                 },
              },
              "updated_annotations" : {}
           },
           "bacteria" : {
              "new_genomes" : {},
              "updated_assemblies" : {},
              "removed_genomes" : {},
              "renamed_genomes" : {},
              "updated_annotations" : {}
           },
           "protists" : {
              "new_genomes" : {},
              "updated_assemblies" : {},
              "removed_genomes" : {},
              "renamed_genomes" : {},
              "updated_annotations" : {}
           },
           "fungi" : {
              "new_genomes" : {},
              "updated_assemblies" : {},
              "removed_genomes" : {},
              "renamed_genomes" : {},
              "updated_annotations" : {}
           },
           "vertebrates" : {
              "new_genomes" : {},
              "updated_assemblies" : {
                 "anabas_testudineus" : {
                    "database" : "anabas_testudineus_core_103_12",
                 },
                 "ailuropoda_melanoleuca" : {
                    "database" : "ailuropoda_melanoleuca_core_103_2",
                 },
              },
              "renamed_genomes" : {},
              "updated_annotations" : {}
           }
        }
        args = SpeciesArgs(
            include_divisions=None,
            exclude_divisions=None,
            statuses=None
        )
        parsed_species = parse_species(report, args)
        expected_species = {
            'ailuropoda_melanoleuca',
            'drosophila_grimshawi',
            'anabas_testudineus',
            'bemisia_tabaci_ssa1ug',
            'panicum_hallii',
            'drosophila_virilis',
            'bemisia_tabaci_sweetpotug'
        }
        self.assertSetEqual(expected_species, parsed_species)

    def test_make_jobs(self):
        servers = {
            'vertebrates': {
                'sta-a': 'vert-server-a',
                'sta-b': 'vert-server-b'
            },
            'nonvertebrates': {
                'sta-a': 'nonvert-server-a',
                'sta-b': 'nonvert-server-b'
            }
        }
        args = JobArgs(
            source_server='sta-a',
            target_server='sta-b',
            convert_innodb=None,
            skip_optimize=None,
            email='email@ebi.ac.uk'
        )
        databases = set([
            Database(name='anabas_testudineus_core_103_12',
                division='EnsemblVertebrates'),
            Database(name='ailuropoda_melanoleuca_core_103_2',
                division='EnsemblVertebrates'),
            Database(name='panicum_hallii_core_50_103_1',
                division='EnsemblPlants'),
            Database(name='bemisia_tabaci_ssa1ug_core_50_103_1',
                division='EnsemblMetazoa'),
            Database(name='bemisia_tabaci_sweetpotug_core_50_103_1',
                division='EnsemblMetazoa'),
            Database(name='drosophila_grimshawi_core_50_103_2',
                division='EnsemblMetazoa'),
            Database(name='drosophila_virilis_core_50_103_2',
                division='EnsemblMetazoa')
        ])
        jobs = make_jobs(databases, servers, args)
        expected_jobs = set([
            CopyJob(source_db_uri='vert-server-a/anabas_testudineus_core_103_12',
                    target_db_uri='vert-server-b/anabas_testudineus_core_103_12',
                    only_tables=None,
                    skip_tables=None,
                    update=None,
                    drop=None,
                    convert_innodb=None,
                    skip_optimize=None,
                    email='email@ebi.ac.uk'),
            CopyJob(source_db_uri='vert-server-a/ailuropoda_melanoleuca_core_103_2',
                    target_db_uri='vert-server-b/ailuropoda_melanoleuca_core_103_2',
                    only_tables=None,
                    skip_tables=None,
                    update=None,
                    drop=None,
                    convert_innodb=None,
                    skip_optimize=None,
                    email='email@ebi.ac.uk'),
            CopyJob(source_db_uri='nonvert-server-a/panicum_hallii_core_50_103_1',
                    target_db_uri='nonvert-server-b/panicum_hallii_core_50_103_1',
                    only_tables=None,
                    skip_tables=None,
                    update=None,
                    drop=None,
                    convert_innodb=None,
                    skip_optimize=None,
                    email='email@ebi.ac.uk'),
            CopyJob(source_db_uri='nonvert-server-a/bemisia_tabaci_ssa1ug_core_50_103_1',
                    target_db_uri='nonvert-server-b/bemisia_tabaci_ssa1ug_core_50_103_1',
                    only_tables=None,
                    skip_tables=None,
                    update=None,
                    drop=None,
                    convert_innodb=None,
                    skip_optimize=None,
                    email='email@ebi.ac.uk'),
            CopyJob(source_db_uri='nonvert-server-a/bemisia_tabaci_sweetpotug_core_50_103_1',
                    target_db_uri='nonvert-server-b/bemisia_tabaci_sweetpotug_core_50_103_1',
                    only_tables=None,
                    skip_tables=None,
                    update=None,
                    drop=None,
                    convert_innodb=None,
                    skip_optimize=None,
                    email='email@ebi.ac.uk'),
            CopyJob(source_db_uri='nonvert-server-a/drosophila_grimshawi_core_50_103_2',
                    target_db_uri='nonvert-server-b/drosophila_grimshawi_core_50_103_2',
                    only_tables=None,
                    skip_tables=None,
                    update=None,
                    drop=None,
                    convert_innodb=None,
                    skip_optimize=None,
                    email='email@ebi.ac.uk'),
            CopyJob(source_db_uri='nonvert-server-a/drosophila_virilis_core_50_103_2',
                    target_db_uri='nonvert-server-b/drosophila_virilis_core_50_103_2',
                    only_tables=None,
                    skip_tables=None,
                    update=None,
                    drop=None,
                    convert_innodb=None,
                    skip_optimize=None,
                    email='email@ebi.ac.uk')
        ])
        self.assertSetEqual(jobs, expected_jobs)


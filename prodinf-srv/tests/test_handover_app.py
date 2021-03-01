import unittest
from handover_app import valid_handover


class TestHandover(unittest.TestCase):
    def test_valid_handover_valid(self):
        release = '101'
        valid_uris = [
            'mysql://ensro@mysql-ens-vertannot-staging:4573/ensembl_compara_fungi_48_101',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/ensembl_compara_metazoa_48_101',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/ensembl_compara_pan_homology_48_101',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/ensembl_compara_plants_48_101',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/ensembl_compara_protists_48_101',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/ensembl_compara_bacteria_48_101',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/ensembl_compara_101',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/bacteria_0_collection_core_48_101_1',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/bacteria_100_collection_core_48_101_1',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/bacteria_101_collection_core_48_101_1',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/fungi_ascomycota1_collection_core_48_101_1',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/fungi_ascomycota2_collection_core_48_101_1',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/capra_hircus_core_101_1',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/ovis_aries_core_101_31',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/capra_hircus_core_101_1',
        ]
        for uri in valid_uris:
            doc = {'_source': {'params': {'src_uri': uri}}}
            try:
                self.assertTrue(valid_handover(doc, release))
            except AssertionError as e:
                raise AssertionError('Invalid Uri: %s' % uri) from e

    def test_valid_handover_invalid(self):
        release = '101'
        invalid_uris = [
            'mysql://ensro@mysql-ens-vertannot-staging:4573/zonotrichia_albicollis_rnaseq_96_101',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/zonotrichia_albicollis_otherfeatures_96_101',
            'mysql://ensro@mysql-ens-vertannot-staging:4573/zonotrichia_albicollis_core_96_101',
        ]
        for uri in invalid_uris:
            doc = {'_source': {'params': {'src_uri': uri}}}
            self.assertFalse(valid_handover(doc, release))

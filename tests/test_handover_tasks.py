from ensembl_prodinf import handover_tasks as ht
import unittest


class ParseDbInfosTest(unittest.TestCase):
    def test_accepted_species_patterns(self):
        names = (
            'homo_sapiens_cdna_100_38',
            'homo_sapiens_core_100_38',
            'homo_sapiens_funcgen_100_38',
            'homo_sapiens_otherfeatures_100_38',
            'homo_sapiens_rnaseq_100_38',
            'homo_sapiens_variation_100_38',
            'bacteria_0_collection_core_47_100_1',
            'bacteria_100_collection_core_47_100_1',
            'bacteria_101_collection_core_47_100_1',
            'fungi_ascomycota1_collection_core_47_100_1',
            'fungi_ascomycota2_collection_core_47_100_1',
            'hordeum_vulgare_core_47_100_3',
            'hordeum_vulgare_funcgen_47_100_3',
            'hordeum_vulgare_otherfeatures_47_100_3',
            'hordeum_vulgare_variation_47_100_3',
            'protists_alveolata1_collection_core_47_100_1',
            'protists_amoebozoa1_collection_core_47_100_1',
            'protists_apusozoa1_collection_core_47_100_1',
            'protists_choanoflagellida1_collection_core_47_100_1',
            'protists_cryptophyta1_collection_core_47_100_1',
            'protists_euglenozoa1_collection_core_47_100_1',
            'anas_platyrhynchos_platyrhynchos_core_100_1',
            'anas_platyrhynchos_platyrhynchos_funcgen_100_1',
            'anas_platyrhynchos_platyrhynchos_rnaseq_100_1',
            'canis_lupus_familiarisbasenji_core_100_11',
            'canis_lupus_familiarisbasenji_funcgen_100_11'
        )
        parsed_names = (
            ('homo_sapiens', 'cdna', '100', '38'),
            ('homo_sapiens', 'core', '100', '38'),
            ('homo_sapiens', 'funcgen', '100', '38'),
            ('homo_sapiens', 'otherfeatures', '100', '38'),
            ('homo_sapiens', 'rnaseq', '100', '38'),
            ('homo_sapiens', 'variation', '100', '38'),
            ('bacteria_0_collection', 'core', '100', '1'),
            ('bacteria_100_collection', 'core', '100', '1'),
            ('bacteria_101_collection', 'core', '100', '1'),
            ('fungi_ascomycota1_collection', 'core', '100', '1'),
            ('fungi_ascomycota2_collection', 'core', '100', '1'),
            ('hordeum_vulgare', 'core', '100', '3'),
            ('hordeum_vulgare', 'funcgen', '100', '3'),
            ('hordeum_vulgare', 'otherfeatures', '100', '3'),
            ('hordeum_vulgare', 'variation', '100', '3'),
            ('protists_alveolata1_collection', 'core', '100', '1'),
            ('protists_amoebozoa1_collection', 'core', '100', '1'),
            ('protists_apusozoa1_collection', 'core', '100', '1'),
            ('protists_choanoflagellida1_collection', 'core', '100', '1'),
            ('protists_cryptophyta1_collection', 'core', '100', '1'),
            ('protists_euglenozoa1_collection', 'core', '100', '1'),
            ('anas_platyrhynchos_platyrhynchos', 'core', '100', '1'),
            ('anas_platyrhynchos_platyrhynchos', 'funcgen', '100', '1'),
            ('anas_platyrhynchos_platyrhynchos', 'rnaseq', '100', '1'),
            ('canis_lupus_familiarisbasenji', 'core', '100', '11'),
            ('canis_lupus_familiarisbasenji', 'funcgen', '100', '11')
        )
        for parsed_name, database_name in zip(parsed_names, names):
            self.assertEqual(parsed_name, ht.parse_db_infos(database_name))

    def test_accepted_compara_patterns(self):
        names = (
            'ensembl_compara_fungi_47_100',
            'ensembl_compara_metazoa_47_100',
            'ensembl_compara_pan_homology_47_100',
            'ensembl_compara_plants_47_100',
            'ensembl_compara_protists_47_100',
            'ensembl_compara_bacteria_47_100',
            'ensembl_compara_100'
        )
        parsed_names = (
            ('fungi', 'compara', None, None),
            ('metazoa', 'compara', None, None),
            ('pan', 'compara', None, None),
            ('plants', 'compara', None, None),
            ('protists', 'compara', None, None),
            ('bacteria', 'compara', None, None),
            ('compara', 'compara', None, None)
        )
        for parsed_name, database_name in zip(parsed_names, names):
            self.assertEqual(parsed_name, ht.parse_db_infos(database_name))

    def test_accepted_ancestral_patterns(self):
        names = (
            'ensembl_ancestral_100',
            'ensembl_ancestral_1'
        )
        parsed = ('ensembl', 'ancestral', None, None)
        for database_name in names:
            self.assertEqual(parsed, ht.parse_db_infos(database_name))

    def test_rejected_species_patterns(self):
        invalid_names = (
            'homo_sapiens_cdna_100',
            'bacteria_0_collection_47_100_1',
            'ensembl_ancestral',
            'ensembl_compara_100_grch37'
        )
        for invalid_database_name in invalid_names:
            self.assertRaises(ValueError, ht.parse_db_infos, invalid_database_name)


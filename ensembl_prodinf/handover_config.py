'''
Created on 11 Dec 2017

@author: dstaines
'''
import os
from ensembl_prodinf.config import load_config_yaml


config_file_path = os.environ.get('HANDOVER_CORE_CONFIG_PATH')
file_config = load_config_yaml(config_file_path)


hc_uri = os.environ.get("HC_URI",
                        file_config.get('hc_uri', "http://127.0.0.1:5001/"))
dc_uri = os.environ.get("DC_URI",
                        file_config.get('dc_uri', "http://127.0.0.1:5006/"))
hc_web_uri = os.environ.get("HC_WEB_URI",
                            file_config.get('hc_web_uri',
                                            "http://127.0.0.1:9000/#!/hc_result/"))
copy_uri = os.environ.get("COPY_URI",
                          file_config.get('copy_uri', "http://127.0.0.1:5002/"))
copy_web_uri = os.environ.get("COPY_WEB_URI",
                              file_config.get('copy_web_uri',
                                              "http://127.0.0.1:9000/#!/copy_result/"))
meta_uri = os.environ.get("META_URI",
                          file_config.get('meta_uri',
                                          "http://127.0.0.1:5003/"))
meta_web_uri = os.environ.get("META_WEB_URI",
                              file_config.get('meta_web_uri',
                                              "http://127.0.0.1:9000/#!/metadata_result/"))
event_uri = os.environ.get("EVENT_URI",
                           file_config.get('event_uri',
                                           'http://127.0.0.1:5004/'))
staging_uri = os.environ.get("STAGING_URI",
                             file_config.get('staging_uri',
                                             "mysql://user@staging:3306/"))
secondary_staging_uri = os.environ.get("SECONDARY_STAGING_URI",
                                       file_config.get('secondary_staging_uri',
                                                       "mysql://user@staging2:3306/"))
live_uri = os.environ.get("LIVE_URI",
                          file_config.get('live_uri',
                                          "mysql://user@127.0.0.1:3306/"))
secondary_live_uri = os.environ.get("SECONDARY_LIVE_URI",
                          file_config.get('secondary_live_uri',
                                          "mysql://user@127.0.0.1:3306/"))
production_uri = os.environ.get("PRODUCTION_URI",
                                file_config.get('production_uri',
                                                "mysql://user@127.0.0.1:3306/ensembl_production"))
compara_uri = os.environ.get("COMPARA_URI",
                             file_config.get('compara_uri',
                                             "mysql://user@127.0.0.1:3306/"))
compara_plants_uri = os.environ.get("COMPARA_PLANTS_URI",
                                    file_config.get('compara_plants_uri',
                                                    "mysql://user@127.0.0.1:3306/"))
compara_metazoa_uri = os.environ.get("COMPARA_METAZOA_URI",
                                     file_config.get('compara_metazoa_uri',
                                                     "mysql://user@127.0.0.1:3306/"))
compara_grch37_uri = os.environ.get("COMPARA_GRCH37_URI",
                                     file_config.get('compara_grch37_uri',
                                                     "mysql://user@127.0.0.1:3306/"))
core_handover_group = os.environ.get("CORE_HANDOVER_GROUP",
                                     file_config.get('core_handover_group',
                                                     "GenebuildPostHandoverService"))
variation_handover_group = os.environ.get("VARIATION_HANDOVER_GROUP",
                                          file_config.get('variation_handover_group',
                                                          "VariationRelease"))
funcgen_handover_group = os.environ.get("FUNCGEN_HANDOVER_GROUP",
                                        file_config.get('funcgen_handover_group',
                                                        "FuncgenIntegrity"))
compara_handover_group = os.environ.get("COMPARA_HANDOVER_GROUP",
                                        file_config.get('compara_handover_group',
                                                        "ComparaIntegrity"))
ancestral_handover_group = os.environ.get("ANCESTRAL_HANDOVER_GROUP",
                                          file_config.get('ancestral_handover_group',
                                                          "ComparaAncestral"))
compara_pan_handover_group = os.environ.get("COMPARA_PAN_HANDOVER_GROUP",
                                            file_config.get('compara_pan_handover_group',
                                                            "ComparaPanIntegrity"))
smtp_server = os.environ.get("SMTP_SERVER",
                             file_config.get('smtp_server', 'smtp.ebi.ac.uk'))
report_server = os.environ.get("REPORT_SERVER",
                               file_config.get('report_server',
                                               "amqp://guest:guest@localhost:5672/%2F"))
report_exchange = os.environ.get("REPORT_EXCHANGE",
                                 file_config.get('report_exchange', 'report_exchange'))
data_files_path = os.environ.get("DATA_FILE_PATH" ,
                                 file_config.get('data_files_path', '/data_files/'))
allowed_database_types = os.environ.get("ALLOWED_DATABASE_TYPES" ,
                                        file_config.get('allowed_database_types',
                                                        'core,rnaseq,cdna,otherfeatures,variation,funcgen,compara,ancestral'))

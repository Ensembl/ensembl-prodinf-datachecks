'''
Created on 11 Dec 2017

@author: dstaines
'''
import os

from ensembl_prodinf.config import load_config_yaml

config_file_path = os.environ.get('HANDOVER_CORE_CONFIG_PATH', os.path.join(os.path.dirname(__file__), 'handover_config.dev.yaml'))
file_config = load_config_yaml(config_file_path)

dc_uri = os.environ.get("DC_URI",
                        file_config.get('dc_uri', "http://127.0.0.1:5006/"))
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
smtp_server = os.environ.get("SMTP_SERVER",
                             file_config.get('smtp_server', 'smtp.ebi.ac.uk'))
report_server = os.environ.get("REPORT_SERVER",
                               file_config.get('report_server',
                                               "amqp://guest:guest@localhost:5672/%2F"))
report_exchange = os.environ.get("REPORT_EXCHANGE",
                                 file_config.get('report_exchange', 'report_exchange'))
report_exchange_type = os.environ.get("REPORT_EXCHANGE_TYPE",
                                      file_config.get('report_exchange_type', 'topic'))
data_files_path = os.environ.get("DATA_FILE_PATH",
                                 file_config.get('data_files_path', '/data_files/'))
allowed_database_types = os.environ.get("ALLOWED_DATABASE_TYPES",
                                        file_config.get('allowed_database_types',
                                                        'core,rnaseq,cdna,otherfeatures,variation,'
                                                        'funcgen,compara,ancestral'))
production_email = os.environ.get("PRODUCTION_EMAIL",
                                  file_config.get('production_email',
                                                  'email@ebi.ac.uk'))
allowed_divisions = os.environ.get("ALLOWED_DIVISIONS",
                                   file_config.get('allowed_divisions',
                                                   'vertebrates'))


dispatch_targets = file_config.get('dispatch_targets', [])
compara_species = file_config.get('compara_species', [])


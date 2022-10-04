# See the NOTICE file distributed with this work for additional information
#   regarding copyright ownership.
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#       http://www.apache.org/licenses/LICENSE-2.0
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import unittest
import pkg_resources
from pathlib import Path
import ensembl.production.datacheck.exceptions
from ensembl.production.datacheck.config import DCConfigLoader, DatacheckConfig


class TestConfigLoader(unittest.TestCase):

    def test_config_load_104(self):
        # DuplicateComparaMemberXref was not implemented at this point
        config = DCConfigLoader.load_config('104')
        self.assertNotIn('DuplicateComparaMemberXref', config.keys())

    def test_config_load_106(self):
        # DuplicateComparaMemberXref was implemented at this point
        config = DCConfigLoader.load_config('106')
        self.assertIn('DuplicateComparaMemberXref', config.keys())

    def test_config_load_fallback(self):
        config = DCConfigLoader.load_config()
        # Load main instead
        self.assertIn('SpeciesCommonName', config.keys())

class TestAPPVersion(unittest.TestCase):

    def test_config_app_version(self):
        
        with open(Path(__file__).parent.parent.parent / 'VERSION') as f:
            version_file = f.read().strip('\n')
            
        version = pkg_resources.require("datacheck")[0].version
        version_config = DatacheckConfig.APP_VERSION
        self.assertEqual(version, version_config)
        self.assertEqual(version, version_file)
        self.assertEqual(version_file, version_config )

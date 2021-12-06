# .. See the NOTICE file distributed with this work for additional information
#     regarding copyright ownership.
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#         http://www.apache.org/licenses/LICENSE-2.0
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import unittest
from flask import Flask, render_template, jsonify, Request, request
from werkzeug.test import EnvironBuilder
from ensembl.production.datacheck.forms import DatacheckSubmissionForm

valid_payload = {
    "server-server_name": "sta-1",
    "server-source": "dbname",
    "server-dbname": "homo",
    "server-species": "",
    "server-db_type": "core",
    "datacheck-datacheck_name": "AlignFeatureExternalDB",
    "datacheck-datacheck_group": "annotation",
    "datacheck-datacheck_type": "critical",
    "submitter-email": "test@gmail.com",
    "submitter-tag": "Testcase"
}


def set_dynamic_choices(form):
    for name, field in form._fields.items():
        if name == 'server':
            field.server_name.choices = [('sta-1', 'sta-1')]
    return form


class TestDatacheckForm(unittest.TestCase):
    def setUp(self):
        self.app = self.create_app()
        self.client = self.app.test_client()
        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def create_app(self):
        app = Flask(__name__)
        app.secret_key = "EnsemblDatacheckFormValidate"

        @app.route("/formvalidate/", methods=("POST",))
        def form_submit():
            form = DatacheckSubmissionForm(request.form)
            form = set_dynamic_choices(form)
            if form.validate():
                return {'valid': True}

            return {'Valid': False}

        return app

    def request(self, *args, **kwargs):
        return self.app.test_request_context(*args, **kwargs)


class TestValidateOnSubmit(TestDatacheckForm):
    def test_not_submitted(self):
        with self.request(method='GET', data={}):
            f = DatacheckSubmissionForm(request.form)
            self.assertEqual(f.validate(), False)

    def test_submitted_not_valid(self):
        with self.request(method='POST', data={}):
            f = DatacheckSubmissionForm(request.form)
            self.assertEqual(f.validate(), False)

    def test_submitted_and_valid(self):
        with self.request(method='POST', data=valid_payload):
            f = DatacheckSubmissionForm(request.form)
            f = set_dynamic_choices(f)
            self.assertEqual(f.validate(), True)


class TestCSRF(TestDatacheckForm):

    def test_valid(self):
        builder = EnvironBuilder(method='POST', data={**valid_payload})
        env = builder.get_environ()
        req = Request(env)
        f = DatacheckSubmissionForm(req.form)
        f = set_dynamic_choices(f)
        self.assertTrue(f.validate())

    def test_form(self):
        response = self.client.post("/formvalidate/",
                                    data={
                                        'server_url': '',
                                        'dbname': None,
                                        'species': None,
                                        'division': None,
                                        'db_type': None,
                                        'datacheck_names': [],
                                        'datacheck_groups': [],
                                        'datacheck_types': [],
                                        'email': '',
                                        'tag': ''
                                    },
                                    )
        assert response.status_code == 200

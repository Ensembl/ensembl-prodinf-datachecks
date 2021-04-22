import unittest
from flask import Flask, render_template, jsonify, Request, request
from werkzeug.test import EnvironBuilder
from ensembl.production.datacheck.forms import DatacheckSubmissionForm

vaild_payload ={
                'server_url':'mysql://ensro@mysql-ens-sta-1:4512/' ,
                'dbname': 'homo_sapiens_core_38_101',
                'species': None,
                'division': None,
                'db_type': 'core',
                'datacheck_names': 'AlignFeatureExternalDB',
                'datacheck_groups': 'annotation',
                'datacheck_types': 'critical',
                'email': 'test@ebi.ac.uk',
                'tag': 'Testcase for datacheck form'
                }

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
            form = DatacheckSubmissionForm(csrf_enabled=False)

            if form.validate_on_submit():
                return {'valid': True}

            return {'Valid': False}

        return app

    def request(self,*args, **kwargs):
        return self.app.test_request_context(*args, **kwargs)

class TestValidateOnSubmit(TestDatacheckForm):
    def test_not_submitted(self):
        with self.request(method='GET', data={}):
            f = DatacheckSubmissionForm(request.form, csrf_enabled=False)
            self.assertEqual(f.is_submitted(), False)
            self.assertEqual(f.validate_on_submit(), False)

    def test_submitted_not_valid(self):
        with self.request(method='POST', data={}):
            f = DatacheckSubmissionForm(request.form, csrf_enabled=False)
            self.assertEqual(f.is_submitted(), True)
            self.assertEqual(f.validate(), False)

    def test_submitted_and_valid(self):
        with self.request(method='POST', data=vaild_payload):
            print(request.form)
            f = DatacheckSubmissionForm(request.form, csrf_enabled=False)
            self.assertEqual(f.validate_on_submit(), True)



class TestCSRF(TestDatacheckForm):
    def test_csrf_token(self):
        with self.request(method='GET'):
            f = DatacheckSubmissionForm(request.form)
            self.assertEqual(hasattr(f, 'csrf_token'), True)
            self.assertEqual(f.validate(), False)

    def test_invalid_csrf(self):
        with self.request(method='POST', data=vaild_payload):
            f = DatacheckSubmissionForm()
            self.assertEqual(f.validate_on_submit(), False)
            self.assertEqual(f.errors['csrf_token'], [u'CSRF token missing'])

    def test_csrf_disabled(self):
        self.app.config['CSRF_ENABLED'] = False

        with self.request(method='POST', data=vaild_payload):
            f = DatacheckSubmissionForm(request.form)
            f.validate()
            self.assertEqual(f.validate_on_submit(), True)

    def test_valid(self):
        csrf_token = DatacheckSubmissionForm().csrf_token.current_token
        builder = EnvironBuilder(method='POST', data={**vaild_payload, 'csrf_token': csrf_token })
        env = builder.get_environ()
        req = Request(env)
        f = DatacheckSubmissionForm(req.form)
        self.assertTrue(f.validate())

    def test_form(self):
        response = self.client.post("/formvalidate/",
                                    data={
                                    'server_url':'' ,
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
         


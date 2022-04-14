# See the NOTICE file distributed with this work for additional information
#    regarding copyright ownership.
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from wtforms import Form, FormField, SelectField, StringField, SubmitField
from wtforms.validators import Email, InputRequired, ValidationError

divisions = [
    ('bacteria', 'Bacteria'),
    ('fungi', 'Fungi'),
    ('metazoa', 'Metazoa'),
    ('plants', 'Plants'),
    ('protists', 'Protists'),
    ('vertebrates', 'Vertebrates'),
    ('virus', 'Virus'),
]

database_types = [
    ('cdna', 'cdna'),
    ('compara', 'compara'),
    ('core', 'core'),
    ('fungcen', 'funcgen'),
    ('otherfeatures', 'otherfeatures'),
    ('rnaseq', 'rnaseq'),
    ('variation', 'variation')
]

datacheck_types = [
    ('', 'critical and advisory'),
    ('critical', 'critical'),
    ('advisory', 'advisory')
]


class AtLeastOne(object):
    """
  At least one field from a set has a value.

  :param fieldnames:
    The names of the other fields.
  :param message:
    Error message to raise in case of a validation error.
  """

    def __init__(self, fieldnames, message=None):
        self.fieldnames = fieldnames
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            valid = False
            for fieldname in self.fieldnames:
                try:
                    other = form[fieldname]
                except KeyError:
                    raise ValidationError(field.gettext("Invalid field name '%s'.") % fieldname)

                if other.data:
                    valid = True

            if not valid:
                message = self.message
                if message is None:
                    message = 'Either %s or one of the following fields is required: %s' % (
                        field.label.text, ','.join(self.fieldnames))

                raise ValidationError(message)


class ServerForm(Form):
    server_name = SelectField('Server Name', validators=[InputRequired()], choices=[])
    source = SelectField('Source', choices=[('dbname', 'Database'), ('species', 'Species'), ('division', 'Division')])
    dbname = StringField('Database', validators=[AtLeastOne(['dbname', 'species', 'division'])],
                         render_kw={"placeholder": " select db name eg: homo_sapiens_core_104_38"})
    species = StringField('Species', validators=[AtLeastOne(['species', 'dbname', 'division'])])
    division = SelectField('Division', validators=[AtLeastOne(['division', 'species', 'dbname'])], choices=divisions,
                           default='vertebrates')
    db_type = SelectField('Database Type', choices=database_types, default='core')


class DatacheckForm(Form):
    datacheck_name = StringField('Names', validators=[AtLeastOne(['datacheck_name', 'datacheck_group'])])
    datacheck_group = StringField('Groups', validators=[AtLeastOne(['datacheck_group', 'datacheck_name'])])
    datacheck_type = SelectField('Type', choices=datacheck_types, default='critical')


class SubmitterForm(Form):
    email = StringField('Email', validators=[Email(), InputRequired()])
    tag = StringField('Tag', validators=[InputRequired()])


class DatacheckSubmissionForm(Form):
    server = FormField(ServerForm, description='Server')
    datacheck = FormField(DatacheckForm, description='Datachecks')
    submitter = FormField(SubmitterForm, description='Submitter')
    submit = SubmitField('Submit')

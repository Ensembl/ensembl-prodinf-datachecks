from wtforms import Form, FormField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import Email, InputRequired, ValidationError

divisions = [
    ('bacteria', 'Bacteria'),
    ('fungi', 'Fungi'),
    ('metazoa', 'Metazoa'),
    ('plants', 'Plants'),
    ('protists', 'Protists'),
    ('vertebrates', 'Vertebrates')
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
    server_name = SelectField('Server Name', validators=[InputRequired()])
    source = SelectField('Source', choices=[('dbname', 'Database'), ('species', 'Species'), ('division', 'Division')])
    dbname = StringField('Database', validators=[AtLeastOne(['species', 'division'])])
    species = StringField('Species', validators=[AtLeastOne(['database', 'division'])])
    division = SelectField('Division', choices=divisions, validators=[AtLeastOne(['database', 'species'])], default='vertebrates')
    db_type = SelectField('Database Type', choices=database_types, default='core')


class DatacheckForm(Form):
    datacheck_name = StringField('Names', validators=[AtLeastOne(['datacheck_name'])])
    datacheck_group = StringField('Groups', validators=[AtLeastOne(['datacheck_group'])])
    datacheck_type = SelectField('Type', choices=datacheck_types, default='critical')


class SubmitterForm(Form):
    email = StringField('Email', validators=[Email(), InputRequired()])
    tag = StringField('Tag')


class DatacheckSubmissionForm(Form):
    server = FormField(ServerForm, description='Server')
    datacheck = FormField(DatacheckForm, description='Datachecks')
    submitter = FormField(SubmitterForm, description='Submitter')
    submit = SubmitField('Submit')


class GIFTsSubmissionForm(Form):
    ensembl_release = StringField('Ensembl Release', validators=[InputRequired()])
    environment = SelectField('Environment', choices=[('dev', 'Dev'), ('staging', 'Staging')],
                              validators=[InputRequired()])
    email = StringField('Email', validators=[Email(), InputRequired()])
    auth_token = TextAreaField('Authentication Token', validators=[InputRequired()])
    tag = StringField('Tag')
    update_ensembl = SubmitField('Update Ensembl')
    process_mapping = SubmitField('Process Mapping')
    publish_mapping = SubmitField('Publish Mapping')

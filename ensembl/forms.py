from wtforms import Form, FormField, SelectField, StringField, SubmitField
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

# Dynamically populate the versions
releases = [
  ('master', '99'),
  ('active', '98'),
  ('live', '97')
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
          message = 'Either %s or one of the following fields is required: %s' % (field.label.text, ','.join(self.fieldnames))

        raise ValidationError(message)


class ServerForm(Form):
  server_url    = StringField('Server URL', validators=[InputRequired()])
  source        = SelectField('Source', choices=[('database', 'Database'), ('species', 'Species'), ('division', 'Division')])
  database      = StringField('Database')
  species       = StringField('Species')
  division      = SelectField('Division', choices=divisions)
  database_type = SelectField('Database Type', choices=database_types, default='core')
  release       = SelectField('Release', choices=releases, default='active')

class DatacheckForm(Form):
  datacheck_name  = StringField('Names')
  datacheck_group = StringField('Groups')
  datacheck_type  = SelectField('Type', choices=[('', 'critical and advisory'), ('critical', 'critical'), ('advisory', 'advisory')])

class ConfigurationForm(Form):
  config_profile  = SelectField('Profile', choices=divisions)
  email           = StringField('Email', validators=[Email()])
  tag             = StringField('Tag')

class DatacheckSubmissionForm(Form):
  server        = FormField(ServerForm, description='Server')
  datacheck     = FormField(DatacheckForm, description='Datachecks')
  configuration = FormField(ConfigurationForm, description='Configuration')
  submit        = SubmitField('Submit')

class GIFTsSubmissionForm(Form):
  ensembl_release = StringField('Ensembl Release', validators=[InputRequired()])
  environment     = SelectField('Environment', choices=[('dev', 'Dev'), ('staging', 'Staging')], validators=[InputRequired()])
  email           = StringField('Email', validators=[Email(), InputRequired()])
  tag             = StringField('Tag')
  update_ensembl  = SubmitField('Update Ensembl')
  process_mapping = SubmitField('Process Mapping')
  publish_mapping = SubmitField('Publish Mapping')

# Miscellaneous utilities used by the package
from email.mime.text import MIMEText
from smtplib import SMTP
import json
import logging
import os
import pwd


def get_default_user():
    """Method to obtain the current user. This can be complicated when running Docker containers"""
    default_user = None
    for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
        user = os.environ.get(name)
        if user:
            default_user = user
            break
    if not default_user:
        default_user = pwd.getpwuid(os.getuid()).pw_name
    return default_user


def send_email(**kwargs):
    """ Utility method for sending an email"""
    logger = kwargs.get('logger', logging)
    from_address = kwargs.get('from_email_address', 'ensembl-production@ebi.ac.uk')
    msg = MIMEText(kwargs['body'])
    msg['Subject'] = kwargs['subject']
    msg['From'] = from_address
    msg['To'] = kwargs['to_address']
    smtp_server = kwargs.get('smtp_server', 'localhost')
    to_address = kwargs['to_address']
    logger.debug('sendmail server: {} - Message from: {}, to: {}, subject: {}'.format(smtp_server, from_address, to_address, msg['Subject']))
    s = SMTP(smtp_server)
    s.sendmail(from_address, (to_address,), msg.as_string())
    s.quit()


def dict_to_perl_string(input_dict):
    """Transform the supplied dict into a string representation of a Perl hash"""
    pairs = []
    for k,v in sorted(filter(lambda k_v: k_v[1] != None, input_dict.items())):
        k = str(k)
        t = type(v).__name__
        if t == 'str':
            pairs.append("\"%s\" => \"%s\"" % (k,escape_perl_string(v)))
        elif (t == 'int') :
            pairs.append("\"%s\" => %d" % (k,v))
        elif t == 'float':
            pairs.append("\"%s\" => %f" % (k,v))
        elif t == 'list':
            pairs.append("\"%s\" => %s" % (k,list_to_perl_string(v)))
        elif t == 'dict':
            pairs.append("\"%s\" => %s" % (k,dict_to_perl_string(v)))
        elif t == 'bool':
            if str(v) == "True":
                pairs.append("\"%s\" => %d" % (k,1))
        else:
            raise Exception("Unsupported type "+str(t))
    return "{%s}" % ", ".join(pairs)

def list_to_perl_string(input_list):
    """Transform the supplied array into a string representation of a Perl array"""
    elems = []
    for v in input_list:
        t = type(v).__name__
        if t == 'str':
            elems.append("\"%s\"" % escape_perl_string(v))
        elif(t == 'int'):
            elems.append("%d" % v)
        elif t == 'float':
            elems.append("%f" % v)
        elif t == 'list':
            elems.append("%s" % list_to_perl_string(v))
        elif t == 'dict':
            elems.append("%s" % dict_to_perl_string(v))
        else:
            raise Exception("Unsupported type "+str(t))
    return "[%s]" % ", ".join(elems)

def escape_perl_string(v):
    """Escape characters with special meaning in perl"""
    return str(v).replace("$","\\$").replace("\"","\\\"").replace("@","\\@")

def perl_string_to_python(s):
    """Parse a Perl hash string into a Python dict"""
    s = s.replace("=>",":").replace("\\$","$").replace("\\@","@")
    try:
        res = json.loads(s)
    except json.JSONDecodeError as e:
        beg = max(0, e.pos - 15)
        end = min(len(e.doc), e.pos + 15)
        raise ValueError('Invalid JSON: {}. --> {} <--'.format(str(e), e.doc[beg:end])) from e
    return res

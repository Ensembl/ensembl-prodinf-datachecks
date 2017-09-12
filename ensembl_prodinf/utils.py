# Miscellaneous utilities used by the package
from email.mime.text import MIMEText
from smtplib import SMTP
import json

def send_email(server, from_address, to_address, subject, body):
    """ Utility method for sending an email"""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = to_address    
    s = SMTP(server)
    s.sendmail(from_address, [to_address], msg.as_string())
    s.quit()

def dict_to_perl_string(input_dict):
    """Transform the supplied dict into a string representation of a Perl hash"""
    pairs = []
    for k,v in sorted(input_dict.items()):
        k = str(k)
        t = type(v).__name__
        if t == 'str':
            pairs.append("\"%s\" => \"%s\"" % (k,escape_perl_string(v)))
        elif t == 'unicode':
            pairs.append("\"%s\" => \"%s\"" % (k,escape_perl_string(str(v))))
        elif (t == 'int' or t == 'long') :
            pairs.append("\"%s\" => %d" % (k,v))
        elif t == 'float':
            pairs.append("\"%s\" => %f" % (k,v))
        elif t == 'list':
            pairs.append("\"%s\" => %s" % (k,list_to_perl_string(v)))
        elif t == 'dict':
            pairs.append("\"%s\" => %s" % (k,dict_to_perl_string(v)))
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
        elif t == 'unicode':
            elems.append("\"%s\"" % escape_perl_string(str(v)))                                                                                                                                                                                                               
        elif(t == 'int' or t == 'long'):
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
    s = s.replace("=>",":").replace("\\$","$").replace("\\@","@")
    return json.loads(s)

# str_p = re.compile('"(.*)"')
# def perl_string_to_python(s):
#     """Transform a Perlified string to a python structure""" 
#     s = s.strip()
#     print s
#     if(s.startswith('{') and s.endswith('}')):
#         return perl_string_to_dict(s)
#     elif(s.startswith('[') and s.endswith(']')):
#         return perl_string_to_list(s)
#     else:
#         m = str_p.match(s)
#         if(m):
#             return str(m.group(1)).replace("\\$","$").replace("\\\"","\"").replace("\\@","@")      
#         else:
#             return s
# 
# dict_p = re.compile('"(.+?)" *=> *(.*?)[},]')
# def perl_string_to_dict(s):
#     d = {}
#     for pair in dict_p.findall(s):
#         d[pair[0]] = perl_string_to_python(pair[1])
#     return d
# 
# def perl_string_to_list(s):
#     d = []
#     return d
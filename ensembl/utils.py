import json

def dict_to_perl_string(input_dict):
    """Transform the supplied dict into a string representation of a Perl hash"""
    pairs = []
    """for k,v in sorted(filter(lambda (k,v): v != None, input_dict.items())):"""
    for k,v in sorted(filter(lambda k_v: k_v[1] != None, input_dict.items())):
        k = str(k)
        t = type(v).__name__
        if t == 'str':
            pairs.append("\"%s\" => \"%s\"" % (k,escape_perl_string(v)))
        elif (t == 'int' or t == 'long') :
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
    """Parse a Perl hash string into a Python dict"""
    s = s.replace("=>",":").replace("\\$","$").replace("\\@","@")
    return json.loads(s)

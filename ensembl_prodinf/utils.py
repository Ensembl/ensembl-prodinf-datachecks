def dict_to_perl_string(input_dict):
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
    return str(v).replace("$","\\$").replace("\"","\\\"").replace("@","\\@")

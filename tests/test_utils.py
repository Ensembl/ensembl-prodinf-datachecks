# -*- coding: utf-8 -*-

import logging
import unittest

from ensembl_prodinf.utils import dict_to_perl_string, perl_string_to_python


logging.basicConfig()

class UtilsTest(unittest.TestCase):

    def test_parse_simple_str(self):
        o = {'a':'b'}
        s = dict_to_perl_string(o)
        self.assertEquals(s, """{"a" => "b"}""")
        o2 = perl_string_to_python(s)
        t = type(o2).__name__
        self.assertEquals(t, "dict")
        self.assertEquals(o2['a'], 'b')

    def test_parse_simple_str_pair(self):
        o = {'a':'b', 'c':'d'}
        s = dict_to_perl_string(o)
        self.assertEquals(s, """{"a" => "b", "c" => "d"}""")
        o2 = perl_string_to_python(s)
        t = type(o2).__name__
        self.assertEquals(t, "dict")
        self.assertEquals(o2['a'], 'b')
        self.assertEquals(o2['c'], 'd')

    def test_parse_simple_int(self):
        o = {'a':99}
        s = dict_to_perl_string(o)
        self.assertEquals(s, """{"a" => 99}""")
        o2 = perl_string_to_python(s)
        t = type(o2).__name__
        self.assertEquals(t, "dict")
        self.assertEquals(o2['a'], 99)

    def test_parse_simple_list(self):
        o = {'a':["a", "b", "c"]}
        s = dict_to_perl_string(o)
        self.assertEquals(s, """{"a" => ["a", "b", "c"]}""")
        o2 = perl_string_to_python(s)
        t = type(o2).__name__
        self.assertEquals(t, "dict")
        self.assertEquals(type(o2['a']).__name__, "list")

    def test_parse_complex(self):
        o = {'a':["a", "b", "c"], 'b':'d', 'c':99}
        s = dict_to_perl_string(o)
        self.assertEquals(s, """{"a" => ["a", "b", "c"], "b" => "d", "c" => 99}""")
        o2 = perl_string_to_python(s)
        t = type(o2).__name__
        self.assertEquals(t, "dict")
        self.assertEquals(type(o2['a']).__name__, "list")
        self.assertEquals(o2['b'], 'd')
        self.assertEquals(o2['c'], 99)

    def test_parse_string_quotes(self):
        o = {'a':"\"b\""}
        s = dict_to_perl_string(o)
        self.assertEquals(s, """{"a" => "\\"b\\""}""")
        o2 = perl_string_to_python(s)
        t = type(o2).__name__
        self.assertEquals(t, "dict")
        self.assertEquals(o2['a'], '"b"')

    def test_parse_string_dollar(self):
        o = {'a':"$b"}
        s = dict_to_perl_string(o)
        self.assertEquals(s, """{"a" => "\\$b"}""")
        o2 = perl_string_to_python(s)
        t = type(o2).__name__
        self.assertEquals(t, "dict")
        self.assertEquals(o2['a'], '$b')

    def test_parse_string_at(self):
        o = {'a':"@b"}
        s = dict_to_perl_string(o)
        self.assertEquals(s, """{"a" => "\\@b"}""")
        o2 = perl_string_to_python(s)
        t = type(o2).__name__
        self.assertEquals(t, "dict")
        self.assertEquals(o2['a'], '@b')                

    def test_parse_none(self):
        o = {'a':None}
        s = dict_to_perl_string(o)
        self.assertEquals(s, """{}""")

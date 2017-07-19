# -*- coding: utf-8 -*-

from ensembl_prodinf import dict_to_perl_string

import unittest
import logging

logging.basicConfig()

class HiveTest(unittest.TestCase):

    def test_parse_simple_str(self):
        o = {'a':'b'}
        s = dict_to_perl_string(o)
        self.assertEquals(s,"""{"a" => "b"}""")

    def test_parse_simple_int(self):
        o = {'a':99}
        s = dict_to_perl_string(o)
        self.assertEquals(s,"""{"a" => 99}""")

    def test_parse_simple_list(self):
        o = {'a':["a","b","c"]}
        s = dict_to_perl_string(o)
        self.assertEquals(s,"""{"a" => ["a", "b", "c"]}""")

    def test_parse_complex(self):
        o = {'a':["a","b","c"],'b':'d','c':99}
        s = dict_to_perl_string(o)
        self.assertEquals(s,"""{"a" => ["a", "b", "c"], "b" => "d", "c" => 99}""")

    def test_parse_string_quotes(self):
        o = {'a':"\"b\""}
        s = dict_to_perl_string(o)
        self.assertEquals(s,"""{"a" => "\\"b\\""}""")

    def test_parse_string_dollar(self):
        o = {'a':"$b"}
        s = dict_to_perl_string(o)
        self.assertEquals(s,"""{"a" => "\\$b"}""")

    def test_parse_string_at(self):
        o = {'a':"@b"}
        s = dict_to_perl_string(o)
        print s
        self.assertEquals(s,"""{"a" => "\\@b"}""")
        

""" Test the functionality of inversion """
from os import path as os_path
from sys import path as sys_path

sys_path.append(os_path.abspath('../src'))

from utility import forward_a_rule_to_an_address
from tokenstr import TokenString, Token
from invert_rule import invert_single_transformation, InversionStatus
from invert_rule import invert_one_rule, check_is_invertible, Invertibility
from invert_helper import Dicts
from config import RUNTIME_CONFIG
from common import RunningStyle
from parse import RulelistReader
import logging
import shutil
import unittest
import os

class InversionTest(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(filename="../results/test_invert_rule.log", level=logging.DEBUG)

    def switch_to_hc(self, max_password_length=31):
        # configuration switch
        RUNTIME_CONFIG.reset_to_hc(max_password_length=max_password_length)
        Dicts.classes['z'] = set(chr(x) for x in range(256))

    def switch_to_jtr(self, max_password_length=31):
        # configuration switch
        RUNTIME_CONFIG.reset_to_jtr(max_password_length=max_password_length)
        Dicts.classes['z'] = set(chr(x) for x in range(32, 127))

    def test_unary_transformation(self):
        ### Reset Configuration ###
        # This is done multiple times in this test function
        self.switch_to_hc()

        ###### Unittest : Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], ":")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abcd123")
        reversed_result = invert_single_transformation([token_str], ":")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"abcd123") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest l Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "l")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("d-1?e")
        reversed_result = invert_single_transformation([token_str], "l")
        if reversed_result.get_number_of_strings() != 4:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"d-1?E") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"d-1?e") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"D-1?e") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"D-1?E") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Somes")
        reversed_result = invert_single_transformation([token_str], "l")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("aBC*"))
        token_str.tokens[1] = Token(set("bCD-"))
        reversed_result = invert_single_transformation([token_str], "l")
        if reversed_result.get_number_of_strings() != 9:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ab") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aB") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"a-") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("ABC"))
        token_str.tokens[1] = Token(set("DEF"))
        reversed_result = invert_single_transformation([token_str], "l")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        ###### Unittest u Command ######
        token_str = TokenString("Somesuperlongpasswordthatdoesn't")
        reversed_result = invert_single_transformation([token_str], "u")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "u")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("S(1)D")
        reversed_result = invert_single_transformation([token_str], "u")
        if reversed_result.get_number_of_strings() != 4:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"S(1)D") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"S(1)d") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"s(1)D") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"s(1)d") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("SOME ONe")
        reversed_result = invert_single_transformation([token_str], "u")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("ABC"))
        token_str.tokens[1] = Token(set("DEF"))
        reversed_result = invert_single_transformation([token_str], "u")
        if reversed_result.get_number_of_strings() != 36:
            raise Exception("Unittest Not Passed")

        ###### Unittest c Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "c")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Sx1")
        reversed_result = invert_single_transformation([token_str], "c")
        if reversed_result.get_number_of_strings() != 4:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Sx1") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"SX1") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"sx1") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"sX1") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("1x?")
        reversed_result = invert_single_transformation([token_str], "c")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"1x?") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"1X?") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("x?xdsfa")
        reversed_result = invert_single_transformation([token_str], "c")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ds?xdsfa")
        reversed_result = invert_single_transformation([token_str], "c")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abC*"))
        token_str.tokens[1] = Token(set("bCD-"))
        reversed_result = invert_single_transformation([token_str], "c")
        if reversed_result.get_number_of_strings() != 9:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cb") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cB") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"c-") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("ABC"))
        token_str.tokens[1] = Token(set("DEF"))
        reversed_result = invert_single_transformation([token_str], "c")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        ###### Unittest C Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "C")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("sX1")
        reversed_result = invert_single_transformation([token_str], "C")
        if reversed_result.get_number_of_strings() != 4:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Sx1") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"SX1") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"sx1") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"sX1") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("1X?")
        reversed_result = invert_single_transformation([token_str], "C")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"1x?") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"1X?") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("X?xdsfa")
        reversed_result = invert_single_transformation([token_str], "C")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Ds?xdsfa")
        reversed_result = invert_single_transformation([token_str], "C")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ds?xdsfa")
        reversed_result = invert_single_transformation([token_str], "C")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("aBC*"))
        token_str.tokens[1] = Token(set("bcD-"))
        reversed_result = invert_single_transformation([token_str], "C")
        if reversed_result.get_number_of_strings() != 9:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aD") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ad") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"a-") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("ABC"))
        token_str.tokens[1] = Token(set("DEF"))
        reversed_result = invert_single_transformation([token_str], "C")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        ###### Unittest t Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "t")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("x?e1. dsw")
        reversed_result = invert_single_transformation([token_str], "t")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"X?E1. DSW") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("a*"))
        token_str.tokens[1] = Token(set("B-"))
        reversed_result = invert_single_transformation([token_str], "t")
        if reversed_result.get_number_of_strings() != 4:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"A-") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"*b") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Ab") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("ABC"))
        token_str.tokens[1] = Token(set("DEF"))
        reversed_result = invert_single_transformation([token_str], "t")
        if reversed_result.get_number_of_strings() != 9:
            raise Exception("Unittest Not Passed")

        ###### Unittest r Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "r")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("alexliu")
        reversed_result = invert_single_transformation([token_str], "r")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"uilxela") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest d Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "d")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Hahathisisalen16")
        reversed_result = invert_single_transformation([token_str], "d")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Hahathisisalen16") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ThisisFunThisisFun")
        reversed_result = invert_single_transformation([token_str], "d")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ThisisFunThisisFun") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ThisisFun") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("someoddword")
        reversed_result = invert_single_transformation([token_str], "d")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("passpasd")
        reversed_result = invert_single_transformation([token_str], "d")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("passpass")
        reversed_result = invert_single_transformation([token_str], "d")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pass") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("bcd"))
        reversed_result = invert_single_transformation([token_str], "d")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"b") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"c") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("def"))
        reversed_result = invert_single_transformation([token_str], "d")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        ###### Unittest f Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "f")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ThisabcdefggfedcbasihT")
        reversed_result = invert_single_transformation([token_str], "f")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Thisabcdefg") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ThisabcdefggfedcbasihT") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Somewordcan'tbedouble")
        reversed_result = invert_single_transformation([token_str], "f")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Somewordcan'tbedouble") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abcddcbe")
        reversed_result = invert_single_transformation([token_str], "f")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("passssap")
        reversed_result = invert_single_transformation([token_str], "f")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pass") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("bcd"))
        reversed_result = invert_single_transformation([token_str], "f")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"b") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"c") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("def"))
        reversed_result = invert_single_transformation([token_str], "f")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        ###### Unittest { Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "{")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("asswordp")
        reversed_result = invert_single_transformation([token_str], "{")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"password") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest } Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "}")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("dpasswor")
        reversed_result = invert_single_transformation([token_str], "}")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"password") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest [ Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "[")
        if reversed_result.get_number_of_strings() != 257:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(chr(0).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(chr(5).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Somesuperlongpasswordthatdoesn")
        reversed_result = invert_single_transformation([token_str], "[")
        if reversed_result.get_number_of_strings() != 256:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("SDFAS")
        reversed_result = invert_single_transformation([token_str], "[")
        if reversed_result.get_number_of_strings() != 256:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        ###### Unittest ] Command ######
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "]")
        if reversed_result.get_number_of_strings() != 257:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(chr(0).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(chr(5).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Somesuperlongpasswordthatdoesn")
        reversed_result = invert_single_transformation([token_str], "]")
        if reversed_result.get_number_of_strings() != 256:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("SDFAS")
        reversed_result = invert_single_transformation([token_str], "]")
        if reversed_result.get_number_of_strings() != 256:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        ###### Unittest q Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "q")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("aabbccddeeffgghhiijj")
        reversed_result = invert_single_transformation([token_str], "q")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abcdefghij") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aabbccddeeffgghhiijj") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Somewordcan'tbedouble")
        reversed_result = invert_single_transformation([token_str], "q")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Somewordcan'tbedouble") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("lent5")
        reversed_result = invert_single_transformation([token_str], "q")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("11223344aa")
        reversed_result = invert_single_transformation([token_str], "q")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"1234a") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("11223044")
        reversed_result = invert_single_transformation([token_str], "q")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("bcd"))
        reversed_result = invert_single_transformation([token_str], "q")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"b") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"c") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("def"))
        reversed_result = invert_single_transformation([token_str], "q")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        ###### Unittest k Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "k")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("O")
        reversed_result = invert_single_transformation([token_str], "k")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"O") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Some")
        reversed_result = invert_single_transformation([token_str], "k")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"oSme") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest K Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "K")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("X")
        reversed_result = invert_single_transformation([token_str], "K")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"X") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Xonm")
        reversed_result = invert_single_transformation([token_str], "K")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Xomn") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest E Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "E")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("A BAAb")
        token_str[1] = Token(" Ab")
        token_str[3] = Token(" Cd")
        token_str[4] = Token(" Ef")
        token_str[5] = Token("Gh")
        reversed_result = invert_single_transformation([token_str], "E")
        # Valid reverse input:
        # (a,A)( )(Bb)(Dd)(fF)(Hh) #32
        # (a,A)( )(Bb)(Dd)( )(Gg) #16
        # (a,A)( )(Bb)( )( )(Gg) #8
        # (a,A)( )(Bb)( )(Ee)(Hh) #16
        if reversed_result.get_number_of_strings() != 72:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"a BdfH") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"a B  g") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"a B  G") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"A B  G") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"AbB  G") == True:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Pa@@ Wo!!!")
        reversed_result = invert_single_transformation([token_str], "E")
        if reversed_result.get_number_of_strings() != 16:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa@@ Wo!!!")
        reversed_result = invert_single_transformation([token_str], "E")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("PA@@ Wo!!!")
        reversed_result = invert_single_transformation([token_str], "E")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Pa@@ wo!!!")
        reversed_result = invert_single_transformation([token_str], "E")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Pa@@ WO!!!")
        reversed_result = invert_single_transformation([token_str], "E")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("P W")
        reversed_result = invert_single_transformation([token_str], "E")
        if reversed_result.get_number_of_strings() != 4:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"P W") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"P w") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"p W") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"p w") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[0] = Token(set("Aa"))
        token_str.tokens[1] = Token(set(" a"))
        token_str.tokens[2] = Token(set(" B"))
        token_str.tokens[3] = Token(set("c"))
        token_str.tokens[4] = Token(set("d"))
        reversed_result = invert_single_transformation([token_str], "E")
        if reversed_result.get_number_of_strings() != 16:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"A bCd") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"A BCd") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"a bCd") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest P Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        # ed part
        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bpe") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bed")
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bed") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("aed")
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aed") == False:
            raise Exception("Unittest Not Passed")
        # aed from a/ae is impossible
        if reversed_result.contains(b"a") == True:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ae") == True:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bced")
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bce") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bced") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bc") == True:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abced")
        token_str[-1] = Token(set("ad"))
        token_str[-2] = Token(set("es"))
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 3:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abce") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abced") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abc") == False:
            raise Exception("Unittest Not Passed")

        # ied part
        token_str = TokenString("payed")
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"paye") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"payed") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pay") == True:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("paied")
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 4:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"paie") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"paied") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pai") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pay") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("payed")
        token_str[2] = Token("iy")  # paied, payed
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 6:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"paye") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"payed") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pay") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pai") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"paie") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"paied") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("whyed")
        token_str[2] = Token("ay")  # whaed whyed
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 5:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"whae") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"whaed") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"wha") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"whye") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"whyed") == False:
            raise Exception("Unittest Not Passed")

        # gged part
        token_str = TokenString("bagged")
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 4:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bagg") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bagge") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bagged") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bag") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("baged")
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bage") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"baged") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bag") == True:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("baged")
        token_str[2] = Token("yg")  # "bayed, baged"
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 4:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bage") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"baged") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"baye") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bayed") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("baged")
        token_str[2] = Token("ygk")  # "bayed, baged, baked"
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 8:  # 1 duplicate (bak)
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bage") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"baged") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"baye") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bayed") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bak") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bake") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"baked") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bagged")
        token_str[3] = Token("gp")  # bagged, bagped,
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 7:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bagged") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bagge") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bagg") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bag") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bagped") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bagpe") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bagp") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bagged")
        token_str[2] = Token("b")
        token_str[3] = Token("gp")  # babged babped
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 6:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"babged") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"babge") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"babg") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"babped") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"babpe") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"babp") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("agged")
        reversed_result = invert_single_transformation([token_str], "P")
        if reversed_result.get_number_of_strings() != 3:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"agged") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"agge") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"agg") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ag") == True:
            raise Exception("Unittest Not Passed")

        ###### Unittest I Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "I")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        # ing part
        token_str = TokenString("cracking")
        reversed_result = invert_single_transformation([token_str], "I")
        if reversed_result.get_number_of_strings() != 7:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cracking") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"crack") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cracka") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cracke") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cracki") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cracko") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cracku") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("cracking")
        token_str[-1] = Token("12g")
        token_str[-2] = Token("$dan")
        token_str[-3] = Token("idol")
        reversed_result = invert_single_transformation([token_str], "I")
        if reversed_result.get_number_of_strings() != 7:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cracking") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"crack") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cracka") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cracke") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cracki") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cracko") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cracku") == False:
            raise Exception("Unittest Not Passed")

        # gg(ing) part
        token_str = TokenString("baging")
        token_str[-1] = Token("12g")
        token_str[-2] = Token("$dan")
        token_str[-3] = Token("idol")
        reversed_result = invert_single_transformation([token_str], "I")
        if reversed_result.get_number_of_strings() != 6:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"baging") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"baga") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bage") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bagi") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bago") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bagu") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bag") == True:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("aaging")
        token_str[1] = Token("ag")  # agging, aaging -> aag and ag not possible
        token_str[-1] = Token("12g")
        token_str[-2] = Token("$dan")
        token_str[-3] = Token("idol")
        reversed_result = invert_single_transformation([token_str], "I")
        if reversed_result.get_number_of_strings() != 13:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"agg") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"agging") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"agge") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aggi") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aggo") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aggu") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"agga") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aaging") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aage") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aagi") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aago") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aagu") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aaga") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ag") == True:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aag") == True:
            raise Exception("Unittest Not Passed")

        # (aeiou) ing
        token_str = TokenString("abing")
        token_str[-1] = Token("12g")
        token_str[-2] = Token("$dan")
        token_str[-3] = Token("idol")
        reversed_result = invert_single_transformation([token_str], "I")
        if reversed_result.get_number_of_strings() != 6:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abing") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aba") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abe") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abi") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abo") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abu") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abding")
        token_str[2] = Token("de")  # abeing, abding
        token_str[-1] = Token("12g")
        token_str[-2] = Token("$dan")
        token_str[-3] = Token("idol")
        reversed_result = invert_single_transformation([token_str], "I")
        if reversed_result.get_number_of_strings() != 13:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abding") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abd") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abda") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abde") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abdi") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abdo") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abdu") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abeing") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abea") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abee") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abei") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abeo") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abeu") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("dr0wssapping")
        reversed_result = invert_single_transformation([token_str], "I")
        if reversed_result.get_number_of_strings() != 8:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"dr0wssapping") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"dr0wssapp") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"dr0wssappa") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"dr0wssappe") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"dr0wssappi") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"dr0wssappo") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"dr0wssappu") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"dr0wssap") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest S Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "S")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Crack96")
        reversed_result = invert_single_transformation([token_str], "S")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cRACK(^") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("cRACK(^")
        reversed_result = invert_single_transformation([token_str], "S")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Crack96") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("cRACK 0")
        token_str.tokens[-1] = Token(set("^("))
        reversed_result = invert_single_transformation([token_str], "S")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Crack 9") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Crack 6") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Crack 0")
        token_str.tokens[-1] = Token(set("96"))
        reversed_result = invert_single_transformation([token_str], "S")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cRACK ^") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cRACK (") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest V Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "V")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("CRaCK96")
        reversed_result = invert_single_transformation([token_str], "V")
        if reversed_result.get_number_of_strings() != 32:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Crack96") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"CRack96") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"CRacK96") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"crack96") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"CRACK96") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("CRaCK96")
        token_str[0] = Token(set("Cc"))
        token_str[1] = Token(set("Rr"))
        reversed_result = invert_single_transformation([token_str], "V")
        if reversed_result.get_number_of_strings() != 32:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Crack96") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"CRack96") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"CRacK96") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"crack96") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"CRACK96") == False:
            raise Exception("Unittest Not Passed")

        ### Reset Configuration ###
        # This is done multiple times in this test function
        self.switch_to_jtr()

        ###### Unittest p Command ######
        # s part
        token_str = TokenString("chs")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ch") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("shs")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"sh") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ash")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ashs")
        token_str[1] = Token(set("as"))
        token_str[2] = Token(set("bh"))
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 4:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aab") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aah") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"asb") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ash") == True:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Dshs")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("axs")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("azs")
        token_str[1] = Token(set("sabc"))
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 3:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aa") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ab") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ac") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("azfs")
        token_str[1] = Token(set("xf"))
        token_str[2] = Token(set("ea"))
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 5:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"axa") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"axe") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"afa") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ax") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"afe") == True:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("fes")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"fe") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("azfs")
        # axfs axes affs afes -> only affs and axes valid
        token_str[1] = Token(set("xf"))
        token_str[2] = Token(set("fe"))
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 5:  # aff and aff are duplicate
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aff") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"axe") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ax") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"axfs") == True:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"afes") == True:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Aess")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Ess")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("dcfs")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("dfes")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Ezys")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("adzys")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bays")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bay") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("passwords")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"password") == False:
            raise Exception("Unittest Not Passed")

        # es part
        token_str = TokenString("aches")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ache") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ach") == False:
            raise Exception("`Unittest Not Passed")

        token_str = TokenString("aches")  # aches, acbes, ashes, asbes
        token_str[1] = Token("cs")
        token_str[2] = Token("bh")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 6:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ache") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ach") == False:
            raise Exception("`Unittest Not Passed")
        if reversed_result.contains(b"ash") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ashe") == False:
            raise Exception("`Unittest Not Passed")
        if reversed_result.contains(b"asbe") == False:
            raise Exception("`Unittest Not Passed")
        if reversed_result.contains(b"acbe") == False:
            raise Exception("`Unittest Not Passed")

        token_str = TokenString("passwordes")
        token_str[-2] = Token("be")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"passworde") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"passwordb") == False:
            raise Exception("Unittest Not Passed")

        # ies part
        token_str = TokenString("bays")  # bbys beys
        #token_str[1] = Token("ba")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bay") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("baies")  # baies/ bbies -> bby, baie, bbie
        token_str[1] = Token("ab")
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 3:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bby") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bbie") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"baie") == False:
            raise Exception("Unittest Not Passed")

        # ves part
        token_str = TokenString("ves")  # bbys beys
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ve") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bves")  # bbys beys
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 3:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bve") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bf") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bfe") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bves")
        token_str[0] = Token("bf")  # bves, fves
        reversed_result = invert_single_transformation([token_str], "p")
        if reversed_result.get_number_of_strings() != 5:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bve") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bf") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bfe") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ffe") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"fve") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest R Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "R")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Vtsvl07")
        reversed_result = invert_single_transformation([token_str], "R")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Crack96") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("nrgptr")
        reversed_result = invert_single_transformation([token_str], "R")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"before") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("vp;fest")
        reversed_result = invert_single_transformation([token_str], "R")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"coldwar") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Vtsvl07")
        token_str[0] = Token(set("VZQ~"))
        reversed_result = invert_single_transformation([token_str], "R")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")

        ###### Unittest L Command ######
        token_str = TokenString("Xeaxj85")
        reversed_result = invert_single_transformation([token_str], "L")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Crack96") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Crsck96") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("xiksqae")
        reversed_result = invert_single_transformation([token_str], "L")
        if reversed_result.get_number_of_strings() != 4:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"coldwar") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"coldwsr") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"coldqsr") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"coldqar") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("vwdiew")
        reversed_result = invert_single_transformation([token_str], "L")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"before") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Xeaxj85")
        token_str[0] = Token(set("X|]?"))
        reversed_result = invert_single_transformation([token_str], "L")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Crack96") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest L Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "L")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Xeaxj85")
        reversed_result = invert_single_transformation([token_str], "L")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Crack96") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Crsck96") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("xiksqae")
        reversed_result = invert_single_transformation([token_str], "L")
        if reversed_result.get_number_of_strings() != 4:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"coldwar") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"coldwsr") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"coldqsr") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"coldqar") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("vwdiew")
        reversed_result = invert_single_transformation([token_str], "L")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"before") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Xeaxj85")
        token_str[0] = Token(set("X|]?"))
        reversed_result = invert_single_transformation([token_str], "L")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Crack96") == False:
            raise Exception("Unittest Not Passed")

    def test_binary_transformation(self):
        ### Reset Configuration ###
        # This is done multiple times in this test function
        self.switch_to_hc()

        ###### Unittest $N Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "$0")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("1234560")
        reversed_result = invert_single_transformation([token_str], "$0")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"123456") == False:
            raise Exception("Unittest Not Passed")

        # test empty string case
        token_str = TokenString("0")
        token_str[0] = Token("0123")
        reversed_result = invert_single_transformation([token_str], "$0")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("Some123456789012345678901234567")
        reversed_result = invert_single_transformation([token_str], "$7")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Some123456789012345678901234567") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Some12345678901234567890123456") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Someone")
        reversed_result = invert_single_transformation([token_str], "$e")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Someon") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Someonx")
        reversed_result = invert_single_transformation([token_str], "$e")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Someon?")
        reversed_result = invert_single_transformation([token_str], "$e")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[4] = Token(set("pca"))
        reversed_result = invert_single_transformation([token_str], "$e")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[4] = Token(set("pca"))
        reversed_result = invert_single_transformation([token_str], "$p")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pacd") == False:
            raise Exception("Unittest Not Passed")

        ### Reset Configuration ###
        # This is done multiple times in this test function
        self.switch_to_jtr()

        # test multiple input case
        token_str = TokenString("Someone")
        reversed_result = invert_single_transformation(
            [token_str], ["$", set("e123")])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Someon") == False:
            raise Exception("Unittest Not Passed")

        # test multiple input case
        token_str = TokenString("Someone")
        reversed_result = invert_single_transformation(
            [token_str], ["$", set("123")])
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        ###### Unittest ^N Command ######
        ### Reset Configuration ###
        # This is done multiple times in this test function
        self.switch_to_hc()

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "^0")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        # test empty string case
        token_str = TokenString("0")
        token_str[0] = Token("0123")
        reversed_result = invert_single_transformation([token_str], "^0")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("7ome123456789012345678901234567")
        reversed_result = invert_single_transformation([token_str], "^7")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"7ome123456789012345678901234567") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ome123456789012345678901234567") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Someone")
        reversed_result = invert_single_transformation([token_str], "^S")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"omeone") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Someonx")
        reversed_result = invert_single_transformation([token_str], "^e")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Someon?")
        reversed_result = invert_single_transformation([token_str], "^?")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[0] = Token(set("pca"))
        reversed_result = invert_single_transformation([token_str], "^e")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[0] = Token(set("pca"))
        reversed_result = invert_single_transformation([token_str], "^p")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"acde") == False:
            raise Exception("Unittest Not Passed")

        ### Reset Configuration ###
        # This is done multiple times in this test function
        self.switch_to_jtr()

        # test multiple input case
        token_str = TokenString("Someone")
        reversed_result = invert_single_transformation(
            [token_str], ["^", set("S123")])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"omeone") == False:
            raise Exception("Unittest Not Passed")

        # test multiple input case
        token_str = TokenString("Someone")
        reversed_result = invert_single_transformation(
            [token_str], ["^", set("123")])
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        ###### Unittest TN Command ######
        ### Reset Configuration ###
        # This is done multiple times in this test function
        self.switch_to_hc()

        # Test empty string
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "T0")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("seq")
        reversed_result = invert_single_transformation([token_str], "T3")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"seq") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("seq")
        reversed_result = invert_single_transformation([token_str], "T2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"seQ") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("aBC*"))
        token_str.tokens[1] = Token(set("bCD-"))
        reversed_result = invert_single_transformation([token_str], "T0")
        if reversed_result.get_number_of_strings() != 16:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"AC") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"b-") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"cb") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("ABC"))
        token_str.tokens[1] = Token(set("DEF"))
        reversed_result = invert_single_transformation([token_str], "T1")
        if reversed_result.get_number_of_strings() != 9:
            raise Exception("Unittest Not Passed")

        ###### Unittest 'N Command ######
        # Test empty string
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "'2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("0")
        reversed_result = invert_single_transformation([token_str], "'4")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"0") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("12")
        reversed_result = invert_single_transformation([token_str], "'4")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"12") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("234")
        reversed_result = invert_single_transformation([token_str], "'4")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"234") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("2345")
        reversed_result = invert_single_transformation([token_str], "'4")
        if reversed_result.get_status() != InversionStatus.OUTSCOPE:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("23456")
        reversed_result = invert_single_transformation([token_str], "'4")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("Somesuperlongpasswordthatdoesn'")
        reversed_result = invert_single_transformation([token_str], "'5")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        ###### Unittest DN Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "D1")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "D0")
        if reversed_result.get_number_of_strings() != 257:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(chr(253).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Somesuperlongpasswordthatdoesn'")
        reversed_result = invert_single_transformation([token_str], "D0")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("SD")
        reversed_result = invert_single_transformation([token_str], "D3")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"SD") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("SDef")
        reversed_result = invert_single_transformation([token_str], "D3")
        if reversed_result.get_number_of_strings() != 256:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # Random Test
        if reversed_result.contains(b"SDe f") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(("SDe"+chr(2) + "f").encode("charmap")) == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("SDe")
        reversed_result = invert_single_transformation([token_str], "D3")
        if reversed_result.get_number_of_strings() != 257:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # Random Test
        if reversed_result.contains(b"SDe") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(("SDe"+chr(1)).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(("SDe"+chr(255)).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest pN Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "p2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("NoNoNoNoNo")
        reversed_result = invert_single_transformation([token_str], "p4")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"No") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"NoNoNoNoNo") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Somewordcan'tbedouble")
        reversed_result = invert_single_transformation([token_str], "p2")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        # Should Be Rejected
        if reversed_result.contains(b"Somewordcan'tbedouble") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abcabcad")
        reversed_result = invert_single_transformation([token_str], "p2")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("dcbdcbdcc")
        reversed_result = invert_single_transformation([token_str], "p2")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("nflnflnfl")
        reversed_result = invert_single_transformation([token_str], "p2")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"nfl") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("bcd"))
        reversed_result = invert_single_transformation([token_str], "p1")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"b") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"c") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("def"))
        reversed_result = invert_single_transformation([token_str], "p1")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("Somesuperlongpasswordthatdoesn'")
        reversed_result = invert_single_transformation([token_str], "D0")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("Somesuperlongpasswordthatdoesn")
        reversed_result = invert_single_transformation([token_str], "D0")
        if reversed_result.get_number_of_strings() != 256:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aSomesuperlongpasswordthatdoesn") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest zN Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "z1")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abcdefghijklmnopqrstuvwxyz")
        reversed_result = invert_single_transformation([token_str], "z8")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abcdefghijklmnopqrstuvwxyz") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("adf")
        reversed_result = invert_single_transformation([token_str], "z3")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("aaabc")
        reversed_result = invert_single_transformation([token_str], "z2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abc") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ababc")
        reversed_result = invert_single_transformation([token_str], "z2")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("bcd"))
        reversed_result = invert_single_transformation([token_str], "z1")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"b") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"c") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("def"))
        reversed_result = invert_single_transformation([token_str], "z1")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("SSmesuperlongpasswordthatdoesn'")
        reversed_result = invert_single_transformation([token_str], "z1")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"SSmesuperlongpasswordthatdoesn'") == False:
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"Smesuperlongpasswordthatdoesn'") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest ZN Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "Z2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abcdefghijklmnopqrstuvwxyz")
        reversed_result = invert_single_transformation([token_str], "Z8")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abcdefghijklmnopqrstuvwxyz") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("adf")
        reversed_result = invert_single_transformation([token_str], "Z3")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("aaabccc")
        reversed_result = invert_single_transformation([token_str], "Z2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aaabc") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("aaabcdc")
        reversed_result = invert_single_transformation([token_str], "Z2")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("bcd"))
        reversed_result = invert_single_transformation([token_str], "Z1")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"b") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"c") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("def"))
        reversed_result = invert_single_transformation([token_str], "Z1")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("Somesuperlongpasswordthatdoesnn")
        reversed_result = invert_single_transformation([token_str], "Z1")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"Somesuperlongpasswordthatdoesnn") == False:
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"Somesuperlongpasswordthatdoesn") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest LN Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "L0")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Super")
        reversed_result = invert_single_transformation([token_str], "L5")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Super") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Super")
        reversed_result = invert_single_transformation([token_str], "L4")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Supe9") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(("Supe"+chr(185)).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Supe ")
        reversed_result = invert_single_transformation([token_str], "L4")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(("Supe"+chr(16)).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(("Supe"+chr(144)).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[1] = Token(set("XY"))
        reversed_result = invert_single_transformation([token_str], "L1")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"p,cde") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(("p"+chr(172)+"cde").encode("charmap")) == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest RN Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "R0")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Sup")
        reversed_result = invert_single_transformation([token_str], "R3")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Sup") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Su ")
        reversed_result = invert_single_transformation([token_str], "R2")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Su@") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"SuA") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Su" + chr(100))
        reversed_result = invert_single_transformation([token_str], "R2")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(("Su"+chr(200)).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(("Su"+chr(201)).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Su" + chr(127))
        reversed_result = invert_single_transformation([token_str], "R2")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(("Su"+chr(255)).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(("Su"+chr(254)).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Su" + chr(128))
        reversed_result = invert_single_transformation([token_str], "R2")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Su" + chr(130))
        reversed_result = invert_single_transformation([token_str], "R2")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[1] = Token(set("01"))
        reversed_result = invert_single_transformation([token_str], "R1")
        if reversed_result.get_number_of_strings() != 4:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"p`cde") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pacde") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pbcde") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pccde") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest +N Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "+0")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Sup")
        reversed_result = invert_single_transformation([token_str], "+3")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Sup") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Sup")
        reversed_result = invert_single_transformation([token_str], "+2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Suo") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Su"+chr(1))
        reversed_result = invert_single_transformation([token_str], "+2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(("Su"+chr(0)).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Su"+chr(0))
        reversed_result = invert_single_transformation([token_str], "+2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(("Su"+chr(255)).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[1] = Token(set("12"))
        reversed_result = invert_single_transformation([token_str], "+1")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"p0cde") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"p1cde") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest -N Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "-0")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Sup")
        reversed_result = invert_single_transformation([token_str], "-3")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Sup") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Sup")
        reversed_result = invert_single_transformation([token_str], "-2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Suq") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Su"+chr(0))
        reversed_result = invert_single_transformation([token_str], "-2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(("Su"+chr(1)).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Su"+chr(255))
        reversed_result = invert_single_transformation([token_str], "-2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(("Su"+chr(0)).encode("charmap")) == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[1] = Token(set("12"))
        reversed_result = invert_single_transformation([token_str], "-1")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"p2cde") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"p3cde") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest .N Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], ".0")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("aac")
        reversed_result = invert_single_transformation([token_str], ".2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aac") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("acc")
        reversed_result = invert_single_transformation([token_str], ".1")
        if reversed_result.get_number_of_strings() != 256:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abc")
        reversed_result = invert_single_transformation([token_str], ".1")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[1] = Token(set("pca"))
        reversed_result = invert_single_transformation([token_str], ".1")
        if reversed_result.get_number_of_strings() != 256:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pccde") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"p`cde") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest ,N Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], ",0")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abc")
        reversed_result = invert_single_transformation([token_str], ",3")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abc") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("acc")
        reversed_result = invert_single_transformation([token_str], ",2")
        if reversed_result.get_number_of_strings() != 256:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abc")
        reversed_result = invert_single_transformation([token_str], ",2")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[1] = Token(set("pca"))
        reversed_result = invert_single_transformation([token_str], ",1")
        if reversed_result.get_number_of_strings() != 256:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ppcde") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pacde") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest yN Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "y2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("heh")
        reversed_result = invert_single_transformation([token_str], "y4")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"heh") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abcd")
        reversed_result = invert_single_transformation([token_str], "y3")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("hehello")
        reversed_result = invert_single_transformation([token_str], "y2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"hello") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("hexello")
        reversed_result = invert_single_transformation([token_str], "y2")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("bcd"))
        reversed_result = invert_single_transformation([token_str], "y1")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"b") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"c") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("def"))
        reversed_result = invert_single_transformation([token_str], "y1")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("SoSosuperlongpasswordthatdoesnt")
        reversed_result = invert_single_transformation([token_str], "y2")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"SoSosuperlongpasswordthatdoesnt") == False:
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"Sosuperlongpasswordthatdoesnt") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest YN Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "Y2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abe")
        reversed_result = invert_single_transformation([token_str], "Y4")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"abe") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abcd")
        reversed_result = invert_single_transformation([token_str], "Y3")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("hellolo")
        reversed_result = invert_single_transformation([token_str], "Y2")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"hello") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("helloxo")
        reversed_result = invert_single_transformation([token_str], "Y2")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("bcd"))
        reversed_result = invert_single_transformation([token_str], "Y1")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"b") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"c") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa")
        token_str.tokens[0] = Token(set("abc"))
        token_str.tokens[1] = Token(set("def"))
        reversed_result = invert_single_transformation([token_str], "Y1")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("Somesuperlongpasswordthatdoesnt")
        reversed_result = invert_single_transformation([token_str], "Y1")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"Somesuperlongpasswordthatdoesnt") == False:
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("Somesuperlongpasswordthatdoesnn")
        reversed_result = invert_single_transformation([token_str], "Y1")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"Somesuperlongpasswordthatdoesnn") == False:
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"Somesuperlongpasswordthatdoesn") == False:
            raise Exception("Unittest Not Passed")

    def test_ternary_transformation(self):
        ###### Unittest ANstr Command ######
        ### Reset Configuration ###
        # This is done multiple times in this test function
        self.switch_to_jtr()

        # Empty string
        token_str = TokenString("")
        reversed_result = invert_single_transformation(
            [token_str], ["A", "4", "c"])
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab2")
        reversed_result = invert_single_transformation(
            [token_str], ["A", "4", "2"])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ab") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab2")
        reversed_result = invert_single_transformation(
            [token_str], ["A", "4", "c"])
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab2c")
        reversed_result = invert_single_transformation(
            [token_str], ["A", "3", "c"])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ab2") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab2c")
        reversed_result = invert_single_transformation(
            [token_str], ["A", "3", set("abc")])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ab2") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab2c")
        reversed_result = invert_single_transformation(
            [token_str], ["A", "3", set("abc")])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ab2") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab2c")
        reversed_result = invert_single_transformation(
            [token_str], ["A", "4", set("abcde123")])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ab2") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab3ab")
        reversed_result = invert_single_transformation(
            [token_str], ["A", "3", set("abcde123")])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ab3b") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab3cb")
        reversed_result = invert_single_transformation(
            [token_str], ["A", "3", set("a")])
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab300")
        reversed_result = invert_single_transformation(
            [token_str], ["A", "z", set("02"), set("01")])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ab3") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab300")
        reversed_result = invert_single_transformation(
            [token_str], ["A", "0", set("02"), set("01")])
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab300")
        reversed_result = invert_single_transformation(
            [token_str], ["A", -1, set("03"), set("01")])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ab0") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab300")
        reversed_result = invert_single_transformation([token_str], [
                                                       "A", -4, set("03"), set("01"), set("03"), set("01"), set("03"), set("01")])
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab300")
        reversed_result = invert_single_transformation(
            [token_str], ["A", -4, set("bace"), set("03"), set("04"), set("01")])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"a") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab300")
        reversed_result = invert_single_transformation(
            [token_str], ["A", -4, set("bace"), set("04"), set("03"), set("01")])
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab300")
        reversed_result = invert_single_transformation(
            [token_str], ["A", -1, set("bace"), set("b123"), set("03"), set("01")])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"0") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab300")
        token_str[0] = Token(set("ab012354"))
        reversed_result = invert_single_transformation(
            [token_str], ["A", -1, set("a"), set("b123"), set("03"), set("01")])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"0") == False:
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("Somesuperlongpasswordthatdoesn'")
        reversed_result = invert_single_transformation(
            [token_str], ["A", "z", set("mn123ad"), set("'")])
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Somesuperlongpasswordthatdoesn'") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Somesuperlongpasswordthatdoes") == False:
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("Somesuperlongpasswordthatdoesn'")
        reversed_result = invert_single_transformation(
            [token_str], ["A", "z", set("m123ad"), set("'")])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Somesuperlongpasswordthatdoesn'") == False:
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("Somesuperlongpasswordthatdoesn")
        reversed_result = invert_single_transformation(
            [token_str], ["A", "z", set("'"), set("mn123ad")])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Somesuperlongpasswordthatdoesn") == False:
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("Somesuperlongpasswordthatdoes")
        reversed_result = invert_single_transformation(
            [token_str], ["A", "z", set("'"), set("mn123ad")])
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        ###### Unittest xNM Command ######
        ### Reset Configuration ###
        # This is done multiple times in this test function
        self.switch_to_hc()

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "x13")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "x30")
        if reversed_result.get_status() != InversionStatus.OUTSCOPE:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("aaaa")
        reversed_result = invert_single_transformation([token_str], "x03")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("aaa")
        reversed_result = invert_single_transformation([token_str], "x03")
        if reversed_result.get_status() != InversionStatus.OUTSCOPE:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("aa")
        reversed_result = invert_single_transformation([token_str], "x03")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"aa") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("a")
        reversed_result = invert_single_transformation([token_str], "x03")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"a") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest iNX Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "i12")
        if reversed_result.get_number_of_strings() != 1:  # Valid empty string.
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        # test length is too short case
        token_str = TokenString("3")
        reversed_result = invert_single_transformation([token_str], "i22")
        if reversed_result.get_number_of_strings() != 1:  # Valid empty string.
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"3") == False:
            raise Exception("Unittest Not Passed")

        # test length == N case
        token_str = TokenString("33")
        reversed_result = invert_single_transformation([token_str], "i23")
        if reversed_result.get_number_of_strings() != 0:  # Valid empty string.
            raise Exception("Unittest Not Passed")

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "i02")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("Somesuperlongpasswordthatdoesn'")
        reversed_result = invert_single_transformation([token_str], "i23")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Somesuperlongpasswordthatdoesn'") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab2")
        reversed_result = invert_single_transformation([token_str], "i3a")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab")
        reversed_result = invert_single_transformation([token_str], "i3a")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ab") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab3ab")
        reversed_result = invert_single_transformation([token_str], "i3a")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ab3b") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab3cb")
        reversed_result = invert_single_transformation([token_str], "i3a")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[1] = Token(set("pca"))
        reversed_result = invert_single_transformation([token_str], "i1p")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pcde") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[1] = Token(set("pca"))
        reversed_result = invert_single_transformation([token_str], "i1e")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        ### Reset Configuration ###
        # This is done multiple times in this test function
        self.switch_to_jtr()

        # test N > string_length case. Append anyway
        token_str = TokenString("12")
        reversed_result = invert_single_transformation(
            [token_str], ["i", "2", set("123")])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"1") == False:
            raise Exception("Unittest Not Passed")

        # test N > string_length case. Append anyway
        token_str = TokenString("12")
        reversed_result = invert_single_transformation(
            [token_str], ["i", "2", set("s13")])
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        # test empty string
        token_str = TokenString("")
        reversed_result = invert_single_transformation(
            [token_str], ["i", "2", set("s13")])
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("Somesuperlongpasswordthatdoesn'")
        reversed_result = invert_single_transformation(
            [token_str], ["i", "2", set("s13")])
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Somesuperlongpasswordthatdoesn'") == False:
            raise Exception("Unittest Not Passed")

        # test max length case
        token_str = TokenString("Somesuperlongpasswordthatdoesn'")
        reversed_result = invert_single_transformation(
            [token_str], ["i", "2", set("m123ad")])
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Somesuperlongpasswordthatdoesn'") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Soesuperlongpasswordthatdoesn'") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest ONM Command ######
        ### Reset Configuration ###
        self.switch_to_hc()

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "O01")
        if reversed_result.get_number_of_strings() != 257:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"0") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"z") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("0")
        reversed_result = invert_single_transformation([token_str], "O22")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"0") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("01")
        reversed_result = invert_single_transformation([token_str], "O22")
        if reversed_result.get_number_of_strings() != 256 * 256 + 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"01") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"01ab") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("012")
        reversed_result = invert_single_transformation([token_str], "O22")
        if reversed_result.get_number_of_strings() != 256 * 256 + 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"012") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"01bd2") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("012")
        reversed_result = invert_single_transformation([token_str], "O22")
        if reversed_result.get_number_of_strings() != 256 * 256 + 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"012") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"01ab2") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("0156789")
        reversed_result = invert_single_transformation([token_str], "O22")
        if reversed_result.get_number_of_strings() != 256 * 256:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"01ae56789") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString(
            "015678901234567890123456789011")  # Len 30. Rejected
        reversed_result = invert_single_transformation([token_str], "O22")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        ###### Unittest oNX Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "o12")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab2")
        reversed_result = invert_single_transformation([token_str], "o3a")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ab2") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab3ab")
        reversed_result = invert_single_transformation([token_str], "o3a")
        if reversed_result.get_number_of_strings() != 256:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"ab3*b") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab3cb")
        reversed_result = invert_single_transformation([token_str], "o3a")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[1] = Token(set("pca"))
        reversed_result = invert_single_transformation([token_str], "o1p")
        if reversed_result.get_number_of_strings() != 256:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"p~cde") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[1] = Token(set("pca"))
        reversed_result = invert_single_transformation([token_str], "o1e")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        ###### Unittest *NM Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "*12")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("super")
        reversed_result = invert_single_transformation([token_str], "*16")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"super") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("super")
        reversed_result = invert_single_transformation([token_str], "*61")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"super") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("memory")
        reversed_result = invert_single_transformation([token_str], "*23")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"meomry") == False:
            raise Exception("Unittest Not Passed")

    def test_memory_and_mode_cmds(self):
        self.switch_to_hc()

        token_str = TokenString("memory")
        reversed_result = invert_single_transformation([token_str], "M")
        if reversed_result.get_status() != InversionStatus.OUTSCOPE:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("memory")
        reversed_result = invert_single_transformation([token_str], "Q")
        if reversed_result.get_status() != InversionStatus.OUTSCOPE:
            raise Exception("Unittest Not Passed")\

        token_str = TokenString("memory")
        reversed_result = invert_single_transformation([token_str], "X123")
        if reversed_result.get_status() != InversionStatus.OUTSCOPE:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("memory")
        reversed_result = invert_single_transformation([token_str], "va23")
        if reversed_result.get_status() != InversionStatus.OUTSCOPE:
            raise Exception("Unittest Not Passed")

        self.switch_to_jtr()
        token_str = TokenString("1")
        reversed_result = invert_single_transformation([token_str], "1")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("2")
        reversed_result = invert_single_transformation([token_str], "2")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("3")
        reversed_result = invert_single_transformation([token_str], "+")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

    def test_length_rejection_cmds(self):
        ###### Unittest >N Command ######
        self.switch_to_jtr()

        token_str = TokenString("memory")
        reversed_result = invert_single_transformation([token_str], ">3")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"memory") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("memo")
        reversed_result = invert_single_transformation([token_str], ">3")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"memo") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("mem")
        reversed_result = invert_single_transformation([token_str], ">3")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], ">3")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        self.switch_to_hc()
        token_str = TokenString("memory")
        reversed_result = invert_single_transformation([token_str], ">3")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"memory") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("memo")
        reversed_result = invert_single_transformation([token_str], ">3")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"memo") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("mem")
        reversed_result = invert_single_transformation([token_str], ">3")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"mem") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], ">3")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        ###### Unittest <N Command ######
        self.switch_to_jtr()

        token_str = TokenString("memory")
        reversed_result = invert_single_transformation([token_str], "<4")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("memo")
        reversed_result = invert_single_transformation([token_str], "<4")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("mem")
        reversed_result = invert_single_transformation([token_str], "<4")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"mem") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "<4")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        self.switch_to_hc()
        token_str = TokenString("memory")
        reversed_result = invert_single_transformation([token_str], "<4")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("memo")
        reversed_result = invert_single_transformation([token_str], "<4")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"memo") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("mem")
        reversed_result = invert_single_transformation([token_str], "<4")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"mem") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "<4")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest _N Command ######
        token_str = TokenString("memory")
        reversed_result = invert_single_transformation([token_str], "_4")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("memo")
        reversed_result = invert_single_transformation([token_str], "_4")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"memo") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("mem")
        reversed_result = invert_single_transformation([token_str], "_4")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "_4")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

    def test_char_class_cmds(self):
        self.switch_to_jtr()

        ###### Unittest !X Command ######
        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], "!b")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        token_str[0] = Token("bp")
        reversed_result = invert_single_transformation([token_str], "!b")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bed")  # bed eed bpd epd
        token_str[0] = Token("be")
        token_str[1] = Token("ep")
        reversed_result = invert_single_transformation([token_str], "!e")
        if reversed_result.get_number_of_strings() != 1:  # Have duplicates
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bpd") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "!b")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest !?C Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "!?u")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], "!?u")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], "!?d")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        token_str[0] = Token("b123")
        reversed_result = invert_single_transformation([token_str], "!?d")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        token_str[0] = Token("BP")
        reversed_result = invert_single_transformation([token_str], "!?u")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bed")  # bed eed bpd epd
        token_str[0] = Token("bE")
        token_str[1] = Token("ap")
        reversed_result = invert_single_transformation([token_str], "!?u")
        if reversed_result.get_number_of_strings() != 2:  # Have duplicates
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bpd") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bad") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest /X Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "/b")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], "/b")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        token_str[0] = Token("bp")
        reversed_result = invert_single_transformation([token_str], "/b")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bed")  # bed eed bpd epd
        token_str[0] = Token("be")
        token_str[1] = Token("ep")
        reversed_result = invert_single_transformation([token_str], "/e")
        if reversed_result.get_number_of_strings() != 4:  # Have duplicates
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"eed") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"epd") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bed") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest /?C Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "/?u")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], "/?u")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("12ed")
        token_str[0] = Token("1b")
        token_str[1] = Token("2a")
        reversed_result = invert_single_transformation([token_str], "/?d")
        if reversed_result.get_number_of_strings() != 4:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"12ed") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"1aed") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"b2ed") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("1ped")
        token_str[0] = Token("1fsabz@#ASF")
        reversed_result = invert_single_transformation([token_str], "/?d")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"1ped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Bped")
        token_str[0] = Token("BP")
        reversed_result = invert_single_transformation([token_str], "/?u")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Bped") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bad")
        token_str[0] = Token("bE")
        token_str[1] = Token("ap")
        reversed_result = invert_single_transformation([token_str], "/?u")
        if reversed_result.get_number_of_strings() != 2:  # Have duplicates
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Ead") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Epd") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest =NX Command ######
        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], "=0b")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], "=0b")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        token_str[0] = Token("bp")
        reversed_result = invert_single_transformation([token_str], "=0b")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bed")
        token_str[0] = Token("be")
        token_str[1] = Token("ep")
        reversed_result = invert_single_transformation([token_str], "=1e")
        if reversed_result.get_number_of_strings() != 2:  # Have duplicates
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"eed") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bed") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "=1e")
        if reversed_result.get_number_of_strings() != 0:  # Have duplicates
            raise Exception("Unittest Not Passed")

        ###### Unittest =N?C Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "=0?u")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], "=0?u")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("12ed")
        token_str[0] = Token("1b")
        token_str[1] = Token("2a")
        reversed_result = invert_single_transformation([token_str], "=1?d")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"12ed") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"b2ed") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("1ped")
        token_str[0] = Token("1fsabz@#ASF")
        reversed_result = invert_single_transformation([token_str], "=0?d")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"1ped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Bped")
        token_str[0] = Token("BP")
        reversed_result = invert_single_transformation([token_str], "=0?u")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Bped") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bad")
        token_str[0] = Token("bE")
        token_str[1] = Token("ap")
        reversed_result = invert_single_transformation([token_str], "=0?u")
        if reversed_result.get_number_of_strings() != 2:  # Have duplicates
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Ead") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Epd") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest (X Command ######
        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], "(b")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], "(b")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        token_str[0] = Token("bp")
        reversed_result = invert_single_transformation([token_str], "(b")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bed")
        token_str[0] = Token("be")
        token_str[1] = Token("ep")
        reversed_result = invert_single_transformation([token_str], "(e")
        if reversed_result.get_number_of_strings() != 2:  # Have duplicates
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"eed") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"epd") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "(e")
        if reversed_result.get_number_of_strings() != 0:  # Have duplicates
            raise Exception("Unittest Not Passed")

        ###### Unittest (?C (left_paren) Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "(?u")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], "(?u")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("12ed")
        token_str[0] = Token("1b")
        token_str[1] = Token("2a")
        reversed_result = invert_single_transformation([token_str], "(?d")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"12ed") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"1aed") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("1ped")
        token_str[0] = Token("1fsabz@#ASF")
        reversed_result = invert_single_transformation([token_str], "(?d")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"1ped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Bped")
        token_str[0] = Token("BP")
        reversed_result = invert_single_transformation([token_str], "(?u")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Bped") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bad")
        token_str[0] = Token("bE")
        token_str[1] = Token("ap")
        reversed_result = invert_single_transformation([token_str], "(?u")
        if reversed_result.get_number_of_strings() != 2:  # Have duplicates
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Ead") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Epd") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest )X Command ######
        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], ")b")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], ")d")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        token_str[-1] = Token("dp")
        reversed_result = invert_single_transformation([token_str], ")d")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("beb")
        token_str[-1] = Token("be")
        token_str[1] = Token("ep")
        reversed_result = invert_single_transformation([token_str], ")e")
        if reversed_result.get_number_of_strings() != 2:  # Have duplicates
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bee") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bpe") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], ")e")
        if reversed_result.get_number_of_strings() != 0:  # Have duplicates
            raise Exception("Unittest Not Passed")

        ###### Unittest )?C (right_paren) Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "(?u")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], "(?u")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("12ed")
        token_str[0] = Token("1b")
        token_str[1] = Token("2a")
        reversed_result = invert_single_transformation([token_str], "(?d")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"12ed") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"1aed") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("1ped")
        token_str[0] = Token("1fsabz@#ASF")
        reversed_result = invert_single_transformation([token_str], "(?d")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"1ped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Bped")
        token_str[0] = Token("BP")
        reversed_result = invert_single_transformation([token_str], "(?u")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Bped") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bad")
        token_str[0] = Token("bE")
        token_str[1] = Token("ap")
        reversed_result = invert_single_transformation([token_str], "(?u")
        if reversed_result.get_number_of_strings() != 2:  # Have duplicates
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Ead") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Epd") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest %NX Command ######
        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], r"%2b")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("dped")
        reversed_result = invert_single_transformation([token_str], r"%2d")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"dped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bped")
        token_str[0] = Token("db")
        reversed_result = invert_single_transformation([token_str], r"%2d")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"dped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("bee")  # bee, bpe, eee, epe
        token_str[0] = Token("be")
        token_str[1] = Token("ep")
        reversed_result = invert_single_transformation([token_str], r"%2e")
        if reversed_result.get_number_of_strings() != 4:  # Have duplicates
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"bee") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"eee") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"epe") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], r"%1e")
        if reversed_result.get_number_of_strings() != 0:  # Have duplicates
            raise Exception("Unittest Not Passed")

        ###### Unittest %N?C Command ######
        token_str = TokenString("bped")
        reversed_result = invert_single_transformation([token_str], r"%1?d")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("d12d")
        reversed_result = invert_single_transformation([token_str], r"%2?d")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"d12d") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("dped")
        token_str[0] = Token("dB")
        reversed_result = invert_single_transformation([token_str], r"%2?l")
        if reversed_result.get_number_of_strings() != 2:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"dped") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Bped") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("b11")
        token_str[0] = Token("b1")
        token_str[1] = Token("1p")
        reversed_result = invert_single_transformation([token_str], r"%2?d")
        if reversed_result.get_number_of_strings() != 4:  # Have duplicates
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"b11") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"111") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"1p1") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], r"%1?a")
        if reversed_result.get_number_of_strings() != 0:  # Have duplicates
            raise Exception("Unittest Not Passed")

        ###### Unittest @X Command ######
        token_str = TokenString("abcdefghijklmn")
        reversed_result = invert_single_transformation([token_str], "@a")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abcdefgh")
        reversed_result = invert_single_transformation([token_str], "@b")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abcdefgh")
        reversed_result = invert_single_transformation([token_str], "@1")
        if reversed_result.get_status() != InversionStatus.OUTSCOPE:
            raise Exception("Unittest Not Passed")

        ###### Unittest @?C Command ######
        token_str = TokenString("12abcdefghijklmn")
        reversed_result = invert_single_transformation([token_str], "@?a")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("ab123456")
        reversed_result = invert_single_transformation([token_str], "@?d")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("123456")
        token_str[0] = Token("123")
        reversed_result = invert_single_transformation([token_str], "@?d")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("123")
        reversed_result = invert_single_transformation([token_str], "@?a")
        if reversed_result.get_status() != InversionStatus.OUTSCOPE:
            raise Exception("Unittest Not Passed")

        ###### Unittest eX Command ######
        token_str = TokenString("")
        reversed_result = invert_single_transformation([token_str], "e ")
        if reversed_result.get_number_of_strings() != 1:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        # abcd123 should be in wordlist
        if reversed_result.contains(b"") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Pa@@ Wo!!!")
        reversed_result = invert_single_transformation([token_str], "e ")
        if reversed_result.get_number_of_strings() != 16:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"Pa@@ wo!!!") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"pA@@ WO!!!") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pa@@ Wo!!!")
        reversed_result = invert_single_transformation([token_str], "e ")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("PA@@ Wo!!!")
        reversed_result = invert_single_transformation([token_str], "e ")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Pa@@ wo!!!")
        reversed_result = invert_single_transformation([token_str], "e ")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("Pa@@ WO!!!")
        reversed_result = invert_single_transformation([token_str], "e ")
        if reversed_result.get_number_of_strings() != 0:  # Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("P W")
        reversed_result = invert_single_transformation([token_str], "e ")
        if reversed_result.get_number_of_strings() != 4:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"P W") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"P w") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"p W") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"p w") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("P@W")
        reversed_result = invert_single_transformation([token_str], "e@")
        if reversed_result.get_number_of_strings() != 4:  # Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"P@W") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"P@w") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"p@W") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"p@w") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[0] = Token(set("Aa"))
        token_str.tokens[1] = Token(set(" a"))
        token_str.tokens[2] = Token(set(" B"))
        token_str.tokens[3] = Token(set("c"))
        token_str.tokens[4] = Token(set("d"))
        reversed_result = invert_single_transformation([token_str], "e ")
        if reversed_result.get_number_of_strings() != 16:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"A bCd") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"A BCd") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"a bCd") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[0] = Token(set("Aa"))
        token_str.tokens[1] = Token(set("*a"))
        token_str.tokens[2] = Token(set("*B"))
        token_str.tokens[3] = Token(set("c"))
        token_str.tokens[4] = Token(set("d"))
        reversed_result = invert_single_transformation([token_str], "e*")
        if reversed_result.get_number_of_strings() != 16:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"A*bCd") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"A*BCd") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains(b"a*bCd") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest sXY Command ######
        token_str = TokenString("above")
        reversed_result = invert_single_transformation([token_str], "sab")
        if reversed_result.get_number_of_strings() != 0: #Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("above")
        reversed_result = invert_single_transformation([token_str], "sdf")
        if reversed_result.get_number_of_strings() != 1: #Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"above") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("above")
        reversed_result = invert_single_transformation([token_str], "sll")
        if reversed_result.get_number_of_strings() != 1: #Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"above") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("love")
        reversed_result = invert_single_transformation([token_str], "sll")
        if reversed_result.get_number_of_strings() != 1: #Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"love") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("love")
        token_str[0] = Token("ab")
        reversed_result = invert_single_transformation([token_str], "sab")
        if reversed_result.get_number_of_strings() != 2: #Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"aove") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"bove") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("love")
        reversed_result = invert_single_transformation([token_str], "sla")
        if reversed_result.get_number_of_strings() != 0: #Should Be Rejected
            raise Exception("Unittest Not Passed")
        
        token_str = TokenString("love")
        reversed_result = invert_single_transformation([token_str], "sal")
        if reversed_result.get_number_of_strings() != 2: #Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"aove") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"love") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("frank")
        reversed_result = invert_single_transformation([token_str], "sff")
        if reversed_result.get_number_of_strings() != 1: #Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"frank") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("above")
        reversed_result = invert_single_transformation([token_str], "sfe")
        if reversed_result.get_number_of_strings() != 2: #Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"above") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"abovf") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[1] = Token(set("ab"))
        reversed_result = invert_single_transformation([token_str], "sba")
        if reversed_result.get_number_of_strings() != 2:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"pacde") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"pbcde") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[1] = Token(set("bd"))
        reversed_result = invert_single_transformation([token_str], "sba")
        if reversed_result.get_number_of_strings() != 1:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"pdcde") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[1] = Token(set("ac"))
        reversed_result = invert_single_transformation([token_str], "sba")
        if reversed_result.get_number_of_strings() != 3:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"pacde") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"pbcde") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"pccde") == False:
            raise Exception("Unittest Not Passed")

        ###### Unittest s?CY Command ######
        token_str = TokenString("above")
        reversed_result = invert_single_transformation([token_str], "s??a")
        if reversed_result.get_number_of_strings() != 2: #Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains (b"above") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains (b"?bove") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("abc")
        reversed_result = invert_single_transformation([token_str], "s?la")
        if reversed_result.get_number_of_strings() != 0: #Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("b12")
        token_str.tokens[0] = Token(set("b1234"))
        reversed_result = invert_single_transformation([token_str], "s?la")
        if reversed_result.get_number_of_strings() != 4: #Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("b12")
        token_str.tokens[0] = Token(set("ab1234"))
        reversed_result = invert_single_transformation([token_str], "s?la")
        if reversed_result.get_number_of_strings() != 30: #Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("a12")
        reversed_result = invert_single_transformation([token_str], "s?la")
        if reversed_result.get_number_of_strings() != 26: #Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"a12") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"z12") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("above")
        reversed_result = invert_single_transformation([token_str], "s?da")
        if reversed_result.get_number_of_strings() != 11: #Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"above") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"0bove") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"9bove") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("pacde")
        token_str.tokens[1] = Token(set("ab"))
        reversed_result = invert_single_transformation([token_str], "s?D0")
        if reversed_result.get_number_of_strings() != 0:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("10235")
        token_str.tokens[1] = Token(set("0aDe?*"))
        reversed_result = invert_single_transformation([token_str], "s?D0")
        if reversed_result.get_number_of_strings() != 86:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"1a235") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"1?235") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"1 235") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"1'235") == False:
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"10235") == False:
            raise Exception("Unittest Not Passed")

    def test_reject_flags(self):
        self.switch_to_jtr()
        token_str = TokenString("flag")
        reversed_result = invert_single_transformation([token_str], "-s")
        if reversed_result.get_number_of_strings() != 0: #Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("flag")
        reversed_result = invert_single_transformation([token_str], "-p")
        if reversed_result.get_number_of_strings() != 0: #Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("flag")
        reversed_result = invert_single_transformation([token_str], "-8")
        if reversed_result.get_number_of_strings() != 0: #Should Be Rejected
            raise Exception("Unittest Not Passed")

        token_str = TokenString("flag")
        reversed_result = invert_single_transformation([token_str], "-c")
        if reversed_result.get_number_of_strings() != 1: #Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"flag") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("flag")
        reversed_result = invert_single_transformation([token_str], "-:")
        if reversed_result.get_number_of_strings() != 1: #Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"flag") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("flag")
        reversed_result = invert_single_transformation([token_str], "->2")
        if reversed_result.get_number_of_strings() != 1: #Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"flag") == False:
            raise Exception("Unittest Not Passed")

        token_str = TokenString("flag")
        reversed_result = invert_single_transformation([token_str], "-<6")
        if reversed_result.get_number_of_strings() != 1: #Should Be Rejected
            raise Exception("Unittest Not Passed")
        if reversed_result.contains ( b"flag") == False:
            raise Exception("Unittest Not Passed")

    @unittest.skip
    def test_inversion_on_JTR_rulelist(self):
        """ test on rule files. time-intensive. by default skipped """

        ### Test Configuration ###
        wordlists_to_use = ["test_inversion.lst"]
        rulelists_to_use = ["test_inversion_JtR.rule"]
        tmp_file_address = "tmp.txt"  # tmp output, will be removed after running
        ##########################

        # Start testing
        self.switch_to_jtr(max_password_length=125)

        if shutil.which(RUNTIME_CONFIG['executable_path']) == None:
            #print("\nJtR Command Executable Doesn't Exist, JtR Test Skipped")
            return

        test_successful = True
        for wordlist_name in wordlists_to_use:

            for rule_list_name in rulelists_to_use:
                rule_list = RulelistReader.read_and_parse_rule_list(
                    rule_list_name, safe_mode=False)

                for r_idx, one_rule in enumerate(rule_list):
                    if check_is_invertible(one_rule) != Invertibility.INVERTIBLE:
                        logging.info(
                            "Rule: {} Not Invertible\n".format(one_rule.raw))

                    else:
                        logging.info("Testing Rule: {}\n".format(r_idx))

                        forward_a_rule_to_an_address(
                            wordlist_name, one_rule, tmp_file_address)
                        with open(tmp_file_address) as f:
                            for line in f:
                                line = line.strip("\r\n")
                                if line == "":
                                    continue
                                pwd, original_word = line.strip(
                                    "\r\n").split("\t")

                                results = invert_one_rule(
                                    TokenString(pwd), one_rule)
                                if results.get_status() == InversionStatus.NORMAL and results.contains(original_word) == True:
                                    continue

                                else:
                                    test_successful = False
                                    logging.info(
                                        "Fail Case: Rule:{}\tOriginal:{}".format(one_rule.raw, original_word))

        os.remove(tmp_file_address) if os.path.exists(
            tmp_file_address) else None
        if test_successful == True:
            logging.info(
                "Test Successful: {} + {}".format(wordlist_name, rule_list_name))

        else:
            logging.info(
                "Test Failed: {} + {}".format(wordlist_name, rule_list_name))

    @unittest.skip
    def test_inversion_on_HC_rulelist(self):
        """ test on rule files. time-intensive. by default skipped """

        ### Test Configuration ###
        wordlists_to_use = ["test_inversion.lst"]
        rulelists_to_use = ["test_inversion_HC.rule"]
        tmp_file_address = "tmp.txt"  # tmp output, will be removed after running
        ##########################

        # Start testing
        self.switch_to_hc(max_password_length=255)

        if shutil.which(RUNTIME_CONFIG['executable_path']) == None:
            #print("\nHC Command Executable Doesn't Exist, HC Test Skipped")
            return

        test_successful = True
        for wordlist_name in wordlists_to_use:

            for rule_list_name in rulelists_to_use:
                rule_list = RulelistReader.read_and_parse_rule_list(
                    rule_list_name, safe_mode=False)

                for r_idx, one_rule in enumerate(rule_list):
                    if check_is_invertible(one_rule) != Invertibility.INVERTIBLE:
                        logging.info(
                            "Rule: {} Not Invertible\n".format(one_rule.raw))

                    else:
                        logging.info("Testing Rule: {}\n".format(r_idx))
                        forward_a_rule_to_an_address(
                            wordlist_name, one_rule, tmp_file_address)
                        # encoding = charmap for hashcat.
                        with open(tmp_file_address, encoding="charmap") as f:
                            for line in f:
                                line = line.strip("\r\n")
                                if line == "":
                                    continue
                                pwd, original_word = line.strip(
                                    "\r\n").split("\t")

                                results = invert_one_rule(
                                    TokenString(pwd), one_rule)
                                if results.get_status() == InversionStatus.NORMAL and results.contains(original_word) == True:
                                    continue

                                else:
                                    test_successful = False
                                    logging.info(
                                        "Fail Case: Rule:{}\tOriginal:{}".format(one_rule.raw, original_word))

        os.remove(tmp_file_address) if os.path.exists(
            tmp_file_address) else None
        if test_successful == True:
            logging.info(
                "Test Successful: {} + {}".format(wordlist_name, rule_list_name))

        else:
            logging.info(
                "Test Failed: {} + {}".format(wordlist_name, rule_list_name))


if __name__ == "__main__":
    # Run Unit Test
    rule_suite = unittest.TestLoader().loadTestsFromTestCase(InversionTest)
    rule_runner = unittest.TextTestRunner()
    rule_runner.run(rule_suite)

"""This file contains utility functions and methods for invert_rule

Mostly definitions usded in JtR/HC here.

Reference:
1. https://github.com/magnumripper/JohnTheRipper/blob/27f51880a4daf1372a115a49c2e04b9fb2406209/src/rules.c
"""
from collections import defaultdict
from common import RunningStyle
from config import RUNTIME_CONFIG

# White Space Doesnt Consider \t here. As we use \t as seperator.
WHITESPACE = " "
CHARS_VOWELS = "aeiouAEIOU"
CHARS_CONSONANTS = "bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ"
CHARS_LOWER = "abcdefghijklmnopqrstuvwxyz"
CHARS_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
CHARS_PUNCTUATION = ".,:;'\"?!`"
CHARS_SPECIALS = "$%^&*()-_+=|\\<>[]{}#@/~"
CHARS_DIGITS = "0123456789"
CHARS_LETTERS = CHARS_LOWER + CHARS_UPPER

CONV_SOURCE = "`1234567890-=\\qwertyuiop[]asdfghjkl;'zxcvbnm,./~!@#$%^&*()_+|QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?"
CONV_SHIFT = "~!@#$%^&*()_+|QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?`1234567890-=\\qwertyuiop[]asdfghjkl;'zxcvbnm,./"
CONV_INVERT = "`1234567890-=\\QWERTYUIOP[]ASDFGHJKL;'ZXCVBNM,./~!@#$%^&*()_+|qwertyuiop{}asdfghjkl:\"zxcvbnm<>?"  # invert aka toggle
CONV_VOWELS = "`1234567890-=\\QWeRTYuioP[]aSDFGHJKL;'ZXCVBNM,./~!@#$%^&*()_+|QWeRTYuioP{}aSDFGHJKL:\"ZXCVBNM<>?"
CONV_RIGHT = "1234567890-=\\\\wertyuiop[]]sdfghjkl;''xcvbnm,./\\!@#$%^&*()_+||WERTYUIOP{}}SDFGHJKL:\"\"XCVBNM<>?|"
CONV_LEFT = "``1234567890-=qqwertyuiop[aasdfghjkl;zzxcvbnm,.~~!@#$%^&*()_+QQWERTYUIOP{AASDFGHJKL:ZZXCVBNM<>"

CHAR_CLASSES = '?vcwpsludaxzVCWPSLUDAXZ'  # All the possible character classes
# all printables allowed
PRINTABLES = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ '


class Setup():
    """ setting up dictionaries for inversion use """

    @staticmethod
    def create_toggle():
        """ Create the preimage for toggle command """
        upper_to_lower = {x: x.lower() for x in CHARS_UPPER}
        lower_to_upper = {x: x.upper() for x in CHARS_LOWER}

        return {**upper_to_lower, **lower_to_upper}

    @staticmethod
    def create_character_classes_dict():
        """  Create class_dict, which follows JtR's definition. Also used in HC.

            ??  matches "?"
            ?v  matches vowels: "aeiouAEIOU"
            ?c  matches consonants: "bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ"
            ?w  matches whitespace: space and horizontal tabulation characters
            ?p  matches punctuation: ".,:;'?!`" and the double quote character
            ?s  matches symbols "$%^&*()-_+=|\<>[]{}#@/~"
            ?l  matches lowercase letters [a-z]
            ?u  matches uppercase letters [A-Z]
            ?d  matches digits [0-9]
            ?a  matches letters [a-zA-Z]
            ?x  matches letters and digits [a-zA-Z0-9]
            ?z  matches all characters
        """

        # built dict
        d = {
            '?':
            '?',
            'v':
            CHARS_VOWELS,
            'c':
            CHARS_CONSONANTS,
            'w':
            WHITESPACE,
            'p':
            CHARS_PUNCTUATION,
            's':
            CHARS_SPECIALS,
            'l':
            CHARS_LOWER,
            'u':
            CHARS_UPPER,
            'd':
            CHARS_DIGITS,
            'a':
            CHARS_LETTERS,
            'x':
            CHARS_LETTERS + CHARS_DIGITS,
            'z':
            set(chr(x) for x in range(256)) if RUNTIME_CONFIG.is_hc() else set(
                chr(x) for x in range(32, 127))
        }

        for key in "VCWPSLUDAXZ":
            lower_key = key.lower()
            d[key] = "".join(i for i in PRINTABLES if i not in d[lower_key])

        return {k: set(v) for k, v in d.items()}

    @staticmethod
    def create_shift_by_shift():
        """ Create the preimage for JtR shift command """
        if len(CONV_SHIFT) != len(CONV_SOURCE):
            raise Exception("Length Broken")

        # build dict
        d = {
            v[0]: v[1]
            for v in zip(CONV_SHIFT + WHITESPACE, CONV_SOURCE + WHITESPACE)
        }

        if len(d) != len(PRINTABLES):
            raise Exception("Dictionary Broken")

        return d

    @staticmethod
    def create_shift_to_left(shift_dict):
        """ Create the preimage for JtR keyboard shift left command """
        d = defaultdict(set)

        if len(CONV_LEFT) != len(CONV_SOURCE):
            raise Exception("Length Broken")

        # build dict
        for v in zip(CONV_LEFT + WHITESPACE, CONV_SOURCE + WHITESPACE):
            d[v[0]].add(v[1])

        # add missing part
        for v in PRINTABLES:
            if v not in d:
                d[v] = None

        if len(d) != len(PRINTABLES):
            raise Exception("Dictionary Broken")

        return d

    @staticmethod
    def create_shift_to_right(shift_dict):
        """ Create the preimage for JtR keyboard shift right command """
        d = defaultdict(set)

        if len(CONV_RIGHT) != len(CONV_SOURCE):
            raise Exception("Length Broken")

        # build dict
        for v in zip(CONV_RIGHT + WHITESPACE, CONV_SOURCE + WHITESPACE):
            d[v[0]].add(v[1])

        # add missing part
        for v in PRINTABLES:
            if v not in d:
                d[v] = None

        if len(d) != len(PRINTABLES):
            raise Exception("Dictionary Broken")

        return d


class Dicts():
    """ Contains a bunch of helpful dictionaries. """
    classes = Setup.create_character_classes_dict()
    toggle = Setup.create_toggle()
    shift = Setup.create_shift_by_shift()
    left = Setup.create_shift_to_left(shift)
    right = Setup.create_shift_to_right(shift)

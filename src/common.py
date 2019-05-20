""" This file contains classes used across different modules """

from enum import Enum
import os
from pyparsing import srange


class RunningStyle(Enum):
    """ An enum that denotes the run time style. Either JtR or Hashcat """
    JTR = 0
    HC = 1


class FatalRuntimeError(Exception):
    """ Exception raised when program runs into fatal errors.

    These are errors that will stop the program from running.
    """

    def __init__(self, msg):
        Exception.__init__(self, msg)


class FilePath():
    """ Wraps the path to a file """

    def __init__(self, a_path):
        if os.path.isfile(a_path) == False:
            raise FatalRuntimeError("Path Error: {}".format(a_path))

        self.info = {}
        abs_path = os.path.abspath(a_path)  # get absolute path
        self.info['addr'] = abs_path  # set full address
        self.info['prefix'], self.info['name'] = os.path.split(
            abs_path)  # get directory and basename

    def __getitem__(self, key):
        return self.info[key]


class PasswordPolicyConf():
    """ Wraps the password policy configuration specified 

    Attr:
        length: whether there's a requirement on length, and what length it is
        digit: whether there's a requirement on digit
        letter: whether there's a requirement on letter
        lower: whether there's a requirement on lowercase letter
        upper: whether there's a requirement on uppercase letter

    """

    def __init__(self,
                 length=-1,
                 digit=False,
                 letter=False,
                 lower=False,
                 upper=False):

        if length == 0:
            raise Exception("Password Policy Invalid")
        if length == None:  # no length
            length = -1

        self.length = length
        self.digit = digit
        self.letter = letter
        self.lower = lower
        self.upper = upper

    def to_arg_string(self):
        """ to string in arg format e.g. (--length=6 --digit --letter)"""
        pol = " "
        if self.length >= 1:
            pol += "--length=" + str(self.length) + " "
        if self.digit == True:
            pol += "--digit "
        if self.letter == True:
            pol += "--letter "
        if self.upper == True:
            pol += "--upper "
        if self.lower == True:
            pol += "--lower "
        return pol if pol != " " else ""

    def to_compact_string(self):
        """ to string in compact format e.g. (-length=6-digit-letter)"""
        pol = ""
        if self.length >= 1:
            pol += "-length=" + str(self.length)
        if self.digit == True:
            pol += "-digit"
        if self.letter == True:
            pol += "-letter"
        if self.upper == True:
            pol += "-upper"
        if self.lower == True:
            pol += "-lower"
        return pol

    def to_rule_string(self, is_jtr):
        """ to string in rule format e.g. (>6 /?a /?d), JTR only """
        pol = " "
        if self.length >= 1:
            if is_jtr == True:
                if self.length <= 10:
                    pol += ">" + str(self.length - 1) + " "
                else:
                    pol += ">" + chr(ord('A') + self.length - 11) + " "
            else:  # hc < means <=, > means >=
                if self.length <= 9:
                    pol += ">" + str(self.length) + " "
                else:
                    pol += ">" + chr(ord('A') + self.length - 10) + " "
        if self.digit == True:
            pol += "/?d "
        if self.letter == True:
            pol += "/?a "
        if self.upper == True:
            pol += "/?u "
        if self.lower == True:
            pol += "/?l "
        return pol if pol != " " else ""

    def to_debug_string(self):
        """ to_arg_string, if empty return none """
        v = self.to_arg_string()
        if v == "":
            return "None"
        else:
            return v

    def arg_string_to_pw_policy(string):
        """ convert from arg string to password policy instance"""
        string = string.strip()
        if string == "":
            return PasswordPolicyConf()

        string_split = string.split(" ")

        length = -1
        digit = False
        letter = False
        lower = False
        upper = False

        for val in string_split:
            if "--digit" in val:
                digit = True
            elif "--letter" in val:
                letter = True
            elif "--lower" in val:
                lower = True
            elif "--upper" in val:
                upper = True
            elif val.startswith("--length="):
                length = int(val[len("--length="):])

        return PasswordPolicyConf(length, digit, letter, lower, upper, symbols)


# Used in AN Command
class Queue:
    """ A homemade queue """

    def __init__(self):
        self.items = []

    def empty(self):
        return self.items == []

    def enqueue(self, item):
        self.items.insert(0, item)

    def dequeue(self):
        return self.items.pop()

    def size(self):
        return len(self.items)

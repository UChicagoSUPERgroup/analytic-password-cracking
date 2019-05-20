from os import path as os_path
from sys import path as sys_path

sys_path.append(os_path.abspath('../src'))

from parse import hc_numeric_constants, jtr_numeric_constants_dash_allowed, RulelistReader
from parse import jtr_must_escape_for_single_char, jtr_could_escape_for_single_char
from parse import Groups, jtr_must_escape_for_range, jtr_numeric_constants, Elements
from invert_helper import CHAR_CLASSES
from config import RUNTIME_CONFIG
from common import RunningStyle
from pyparsing import printables
import unittest


class ParseTest(unittest.TestCase):
    """Verifies the functionality of the JTR rule parser"""


    def test_groups(self):

        ############### Test Groups.single_position() Function #########
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        X = Groups.single_position()

        # Validation
        for c in jtr_numeric_constants:
            if not X.matches(c):
                raise Exception("single_position Contruction Error")
        ############################################################

        ############### Test Groups.in_bracket_position() Function #########
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        X = Groups.in_bracket_position()

        # Validation
        for c in jtr_numeric_constants:
            if c == "-":
                if not X.matches("\\"+c) or X.matches(c):
                    raise Exception("in_bracket_position Contruction Error")
            elif not X.matches(c):
                raise Exception("in_bracket_position Contruction Error")

        for c1 in jtr_numeric_constants_dash_allowed:
            for c2 in jtr_numeric_constants_dash_allowed:
                if not X.matches(c1+"-"+c2):
                    raise Exception("in_bracket_position Contruction Error")
        ############################################################

        ############### Test Groups.single_char() Function #########
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        X = Groups.single_char()
        # Validation before return.
        for c in jtr_must_escape_for_single_char:
            if X.matches(c):
                raise Exception("single_char Contruction Error")
            if not X.matches("\\"+c):
                raise Exception("single_char Contruction Error")

        for c in jtr_could_escape_for_single_char:
            if not X.matches(c):
                raise Exception("single_char Contruction Error")
            if not X.matches("\\"+c):
                raise Exception("single_char Contruction Error")

        for c in printables + " ":
            if c not in jtr_must_escape_for_single_char and not X.matches(c):
                raise Exception("single_char Contruction Error")

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        X = Groups.single_char()
        for c in printables + " ":
            if not X.matches(c):
                raise Exception("single_char Contruction Error")
        ############################################################

        ############### Test Groups.single_char_append() Function #########
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        X = Groups.single_char_append()
        # Validation
        for c in jtr_must_escape_for_single_char:
            if X.matches(c):
                raise Exception("single_char_append Contruction Error")
            if not X.matches("\\"+c):
                raise Exception("single_char_append Contruction Error")

        for c in jtr_could_escape_for_single_char:
            if not X.matches(c):
                raise Exception("single_char_append Contruction Error")
            if not X.matches("\\"+c):
                raise Exception("single_char_append Contruction Error")

        for c in printables:
            if c not in jtr_must_escape_for_single_char + '"' and not X.matches(c):
                raise Exception("single_char_append Contruction Error")
        ############################################################

        ############### Test Groups.in_bracket_char() Function #########
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        X = Groups.in_bracket_char()

        # Validation
        for c in jtr_must_escape_for_range:
            if X.matches(c):
                raise Exception("in_bracket_char Contruction Error")
            if not X.matches("\\"+c):
                raise Exception("in_bracket_char Contruction Error")

        for c in printables:
            if c not in jtr_must_escape_for_range and not X.matches(c):
                raise Exception("in_bracket_char Contruction Error")
        ############################################################

        ############### Test Groups.in_bracket_char_append() Function #########
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        X = Groups.in_bracket_char_append()

        # Validation
        for c in jtr_must_escape_for_range:
            if X.matches(c):
                raise Exception("in_bracket_char_append Contruction Error")
            if not X.matches("\\"+c):
                raise Exception("in_bracket_char_append Contruction Error")

        for c in printables:
            if c not in jtr_must_escape_for_range + '"' and not X.matches(c):
                raise Exception("in_bracket_char_append Contruction Error")
        #####################################################################

        ############### Test Groups.character_classes_group() Function #########
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        X = Groups.character_classes_group()

        # Validation
        for c in CHAR_CLASSES:
            if not X.matches("?"+c):
                raise Exception("character_classes_group Contruction Error")
        #####################################################################


    def test_flags(self):
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('-:', '-8 ', '-c -s -p', '-s-c', '-<7 ->7', '-<5 ->5 -c',
                 '-<3 ->3 -c ', '->[4-9A]', '->[5-9A]', '-[:c]', '-p-[c:]', '->[5-9A]')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)


    def test_unary_cmds(self):
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = (':lucCtrdf}{][qkKEPISV',
                 ": l u c C t r d f } { ] [ q k K E P I S V")
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = (':lucCtrdf}{\]\[pqkKEPISVRL', ": l u c C t r d f } { \] \[ p q P I S V R L",
                 '\p1[lc]', ":[RL]", "[RL]", "\p[lc]", "\\r[llc]", "[}{] \\0", "\p[c:]")
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)


    def test_binary_cmds(self):

        ################## Test TN Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('T1', 'T0 T2 T4 T6 T8 TA TC TE')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('Tm', 'T0', 'T[1-9A-E]', 'T\\0',
                 'T0 T2 T4 T6 T8 TA TC TE Tm', 'T2T[z0]T[z1]')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #####################################################

        ################## Test DN Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('D1', 'D0 D2 D4 D6 D8 DA DC DE')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('Dm', 'D0', 'D[1-9A-E]', 'D\\0',
                 'D0 D2 D4 D6 D8 DA DC DE Dm', 'D2D[z0]D[z1]')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #####################################################

        ################## Test pN Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('p1', 'p0 p2 p4 p6 p8 pA pC pE')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #####################################################

        ################## Test zN Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('z1', 'z0 z2 z4 z6 z8 zA zC zE')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('zm', 'z0', 'z[1-9A-E]', 'z\\0',
                 'z0 z2 z4 z6 z8 zA zC zE zm', 'z2z[z0]z[z1]')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #####################################################

        ################## Test ZN Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('Z1', 'Z0 Z2 Z4 Z6 Z8 ZA ZC ZE')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('Zm', 'Z0', 'Z[1-9A-E]', 'Z\\0',
                 'Z0 Z2 Z4 Z6 Z8 ZA ZC ZE Zm', 'Z2Z[z0]Z[z1]')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #####################################################

        ################## Test LN Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('L1', 'L0 L2 L4 L6 L8 LA LC LE')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #####################################################

        ################## Test RN Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('R1', 'R0 R2 R4 R6 R8 RA RC RE')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #####################################################

        ################## Test +N Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('+1', '+0 +2 +4 +6 +8 +A +C +E')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('+m', '+0', '+[1-9A-E]', '+\\0',
                 '+0 +2 +4 +6 +8 +A +C +E +m', '+2+[z0]+[z1]')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #####################################################

        ################## Test -N Commands ##################
        # -N is HC only, - is flag in JtR
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('-1', '-0 -2 -4 -6 -8 -A -C -E')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #####################################################

        ################## Test .N Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('.1', '.0 .2 .4 .6 .8 .A .C .E')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('.m', '.0', '.[1-9A-E]', '.\\0',
                 '.0 .2 .4 .6 .8 .A .C .E .m', '.2.[z0].[z1]')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #####################################################

        ################## Test ,N Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = (',1', ',0 ,2 ,4 ,6 ,8 ,A ,C ,E')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = (',m', ',0', ',[1-9A-E]', ',\\0',
                 ',0 ,2 ,4 ,6 ,8 ,A ,C ,E ,m', ',2,[z0],[z1]')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #####################################################

        ################## Test YN Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('Y1', 'Y0 Y2 Y4 Y6 Y8 YA YC YE')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('Ym', 'Y0', 'Y[1-9A-E]', 'Y\\0',
                 'Y0 Y2 Y4 Y6 Y8 YA YC YE Ym', 'Y2Y[z0]Y[z1]')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #####################################################

        ################## Test yN Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('y1', ' y0 y2 y4 y6 y8 yA yC yE')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('ym', 'y0', 'y[1-9A-E]', 'y\\0',
                 'y0 y2 y4 y6 y8 yA yC yE ym', 'y2y[z0]y[z1]')
        expected_out = tuple(i.replace(" ", "") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #####################################################

        ################## Test $X Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC

        tests = ('$1', '$*$ $.$+$%$$')
        expected_out = [['$1'], ['$*', '$ ', '$.', '$+', '$%', '$$']]
        actual_out = [Elements.parser().parseString(x).asList() for x in tests]
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('$a', '$[1-9!0a-rt-z"-/:-@\[-`{-~]', '$[1-9!]', '$s',
                 '$!', '$[ _\-]', '$\p[)}\]>]', '$\\1', '$[a-z]', '$[2!37954860.?]',
                 '$[1a-z2-90]', '$[({[<]$\p[)}\]>]', '$[1!@#$%^&*\-=_+.?|:\'"]', '$\p[)}\]>]')
        expected_out = tuple(i.strip(" ") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #####################################################

        ################## Test ^X Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC

        tests = ('^1', '^* ^ ^. ^+^%^^')
        expected_out = [['^1'], ['^*', '^ ', '^.', '^+', '^%', '^^']]
        actual_out = [Elements.parser().parseString(x).asList() for x in tests]
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('^a', '^[1-9!0a-rt-z"-/:-@\[-`{-~]', '^[1-9!]', '^s',
                 '^!', '^[ _\-]', '^\p[)}\]>]', '^\\1', '^[a-z]', '^[2!37954860.?]',
                 '^[1a-z2-90]', '^[({[<]^\p[)}\]>]', '^[1!@#$%^&*\-=_+.?|:\'"]', '^\p[)}\]>]')
        expected_out = tuple(i.strip(" ") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #####################################################


    def test_ternary_cmds(self):
        ################## Test ANStr Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('Az"\'s"', 'Az"!!"', 'A0"[tT]he"', 'A0"__"', 'A0"[mdMD]r."', 'Az"[190][0-9]"', 'Az"[782][0-9]"', r'Az"[0-9]\0\0"', 'Az"20[01]"', r'A\p[z0]"[a-z][a-z]"', 'A0"[0-9][0-9][0-9] [NSEWnsew]"', r"""Az"[0-9!$@#%.^&()_+\-={}|\[\]\\;':,/\<\>?`~*]" """,
                 r"""Az"[!$@#%.^&()_+\-={}|\[\]\\;':,/\<\>?`~*][!$@#%.^&()_+\-={}|\[\]\\;':,/\<\>?`~*]" """, r"""A[0-5]"[!$@#%.^&()_+\-={}|\[\]\\;':,/\<\>?`~*]" """, r"""A[9]"[!$@#%.^&()_+\-={}|\[\]\\;':,/\<\>?`~*]"Az"[0-9][0-9]" """)
        expected_out = tuple(i.strip(" ").replace("\"", "")
                             for i in tests)  # suppress " during parsing
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #########################################################

        ################## Test xNM Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = (' x**', r'x1\1 ',
                 r'x2\p[2-8] ', 'x3\p[2-7] ', r'x1\1', ' x58x63 ', 'x05x57 ', 'x30')
        expected_out = tuple(i.strip(" ") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = (' x58x63 ', 'x05x57 ', 'x30')
        expected_out = tuple(i.strip(" ") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        ######################################################

        ################## Test *NM Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = (' *58*63 ', '*05*57 ', '*30')
        expected_out = tuple(i.strip(" ") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        ######################################################

        ################## Test ONM Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = (' O**', r'O1\1 ',
                 r'O2\p[2-8] ', 'O3\p[2-7] ', r'O1\1', ' O58O63 ', 'O05x57 ', 'O30')
        expected_out = tuple(i.strip(" ") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = (' O58O63 ', 'O05O57 ', 'O30', 'O26')
        expected_out = tuple(i.strip(" ") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        ######################################################

        ################## Test iNX Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = (' i[12].', r'i\0[a-z] ', 'i0q ', r"""i\p2[6-9][0-9a-zA-Z!$ @#%.^&()_+\-={}|[\]\\;'":,/<>?`~*]""",
                 r""" i[0-5][0-9a-zA-Z!$ @#%.^&()_+\-={}|[\]\\;'":,/<>?`~*] """, ' i7( ', 'i7 i0-')
        expected_out = tuple(i.strip(" ") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = (' i7( ', 'i7 i0-', 'i0q')
        expected_out = tuple(i.strip(" ") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        ######################################################

        ################## Test iNX Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = (' i[12].', r'i\0[a-z] ', 'i0q ', r"""i\p2[6-9][0-9a-zA-Z!$ @#%.^&()_+\-={}|[\]\\;'":,/<>?`~*]""",
                 r""" i[0-5][0-9a-zA-Z!$ @#%.^&()_+\-={}|[\]\\;'":,/<>?`~*] """, ' i7( ', 'i7 i0-')
        expected_out = tuple(i.strip(" ") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = (' i7( ', 'i7 i0-', 'i0q')
        expected_out = tuple(i.strip(" ") for i in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        ######################################################

        ################## Test oNX Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = (' o[12].', r'o\0[a-z] ', 'o0q ', r"""o\p2[6-9][0-9a-zA-Z!$ @#%.^&()_+\-={}|[\]\\;'":,/<>?`~*]""",
                 r""" o[0-5][0-9a-zA-Z!$ @#%.^&()_+\-={}|[\]\\;'":,/<>?`~*] """, ' o7( ', 'o7 o0-')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = (' o7( ', 'o7 o0-', 'o0q')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        ######################################################


    def test_memory_cmds(self):
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = (' M ', 'MQ ', ' MQ', 'Xpz0', 'X0z0',
                 ' Xpz0 ', 'X428', 'val1', ' X428 ', ' val1')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = (' M6 ', 'MQ4 ', ' MQ4', ' 46M', '4', '6',
                 'M', 'Q', '4 ', 'M ', ' Q', 'X428', ' X428 ')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)


    def test_mode_cmds(self):
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('1', '2', '+', ' + 1 2 ')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple(" ".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)


    def test_length_rejection_cmds(self):
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('>2', '>[2-8]', '>[8-9A-E]', '>[1-9A-E]', '>-', r'>\r[00123456789]', '>A', '>*', '>\p[3-9]'
                 '<2', '<[2-8]', '<[8-9A-E]', '<[1-9A-E]', '<-', r'<\r[00123456789]', '<A', '<*', '<\p[3-9]'
                 '_2', '_[2-8]', '_[8-9A-E]', '_[1-9A-E]', '_-', r'_\r[00123456789]', '_A', '_*', '_\p[3-9]')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('>2', '>A', '<2', '<A', '_A', '_2')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)


    def test_char_class_cmds(self):
        ################## Test !X !?C Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('!?A', '!?a', '!?X', '!?x', '!?v', '!?V', '!?l', '!?L', '!?u', '!?U', '!?p', '!??', '!?w', '!?d', '!?D'
                 '!a', '!e', '!i', '!o', '!u', '!I', '!W', '!E', '!C', '!A', '!0', '!@', '!$', r'!\\', '!;', '!;', '!<')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('!a', '!e', '!i', '!o', '!u', '!I', '!W', '!E', '!C',
                 '!A', '!0', '!@', '!$', '!\\', '!;', '!;', '!<')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #########################################################

        ################## Test /X /?C Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('/?A', '/?a', '/?X', '/?x', '/?v', '/?V', '/?l', '/?L', '/?u', '/?U', '/?p', '/??', '/?w', '/?d', '/?D'
                 '/a', '/e', '/i', '/o', '/u', '/I', '/W', '/E', '/C', '/A', '/0', '/@', '/$', r'/\\', '/;', '/;', '/<')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('/a', '/e', '/i', '/o', '/u', '/I', '/W', '/E', '/C',
                 '/A', '/0', '/@', '/$', '/\\', '/;', '/;', '/<')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #########################################################

        ################## Test )X )?C Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = (')?A', ')?a', ')?X', ')?x', ')?v', ')?V', ')?l', ')?L', ')?u', ')?U', ')?p', ')??', ')?w', ')?d', ')?D'
                 ')a', ')e', ')i', ')o', ')u', ')I', ')W', ')E', ')C', ')A', ')0', ')@', ')$', r')\\', ');', ');', ')<')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = (')a', ')e', ')i', ')o', ')u', ')I', ')W', ')E', ')C',
                 ')A', ')0', ')@', ')$', ')\\', ');', ');', ')<')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #########################################################

        ################## Test (X (?C Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('(?A', '(?a', '(?X', '(?x', '(?v', '(?V', '(?l', '(?L', '(?u', '(?U', '(?p', '(??', '(?w', '(?d', '(?D'
                 '(a', '(e', '(i', '(o', '(u', '(I', '(W', '(E', '(C', '(A', '(0', '(@', '($', r'(\\', '(;', '(;', '(<')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('(a', '(e', '(i', '(o', '(u', '(I', '(W', '(E', '(C',
                 '(A', '(0', '(@', '($', '(\\', '(;', '(;', '(<')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #########################################################

        ################## Test eX e?C Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('e?A', 'e?a', 'e?X', 'e?x', 'e?v', 'e?V', 'e?l', 'e?L', 'e?u', 'e?U', 'e?p', 'e??', 'e?w', 'e?d', 'e?D'
                 'ea', 'ee', 'ei', 'eo', 'eu', 'eI', 'eW', 'eE', 'eC', 'eA', 'e0', 'e@', 'e$', r'e\\', 'e;', 'e;', 'e<')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('ea', 'ee', 'ei', 'eo', 'eu', 'eI', 'eW', 'eE', 'eC',
                 'eA', 'e0', 'e@', 'e$', 'e\\', 'e;', 'e;', 'e<')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #########################################################

        ################## Test @X @?C Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('@?A', '@?a', '@?X', '@?x', '@?v', '@?V', '@?l', '@?L', '@?u', '@?U', '@?p', '@??', '@?w', '@?d', '@?D'
                 '@a', '@e', '@i', '@o', '@u', '@I', '@W', '@E', '@C', '@A', '@0', '@@', '@$', r'@\\', '@;', '@;', '@<')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('@a', '@e', '@i', '@o', '@u', '@I', '@W', '@E', '@C',
                 '@A', '@0', '@@', '@$', '@\\', '@;', '@;', '@<')
        expected_out = tuple(x.strip(" ") for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        #########################################################

        ################## Test %NX %N?C Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('%2?a', '%9 ', '%1?a', '%1??', '%2?A', '%2?d', r'%2c')
        expected_out = tuple(x for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('%9 ', r'%2c')
        expected_out = tuple(x for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        ############################################################

        ################## Test =NX =N?C Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('=2?a', '=9 ', '=1?a', '=1??', '=2?A', '=2?d', r'=2c')
        expected_out = tuple(x for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('=9 ', r'=2c')
        expected_out = tuple(x for x in tests)
        actual_out = tuple("".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        ############################################################

        ################## Test sXY, s?CY Commands ##################
        RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
        tests = ('s???', 's?za', 's?d0', 's?aA', 'sa4 se3 sl1 so0 ss$', 'se3 sl1 so0 ss$',
                 's8B s0O', r's/\\', 's/\'', r's>\\', 's<"', 's3# s8*', 'sI1', 's _')
        expected_out = tuple(x for x in tests)
        actual_out = tuple(" ".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)

        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = ('sa4 se3 sl1 so0 ss$', 'se3 sl1 so0 ss$', 's8B s0O', 's/\\', 's/\'', 's>\\',
                 's<"', 's3# s8*', 'sI1', 's _')
        expected_out = tuple(x for x in tests)
        actual_out = tuple(" ".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        ############################################################

    def test_p_rules(self):
        RUNTIME_CONFIG['running_style'] = RunningStyle.HC
        tests = (r'%2s Tp', r'%2s Dp', r'%2s xp4', r'%2s Op2', r'%2s ip!', r'%2s op$',
                 r"%2s 'p", r'%2s l M Xp28', r'%2s Lp', r'%2s Rp', r'%2s *p4',
                 r'%2s +p', r'%2s -p', r'%2s ,p', r'%2s .p',)
        expected_out = tuple(x for x in tests)
        actual_out = tuple(" ".join(i) for i in (
            Elements.parser().parseString(x).asList() for x in tests))
        self.assertEqual(actual_out, expected_out)
        


    def test_rule_files(self):
        try:
            RUNTIME_CONFIG['running_style'] = RunningStyle.JTR
            RulelistReader.read_and_parse_rule_list(
                "test_parsing_JtR.rule", safe_mode=False)
            RulelistReader.read_and_parse_rule_list(
                "john.rule", safe_mode=False)
            RulelistReader.read_and_parse_rule_list(
                "spiderkorelogic.rule", safe_mode=False)
            RulelistReader.read_and_parse_rule_list(
                "megatron.rule", safe_mode=False)

            RUNTIME_CONFIG['running_style'] = RunningStyle.HC
            RulelistReader.read_and_parse_rule_list(
                "test_parsing_HC.rule", safe_mode=False)
            RulelistReader.read_and_parse_rule_list(
                "best64.rule", safe_mode=False)
            RulelistReader.read_and_parse_rule_list(
                "T0XlC.rule", safe_mode=False)
            RulelistReader.read_and_parse_rule_list(
                "generated2.rule", safe_mode=False)
        except:
            raise


if __name__ == "__main__":
    # Run Unit Test
    rule_suite = unittest.TestLoader().loadTestsFromTestCase(ParseTest)
    rule_runner = unittest.TextTestRunner()
    rule_runner.run(rule_suite)

"""This file contains a parser to parse rules"""
from collections import OrderedDict
from config import RUNTIME_CONFIG
from copy import deepcopy
from common import FatalRuntimeError, RunningStyle
from enum import Enum
from invert_helper import CHAR_CLASSES
from pyparsing import Word, nums, alphas, alphanums, ZeroOrMore
from pyparsing import Literal, Suppress, srange, Group, QuotedString
from pyparsing import printables, WordEnd, Combine, OneOrMore, White
from pyparsing import MatchFirst, StringEnd, Empty
import os
""" Some char definitions

Reference:
1. https://www.openwall.com/john/doc/RULES.shtml
2. https://hashcat.net/wiki/doku.php?id=rule_based_attack
"""

jtr_numeric_constants = srange("[a-kA-Z0-9]") + "lmpz*-+"
# chars that can be used to denote a range. 1-3, A-Z.
jtr_numeric_constants_dash_allowed = srange("[A-Z0-9]")
jtr_escaped_chars = "-<>[]\\"
jtr_must_escape_for_single_char = "[\\"
jtr_must_escape_for_range = "]"
jtr_could_escape_for_single_char = "".join(
    x for x in jtr_escaped_chars if x not in jtr_must_escape_for_single_char)

hc_numeric_constants = srange("[A-Z0-9p]")


class RuleWrapper():
    """A wrapper class for a rule. A rule normally occupies a line in a rulelist file.

    Attr:
        raw: the raw rule string (read from file)
        
        tokenized: tokenized rule, will be further processed.

        rules: fully parsed, unparalleled and tokenized subrules.
    """

    @staticmethod
    def _process_group(group):
        """ Process a group

        The definition of a group is either a \prefix + bracket or a literal
        1. Escape chars in a bracket
        2. Tokenize everything.
        3. Convert range into tuples.
        """
        # If the group is (\p\r\p#)[something]
        if group.startswith("\\p") or group.startswith("\\r"):

            tokens = []
            prefix = ""  # capture the \p,\r prefix and remove it from string.
            while group.startswith("\\p") or group.startswith("\\r"):
                # "\p#"
                if group[2] in "0123456789":
                    prefix += group[:3]
                    group = group[3:]
                else:  # "\r" or "\p"
                    prefix += group[:2]
                    group = group[2:]

            # add prefix
            tokens.append(prefix)

            # Remove the bracket from string
            group = group[1:-1]
            # First, eliminate escape except \\-
            i = 0
            tmpgroup = ""
            while i <= len(group) - 1:
                if group[i] == "\\" and group[i + 1] != "-":
                    tmpgroup += group[i + 1]
                    i = i + 2
                else:
                    tmpgroup += group[i]
                    i = i + 1
            group = tmpgroup
            letters = []
            i = 0

            # here every escaped char is transformed except '-'
            # we then transform a range into each single chars in order
            while i <= len(group) - 1:
                if i == len(group) - 1:  # Last char, add.
                    letters.append(group[i])
                    i = i + 1

                # A true range (not \\-)
                elif group[i + 1] == '-' and i + 2 <= len(
                        group) - 1 and group[i] != "\\":

                    ascii_start = ord(
                        group[i]) if ord(group[i]) < ord(group[i + 2]) else ord(
                            group[i + 2])
                    ascii_end = ord(group[i + 2]) if ord(group[i]) < ord(
                        group[i + 2]) else ord(group[i])

                    for letter in range(ascii_start,
                                        ascii_end + 1):  # Create the range
                        letters.append(chr(letter))

                    i = i + 3  # Skip the rest

                else:
                    # If escape
                    if (group[i] == "\\" and group[i + 1] == "-"):  # \\- escape
                        letters.append(group[i + 1])
                        i = i + 2

                    else:  # Otherwise add single
                        letters.append(group[i])
                        i = i + 1
            tokens.append(tuple(letters))
            return tokens

        # If the group is just [something]
        elif group.startswith("[") and group.endswith("]"):

            # Remove bracket
            group = group[1:-1]

            # First, eliminate escape except \\-
            i = 0
            tmpgroup = ""
            while (i <= len(group) - 1):
                if (group[i] == "\\" and group[i + 1] != "-"):
                    tmpgroup += group[i + 1]
                    i = i + 2
                else:
                    tmpgroup += group[i]
                    i = i + 1

            group = tmpgroup

            letters = []
            i = 0
            while i <= len(group) - 1:
                if i == len(group) - 1:
                    letters.append(group[i])
                    i = i + 1

                elif group[i + 1] == '-' and i + 2 <= len(
                        group) - 1 and group[i] != "\\":
                    ascii_start = ord(
                        group[i]) if ord(group[i]) < ord(group[i + 2]) else ord(
                            group[i + 2])
                    ascii_end = ord(group[i + 2]) if ord(group[i]) < ord(
                        group[i + 2]) else ord(group[i])

                    # Create range
                    for letter in range(ascii_start,
                                        ascii_end + 1):  # Create the range
                        letters.append(chr(letter))  # Add
                    i = i + 3

                else:
                    # Escape
                    if group[i] == "\\" and group[i + 1] == "-":  # \\ escape
                        letters.append(group[i + 1])
                        i = i + 2
                    # Otherwise add
                    else:
                        letters.append(group[i])
                        i = i + 1

            return tuple(letters)

        else:
            # Literals, tokenize them
            tokens = [g for g in group]

            if len(tokens) == 1:  # No need for [] if len = 1
                tokens = tokens[0]

            return tokens

    def __init__(self, raw, tokenized):
        """Create a parsed rule 

        Feed in a raw string (read from file) and a parsed string (a list of strings).
        Further process the parsed string and save raw string for debug and other purposes.
        
        Args:
            raw: the raw rule string (read from file)
            tokenized: tokenized rule, will be further processed.
        """
        self.raw = raw
        self.tokenized = tokenized
        self._process_rule()

    def __repr__(self):
        return "Raw: {}\nSubrules:{}\nNumber of Subrules:{}\n".format(
            self.raw, self.rules, len(self.rules))

    def _process_rule(self):
        """ Given a tokenized rule, further process it.

        Things done in this function:
        1. detect ranges and replace \# with \number
        2. Replace escaped chars with real chars (\[ -> [), 
            tokenize all the rules. Detect \r and note it. 
            change a bracket range to tuple. [3-4] -> tuple(3,4)
        3. Determine what parallel type it is.
        4. Unparallelize rules if necessary, and also convert tuples to sets for fast look-ups.
        """
        if RUNTIME_CONFIG.is_jtr():

            # Step 1: detect ranges and replace \# with \number
            previous_ranges = []  # save all prev ranges

            # now a single rule is still a string
            for idx, single_rule in enumerate(self.tokenized):

                new_single_rule = ""
                # Pad the string for operation
                padded_single_rule = chr(1) + single_rule + chr(1)

                i = 0  # for iterating padded_single_rule
                while i < len(padded_single_rule):
                    # skip the padded part.
                    if padded_single_rule[i] == chr(1):
                        i += 1
                        continue

                    # Case 1, it is now \#.
                    # Replace with it \p#[]
                    if padded_single_rule[i] == "\\" and padded_single_rule[
                            i + 1] in "0123456789":

                        p_num = int(padded_single_rule[i + 1])

                        if p_num == 0:  # if this number = 0, means immediate previous range
                            the_range = previous_ranges[-1]
                        else:
                            # back reference to previous ranges (num-1), list indexing ranges from 0
                            the_range = previous_ranges[p_num - 1]

                        # convert \# to \p#[]
                        p_str = "\p" + padded_single_rule[i + 1] + the_range

                        # construct new single_rule
                        new_single_rule += p_str  # Add newly constructed \# with \p#[]

                        # Also add this range to previous range
                        previous_ranges.append(the_range)

                        i = i + 2  # skip \#.

                    # Detect pure ranges and save it.
                    # Start of a range
                    elif padded_single_rule[i] == "[" and padded_single_rule[
                            i - 1] != "\\":

                        # capturing the range
                        j = i
                        # Not the end ]
                        while not (padded_single_rule[j] == "]" and
                                   padded_single_rule[j - 1] != "\\"):
                            j += 1

                        the_range = padded_single_rule[i:j + 1]  # Get the range
                        previous_ranges.append(the_range)  # Save
                        new_single_rule += the_range  # Construct new_single_new
                        i = j + 1  # skip what's added

                    # Escaped chars
                    elif padded_single_rule[i] == "\\" and padded_single_rule[
                            i + 1] in "\<>[]-":
                        # add to new_single_rule
                        new_single_rule += padded_single_rule[i:i + 2]
                        i = i + 2

                    else:
                        # add to new_single_rule
                        new_single_rule += padded_single_rule[i]
                        i = i + 1

                self.tokenized[idx] = new_single_rule
                # Step 1 End here

            # Step 2
            # Replace escaped chars with real chars (\[ -> [), tokenize all the rules. Detect \r and note it
            # Alao change a bracket range to tuple. [3-4] -> tuple(3,4)
            new_tokenize = []
            all_groups = []  # all groups of all transformations.

            for single_rule in self.tokenized:
                # Pad the string for operation
                padded_single_rule = chr(1) + single_rule + chr(1)
                # all groups of a single transformation (one single rule like ANStr).
                groups_of_a_trans = []

                # Below we're detecting groups
                # A group is either a literal not in a bracket or everything in a bracket.
                i = 0
                while i < len(padded_single_rule):

                    if padded_single_rule[i] == chr(1):
                        i += 1
                        continue

                    # A Range with \p or \r or \p#, capture the entire range
                    if (padded_single_rule[i] == "\\" and padded_single_rule[i + 1] == "p") or\
                       (padded_single_rule[i] == "\\" and padded_single_rule[i + 1] == "r") or\
                       (padded_single_rule[i] == "\\" and padded_single_rule[i + 1] == "p" and padded_single_rule[i + 2] in "0123456789"):

                        # capture the whole range
                        j = i
                        # Not the end ]
                        while not (padded_single_rule[j] == "]" and
                                   padded_single_rule[j - 1] != "\\"):
                            j += 1

                        groups_of_a_trans.append(padded_single_rule[i:j + 1])
                        i = j + 1

                    # A Range without prefix (\p, \r, \p#)
                    # Just a range with no \p preceding.
                    elif padded_single_rule[i] == "[" and padded_single_rule[
                            i - 1] != "\\":
                        # capture the whole range
                        j = i
                        # Not the end ]
                        while not (padded_single_rule[j] == "]" and
                                   padded_single_rule[j - 1] != "\\"):
                            j += 1

                        groups_of_a_trans.append(padded_single_rule[i:j + 1])
                        i = j + 1

                    else:  # Literal

                        # If the litral is escape
                        if padded_single_rule[i] == "\\":
                            groups_of_a_trans.append(padded_single_rule[i + 1])
                            i = i + 2
                        else:
                            groups_of_a_trans.append(
                                padded_single_rule[i])  # else append itself
                            i = i + 1

                all_groups.append(groups_of_a_trans)

            # For each group transform into tokens
            self.tokenized = [[
                RuleWrapper._process_group(group) for group in groups_of_a_trans
            ] for groups_of_a_trans in all_groups]
            # After tokenization, each component in a transformation can only be list/tuple/str.
            # And lists are in the form of [\p, tuple]
            #### Major Process For JtR Done ####

        # Step 3. Determine what parallel type it is.
        self.detect_parallelism()

        # Step 4. Unparallellize rules if necessary, and also convert tuples to sets for fast look-ups.
        self.get_subrules()

    @staticmethod
    def create_component_for_current_rule(sub_rules):
        """ Append empty component for each sub_rule.

        Used to break rules into sub rules, as we need to append the list for current single command
        """
        if (sub_rules == [[]]):
            sub_rules[0].append([])
        else:
            for sub_rule_idx in range(len(sub_rules)):
                # For each line of sub_rules, append it
                sub_rules[sub_rule_idx].append([])

        return sub_rules

    @staticmethod
    def replicate_rules(rules, times):
        """Replicate the rules for some times 

        Replicate the first rule # of times, then second rule, then third
        """
        ret_val = []

        for rule in rules:
            for _ in range(times):
                copy_rule = deepcopy(rule)
                ret_val.append(copy_rule)

        return ret_val

    @staticmethod
    def append_directly(sub_rules, the_thing):
        """Append a string to the current single rule (which is a list)"""

        for sub_rules_idx in range(len(sub_rules)):
            # This thing is line of rules, the last [] is for current single rule
            sub_rules[sub_rules_idx][-1].append(the_thing)

        return sub_rules

    @staticmethod
    def append_full_parallel(sub_rules, the_list):
        """ Expand Pure Parallel.

        The way we expand this is copy the first line of subrules, double it
        multiple times, then copy the second line, etc.
        """
        sub_rules = RuleWrapper.replicate_rules(
            sub_rules,
            len(the_list))  # replicate previous sub_rules len(the_set) times

        for sub_rules_idx in range(len(sub_rules)):
            sub_rules[sub_rules_idx][-1].append(
                the_list[sub_rules_idx % len(the_list)])

        return sub_rules

    @staticmethod
    def append_slash_parallel(sub_rules, comp, is_expanded_by_parallelism):
        r""" Expand \p and \r [something].

        If the previous range specified in p# is expanded by some pure parallel, then
        we need to feed this range in a certain way (l l c c). Otherwise in another way (l c l c).
        """
        if len(
                comp
        ) != 2:  # List len error? it can only be something like [\p1, tuple()]
            raise FatalRuntimeError("Sorry List Length Error")

        else:
            parallel_preifx = comp[0]

            # Detect Command
            if parallel_preifx.startswith(
                    "\\p") != True and parallel_preifx.startswith(
                        "\\r") != True:
                # only be something like [\p1, tuple()]
                raise FatalRuntimeError(
                    "Sorry Parrallel Command is not \p or \\r")

            if type(comp[1]) is not tuple or len(comp) != 2:  # Detect Type
                # only be something like [\p1, set()]
                raise FatalRuntimeError("Sorry Comp Type Error")

            if parallel_preifx == "\\r":  # \r only, it is actually pure parallel.
                the_tuple = comp[1]
                return RuleWrapper.append_full_parallel(sub_rules, the_tuple)

            parallel_preifx = parallel_preifx.replace("\\r",
                                                      "")  # get rid of \r
            if parallel_preifx == "\\p":  # \p
                the_tuple = comp[1]
                for sub_rules_idx in range(len(sub_rules)):
                    sub_rules[sub_rules_idx][-1].append(
                        the_tuple[sub_rules_idx % len(the_tuple)])
                    # Put it one by one

            elif parallel_preifx.startswith("\\p"):  # \p number
                # Get the number it parallels with
                parrallel_with = int(parallel_preifx[2])

                # The previous is not expanded
                if is_expanded_by_parallelism[parrallel_with - 1] == False:
                    the_tuple = comp[1]
                    for sub_rules_idx in range(len(sub_rules)):
                        sub_rules[sub_rules_idx][-1].append(
                            the_tuple[sub_rules_idx % len(the_tuple)])

                else:  # The previous is expanded
                    the_tuple = comp[1]
                    each_rule_length = len(sub_rules) / len(the_tuple)
                    for sub_rules_idx in range(len(sub_rules)):  # size = 8
                        # Could overflow here
                        sub_rules[sub_rules_idx][-1].append(the_tuple[int(
                            sub_rules_idx / each_rule_length)])

            return sub_rules

    def get_subrules(self):
        """ Create Subrules

        1. We expand all tuples based on specification. 
        If the tuple is the parameter str in ANStr or X in iNX/$X/^X, not expanded.
        
        2. Transform tuples into sets for fast look-ups.
        """

        if self.is_parallel == False:  # Just return what we have
            # Transform tuples into sets.
            for i, transformation in enumerate(self.tokenized):
                for c, comp in enumerate(transformation):
                    if type(comp) is tuple:
                        transformation[c] = set(comp)
                    if type(comp) is list:
                        raise FatalRuntimeError(
                            "Parallel Type Error for {}".format(self.raw))
                self.tokenized[i] = transformation
                self.rules = [deepcopy(self.tokenized)]  # just this one rule

        else:  # Otherwise break it.

            sub_rules = [[]]  # Start with a line of rules
            # Indicate the way it is organized, True: :, :, c, c. False: :, c, :, c
            is_expanded_by_parallelism = []

            for transformation in self.tokenized:

                sub_rules = RuleWrapper.create_component_for_current_rule(
                    sub_rules)  # Initialize component for current single_rule

                for i, comp in enumerate(transformation):

                    if type(
                            comp
                    ) is str:  # The current comp of the single_rule is str, just append it
                        sub_rules = RuleWrapper.append_directly(sub_rules, comp)

                    # The current comp of the single_rule is tuple, pure parallel, double the size
                    # Unless it is str in ANstr or X in iNX/$X/^X.
                    elif (type(comp) is tuple):
                        # don't expand, just append comp to every sub_rule.
                        if (i >= 2 and transformation[0] in "Ai") or (
                                i == 1 and transformation[0] in "$^"):
                            sub_rules = RuleWrapper.append_directly(
                                sub_rules, set(comp))

                        else:
                            # Reconstruct as the previous ranges are all expanded
                            is_expanded_by_parallelism = [
                                True for _ in is_expanded_by_parallelism
                            ]
                            is_expanded_by_parallelism.append(False)

                            sub_rules = RuleWrapper.append_full_parallel(
                                sub_rules, comp)

                    # In parallel with something (i.e. \p), add but dont change the size
                    elif type(comp) is list:
                        is_expanded_by_parallelism.append(False)

                        sub_rules = RuleWrapper.append_slash_parallel(
                            sub_rules, comp, is_expanded_by_parallelism)

            self.rules = sub_rules

    def detect_parallelism(self):
        """ Detect parallel type

        The component in a transformation right now can only be 3 types:
        1. str
        2. tuple
        3. list, normally in the form of [\p, tuple]
        
        Set is_parallel to True if there is a tuple. The only exception is when there is a tuple, but the tuple is the parameter str in ANStr or X in iNX.
        We don't expand in this exception for efficiency reasons.
        """
        self.is_parallel = False

        for transformation in self.tokenized:
            for i, comp in enumerate(transformation):
                if type(comp) == str:
                    continue
                if type(comp) == list:
                    for c in comp:
                        if type(c) == tuple:
                            self.is_parallel = True
                if type(comp) == tuple and not (i >= 2 and
                                                transformation[0] in "Ai"):
                    self.is_parallel = True


class RulelistReader():
    """ A wrapper class that reads a rule list file, parses it and returns the list."""

    @staticmethod
    def _read_raw_rules_from_file(rules_dir, filename):
        """ Read rules from file line by line, skip lines starting with "#" and "[List.", no parsing

        Specify a rules_dir and a filename, full_path = {rules_dir}/{filename}. full_path should exist.

        Args:
            rules_dir: directory where the file is stored
            filename: filename of the rule
        """
        full_path = '{}/{}'.format(rules_dir, filename)

        if not os.path.isfile(full_path):
            raise FatalRuntimeError(
                "Rule List Address :{} Doesn't Exists! ".format(full_path))

        with open(full_path, 'r') as infile:
            rules = infile.read().splitlines()
            return [
                rule.strip("\r\n")
                for rule in rules
                if rule and not rule.startswith(("#", '[List.'))
            ]

    @staticmethod
    def read_and_parse_rule_list(filename,
                                 rules_dir="../data/rulelists/",
                                 safe_mode=True):
        """ Read rules from file, and parse it.

        Args:
            filename: filename of the rule
            rules_dir: directory where the file is stored
            safe_mode: ignore errors or not.
        """

        parser = Elements.parser()

        raw_rules = RulelistReader._read_raw_rules_from_file(
            rules_dir, filename)

        parsed_rules = []

        for rule in raw_rules:
            try:
                parsed_rules.append(
                    RuleWrapper(rule,
                                parser.parseString(rule).asList()))
            except:
                if safe_mode == True:
                    print("Parsing rule: {} failed, discarded".format(rule))
                else:
                    print("Parsing rule: {} failed".format(rule))
                    raise
        return parsed_rules


def jtr_only_func(func):
    """Decorator to check that the current program is running on JTR mode"""

    def wrapper(*args, **kwargs):
        if RUNTIME_CONFIG['running_style'] != RunningStyle.JTR:
            raise FatalRuntimeError(
                "Should Not Enter {} Function in non-JTR Mode".format(
                    func.__name__))
        return func(*args, **kwargs)

    return wrapper


class Groups():
    """ Helper class to parse rules

    These are not rule elements. These are constants that are used rule elements.
    Constant groups et cetera
    """

    @staticmethod
    def single_position():
        """ Single position N.

        0...9   for 0...9
        A...Z   for 10...35
        *   for max_length
        -   for (max_length - 1)
        +   for (max_length + 1)
        a...k   user-defined numeric variables (with the "v" command)
        l   initial or updated word's length (updated whenever "v" is used)
        m   initial or memorized word's last character position
        p   position of the character last found with the "/" or "%" commands
        z   "infinite" position or length (beyond end of word)
        """

        if RUNTIME_CONFIG.is_jtr():
            return Word(jtr_numeric_constants, exact=1)
        elif RUNTIME_CONFIG.is_hc():
            return Word(hc_numeric_constants, exact=1)
        else:
            raise FatalRuntimeError(
                "Unknown RUNTIME_CONFIG['running_style'] Type: {}".format(
                    RUNTIME_CONFIG['running_style']))

    @staticmethod
    @jtr_only_func
    def in_bracket_position():
        """ Valid positions that can appear in [], only valid in JtR mode

        Example:
        A[1-3A-B]"ab"
        """

        # the chars that must be escaped in a range. "-" is valid position in JtR.
        must_escaped_chars = "-"

        # first, purge all must_escaped_chars from
        purged = jtr_numeric_constants
        for c in must_escaped_chars:
            purged = purged.replace(c, "")

        # next, add the escaped version
        valid_singles = Word(purged, exact=1)
        for c in must_escaped_chars:
            valid_singles = Literal("\\" + c) | valid_singles

        # valid position ranges using a dash: A-Z, 0-9
        valid_ranges = Word(jtr_numeric_constants_dash_allowed, exact=1) + \
            Literal("-") + Word(jtr_numeric_constants_dash_allowed, exact=1)
        return valid_ranges | valid_singles

    @staticmethod
    def positions_in_bracket():
        """ add [] to valid in_bracket_position"""
        # combine both
        return Elements._add_brackets(Groups.in_bracket_position())

    @staticmethod
    def single_char():
        """ Valid single char X"""
        initial_chars = printables

        # Additional requirements for JTR.
        if RUNTIME_CONFIG.is_jtr():

            # purge the must escape chars
            for c in jtr_must_escape_for_single_char:
                initial_chars = initial_chars.replace(c, "")

            escaped_valid_chars = Word(initial_chars, exact=1)
            # escape must escape chars.
            for c in jtr_must_escape_for_single_char:
                escaped_valid_chars = Literal("\\" + c) | escaped_valid_chars

            # add could escape chars.
            for c in jtr_could_escape_for_single_char:
                escaped_valid_chars = Literal("\\" + c) | escaped_valid_chars

        else:
            escaped_valid_chars = Word(initial_chars, exact=1)

        # Consider space
        return escaped_valid_chars | White(" ", max=1)

    @staticmethod
    def single_char_for_char_class():
        """ Valid single char X that considers character class"""
        initial_chars = printables
        if RUNTIME_CONFIG.is_jtr():
            for c in "?" + jtr_must_escape_for_single_char:
                initial_chars = initial_chars.replace(c, "")

            valid_single_char = Word(initial_chars, exact=1)

            for c in jtr_must_escape_for_single_char:
                valid_single_char = Literal("\\" + c) | valid_single_char

        else:
            valid_single_char = Word(initial_chars, exact=1)

        # Consider space
        valid_single_char = valid_single_char | White(" ", max=1)
        return valid_single_char

    @staticmethod
    def range_char_for_char_class():
        """ Valid range char [X] that considers character class"""
        initial_chars = printables
        if RUNTIME_CONFIG.is_jtr():
            for c in "?" + jtr_must_escape_for_range:
                initial_chars = initial_chars.replace(c, "")

            valid_in_bracket_char = Word(initial_chars, exact=1)

            for c in jtr_must_escape_for_range:
                valid_in_bracket_char = Literal("\\" +
                                                c) | valid_in_bracket_char

        else:
            valid_in_bracket_char = Word(initial_chars, exact=1)

        # Consider space
        valid_in_bracket_char = valid_in_bracket_char | White(" ", max=1)
        return valid_in_bracket_char

    @staticmethod
    def range_char_for_char_class_in_bracket():
        """ add brackets (aka add '[]') to a group of chars """
        return Elements._add_brackets(Groups.range_char_for_char_class())

    @staticmethod
    def single_class():
        """ character class """
        return Word(CHAR_CLASSES, exact=1)

    @staticmethod
    def class_range():
        """ character class in range"""
        return Groups.single_class()

    @staticmethod
    def class_range_in_bracket():
        """ character class in range with parallel"""
        return Elements._add_brackets(Groups.class_range())

    @staticmethod
    @jtr_only_func
    def in_bracket_char():
        """ A range of chars that can appear in [], only valid in JtR

        To parse a range, not like single_char, we don't parse chars separately, we read the range as a whole.
        At this stage you just need to capture [], that's it.
        So it should be Literal("[") + allchar(replace"]") + Literal("]")
        """

        # Escape ]
        initial_chars = printables
        for c in jtr_must_escape_for_range:
            initial_chars = initial_chars.replace(c, "")

        valid_in_bracket_char = Word(initial_chars, exact=1)
        for c in jtr_must_escape_for_range:
            valid_in_bracket_char = Literal("\\" + c) | valid_in_bracket_char

        # Consider space
        valid_in_bracket_char = valid_in_bracket_char | White(" ", max=1)
        return valid_in_bracket_char

    @staticmethod
    @jtr_only_func
    def chars_in_bracket():
        r""" add [] to valid in_bracket_char """
        return Elements._add_brackets(Groups.in_bracket_char())

    @staticmethod
    def single_char_append():
        """ Valid single char X in Az"", only valid in JtR """

        # Remove " from chars
        initial_chars = printables.replace('"', "")

        # Escape [ AND \
        for c in jtr_must_escape_for_single_char:
            initial_chars = initial_chars.replace(c, "")

        escaped_valid_chars = Word(initial_chars, exact=1)
        for c in jtr_must_escape_for_single_char:
            escaped_valid_chars = Literal("\\" + c) | escaped_valid_chars

        for c in jtr_could_escape_for_single_char:
            escaped_valid_chars = Literal("\\" + c) | escaped_valid_chars

        # Consider space
        escaped_valid_chars = escaped_valid_chars | White(" ", max=1)
        return escaped_valid_chars

    @staticmethod
    @jtr_only_func
    def in_bracket_char_append():
        """ A range that appears in Az"[]", The difference is " is not allowed

        To parse a range, not like single_char, we don't parse chars seperately, we read the range as a whole.
        """

        # Note: Remove " from strings, its illegal to have it in quotes
        initial_chars = printables.replace('"', "")

        for c in jtr_must_escape_for_range:
            initial_chars = initial_chars.replace(c, "")

        valid_single_char = Word(initial_chars, exact=1)
        for c in jtr_must_escape_for_range:
            valid_single_char = Literal("\\" + c) | valid_single_char

        # Consider space
        valid_single_char = valid_single_char | White(" ", max=1)
        return valid_single_char

    @staticmethod
    @jtr_only_func
    def chars_append_in_bracket():
        r""" add [] to valid in_bracket_char_append """
        return Elements._add_brackets(Groups.in_bracket_char_append())

    @staticmethod
    def get_all_possible(char_type):
        """ Get all possible chars/positions. Specify what type do you want.

        If type == JtR, need to consider ranges and parallelism.
        """
        if char_type == "char":
            all_values = Groups.single_char()
            if RUNTIME_CONFIG.is_jtr():
                in_bracket_char = Groups.chars_in_bracket()
                slash_p_range_char = Elements._create_slash_parallel_cmds(
                    in_bracket_char)
                slash_number = Elements._create_slash_number_cmds()
                all_values = slash_number | slash_p_range_char | in_bracket_char | all_values

        elif char_type == "char_append":
            all_values = Groups.single_char_append()
            if RUNTIME_CONFIG.is_jtr():
                in_bracket_char_append = Groups.chars_append_in_bracket()
                slash_p_range_char_append = Elements._create_slash_parallel_cmds(
                    in_bracket_char_append)
                slash_number = Elements._create_slash_number_cmds()
                all_values = slash_number | slash_p_range_char_append | in_bracket_char_append | all_values

        elif char_type == "char_for_class":
            all_values = Groups.single_char_for_char_class()
            if RUNTIME_CONFIG.is_jtr():  # JTR supports
                in_bracket_char_for_class = Groups.range_char_for_char_class_in_bracket(
                )
                slash_p_in_bracket_char_class = Elements._create_slash_parallel_cmds(
                    in_bracket_char_for_class)
                slash_number = Elements._create_slash_number_cmds()
                all_values = slash_number | in_bracket_char_for_class | slash_p_in_bracket_char_class | all_values

        elif char_type == "class":
            all_values = Groups.single_class()
            if RUNTIME_CONFIG.is_jtr():  # JTR supports
                in_bracket_class = Groups.class_range_in_bracket()
                slash_p_in_bracket_class = Elements._create_slash_parallel_cmds(
                    in_bracket_class)
                slash_number = Elements._create_slash_number_cmds()
                all_values = slash_number | in_bracket_class | slash_p_in_bracket_class | all_values

        elif char_type == "simple_position":
            all_values = Groups.single_position()
            if RUNTIME_CONFIG.is_jtr():
                in_bracket_position = Groups.positions_in_bracket()
                slash_p_in_bracket_position = Elements._create_slash_parallel_cmds(
                    in_bracket_position)
                slash_number = Elements._create_slash_number_cmds()
                all_values = slash_number | slash_p_in_bracket_position | in_bracket_position | all_values

        else:
            raise Exception("Unknown Char_Class")

        return all_values

    @staticmethod
    @jtr_only_func
    def character_classes_group():
        """ All character classes

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

        all_chars = Groups.get_all_possible("class")
        return Literal('?') + all_chars


class Elements():
    """This class creates a parser capable for the JTR Rule language."""

    @staticmethod
    @jtr_only_func
    def _add_brackets(cmds):
        """Add brackets to commands, and accept one/more cmds inside the bracket. JTR Only

        This function does not modify cmds or add dash to cmds.
        """

        if not isinstance(cmds, MatchFirst) and not isinstance(cmds, Word):
            raise Exception("Wrong Usage of func _create_group_of_cmds")

        if cmds.matches("]"):
            raise Exception("Cores should escape brackets {}".format(cmds))

        return Combine(Literal("[") + OneOrMore(cmds) + Literal("]"))

    @staticmethod
    @jtr_only_func
    def _create_slash_parallel_cmds(parallel_cmds):
        """Add \p, \p1-\p9, \r to a cmd range ([cmds]). JTR Only"""

        slash = ZeroOrMore(
            Literal("\p") + Word(nums, exact=1) | Literal("\p") |
            Literal("\\r"))

        slash_cmd = Combine(slash + parallel_cmds)

        return slash_cmd

    @staticmethod
    @jtr_only_func
    def _create_slash_number_cmds():
        """Create \0-\9, which refers to previous ranges. JTR Only"""

        slash_num = Combine(Literal("\\") + Word(nums, exact=1))
        return slash_num

    @staticmethod
    def reject_flags():
        """ Parse Rejection Flags. JTR Only

        -:  no-op: don't reject
        -c  reject this rule unless current hash type is case-sensitive
        -8  reject this rule unless current hash type uses 8-bit characters
        -s  reject this rule unless some password hashes were split at loading
        -p  reject this rule unless word pair commands are currently allowed
        ->N reject this rule unless length N or longer is supported
        -<N reject this rule unless length N or shorter is supported
        """
        if RUNTIME_CONFIG[
                'running_style'] != RunningStyle.JTR:  # Only used in JTR
            return Empty()

        str_reject_flags_prefix = "-"
        str_reject_flags_cores = "c8sp:"
        str_reject_flags_length = "<>"

        word_reject_flags_prefix = Word(str_reject_flags_prefix, exact=1)
        word_reject_flags_cores = Word(str_reject_flags_cores, exact=1)
        word_reject_flags_length = Word(str_reject_flags_length, exact=1)

        simple_reject_flags = Combine(word_reject_flags_prefix +
                                      word_reject_flags_cores)
        simple_reject_flags_length = Combine(
            word_reject_flags_prefix + word_reject_flags_length +
            Word(jtr_numeric_constants_dash_allowed, exact=1))

        # -[:c]
        parallel_reject_flags = Combine(word_reject_flags_prefix + Elements.
                                        _add_brackets(word_reject_flags_cores))
        # -\r\p[:c]
        parallel_reject_flags_slash = Combine(
            word_reject_flags_prefix + Elements._create_slash_parallel_cmds(
                Elements._add_brackets(word_reject_flags_cores)))
        # ->8, -<7
        parallel_reject_flags_length = Combine(word_reject_flags_prefix +
                                               word_reject_flags_length +
                                               Groups.positions_in_bracket())

        one_reject_flags = simple_reject_flags | parallel_reject_flags | parallel_reject_flags_slash | simple_reject_flags_length | parallel_reject_flags_length

        return ZeroOrMore(one_reject_flags)

    @staticmethod
    def unary_cmds():
        """ Parse Commands with no parameters

        :   no-op: do nothing to the input word
        l   convert to lowercase
        u   convert to uppercase
        c   capitalize
        C   lowercase the first character, and uppercase the rest
        t   toggle case of all characters in the word
        r   reverse: "Fred" -> "derF"
        d   duplicate: "Fred" -> "FredFred"
        f   reflect: "Fred" -> "FredderF"
        {   rotate the word left: "jsmith" -> "smithj"
        }   rotate the word right: "smithj" -> "jsmith"
        [   delete the first character
        ]   delete the last character
        q   Duplicate every character
        k   Swaps first two characters
        K   Swaps last two characters
        E   Lower case the whole line, then upper case the first letter and every letter after a space
        P   "crack" -> "cracked", etc. (lowercase only)
        I   "crack" -> "cracking", etc. (lowercase only)
        S   shift case: "Crack96" -> "cRACK(^"
        V   lowercase vowels, uppercase consonants: "Crack96" -> "CRaCK96"
        M   Memorize current word
        Q   Reject plains where the memory saved matches current word
        p   pluralize: "crack" -> "cracks", etc. JTR Only
        R   shift each character right, by keyboard: "Crack96" -> "Vtsvl07" JTR Only
        L   shift each character left, by keyboard: "Crack96" -> "Xeaxj85" JTR Only
        """

        str_unary_cmds = ":lucCtrdf}{][qkKEPISVMQ"

        if RUNTIME_CONFIG.is_jtr():
            # JTR only pRL
            str_unary_cmds += 'pRL'

            # Some char definitions
            must_escaped_chars = "]["

            # Escape []
            for c in must_escaped_chars:
                str_unary_cmds = str_unary_cmds.replace(c, "")

            simple_unary_cmds = Combine(Word(str_unary_cmds, exact=1))
            for c in must_escaped_chars:
                simple_unary_cmds = Literal("\\" + c) | simple_unary_cmds

            # Type 1 [cmds]
            parallel_unary_cmds_1 = Combine(
                Elements._add_brackets(simple_unary_cmds))
            # Type 2 :[cmds]
            parallel_unary_cmds_2 = Combine(
                Literal(":") + parallel_unary_cmds_1)
            # Type 3 \p[cmds] or \p1[cmds]
            parallel_unary_cmds_3 = Combine(
                Elements._create_slash_parallel_cmds(parallel_unary_cmds_1))
            # Type 4 \0-\9
            parallel_unary_cmds_4 = Combine(
                Elements._create_slash_number_cmds())

            one_unary_cmd = parallel_unary_cmds_4 | parallel_unary_cmds_3 | parallel_unary_cmds_2 | simple_unary_cmds | parallel_unary_cmds_1

        else:
            simple_unary_cmds = Combine(Word(str_unary_cmds, exact=1))

            one_unary_cmd = simple_unary_cmds

        unary_cmds = ZeroOrMore(one_unary_cmd)

        return unary_cmds

    @staticmethod
    def binary_cmds():
        """ Parse Commands with 1 parameter

        $X  append character X to the word
        ^X  prefix the word with character X
        TN  toggle case of the character in position N
        'N  truncate the word at length N
        DN  delete the character in position N
        pN  Append duplicated word N times, HC only
        zN  Duplicates first character N times
        ZN  Duplicates last character N times
        LN  Bitwise shift left character @ N, HC only
        RN  Bitwise shift right character @ N, HC only
        +N  Increment character @ N by 1 ascii value
        -N  Decrement character @ N by 1 ascii value, HC only
        .N  Replaces character @ N with value at @ N plus 1
        ,N  Replaces character @ N with value at @ N minus 1
        yN  Duplicates first N characters
        YN  Duplicates last N characters
        """
        # commands that take a character as a parameter, and doesn't allow ?c
        str_char_cmds_prefix = "$^"

        # commands that take a position as a parameter
        str_position_cmds_prefix = "T'DzZ+.,yY"
        if RUNTIME_CONFIG.is_hc():
            str_position_cmds_prefix += '-pRL'  # HC only pN cmd

        # simple cmds, no parallelism
        simple_char_cmds = Combine(
            Word(str_char_cmds_prefix, exact=1) + Groups.single_char())

        # simple cmds, no parallelism
        simple_position_cmds = Combine(
            Word(str_position_cmds_prefix, exact=1) + Groups.single_position())

        if RUNTIME_CONFIG.is_jtr():
            # $[]
            parrallel_char_cmds_1 = Combine(
                Word(str_char_cmds_prefix, exact=1) + Groups.chars_in_bracket())
            # $\p[] $\r[]
            parrallel_char_cmds_2 = Combine(
                Word(str_char_cmds_prefix, exact=1) +
                Elements._create_slash_parallel_cmds(Groups.chars_in_bracket()))
            # $\0-\9
            parrallel_char_cmds_3 = Combine(
                Word(str_char_cmds_prefix, exact=1) +
                Elements._create_slash_number_cmds())

            char_cmds = simple_char_cmds | parrallel_char_cmds_3 | parrallel_char_cmds_2 | parrallel_char_cmds_1

            # T[]
            parrallel_position_cmds_1 = Combine(
                Word(str_position_cmds_prefix, exact=1) +
                Groups.positions_in_bracket())
            # T\p[] T\r[]
            parrallel_position_cmds_2 = Combine(
                Word(str_position_cmds_prefix, exact=1) + Elements.
                _create_slash_parallel_cmds(Groups.positions_in_bracket()))
            # T\0-\9
            parrallel_position_cmds_3 = Combine(
                Word(str_position_cmds_prefix, exact=1) +
                Elements._create_slash_number_cmds())

            position_cmds = simple_position_cmds | parrallel_position_cmds_3 | parrallel_position_cmds_2 | parrallel_position_cmds_1

        else:
            char_cmds = simple_char_cmds

            position_cmds = simple_position_cmds

        return ZeroOrMore(char_cmds | position_cmds)

    @staticmethod
    def ternary_cmds():
        r""" Parse Commands with 2 parameters

        AN"STR" insert string STR into the word at position N
        xNM extract substring from position N for up to M characters
        iNX insert character X in position N and shift the rest right
        oNX overstrike character in position N with character X
        ONM Deletes M characters, starting at position N
        *NM Swaps character at position N with character at position M #HC Only
        """

        # Some defs of possible positions
        all_positions = Groups.get_all_possible("simple_position")

        # Some defs of possible chars
        all_chars = Groups.get_all_possible(char_type="char")

        # prefixer
        str_prefix_nx = "oi"

        str_prefix_nm = "xO"
        if RUNTIME_CONFIG.is_hc():
            str_prefix_nm += '*'

        str_prefix_nstr = "A"

        # Building Parser
        nx_cmds = Combine(
            Word(str_prefix_nx, exact=1) + all_positions + all_chars)

        nm_cmds = Combine(
            Word(str_prefix_nm, exact=1) + all_positions + all_positions)

        all_cmds = nm_cmds | nx_cmds

        if RUNTIME_CONFIG.is_jtr():
            all_chars_append = Groups.get_all_possible("char_append")

            # build
            nstr_cmds = Combine(
                Word(str_prefix_nstr, exact=1) + all_positions + Suppress('"') +
                OneOrMore(all_chars_append) + Suppress('"'))
            all_cmds = all_cmds | nstr_cmds

        return ZeroOrMore(all_cmds)

    @staticmethod
    def memory_cmds():
        """ Memory access commands. 

        M & Q are defined in simple commands
        4   Append the word saved to memory to current word. HC only
        6   Prepend the word saved to memory to current word. HC only
        XNMI    Insert substring of length M starting from position N of word saved to memory at position I
        vVNM    update "l" (length), then subtract M from N and assign to variable V. JtR only
        """

        # MQ46
        str_memory_cmds = ""
        if RUNTIME_CONFIG.is_hc():
            str_memory_cmds += "46"
        simple_memory_cmds = Word(str_memory_cmds, exact=1)

        # xnmi
        all_positions = Groups.get_all_possible("simple_position")
        xnmi_cmd = Combine(
            Word("X", exact=1) + all_positions + all_positions + all_positions)

        # construct all_cmds
        all_cmds = simple_memory_cmds | xnmi_cmd

        # vvnm
        if RUNTIME_CONFIG.is_jtr():
            vvnm_cmd = Combine(
                Word("v", exact=1) + Word(srange("[a-k]"), exact=1) +
                all_positions + all_positions)
            all_cmds = all_cmds | vvnm_cmd

        return ZeroOrMore(all_cmds)

    @staticmethod
    def mode_cmds():
        """ Extra "single crack" mode commands. JtR only

        1   first word only
        2   second word only
        +   the concatenation of both (should only be used after a "1" or "2")
        """
        if RUNTIME_CONFIG[
                'running_style'] != RunningStyle.JTR:  # Only used in JTR
            return Empty()

        mode_cmds = Combine(Word("12+", exact=1))
        return ZeroOrMore(mode_cmds)

    @staticmethod
    def length_rejection_cmds():
        """ Rejections that don't involve character class.

        <N      reject the word unless it is less than N characters long
        >N      reject the word unless it is greater than N characters long
        _N      reject plains of length not equal to N
        """
        str_length_rejections_cmds = "><_"

        all_positions = Groups.get_all_possible("simple_position")

        all_cmds = Combine(
            Word(str_length_rejections_cmds, exact=1) + all_positions)
        return ZeroOrMore(all_cmds)

    @staticmethod
    def char_class_cmds():
        """ Character class commands. Rejections and Transformations that involve character class.

        !X      reject the word if it contains character X
        !?C     reject the word if it contains a character in class C
        /X      reject the word unless it contains character X
        /?C     reject the word unless it contains a character in class C
        =NX     reject the word unless character in position N is equal to X
        =N?C    reject the word unless character in position N is in class C
        (X      reject the word unless its first character is X
        (?C     reject the word unless its first character is in class C
        )X      reject the word unless its last character is X
        )?C     reject the word unless its last character is in class C
        %NX     reject the word unless it contains at least N instances of X
        %N?C    reject the word unless it contains at least N characters of class C
        sXY     replace all characters X in the word with Y
        s?CY    replace all characters of class C in the word with Y
        @X      purge all characters X from the word
        @?C     purge all characters of class C from the word
        eX      Lower case the whole line, then upper case the first letter and every letter after a custom separator character
        e?C     Lower case the whole line, then upper case the first letter and every letter after class C
        """

        str_something_x_cmds = "!/)(@e"
        str_something_nx_cmds = "=%"
        str_something_xy_cmds = "s"

        # define valid chars
        all_char_class_chars = Groups.get_all_possible("char_for_class")
        all_single_chars = Groups.get_all_possible("char")

        # define valid positions
        all_positions = Groups.get_all_possible("simple_position")

        something_x_cmds = Combine(
            Word(str_something_x_cmds, exact=1) + all_char_class_chars)
        something_nx_cmds = Combine(
            Word(str_something_nx_cmds, exact=1) + all_positions +
            all_char_class_chars)
        something_xy_cmds = Combine(
            Word(str_something_xy_cmds, exact=1) + all_char_class_chars +
            all_single_chars)
        all_cmds = something_x_cmds | something_nx_cmds | something_xy_cmds

        if RUNTIME_CONFIG.is_jtr():  # Positions JTR supports
            all_char_class = Groups.character_classes_group()
            something_qc_cmds = Combine(
                Word(str_something_x_cmds, exact=1) + all_char_class)
            something_nqc_cmds = Combine(
                Word(str_something_nx_cmds, exact=1) + all_positions +
                all_char_class)
            something_qcy_cmds = Combine(
                Word(str_something_xy_cmds, exact=1) + all_char_class +
                all_single_chars)
            all_cmds = all_cmds | something_qc_cmds | something_nqc_cmds | something_qcy_cmds

        return ZeroOrMore(all_cmds)

    @staticmethod
    def parser():
        """ Contruct the actual parser """
        if RUNTIME_CONFIG['running_style'] not in (RunningStyle.JTR,
                                                   RunningStyle.HC):
            raise Exception("Unknown Running Style: {}".format(
                RUNTIME_CONFIG['running_style']))

        reject_flags = Elements.reject_flags()
        unary_cmds = Elements.unary_cmds()
        binary_cmds = Elements.binary_cmds()
        ternary_cmds = Elements.ternary_cmds()
        memory_cmds = Elements.memory_cmds()
        mode_cmds = Elements.mode_cmds()
        length_rejection_cmds = Elements.length_rejection_cmds()
        char_class_cmds = Elements.char_class_cmds()
        return (reject_flags & length_rejection_cmds & unary_cmds & binary_cmds
                & ternary_cmds & memory_cmds & mode_cmds &
                char_class_cmds) + StringEnd()

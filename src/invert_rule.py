"""This file contains functions to invert transformation rules."""

from common import FatalRuntimeError, RunningStyle
from config import RUNTIME_CONFIG
from copy import deepcopy
from enum import Enum
from invert_helper import Dicts
from itertools import chain, combinations, product, permutations
import traceback
from tokenstr import TokenStringBase, Token, TokenType, TokenString
from utility import convert_str_length_to_int, get_name_of_a_rule
from feasibility import Invertibility


class InversionStatus(Enum):
    """ An enum that represents the inversion status.
    
    Attr:
        ERROR: Something went wrong, discard this result
        OUTSCOPE: Out of scope. Cannot be handled in current settings, require running JtR/HC
        NORMAL: Successful, there will be some preimages (0 to many). If rejected, there will be no preimages.
    """
    ERROR = 1,
    OUTSCOPE = 2,
    NORMAL = 3,


class InversionResult():
    """ A class that saves inversion results. """

    def __init__(self, value=None):
        """ Initalize a InversionResult

        Args:
            value: the initalization value. If value
                is None, then initialize emtpy list. 
                If value is string, tokenize the string.
        """
        self.status = InversionStatus.NORMAL
        if value is None or isinstance(value, TokenStringBase):
            self.results = [] if value is None else [value]
        else:
            raise FatalRuntimeError("Unknown value type")

        self.memorized_words = set()  # for special command
        self.error_msg = ""

    def __add__(self, x):
        """ add another instance of InversionResult, concat two lists. """
        if not isinstance(x, type(self)):
            raise Exception("Need to Add Two Result Class")

        self.results += x.results
        self.memorized_words |= x.memorized_words
        return self

    def __iter__(self):
        yield from self.results

    def is_normal(self):
        return self.status == InversionStatus.NORMAL

    def is_out_of_scope(self):
        return self.status == InversionStatus.OUTSCOPE

    def is_error(self):
        return self.status == InversionStatus.ERROR

    def add(self, value):
        """ add a Tokenstring/RegexTokenString """
        if isinstance(value, TokenStringBase):
            self.results.append(value)
        else:
            raise FatalRuntimeError("Unknown value type")

    def get_status(self):
        """ get the inversion status """
        return self.status

    def set_status(self, new_status):
        """ set the inversion status """
        self.status = new_status

    def get_value(self):
        """ return self.results """
        return self.results

    def is_null(self):
        """ Check if the results are null

        Returns:
            True if len(self.result) is 0 
        """

        return len(self.results) == 0

    def set_error_msg(self, msg):
        """ set error msg when something goes wrong, only used when inversion error 
    
        Args:
            msg: the error msg
        """
        self.error_msg = msg

    def get_number_of_strings(self, remove_non_ascii=False):
        """ count the number of possible strings represented. 
        
        Args:
            remove_non_ascii: whether to remove strings with non-ascii printable chars.
        """
        if (self.is_null == True or self.results == []):
            return 0

        count = 0

        for ts in self.results:
            if len(ts) == 0:  # Length = 0 means 1 empty string
                count += 1

            else:
                tmp_count = 1  # get count for one tokenstring
                for i in range(len(ts)):

                    if remove_non_ascii == False:
                        tmp_count *= len(ts.tokens[i])

                    else:
                        tmp_count *= len(
                            set(c for c in ts.tokens[i].get_value()
                                if char_is_printable(c)))

                    if tmp_count == 0:
                        break

                count += tmp_count

        return count

    def get_all_strings(self, unique=False):
        """ convert tokenstring repr to strings.
        
        Args:
            unique: whether to return only unique strings.
        """
        strings = []
        for ts in self.results:
            strings = strings + ts.to_strings()
        return strings if unique == False else set(strings)

    def contains(self, word):
        """ if a word is contained in the results. """
        for val in self.results:
            if val.contains(word):
                return True

        return False

    def memorize(self, words):
        self.memorized_words |= words

    def is_memorized(self, word):
        return word in self.memorized_words

    def has_memory(self):
        return len(self.memorized_words) != 0


class Inversion():
    """ A class contains only static functions. Each function inverts one rule """

    @staticmethod
    def invert_colon_command(token_str,
                             rule,
                             just_check=False,
                             enable_regex=False):
        """ :   do nothing 

        Inversion Idea:
            Since colon command does nothing, just return the input tokenstring

        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """

        if just_check == True:
            return Invertibility.INVERTIBLE

        # whether regex is enabled or not doesn't matter
        # nothing to be done, just add the tokenstr and return it.
        inversion_result = InversionResult()
        inversion_result.add(token_str)
        return inversion_result

    @staticmethod
    def invert_l_command(token_str, rule, just_check=False, enable_regex=False):
        """ l   lowercase all letters: paSSword -> password
        
        Inversion Idea:
            change each lowercase letter into a set of itself and its uppercase counterpart
            If there are any uppercase letters, that means this rule was never run on the word, so reject immediately.

        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:

            token_str_length = len(token_str)

            for idx, token in enumerate(token_str):
                new_set_other = set(
                    x for x in token.get_value().difference(Dicts.classes['a'])
                )  # All non-alphabetical characters
                new_set_lower = set(
                    chain.from_iterable(
                        (x, x.upper()) for x in token.get_value().intersection(
                            Dicts.classes['l'])))  # Get all lower case in dict
                new_set = new_set_other | new_set_lower

                if new_set == set():  # rejected
                    return inversion_result
                else:
                    token_str[idx].set_value(new_set)

            inversion_result.add(token_str)

            return inversion_result

        else:

            has_regex = False
            new_tokens = []
            for idx, token in enumerate(token_str):
                new_set_other = set(
                    x for x in token.get_value().difference(Dicts.classes['a'])
                )  # All non-alphabetical characters
                new_set_lower = set(
                    chain.from_iterable(
                        (x, x.upper()) for x in token.get_value().intersection(
                            Dicts.classes['l'])))  # Get all lower case in dict
                new_set = new_set_other | new_set_lower

                if token.is_range():
                    if new_set == set():
                        return inversion_result
                    else:
                        token.only_set_value(new_set)
                        new_tokens.append(token)

                else:
                    has_regex = True
                    if new_set == set():
                        # Reject if require at least one
                        if token.start >= 1:
                            return inversion_result

                    else:
                        # Careful you would have to set start and end for regex
                        # tokenstrings using set_value.
                        token.only_set_value(new_set)
                        new_tokens.append(token)

            # Filter the case where it only contains regex with range 0-inf and
            # regex are filtered. This case should be rejected
            if has_regex == True and len(new_tokens) == 0:
                # can only be empty
                token_str.tokens = []
                token_str.set_min_len(0)
                token_str.set_max_len(1)
                inversion_result.add(token_str)

            token_str.tokens = new_tokens
            inversion_result.add(token_str)

            return inversion_result

    @staticmethod
    def invert_u_command(token_str, rule, just_check=False, enable_regex=False):
        """ u   uppercase all letters: paSSword -> PASSWORD
        
        Inversion Idea:
            change each uppercase letter into a set of itself and its lowercase counterpart
            If there are any lowercase letters, that means this rule was never run on the word, so reject immediately.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:

            token_str_length = len(token_str)

            for idx, token in enumerate(token_str):

                new_set_other = set(
                    x for x in token.get_value().difference(Dicts.classes['a'])
                )  # Get all other
                new_set_upper = set(
                    chain.from_iterable((x, x.lower())
                                        for x in token.get_value().intersection(
                                            Dicts.classes['u']))
                )  # Get uppercase and convert to lowercase
                new_set = new_set_other | new_set_upper
                if new_set == set():  # rejected
                    return inversion_result
                else:
                    token_str[idx].set_value(new_set)

            inversion_result.add(token_str)
            return inversion_result

        else:
            has_regex = False
            new_tokens = []
            for idx, token in enumerate(token_str):
                new_set_other = set(
                    x for x in token.get_value().difference(Dicts.classes['a'])
                )  # Get all other
                new_set_upper = set(
                    chain.from_iterable((x, x.lower())
                                        for x in token.get_value().intersection(
                                            Dicts.classes['u']))
                )  # Get uppercase and convert to lowercase
                new_set = new_set_other | new_set_upper

                if token.is_range():
                    if new_set == set():
                        return inversion_result
                    else:
                        token.only_set_value(new_set)
                        new_tokens.append(token)

                else:
                    has_regex = True
                    if new_set == set():
                        if token.start >= 1:
                            return inversion_result
                    else:
                        token.only_set_value(new_set)
                        new_tokens.append(token)

            # Filter the case. This case should be rejected
            if has_regex == True and len(new_tokens) == 0:
                # can only be empty
                token_str.tokens = []
                token_str.set_min_len(0)
                token_str.set_max_len(1)
                inversion_result.add(token_str)
                return inversion_result

            token_str.tokens = new_tokens
            inversion_result.add(token_str)

            return inversion_result

    @staticmethod
    def invert_c_command(token_str, rule, just_check=False, enable_regex=False):
        """ c   capitalize first letter, lowercase rest: passWord -> Password

        Inversion Idea:
            check if first letter is capitalized and rest are lowercase.
            If they are, return the word with each letter and it's upper/lowercased counterpart
            If not, then reject the word.

        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:

            token_str_length = len(token_str)

            for idx, token in enumerate(token_str):
                if idx == 0:
                    new_set_other = set(x for x in token.get_value().difference(
                        Dicts.classes['a']))  # Get all other
                    new_set_lower = set(
                        chain.from_iterable((x, x.lower())
                                            for x in token.get_value().
                                            intersection(Dicts.classes['u']))
                    )  # all uppercase and corresponding lower
                    new_set = new_set_other | new_set_lower
                    if new_set == set():  # rejected
                        return inversion_result
                    else:
                        token_str[idx].set_value(new_set)

                else:
                    # Other Character, should be lower
                    new_set_other = set(x for x in token.get_value().difference(
                        Dicts.classes['a']))  # Get all other
                    new_set_upper = set(
                        chain.from_iterable((x, x.upper())
                                            for x in token.get_value().
                                            intersection(Dicts.classes['l']))
                    )  # all lowercase and corresponding upper
                    new_set = new_set_other | new_set_upper

                    if new_set == set():  # rejected
                        return inversion_result
                    else:
                        token_str[idx].set_value(new_set)

            inversion_result.add(token_str)
            return inversion_result

        else:
            less_than = deepcopy(token_str)
            less_than.set_max_len(1)

            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_or_equal = RegexTokenString.fix_first_N_position(
                token_str, 1)
            for one_ts in greater_or_equal:

                tokens = []

                for idx, token in enumerate(one_ts):
                    if idx == 0:

                        new_set_other = set(
                            x for x in token.get_value().difference(
                                Dicts.classes['a']))  # Get all other
                        new_set_lower = set(
                            chain.from_iterable(
                                (x, x.lower())
                                for x in token.get_value().intersection(
                                    Dicts.classes['u']))
                        )  # all uppercase and corresponding lower
                        new_set = new_set_other | new_set_lower

                        if token.is_range():

                            if new_set == set():  # rejected
                                break
                            else:
                                token.set_value(new_set)
                                tokens.append(token)

                        else:
                            if new_set == set():
                                if token.start > 0:
                                    break
                                else:  # could be nothing
                                    pass
                            else:
                                token.set_value(new_set)
                                tokens.append(token)

                    else:
                        new_set_other = set(
                            x for x in token.get_value().difference(
                                Dicts.classes['a']))  # Get all other
                        new_set_upper = set(
                            chain.from_iterable(
                                (x, x.upper())
                                for x in token.get_value().intersection(
                                    Dicts.classes['l']))
                        )  # all lowercase and corresponding upper
                        new_set = new_set_other | new_set_upper

                        if token.is_range():

                            if new_set == set():
                                break
                            else:
                                token.only_set_value(new_set)
                                tokens.append(token)

                        else:
                            if new_set == set():
                                if token.start > 0:
                                    break
                                else:  # could be nothing
                                    pass
                            else:
                                token.only_set_value(new_set)
                                tokens.append(token)

                else:
                    one_ts.tokens = tokens
                    inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_C_command(token_str, rule, just_check=False, enable_regex=False):
        """ C   lowercase first char, uppercase rest: Pas$Word -> pAS$WORD
        
        Inversion Idea:
            check if first letter is lowercase and rest are capitalized.
            If they are, return the word with each letter and its upper/lowercased counterpart
            If not, then reject the word.

        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:

            token_str_length = len(token_str)

            for idx, token in enumerate(token_str):
                if idx == 0:
                    new_set_other = set(x for x in token.get_value().difference(
                        Dicts.classes['a']))  # All non-alphabetical characters
                    new_set_lower = set(
                        chain.from_iterable((x, x.upper())
                                            for x in token.get_value().
                                            intersection(Dicts.classes['l']))
                    )  # all lowercase and corresponding upper
                    new_set = new_set_other | new_set_lower

                    if new_set == set():  # rejected
                        return inversion_result
                    else:
                        token_str[idx].set_value(new_set)

                else:
                    new_set_other = set(x for x in token.get_value().difference(
                        Dicts.classes['a']))  # All non-alphabetical characters
                    new_set_upper = set(
                        chain.from_iterable((x, x.lower())
                                            for x in token.get_value().
                                            intersection(Dicts.classes['u']))
                    )  # all uppercase and corresponding lower
                    new_set = new_set_other | new_set_upper
                    if new_set == set():  # rejected
                        return inversion_result
                    else:
                        token_str[idx].set_value(new_set)

            inversion_result.add(token_str)
            return inversion_result

        else:
            less_than = deepcopy(token_str)
            less_than.set_max_len(1)

            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_or_equal = RegexTokenString.fix_first_N_position(
                token_str, 1)
            for one_ts in greater_or_equal:

                tokens = []

                for idx, token in enumerate(one_ts):
                    if idx == 0:

                        new_set_other = set(x for x in token.get_value().
                                            difference(Dicts.classes['a']))
                        new_set_lower = set(
                            chain.from_iterable(
                                (x, x.upper())
                                for x in token.get_value().intersection(
                                    Dicts.classes['l'])))
                        new_set = new_set_other | new_set_lower

                        if token.is_range():

                            if new_set == set():
                                break
                            else:
                                token.set_value(new_set)
                                tokens.append(token)

                        else:
                            if new_set == set():
                                if token.start > 0:
                                    break
                                else:  # could be nothing
                                    pass
                            else:
                                token.set_value(new_set)
                                tokens.append(token)

                    else:
                        new_set_other = set(x for x in token.get_value().
                                            difference(Dicts.classes['a']))
                        new_set_upper = set(
                            chain.from_iterable(
                                (x, x.lower())
                                for x in token.get_value().intersection(
                                    Dicts.classes['u'])))
                        new_set = new_set_other | new_set_upper

                        if token.is_range():

                            if new_set == set():
                                break
                            else:
                                token.only_set_value(new_set)
                                tokens.append(token)

                        else:
                            if new_set == set():
                                if token.start > 0:
                                    break
                                else:  # could be nothing
                                    pass
                            else:
                                token.only_set_value(new_set)
                                tokens.append(token)

                else:
                    one_ts.tokens = tokens
                    inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_t_command(token_str, rule, just_check=False, enable_regex=False):
        """ t   toggles the case of all chars: h3llO-> H3LLo
        
        Inversion Idea:
            toggle the case of all chars

        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:

            token_str_length = len(token_str)

            for idx, token in enumerate(token_str):
                token_str[idx].set_value({
                    Dicts.toggle.setdefault(x, x) for x in token.get_value()
                })  # toggle the char

            inversion_result.add(token_str)
            return inversion_result

        else:
            for idx, token in enumerate(token_str):
                token_str[idx].only_set_value(
                    {Dicts.toggle.setdefault(x, x) for x in token.get_value()})

            inversion_result.add(token_str)
            return inversion_result

    @staticmethod
    def invert_r_command(token_str, rule, just_check=False, enable_regex=False):
        """ r   Invert the word: password -> drowssap
        
        Inversion Idea:
            Reverse the tokenstring
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:
            token_str.tokens = token_str.tokens[::-1]  # reverse the string
            inversion_result.add(token_str)
            return inversion_result

        else:
            token_str.tokens = token_str.tokens[::-1]
            inversion_result.add(token_str)
            return inversion_result

    @staticmethod
    def invert_d_command(token_str, rule, just_check=False, enable_regex=False):
        """ d   Duplicates word: pass -> passpass
        
        Inversion Idea:
            cut the word in half and make sure each lines up.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        return Inversion.invert_p_N_command(token_str, "p1", just_check,
                                            enable_regex)

    @staticmethod
    def invert_f_command(token_str, rule, just_check=False, enable_regex=False):
        """ f   Reflects the word: pass -> passssap
        
        Inversion Idea:
            cut in half and work from opposite ends comparing.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:

            token_str_length = len(token_str)

            # Doubled word is too long
            if token_str_length * 2 > RUNTIME_CONFIG['max_password_length']:
                original_ts = deepcopy(token_str)
                inversion_result.add(original_ts)

            if token_str_length % 2 != 0:  # Not even number, reject
                return inversion_result

            half_length = int(token_str_length / 2)
            for idx in range(half_length):
                # compare left with right
                left_set = set(token_str[idx].get_value())
                right_set = set(
                    token_str[token_str_length - idx - 1].get_value())
                intersect_set = left_set.intersection(right_set)

                if intersect_set == set():
                    return inversion_result
                else:
                    if token_str[idx].is_regex() and token_str[
                            idx + half_length].is_regex():
                        start = max(token_str[idx + half_length].start,
                                    token_str[idx].start)
                        end = min(token_str[idx + half_length].end,
                                  token_str[idx].end)

                        token_str[idx] = Token(intersect_set, start, end)
                    else:
                        token_str[idx] = Token(intersect_set)

            token_str.tokens = token_str.tokens[:half_length]
            token_str.length = half_length
            inversion_result.add(token_str)
            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_left_curly_bracket_command(token_str,
                                          rule,
                                          just_check=False,
                                          enable_regex=False):
        """ {   Rotates the word left: password -> asswordp
        
        Inversion Idea:
            rotate the word right
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """

        if just_check == True:
            return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:
            token_str_length = len(token_str)
            token_str.tokens = token_str.tokens[token_str_length - 1:] + \
                token_str.tokens[:token_str_length - 1]  # rotate back
            inversion_result.add(token_str)
            return inversion_result

        else:
            # Enumerate the last char. Coz only the last char matters (last
            # char put to first)
            less_than = deepcopy(token_str)
            less_than.set_max_len(1)
            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_or_equal = RegexTokenString.fix_last_N_position(
                token_str, 1)
            for one_ts in greater_or_equal:

                one_ts.tokens = one_ts.tokens[-1:] + one_ts.tokens[:-1]
                inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_right_curly_bracket_command(token_str,
                                           rule,
                                           just_check=False,
                                           enable_regex=False):
        """ }   Rotates the word right: password -> dpasswor

        Inversion Idea:
            rotate the word left.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:
            # rotate back
            token_str.tokens = token_str.tokens[1:] + token_str.tokens[:1]
            inversion_result.add(token_str)
            return inversion_result

        else:
            # Enumerate the last char. Coz only the last char matters (last
            # char put to first)
            less_than = deepcopy(token_str)
            less_than.set_max_len(1)
            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_or_equal = RegexTokenString.fix_first_N_position(
                token_str, 1)
            for one_ts in greater_or_equal:

                one_ts.tokens = one_ts.tokens[1:] + one_ts.tokens[:1]
                inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_left_square_bracket_command(token_str,
                                           rule,
                                           just_check=False,
                                           enable_regex=False):
        """ [   Deletes the first character

        Inversion Idea:
            Shift the rest of the word right one, and insert an allchar set into the first position
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        return Inversion.invert_D_N_command(token_str, ["D", "0"], just_check,
                                            enable_regex)

    @staticmethod
    def invert_right_square_bracket_command(token_str,
                                            rule,
                                            just_check=False,
                                            enable_regex=False):
        """ ]   Deletes the last character

        Inversion Idea:
            Append the set of all possible chars to the end of the word.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:

            token_str_length = len(token_str)

            # Len = 0 covered here.
            if token_str_length == 0:
                # Could be empty too, this is a corner case
                inversion_result.add(deepcopy(token_str))
                token_str.tokens = [Token(Dicts.classes['z'])]
            else:
                token_str.tokens = token_str.tokens + \
                    [Token(Dicts.classes['z'])]

            token_str.length = token_str_length + 1

            inversion_result.add(token_str)
            return inversion_result

        else:
            # case1: less than 1
            less_than = deepcopy(token_str)
            less_than.set_max_len(1)
            if less_than.is_valid():
                inversion_result.add(less_than)

            token_str.tokens = token_str.tokens + [Token(Dicts.classes['z'])]
            token_str.increase_window(1)
            inversion_result.add(token_str)

            return inversion_result

    @staticmethod
    def invert_D_N_command(token_str,
                           rule,
                           just_check=False,
                           enable_regex=False):
        """ DN  Deletes char at position N

        Inversion Idea:
            Shift the part of the word to the right of the position right one
            insert an allchar set into that spot
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            try:
                N = convert_str_length_to_int(rule[1])
                return Invertibility.INVERTIBLE
            except BaseException:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        parameter_n = convert_str_length_to_int(rule[1])

        if enable_regex == False:

            token_str_length = len(token_str)

            # remove one get max_length, rejected
            if token_str_length == RUNTIME_CONFIG['max_password_length']:
                return inversion_result

            if token_str_length <= parameter_n - 1:  # no deletion
                inversion_result.add(token_str)
            elif token_str_length >= parameter_n + 1:  # definitely some deletion
                token_str.tokens = token_str.tokens[:parameter_n] + [
                    Token(Dicts.classes['z'])
                ] + token_str.tokens[parameter_n:]
                token_str.length = token_str_length + 1
                inversion_result.add(token_str)
            else:  # two cases.
                # Case 1: There's no word there
                inversion_result.add(deepcopy(token_str))

                # Length == 0 covered.
                if token_str_length == 0:
                    token_str.tokens = [Token(Dicts.classes['z'])]
                else:
                    token_str.tokens = token_str.tokens[:parameter_n] + [
                        Token(Dicts.classes['z'])
                    ] + token_str.tokens[parameter_n:]
                token_str.length = token_str_length + 1

                inversion_result.add(token_str)  # CASE 2: There'a word there

            return inversion_result

        else:
            # case1: less than N + 1
            less_than = deepcopy(token_str)
            less_than.set_max_len(parameter_n + 1)
            if less_than.is_valid():
                inversion_result.add(less_than)

            # case2: something is at Nth position
            greater_or_equal = RegexTokenString.fix_first_N_position(
                token_str, parameter_n)  # get all =N
            for one_ts in greater_or_equal:
                one_ts.tokens = one_ts.tokens[:parameter_n] + \
                    [Token(Dicts.classes['z'])] + one_ts.tokens[parameter_n:]
                one_ts.increase_window(1)
                inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_q_command(token_str, rule, just_check=False, enable_regex=False):
        """ q   Duplicates every character: abcd -> aabbccdd

        Inversion Idea:
            make sure the length of the str is even. check that every two char match
            Return a string consisting only of the positions where i%2 == 0
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:

            token_str_length = len(token_str)

            if token_str_length == 0:  # 0 * 2 = 0
                inversion_result.add(token_str)
                return inversion_result

            # potentially too long for duplicate
            if token_str_length * 2 > RUNTIME_CONFIG['max_password_length']:
                original_ts = deepcopy(token_str)
                inversion_result.add(original_ts)

            if token_str_length % 2 != 0:
                return inversion_result

            final_ts = deepcopy(token_str)  # save the final result
            half_length = int(token_str_length / 2)
            final_ts.tokens = final_ts.tokens[:half_length]
            final_ts.length = half_length

            ctr = 0  # pointer noting the place
            while ctr < token_str_length:
                left_set = set(token_str[ctr].get_value())
                right_set = set(token_str[ctr + 1].get_value())
                # get the intersection of two sides.
                intersect_set = left_set.intersection(right_set)
                if intersect_set == set():
                    return inversion_result
                else:
                    final_ts[int(ctr / 2)] = Token(intersect_set)
                    ctr += 2

            inversion_result.add(final_ts)
            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_k_command(token_str, rule, just_check=False, enable_regex=False):
        """ k   Swaps first two characters: password -> apssword

        Inversion Idea:
            Swap the first two characters and return.
            If word is 1 char long, return it.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:

            token_str_length = len(token_str)

            if token_str_length < 2:
                inversion_result.add(token_str)
                return inversion_result

            token_str[0], token_str[1] = token_str[1], token_str[0]  # swap

            inversion_result.add(token_str)
            return inversion_result

        else:
            less_than = deepcopy(token_str)
            less_than.set_max_len(2)  # <2, do nothing
            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_or_equal = RegexTokenString.fix_first_N_position(
                token_str, 2)  # get last 2 chars fixed
            for one_ts in greater_or_equal:
                one_ts[0], one_ts[1] = one_ts[1], one_ts[0]
                inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_K_command(token_str, rule, just_check=False, enable_regex=False):
        """ K   Swaps last two characters: password -> passwodr

        Inversion Idea:
            Swap last two characters and return.
            If word is 1 char long, return it.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:

            token_str_length = len(token_str)

            if token_str_length < 2:
                inversion_result.add(token_str)
                return inversion_result

            token_str[-1], token_str[-2] = token_str[-2], token_str[-1]  # swap
            inversion_result.add(token_str)

            return inversion_result

        else:
            less_than = deepcopy(token_str)
            less_than.set_max_len(2)  # <2, do nothing
            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_or_equal = RegexTokenString.fix_last_N_position(
                token_str, 2)  # get last 2 chars fixed
            for one_ts in greater_or_equal:
                one_ts[-1], one_ts[-2] = one_ts[-2], one_ts[-1]
                inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_E_command(token_str, rule, just_check=False, enable_regex=False):
        """ E   Lower case the whole line, then upper case the first letter and every letter after a space: "p@ssW0rd w0rld" -> "P@ssw0rd W0rld"

        Inversion Idea:
            Check to make sure first letter is uppercased and every letter after a space is uppercased.
            Put each letter in a set with its upper/lowercase counterpart.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        return Inversion.invert_e_X_command(token_str, "e ", just_check,
                                            enable_regex)

    @staticmethod
    def s_sanity_check(input_token_str, inversion_result):
        """ check all cases that end with "s", s pre-removed """

        # Flag
        filtered = False
        # const defs
        sxz_set = set("sxz")
        cs_set = set("cs")
        h_set = set("h")
        f_set = set("f")
        e_set = set("e")
        y_set = set("y")
        aeiou_set = set("aeiou")

        # For each token_string, have to survive all checking to be valid
        ret_val = []
        # length > 3, removal of "s" resulted in the condition of ch/sh
        if len(input_token_str) > 2 and len(
                h_set & input_token_str[-1].get_value()) != 0 and len(
                    cs_set & input_token_str[-2].get_value()) != 0:
            filtered = True

            # Rejected
            if input_token_str[-2].get_value().issubset(
                    cs_set) and input_token_str[-1].get_value().issubset(h_set):
                pass

            # Remove the form of ch/sh, and then it stands as valid append s
            # condition
            else:
                # Remove seperately, there will be duplicates, but dont matter
                if input_token_str[-1].get_value().issubset(h_set) != True:
                    token_str_1 = deepcopy(input_token_str)
                    token_str_1[-1].set_value(token_str_1[-1].get_value() -
                                              h_set)
                    ret_val.append(token_str_1)

                if input_token_str[-2].get_value().issubset(cs_set) != True:
                    token_str_2 = deepcopy(input_token_str)
                    token_str_2[-2].set_value(token_str_2[-2].get_value() -
                                              cs_set)
                    ret_val.append(token_str_2)

        # removal of "s" resulted in the condition of "sxz"
        if len(input_token_str) >= 1 and len(
                sxz_set & input_token_str[-1].get_value()) != 0:
            filtered = True

            # only sxz, rejected
            if input_token_str[-1].get_value().issubset(sxz_set):
                pass

            # remoe sxz situation
            else:
                token_str_3 = deepcopy(input_token_str)
                token_str_3[-1].set_value(token_str_3[-1].get_value() - sxz_set)
                ret_val.append(token_str_3)

        # removal of "f" resulted in "xf" condition -> last one f, and second
        # to last if not f.
        if len(input_token_str) >= 2 and len(
                f_set & input_token_str[-1].get_value()) != 0 and len(
                    input_token_str[-2].get_value().difference(f_set)) != 0:
            filtered = True

            # remove "f" from last one, or remove everything not f from second
            # to last one
            if len(input_token_str[-1].get_value() - f_set) != 0:
                token_str_4 = deepcopy(input_token_str)
                token_str_4[-1].set_value(token_str_4[-1].get_value() - f_set)
                ret_val.append(token_str_4)

            # second to last is f
            if len(input_token_str[-2].get_value() & f_set) != 0:
                token_str_5 = deepcopy(input_token_str)
                token_str_5[-2].set_value(f_set)
                ret_val.append(token_str_5)

        # remove s get fe
        if len(input_token_str) > 2 and len(
                e_set & input_token_str[-1].get_value()) != 0 and len(
                    f_set & input_token_str[-2].get_value()) != 0:
            filtered = True

            if input_token_str[-1].get_value().issubset(e_set) != True:
                token_str_6 = deepcopy(input_token_str)
                token_str_6[-1].set_value(token_str_6[-1].get_value() - e_set)
                ret_val.append(token_str_6)

            if input_token_str[-2].get_value().issubset(f_set) != True:
                token_str_7 = deepcopy(input_token_str)
                token_str_7[-2].set_value(token_str_7[-2].get_value() - f_set)
                ret_val.append(token_str_7)

        # length > 3 and get zy -> to ies
        if len(input_token_str) > 2 and len(
                input_token_str[-2].get_value().difference(aeiou_set)
        ) != 0 and len(input_token_str[-1].get_value() & y_set) != 0:
            filtered = True

            if len(input_token_str[-1].get_value() - y_set) != 0:
                token_str_8 = deepcopy(input_token_str)
                token_str_8[-1].set_value(token_str_8[-1].get_value() - y_set)
                ret_val.append(token_str_8)

            # second to last is aeiou
            if len(input_token_str[-2].get_value() & aeiou_set) != 0:
                token_str_9 = deepcopy(input_token_str)
                token_str_9[-2].set_value(
                    input_token_str[-2].get_value() & aeiou_set)
                ret_val.append(token_str_9)

        # Passed all sanity check
        # input_token_str survives all the checking, it should be added
        if filtered == False:
            inversion_result.add(input_token_str)

        return ret_val

    @staticmethod
    def es_sanity_check(input_token_str, inversion_result):
        """ check all cases that end with "es", es pre-removed """

        sxz_set = set("sxz")
        cs_set = set("cs")
        h_set = set("h")

        # Valid case 1: sxz
        if len(input_token_str) >= 1 and len(
                sxz_set & input_token_str[-1].get_value()) != 0:
            token_str_1 = deepcopy(input_token_str)
            token_str_1[-1].set_value(token_str_1[-1].get_value() & sxz_set)
            inversion_result.add(token_str_1)

        # Valid case 2: The only valid case of being es is ch/sh with length >
        # 2 . Otherwise ending with es are invalid
        if len(input_token_str) > 2 and len(
                h_set & input_token_str[-1].get_value()) != 0 and len(
                    cs_set & input_token_str[-2].get_value()) != 0:
            token_str_2 = deepcopy(input_token_str)
            token_str_2[-1].set_value(token_str_2[-1].get_value() & h_set)
            token_str_2[-2].set_value(token_str_2[-2].get_value() & cs_set)
            inversion_result.add(token_str_2)

        # other cases are rejected

    @staticmethod
    def ves_sanity_check(input_token_str, inversion_result):
        """ check all cases that end with "ves", ves pre-removed """

        f_set = set("f")
        e_set = set("e")

        # ends with ves, so v could be f, and if what's before f is not f, them
        # bf -> bves
        if len(input_token_str) >= 1 and len(
                input_token_str[-1].get_value().difference(f_set)) != 0:

            # remove "f" from last one, or remove everything not f from second
            # to last one
            token_str_1 = deepcopy(input_token_str)
            token_str_1[-1].set_value(
                input_token_str[-1].get_value().difference(f_set))
            token_str_1.append_token(Token("f"))

            inversion_result.add(token_str_1)

        # ends with ves, it could be just fe at the end
        if len(input_token_str) >= 1:

            token_str_2 = deepcopy(input_token_str)
            token_str_2.append_token(Token("f"))
            token_str_2.append_token(Token("e"))

            inversion_result.add(token_str_2)

    @staticmethod
    def ies_sanity_check(input_token_str, inversion_result):
        """ check all cases that end with "ies", ies pre-removed """

        # bby -> bbies, bay -> bays
        y_set = set("y")
        aeiou_set = set("aeiou")

        if len(input_token_str) >= 2 and len(
                input_token_str[-1].get_value().difference(aeiou_set)) != 0:

            token_str_1 = deepcopy(input_token_str)
            token_str_1[-1].set_value(
                input_token_str[-1].get_value().difference(aeiou_set))
            token_str_1.append_token(Token("y"))
            inversion_result.add(token_str_1)

    @staticmethod
    def ed_sanity_check(input_token_str, inversion_result):
        """ check all cases that end with "ed", ed pre-removed """

        # For each token_string, have to survive all checking to be valid
        ret_val = []

        # a(ed) is impossible, so is ab(ed)
        if len(input_token_str) <= 2:
            return ret_val

        # Flag
        filtered = False

        bgp_set = set("bgp")
        y_set = set("y")

        # filter condition (gged), remove ed, you get the condition to double
        # (bag) bgp
        if len(input_token_str) >= 3 and len(
                input_token_str[-1].get_value() & bgp_set) != 0 and len(
                    input_token_str[-2].get_value().difference(bgp_set)) != 0:
            filtered = True

            # Filter that part.
            # either [-1] != bgp
            if len(input_token_str[-1].get_value() - bgp_set) != 0:

                token_str_1 = deepcopy(input_token_str)
                token_str_1[-1].set_value(input_token_str[-1].get_value() -
                                          bgp_set)
                ret_val.append(token_str_1)

            # or [-2] = bgp
            if len(input_token_str[-2].get_value() & bgp_set) != 0:
                token_str_2 = deepcopy(input_token_str)
                token_str_2[-2].set_value(
                    input_token_str[-2].get_value() & bgp_set)
                ret_val.append(token_str_2)

        # filter condition (ied), remove ed, you ends with y, then it is not
        # possible
        if len(y_set & input_token_str[-1].get_value()) != 0:
            filtered = True

            # Filter that part.
            # [-1] != y
            if len(input_token_str[-1].get_value() - y_set) != 0:

                token_str_3 = deepcopy(input_token_str)
                token_str_3[-1].set_value(input_token_str[-1].get_value() -
                                          y_set)
                ret_val.append(token_str_3)

        if filtered == False:
            inversion_result.add(input_token_str)

        return ret_val

    @staticmethod
    def ing_sanity_check(input_token_str, inversion_result):
        """ check all cases that end with "ing", ing pre-removed """

        # For each token_string, have to survive all checking to be valid
        ret_val = []

        # a(ing) and ac(ing) are impossible by just append ing
        if len(input_token_str) <= 2:
            return ret_val

        # Flag
        filtered = False

        bgp_set = set("bgp")
        aeiou_set = set("aeiou")

        # filter condition (gging), remove ing, you get the condition to double
        # (bag) bgp
        if len(input_token_str) >= 3 and len(
                input_token_str[-1].get_value() & bgp_set) != 0 and len(
                    input_token_str[-2].get_value().difference(bgp_set)) != 0:
            filtered = True

            # Filter that part.
            # either [-1] != bgp
            if len(input_token_str[-1].get_value() - bgp_set) != 0:

                token_str_1 = deepcopy(input_token_str)
                token_str_1[-1].set_value(input_token_str[-1].get_value() -
                                          bgp_set)
                ret_val.append(token_str_1)

            # or [-2] = bgp
            if len(input_token_str[-2].get_value() & bgp_set) != 0:
                token_str_2 = deepcopy(input_token_str)
                token_str_2[-2].set_value(
                    input_token_str[-2].get_value() & bgp_set)
                ret_val.append(token_str_2)

        # filter condition (aeiou + ing), remove ing, you ends with aeiou, then
        # it is not possible
        if len(aeiou_set & input_token_str[-1].get_value()) != 0:
            filtered = True

            # Filter that part.
            # [-1] != aeiou_set
            if len(input_token_str[-1].get_value() - aeiou_set) != 0:

                token_str_3 = deepcopy(input_token_str)
                token_str_3[-1].set_value(input_token_str[-1].get_value() -
                                          aeiou_set)
                ret_val.append(token_str_3)

        if filtered == False:
            inversion_result.add(input_token_str)

        return ret_val

    @staticmethod
    def invert_P_command(token_str, rule, just_check=False, enable_regex=False):
        """ P   "crack" -> "cracked", etc. (lowercase only)

        Inversion Idea:
            Case by case study. Check if it ends with "ed", and find all possible preimages.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == False:
                return Invertibility.INVERTIBLE
            else:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:
            # len(1,2) doesn't change
            if len(token_str) <= 2:
                inversion_result.add(token_str)
                return inversion_result

            bgp_set = set("bgp")

            # Below guaranteed length >= 3
            # If ends with "ed"
            if "e" in token_str[-2].get_value(
            ) and "d" in token_str[-1].get_value():
                # first, it could be itself
                token_str_1 = deepcopy(token_str)
                token_str_1[-2].set_value("e")
                token_str_1[-1].set_value("d")
                inversion_result.add(token_str_1)

                # second, it could be "???e".
                token_str_2 = deepcopy(token_str)
                token_str_2.pop_token(-1)
                token_str_2[-1].set_value("e")
                if len(token_str_2) >= 3:
                    inversion_result.add(token_str_2)

                # third, ed but can't be filtered (e.g. bag -> bagged)
                tmp_token_string = deepcopy(token_str)
                tmp_token_string.pop_token(-1)
                tmp_token_string.pop_token(-1)
                q = [tmp_token_string]

                while len(q) != 0:

                    ret = Inversion.ed_sanity_check(q.pop(0), inversion_result)

                    if len(ret) != 0:

                        q += ret

            # fourth, ied. remove ed, change i to y.
            if "i" in token_str[-3].get_value() and "e" in token_str[
                    -2].get_value() and "d" in token_str[-1].get_value():
                token_str_3 = deepcopy(token_str)
                token_str_3.pop_token(-1)
                token_str_3.pop_token(-1)
                token_str_3[-1].set_value("y")
                inversion_result.add(token_str_3)

            # fifth, bagged possible and agged impossible
            if len(token_str) >= 6 and len(token_str[-5].get_value().difference(
                    bgp_set)) != 0 and len(token_str[-4].get_value(
                    ) & token_str[-3].get_value() & bgp_set) != 0:
                token_str_4 = deepcopy(token_str)
                token_str_4.pop_token(-1)  # pop unless part.
                token_str_4.pop_token(-1)  # pop unless part.
                token_str_4.pop_token(-1)  # pop unless part.
                token_str_4[-2].set_value(
                    token_str_4[-2].get_value().difference(bgp_set))
                token_str_4[-1].set_value(token_str_4[-1].get_value() & bgp_set)
                inversion_result.add(token_str_4)

            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_I_command(token_str, rule, just_check=False, enable_regex=False):
        """ I   "crack" -> "cracking", etc. (lowercase only)

        Inversion Idea:
            Case by case study. Check if it ends with "ing", and find all possible preimages.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == False:
                return Invertibility.INVERTIBLE
            else:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:

            # len(1,2) doesn't change
            if len(token_str) <= 2:
                inversion_result.add(token_str)
                return inversion_result

            aeiou_set = set("aeiou")
            bgp_set = set("bgp")

            # Below guaranteed length >= 3
            # If ends with "ing"
            if "i" in token_str[-3].get_value() and "n" in token_str[
                    -2].get_value() and "g" in token_str[-1].get_value():
                # first, it could be itself
                token_str_1 = deepcopy(token_str)
                token_str_1[-3].set_value("i")
                token_str_1[-2].set_value("n")
                token_str_1[-1].set_value("g")
                inversion_result.add(token_str_1)

                # second, ing but can't be filtered (e.g. bag -> bagging)
                tmp_token_string = deepcopy(token_str)
                tmp_token_string.pop_token(-1)
                tmp_token_string.pop_token(-1)
                tmp_token_string.pop_token(-1)
                q = [tmp_token_string]

                while len(q) != 0:

                    ret = Inversion.ing_sanity_check(q.pop(0), inversion_result)

                    if len(ret) != 0:

                        q += ret

                # Third remove aeiou then append ing
                if len(token_str) >= 5:
                    token_str_3 = deepcopy(token_str)
                    token_str_3.pop_token(-1)
                    token_str_3.pop_token(-1)
                    token_str_3[-1].set_value(aeiou_set)
                    inversion_result.add(token_str_3)

            # Fourth, bagging possible agging impossible
            if len(token_str) >= 7 and len(token_str[-6].get_value().difference(
                    bgp_set)) != 0 and len(token_str[-5].get_value(
                    ) & token_str[-4].get_value() & bgp_set) != 0:
                token_str_4 = deepcopy(token_str)
                token_str_4.pop_token(-1)  # pop useless part.
                token_str_4.pop_token(-1)  # pop useless part.
                token_str_4.pop_token(-1)  # pop useless part.
                token_str_4.pop_token(-1)  # pop useless part.
                token_str_4[-2].set_value(
                    token_str_4[-2].get_value().difference(bgp_set))
                token_str_4[-1].set_value(token_str_4[-1].get_value() & bgp_set)
                inversion_result.add(token_str_4)

            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    # Here we know the rule is only, no parameters for rule 'S'
    def invert_S_command(token_str, rule, just_check=False, enable_regex=False):
        """ S   shift case: "Crack96" -> "cRACK(^"
        
        Inversion Idea:
            Shifts the case for every character in the TokenString using the shift dictionary
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        
        """
        if just_check == True:
            if enable_regex == False:
                return Invertibility.INVERTIBLE
            else:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:
            for idx, token in enumerate(token_str):

                if token.is_range():
                    token_str[idx].set_value(  # use prebuilt dict
                        {Dicts.shift[x] for x in token.get_value()})

                else:
                    token_str[idx].set_value(
                        {Dicts.shift[x] for x in token.get_value()},
                        token.start, token.end)

            inversion_result.add(token_str)
            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_V_command(token_str, rule, just_check=False, enable_regex=False):
        """
        V   lowercase vowels, uppercase consonants: "Crack96" -> "CRaCK96"
        
        Inversion Idea:
            If there are any uppercase vowels or lowercase consonants in literals, the word is rejected
            If they are ranges, then they are dropped from the ranges and if the range is comprised of the above characters, the word is rejected
            Otherwise, invert and changes vowels to uppercase and consonants to lowercase. Leaves the other characters the same.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == False:
                return Invertibility.INVERTIBLE
            else:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:
            for idx, token in enumerate(token_str):

                if token.is_range():
                    # Get two results in list-comprehension
                    lower_vowel = set(
                        chain.from_iterable(
                            (x, x.upper()) for x in token.get_value() if
                            (x in Dicts.classes['v'] and x in Dicts.classes['l']
                            )))  # Get Lower V in Set Convert Them to Upper
                    upper_cons = set(
                        chain.from_iterable(
                            (x, x.lower()) for x in token.get_value() if
                            (x in Dicts.classes['c'] and x in Dicts.classes['u']
                            )))  # Get Upper C in Set Convert Them to Lower
                    other_char = {
                        x for x in token.get_value()
                        if (x not in Dicts.classes['v'] and
                            x not in Dicts.classes['c'])
                    }

                    new_set = lower_vowel | upper_cons | other_char
                    if new_set == set():
                        return inversion_result

                    token_str[idx].set_value(new_set)

                else:
                    lower_vowel = set(
                        chain.from_iterable(
                            (x, x.upper()) for x in token.get_value() if
                            (x in Dicts.classes['v'] and x in Dicts.classes['l']
                            )))  # Get Lower V in Set Convert Them to Upper
                    upper_cons = set(
                        chain.from_iterable(
                            (x, x.lower()) for x in token.get_value() if
                            (x in Dicts.classes['c'] and x in Dicts.classes['u']
                            )))  # Get Upper C in Set Convert Them to Lower
                    other_char = {
                        x for x in token.get_value()
                        if (x not in Dicts.classes['v'] and
                            x not in Dicts.classes['c'])
                    }

                    new_set = lower_vowel | upper_cons | other_char
                    if new_set == set():
                        return inversion_result

                    token_str[idx].set_value(ew_set, token.start, token.end)

            inversion_result.add(token_str)
            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_p_command(token_str, rule, just_check=False, enable_regex=False):
        """ p   pluralize: "crack" -> "cracks", etc. (lowercase only)

        Inversion Idea:
            Case by case study. Check if it ends with "s", and find all possible preimages.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == False:
                return Invertibility.INVERTIBLE
            else:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:

            # If length < 2, do nothing
            if len(token_str) <= 1:
                inversion_result.add(token_str)
                return inversion_result

            # If length = 2, it's impossible
            if len(token_str) == 2:
                return inversion_result

            # All below length >= 3
            # First check s
            # If it is s, then after removing it, it shouldn't form the
            # condition to be ies, ves or es.
            if "s" in token_str[-1].get_value():

                tmp_token_string = deepcopy(token_str)
                tmp_token_string.pop_token(-1)

                q = [tmp_token_string]

                while len(q) != 0:

                    ret = Inversion.s_sanity_check(q.pop(0), inversion_result)

                    if len(ret) != 0:

                        q += ret

            # Second check es
            if "s" in token_str[-1].get_value(
            ) and "e" in token_str[-2].get_value():

                # remove es
                tmp_token_string = deepcopy(token_str)
                tmp_token_string.pop_token(-1)
                tmp_token_string.pop_token(-1)

                Inversion.es_sanity_check(tmp_token_string, inversion_result)

            # Third check ves
            if "s" in token_str[-1].get_value() and "e" in token_str[
                    -2].get_value() and "v" in token_str[-3].get_value():

                # remove es
                tmp_token_string = deepcopy(token_str)
                tmp_token_string.pop_token(-1)
                tmp_token_string.pop_token(-1)
                tmp_token_string.pop_token(-1)

                Inversion.ves_sanity_check(tmp_token_string, inversion_result)

            # Final check ies
            if "s" in token_str[-1].get_value() and "e" in token_str[
                    -2].get_value() and "i" in token_str[-3].get_value():

                # remove es
                tmp_token_string = deepcopy(token_str)
                tmp_token_string.pop_token(-1)
                tmp_token_string.pop_token(-1)
                tmp_token_string.pop_token(-1)

                Inversion.ies_sanity_check(tmp_token_string, inversion_result)

            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_R_command(token_str, rule, just_check=False, enable_regex=False):
        """ R   shift each character right, by keyboard: "Crack96" -> "Vtsvl07"
        
        Inversion Idea:
            We shift each character left by keyboard.
            We note that some are not perfectly shifted left, and that's due to how they are initially shifted right.
            If words contain literals that, when shifted right are none, we reject the word.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """

        if just_check == True:
            if enable_regex == False:
                return Invertibility.INVERTIBLE
            else:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:
            for idx, token in enumerate(token_str):
                if token.is_range():
                    new_set = set()
                    for x in token.get_value():
                        if Dicts.right[x] is not None:
                            new_set = new_set | set(
                                Dicts.right[x])  #  use prebuilt dict

                    if new_set == set():
                        return inversion_result
                    else:
                        token_str[idx].set_value(new_set)

                else:
                    new_set = set()
                    for x in token.get_value():
                        if Dicts.right[x] is not None:
                            new_set = new_set | set(Dicts.right[x])

                    if new_set == set():
                        return inversion_result
                    else:
                        token_str[idx].set_value(new_set, token.start,
                                                 token.end)

            inversion_result.add(token_str)
            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_L_command(token_str, rule, just_check=False, enable_regex=False):
        """ L   shift each character left, by keyboard: "Crack96" -> "Xeaxj85"
        
        Inversion Idea:
            we shift each character right by keyboard.
            We note that some are not perfectly shifted right, and that's due to how they are initially shifted left.
            We also note that a, q, and z map to themselves.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == False:
                return Invertibility.INVERTIBLE
            else:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        if enable_regex == False:
            for idx, token in enumerate(token_str):
                if token.is_range():
                    new_set = set()
                    for x in token.get_value():
                        if Dicts.left[x] is not None:
                            new_set = new_set | set(
                                Dicts.left[x])  # use prebuilt dict

                    if new_set == set():
                        return inversion_result
                    else:
                        token_str[idx].set_value(new_set)

                else:
                    new_set = set()
                    for x in token.get_value():
                        if Dicts.left[x] is not None:
                            new_set = new_set | set(Dicts.left[x])

                    if new_set == set():
                        return inversion_result
                    else:
                        token_str[idx].set_value(new_set, token.start,
                                                 token.end)

            inversion_result.add(token_str)
            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_one_insertion(token_str, starting_position, params):
        r""" Invert Insertion to Single Position.
        
        Say the transformation is A0"[a-z][A-Z]", the input Should Be 
        (password, 0, [set(a-z),set(A-Z)]). Invert this insertion by removing the chars
        
        Args:
            starting_position: a parsed integer denoting position.
            param: a set of appended string.
        
        Returns:
            None if failed, otherwise token_str
        """
        ret_token_str = TokenString()  # Get a copy and modify it.

        # The length of words inserted. A0"[a-z][A-Z]" = 2
        insertion_range = len(params)

        # Not Long Enough
        # insert a string longer than the tokenstring size, rejected
        # If you don't want to allow empty string to be produced here, change
        # to >=.
        if insertion_range > len(token_str.tokens):
            return None

        if starting_position >= 0:

            # start 0 insert 1  = 1. If empty length = 1 <- how can both if
            # empty and if has one = 1? I think this is throwing one off.
            ending_position = starting_position + insertion_range

            # Means append, handles cases like: "0" + A3"12345" -> "012345".
            if ending_position >= len(token_str.tokens):
                ending_position = len(token_str.tokens)

        else:  # starting_position < 0

            # the opposite way, if insert at -1, length 3, it is (-4) to (-1)
            ending_position = starting_position - insertion_range

            # swap
            starting_position, ending_position = ending_position, starting_position

            # Convert to positive positions here.
            # Means append, if A(-4)"123" and you get b123, starting position
            # -4 - 3 = -7.
            if abs(starting_position) > len(token_str.tokens):
                ending_position = len(token_str.tokens)
            else:
                ending_position = len(token_str.tokens) + ending_position

        for i in range(insertion_range):
            token = token_str[ending_position - i - 1]  # For current insertion

            if token.is_range():
                intersect_set = token.get_value() & set(
                    params[insertion_range - i - 1])
                if intersect_set == set():
                    return None
                else:
                    pass

        # Remove the inserted part
        ret_token_str.append_tokens(
            token_str[:ending_position - insertion_range])
        ret_token_str.append_tokens(token_str[ending_position:])
        return ret_token_str

    @staticmethod
    def invert_dollar_X_command(token_str,
                                rule,
                                just_check=False,
                                enable_regex=False):
        """ $X  Append character X to the word 

        Inversion Idea:
            remove the inserted strings.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            return Invertibility.INVERTIBLE

        if enable_regex == False:
            return Inversion.invert_i_N_X_command(
                token_str, ["i", len(token_str) - 1, rule[1]], just_check,
                enable_regex)

        else:
            inversion_result = InversionResult()
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_caret_X_command(token_str,
                               rule,
                               just_check=False,
                               enable_regex=False):
        """ ^X prefix the word with character X

        Inversion Idea:
            remove the inserted string
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """

        return Inversion.invert_i_N_X_command(token_str, ["i", "0", rule[1]],
                                              just_check, enable_regex)

    @staticmethod
    def invert_i_N_X_command(token_str,
                             rule,
                             just_check=False,
                             enable_regex=False):
        """ iNX insert character X in position N and shift the rest right 
    
        Inversion Idea:
            remove the inserted string
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check:
            if enable_regex == False:
                try:
                    N = convert_str_length_to_int(rule[1])
                    return Invertibility.INVERTIBLE
                except BaseException:
                    return Invertibility.UNINVERTIBLE
            else:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()
        N = convert_str_length_to_int(rule[1])
        X = rule[2]

        if enable_regex == False:
            # If token_str_length is max_length, it could be itself
            if len(token_str) + 1 > RUNTIME_CONFIG['max_password_length']:
                inversion_result.add(deepcopy(token_str))

            # HC Style Doesn't Append If Too Short
            if RUNTIME_CONFIG.is_hc():
                # Length == 0 covered
                if len(token_str) < N:
                    inversion_result.add(token_str)
                    return inversion_result

                if len(token_str) == N:  # It's no possible to get length = N.
                    return inversion_result

                # guranteed len(token_str) >= N + 1
                res = Inversion.invert_one_insertion(token_str, N, [X])

                if res is not None:
                    inversion_result.add(res)

            else:
                if len(token_str
                      ) <= 0:  # will insert one string anyhow, require len >= 1
                    return inversion_result

                # guranteed len(token_str) >= 1
                res = Inversion.invert_one_insertion(token_str, N, [X])

                if res is not None:
                    inversion_result.add(res)
            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_A_N_str_command(token_str,
                               rule,
                               just_check=False,
                               enable_regex=False):
        """ AN"STR" insert string STR into the word at position N
    
        Inversion Idea:
            remove the inserted string
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check:
            if enable_regex == False:
                try:
                    convert_str_length_to_int(rule[1])
                    return Invertibility.INVERTIBLE
                except BaseException:
                    return Invertibility.UNINVERTIBLE
            else:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:
            # If token_str_length is max_length, it could be itself
            if len(token_str) + \
                    len(rule[2:]) > RUNTIME_CONFIG['max_password_length']:
                inversion_result.add(deepcopy(token_str))

            if len(token_str
                  ) <= 0:  # will insert one string anyhow, require len >= 1
                return inversion_result

            # guranteed len(token_str) >= 1
            token_str = Inversion.invert_one_insertion(token_str, N, rule[2:])

            if token_str is not None:
                inversion_result.add(token_str)

            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_T_N_command(token_str,
                           rule,
                           just_check=False,
                           enable_regex=False):
        """
        TN  Toggles case of char at position N

        Inversion Idea:
            toggle the case at position N
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            try:
                N = convert_str_length_to_int(rule[1])
                return Invertibility.INVERTIBLE
            except BaseException:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:

            length = len(token_str)

            if length == 0:  # Nothing to do
                inversion_result.add(token_str)
                return inversion_result

            if N > length - 1:  # not toggled
                inversion_result.add(token_str)
                return inversion_result

            token_str[N].set_value({
                Dicts.toggle.setdefault(x, x) for x in token_str[N].get_value()
            })

            inversion_result.add(token_str)
            return inversion_result

        else:
            # For length >= N, find the Nth position.
            # For length < N, do nothing.
            # There are two ways to do this, one is break the tokenstring
            # Second set external length.
            # Let's try second method first
            less_than = deepcopy(token_str)
            less_than.set_max_len(N + 1)

            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_or_equal = RegexTokenString.fix_first_N_position(
                token_str, N + 1)
            for one_ts in greater_or_equal:
                one_ts[N].set_value({
                    Dicts.toggle.setdefault(x, x)
                    for x in one_ts[N].get_value()
                })
                inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_prime_N_command(token_str,
                               rule,
                               just_check=False,
                               enable_regex=False):
        """ 'N  Truncates word at position N

        Inversion Idea:
            If word is longer than N, reject because rule hasn't been implemented
            If word is equal to N, add a regex all char to the end
            If word is shorter than N, return that word.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            try:
                N = convert_str_length_to_int(rule[1])
                return Invertibility.UNINVERTIBLEOPTIMIZATBLE
            except BaseException:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:

            length = len(token_str)

            if length < N:  # length < N, can only be itself.
                inversion_result.add(token_str)
                return inversion_result

            elif length == N:
                # Length == 4, either itself, or add some string that requires
                # regex. return None to ask HC to handle.
                inversion_result.set_status(InversionStatus.OUTSCOPE)
                return inversion_result

            else:  # Length > N, rejected
                return inversion_result

        else:
            # For prime N, length = N is the most valid
            # Less than N, it still what it is.
            less_than = deepcopy(token_str)
            less_than.set_max_len(N)  # <N, do nothing

            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_or_equal = RegexTokenString.enumerate_N(token_str,
                                                            N)  # get all =N
            for one_ts in greater_or_equal:
                one_ts.tokens += [Token(Dicts.classes['z'], 0, float("inf"))]
                one_ts.reset_max_len()
                inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_p_N_command(token_str,
                           rule,
                           just_check=False,
                           enable_regex=False):
        """ pN  Appends duplicated word N times: pass -> (p2) passpasspass

        Inversion Idea:
            divide the word into N + 1 equal sections. If it's not divisible, then rule not implemented
            Make sure each section is the exact same, then return the original.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                try:
                    N = convert_str_length_to_int(rule[1])
                    return Invertibility.INVERTIBLE
                except BaseException:
                    return Invertibility.UNINVERTIBLE

        N = convert_str_length_to_int(rule[1]) + 1

        if enable_regex == False:
            # Initialize Utilities.
            inversion_result = InversionResult()

            if N == 1:
                inversion_result.add(token_str)
                return inversion_result

            length = len(token_str)

            if length == 0:  # Length = 0. No duplicate.
                inversion_result.add(token_str)
                return inversion_result

            div_size = 0
            index = 0

            # if a word is larger than max_length, it can't be printed
            if length * N > RUNTIME_CONFIG['max_password_length']:
                original_ts = deepcopy(token_str)
                inversion_result.add(original_ts)

            if length % N == 0:  # Not N's multiply
                # abcabcad p2
                div_size = int(length / N)
                index = div_size
            else:  # Reject what's below
                return inversion_result

            # for idx in range(length): #I am aware that this will check the
            # original word against itself... also: doing 0 indexing
            while index < length:
                left_set = set(token_str[index % div_size].get_value())
                right_set = set(token_str[index].get_value())
                intersect_set = left_set.intersection(right_set)

                if intersect_set == set():
                    # dcbdcbdcc p2
                    return inversion_result
                else:
                    # nflnflnfl p2
                    if token_str[index].is_regex() and token_str[
                            index % div_size].is_regex():
                        start = max(token_str[index].start,
                                    token_str[index % div_size].start)
                        end = min(token_str[index].end,
                                  token_str[index % div_size].end)
                        token_str[index] = Token(intersect_set, start, end)
                    else:
                        token_str[index % div_size] = Token(intersect_set)
                index += 1

            token_str.tokens = token_str.tokens[:div_size]
            token_str.length = div_size

            inversion_result.add(token_str)

            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_z_N_command(token_str,
                           rule,
                           just_check=False,
                           enable_regex=False):
        """ zN  Duplicates first character N times: hi -> (z2) hhhi

        Inversion Idea:
            check the first N characters.
            If they are all the same as the N+1th character, return
            Otherwise reject.    
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            try:
                N = convert_str_length_to_int(rule[1])
                return Invertibility.INVERTIBLE
            except BaseException:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:
            if N == 0:
                inversion_result.add(token_str)
                return inversion_result

            length = len(token_str)

            if length == 0:  # Not word to duplicate
                inversion_result.add(token_str)
                return inversion_result

            # Potentially not duplicated
            if length + N > RUNTIME_CONFIG['max_password_length']:
                # abcdefghijklmnopqrstuvwxyz z8
                overlarge_ts = deepcopy(token_str)
                inversion_result.add(overlarge_ts)

            if length < N + 1:  # Not possible, below rejected
                # adf z3
                return inversion_result

            # due to zero indexing, should give the N+1st char in word
            match = set(token_str[N].get_value())

            intersect_set = set()

            for idx in range(N):
                # aaabc z2
                value = set(token_str[idx].get_value())
                intersect_set = match.intersection(value)
                if intersect_set == set():
                    return inversion_result
                match = intersect_set

            token_str.tokens = token_str.tokens[N:]
            token_str[0].set_value(intersect_set)
            token_str.length = length - N
            inversion_result.add(token_str)

            return inversion_result

        else:
            if N == 0:
                inversion_result.add(token_str)
                return inversion_result

            less_than = deepcopy(token_str)
            less_than.set_max_len(1)

            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_than = deepcopy(token_str)
            greater_than.set_min_len(RUNTIME_CONFIG['max_password_length'] - N +
                                     1)
            if greater_than.is_valid():
                inversion_result.add(greater_than)

            greater_or_equal = RegexTokenString.fix_first_N_position(
                token_str, N + 1)
            for one_ts in greater_or_equal:

                # remember to decrease input len requirement window
                one_ts.decrease_window(N)

                match = set(one_ts[N].get_value())
                for idx in range(N):
                    value = set(one_ts[idx].get_value())
                    intersect_set = match.intersection(value)
                    if intersect_set == set():
                        break
                    match = intersect_set

                else:
                    one_ts.tokens = one_ts.tokens[N:]
                    one_ts[0].set_value(intersect_set)
                    inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_Z_N_command(token_str,
                           rule,
                           just_check=False,
                           enable_regex=False):
        """ ZN  Duplicates last character N times: hello -> (Z2) hellooo

        Inversion Idea:
            Check the last N characters.
            If they are all the same as the length - Nth char (len - N - 1 if 0 indexing), return
            Otherwise, reject
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            try:
                N = convert_str_length_to_int(rule[1])
                return Invertibility.INVERTIBLE
            except BaseException:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:

            if N == 0:
                inversion_result.add(token_str)
                return inversion_result

            length = len(token_str)

            if length == 0:
                inversion_result.add(token_str)
                return inversion_result

            # Potentially not duplicated
            if length + N > RUNTIME_CONFIG['max_password_length']:
                overlarge_ts = deepcopy(token_str)
                inversion_result.add(overlarge_ts)

            if length < N + 1:  # Below Rejected, not possible.
                return inversion_result

            # this is the set you reference
            match = set(token_str[length - N - 1].get_value())

            for idx in range(N):
                # aaabccc
                value = set(token_str[length - idx - 1].get_value())
                intersect_set = match.intersection(value)
                if intersect_set == set():
                    return inversion_result
                match = intersect_set

            token_str.tokens = token_str.tokens[:(length - N)]
            token_str[-1].set_value(intersect_set)
            token_str.length = token_str.length - N

            inversion_result.add(token_str)
            return inversion_result

        else:
            if N == 0:
                inversion_result.add(token_str)
                return inversion_result

            less_than = deepcopy(token_str)
            less_than.set_max_len(1)

            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_than = deepcopy(token_str)
            greater_than.set_min_len(RUNTIME_CONFIG['max_password_length'] - N +
                                     1)
            if greater_than.is_valid():
                inversion_result.add(greater_than)

            greater_or_equal = RegexTokenString.fix_last_N_position(
                token_str, N + 1)
            for one_ts in greater_or_equal:
                # remember to decrease input len requirement window
                one_ts.decrease_window(N)

                # this is the set you reference
                match = set(one_ts[-1].get_value())

                for idx in range(2, N + 2):
                    # aaabccc
                    value = set(one_ts[-idx].get_value())
                    intersect_set = match.intersection(value)
                    if intersect_set == set():
                        break
                    match = intersect_set

                else:
                    one_ts.tokens = one_ts.tokens[:-N]
                    one_ts[-1].set_value(intersect_set)
                    inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_L_N_command(token_str,
                           rule,
                           just_check=False,
                           enable_regex=False):
        """ LN  Bitwise left shift char at position N
        
        Inversion Idea:
            Bitwise right shift char at pos N.
            HC seems to convert to ascii, bitwise shift, then convert back.
            Doesn't seem to be a max where they just delete the chars.
            If word is smaller than N + 1, return
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            try:
                N = convert_str_length_to_int(rule[1])
                return Invertibility.INVERTIBLE
            except BaseException:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:

            length = len(token_str)

            if length < N + 1:
                inversion_result.add(token_str)
                return inversion_result

            bitwise = set(
                ord(x) for x in token_str[N].get_value() if (ord(x) % 2 != 1))
            if bitwise == set(
            ):  # In case of false results. Because shifting left initially, last bit should be 0. If not, return!
                return inversion_result

            val_1 = set(x >> 1 for x in bitwise)
            val_2 = set((x + 256) >> 1 for x in bitwise)

            char_set = set(chr(x) for x in (val_1 | val_2))
            token_str[N].set_value(char_set)

            inversion_result.add(token_str)
            return inversion_result

        else:
            # For length >= N, find the Nth position.
            # For length < N, do nothing.
            # There are two ways to do this, one is break the tokenstring
            # Second set external length.
            # Let's try second method first
            less_than = deepcopy(token_str)
            less_than.set_max_len(N + 1)

            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_or_equal = RegexTokenString.fix_first_N_position(
                token_str, N + 1)
            for one_ts in greater_or_equal:

                bitwise = set(
                    ord(x) for x in one_ts[N].get_value() if (ord(x) % 2 != 1))
                if bitwise == set(
                ):  # In case of false results. Because shifting left initially, last bit should be 0. If not, return!
                    continue

                val_1 = set(x >> 1 for x in bitwise)
                val_2 = set((x + 256) >> 1 for x in bitwise)

                char_set = set(chr(x) for x in (val_1 | val_2))
                one_ts[N].set_value(char_set)
                inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_R_N_command(token_str,
                           rule,
                           just_check=False,
                           enable_regex=False):
        """ RN  Bitwise right shift char at position N
        
        Inversion Idea:
            Bitwise left shift char at pos N
            HC seems to convert to ascii, bitwise shift, then convert back.
            Doesn't seem to be a max where they just delete the chars.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            try:
                N = convert_str_length_to_int(rule[1])
                return Invertibility.INVERTIBLE
            except BaseException:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:

            length = len(token_str)

            # Cover by length < N + 1

            if length < N + 1:
                inversion_result.add(token_str)
                return inversion_result

            val = set(ord(x) for x in token_str[N].get_value() if ord(x) <= 127)
            if val == set():
                return inversion_result

            char_set = set(chr(x * 2) for x in val) | set(
                chr(x * 2 + 1) for x in val)
            token_str[N] = Token(char_set)

            inversion_result.add(token_str)
            return inversion_result

        else:
            # For length >= N, find the Nth position.
            # For length < N, do nothing.
            # There are two ways to do this, one is break the tokenstring
            # Second set external length.
            # Let's try second method first
            less_than = deepcopy(token_str)
            less_than.set_max_len(N + 1)

            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_or_equal = RegexTokenString.fix_first_N_position(
                token_str, N + 1)
            for one_ts in greater_or_equal:
                val = set(
                    ord(x) for x in one_ts[N].get_value() if ord(x) <= 127)
                if val == set():
                    continue

                char_set = set(chr(x * 2) for x in val) | set(
                    chr(x * 2 + 1) for x in val)
                one_ts[N].set_value(char_set)
                inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_plus_N_command(token_str,
                              rule,
                              just_check=False,
                              enable_regex=False):
        """ +N  Increment char at position N by 1 ascii value
        
        Inversion Idea:
            Decrement char at position N by 1 ascii value.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            try:
                N = convert_str_length_to_int(rule[1])
                return Invertibility.INVERTIBLE
            except BaseException:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:

            length = len(token_str)

            # Length == 0 covered

            if len(token_str) < N + 1:
                inversion_result.add(token_str)
                return inversion_result

            ascii_set = set(
                chr((ord(x) - 1 + 256) % 256) for x in token_str[N].get_value())
            token_str[N].set_value(ascii_set)
            inversion_result.add(token_str)

            return inversion_result

        else:
            less_than = deepcopy(token_str)
            less_than.set_max_len(N + 1)

            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_or_equal = RegexTokenString.fix_first_N_position(
                token_str, N + 1)
            for one_ts in greater_or_equal:
                ascii_set = set(
                    chr((ord(x) - 1 + 256) % 256)
                    for x in one_ts[N].get_value())
                one_ts[N].set_value(ascii_set)
                inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_minus_N_command(token_str,
                               rule,
                               just_check=False,
                               enable_regex=False):
        """
        -N  Decrement char at position N by 1 ascii value

        Inversion Idea:
            Increment char at position N by 1 ascii value.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            try:
                N = convert_str_length_to_int(rule[1])
                return Invertibility.INVERTIBLE
            except BaseException:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:

            length = len(token_str)

            # Length == 0 covered

            if len(token_str) < N + 1:
                inversion_result.add(token_str)
                return inversion_result

            ascii_set = set(
                chr((ord(x) + 1) % 256) for x in token_str[N].get_value())
            token_str[N].set_value(ascii_set)
            inversion_result.add(token_str)

            return inversion_result

        else:
            less_than = deepcopy(token_str)
            less_than.set_max_len(N + 1)

            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_or_equal = RegexTokenString.fix_first_N_position(
                token_str, N + 1)
            for one_ts in greater_or_equal:
                ascii_set = set(
                    chr((ord(x) + 1) % 256) for x in one_ts[N].get_value())
                one_ts[N].set_value(ascii_set)
                inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_period_N_command(token_str,
                                rule,
                                just_check=False,
                                enable_regex=False):
        """ .N  Replace char at position N with the char at position N + 1
        
        Inversion Idea:
            check to make sure the Nth and N + 1th position have the same char in it.
            If so, place all char set at position N.
            If there is no position N + 1, word is returned unchanged
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        

        """
        if just_check == True:
            try:
                N = convert_str_length_to_int(rule[1])
                return Invertibility.INVERTIBLE
            except BaseException:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:

            length = len(token_str)

            # Length == 0 covered

            if length - 1 < N + 1:
                inversion_result.add(token_str)
                return inversion_result

            N_char = set(token_str[N].get_value())
            N_plus_char = set(token_str[N + 1].get_value())
            intersect_set = N_char.intersection(N_plus_char)

            if intersect_set == set():
                return inversion_result
            else:
                token_str[N + 1] = Token(intersect_set)
                token_str[N] = Token(Dicts.classes['z'])
                inversion_result.add(token_str)

            return inversion_result

        else:
            less_than = deepcopy(token_str)
            less_than.set_max_len(N + 2)

            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_or_equal = RegexTokenString.fix_first_N_position(
                token_str, N + 2)
            for one_ts in greater_or_equal:
                N_char = set(one_ts[N].get_value())
                N_plus_char = set(one_ts[N + 1].get_value())
                intersect_set = N_char.intersection(N_plus_char)

                if intersect_set == set():
                    continue
                else:
                    one_ts[N + 1].set_value(intersect_set)
                    one_ts[N].set_value(Dicts.classes['z'])
                    inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_comma_N_command(token_str,
                               rule,
                               just_check=False,
                               enable_regex=False):
        """ ,N  Replace char at position N with the char at position N - 1

        Inversion Idea:
            place all char set at position N
            If there is no position N - 1, word is returned unchanged
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            try:
                N = convert_str_length_to_int(rule[1])
                return Invertibility.INVERTIBLE
            except BaseException:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:

            length = len(token_str)

            # Length == 0 covered

            if N == 0:  # If N == 0, no operation is performed.
                inversion_result.add(token_str)
                return inversion_result

            if length - 1 < N:  # If N >= len, no operation is performed.
                inversion_result.add(token_str)
                return inversion_result

            N_char = set(token_str[N].get_value())
            N_minus_char = set(token_str[N - 1].get_value())
            intersect_set = N_char.intersection(N_minus_char)

            if intersect_set == set():
                return inversion_result
            else:
                token_str[N - 1] = Token(intersect_set)
                token_str[N] = Token(Dicts.classes['z'])
                inversion_result.add(token_str)

            return inversion_result

        else:
            if N == 0:  # If N == 0, no operation is performed.
                inversion_result.add(token_str)
                return inversion_result

            less_than = deepcopy(token_str)
            less_than.set_max_len(N + 1)

            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_or_equal = RegexTokenString.fix_first_N_position(
                token_str, N + 1)
            for one_ts in greater_or_equal:
                N_char = set(one_ts[N].get_value())
                N_minus_char = set(one_ts[N - 1].get_value())
                intersect_set = N_char.intersection(N_minus_char)

                if intersect_set == set():
                    continue
                else:
                    one_ts[N - 1].set_value(intersect_set)
                    one_ts[N].set_value(Dicts.classes['z'])
                    inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_y_N_command(token_str,
                           rule,
                           just_check=False,
                           enable_regex=False):
        """ yN  Duplicates first N characters: hello -> (y2) hehello

        Inversion Idea:
            Take the first N characters and the first N characters after that
            Compare the two. If they match, return, otherwise reject.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        
        """
        if just_check == True:
            try:
                N = convert_str_length_to_int(rule[1])
                return Invertibility.INVERTIBLE
            except BaseException:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:

            if N == 0:
                inversion_result.add(token_str)
                return inversion_result

            length = len(token_str)

            # Potentially not duplicated
            if length + N > RUNTIME_CONFIG['max_password_length']:
                overlarge_ts = deepcopy(token_str)
                inversion_result.add(overlarge_ts)

            if length < N:  # Not duplicated
                inversion_result.add(token_str)

            if length < 2 * N:  # Below Rejected.
                return inversion_result

            add_str = token_str[:N]
            check_str = token_str[N:2 * N]
            for idx in range(N):
                # hehello
                left_set = set(add_str[idx].get_value())
                right_set = set(check_str[idx].get_value())
                intersect_set = left_set.intersection(right_set)
                if intersect_set == set():
                    return inversion_result
                else:
                    token_str[N + idx].set_value(intersect_set)

            token_str.tokens = token_str.tokens[N:]
            token_str.length = length - N
            inversion_result.add(token_str)
            return inversion_result

        else:
            if N == 0:
                inversion_result.add(token_str)
                return inversion_result

            less_than = deepcopy(token_str)
            less_than.set_max_len(N)  # do nothing if length < N

            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_than = deepcopy(token_str)
            greater_than.set_min_len(RUNTIME_CONFIG['max_password_length'] - N +
                                     1)
            if greater_than.is_valid():
                inversion_result.add(greater_than)

            greater_or_equal = RegexTokenString.fix_first_N_position(
                token_str, N * 2)
            for one_ts in greater_or_equal:
                # remember to decrease input len requirement window
                one_ts.decrease_window(N)

                add_str = one_ts[:N]
                check_str = one_ts[N:2 * N]

                for v in zip(add_str, check_str):
                    inter_set = v[0].get_value().intersection(v[1].get_value())
                    if inter_set == set():
                        break
                    else:
                        v[1].set_value(inter_set)

                else:
                    one_ts.tokens = one_ts.tokens[N:]
                    inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_Y_N_command(token_str,
                           rule,
                           just_check=False,
                           enable_regex=False):
        """ YN  Duplicates last N characters: hello -> (Y2) hellolo

        Inversion Idea:
            Take the last N characters and the N characters before that.
            Commpare the two. If they match, return. Otherwise, reject.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """

        if just_check == True:
            try:
                N = convert_str_length_to_int(rule[1])
                return Invertibility.INVERTIBLE
            except BaseException:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:
            if N == 0:
                inversion_result.add(token_str)
                return inversion_result

            length = len(token_str)

            # Potentially not duplicated
            if length + N > RUNTIME_CONFIG['max_password_length']:
                overlarge_ts = deepcopy(token_str)
                inversion_result.add(overlarge_ts)

            if length < N:  # Not duplicated
                inversion_result.add(token_str)

            if length < 2 * N:  # Rejected.
                return inversion_result

            add_str = token_str[-N:]
            check_str = token_str[-2 * N:-N]
            for idx in range(N):
                left_set = set(add_str[idx].get_value())
                right_set = set(check_str[idx].get_value())
                intersect_set = left_set.intersection(right_set)
                if intersect_set == set():
                    return inversion_result
                else:
                    token_str[length - 2 * N + idx] = Token(intersect_set)
            token_str.tokens = token_str.tokens[:-N]
            token_str.length = length - N
            inversion_result.add(token_str)
            return inversion_result

        else:
            if N == 0:
                inversion_result.add(token_str)
                return inversion_result

            less_than = deepcopy(token_str)
            less_than.set_max_len(N)  # do nothing if length < N

            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_than = deepcopy(token_str)
            greater_than.set_min_len(RUNTIME_CONFIG['max_password_length'] - N +
                                     1)
            if greater_than.is_valid():
                inversion_result.add(greater_than)

            greater_or_equal = RegexTokenString.fix_last_N_position(
                token_str, N * 2)
            for one_ts in greater_or_equal:

                # remember to decrease input len requirement window
                one_ts.decrease_window(N)

                add_str = one_ts[-N:]
                check_str = one_ts[-2 * N:-N]

                for v in zip(add_str, check_str):
                    inter_set = v[0].get_value().intersection(v[1].get_value())

                    if inter_set == set():
                        break
                    else:
                        v[1].set_value(inter_set)

                else:
                    one_ts.tokens = one_ts.tokens[:-N]
                    inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_x_N_M_command(token_str,
                             rule,
                             just_check=False,
                             enable_regex=False):
        """ xNM Extracts M chars, starting at position N

        Inversion Idea:
            Requires regex.
            Add an allchar all length regex char to the front and back of the word.
            For xNM to valid, len(string) >= N + M
            If length < M, it cannot from xNM, just itself
            If length == M, it could be from xNM + itself given any N.
            If N + M > length > M, it cannot from xNM, could be just from itself.
            If length >= N + M, rejected
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """

        if just_check == True:
            if enable_regex == False:
                # for JtR don't optimize
                if RUNTIME_CONFIG.is_jtr():
                    return Invertibility.UNINVERTIBLE

                try:
                    N = convert_str_length_to_int(rule[1])
                    M = convert_str_length_to_int(rule[2])
                    return Invertibility.UNINVERTIBLEOPTIMIZATBLE
                except BaseException:
                    return Invertibility.UNINVERTIBLE
            else:
                return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        M = convert_str_length_to_int(rule[2])

        if enable_regex == False:

            length = len(token_str)

            # why max(N + 1, N + M)? M = 0 special case
            # length < M or max(N + 1, N + M) > length > M,can only be itself.
            if length < M or M < length < max(N + 1, N + M):
                inversion_result.add(token_str)
                return inversion_result

            elif length == M:
                # Length == M, either itself, or add some string that requires
                # regex. return None to ask HC to handle.
                inversion_result.set_status(InversionStatus.OUTSCOPE)
                return inversion_result

            else:  # Length > N, rejected
                return inversion_result

        else:

            # For length < M and max(N + 1, N + M) > length > M, lazy eval
            lazy_1 = deepcopy(token_str)
            lazy_1.set_max_len(M)  # <N, do nothing
            if lazy_1.is_valid():
                inversion_result.add(lazy_1)

            lazy_2 = deepcopy(token_str)
            # max(N + 1, N + M) > length > M, do nothing
            lazy_2.set_max_len(max(N + 1, N + M))
            lazy_2.set_min_len(M + 1)
            if lazy_2.is_valid():
                inversion_result.add(lazy_2)

            greater_or_equal = RegexTokenString.enumerate_N(
                token_str, M)  # get all =M, or itself
            for one_ts in greater_or_equal:
                inversion_result.add(deepcopy(one_ts))  # itself, or some regex
                one_ts.tokens = [Token(Dicts.classes['z']) for _ in range(N)
                                ] + one_ts.tokens + [
                                    Token(Dicts.classes['z'], 0, float("inf"))
                                ]
                one_ts.set_min_len(N)  # N?
                one_ts.reset_max_len()
                inversion_result.add(one_ts)

            return inversion_result

    @staticmethod
    def invert_o_N_X_command(token_str,
                             rule,
                             just_check=False,
                             enable_regex=False):
        """ oNX Overwrites char at position N with char X

        Inversion Idea:
            If char at position N is X, replace with allchar set
            Otherwise reject
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            try:
                N = convert_str_length_to_int(rule[1])
                return Invertibility.INVERTIBLE
            except BaseException:
                return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])
        X = rule[2]

        if enable_regex == False:

            length = len(token_str)

            # Nothing to do.
            if length == 0:
                inversion_result.add(token_str)
                return inversion_result

            if N >= len(token_str):
                inversion_result.add(token_str)
            else:
                if X in set(token_str[N].get_value()):
                    token_str[N] = Token(Dicts.classes['z'])
                    inversion_result.add(token_str)
                else:
                    return inversion_result

            return inversion_result

        else:
            less_than = deepcopy(token_str)
            less_than.set_max_len(N + 1)

            if less_than.is_valid():
                inversion_result.add(less_than)

            greater_or_equal = RegexTokenString.fix_first_N_position(
                token_str, N + 1)
            for one_ts in greater_or_equal:
                if X in set(one_ts[N].get_value()):
                    one_ts[N].set_value(Dicts.classes['z'])
                    inversion_result.add(one_ts)
                else:
                    continue

            return inversion_result

    @staticmethod
    def invert_O_N_M_command(token_str,
                             rule,
                             just_check=False,
                             enable_regex=False):
        """ ONM Deletes M chars, starting at position N

        Inversion Idea:
            add a regex char for M characters.
            If length is less than N-1, keep.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """

        if just_check == True:
            if enable_regex == False:
                try:
                    N = convert_str_length_to_int(rule[1])
                    M = convert_str_length_to_int(rule[2])
                    if M <= RUNTIME_CONFIG['m_threshold']:
                        return Invertibility.INVERTIBLE
                    else:
                        return Invertibility.UNINVERTIBLE
                except BaseException:
                    return Invertibility.UNINVERTIBLE
            else:
                return Invertibility.UNINVERTIBLE

        N = convert_str_length_to_int(rule[1])
        M = convert_str_length_to_int(rule[2])

        if enable_regex == False:
            # If M > 3, below shohuld not be executed.
            if M > RUNTIME_CONFIG['m_threshold']:
                raise Exception("M should be <= {}".format(
                    RUNTIME_CONFIG['m_threshold']))

            inversion_result = InversionResult()
            token_str = deepcopy(token_str)

            if len(token_str) < N:  # If Length < N, can only be itself
                inversion_result.add(token_str)
                return inversion_result

            else:  # >= N

                # If Length < N + M, can either be itself, or something after
                # deleted
                if len(token_str) < (N + M):
                    original_ts = deepcopy(token_str)
                    inversion_result.add(original_ts)

                    token_str.tokens = token_str.tokens[:N] + [
                        Token(Dicts.classes['z'])
                    ] * M + token_str.tokens[N:]
                    token_str.length += M
                    inversion_result.add(token_str)

                    return inversion_result
                # Length >= (N + M) and Length <= RUNTIME_CONFIG['max_password_length'] - M
                elif len(
                        token_str) <= RUNTIME_CONFIG['max_password_length'] - M:
                    # Add something in between
                    token_str.tokens = token_str.tokens[:N] + [
                        Token(Dicts.classes['z'])
                    ] * M + token_str.tokens[N:]
                    token_str.length += M
                    inversion_result.add(token_str)
                    return inversion_result

                else:  # Else it is not possible, rejected
                    return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_asterisk_N_M_command(token_str,
                                    rule,
                                    just_check=False,
                                    enable_regex=False):
        r""" *NM Swaps character at position N with a character at position M. (indexing starting at 0)
        
        Inversion Idea:
            Reswap those two characters and return.
            If word is shorter than the position of either N or M, return word.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                try:
                    N = convert_str_length_to_int(rule[1])
                    M = convert_str_length_to_int(rule[2])
                    return Invertibility.INVERTIBLE
                except BaseException:
                    return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()
        N = convert_str_length_to_int(rule[1])
        M = convert_str_length_to_int(rule[2])

        if enable_regex == False:
            length = len(token_str)

            if length == 0:  # nothing to swap
                inversion_result.add(token_str)
                return inversion_result

            if length < N + 1 or length < M + 1:
                inversion_result.add(token_str)
                return inversion_result

            token_str[M], token_str[N] = token_str[N], token_str[M]

            inversion_result.add(token_str)
            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_M_command(token_str, rule, just_check=False, enable_regex=False):
        """ Memory Command M

        Inversion Idea:
            None
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """

        if just_check:
            return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()
        inversion_result.set_status(InversionStatus.OUTSCOPE)
        return inversion_result

    @staticmethod
    def invert_Q_command(token_str, rule, just_check=False, enable_regex=False):
        """ Memory Command Q

        Inversion Idea:
            None
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check:
            return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()
        inversion_result.set_status(InversionStatus.OUTSCOPE)
        return inversion_result

    @staticmethod
    def invert_X_N_M_I_command(token_str,
                               rule,
                               just_check=False,
                               enable_regex=False):
        """ Memory Command XNMI

        Inversion Idea:
            None
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check:
            return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()
        inversion_result.set_status(InversionStatus.OUTSCOPE)
        return inversion_result

    @staticmethod
    def invert_4_command(token_str, rule, just_check=False, enable_regex=False):
        """ Memory Command 4

        Inversion Idea:
            None
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()
        inversion_result.set_status(InversionStatus.OUTSCOPE)
        return inversion_result

    @staticmethod
    def invert_6_command(token_str, rule, just_check=False, enable_regex=False):
        """ Memory Command 6

        Inversion Idea:
            None
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()
        inversion_result.set_status(InversionStatus.OUTSCOPE)
        return inversion_result

    @staticmethod
    def invert_v_V_N_M_command(token_str,
                               rule,
                               just_check=False,
                               enable_regex=False):
        """ Memory Command vVNM

        Inversion Idea:
            None
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check:
            return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()
        inversion_result.set_status(InversionStatus.OUTSCOPE)
        return inversion_result

    @staticmethod
    def invert_mode_command(token_str,
                            rule,
                            just_check=False,
                            enable_regex=False):
        """ Mode Commands 1 or 2

        Inversion Idea:
            None
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check:
            return Invertibility.INVERTIBLE

        inversion_result = InversionResult()
        return inversion_result

    @staticmethod
    def invert_less_than_N_command(token_str,
                                   rule,
                                   just_check=False,
                                   enable_regex=False):
        """ <N   Reject unless word is less than N chars long
        
        Inversion Idea:
            HC: Reject unless word is less or equal than N chars long
            JtR: Reject unless word is less than N chars long
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                try:
                    N = convert_str_length_to_int(rule[1])
                    return Invertibility.INVERTIBLE
                except BaseException:
                    return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:

            if RUNTIME_CONFIG.is_jtr():
                if len(token_str) < N:
                    inversion_result.add(token_str)

            else:
                if len(token_str) <= N:
                    inversion_result.add(token_str)

            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_greater_than_N_command(token_str,
                                      rule,
                                      just_check=False,
                                      enable_regex=False):
        """ >N  Reject unless word is greater than N chars long
        
        Inversion Idea:
            HC: Reject unless word is greater or equal than N chars long
            JtR: Reject unless word is greater than N chars long
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                try:
                    N = convert_str_length_to_int(rule[1])
                    return Invertibility.INVERTIBLE
                except BaseException:
                    return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()

        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:

            if RUNTIME_CONFIG.is_jtr():

                if len(token_str) > N:
                    inversion_result.add(token_str)

            else:

                if len(token_str) >= N:
                    inversion_result.add(token_str)

            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_underscore_N_command(token_str,
                                    rule,
                                    just_check=False,
                                    enable_regex=False):
        """ _N  Reject if word length is not equal to N
        
        Inversion Idea:
            If word is not N characters long, reject
            Otherwise, do nothing.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                try:
                    N = convert_str_length_to_int(rule[1])
                    return Invertibility.INVERTIBLE
                except BaseException:
                    return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()
        N = convert_str_length_to_int(rule[1])

        if enable_regex == False:

            if len(token_str) == N:
                inversion_result.add(token_str)

            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_bang_X_command(token_str,
                              rule,
                              just_check=False,
                              enable_regex=False):
        """ !X - reject the word if it contains character X

        Inversion Idea:
            reject the word if it contains character X. purge X from list
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                return Invertibility.INVERTIBLE

        inversion_result = InversionResult()
        X = rule[1]

        if enable_regex == False:

            for idx, token in enumerate(token_str):
                if X in token.get_value():
                    purge_set = set(x for x in token.get_value()
                                    if (x != X))  # purge X from set
                    if purge_set == set():
                        return inversion_result
                    else:
                        token_str[idx].set_value(purge_set)

            inversion_result.add(token_str)
            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_bang_question_C_command(token_str,
                                       rule,
                                       just_check=False,
                                       enable_regex=False):
        """ !?C - reject the word if it contains a character in class C 

        Inversion Idea:
            reject the word if it contains a character in class C. Purge class C from list
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                return Invertibility.INVERTIBLE

        inversion_result = InversionResult()
        C = rule[2]

        if enable_regex == False:

            for idx, token in enumerate(token_str):
                # see invert_at_question_C_command()
                if set(token.get_value()).intersection(Dicts.classes[C]):
                    purge_set = set(x for x in token.get_value()
                                    if (x not in Dicts.classes[C]))
                    if purge_set == set():
                        return inversion_result
                    else:
                        token_str[idx].set_value(purge_set)

            inversion_result.add(token_str)
            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_slash_X_command(token_str,
                               rule,
                               just_check=False,
                               enable_regex=False):
        """ /X - reject the word unless it contains character X

        Inversion Idea:
            If the word contains X, do nothing, else reject. Split into multiple tokenstrings if needed            
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                return Invertibility.INVERTIBLE

        inversion_result = InversionResult()
        X = rule[1]

        if enable_regex == False:
            potential_result = InversionResult()

            for idx, token in enumerate(token_str):
                if X in token.get_value():
                    if len(token.get_value(
                    )) == 1:  # if the char can only be X, just return itself
                        inversion_result.add(token_str)
                        return inversion_result

                    else:  # otherwise return multiple cases, set the char at idx to X.
                        temp_ts = deepcopy(token_str)
                        temp_ts.tokens[idx].set_value(X)
                        potential_result.add(temp_ts)

            return potential_result  # rejected if empty

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_slash_question_C_command(token_str,
                                        rule,
                                        just_check=False,
                                        enable_regex=False):
        """ /?C - reject the word unless it contains a character in class C

        Inversion Idea:
            If the word contains ?C, do nothing, else reject. Split into multiple tokenstrings if needed            
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                return Invertibility.INVERTIBLE

        inversion_result = InversionResult()
        C = rule[2]

        if enable_regex == False:

            potential_result = InversionResult()

            for idx, token in enumerate(token_str):

                intersect_set = set(token.get_value()).intersection(
                    Dicts.classes[C])

                # if everything at idx is in class C.
                if token.get_value().issubset(intersect_set):
                    if intersect_set:
                        inversion_result.add(token_str)
                        return inversion_result

                else:  # else could be other things, split
                    if intersect_set:
                        temp_ts = deepcopy(token_str)
                        temp_ts.tokens[idx].set_value(intersect_set)
                        potential_result.add(temp_ts)

            return potential_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_equal_N_X_command(token_str,
                                 rule,
                                 just_check=False,
                                 enable_regex=False):
        """ =NX - reject the word unless character in position N is equal to X
        
        Inversion Idea:
            Case by case, count different types of tokens, and split.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                try:
                    N = convert_str_length_to_int(rule[1])
                    return Invertibility.INVERTIBLE
                except BaseException:
                    return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()
        N = convert_str_length_to_int(rule[1])
        X = rule[2]

        if enable_regex == False:
            if N >= len(token_str):  # too short
                return inversion_result

            if X in token_str[N].get_value():
                token_str[N].set_value(X)
                inversion_result.add(token_str)

            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_equal_N_question_C_command(token_str,
                                          rule,
                                          just_check=False,
                                          enable_regex=False):
        """ =N?C - reject the word unless character in position N is in class C 
        
        Inversion Idea:
            Case by case, count different types of tokens, and split.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                try:
                    N = convert_str_length_to_int(rule[1])
                    return Invertibility.INVERTIBLE
                except BaseException:
                    return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()
        N = convert_str_length_to_int(rule[1])
        C = rule[3]

        if enable_regex == False:
            if N >= len(token_str):
                return inversion_result

            intersect_set = set(token_str[N].get_value()).intersection(
                Dicts.classes[C])  # see invert_at_question_C_command
            if intersect_set:  # in class C.
                token_str[N].set_value(intersect_set)
                inversion_result.add(token_str)

            return inversion_result  # rejected if empty

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_left_paren_X_command(token_str,
                                    rule,
                                    just_check=False,
                                    enable_regex=False):
        """ (X - reject the word unless its first character is X
        
        Inversion Idea:
            Unless the first letter of the candidate password is X, the password is rejected.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                return Invertibility.INVERTIBLE

        inversion_result = InversionResult()
        X = rule[1]

        if enable_regex == False:
            if len(token_str) > 0:

                token_str[0].set_value(X)
                inversion_result.add(token_str)

            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_left_paren_question_C_command(token_str,
                                             rule,
                                             just_check=False,
                                             enable_regex=False):
        """ (?C - reject the word unless its first character is in class C 
        
        Inversion Idea:
            Unless the first letter of the candidate password is X, the password is rejected.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        C = rule[2]

        if enable_regex == False:
            if len(token_str) > 0:
                intersect_set = set(token_str[0].get_value()).intersection(
                    Dicts.classes[C])
                if intersect_set:
                    token_str[0].set_value(intersect_set)
                    inversion_result.add(token_str)

            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_right_paren_X_command(token_str,
                                     rule,
                                     just_check=False,
                                     enable_regex=False):
        """ )X - reject the word unless its last character is X

        Inversion Idea:
            Unless the last letter of the candidate password is X, the password is rejected.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """

        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        X = rule[1]

        if enable_regex == False:
            if len(token_str) > 0:
                # char the last char
                if X in token_str[-1].get_value():
                    token_str[-1].set_value(X)
                    inversion_result.add(token_str)

            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_right_paren_question_C_command(token_str,
                                              rule,
                                              just_check=False,
                                              enable_regex=False):
        """ )?C - reject the word unless its last character is in class C 

        Inversion Idea:
            Unless the last letter of the candidate password is ?C, the password is rejected.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """

        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        C = rule[2]

        if enable_regex == False:
            if len(token_str) > 0:
                # check the last char
                intersect_set = set(token_str[-1].get_value()).intersection(
                    Dicts.classes[C])
                if intersect_set:
                    token_str[-1].set_value(intersect_set)
                    inversion_result.add(token_str)

            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_percent_N_X_command(token_str,
                                   rule,
                                   just_check=False,
                                   enable_regex=False):
        """ %NX - reject the word unless it contains at least N instances of X
        
        Inversion Idea:
            if word has less than N inst, rule fails, else return tokenstring
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                try:
                    N = convert_str_length_to_int(rule[1])
                    return Invertibility.INVERTIBLE
                except BaseException:
                    return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()
        N = convert_str_length_to_int(rule[1])
        X = rule[2]

        literal_count = 0
        range_count = []

        if enable_regex == False:
            for idx, token in enumerate(token_str):
                if X in token.get_value():
                    if len(token.get_value()) == 1:
                        literal_count += 1
                    else:
                        range_count.append(idx)

            if literal_count >= N:
                inversion_result.add(token_str)
                return inversion_result
            else:
                after_lit = N - literal_count

                # If there are enough X.
                if len(range_count) >= after_lit:
                    for comb in combinations(range_count, after_lit):
                        tmp_token_string = deepcopy(token_str)
                        for v in comb:  # set specific position to X
                            tmp_token_string[v].set_value(X)
                        inversion_result.add(tmp_token_string)

                return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_percent_N_question_C_command(token_str,
                                            rule,
                                            just_check=False,
                                            enable_regex=False):
        """ %N?C - reject the word unless it contains at least N characters of class C 
        
        Inversion Idea:
            if word has less than N inst, rule fails, else return tokenstring
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                try:
                    N = convert_str_length_to_int(rule[1])
                    return Invertibility.INVERTIBLE
                except BaseException:
                    return Invertibility.UNINVERTIBLE

        inversion_result = InversionResult()
        N = convert_str_length_to_int(rule[1])
        C = rule[3]

        literal_count = 0
        range_count = []

        if enable_regex == False:
            for idx, token in enumerate(token_str):
                # @?C
                if set(token.get_value()).intersection(Dicts.classes[C]):
                    if len(token.get_value()) == 1:
                        literal_count += 1
                    else:
                        range_count.append(idx)

            if literal_count >= N:
                inversion_result.add(token_str)
                return inversion_result
            else:
                after_lit = N - literal_count

                # Should not use to_string, check set.
                if len(range_count) >= after_lit:

                    for comb in combinations(range_count, after_lit):
                        tmp_token_string = deepcopy(token_str)
                        for v in comb:
                            tmp_token_string[v].set_value(
                                tmp_token_string[v].get_value().intersection(
                                    Dicts.classes[C]))
                        inversion_result.add(tmp_token_string)

                return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_at_X_command(token_str,
                            rule,
                            just_check=False,
                            enable_regex=False):
        """ @X - purge all characters X from the word 

        Inversion Idea:
            None
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """

        if just_check:
            return Invertibility.UNINVERTIBLEOPTIMIZATBLE

        X = rule[1]
        set_X = set(X)

        if enable_regex == False:

            inversion_result = InversionResult()

            for idx, token in enumerate(token_str):

                # If only contains X, rejected
                if token.get_value().issubset(set_X):
                    return inversion_result

            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_at_question_C_command(token_str,
                                     rule,
                                     just_check=False,
                                     enable_regex=False):
        """ @?C - purge all characters of class C from the word 
        
        Inversion Idea:
            None
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check:
            return Invertibility.UNINVERTIBLEOPTIMIZATBLE

        C = rule[2]
        class_C = Dicts.classes[C]

        if enable_regex == False:
            inversion_result = InversionResult()

            for idx, token in enumerate(token_str):

                # If only contains ?C, rejected
                if token.get_value().issubset(class_C):
                    return inversion_result

            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_s_X_Y_command(token_str,
                             rule="sXY",
                             just_check=False,
                             enable_regex=False):
        """ sXY replace all characters X in the word with Y 
        
        Inversion Idea:
            If Y presents, replace Y with X and Y.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check:
            return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        X = rule[1]
        Y = rule[2]

        if enable_regex == False:
            for idx, token in enumerate(token_str):
                # X in set and Y not in set, remove X, if empty, reject
                if X in token.get_value() and Y not in token.get_value():
                    minus_X = set(x for x in token.get_value() if (x != X))
                    if len(minus_X) == 0:
                        return inversion_result
                    else:
                        token_str[idx].set_value(minus_X)

                # X not in set and Y in set, add X.
                elif X not in token.get_value() and Y in token.get_value():
                    token_str[idx].set_value(token_str[idx].get_value() |
                                             set(X))

                else:
                    pass

            inversion_result.add(token_str)
            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_s_question_C_Y_command(token_str,
                                      rule="s?CY",
                                      just_check=False,
                                      enable_regex=False):
        """ s?CY replace all characters of class C in the word with Y

        Inversion Idea:
            If Y presents, replace Y with ?C and Y.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """

        if just_check:
            return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        C = rule[2]
        Y = rule[3]

        if enable_regex == False:
            for idx, token in enumerate(token_str):
                # full subset, rejected.
                # If only X, reject
                if token.get_value().issubset(set(
                        Dicts.classes[C])) and Y not in token.get_value():
                    return inversion_result
                elif Y in token.get_value():
                    token_str[idx].set_value(token_str[idx].get_value() |
                                             set(Y) | set(Dicts.classes[C]))
                else:
                    token.set_value(token.get_value() - set(Dicts.classes[C]))

            inversion_result.add(token_str)
            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    @staticmethod
    def invert_e_X_command(token_str,
                           rule,
                           just_check=False,
                           enable_regex=False):
        """ eX  Lower case the whole line, then upper case the first letter and every letter after a custom separator character: p@ssW0rd-w0rld -> (e-) P@ssw0rd-W0rld

        Inversion Idea:
            Check to make sure first letter is uppercase as well as every letter after delim.
            Make sure all other letters are lowercase.
            Put each letter in a set with its upper/lowercase counterpart.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check == True:
            if enable_regex == True:
                return Invertibility.UNINVERTIBLE
            else:
                return Invertibility.INVERTIBLE

        X = rule[1]
        set_X = set(X)

        if enable_regex == False:

            inversion_result = InversionResult()

            if len(token_str) == 0:  # Nothing to do
                inversion_result.add(token_str)
                return inversion_result

            # Case "_A/aB/b" * "_A/aB/b" * "_A/aB/b"
            # Case1: "_" "Upper" "Any"
            # Case2: "Any-_" "_" "Upper"
            # Case3: "_" "_" "Upper"
            # Case4: "Any-_" "Any-_" "Any"

            # First, find all consecutive Xs.
            groups = []
            group = []
            is_consecutive = False
            for idx, token in enumerate(token_str):
                if X in token.get_value():
                    group.append((token.get_value(), idx))

                else:
                    if len(group) != 0:
                        groups.append(group)
                        group = []

            # If the end contains 'X'
            if len(group) != 0:
                groups.append(group)
                group = []

            # For each consecutive group, get Combination (AB, AB', A'B, AB)
            expanded_sets_for_groups = []

            for group in groups:
                expanded_sets = []
                masks = product((True, False), repeat=len(group))
                for mask in masks:
                    one_expansion = []
                    for set_v, mask_v in zip(group, mask):
                        if mask_v == True:
                            one_expansion.append((set_X, set_v[1]))
                        else:
                            if set_v[0] - set_X:
                                one_expansion.append((set_v[0] - set_X,
                                                      set_v[1]))
                            else:
                                break
                    else:
                        expanded_sets.append(one_expansion)

                if len(expanded_sets) != 0:
                    expanded_sets_for_groups.append(expanded_sets)

            # For all group, get Product of all its combinations
            for p in product(*expanded_sets_for_groups):
                tmp_token_str = deepcopy(token_str)
                for l in p:
                    for v in l:
                        tmp_token_str[v[1]].set_value(v[0])

                prev_X = True  # For the first one
                # If first is set_X, continued, otherwise upper case
                for idx, token in enumerate(tmp_token_str):

                    if token.get_value() == set_X:
                        prev_X = True
                        continue

                    else:
                        # Upper
                        if prev_X == True:
                            prev_X = False
                            other_sets = set(x for x in token.get_value().
                                             difference(Dicts.classes['a']))
                            upper_sets = set(
                                chain.from_iterable(
                                    (x, x.lower())
                                    for x in token.get_value().intersection(
                                        Dicts.classes['u'])))
                            if other_sets | upper_sets:
                                token.set_value(other_sets | upper_sets)
                            else:
                                break

                        # Lower
                        else:
                            other_sets = set(x for x in token.get_value().
                                             difference(Dicts.classes['a']))
                            upper_sets = set(
                                chain.from_iterable(
                                    (x, x.upper())
                                    for x in token.get_value().intersection(
                                        Dicts.classes['l'])))
                            if other_sets | upper_sets:
                                token.set_value(other_sets | upper_sets)
                            else:
                                break

                else:
                    inversion_result.add(tmp_token_str)

            return inversion_result

        else:
            inversion_result.set_status(InversionStatus.OUTSCOPE)
            return inversion_result

    def invert_flag_command(token_str,
                            rule,
                            just_check=False,
                            enable_regex=False):
        """ Rejection Flags (-s, -p, -8, -c, ->4, etc.)
        
        Inversion Idea:
            Some flags result in a rejection, others have no effect.
        
        Args:
            token_str: the tokenstring for rule inversion.

            rule: the tokenized transformation.

            just_check: If True, only returns the invertibility. No actual inversion.

            enable_regex: If enables regex.

        Returns:
            An instance of InversionResult containing all possible preimages (represented in tokenstrings)
        """
        if just_check:
            return Invertibility.INVERTIBLE

        inversion_result = InversionResult()

        if (rule[1] in "ps8"):  # -p, -s rejct
            return inversion_result

        else:  # -c, -:, ->N, -<N. Don't do anything
            inversion_result.add(token_str)
            return inversion_result


def get_inversion_function(transformation):
    """ Based on tokenized transformation, get the corresponding inversion function """
    corresponding_function = getattr(
        Inversion, "invert_{}_command".format(
            get_name_of_a_rule(transformation)))
    return corresponding_function


def invert_single_transformation(token_strs, transformation,
                                 enable_regex=False):
    """ Invert a single transformation

    Args:
        token_strs: A list a of tokenstrings to be inverted

        transformation: The transformation rule

        enable_regex: Whether to enable regex operation.

    Returns:
        An instance of InversionResult containing all possible preimages (represented in tokenstrings)
    """
    ret_val = InversionResult()
    try:
        inversion_function = get_inversion_function(transformation)
        for token_str in token_strs:
            # invert one transfomration
            single_result = inversion_function(
                token_str, transformation, enable_regex=enable_regex)

            # if out_of_scope, call JtR/HC to handle.
            if single_result.get_status() == InversionStatus.OUTSCOPE:
                ret_val.set_status(InversionStatus.OUTSCOPE)
                return ret_val

            # otherwise save inversion result
            else:
                ret_val += single_result

    # if anything goes wrong during inversion, abort
    except Exception as e:
        ret_val.set_status(InversionStatus.ERROR)
        ret_val.set_error_msg(str(e))

    finally:
        return ret_val


def invert_one_subrule(token_str, subrule, enable_regex=False, skip_index=None):
    """ Invert a subrule, which doesn't have any parallelism

    Args:
        token_strs: A list a of tokenstrings to be inverted

        subrule: A rule consists of multiple transformations and has no parallelism.

        enable_regex: Whether to enable regex operation.

        skip_index: additional information for special cases in JtR.

    Returns:
        An instance of InversionResult containing all possible preimages (represented in tokenstrings)
    """
    memorized_words = set()

    result = InversionResult(token_str)
    # For each transformation
    for i, transformation in enumerate(subrule[::-1]):

        # If that place is Q, then memorize the word.
        if skip_index != None and (i + skip_index) == len(subrule) - 1:

            if transformation[0] == "Q":
                # memorize
                strings = result.get_all_strings()
                memorized_words |= set(strings)

            else:
                raise Exception("Unknown Subrule Type")

            continue

        result = invert_single_transformation(result.get_value(),
                                              transformation)

        if result.is_normal() != True or result.is_null() == True:
            return result

    result.memorize(memorized_words)
    return result


def invert_one_rule(token_str, one_rule, enable_regex=False, skip_index=None):
    """ Invert one rule. A rule is line of transformations in a rule list file.

    Args:
        token_str: the initial tokenized password.

        one_rule: tokenized rule.

        enable_regex: Whether to enable regex operation.

        skip_index: additional information for special cases in JtR.

    Returns:
        An instance of InversionResult containing all possible preimages (represented in tokenstrings)
    """

    ret_val = InversionResult()

    for subrule in one_rule.rules:

        result = invert_one_subrule(
            deepcopy(token_str), subrule, skip_index, skip_index)
        result_status = result.get_status()

        # If the inverison goes well
        if result_status == InversionStatus.NORMAL:
            ret_val += result

        # If the rule cannot be inverted or something goes wrong
        else:
            ret_val.set_status(result_status)
            if result.error_msg != "":
                ret_val.set_error_msg(result.error_msg)
            return ret_val

    return ret_val


def check_one_transformation(transformation, enable_regex=False):
    inversion_function = get_inversion_function(transformation)
    single_invertibility = inversion_function(
        None, transformation, just_check=True, enable_regex=enable_regex)
    return single_invertibility


def check_is_invertible(one_rule, enable_regex=False):
    """ Check the invertibility of a rule. 

    Args:
        enable_regex: Whether to enable regex operation.

    Returns:
        Invertibility
    """
    rule_invertibility = Invertibility.INVERTIBLE

    for subrule in one_rule.rules:  # each subrule
        for transformation in subrule:  # each transformation
            single_invertibility = check_one_transformation(
                transformation, enable_regex)
            if single_invertibility < rule_invertibility:  # set to lowest possibility
                rule_invertibility = single_invertibility
                if rule_invertibility == Invertibility.UNINVERTIBLE:
                    return rule_invertibility

    return rule_invertibility


def get_special_invertibility(rulelist, enable_regex=False):
    """ check rules and find special invertibility """
    if enable_regex == True:
        return

    #### Check Special Type 1: ends with Q and only have Az,r,d after it, change to invertible ####
    for r in rulelist:
        # originally Q is rejected
        if r.feasibility.is_uninvertible() != True:
            continue

        is_special = True

        # subspecial: Only has one Q, no M,X. What's before Q is just "><dfrA^$"
        for subrule in r.rules:  #For Each Subrule

            sub_rejected = False

            q_index = float('inf')

            # First round, find Q and MX
            for idx, comp in enumerate(subrule[::-1]):

                if comp[0] in "Q":

                    if q_index == float("inf"):
                        q_index = len(subrule) - idx - 1

                    else:
                        sub_rejected = True
                        break

                elif comp[0] in "MX":
                    # totally not possible
                    sub_rejected = True
                    break

            else:
                if q_index != float("inf"):
                    # what's after Q should within "><dfrA^$/"
                    for idx, comp in enumerate(subrule[q_index + 1:]):
                        if comp[0] in "><dfrA^$/":
                            continue
                        else:
                            sub_rejected = True
                            break

                    for transformation in subrule[:q_index]:
                        # What's Before Q should also be invertible, like xNM
                        if check_one_transformation(
                                transformation) != Invertibility.INVERTIBLE:
                            sub_rejected = True
                            break

                else:
                    sub_rejected = True

            if sub_rejected == True:
                is_special = False
                break

        if is_special == True:
            # Change Invertibility too
            r.feasibility.set_to_special_memory(q_index)

    #### Check Special Type 2: a lot of deletion in the beginning, will affect trie search, mark as uninvertible"""
    for r in rulelist:
        # If not invertible, forget about it
        if r.feasibility.is_invertible() != True:
            continue

        for subrule in r.rules:

            # Build special case
            # (count(D0-D6) >= 2 && (count(Deletion) >= 3)
            # || (count(D0-D6) >= 2 && (count(l/u/c/C) >= 1)
            early_threshold = 6  # [D0 - D_thresh] is considered early
            early_factor = 0  # if early deletion >= 2, needs binary search than trie search
            total_factor = 0  # total deletion
            o_threshold = 2
            o_factor = 0
            n_threshold = 2
            n_factor = 0
            shift_cases = False

            for transformation in subrule:

                if transformation[0] in "D":
                    N = convert_str_length_to_int(transformation[1])
                    # If D0 - D6, increase early factor
                    if N <= early_threshold:
                        early_factor += 1
                    total_factor += 1
                elif transformation[0] in "[":
                    early_factor += 1
                    total_factor += 1
                elif transformation[0] in "]":
                    total_factor += 1
                elif transformation[0] in "O":
                    N = convert_str_length_to_int(transformation[1])
                    M = convert_str_length_to_int(transformation[2])
                    if N <= early_threshold:
                        early_factor += M
                    total_factor += M
                elif transformation[0] in "lucCeE":
                    shift_cases = True
                elif transformation[0] in "o":
                    N = convert_str_length_to_int(transformation[1])
                    if N <= o_threshold:
                        o_factor += 1
                elif transformation[0] in ".,":
                    N = convert_str_length_to_int(transformation[1])
                    if N <= n_threshold:
                        n_factor += 1
                else:
                    continue

            if early_factor >= 2 and (shift_cases == True or total_factor >= 3):
                r.feasibility.set_to_optimizable()
                break
            elif early_factor + o_factor >= 3:
                r.feasibility.set_to_optimizable()
                break
            elif early_factor + n_factor >= 3:
                r.feasibility.set_to_optimizable()
                break
            else:
                pass

    return rulelist

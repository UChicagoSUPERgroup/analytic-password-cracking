"""This file contains intermediate data structure used in invert_rule"""
from abc import ABCMeta, abstractmethod
from common import FatalRuntimeError
from enum import Enum
from copy import deepcopy
from utility import char_is_printable
from itertools import chain, combinations, product, permutations
from invert_helper import Dicts


class TokenType(Enum):
    """ An enum that represents the different types of tokens that can exist
    
    Attr:
        Range: match char a, if a is in the set of chars.
        Regex: match char a multiple times (as specified by [from, to]), if a is in the set of chars
    """

    Range = 1
    Regex = 2


class TokenBase(metaclass=ABCMeta):
    """ Abstract Class Definition For Token

    A Token is a union of (Set<chars>, Set<chars> + A Range).
    Implemented by Token Class and RegexToken Class.
    """

    @abstractmethod
    def __init__(self, val):
        pass

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def set_value(self, val):
        pass

    @abstractmethod
    def get_value(self):
        pass

    @abstractmethod
    def get_type(self):
        pass

    def get_ord(self, c):
        """ Convert char to chr(number) if needed """
        if 32 <= ord(c) <= 126:
            return c

        else:
            return "chr({})".format(ord(c))

    def get_set_name(self, token_value):
        """ Compress set representatiom if possible """
        token_value = set(token_value)

        if token_value == Dicts.classes['z']:
            return "class_z"
        elif token_value == Dicts.classes['a']:
            return "class_a"
        elif token_value == Dicts.classes['l']:
            return "class_l"
        elif token_value == Dicts.classes['u']:
            return "class_u"
        elif token_value == Dicts.classes['d']:
            return "class_d"
        else:
            return ",".join(list(map(self.get_ord, token_value)))

    @abstractmethod
    def is_range(self):
        pass

    @abstractmethod
    def is_regex(self):
        pass

    @abstractmethod
    def only_set_value(self, val):
        pass


class Token(TokenBase):

    def __init__(self, val):
        """ Initialize token with a set val.

        A token matches char a, if a is in val. Assume val is type set, if val is str, val = set(val)
        """
        self.set_value(val)

    def __len__(self):
        """ returns cardinality of set """
        return len(self.token_value)

    def __repr__(self):
        """ print this token """
        return 'set({})'.format(self.get_set_name(self.token_value))

    def set_value(self, val):
        """ Specify the set of chars. Assume val is type set, if val is str, val = set(val) """
        if type(val) is str:
            self.token_value = set(val)

        elif type(val) is set:
            self.token_value = val

        else:
            raise FatalRuntimeError("Unknown Set Up Type In Token")

    def get_value(self):
        """ return the set of chars"""
        return self.token_value

    def get_type(self):
        """ return the tokentype"""
        return TokenType.Range

    def is_range(self):
        """ check if the tokentype is range """
        return True

    def is_regex(self):
        """ check if this token is regex token """
        return False

    def only_set_value(self, val):
        """ only set value """
        self.set_value(val)


class RegexToken(TokenBase):
    """ A Regex Token

    It matches at least N (inclusive), at most M (exclusive) chars, where each char c is in set(val).
    """

    def set_value(self, val, start, end):
        """ Set the value in RegexToken, and the range. The token is initialized as: set(val), [start, end)."""
        if type(val) is str:
            self.token_value = set(val)

        elif type(val) is set:
            self.token_value = val

        else:
            raise FatalRuntimeError("Unknown Set Up Type In Token")

        if (start != None and end == None) or (start == None and end != None):
            raise FatalRuntimeError("Set Both Start and End for regex")

        self.start = self.set_start(start)
        self.end = self.set_end(end)

    def only_set_value(self, val):
        """ Only set the value in RegexToken. Keep the range"""
        if type(val) is str:
            self.token_value = set(val)

        elif type(val) is set:
            self.token_value = val

        else:
            raise FatalRuntimeError("Unknown Set Up Type In Token")

    def get_type(self):
        """ return the tokentype"""
        return TokenType.Regex

    def __init__(self, val, start=None, end=None):
        """ Initialize a RegexToken as set(val) + [start, end). start and end cannot both be None

        Params:
        val: a set of chars, or a string. If val is a string, call set(val)
        start: start of a range.
        end: end of a range (exclusive).
        """
        self.set_value(val, start, end)

    def __repr__(self):
        """ print this token """
        return 'set({}) [{} - {})'.format(
            get_set_name(self.token_value), self.start, self.end)

    def is_regex(self):
        """ return True because this is a regex token """
        return True

    def is_range(self):
        """ return False because this is not a regex token """
        return False

    def set_start(self, val):
        """ set the start value. start has to be at least 0."""
        self.start = max(0, val)

    def set_end(self, val):
        """ set the end value. end has to be at least 0."""
        self.start = max(0, val)

    def decrease_window(self, val):
        """ decrease the range by val """
        self.set_start(self.start - val)
        self.set_end(self.end - val)
        if self.start == 0 and self.end == 0:
            raise FatalRuntimeError("self.start and self.end both 0")


class TokenStringBase(metaclass=ABCMeta):
    """
    A TokenString Base

    Implemented by TokenString Class and RegexTokenString Class.
    """

    @abstractmethod
    def __init__(self, word):
        pass

    @abstractmethod
    def __setitem__(self, key, value):
        pass

    @abstractmethod
    def __getitem__(self, key):
        pass

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def __iter__(self):
        pass

    def insert(self, idx, x):
        pass

    def to_strings(self, remove_non_ascii=True):
        pass

    def contains(self, word):
        pass


class RegexTokenString(TokenStringBase):
    """ A RegexTokenString Tries To Mimic Regex. It is a List<RegexToken/Token>

    It is a strict subset of Regex Language.
    This class also contains methods for manipulating the List.
    """

    def __init__(self, word):
        """ Initialize a regex tokenstring """
        self.tokens = [] if word is None else [RegexToken(g) for g in word]

        # Additional length requirement. Denoting the length for input string before mangling
        # min_len <= Length < max_len
        self.min_len = 0
        self.max_len = RUNTIME_CONFIG['max_cut_length']

    def __setitem__(self, key, value):
        self.tokens[key] = value

    def __getitem__(self, key):
        return self.tokens[key]

    def __repr__(self):
        """Print this tokenstring"""
        return '{}, MatchRange[{},{})'.format(self.tokens, self.min_len,
                                              self.max_len)

    def __iter__(self):
        yield from self.tokens

    def decrease_window(self, val):
        """ decrease the match window"""
        self.max_len -= val
        if self.max_len < 0:
            self.max_len = 0

        self.min_len -= val
        if self.min_len < 0:
            self.min_len = 0

    def increase_window(self, val):
        """ increase the match length"""
        self.max_len += val
        if self.max_len > RUNTIME_CONFIG['max_cut_length']:
            self.max_len = RUNTIME_CONFIG['max_cut_length']

        self.min_len += val
        if self.min_len > RUNTIME_CONFIG['max_cut_length']:
            self.min_len = RUNTIME_CONFIG['max_cut_length']

    def count_non_regex_tokens(self):
        """ Count Non RegexToken Tokens"""
        return sum(token.is_range() for token in self.tokens)

    @staticmethod
    def RegexTokenStringFrom(regex_token_string):
        """ Inherent the configuration from an old regex_token_string, and create a new instance"""
        new_instance = RegexTokenString(None)
        new_instance.min_len = regex_token_string.min_len
        new_instance.max_len = regex_token_string.max_len
        return new_instance

    def set_max_len(self, l):
        """ set min_len, only update when narrowing the max length """
        if l > RUNTIME_CONFIG['max_cut_length']:
            l = RUNTIME_CONFIG['max_cut_length']

        if l < self.max_len:
            self.max_len = l

        self.max_len = l

    def set_min_len(self, l):
        """ set min_len, only update when narrowing the min length """
        if l < 0:
            l = 0

        if l > self.min_len:
            self.min_len = l

    def reset_max_len(self):
        """ reset max_len """
        self.max_len = RUNTIME_CONFIG['max_cut_length']

    def reset_min_len(self):
        """ reset min_len """
        self.min_len = 0

    def is_valid(self):
        """ Check if this RegexTokenString is still valid

        Only valid when 1 and 2 are both satisfied.
        1. the number of non_regex_token is greater than self.max_len
        2. self.max_len > self.min_len
        """
        non_regex_count = self.count_non_regex_tokens()
        if non_regex_count >= self.max_len:
            return False

        # special case, contains only regex with all 0
        if self.max_len == 1 and self.min_len == 0:
            for token in self.tokens:
                if token.is_regex() and token.start == 0:
                    pass
                else:
                    break
            else:
                self.tokens = []
                return True

            return False

        return self.max_len > self.min_len

    # Use dp to optimize potentially
    def regexmatch(self, word, regex):
        """ Recursively check if a regex matches the word """
        if word == "":
            if len(regex) == 0:
                return True

            else:
                for reg in regex:
                    if reg.is_regex() and reg.start == 0:
                        continue
                    return False
                return True

        if len(regex) == 0 and word != "":
            return False

        c = word[0]

        if regex[0].is_range():
            if c in regex[0].get_value():
                return regexmatch(word[1:], regex[1:])
            else:
                return False

        else:
            if c in regex[0].get_value(
            ) and regex[0].end >= 2:  # < end, so end >= 2
                # must match 1.
                if regex[0].start > 0:
                    regex[0].decrease_window(1)
                    return regexmatch(word[1:], regex)
                else:
                    regex[0].decrease_window(1)
                    return regexmatch(word[1:], regex) or regexmatch(
                        word[1:], regex[1:]) or regexmatch(word, regex[1:])
            else:
                if regex[0].start != 0:
                    return False
                else:  # match next one
                    return regexmatch(word, regex[1:])

    def contains(self, word):
        """ Check if this regex tokenstring matches the word. """

        # First check meet additional length requirement
        if len(word) >= self.max_len or len(word) < self.min_len:
            return False

        return self.regexmatch(word, deepcopy(self.tokens))

    @staticmethod
    def fix_first_N_position(token_str, N):
        """ Fix the first N chars of a regex tokenstring. i.e. make the first N tokens Token()

        You the first length chars should be Range not Regex. Output could have regex, no fixed length

        Steps:
        1. Figure out how many regexes are there, how many ranges are there
        2. Use all possible regex to fill to length
        3. Use the first i tokens(range + regex) to fill length. append what's left
        4. When appending what's left. There are multiple cases.

        Example:
        (r*)ab(r*)c for length 5
        case1: (r*) >= 5 (not = 5)
        case2: rrrra + b(r*)c
        case3: rrrab + (r*)c
        case4: rrabr + (r*)c
        case4: rabrr + (r*)c
        case5: abrrr + (r*)c
        case6: abrrc
        case7: rabrc
        case8: rrabc
        """

        length = N

        # Special case length = 0, nothing is fixed return the original
        if length == 0:
            return [token_str]

        # if input token_str doesn't accept length at least N, reject
        if token_str.max_len <= length:
            return []

        non_regex_pos = []
        regex_pos = []

        # First, figure out how many fix length tokens, how many regex
        for idx, token in enumerate(token_str.tokens):
            if token.is_range():
                non_regex_pos.append(idx)

            else:

                # if regex.start != 0, should make start = 0 by adding dups.
                # if regex.end != inf, not real regex
                if token.start != 0 or token.end != float("inf"):
                    raise FatalRuntimeError(
                        "Flatting Regex If Start != 0 or End != 0")

                regex_pos.append(idx)

        # no regex
        if len(regex_pos) == 0:
            if len(non_regex_pos) >= length:
                return [token_str]
            else:
                return []

        # else has regex
        # Next, use regex to fill the position.
        # If token len < length, all regex are possible to be used to enuemrate to length
        if len(non_regex_pos) < length:
            regex_pos_valid_to_enumerate = regex_pos
        else:
            # if length = 3, reg token token reg token rex -> only first 2 reges are token into consider
            regex_pos_valid_to_enumerate = [
                x for x in regex_pos if x <= non_regex_pos[length - 1]
            ]

        # The first N are all ranges
        if len(regex_pos_valid_to_enumerate) == 0:
            return [token_str]

        ret_val = []

        # Find the ending position
        max_range = max(regex_pos_valid_to_enumerate + non_regex_pos)
        regex_count = []

        # Use the first i tokens to contruct length, append what's left
        for i in range(max_range + 1):
            if i in regex_pos_valid_to_enumerate:
                regex_count.append(i)

            # If we didn't see any regex, conitnue
            if len(regex_count) == 0:
                continue

            # Just one p here, distribute values cross regexes
            for p in RegexTokenString.partition(
                    length - i + len(regex_count) - 1, len(regex_count)):
                tmp_token_str = RegexTokenString.RegexTokenStringFrom(token_str)
                tmp_tokens = []

                # create tokens
                for j in range(i + 1):
                    if j in regex_count:
                        j_index = regex_count.index(j)
                        if p[j_index] != 0:
                            tmp_tokens += [
                                Token(token_str[j].get_value())
                                for _ in range(p[j_index])
                            ]

                        # if j is the last one. What's after it is still inf.
                        if j == i:
                            # Remove share = 0 to reduce dups, ie. if p[j_index] != 0:
                            tmp_tokens += [
                                Token(token_str[j].get_value(), 0, float("inf"))
                            ]
                    else:
                        tmp_tokens += [Token(token_str[j].get_value())]

                tmp_token_str.tokens = tmp_tokens + \
                    deepcopy(token_str.tokens[i+1:])

                # only set min_len when narrowing
                tmp_token_str.set_min_len(length)
                ret_val.append(tmp_token_str)

        return ret_val

    @staticmethod
    def fix_last_N_position(token_str, N):
        """ Fix the last N chars in a regex tokenstring

        Same logic as first_N_position

        Example:
        N = 2
        ba(1)*(2)*c:
        case1: ba(1*)2(*) 2c
        case2: ba(1*)     1c
        case3: ba(1*)     1c
        """
        length = N

        # Special case length = 0, nothing is fixed return the original
        if length == 0:
            return [token_str]

        if token_str.max_len <= length:
            return []

        non_regex_pos = []
        regex_pos = []

        # First, figure out how many fix length tokens, how many regex
        for idx, token in enumerate(token_str.tokens):

            if token.is_range():
                non_regex_pos.append(idx)

            else:
                # if regex.start != 0, should make start = 0 by adding dups.
                # if regex.end != inf, not real regex
                if token.start != 0 or token.end != float("inf"):
                    raise FatalRuntimeError(
                        "Flatting Regex If Start != 0 or End != 0")

                regex_pos.append(idx)

        # no regex
        if len(regex_pos) == 0:

            if len(non_regex_pos) >= length:
                return [token_str]

            else:
                return []

        # else has regex
        # Next, use regex to fill the position.
        # If token len < length, all regex are possible to be used to enuemrate to length
        if len(non_regex_pos) < length:
            regex_pos_valid_to_enumerate = regex_pos
        else:
            # if length = 3, reg token token reg token rex -> only last 2 reges are token into consider
            regex_pos_valid_to_enumerate = [
                x for x in regex_pos if x >= non_regex_pos[-length]
            ]

        # The last N are all non-regex
        if len(regex_pos_valid_to_enumerate) == 0:
            return [token_str]

        ret_val = []

        # Find the ending position
        min_range = min(regex_pos_valid_to_enumerate + non_regex_pos)
        max_range = max(regex_pos_valid_to_enumerate + non_regex_pos)
        regex_count = []

        # Use the last i tokens to contruct length, append what's left
        for i in reversed(range(min_range, max_range + 1)):

            if i in regex_pos_valid_to_enumerate:
                regex_count.append(i)

            # If we didn't see any regex, conitnue
            if len(regex_count) == 0:
                continue

            # Just one p here, distribute values cross regexes
            for p in RegexTokenString.partition(
                    length - max_range + i - 1 + len(regex_count),
                    len(regex_count)):
                tmp_token_str = RegexTokenString.RegexTokenStringFrom(token_str)
                tmp_tokens = []

                # create tokens
                for j in reversed(range(i, max_range + 1)):
                    if j in regex_count:
                        j_index = regex_count.index(j)
                        if p[j_index] != 0:
                            tmp_tokens = [
                                Token(token_str[j].get_value())
                                for _ in range(p[j_index])
                            ] + tmp_tokens

                        # if j is the last one. What's after it is still inf.
                        if j == i:
                            # Remove share = 0 to reduce dups, ie. if p[j_index] != 0:
                            tmp_tokens = [
                                Token(token_str[j].get_value(), 0, float("inf"))
                            ] + tmp_tokens
                    else:
                        tmp_tokens = [Token(token_str[j].get_value())
                                     ] + tmp_tokens

                tmp_token_str.tokens = deepcopy(
                    token_str.tokens[:i]) + tmp_tokens

                # only set min len when narrowing
                tmp_token_str.set_min_len(length)

                ret_val.append(tmp_token_str)

        return ret_val

    @staticmethod
    def enumerate_N(token_str, N):
        """ We enumerate all possible strings to length N.

        If number of ranges >= N, then it is impossible to get that.
        So the output length is fixed, no regex
        """
        length = N

        # Special case length = 0
        if length == 0:
            for token in token_str.tokens:
                if token.is_range():
                    return []

            tmp_token_str = deepcopy(token_str)
            tmp_token_str.tokens = []
            tmp_token_str.set_max_len(1)
            return [tmp_token_str]

        # if not support, dont enumerate
        if token_str.max_len <= length:
            return []

        non_regex_pos = []
        regex_pos = []

        # First, figure out how many fix length tokens, how many regex
        for idx, token in enumerate(token_str.tokens):
            if token.is_range():
                non_regex_pos.append(idx)

            else:
                # if regex.start != 0, should make start = 0 by adding dups.
                # if regex.end != inf, not real regex
                if token.start != 0 or token.end != float("inf"):

                    raise FatalRuntimeError(
                        "Flatting Regex If Start != 0 or End != 0")

                regex_pos.append(idx)

        # no regex
        if len(regex_pos) == 0:
            if len(non_regex_pos) >= length:
                return [token_str]

            else:
                return []

        # else has regex
        # Next, use regex to fill the position.
        # If token len < length, all regex are possible to be used to enuemrate to length
        if len(non_regex_pos) < length:
            regex_pos_valid_to_enumerate = regex_pos
        else:
            # if length = 3, reg token token reg token rex -> only first 2 reges are token into consider
            regex_pos_valid_to_enumerate = [
                x for x in regex_pos if x <= non_regex_pos[length - 1]
            ]

        # The first N are all ranges
        if len(regex_pos_valid_to_enumerate) == 0:
            return [token_str]

        ret_val = []

        # Find the ending position
        max_range = max(regex_pos_valid_to_enumerate + non_regex_pos)
        regex_count = []

        # Use the first i tokens to contruct length, append what's left
        for i in range(max_range + 1):
            if i in regex_pos_valid_to_enumerate:
                regex_count.append(i)

            # If we didn't see any regex, conitnue
            if len(regex_count) == 0:
                continue

            # Just one p here, distribute values cross regexes
            for p in RegexTokenString.partition(
                    length - i + len(regex_count) - 1, len(regex_count)):
                tmp_token_str = RegexTokenString.RegexTokenStringFrom(token_str)
                tmp_tokens = []

                # create tokens
                for j in range(i + 1):
                    if j in regex_count:
                        j_index = regex_count.index(j)
                        if p[j_index] != 0:
                            tmp_tokens += [
                                Token(token_str[j].get_value())
                                for _ in range(p[j_index])
                            ]

                    else:
                        tmp_tokens += [Token(token_str[j].get_value())]

                tmp_token_str.tokens = tmp_tokens

                # only set min len when narrowing
                tmp_token_str.set_min_len(length)

                ret_val.append(tmp_token_str)

        return ret_val

    @staticmethod
    def partition(val, bins):
        """ Partition n items into k bins.

        Reference: https://stackoverflow.com/questions/13131491/partition-n-items-into-k-bins-in-python-lazily
        """
        if bins == 0:
            raise FatalRuntimeError("Error 0 bins")

        if bins == 1:
            yield [val]
        elif val == 0:
            yield [0] * bins
        elif val > 0 and bins > 1:
            for i in range(0, val + 1):
                for part in RegexTokenString.partition(val - i, bins - 1):
                    if len([i] + part) == bins:
                        yield [i] + part


class TokenString(TokenStringBase):
    """ A TokenString is a List<Token> along with methods for manipulating this List. """

    def __init__(self, word=None):
        self.tokens = [] if word is None else [Token(g) for g in word]
        self.length = len(self.tokens)

    def __len__(self):
        """ length of the list"""
        return self.length

    def __setitem__(self, key, value):
        self.tokens[key] = value

    def __getitem__(self, key):
        return self.tokens[key]

    def __repr__(self):
        return '{}, Length {}'.format(self.tokens, self.length)

    def __iter__(self):
        yield from self.tokens

    def __deepcopy__(self, memo):
        """ customize deepcopy for performance issues """
        obj = TokenString()
        obj.tokens = [Token(t.token_value) for t in self.tokens]
        obj.length = len(obj.tokens)
        return obj

    def to_strings(self, remove_non_ascii=True):
        """ Forms all possible permutations of strings for a given token string."""

        def extract_value(x):
            """ Safe way of extractin value and ensuring that no regex present """
            if remove_non_ascii == True:
                return set(c for c in x.get_value() if char_is_printable(c))
            else:
                return x.get_value()

        if self.length == 0:
            return [""]

        if self.length < 0:
            raise FatalRuntimeError("Length < 0 in tokenstring")

        tokens_as_list = (extract_value(x) for x in self.tokens[:self.length])

        list_ex = list("".join(string) for string in product(*tokens_as_list))

        return list_ex

    def contains(self, word):
        """ Check if this regex tokenstring matches the word. """
        if self.length != len(word):
            return False

        for i in range(self.length):
            if type(word[i]) == int:  # word is byte array
                if chr(word[i]) not in self.tokens[i].get_value():
                    break
            else:  # word is string
                if word[i] not in self.tokens[i].get_value():
                    break
        else:
            return True

    def pop_token(self, pos):
        """ pop a token from self.tokens, also reduce length by 1 """
        if len(self.tokens) == 0:
            return

        else:
            self.tokens.pop(pos)
            self.length -= 1

    def append_token(self, token):
        """ append a token to self.tokens, also increase length by 1 """
        if type(token) != Token:
            raise FatalRuntimeError("Tokens type error")
        self.tokens.append(token)
        self.length += 1

    def append_tokens(self, tokens):
        """ append a list of tokens to self.tokens, also increase the length """
        if type(tokens) != list:
            raise FatalRuntimeError("Tokens type error")
        self.tokens += tokens
        self.length += len(tokens)

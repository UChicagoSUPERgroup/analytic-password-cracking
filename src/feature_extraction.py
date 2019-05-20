"""This file contains functions to extract features given a rulelist."""
from copy import deepcopy
from common import FatalRuntimeError, Queue
from config import RUNTIME_CONFIG
from feature import *
from utility import convert_str_length_to_int, get_name_of_a_rule
from invert_helper import Dicts, CHAR_CLASSES
import math
import itertools


class NotCountableException(Exception):
    """ An exception denotes that the rule cannot be counted, require external help """
    pass


def precompute_p_valid_cases():
    """ precompute all valid p cases """
    aeiou_set = set("aeiou")
    sxz_set = set("sxz")
    cs_set = set("cs")
    h_set = set("h")
    y_set = set("y")
    f_set = set("f")
    e_set = set("e")
    """
    (
    (s[-1] not in "sxz" or                             len < 2) and
    (s[-1] not in "h"   or s[-2] not in "cs"        or len < 3) and
    (s[-1] not in "f"   or s[-2] in "f"             or len < 2) and
    (s[-1] not in "e"   or s[-2] not in "f"         or len < 3) and
    (s[-1] not in "y"   or s[-2] in "aeiou"         or len < 3)
    )
    """

    # Precomputation for Product
    # AB + A'B + B'A
    group1 = [
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - sxz_set, -1),
            RejectUnlessLessThanLength(2)
        ],  # AB
        [
            RejectUnlessCharInPosition(sxz_set, -1),
            RejectUnlessLessThanLength(2)
        ],  #A'B
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - sxz_set, -1),
            RejectUnlessGreaterThanLength(1)
        ]  #AB'
    ]

    group2 = [
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - h_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - cs_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #ABC
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - h_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - cs_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #ABC'
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - h_set, -1),
            RejectUnlessCharInPosition(cs_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #AB'C
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - h_set, -1),
            RejectUnlessCharInPosition(cs_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #AB'C'
        [
            RejectUnlessCharInPosition(h_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - cs_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #A'BC
        [
            RejectUnlessCharInPosition(h_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - cs_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #A'BC'
        [
            RejectUnlessCharInPosition(h_set, -1),
            RejectUnlessCharInPosition(cs_set, -2),
            RejectUnlessLessThanLength(3)
        ]  #A'B'C
    ]

    group3 = [
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - f_set, -1),
            RejectUnlessCharInPosition(f_set, -2),
            RejectUnlessLessThanLength(2)
        ],  #ABC
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - f_set, -1),
            RejectUnlessCharInPosition(f_set, -2),
            RejectUnlessGreaterThanLength(1)
        ],  #ABC'
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - f_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - f_set, -2),
            RejectUnlessLessThanLength(2)
        ],  #AB'C
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - f_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - f_set, -2),
            RejectUnlessGreaterThanLength(1)
        ],  #AB'C'
        [
            RejectUnlessCharInPosition(f_set, -1),
            RejectUnlessCharInPosition(f_set, -2),
            RejectUnlessLessThanLength(2)
        ],  #A'BC
        [
            RejectUnlessCharInPosition(f_set, -1),
            RejectUnlessCharInPosition(f_set, -2),
            RejectUnlessGreaterThanLength(1)
        ],  #A'BC'
        [
            RejectUnlessCharInPosition(f_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - f_set, -2),
            RejectUnlessLessThanLength(2)
        ],  #A'B'C
    ]

    group4 = [
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - e_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - f_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #ABC
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - e_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - f_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #ABC'
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - e_set, -1),
            RejectUnlessCharInPosition(f_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #AB'C
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - e_set, -1),
            RejectUnlessCharInPosition(f_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #AB'C'
        [
            RejectUnlessCharInPosition(e_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - f_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #A'BC
        [
            RejectUnlessCharInPosition(e_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - f_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #A'BC'
        [
            RejectUnlessCharInPosition(e_set, -1),
            RejectUnlessCharInPosition(f_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #A'B'C
    ]

    group5 = [
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - y_set, -1),
            RejectUnlessCharInPosition(aeiou_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #ABC
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - y_set, -1),
            RejectUnlessCharInPosition(aeiou_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #ABC'
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - y_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - aeiou_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #AB'C
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - y_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - aeiou_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #AB'C'
        [
            RejectUnlessCharInPosition(y_set, -1),
            RejectUnlessCharInPosition(aeiou_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #A'BC
        [
            RejectUnlessCharInPosition(y_set, -1),
            RejectUnlessCharInPosition(aeiou_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #A'BC'
        [
            RejectUnlessCharInPosition(y_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - aeiou_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #A'B'C
    ]

    dup = {}
    p_valid_cases = []
    for element in itertools.product(group1, group2, group3, group4, group5):
        tmp_dep_list = DependencyList()
        for group in element:
            for dependency in group:
                # generate a dependency list that represents the "and" relationship
                tmp_dep_list.prepend_dependency(deepcopy(dependency))
        tmp_dep_list.clean_list()

        # It's impossible to get satisfied here
        if tmp_dep_list.is_active(
        ) and len(tmp_dep_list.get_active()) != 0 and frozenset(
                tmp_dep_list.this_list) not in dup:  #remove dup dependency list
            p_valid_cases.append(tmp_dep_list)
            dup[frozenset(tmp_dep_list.this_list)] = None

    return p_valid_cases


p_valid_cases = precompute_p_valid_cases()


def precompute_P_valid_cases():
    """ precompute all valid P cases """
    bgp_set = set("bgp")
    d_set = set("d")
    y_set = set("y")
    e_set = set("e")
    """
    (
    (s[-1] not in "d"   or s[-2] not in "e"     or len < 3) and
    (s[-1] not in "y"                           or len < 3) and
    (s[-1] not in "bgp" or s[-2] in "bgp"       or len < 3) and
    (s[-1] not in "e"   or                      or len < 3)
    )
    """
    # Precomputation for Product

    group1 = [
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - d_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - e_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #ABC
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - d_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - e_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #ABC'
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - d_set, -1),
            RejectUnlessCharInPosition(e_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #AB'C
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - d_set, -1),
            RejectUnlessCharInPosition(e_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #AB'C'
        [
            RejectUnlessCharInPosition(d_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - e_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #A'BC
        [
            RejectUnlessCharInPosition(d_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - e_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #A'BC'
        [
            RejectUnlessCharInPosition(d_set, -1),
            RejectUnlessCharInPosition(e_set, -2),
            RejectUnlessLessThanLength(3)
        ]  #A'B'C
    ]

    group2 = [
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - y_set, -1),
            RejectUnlessLessThanLength(3)
        ],  # AB
        [RejectUnlessCharInPosition(y_set, -1),
         RejectUnlessLessThanLength(3)],  #A'B
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - y_set, -1),
            RejectUnlessGreaterThanLength(2)
        ]  #AB'
    ]

    group3 = [
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -1),
            RejectUnlessCharInPosition(bgp_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #ABC
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -1),
            RejectUnlessCharInPosition(bgp_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #ABC'
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #AB'C
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #AB'C'
        [
            RejectUnlessCharInPosition(bgp_set, -1),
            RejectUnlessCharInPosition(bgp_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #A'BC
        [
            RejectUnlessCharInPosition(bgp_set, -1),
            RejectUnlessCharInPosition(bgp_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #A'BC'
        [
            RejectUnlessCharInPosition(bgp_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #A'B'C
    ]

    group4 = [
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - e_set, -1),
            RejectUnlessLessThanLength(3)
        ],  # AB
        [RejectUnlessCharInPosition(e_set, -1),
         RejectUnlessLessThanLength(3)],  #A'B
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - e_set, -1),
            RejectUnlessGreaterThanLength(2)
        ]  #AB'
    ]

    dup = {}
    P_valid_cases = []
    for element in itertools.product(group1, group2, group3, group4):
        tmp_dep_list = DependencyList()
        for group in element:
            for dependency in group:
                # generate a dependency list that represents the "and" relationship
                tmp_dep_list.prepend_dependency(deepcopy(dependency))
            #print()
        tmp_dep_list.clean_list()
        #print(tmp_dep_list)
        # It's impossible to get satisfied here
        # Note <3 part are all conflicting with <3 requirement outside, so remove all of them.
        if tmp_dep_list.is_active() and len(
                tmp_dep_list.get_active()) != 0 and frozenset(
                    tmp_dep_list.this_list) not in dup:  #
            for dep_list in tmp_dep_list.get_active():
                if dep_list.get_type() == 6 and dep_list.get_len() == 3:
                    break
            else:
                P_valid_cases.append(tmp_dep_list)
                dup[frozenset(tmp_dep_list.this_list)] = None

    return P_valid_cases


P_valid_cases = precompute_P_valid_cases()


def precompute_I_valid_cases():
    """
    precompute all valid I cases
    (
    (s[-3] not in "i"     or s[-2] not in "n"  or s[-1] in "g"  or len < 3) or
    (s[-1] not in "aeiou"                                       or len < 3) or
    (s[-1] not in "bgp"   or s[-2] in "bgp"                     or len < 3) or
    )
    """
    aeiou_set = set("aeiou")
    bgp_set = set("bgp")
    i_set = set("i")
    n_set = set("n")
    g_set = set("g")

    group1 = [
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - i_set, -3),
            RejectUnlessCharInPosition(Dicts.classes['z'] - n_set, -2),
            RejectUnlessCharInPosition(Dicts.classes['z'] - g_set, -1),
            RejectUnlessLessThanLength(3)
        ],  #ABCD
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - i_set, -3),
            RejectUnlessCharInPosition(Dicts.classes['z'] - n_set, -2),
            RejectUnlessCharInPosition(Dicts.classes['z'] - g_set, -1),
            RejectUnlessGreaterThanLength(2)
        ],  #ABCD'
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - i_set, -3),
            RejectUnlessCharInPosition(Dicts.classes['z'] - n_set, -2),
            RejectUnlessCharInPosition(g_set, -1),
            RejectUnlessLessThanLength(3)
        ],  #ABC'D
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - i_set, -3),
            RejectUnlessCharInPosition(Dicts.classes['z'] - n_set, -2),
            RejectUnlessCharInPosition(g_set, -1),
            RejectUnlessGreaterThanLength(2)
        ],  #ABC'D'
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - i_set, -3),
            RejectUnlessCharInPosition(n_set, -2),
            RejectUnlessCharInPosition(Dicts.classes['z'] - g_set, -1),
            RejectUnlessLessThanLength(3)
        ],  #AB'CD
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - i_set, -3),
            RejectUnlessCharInPosition(n_set, -2),
            RejectUnlessCharInPosition(Dicts.classes['z'] - g_set, -1),
            RejectUnlessGreaterThanLength(2)
        ],  #AB'CD'
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - i_set, -3),
            RejectUnlessCharInPosition(n_set, -2),
            RejectUnlessCharInPosition(g_set, -1),
            RejectUnlessLessThanLength(3)
        ],  #AB'C'D
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - i_set, -3),
            RejectUnlessCharInPosition(n_set, -2),
            RejectUnlessCharInPosition(g_set, -1),
            RejectUnlessGreaterThanLength(2)
        ],  #AB'C'D'
        [
            RejectUnlessCharInPosition(i_set, -3),
            RejectUnlessCharInPosition(Dicts.classes['z'] - n_set, -2),
            RejectUnlessCharInPosition(Dicts.classes['z'] - g_set, -1),
            RejectUnlessLessThanLength(3)
        ],  #A'BCD
        [
            RejectUnlessCharInPosition(i_set, -3),
            RejectUnlessCharInPosition(Dicts.classes['z'] - n_set, -2),
            RejectUnlessCharInPosition(Dicts.classes['z'] - g_set, -1),
            RejectUnlessGreaterThanLength(2)
        ],  #A'BCD'
        [
            RejectUnlessCharInPosition(i_set, -3),
            RejectUnlessCharInPosition(Dicts.classes['z'] - n_set, -2),
            RejectUnlessCharInPosition(g_set, -1),
            RejectUnlessLessThanLength(3)
        ],  #A'BC'D
        [
            RejectUnlessCharInPosition(i_set, -3),
            RejectUnlessCharInPosition(Dicts.classes['z'] - n_set, -2),
            RejectUnlessCharInPosition(g_set, -1),
            RejectUnlessGreaterThanLength(2)
        ],  #A'BC'D'
        [
            RejectUnlessCharInPosition(i_set, -3),
            RejectUnlessCharInPosition(n_set, -2),
            RejectUnlessCharInPosition(Dicts.classes['z'] - g_set, -1),
            RejectUnlessLessThanLength(3)
        ],  #A'B'CD
        [
            RejectUnlessCharInPosition(i_set, -3),
            RejectUnlessCharInPosition(n_set, -2),
            RejectUnlessCharInPosition(Dicts.classes['z'] - g_set, -1),
            RejectUnlessGreaterThanLength(2)
        ],  #A'B'CD'
        [
            RejectUnlessCharInPosition(i_set, -3),
            RejectUnlessCharInPosition(n_set, -2),
            RejectUnlessCharInPosition(g_set, -1),
            RejectUnlessLessThanLength(3)
        ]  #A'B'C'D
    ]

    group2 = [
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - aeiou_set, -1),
            RejectUnlessLessThanLength(3)
        ],  # AB
        [
            RejectUnlessCharInPosition(aeiou_set, -1),
            RejectUnlessLessThanLength(3)
        ],  #A'B
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - aeiou_set, -1),
            RejectUnlessGreaterThanLength(2)
        ]  #AB'
    ]

    group3 = [
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -1),
            RejectUnlessCharInPosition(bgp_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #ABC
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -1),
            RejectUnlessCharInPosition(bgp_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #ABC'
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #AB'C
        [
            RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #AB'C'
        [
            RejectUnlessCharInPosition(bgp_set, -1),
            RejectUnlessCharInPosition(bgp_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #A'BC
        [
            RejectUnlessCharInPosition(bgp_set, -1),
            RejectUnlessCharInPosition(bgp_set, -2),
            RejectUnlessGreaterThanLength(2)
        ],  #A'BC'
        [
            RejectUnlessCharInPosition(bgp_set, -1),
            RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -2),
            RejectUnlessLessThanLength(3)
        ],  #A'B'C
    ]

    dup = {}
    I_valid_cases = []
    for element in itertools.product(group1, group2, group3):
        tmp_dep_list = DependencyList()
        for group in element:
            for dependency in group:
                # generate a dependency list that represents the "and" relationship
                tmp_dep_list.prepend_dependency(deepcopy(dependency))
        tmp_dep_list.clean_list()
        # It's impossible to get satisfied here
        if tmp_dep_list.is_active() and len(
                tmp_dep_list.get_active()) != 0 and frozenset(
                    tmp_dep_list.this_list) not in dup:  #
            I_valid_cases.append(tmp_dep_list)
            dup[frozenset(tmp_dep_list.this_list)] = None

    return I_valid_cases


I_valid_cases = precompute_I_valid_cases()


class FeatureExtraction():
    """ A class containing only static functions to extract features """

    @staticmethod
    def extract_colon_command(subrule_dependency, rule):
        """ no-op: do nothing to the input word

        Effects on Dependency:
            None, just return in input

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        return subrule_dependency

    @staticmethod
    def extract_l_command(subrule_dependency, rule):
        """ l   lowercase all letters: paSSword -> password

        Effects on Dependency:
            change each lowercase letter into a set of itself and its uppercase counterpart

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    # Non reject length type
                    if 5 >= read_only_depend.dependency_type >= 1:
                        depend = deepcopy(read_only_depend)

                        # update charset
                        ori_set = depend.get_chars()
                        others = set(
                            x for x in ori_set
                            if x not in Dicts.classes['a'])  # Non-letters
                        intersect = set(x for x in ori_set
                                        if x in Dicts.classes['l'])  # Lower
                        dest_set = intersect | set(
                            x.upper() for x in intersect) | others  # Reverse

                        depend.set_chars(dest_set)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 6 <= read_only_depend.dependency_type <= 7:
                        depend = deepcopy(read_only_depend)
                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_u_command(subrule_dependency, rule):
        """ u   uppercase all letters: paSSword -> PASSWORD

        Effects on Dependency:
            No effect on length, switch chars

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        depend = deepcopy(read_only_depend)

                        ori_set = depend.get_chars()
                        others = set(
                            x for x in ori_set
                            if x not in Dicts.classes['a'])  # Non-letters
                        intersect = set(
                            x for x in ori_set if x in Dicts.classes['u'])
                        dest_set = others | intersect | set(
                            x.lower() for x in intersect)
                        depend.set_chars(dest_set)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        depend = deepcopy(read_only_depend)

                        ori_set = depend.get_chars()
                        others = set(
                            x for x in ori_set
                            if x not in Dicts.classes['a'])  # Non-letters
                        intersect = set(
                            x for x in ori_set if x in Dicts.classes['u'])
                        dest_set = others | intersect | set(
                            x.lower() for x in intersect)
                        depend.set_chars(dest_set)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)
                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend = deepcopy(read_only_depend)
                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend = deepcopy(read_only_depend)
                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        others = set(
                            x for x in chars
                            if x not in Dicts.classes['a'])  # Non-letters
                        intersect = set(
                            x for x in chars if x in Dicts.classes['u'])
                        dest_set = others | intersect | set(
                            x.lower() for x in intersect)

                        one_dep_list.prepend_dependency(
                            read_only_depend.make_new(from_idx, to_idx, number,
                                                      dest_set))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_c_command(subrule_dependency, rule):
        """ c   capitalize first letter, lowercase rest: passWord -> Password

        Effects on Dependency:
            No effect on length, switch chars

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if read_only_depend.dependency_type == 1:
                        #A Trick to play
                        ori_set = read_only_depend.get_chars()
                        upper_set = set(x for x in ori_set
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in ori_set
                                        if x in Dicts.classes['l'])  # lower
                        #In this case c command doesn't change anything
                        if (lower_set | set(x.upper() for x in lower_set)) == (
                                upper_set | set(x.lower() for x in upper_set)):
                            #print("Play Trick In c Command\n")
                            depend0 = deepcopy(read_only_depend)
                            one_dep_list.prepend_dependency(depend0)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)
                            continue

                        # No op
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        #Normal procedure
                        def general_prepend_dependency_to_list(
                                char_set_pos_0,
                                char_set_after_1,
                                pos_0_satisfies,
                                other_deps=[]):
                            intersect = char_set_pos_0 & char_set_after_1

                            if pos_0_satisfies == True:
                                addition_num = -1
                            else:
                                addition_num = 0

                            dep_lis_intersect = deepcopy(one_dep_list)

                            if not (chars_set_after_1 == set() and
                                    (read_only_depend.get_number() + 1 +
                                     addition_num) <= 0):
                                depend_num_char_after_1 = read_only_depend.make_new(
                                    chars_set_after_1,
                                    read_only_depend.get_number() + 1 +
                                    addition_num)
                                dep_lis_intersect.prepend_dependency(
                                    depend_num_char_after_1)

                                depend_char_at_pos_0_intersect = RejectUnlessCharInPosition(
                                    intersect, 0)
                                dep_lis_intersect.prepend_dependency(
                                    depend_char_at_pos_0_intersect)

                                for val in other_deps:
                                    dep_lis_intersect.prepend_dependency(
                                        deepcopy(val))

                                save_split_dep_lists.append_dependency_list(
                                    dep_lis_intersect)
                            else:  # rejected
                                pass

                            #Char at 0 is not in the chars checked after 1
                            dep_lis_rest = deepcopy(one_dep_list)
                            if not (chars_set_after_1 == set() and
                                    (read_only_depend.get_number() +
                                     addition_num) <= 0):
                                depend_num_char_after_1 = read_only_depend.make_new(
                                    chars_set_after_1,
                                    read_only_depend.get_number() +
                                    addition_num)
                                dep_lis_rest.prepend_dependency(
                                    depend_num_char_after_1)

                                depend_char_at_pos_0_rest = RejectUnlessCharInPosition(
                                    char_set_pos_0 - char_set_after_1, 0)
                                dep_lis_rest.prepend_dependency(
                                    depend_char_at_pos_0_rest)

                                for val in other_deps:
                                    dep_lis_rest.prepend_dependency(
                                        deepcopy(val))
                                save_split_dep_lists.append_dependency_list(
                                    dep_lis_rest)

                            else:  # rejected
                                pass

                        # how it works
                        ori_set = read_only_depend.get_chars()

                        non_letter_set = set(
                            x for x in ori_set
                            if x not in Dicts.classes['a'])  # Non-letters
                        upper_set = set(x for x in ori_set
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in ori_set
                                        if x in Dicts.classes['l'])  # lower

                        chars_set_after_1 = lower_set | set(
                            x.upper() for x in lower_set) | non_letter_set
                        #Char At Position 0 that will satisfy the / command
                        char_set_at_0_satisfies = upper_set | set(
                            x.lower()
                            for x in upper_set) | non_letter_set  # Reverse
                        #Char At Position 0 doesn't satisfy the / command
                        char_set_at_0_rest = set(
                            Dicts.classes['z']) - char_set_at_0_satisfies

                        general_prepend_dependency_to_list(
                            char_set_at_0_satisfies, chars_set_after_1, True,
                            [])
                        general_prepend_dependency_to_list(
                            char_set_at_0_rest, chars_set_after_1, False, [])

                    elif read_only_depend.dependency_type == 2:
                        #dependency type

                        #A Trick to play
                        ori_set = read_only_depend.get_chars()
                        upper_set = set(x for x in ori_set
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in ori_set
                                        if x in Dicts.classes['l'])  # lower
                        #In this case c command doesn't change anything
                        if (lower_set | set(x.upper() for x in lower_set)) == (
                                upper_set | set(x.lower() for x in upper_set)):
                            #print("Play Trick In c Command\n")
                            depend0 = deepcopy(read_only_depend)
                            one_dep_list.prepend_dependency(depend0)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)
                            continue

                        # No op
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        #Normal procedure
                        def general_prepend_dependency_to_list(
                                char_set_pos_0,
                                char_set_after_1,
                                pos_0_satisfies,
                                other_deps=[]):
                            intersect = char_set_pos_0 & char_set_after_1

                            if pos_0_satisfies == True:
                                addition_num = -1
                            else:
                                addition_num = 0

                            dep_lis_intersect = deepcopy(one_dep_list)

                            if not (chars_set_after_1 == set() and
                                    (read_only_depend.get_number() + 1 +
                                     addition_num) <= 0):
                                depend_num_char_after_1 = read_only_depend.make_new(
                                    chars_set_after_1,
                                    read_only_depend.get_number() + 1 +
                                    addition_num)
                                dep_lis_intersect.prepend_dependency(
                                    depend_num_char_after_1)

                            depend_char_at_pos_0_intersect = RejectUnlessCharInPosition(
                                intersect, 0)
                            dep_lis_intersect.prepend_dependency(
                                depend_char_at_pos_0_intersect)

                            for val in other_deps:
                                dep_lis_intersect.prepend_dependency(
                                    deepcopy(val))

                            save_split_dep_lists.append_dependency_list(
                                dep_lis_intersect)

                            #Char at 0 is not in the chars checked after 1
                            dep_lis_rest = deepcopy(one_dep_list)
                            if not (chars_set_after_1 == set() and
                                    (read_only_depend.get_number() +
                                     addition_num) <= 0):
                                depend_num_char_after_1 = read_only_depend.make_new(
                                    chars_set_after_1,
                                    read_only_depend.get_number() +
                                    addition_num)
                                dep_lis_rest.prepend_dependency(
                                    depend_num_char_after_1)

                            depend_char_at_pos_0_rest = RejectUnlessCharInPosition(
                                char_set_pos_0 - char_set_after_1, 0)
                            dep_lis_rest.prepend_dependency(
                                depend_char_at_pos_0_rest)

                            for val in other_deps:
                                dep_lis_rest.prepend_dependency(deepcopy(val))
                            save_split_dep_lists.append_dependency_list(
                                dep_lis_rest)

                        # how it works
                        ori_set = read_only_depend.get_chars()

                        non_letter_set = set(
                            x for x in ori_set
                            if x not in Dicts.classes['a'])  # Non-letters
                        upper_set = set(x for x in ori_set
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in ori_set
                                        if x in Dicts.classes['l'])  # lower

                        chars_set_after_1 = lower_set | set(
                            x.upper() for x in lower_set) | non_letter_set
                        #Char At Position 0 that will satisfy the / command
                        char_set_at_0_satisfies = upper_set | set(
                            x.lower()
                            for x in upper_set) | non_letter_set  # Reverse
                        #Char At Position 0 doesn't satisfy the / command
                        char_set_at_0_rest = set(
                            Dicts.classes['z']) - char_set_at_0_satisfies

                        general_prepend_dependency_to_list(
                            char_set_at_0_satisfies, chars_set_after_1, True,
                            [])
                        general_prepend_dependency_to_list(
                            char_set_at_0_rest, chars_set_after_1, False, [])

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        #Same as above. Change the case of chars in char set.
                        #If check positive position
                        #If check negative position

                        #A Trick to play
                        ori_set = read_only_depend.get_chars()
                        upper_set = set(x for x in ori_set
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in ori_set
                                        if x in Dicts.classes['l'])  # lower
                        #In this case c command doesn't change anything
                        if (lower_set | set(x.upper() for x in lower_set)) == (
                                upper_set | set(x.lower() for x in upper_set)):
                            #print("Play Trick In c Command\n")
                            depend0 = deepcopy(read_only_depend)
                            one_dep_list.prepend_dependency(depend0)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)
                            continue

                        #Normal procedure
                        ori_pos = read_only_depend.get_position()

                        ori_set = read_only_depend.get_chars()
                        non_letter_set = set(
                            x for x in ori_set
                            if x not in Dicts.classes['a'])  # Non-letters
                        upper_set = set(x for x in ori_set
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in ori_set
                                        if x in Dicts.classes['l'])  # lower

                        if ori_pos >= 0:
                            if ori_pos == 0:
                                dest_set = non_letter_set | upper_set | set(
                                    x.lower() for x in upper_set)

                            else:
                                dest_set = non_letter_set | lower_set | set(
                                    x.upper() for x in lower_set)

                            depend = deepcopy(read_only_depend)
                            depend.set_chars(dest_set)
                            one_dep_list.prepend_dependency(depend)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)

                        elif ori_pos < 0:

                            equal_len = abs(ori_pos)

                            #if length = abs(oir_pos):
                            depend_len_upper = RejectUnlessGreaterThanLength(
                                equal_len - 1)
                            depend_len_lower = RejectUnlessLessThanLength(
                                equal_len + 1)

                            dest_set = non_letter_set | upper_set | set(
                                x.lower() for x in upper_set)

                            depend = deepcopy(read_only_depend)
                            depend.set_chars(dest_set)
                            equal_dep_list = deepcopy(one_dep_list)
                            equal_dep_list.prepend_dependency(depend)
                            equal_dep_list.prepend_dependency(depend_len_lower)
                            equal_dep_list.prepend_dependency(depend_len_upper)
                            save_split_dep_lists.append_dependency_list(
                                equal_dep_list)

                            #if length != abs(ori_pos)
                            depend_len_less = RejectUnlessGreaterThanLength(
                                equal_len)
                            depend_len_more = RejectUnlessLessThanLength(
                                equal_len)

                            dest_set = non_letter_set | lower_set | set(
                                x.upper() for x in lower_set)

                            #type1
                            depend = deepcopy(read_only_depend)
                            depend.set_chars(dest_set)
                            less_dep_list = deepcopy(one_dep_list)
                            less_dep_list.prepend_dependency(depend)
                            less_dep_list.prepend_dependency(depend_len_less)
                            save_split_dep_lists.append_dependency_list(
                                less_dep_list)

                            #type2
                            depend = deepcopy(read_only_depend)
                            depend.set_chars(dest_set)
                            more_dep_list = deepcopy(one_dep_list)
                            more_dep_list.prepend_dependency(depend)
                            more_dep_list.prepend_dependency(depend_len_more)
                            save_split_dep_lists.append_dependency_list(
                                more_dep_list)

                        else:
                            raise ValueError("ValueError Ori_pos")

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        #c command doesn't affect length. Do Nothing
                        depend0 = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend0)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        #c command doesn't affect length. Do Nothing
                        depend0 = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend0)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        #A Trick to play
                        upper_set = set(x for x in chars
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in chars
                                        if x in Dicts.classes['l'])  # lower
                        #In this case c command doesn't change anything
                        if (lower_set | set(x.upper() for x in lower_set)) == (
                                upper_set | set(x.lower() for x in upper_set)):
                            one_dep_list.prepend_dependency(read_only_depend)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)
                            continue

                        if from_idx >= 0:

                            # everything is lowercased
                            if from_idx >= 1:
                                others = set(x for x in chars if x not in Dicts.
                                             classes['a'])  # Non-letters
                                intersect = set(
                                    x for x in chars if x in Dicts.classes['l'])
                                dest_set = others | intersect | set(
                                    x.upper() for x in intersect)

                                one_dep_list.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number, dest_set))
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                            # pos 0 is included
                            else:

                                # if char at pos 0 contributes to number
                                dep_list_case_1 = deepcopy(one_dep_list)

                                others = set(x for x in chars if x not in Dicts.
                                             classes['a'])  # Non-letters
                                upper_intersect = set(
                                    x for x in chars if x in Dicts.classes['u'])
                                upper_dest_set = others | upper_intersect | set(
                                    x.lower() for x in upper_intersect)

                                intersect = set(
                                    x for x in chars if x in Dicts.classes['l'])
                                dest_set = others | intersect | set(
                                    x.upper() for x in intersect)

                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        upper_dest_set, 0))
                                try:
                                    # if creation of dependency failed, this part is ignored
                                    tmp_dep = read_only_depend.make_new(
                                        1, to_idx, number - 1, dest_set)
                                    dep_list_case_1.prepend_dependency(tmp_dep)
                                except:
                                    pass
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                                # else doesn't contributes to number
                                dep_list_case_2 = deepcopy(one_dep_list)
                                dep_list_case_2.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) -
                                        upper_dest_set, 0))
                                try:
                                    tmp_dep = read_only_depend.make_new(
                                        1, to_idx, number, dest_set)
                                    dep_list_case_2.prepend_dependency(tmp_dep)
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_2)
                                #rejected
                                except:
                                    pass

                        else:
                            # case1: if len > -from_idx:
                            # this one doesn't matter
                            dep_list_case_1 = deepcopy(one_dep_list)
                            others = set(
                                x for x in chars
                                if x not in Dicts.classes['a'])  # Non-letters
                            intersect = set(
                                x for x in chars if x in Dicts.classes['l'])
                            dest_set = others | intersect | set(
                                x.upper() for x in intersect)

                            dep_list_case_1.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number, dest_set))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(-from_idx))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1)

                            # case2: if len == -from_idx, then you know
                            # if char at pos 0 contributes to number
                            dep_list_case_2 = deepcopy(one_dep_list)

                            others = set(
                                x for x in chars
                                if x not in Dicts.classes['a'])  # Non-letters
                            upper_intersect = set(
                                x for x in chars if x in Dicts.classes['u'])
                            upper_dest_set = others | upper_intersect | set(
                                x.lower() for x in upper_intersect)

                            dep_list_case_2.prepend_dependency(
                                RejectUnlessCharInPosition(upper_dest_set, 0))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessLessThanLength(-from_idx + 1))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessGreaterThanLength(-from_idx - 1))
                            try:
                                tmp_dep = read_only_depend.make_new(
                                    from_idx + 1, to_idx, number - 1, dest_set)
                                dep_list_case_2.prepend_dependency(tmp_dep)
                            except:
                                pass
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_2)

                            # else doesn't contributes to number
                            dep_list_case_3 = deepcopy(one_dep_list)
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) - upper_dest_set,
                                    0))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessLessThanLength(-from_idx + 1))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessGreaterThanLength(-from_idx - 1))

                            try:
                                tmp_dep = read_only_depend.make_new(
                                    from_idx + 1, to_idx, number, dest_set)
                                dep_list_case_3.prepend_dependency(tmp_dep)
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_3)
                            #rejected
                            except:
                                pass

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_C_command(subrule_dependency, rule):
        """ C   lowercase first char, uppercase rest: Pas$Word -> pAS$WORD

        Effects on Dependency:
            No effect on length, switch cases.

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if read_only_depend.dependency_type == 1:
                        #A Trick to play
                        ori_set = read_only_depend.get_chars()
                        upper_set = set(x for x in ori_set
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in ori_set
                                        if x in Dicts.classes['l'])  # lower
                        #In this case c command doesn't change anything
                        if (lower_set | set(x.upper() for x in lower_set)) == (
                                upper_set | set(x.lower() for x in upper_set)):
                            #print("Play Trick In c Command\n")
                            depend0 = deepcopy(read_only_depend)
                            one_dep_list.prepend_dependency(depend0)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)
                            continue

                        # No op
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        def general_prepend_dependency_to_list(
                                char_set_pos_0,
                                char_set_after_1,
                                pos_0_satisfies,
                                other_deps=[]):
                            intersect = char_set_pos_0 & char_set_after_1

                            if pos_0_satisfies == True:
                                addition_num = -1
                            else:
                                addition_num = 0

                            dep_lis_intersect = deepcopy(one_dep_list)

                            if not (chars_set_after_1 == set() and
                                    (read_only_depend.get_number() + 1 +
                                     addition_num) <= 0):
                                depend_num_char_after_1 = read_only_depend.make_new(
                                    chars_set_after_1,
                                    read_only_depend.get_number() + 1 +
                                    addition_num)
                                dep_lis_intersect.prepend_dependency(
                                    depend_num_char_after_1)
                                depend_char_at_pos_0_intersect = RejectUnlessCharInPosition(
                                    intersect, 0)
                                dep_lis_intersect.prepend_dependency(
                                    depend_char_at_pos_0_intersect)
                                for val in other_deps:
                                    dep_lis_intersect.prepend_dependency(
                                        deepcopy(val))

                                save_split_dep_lists.append_dependency_list(
                                    dep_lis_intersect)
                            else:  # rejected
                                pass

                            #Char at 0 is not in the chars checked after 1
                            dep_lis_rest = deepcopy(one_dep_list)
                            if not (chars_set_after_1 == set() and
                                    (read_only_depend.get_number() +
                                     addition_num) <= 0):
                                depend_num_char_after_1 = read_only_depend.make_new(
                                    chars_set_after_1,
                                    read_only_depend.get_number() +
                                    addition_num)
                                dep_lis_rest.prepend_dependency(
                                    depend_num_char_after_1)
                                depend_char_at_pos_0_rest = RejectUnlessCharInPosition(
                                    char_set_pos_0 - char_set_after_1, 0)
                                dep_lis_rest.prepend_dependency(
                                    depend_char_at_pos_0_rest)
                                for val in other_deps:
                                    dep_lis_rest.prepend_dependency(
                                        deepcopy(val))
                                save_split_dep_lists.append_dependency_list(
                                    dep_lis_rest)
                            else:  # rejected
                                pass

                        # how it works
                        ori_set = read_only_depend.get_chars()

                        non_letter_set = set(
                            x for x in ori_set
                            if x not in Dicts.classes['a'])  # Non-letters
                        upper_set = set(x for x in ori_set
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in ori_set
                                        if x in Dicts.classes['l'])  # lower

                        chars_set_after_1 = upper_set | set(
                            x.lower() for x in upper_set) | non_letter_set
                        #Char At Position 0 that will satisfy the / command
                        char_set_at_0_satisfies = lower_set | set(
                            x.upper()
                            for x in lower_set) | non_letter_set  # Reverse
                        #Char At Position 0 doesn't satisfy the / command
                        char_set_at_0_rest = set(
                            Dicts.classes['z']) - char_set_at_0_satisfies

                        general_prepend_dependency_to_list(
                            char_set_at_0_satisfies, chars_set_after_1, True,
                            [])
                        general_prepend_dependency_to_list(
                            char_set_at_0_rest, chars_set_after_1, False, [])

                    elif read_only_depend.dependency_type == 2:
                        #A Trick to play
                        ori_set = read_only_depend.get_chars()
                        upper_set = set(x for x in ori_set
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in ori_set
                                        if x in Dicts.classes['l'])  # lower
                        #In this case c command doesn't change anything
                        if (lower_set | set(x.upper() for x in lower_set)) == (
                                upper_set | set(x.lower() for x in upper_set)):
                            #print("Play Trick In c Command\n")
                            depend0 = deepcopy(read_only_depend)
                            one_dep_list.prepend_dependency(depend0)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)
                            continue

                        # No op
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        def general_prepend_dependency_to_list(
                                char_set_pos_0,
                                char_set_after_1,
                                pos_0_satisfies,
                                other_deps=[]):
                            intersect = char_set_pos_0 & char_set_after_1

                            if pos_0_satisfies == True:
                                addition_num = -1
                            else:
                                addition_num = 0

                            dep_lis_intersect = deepcopy(one_dep_list)

                            if not (chars_set_after_1 == set() and
                                    (read_only_depend.get_number() + 1 +
                                     addition_num) <= 0):
                                depend_num_char_after_1 = read_only_depend.make_new(
                                    chars_set_after_1,
                                    read_only_depend.get_number() + 1 +
                                    addition_num)
                                dep_lis_intersect.prepend_dependency(
                                    depend_num_char_after_1)

                            depend_char_at_pos_0_intersect = RejectUnlessCharInPosition(
                                intersect, 0)
                            dep_lis_intersect.prepend_dependency(
                                depend_char_at_pos_0_intersect)

                            for val in other_deps:
                                dep_lis_intersect.prepend_dependency(
                                    deepcopy(val))

                            save_split_dep_lists.append_dependency_list(
                                dep_lis_intersect)

                            #Char at 0 is not in the chars checked after 1
                            dep_lis_rest = deepcopy(one_dep_list)
                            if not (chars_set_after_1 == set() and
                                    (read_only_depend.get_number() +
                                     addition_num) <= 0):
                                depend_num_char_after_1 = read_only_depend.make_new(
                                    chars_set_after_1,
                                    read_only_depend.get_number() +
                                    addition_num)
                                dep_lis_rest.prepend_dependency(
                                    depend_num_char_after_1)

                            depend_char_at_pos_0_rest = RejectUnlessCharInPosition(
                                char_set_pos_0 - char_set_after_1, 0)
                            dep_lis_rest.prepend_dependency(
                                depend_char_at_pos_0_rest)

                            for val in other_deps:
                                dep_lis_rest.prepend_dependency(deepcopy(val))
                            save_split_dep_lists.append_dependency_list(
                                dep_lis_rest)

                        # how it works
                        ori_set = read_only_depend.get_chars()

                        non_letter_set = set(
                            x for x in ori_set
                            if x not in Dicts.classes['a'])  # Non-letters
                        upper_set = set(x for x in ori_set
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in ori_set
                                        if x in Dicts.classes['l'])  # lower

                        chars_set_after_1 = upper_set | set(
                            x.lower() for x in upper_set) | non_letter_set
                        #Char At Position 0 that will satisfy the / command
                        char_set_at_0_satisfies = lower_set | set(
                            x.upper()
                            for x in lower_set) | non_letter_set  # Reverse
                        #Char At Position 0 doesn't satisfy the / command
                        char_set_at_0_rest = set(
                            Dicts.classes['z']) - char_set_at_0_satisfies

                        general_prepend_dependency_to_list(
                            char_set_at_0_satisfies, chars_set_after_1, True,
                            [])
                        general_prepend_dependency_to_list(
                            char_set_at_0_rest, chars_set_after_1, False, [])

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        #Same as above. Change the case of chars in char set.
                        #If check positive position
                        #If check negative position

                        ori_pos = read_only_depend.get_position()

                        ori_set = read_only_depend.get_chars()
                        non_letter_set = set(
                            x for x in ori_set
                            if x not in Dicts.classes['a'])  # Non-letters
                        upper_set = set(x for x in ori_set
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in ori_set
                                        if x in Dicts.classes['l'])  # lower

                        if ori_pos >= 0:
                            if ori_pos == 0:
                                dest_set = non_letter_set | lower_set | set(
                                    x.upper() for x in lower_set)

                            else:
                                dest_set = non_letter_set | upper_set | set(
                                    x.lower() for x in upper_set)

                            depend = deepcopy(read_only_depend)
                            depend.set_chars(dest_set)
                            one_dep_list.prepend_dependency(depend)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)

                        elif ori_pos < 0:

                            equal_len = abs(ori_pos)

                            #if length = abs(oir_pos):
                            depend_len_upper = RejectUnlessGreaterThanLength(
                                equal_len - 1)
                            depend_len_lower = RejectUnlessLessThanLength(
                                equal_len + 1)

                            dest_set = non_letter_set | lower_set | set(
                                x.upper() for x in lower_set)

                            depend = deepcopy(read_only_depend)
                            depend.set_chars(dest_set)
                            equal_dep_list = deepcopy(one_dep_list)
                            equal_dep_list.prepend_dependency(depend)
                            equal_dep_list.prepend_dependency(depend_len_lower)
                            equal_dep_list.prepend_dependency(depend_len_upper)
                            save_split_dep_lists.append_dependency_list(
                                equal_dep_list)

                            #if length != abs(ori_pos)
                            depend_len_less = RejectUnlessGreaterThanLength(
                                equal_len)
                            depend_len_more = RejectUnlessLessThanLength(
                                equal_len)

                            dest_set = non_letter_set | upper_set | set(
                                x.lower() for x in upper_set)

                            #type1
                            depend = deepcopy(read_only_depend)
                            depend.set_chars(dest_set)
                            less_dep_list = deepcopy(one_dep_list)
                            less_dep_list.prepend_dependency(depend)
                            less_dep_list.prepend_dependency(depend_len_less)
                            save_split_dep_lists.append_dependency_list(
                                less_dep_list)

                            #type2
                            depend = deepcopy(read_only_depend)
                            depend.set_chars(dest_set)
                            more_dep_list = deepcopy(one_dep_list)
                            more_dep_list.prepend_dependency(depend)
                            more_dep_list.prepend_dependency(depend_len_more)
                            save_split_dep_lists.append_dependency_list(
                                more_dep_list)

                        else:
                            raise ValueError("ValueError Ori_pos")

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        #c command doesn't affect length. Do Nothing
                        depend0 = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend0)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        #c command doesn't affect length. Do Nothing
                        depend0 = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend0)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        #A Trick to play
                        upper_set = set(x for x in chars
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in chars
                                        if x in Dicts.classes['l'])  # lower
                        #In this case c command doesn't change anything
                        if (lower_set | set(x.upper() for x in lower_set)) == (
                                upper_set | set(x.lower() for x in upper_set)):
                            one_dep_list.prepend_dependency(read_only_depend)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)
                            continue

                        if from_idx >= 0:

                            # everything is lowercased
                            if from_idx >= 1:
                                others = set(x for x in chars if x not in Dicts.
                                             classes['a'])  # Non-letters
                                intersect = set(
                                    x for x in chars if x in Dicts.classes['u'])
                                dest_set = others | intersect | set(
                                    x.lower() for x in intersect)

                                one_dep_list.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number, dest_set))
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                            # pos 0 is included
                            else:

                                # if char at pos 0 contributes to number
                                dep_list_case_1 = deepcopy(one_dep_list)

                                others = set(x for x in chars if x not in Dicts.
                                             classes['a'])  # Non-letters
                                lower_intersect = set(
                                    x for x in chars if x in Dicts.classes['l'])
                                lower_dest_set = others | lower_intersect | set(
                                    x.upper() for x in lower_intersect)

                                intersect = set(
                                    x for x in chars if x in Dicts.classes['u'])
                                dest_set = others | intersect | set(
                                    x.lower() for x in intersect)

                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        lower_dest_set, 0))
                                try:
                                    tmp_dep = read_only_depend.make_new(
                                        1, to_idx, number - 1, dest_set)
                                    dep_list_case_1.prepend_dependency(tmp_dep)
                                except:
                                    pass
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                                # else doesn't contributes to number
                                dep_list_case_2 = deepcopy(one_dep_list)
                                dep_list_case_2.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) -
                                        lower_dest_set, 0))
                                try:
                                    tmp_dep = read_only_depend.make_new(
                                        1, to_idx, number, dest_set)
                                    dep_list_case_2.prepend_dependency(tmp_dep)
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_2)
                                #rejected
                                except:
                                    pass

                        else:
                            # case1: if len > -from_idx:
                            # this one doesn't matter
                            dep_list_case_1 = deepcopy(one_dep_list)
                            others = set(
                                x for x in chars
                                if x not in Dicts.classes['a'])  # Non-letters
                            intersect = set(
                                x for x in chars if x in Dicts.classes['u'])
                            dest_set = others | intersect | set(
                                x.lower() for x in intersect)

                            dep_list_case_1.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number, dest_set))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(-from_idx))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1)

                            # case2: if len == -from_idx, then you know
                            # if char at pos 0 contributes to number
                            dep_list_case_2 = deepcopy(one_dep_list)

                            others = set(
                                x for x in chars
                                if x not in Dicts.classes['a'])  # Non-letters
                            lower_intersect = set(
                                x for x in chars if x in Dicts.classes['l'])
                            lower_dest_set = others | lower_intersect | set(
                                x.upper() for x in lower_intersect)

                            dep_list_case_2.prepend_dependency(
                                RejectUnlessCharInPosition(lower_dest_set, 0))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessLessThanLength(-from_idx + 1))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessGreaterThanLength(-from_idx - 1))
                            try:
                                tmp_dep = read_only_depend.make_new(
                                    from_idx + 1, to_idx, number - 1, dest_set)
                                dep_list_case_2.prepend_dependency(tmp_dep)
                            except:
                                pass
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_2)

                            # else doesn't contributes to number
                            dep_list_case_3 = deepcopy(one_dep_list)
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) - lower_dest_set,
                                    0))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessLessThanLength(-from_idx + 1))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessGreaterThanLength(-from_idx - 1))

                            try:
                                tmp_dep = read_only_depend.make_new(
                                    from_idx + 1, to_idx, number, dest_set)
                                dep_list_case_3.prepend_dependency(tmp_dep)
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_3)

                            #rejected
                            except:
                                pass

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_t_command(subrule_dependency, rule):
        """ t   toggles the case of all chars: h3llO-> H3LLo

        Effects on Dependency:
            no effect on length, switch cases

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        depend = deepcopy(read_only_depend)

                        ori_set = depend.get_chars()
                        lowered = set(
                            Dicts.toggle.setdefault(x, x) for x in ori_set
                        )  # use setdefault to denote anything other than lower
                        depend.set_chars(lowered)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        depend = deepcopy(read_only_depend)

                        ori_set = depend.get_chars()
                        lowered = set(
                            Dicts.toggle.setdefault(x, x) for x in ori_set)
                        depend.set_chars(lowered)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)
                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend = deepcopy(read_only_depend)
                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend = deepcopy(read_only_depend)
                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        toggled_chars = set(
                            Dicts.toggle.setdefault(x, x) for x in chars
                        )  # use setdefault to denote anything other than lower
                        one_dep_list.prepend_dependency(
                            read_only_depend.make_new(from_idx, to_idx, number,
                                                      toggled_chars))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_r_command(subrule_dependency, rule):
        """ r   Reverses the word: password -> drowssap

        Effects on Dependency:
            reverse the position, doesn't affect length

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    # Reject_If_Contains_Number_Of_Char.
                    # Reject_Unless_Contains_Number_Of_Char
                    if 1 <= read_only_depend.dependency_type <= 2:
                        # Reverse Doesnot change number of chars
                        depend = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        depend = deepcopy(read_only_depend)

                        # Check the counter position.
                        # For example.
                        # =1a is now =(-2)a
                        ori_pos = depend.get_position()

                        dest_pos = -(ori_pos + 1)
                        depend.set_position(dest_pos)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Less_Than_Length
                    # Reject_Unless_Greater_Than_Length
                    elif 6 <= read_only_depend.dependency_type <= 7:
                        # Reverse Doesnot change number of chars
                        depend = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        one_dep_list.prepend_dependency(
                            read_only_depend.make_new(-to_idx, -from_idx,
                                                      number, chars))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_d_command(subrule_dependency, rule):
        """ d   Duplicates word: pass -> passpass

        Effects on Dependency:
            Divide length by two, enumerate position to further investigate

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        return FeatureExtraction.extract_p_N_command(subrule_dependency, "p1")

    @staticmethod
    def extract_f_command(subrule_dependency, rule):
        """ f   Reflects the word: pass -> passssap

        Effects on Dependency:
            Divide length by two, enumerate position to further investigate

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists

        Problem Found: If left_range and right_range have chongdie. (3-5) (3-9)
        You actually want (3-6) (7-8)
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:
                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:

                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    # Reject_If_Contains_Number_Of_Char, It does not appear.
                    if 1 <= read_only_depend.dependency_type <= 2:
                        # No op
                        depend_length_no_op = RejectUnlessGreaterThanLength(
                            int(
                                math.ceil((RUNTIME_CONFIG['max_password_length']
                                           + 1) / 2)) - 1)
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        # OP
                        depend_length_op = RejectUnlessLessThanLength(
                            int(
                                math.ceil(
                                    (RUNTIME_CONFIG['max_password_length'] + 1)
                                    / 2)))

                        depend = deepcopy(read_only_depend)

                        ori_number = depend.get_number()
                        dest_number = int(math.ceil(ori_number * 1.0 / 2))
                        depend.set_number(dest_number)

                        one_dep_list.prepend_dependency(depend)
                        one_dep_list.prepend_dependency(depend_length_op)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        # No op
                        depend_length_no_op = RejectUnlessGreaterThanLength(
                            int(
                                math.ceil((RUNTIME_CONFIG['max_password_length']
                                           + 1) / 2)) - 1)
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        ori_pos = read_only_depend.get_position()
                        # OP
                        depend_length_op = RejectUnlessLessThanLength(
                            int(
                                math.ceil(
                                    (RUNTIME_CONFIG['max_password_length'] + 1)
                                    / 2)))

                        if ori_pos < 0:
                            #2 Possible Situtations.
                            #If Length >= -ori_pos, reverse the value
                            #=(-8) now =7
                            depend = deepcopy(read_only_depend)
                            depend_case_1 = RejectUnlessGreaterThanLength(
                                -ori_pos - 1)
                            depend.set_position(-ori_pos - 1)
                            op_dep_list_1 = deepcopy(one_dep_list)
                            op_dep_list_1.prepend_dependency(
                                deepcopy(depend_length_op))
                            op_dep_list_1.prepend_dependency(depend_case_1)
                            op_dep_list_1.prepend_dependency(depend)
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list_1)

                            #If Length < -ori_pos and Length >= ceil(-ori_pos/2)
                            # =(-5) now
                            for word_len in range(
                                    int(math.ceil(-ori_pos / 2)), -ori_pos):
                                depend = deepcopy(read_only_depend)
                                depend_case_2_upper = RejectUnlessLessThanLength(
                                    word_len + 1)
                                depend_case_2_lower = RejectUnlessGreaterThanLength(
                                    word_len - 1)

                                depend.set_position(ori_pos + word_len)
                                op_dep_list_2 = deepcopy(one_dep_list)
                                op_dep_list_2.prepend_dependency(
                                    deepcopy(depend_length_op))
                                op_dep_list_2.prepend_dependency(
                                    depend_case_2_upper)
                                op_dep_list_2.prepend_dependency(
                                    depend_case_2_lower)
                                op_dep_list_2.prepend_dependency(depend)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_2)

                        elif ori_pos >= 0:
                            # =5a case1: >= 3, <=5. case2: >=6.
                            word_len = int(math.ceil((ori_pos + 1) / 2))

                            while True:  # =5a case1: >= 3, <=5. case2: >=6.
                                tmp = deepcopy(one_dep_list)

                                depend_len_lower = RejectUnlessGreaterThanLength(
                                    word_len - 1)
                                depend_len_upper = RejectUnlessLessThanLength(
                                    word_len + 1)

                                #Case1: check position 2 * word_len - ori_pos - 1
                                if word_len <= ori_pos:
                                    depend_char_at_pos = RejectUnlessCharInPosition(
                                        read_only_depend.get_chars(),
                                        2 * word_len - ori_pos - 1)
                                    tmp.prepend_dependency(depend_len_lower)
                                    tmp.prepend_dependency(depend_len_upper)
                                    tmp.prepend_dependency(depend_char_at_pos)
                                    tmp.prepend_dependency(
                                        deepcopy(depend_length_op))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp)

                                #Case 2: doesnt change the position
                                else:
                                    tmp.prepend_dependency(depend_len_lower)
                                    tmp.prepend_dependency(
                                        deepcopy(read_only_depend))
                                    tmp.prepend_dependency(
                                        deepcopy(depend_length_op))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp)
                                    break

                                word_len += 1

                        else:
                            raise ValueError("Error")

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        # no op
                        depend_length_no_op = RejectUnlessGreaterThanLength(
                            int(
                                math.ceil((RUNTIME_CONFIG['max_password_length']
                                           + 1) / 2)) - 1)
                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(
                            depend_length_no_op)  # >=16 do nothing
                        tmp_dependency_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                        # No OP
                        depend_length_op = RejectUnlessLessThanLength(
                            int(
                                math.ceil(
                                    (RUNTIME_CONFIG['max_password_length'] + 1)
                                    / 2)))

                        depend = deepcopy(read_only_depend)

                        ori_len = depend.get_len()
                        dest_len = int(math.floor((ori_len - 1) * 1.0 / 2) + 1)
                        depend.set_len(dest_len)

                        one_dep_list.prepend_dependency(depend)
                        one_dep_list.prepend_dependency(depend_length_op)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        # no op
                        depend_length_no_op = RejectUnlessGreaterThanLength(
                            int(
                                math.ceil((RUNTIME_CONFIG['max_password_length']
                                           + 1) / 2)) - 1)
                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(
                            depend_length_no_op)  # >=16 do nothing
                        tmp_dependency_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                        # No OP
                        depend_length_op = RejectUnlessLessThanLength(
                            int(
                                math.ceil(
                                    (RUNTIME_CONFIG['max_password_length'] + 1)
                                    / 2)))

                        depend = deepcopy(read_only_depend)

                        ori_len = depend.get_len()
                        dest_len = int(math.ceil((ori_len + 1) * 1.0 / 2) - 1)
                        depend.set_len(dest_len)

                        one_dep_list.prepend_dependency(depend)
                        one_dep_list.prepend_dependency(depend_length_op)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        # no op
                        depend_length_no_op = RejectUnlessGreaterThanLength(
                            int(
                                math.ceil((RUNTIME_CONFIG['max_password_length']
                                           + 1) / 2)) - 1)
                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(
                            depend_length_no_op)  # >=16 do nothing
                        tmp_dependency_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        # from i to j, has x nunmber of char c.
                        # need to enumerate to x
                        if from_idx >= 0:
                            min_len = (to_idx + 2 - 1) // 2  #ceil operation
                            max_len = to_idx
                        else:
                            min_len = (-from_idx + 2 - 1) // 2  #ceil operation
                            max_len = -from_idx

                        for input_len in range(min_len, max_len):

                            # count number of full duplicate, also find left bound and right bound
                            left_range = [0 for _ in range(input_len)]
                            right_range = [0 for _ in range(input_len)]
                            for i in range(from_idx, to_idx):
                                if i < 0:
                                    i = 2 * input_len + i  #convert to pos position
                                else:
                                    i = i

                                if i < input_len:
                                    i_in_original = i % input_len
                                    left_range[i_in_original] += 1
                                else:
                                    i_in_original = input_len - (
                                        i % input_len) - 1
                                    right_range[i_in_original] += 1

                            # left bound
                            left_from = 0
                            left_to = 0
                            start = False
                            for i, v in enumerate(left_range):
                                if v > 0:
                                    if start == False:
                                        left_from = i
                                        left_to = i + 1
                                        start = True
                                    else:
                                        left_to = i + 1
                                else:
                                    if start == True:
                                        break
                                    else:
                                        continue

                            # right bound
                            right_from = 0
                            right_to = 0
                            start = False
                            for i, v in enumerate(right_range):
                                if v > 0:
                                    if start == False:
                                        right_from = i
                                        right_to = i + 1
                                        start = True
                                    else:
                                        right_to = i + 1
                                else:
                                    if start == True:
                                        break
                                    else:
                                        continue

                            addition_requirements = []
                            addition_requirements.append(
                                RejectUnlessGreaterThanLength(input_len - 1))
                            addition_requirements.append(
                                RejectUnlessLessThanLength(input_len + 1))

                            if read_only_depend.dependency_type == 4:
                                FeatureExtraction.handles_left_right_shares_number_for_exact(
                                    left_from, left_to, right_from, right_to,
                                    number, chars, read_only_depend,
                                    one_dep_list, save_split_dep_lists,
                                    addition_requirements)
                            else:
                                FeatureExtraction.handles_left_right_shares_number_for_at_least(
                                    left_from, left_to, right_from, right_to,
                                    number, chars, read_only_depend,
                                    one_dep_list, save_split_dep_lists,
                                    addition_requirements)

                        # another case, input_len >= max_len, do nothing
                        op_dep_list_1 = deepcopy(one_dep_list)
                        if from_idx >= 0:
                            op_dep_list_1.prepend_dependency(
                                deepcopy(read_only_depend))
                        else:  # negative, reverse
                            if read_only_depend.dependency_type == 5:
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessFromToContainsAtLeastNumberOfChars(
                                        -read_only_depend.get_to(),
                                        -read_only_depend.get_from(),
                                        read_only_depend.get_number(),
                                        read_only_depend.get_chars()))
                            else:
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessFromToContainsExactlyNumberOfChars(
                                        -read_only_depend.get_to(),
                                        -read_only_depend.get_from(),
                                        read_only_depend.get_number(),
                                        read_only_depend.get_chars()))
                        op_dep_list_1.prepend_dependency(
                            RejectUnlessGreaterThanLength(max_len - 1))
                        op_dep_list_1.prepend_dependency(
                            RejectUnlessLessThanLength(
                                int(
                                    math.ceil(
                                        (RUNTIME_CONFIG['max_password_length'] +
                                         1) / 2))))
                        save_split_dep_lists.append_dependency_list(
                            op_dep_list_1)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_left_curly_bracket_command(subrule_dependency, rule):
        """ {   Rotates the word left: password -> asswordp

        Effects on Dependency:
            Doesn't change number, rotate positions.

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        # Reverse Doesnot change number of chars
                        depend = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        #Char in position
                        depend = deepcopy(read_only_depend)

                        #Get the position
                        ori_pos = depend.get_position()

                        #Check Negative - Just Plus 1. Also Add Length Dependency
                        #Say Check -3. Now check -2. The Length still has to be >= 3
                        if ori_pos < 0:
                            dest_pos = ori_pos + 1
                            depend.set_position(dest_pos)
                            depend0 = RejectUnlessGreaterThanLength(-ori_pos -
                                                                    1)

                            one_dep_list.prepend_dependency(depend)
                            one_dep_list.prepend_dependency(depend0)

                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)

                        else:
                            # wordlen == 4. { check 3. means check 0.
                            depend1_0 = RejectUnlessGreaterThanLength(ori_pos)
                            depend1_1 = RejectUnlessLessThanLength(ori_pos + 2)
                            depend1_2 = deepcopy(depend)
                            depend1_2.set_position(0)

                            tmp_dependency_list1 = deepcopy(one_dep_list)
                            tmp_dependency_list1.prepend_dependency(depend1_0)
                            tmp_dependency_list1.prepend_dependency(depend1_1)
                            tmp_dependency_list1.prepend_dependency(depend1_2)

                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list1)

                            #else wordlen>4 { check 3. now check pos 4.
                            tmp_dependency_list2 = deepcopy(one_dep_list)
                            depend0 = RejectUnlessGreaterThanLength(
                                ori_pos + 1)  # >3, then check -4
                            dest_pos = ori_pos + 1
                            depend.set_position(dest_pos)

                            tmp_dependency_list2.prepend_dependency(depend)
                            tmp_dependency_list2.prepend_dependency(depend0)

                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list2)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif read_only_depend.dependency_type == 4:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        if from_idx >= 0:
                            # op case
                            if from_idx + 1 < to_idx:
                                # if len == to_idx, then first_char + shift_range
                                # case1: first_char equals
                                op_dep_list_1 = deepcopy(one_dep_list)
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, 0))
                                op_dep_list_1.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx + 1, to_idx, number - 1,
                                        chars))
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessGreaterThanLength(to_idx - 1))
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessLessThanLength(to_idx + 1))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_1)

                                # case2: first_char not equals
                                op_dep_list_2 = deepcopy(one_dep_list)
                                op_dep_list_2.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, 0))
                                op_dep_list_2.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx + 1, to_idx, number, chars))
                                op_dep_list_2.prepend_dependency(
                                    RejectUnlessGreaterThanLength(to_idx - 1))
                                op_dep_list_2.prepend_dependency(
                                    RejectUnlessLessThanLength(to_idx + 1))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_2)

                            else:
                                if number == 1:  # case2 is rejected
                                    # case1: first_char equals
                                    op_dep_list_1 = deepcopy(one_dep_list)
                                    op_dep_list_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, 0))
                                    op_dep_list_1.prepend_dependency(
                                        RejectUnlessGreaterThanLength(to_idx -
                                                                      1))
                                    op_dep_list_1.prepend_dependency(
                                        RejectUnlessLessThanLength(to_idx + 1))
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list_1)
                                else:  # case 1 is rejected
                                    op_dep_list_2 = deepcopy(one_dep_list)
                                    op_dep_list_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars, 0))
                                    op_dep_list_2.prepend_dependency(
                                        RejectUnlessGreaterThanLength(to_idx -
                                                                      1))
                                    op_dep_list_2.prepend_dependency(
                                        RejectUnlessLessThanLength(to_idx + 1))
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list_2)

                            # else shift window only
                            no_op_dep_list = deepcopy(one_dep_list)
                            no_op_dep_list.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx + 1, to_idx + 1, number, chars))
                            no_op_dep_list.prepend_dependency(
                                RejectUnlessGreaterThanLength(to_idx))
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list)

                        else:
                            if to_idx == 0:
                                if from_idx + 1 < to_idx:
                                    op_dep_list_1 = deepcopy(one_dep_list)
                                    op_dep_list_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, 0))
                                    op_dep_list_1.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx + 1, to_idx, number - 1,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list_1)

                                    # case2: first_char not equals
                                    op_dep_list_2 = deepcopy(one_dep_list)
                                    op_dep_list_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars, 0))
                                    op_dep_list_2.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx + 1, to_idx, number,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list_2)
                                else:
                                    if number == 1:  # case2 is rejected
                                        op_dep_list_1 = deepcopy(one_dep_list)
                                        op_dep_list_1.prepend_dependency(
                                            RejectUnlessCharInPosition(
                                                chars, 0))
                                        save_split_dep_lists.append_dependency_list(
                                            op_dep_list_1)
                                    else:  # case 1 rejected.
                                        op_dep_list_2 = deepcopy(one_dep_list)
                                        op_dep_list_2.prepend_dependency(
                                            RejectUnlessCharInPosition(
                                                set(Dicts.classes['z']) - chars,
                                                0))
                                        save_split_dep_lists.append_dependency_list(
                                            op_dep_list_2)

                            else:
                                no_op_dep_list = deepcopy(one_dep_list)
                                no_op_dep_list.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx + 1, to_idx + 1, number,
                                        chars))
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list)

                    elif read_only_depend.dependency_type == 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        if from_idx >= 0:
                            if from_idx + 1 < to_idx:
                                # if len == to_idx, then first_char + shift_range
                                # case1: first_char equals
                                op_dep_list_1 = deepcopy(one_dep_list)
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, 0))
                                op_dep_list_1.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx + 1, to_idx, number - 1,
                                        chars))
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessGreaterThanLength(to_idx - 1))
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessLessThanLength(to_idx + 1))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_1)

                                # case2: first_char not equals
                                op_dep_list_2 = deepcopy(one_dep_list)
                                op_dep_list_2.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, 0))
                                op_dep_list_2.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx + 1, to_idx, number, chars))
                                op_dep_list_2.prepend_dependency(
                                    RejectUnlessGreaterThanLength(to_idx - 1))
                                op_dep_list_2.prepend_dependency(
                                    RejectUnlessLessThanLength(to_idx + 1))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_2)
                            else:
                                # case1: first_char equals
                                op_dep_list_1 = deepcopy(one_dep_list)
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, 0))
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessGreaterThanLength(to_idx - 1))
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessLessThanLength(to_idx + 1))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_1)

                                # case2: first_char not equals
                                # rejected

                            # else shift window only
                            no_op_dep_list = deepcopy(one_dep_list)
                            no_op_dep_list.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx + 1, to_idx + 1, number, chars))
                            no_op_dep_list.prepend_dependency(
                                RejectUnlessGreaterThanLength(to_idx))
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list)

                        else:
                            if to_idx == 0:
                                if from_idx + 1 < to_idx:
                                    op_dep_list_1 = deepcopy(one_dep_list)
                                    op_dep_list_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, 0))
                                    op_dep_list_1.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx + 1, to_idx, number - 1,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list_1)

                                    # case2: first_char not equals
                                    op_dep_list_2 = deepcopy(one_dep_list)
                                    op_dep_list_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars, 0))
                                    op_dep_list_2.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx + 1, to_idx, number,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list_2)
                                else:
                                    op_dep_list_1 = deepcopy(one_dep_list)
                                    op_dep_list_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, 0))
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list_1)

                                    # case2: first_char not equals
                                    # rejected

                            else:
                                no_op_dep_list = deepcopy(one_dep_list)
                                no_op_dep_list.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx + 1, to_idx + 1, number,
                                        chars))
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_right_curly_bracket_command(subrule_dependency, rule):
        """ }   Rotates the word right: password -> dpasswor

        Effects on Dependency:
            Doesn't change number, rotate positions.

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        # Reverse Doesnot change number of chars
                        depend = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        #Test Cases Same As Above
                        depend = deepcopy(read_only_depend)
                        ori_pos = depend.get_position()

                        if ori_pos >= 0:
                            dest_pos = ori_pos - 1
                            depend0 = RejectUnlessGreaterThanLength(
                                ori_pos)  #Implicity > Origin_pos
                            depend.set_position(dest_pos)

                            one_dep_list.prepend_dependency(depend)
                            one_dep_list.prepend_dependency(depend0)

                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)

                        else:  # Char in -3. 2 possibilities: len == 3 and len > 3
                            # ==3. } check -3. means check last one.
                            tmp_dependency_list1 = deepcopy(one_dep_list)

                            depend1_0 = RejectUnlessGreaterThanLength(-ori_pos -
                                                                      1)
                            depend1_1 = RejectUnlessLessThanLength(-ori_pos + 1)
                            depend1_2 = deepcopy(depend)
                            depend1_2.set_position(-ori_pos - 1)

                            tmp_dependency_list1.prepend_dependency(depend1_0)
                            tmp_dependency_list1.prepend_dependency(depend1_1)
                            tmp_dependency_list1.prepend_dependency(depend1_2)

                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list1)

                            #else
                            tmp_dependency_list2 = deepcopy(one_dep_list)

                            depend0 = RejectUnlessGreaterThanLength(
                                -ori_pos)  # >3, then check -4
                            dest_pos = ori_pos - 1
                            depend.set_position(dest_pos)

                            tmp_dependency_list2.prepend_dependency(depend0)
                            tmp_dependency_list2.prepend_dependency(depend)

                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list2)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    elif read_only_depend.dependency_type == 4:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        if from_idx >= 0:
                            if from_idx + 1 < to_idx:
                                if from_idx == 0:
                                    op_dep_list_1 = deepcopy(one_dep_list)
                                    op_dep_list_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, -1))
                                    op_dep_list_1.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx - 1, number - 1,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list_1)

                                    # case2: first_char not equals
                                    op_dep_list_2 = deepcopy(one_dep_list)
                                    op_dep_list_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars,
                                            -1))
                                    op_dep_list_2.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx - 1, number,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list_2)

                                else:
                                    no_op_dep_list = deepcopy(one_dep_list)
                                    no_op_dep_list.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx - 1, to_idx - 1, number,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        no_op_dep_list)
                            else:
                                if from_idx == 0:
                                    if number == 1:
                                        op_dep_list_1 = deepcopy(one_dep_list)
                                        op_dep_list_1.prepend_dependency(
                                            RejectUnlessCharInPosition(
                                                chars, -1))
                                        save_split_dep_lists.append_dependency_list(
                                            op_dep_list_1)

                                    # case2: first_char not equals
                                    else:
                                        op_dep_list_2 = deepcopy(one_dep_list)
                                        op_dep_list_2.prepend_dependency(
                                            RejectUnlessCharInPosition(
                                                set(Dicts.classes['z']) - chars,
                                                -1))
                                        save_split_dep_lists.append_dependency_list(
                                            op_dep_list_2)

                                else:
                                    no_op_dep_list = deepcopy(one_dep_list)
                                    no_op_dep_list.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx - 1, to_idx - 1, number,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        no_op_dep_list)

                        else:
                            if from_idx + 1 < to_idx:
                                # if len == to_idx, then first_char + shift_range
                                # case1: first_char equals
                                op_dep_list_1 = deepcopy(one_dep_list)
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, -1))
                                op_dep_list_1.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx - 1, number - 1,
                                        chars))
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessGreaterThanLength(-from_idx -
                                                                  1))
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessLessThanLength(-from_idx + 1))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_1)

                                # case2: first_char not equals
                                op_dep_list_2 = deepcopy(one_dep_list)
                                op_dep_list_2.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, -1))
                                op_dep_list_2.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx - 1, number, chars))
                                op_dep_list_2.prepend_dependency(
                                    RejectUnlessGreaterThanLength(-from_idx -
                                                                  1))
                                op_dep_list_2.prepend_dependency(
                                    RejectUnlessLessThanLength(-from_idx + 1))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_2)

                                # else shift window only
                                no_op_dep_list = deepcopy(one_dep_list)
                                no_op_dep_list.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx - 1, to_idx - 1, number,
                                        chars))
                                no_op_dep_list.prepend_dependency(
                                    RejectUnlessGreaterThanLength(-from_idx))
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list)
                            else:
                                if number == 1:
                                    # if len == to_idx, then first_char + shift_range
                                    # case1: first_char equals
                                    op_dep_list_1 = deepcopy(one_dep_list)
                                    op_dep_list_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, -1))
                                    op_dep_list_1.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            -from_idx - 1))
                                    op_dep_list_1.prepend_dependency(
                                        RejectUnlessLessThanLength(-from_idx +
                                                                   1))
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list_1)

                                else:
                                    op_dep_list_2 = deepcopy(one_dep_list)
                                    op_dep_list_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars,
                                            -1))
                                    op_dep_list_2.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            -from_idx - 1))
                                    op_dep_list_2.prepend_dependency(
                                        RejectUnlessLessThanLength(-from_idx +
                                                                   1))
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list_2)

                                # else shift window only
                                no_op_dep_list = deepcopy(one_dep_list)
                                no_op_dep_list.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx - 1, to_idx - 1, number,
                                        chars))
                                no_op_dep_list.prepend_dependency(
                                    RejectUnlessGreaterThanLength(-from_idx))
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list)

                    # from_to_contains
                    elif read_only_depend.dependency_type == 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        if from_idx >= 0:
                            if from_idx + 1 < to_idx:
                                if from_idx == 0:
                                    op_dep_list_1 = deepcopy(one_dep_list)
                                    op_dep_list_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, -1))
                                    op_dep_list_1.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx - 1, number - 1,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list_1)

                                    # case2: first_char not equals
                                    op_dep_list_2 = deepcopy(one_dep_list)
                                    op_dep_list_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars,
                                            -1))
                                    op_dep_list_2.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx - 1, number,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list_2)

                                else:
                                    no_op_dep_list = deepcopy(one_dep_list)
                                    no_op_dep_list.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx - 1, to_idx - 1, number,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        no_op_dep_list)
                            else:
                                if from_idx == 0:
                                    op_dep_list_1 = deepcopy(one_dep_list)
                                    op_dep_list_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, -1))
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list_1)

                                    # case2: first_char not equals
                                    # rejected

                                else:
                                    no_op_dep_list = deepcopy(one_dep_list)
                                    no_op_dep_list.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx - 1, to_idx - 1, number,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        no_op_dep_list)

                        else:
                            if from_idx + 1 < to_idx:
                                # if len == to_idx, then first_char + shift_range
                                # case1: first_char equals
                                op_dep_list_1 = deepcopy(one_dep_list)
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, -1))
                                op_dep_list_1.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx - 1, number - 1,
                                        chars))
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessGreaterThanLength(-from_idx -
                                                                  1))
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessLessThanLength(-from_idx + 1))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_1)

                                # case2: first_char not equals
                                op_dep_list_2 = deepcopy(one_dep_list)
                                op_dep_list_2.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, -1))
                                op_dep_list_2.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx - 1, number, chars))
                                op_dep_list_2.prepend_dependency(
                                    RejectUnlessGreaterThanLength(-from_idx -
                                                                  1))
                                op_dep_list_2.prepend_dependency(
                                    RejectUnlessLessThanLength(-from_idx + 1))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_2)

                                # else shift window only
                                no_op_dep_list = deepcopy(one_dep_list)
                                no_op_dep_list.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx - 1, to_idx - 1, number,
                                        chars))
                                no_op_dep_list.prepend_dependency(
                                    RejectUnlessGreaterThanLength(-from_idx))
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list)
                            else:
                                # if len == to_idx, then first_char + shift_range
                                # case1: first_char equals
                                op_dep_list_1 = deepcopy(one_dep_list)
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, -1))
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessGreaterThanLength(-from_idx -
                                                                  1))
                                op_dep_list_1.prepend_dependency(
                                    RejectUnlessLessThanLength(-from_idx + 1))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_1)

                                # case2: first_char not equals
                                # rejected

                                # else shift window only
                                no_op_dep_list = deepcopy(one_dep_list)
                                no_op_dep_list.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx - 1, to_idx - 1, number,
                                        chars))
                                no_op_dep_list.prepend_dependency(
                                    RejectUnlessGreaterThanLength(-from_idx))
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_left_square_bracket_command(subrule_dependency, rule):
        """ [   Deletes the first character

        Effects on Dependency:
            Length + 1, reason about the char deleted

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        return FeatureExtraction.extract_D_N_command(subrule_dependency,
                                                     ["D", 0])

    @staticmethod
    def extract_right_square_bracket_command(subrule_dependency, rule):
        """ ]   Deletes the last character

        Effects on Dependency:
            Length + 1, reason about the char deleted

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        return FeatureExtraction.extract_D_N_command(subrule_dependency,
                                                     ["D", -1])

    @staticmethod
    def extract_D_N_command_HC(subrule_dependency, rule):
        """ DN  Deletes char at position N

        Effects on Dependency:
            Length + 1, reason about the char deleted

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Countable")

        if N < 0 and N != -1:
            raise ValueError("Unknown Value of N: {}".format(N))

        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:
                depend = deepcopy(read_only_depend)

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        # On going.
                        # D7 -- >= 8 delete 8. Else nothing
                        if N >= 0:
                            len_threshold = N
                        else:  # -1
                            len_threshold = -N - 1

                        # >= 9. Delete something. Change only delete the char.

                        # Char in pos == char
                        depend0_0 = RejectUnlessGreaterThanLength(len_threshold)
                        depend0_1 = RejectUnlessCharInPosition(
                            depend.get_chars(), N)
                        depend0_2 = deepcopy(depend)
                        depend0_2.set_number(depend0_2.get_number() + 1)

                        tmp_dependency_list0 = deepcopy(one_dep_list)
                        tmp_dependency_list0.prepend_dependency(depend0_0)
                        tmp_dependency_list0.prepend_dependency(depend0_1)
                        tmp_dependency_list0.prepend_dependency(depend0_2)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list0)

                        # Char in pos != char doesnt change
                        depend1_0 = RejectUnlessGreaterThanLength(len_threshold)
                        depend1_1 = RejectUnlessCharInPosition(
                            set(Dicts.classes['z']) - depend.get_chars(), N)
                        depend1_2 = deepcopy(depend)

                        tmp_dependency_list1 = deepcopy(one_dep_list)
                        tmp_dependency_list1.prepend_dependency(depend1_0)
                        tmp_dependency_list1.prepend_dependency(depend1_1)
                        tmp_dependency_list1.prepend_dependency(depend1_2)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list1)

                        # <9. Do nothing. Reject same thing.
                        depend2_0 = RejectUnlessLessThanLength(len_threshold +
                                                               1)
                        depend2_1 = deepcopy(depend)
                        tmp_dependency_list2 = deepcopy(one_dep_list)
                        tmp_dependency_list2.prepend_dependency(depend2_0)
                        tmp_dependency_list2.prepend_dependency(depend2_1)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list2)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:

                        pos = depend.get_position()
                        # Both N>=0 and pos>=0
                        if N >= 0 and pos >= 0:
                            # Reject pos you can assume len >= pos + 1. Otherwise rejected.
                            if N > pos:  #Delete position greater than reject position. Doesn't matter
                                depend0_0 = RejectUnlessGreaterThanLength(pos)
                                depend0_1 = deepcopy(depend)
                                tmp_dependency_list0 = deepcopy(one_dep_list)
                                tmp_dependency_list0.prepend_dependency(
                                    depend0_1)
                                tmp_dependency_list0.prepend_dependency(
                                    depend0_0)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list0)

                            elif N == pos:
                                # If len == pos + 1 and N  == pos. Then last one deleted. Rejected
                                # So len > pos + 1
                                depend1_0 = RejectUnlessGreaterThanLength(pos +
                                                                          1)
                                depend1_1 = deepcopy(depend)
                                depend1_1.set_position(pos + 1)
                                tmp_dependency_list1 = deepcopy(one_dep_list)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_0)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_1)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list1)

                            elif N < pos:
                                # D0, =1a
                                # Satisfies both length. Then move reject position to pos-1
                                # We now know length >= pos + 1. And N < pos. Definitely have something to delete
                                depend2_0 = RejectUnlessGreaterThanLength(
                                    pos + 1
                                )  #Length requirement from pos. Also deleted one
                                depend2_1 = deepcopy(depend)
                                depend2_1.set_position(pos + 1)
                                tmp_dependency_list2 = deepcopy(one_dep_list)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_1)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_0)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list2)

                                # The rest is rejected for sure:
                                # > pos + <N. But also know N < pos. So it is rejected

                        elif N < 0 and pos < 0:

                            if abs(N) > abs(
                                    pos
                            ):  #Delete position greater than reject position. Doesn't matter
                                # D-3, Reject -2. Doesnt matter
                                depend0_0 = RejectUnlessGreaterThanLength(
                                    abs(pos) - 1)
                                depend0_1 = deepcopy(depend)
                                tmp_dependency_list0 = deepcopy(one_dep_list)
                                tmp_dependency_list0.prepend_dependency(
                                    depend0_1)
                                tmp_dependency_list0.prepend_dependency(
                                    depend0_0)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list0)

                            elif abs(N) == abs(pos):
                                # D-2, Reject -2. Reject-3
                                # If len == 2. Rejected. because str too short
                                depend1_0 = RejectUnlessGreaterThanLength(
                                    abs(pos))
                                depend1_1 = deepcopy(depend)
                                depend1_1.set_position(
                                    depend1_1.get_position() - 1)
                                tmp_dependency_list1 = deepcopy(one_dep_list)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_0)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_1)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list1)

                            # D-1, Reject -2. Reject -3
                            elif abs(N) < abs(pos):

                                # D-1, Reject -2. Reject -3
                                depend2_0 = RejectUnlessGreaterThanLength(
                                    abs(pos) - 1)  #Length requirement from pos
                                depend2_1 = deepcopy(depend)
                                #Fixed Typo
                                depend2_1.set_position(
                                    depend2_1.get_position() - 1)
                                tmp_dependency_list2 = deepcopy(one_dep_list)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_1)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_0)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list2)

                                # The rest is rejected for sure:
                                # > pos + <N. But also know N < pos. So it is rejected

                        elif N >= 0 and pos < 0:
                            # D3 )a
                            word_len = max(1, -pos)
                            while True:

                                depend_len_lower = RejectUnlessGreaterThanLength(
                                    word_len - 1)
                                depend_len_upper = RejectUnlessLessThanLength(
                                    word_len + 1)

                                if word_len <= N:  #Delete actually does nothing. Still reject the same thing
                                    depend0 = deepcopy(depend)
                                    depend0_1 = RejectUnlessGreaterThanLength(
                                        -pos - 1)  #At least length -pos
                                    tmp = deepcopy(one_dep_list)
                                    tmp.prepend_dependency(depend0)
                                    tmp.prepend_dependency(depend0_1)
                                    tmp.prepend_dependency(depend_len_lower)
                                    tmp.prepend_dependency(depend_len_upper)
                                    save_split_dep_lists.append_dependency_list(
                                        tmp)

                                elif word_len > N and word_len <= N - pos:  #D3, =-2a. #Len = 4 or 5. Check-3a

                                    depend1 = deepcopy(depend)
                                    depend1.set_position(pos - 1)
                                    depend1_1 = RejectUnlessGreaterThanLength(
                                        -pos)  #At least length -pos + 1
                                    tmp = deepcopy(one_dep_list)
                                    tmp.prepend_dependency(depend1)
                                    tmp.prepend_dependency(depend1_1)
                                    tmp.prepend_dependency(depend_len_lower)
                                    tmp.prepend_dependency(depend_len_upper)
                                    save_split_dep_lists.append_dependency_list(
                                        tmp)

                                else:  #D3, =-2a. #Len = 6. Still check -2

                                    depend2 = deepcopy(depend)
                                    depend2_1 = RejectUnlessGreaterThanLength(
                                        -pos)  #At least length -pos + 1
                                    tmp = deepcopy(one_dep_list)
                                    tmp.prepend_dependency(depend2)
                                    tmp.prepend_dependency(depend2_1)
                                    tmp.prepend_dependency(depend_len_lower)
                                    save_split_dep_lists.append_dependency_list(
                                        tmp)
                                    break

                                word_len += 1

                        else:  #N < 0 and pos >= 0:
                            # =0a D-2
                            #print("here")
                            word_len = max(1, pos + 1)
                            while True:

                                depend_len_lower = RejectUnlessGreaterThanLength(
                                    word_len - 1)
                                depend_len_upper = RejectUnlessLessThanLength(
                                    word_len + 1)

                                if word_len < -N:  #Delete actually does nothing. Still reject the same thing. len==1. Check a
                                    depend0 = deepcopy(depend)
                                    tmp = deepcopy(one_dep_list)
                                    tmp.prepend_dependency(depend0)
                                    tmp.prepend_dependency(depend_len_lower)
                                    tmp.prepend_dependency(depend_len_upper)
                                    save_split_dep_lists.append_dependency_list(
                                        tmp)

                                elif word_len >= -N and word_len <= pos - N:  # =0a D-2. len == 2. Check =1a
                                    #Whenever delete soemthing. Length should be >= pos + 2
                                    depend1 = deepcopy(depend)
                                    depend1.set_position(pos + 1)
                                    depend1_1 = RejectUnlessGreaterThanLength(
                                        pos + 1)  #At least length pos + 2
                                    tmp = deepcopy(one_dep_list)
                                    tmp.prepend_dependency(depend1)
                                    tmp.prepend_dependency(depend1_1)
                                    tmp.prepend_dependency(depend_len_lower)
                                    tmp.prepend_dependency(depend_len_upper)
                                    save_split_dep_lists.append_dependency_list(
                                        tmp)

                                else:  #=0a D-2. len >=3 doesn't matter

                                    depend2 = deepcopy(depend)
                                    depend2_1 = RejectUnlessGreaterThanLength(
                                        pos + 1)  #At least length pos + 2
                                    tmp = deepcopy(one_dep_list)
                                    tmp.prepend_dependency(depend2)
                                    tmp.prepend_dependency(depend2_1)
                                    tmp.prepend_dependency(depend_len_lower)
                                    save_split_dep_lists.append_dependency_list(
                                        tmp)
                                    break

                                word_len += 1

                        # Both N<=0 and pos<=0

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        #print(depend)
                        # D7 -- >= 8 delete 8. Else nothing
                        if N >= 0:
                            len_threshold = N
                        else:  # -1
                            len_threshold = -N - 1

                        # >= 9. Delete something
                        depend0_0 = RejectUnlessGreaterThanLength(len_threshold)
                        depend0_1 = deepcopy(depend)
                        #JTR Only?
                        #depend0_2 = RejectUnlessGreaterThanLength(1) #Delete something, then must >=2
                        depend0_1.set_len(depend.get_len() + 1)
                        tmp_dependency_list0 = deepcopy(one_dep_list)
                        tmp_dependency_list0.prepend_dependency(depend0_0)
                        tmp_dependency_list0.prepend_dependency(depend0_1)
                        #tmp_dependency_list0.prepend_dependency(depend0_2)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list0)

                        # <9. Do nothing. Reject length.
                        depend1_0 = RejectUnlessLessThanLength(len_threshold +
                                                               1)
                        depend1_1 = deepcopy(depend)
                        tmp_dependency_list1 = deepcopy(one_dep_list)
                        tmp_dependency_list1.prepend_dependency(depend1_0)
                        tmp_dependency_list1.prepend_dependency(depend1_1)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list1)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        # D7 -- >= 8 delete 8. Else nothing
                        if N >= 0:
                            len_threshold = N
                        else:  # -1
                            len_threshold = -N - 1

                        # >= 9. Delete something
                        depend0_0 = RejectUnlessGreaterThanLength(len_threshold)
                        depend0_1 = deepcopy(depend)
                        #JTR Only?
                        #depend0_2 = RejectUnlessGreaterThanLength(1) #Delete something, then must >=2
                        depend0_1.set_len(depend.get_len() + 1)
                        tmp_dependency_list0 = deepcopy(one_dep_list)
                        tmp_dependency_list0.prepend_dependency(depend0_0)
                        tmp_dependency_list0.prepend_dependency(depend0_1)
                        #tmp_dependency_list0.prepend_dependency(depend0_2)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list0)

                        # <9. Do nothing. Reject length.
                        depend1_0 = RejectUnlessLessThanLength(len_threshold +
                                                               1)
                        depend1_1 = deepcopy(depend)
                        tmp_dependency_list1 = deepcopy(one_dep_list)
                        tmp_dependency_list1.prepend_dependency(depend1_0)
                        tmp_dependency_list1.prepend_dependency(depend1_1)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list1)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        if N == -1:  # always delete the last one 1(well, not always)
                            #No op
                            depend_length_no_op = RejectUnlessLessThanLength(1)
                            no_op_dep_list_1 = deepcopy(one_dep_list)
                            no_op_dep_list_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            no_op_dep_list_1.prepend_dependency(
                                depend_length_no_op)
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list_1)

                            #Op
                            depend_length_op = RejectUnlessGreaterThanLength(0)

                            if from_idx >= 0:
                                # doesn't matter
                                dep_list_case_1 = deepcopy(one_dep_list)
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                            else:
                                # doesn't matter, just shift window
                                dep_list_case_1 = deepcopy(one_dep_list)
                                dep_list_case_1.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx - 1, to_idx - 1, number,
                                        chars))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                        # N >= 0
                        else:
                            #No op
                            depend_length_no_op_lower = RejectUnlessLessThanLength(
                                N + 1)

                            no_op_dep_list_1 = deepcopy(one_dep_list)
                            no_op_dep_list_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            no_op_dep_list_1.prepend_dependency(
                                depend_length_no_op_lower)
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list_1)

                            #Op
                            depend_length_op_lower = RejectUnlessGreaterThanLength(
                                N)

                            if from_idx >= 0:
                                # the N'th char is not X
                                # case1: N in the range of [from,to)
                                # this range is mapped to two ranges in original [from_idx,N) and [N+1, to_idx+1)
                                if to_idx > N >= from_idx:
                                    left_from = from_idx
                                    left_to = N
                                    right_from = N + 1
                                    right_to = to_idx + 1

                                    if read_only_depend.dependency_type == 4:
                                        FeatureExtraction.handles_left_right_shares_number_for_exact(
                                            left_from, left_to, right_from,
                                            right_to, number, chars,
                                            read_only_depend, one_dep_list,
                                            save_split_dep_lists,
                                            [depend_length_op_lower])
                                    else:
                                        FeatureExtraction.handles_left_right_shares_number_for_at_least(
                                            left_from, left_to, right_from,
                                            right_to, number, chars,
                                            read_only_depend, one_dep_list,
                                            save_split_dep_lists,
                                            [depend_length_op_lower])

                                # case2: N outside [From,to)
                                else:
                                    # shift window
                                    if N < from_idx:
                                        dep_list_case_1 = deepcopy(one_dep_list)
                                        dep_list_case_1.prepend_dependency(
                                            read_only_depend.make_new(
                                                from_idx + 1, to_idx + 1,
                                                number, chars))
                                        dep_list_case_1.prepend_dependency(
                                            deepcopy(depend_length_op_lower))
                                        save_split_dep_lists.append_dependency_list(
                                            dep_list_case_1)
                                    # do nothing
                                    else:
                                        dep_list_case_1 = deepcopy(one_dep_list)
                                        dep_list_case_1.prepend_dependency(
                                            deepcopy(read_only_depend))
                                        dep_list_case_1.prepend_dependency(
                                            deepcopy(depend_length_op_lower))
                                        save_split_dep_lists.append_dependency_list(
                                            dep_list_case_1)

                            else:
                                # same old thing, see if it falls in the range

                                # case1: N - to_idx + 1 < len < N - from_idx + 1
                                # new range: [len+from_idx-1, N) [N+1, len+to_idx)
                                # len also at least -from_idx + 1
                                for input_len in range(
                                        max(N - to_idx + 2, -from_idx + 1),
                                        N - from_idx + 1):
                                    left_from = input_len + from_idx - 1
                                    left_to = N
                                    right_from = N + 1
                                    right_to = input_len + to_idx

                                    addition_requirements = []
                                    addition_requirements.append(
                                        depend_length_op_lower)
                                    addition_requirements.append(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    addition_requirements.append(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))

                                    if read_only_depend.dependency_type == 4:
                                        FeatureExtraction.handles_left_right_shares_number_for_exact(
                                            left_from, left_to, right_from,
                                            right_to, number, chars,
                                            read_only_depend, one_dep_list,
                                            save_split_dep_lists,
                                            addition_requirements)
                                    else:
                                        FeatureExtraction.handles_left_right_shares_number_for_at_least(
                                            left_from, left_to, right_from,
                                            right_to, number, chars,
                                            read_only_depend, one_dep_list,
                                            save_split_dep_lists,
                                            addition_requirements)

                                # case2: len >= N - from_idx + 1
                                # doesn't matter
                                tmp_dependency_list = deepcopy(one_dep_list)
                                tmp_dependency_list.prepend_dependency(
                                    deepcopy(read_only_depend))
                                tmp_dependency_list.prepend_dependency(
                                    RejectUnlessGreaterThanLength(N - from_idx))
                                tmp_dependency_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list)

                                # case3: len <= N - to_idx + 1
                                tmp_dependency_list = deepcopy(one_dep_list)
                                tmp_dependency_list.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx - 1, to_idx - 1, number,
                                        chars))
                                tmp_dependency_list.prepend_dependency(
                                    RejectUnlessLessThanLength(N - to_idx + 2))
                                tmp_dependency_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_D_N_command_JTR(subrule_dependency, rule):
        """ special handling JTR 

        JTR's logic: if length == 1, delete first/last char will result in a rejection 
        """
        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Countable")

        ret_val = FeatureExtraction.extract_D_N_command_HC(
            subrule_dependency, rule)
        # JtR length = 1 after deletion gets rejected.
        if N == 0 or N == -1:
            ret_val.prepend_dependency_to_all_lists(
                RejectUnlessGreaterThanLength(1))

        return ret_val

    @staticmethod
    def extract_D_N_command(subrule_dependency, rule):
        """ handles D_N_command """
        if RUNTIME_CONFIG.is_jtr():
            return FeatureExtraction.extract_D_N_command_JTR(
                subrule_dependency, rule)
        else:
            return FeatureExtraction.extract_D_N_command_HC(
                subrule_dependency, rule)

    @staticmethod
    def extract_q_command(subrule_dependency, rule):
        """ q   Duplicates every character: abcd -> aabbccdd

        Effects on Dependency:
            Divide length by 2, enumerate positions

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists

        # Fix is like p_N
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        # No op
                        depend_length_no_op = RejectUnlessGreaterThanLength(
                            int(
                                math.ceil((RUNTIME_CONFIG['max_password_length']
                                           + 1) / 2)) - 1)
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        # OP
                        depend_length_op = RejectUnlessLessThanLength(
                            int(
                                math.ceil(
                                    (RUNTIME_CONFIG['max_password_length'] + 1)
                                    / 2)))

                        depend = deepcopy(read_only_depend)

                        ori_number = depend.get_number()
                        dest_number = int(math.ceil(ori_number * 1.0 / 2))
                        depend.set_number(dest_number)

                        one_dep_list.prepend_dependency(depend)
                        one_dep_list.prepend_dependency(depend_length_op)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        # no operation due to too long.
                        depend_length_no_op = RejectUnlessGreaterThanLength(
                            int(
                                math.ceil((RUNTIME_CONFIG['max_password_length']
                                           + 1) / 2)) - 1)
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        # op
                        depend_length_op = RejectUnlessLessThanLength(
                            int(
                                math.ceil(
                                    (RUNTIME_CONFIG['max_password_length'] + 1)
                                    / 2)))

                        #Original d command
                        depend = deepcopy(read_only_depend)

                        # Get check position
                        ori_pos = depend.get_position()

                        #**** Can you simpify what's below to just:
                        #new_pos = int(math.floor((ori_pos)/2))
                        #I think it is the same. min_word_length - 1 = new_pos
                        depend.set_position(int(math.floor((ori_pos) / 2)))
                        op_dep_list = deepcopy(one_dep_list)
                        op_dep_list.prepend_dependency(depend_length_op)
                        op_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(op_dep_list)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend_length_not_dup = RejectUnlessGreaterThanLength(
                            int(
                                math.ceil((RUNTIME_CONFIG['max_password_length']
                                           + 1) / 2)) - 1)
                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(
                            depend_length_not_dup)  # >=16 do nothing
                        tmp_dependency_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                        # OP
                        depend_length_op = RejectUnlessLessThanLength(
                            int(
                                math.ceil(
                                    (RUNTIME_CONFIG['max_password_length'] + 1)
                                    / 2)))

                        # original d command
                        depend = deepcopy(read_only_depend)

                        ori_len = depend.get_len()
                        dest_len = int(math.floor((ori_len - 1) * 1.0 / 2) + 1)
                        depend.set_len(dest_len)

                        one_dep_list.prepend_dependency(depend)
                        one_dep_list.prepend_dependency(depend_length_op)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend_length_no_op = RejectUnlessGreaterThanLength(
                            int(
                                math.ceil((RUNTIME_CONFIG['max_password_length']
                                           + 1) / 2)) - 1)
                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(
                            depend_length_no_op)  # >=16 do nothing
                        tmp_dependency_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                        # No OP
                        depend_length_op = RejectUnlessLessThanLength(
                            int(
                                math.ceil(
                                    (RUNTIME_CONFIG['max_password_length'] + 1)
                                    / 2)))

                        # original d command
                        depend = deepcopy(read_only_depend)

                        ori_len = depend.get_len()
                        dest_len = int(math.ceil((ori_len + 1) * 1.0 / 2) - 1)
                        depend.set_len(dest_len)

                        one_dep_list.prepend_dependency(depend)
                        one_dep_list.prepend_dependency(depend_length_op)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()
                        # from i to j, has x nunmber of char c.
                        # need to enumerate to x
                        if from_idx >= 0:
                            min_len = (
                                to_idx + 2 - 1) // 2  # at least min to survive
                        else:
                            min_len = (-from_idx + 2 -
                                       1) // 2  # at least min to survive

                        max_len = RUNTIME_CONFIG[
                            'max_password_length'] // 2  # no op performed

                        counter = [0 for _ in range(max_len + 2)]
                        # count number of full duplicate, also find left bound and right bound
                        for i in range(from_idx, to_idx):
                            if from_idx >= 0:
                                counter[i // 2] += 1
                            else:
                                counter[-(i // 2)] += 1

                        # left bound
                        left_from = 0
                        left_to = 0
                        start = False
                        for i, v in enumerate(counter):
                            if v > 0:
                                if start == False:
                                    left_from = i
                                    left_to = i + 1
                                    start = True
                                else:
                                    left_to = i + 1
                                counter[i] -= 1
                            else:
                                if start == True:
                                    break
                                else:
                                    continue

                        # right bound
                        right_from = 0
                        right_to = 0
                        start = False
                        for i, v in enumerate(counter):
                            if v > 0:
                                if start == False:
                                    right_from = i
                                    right_to = i + 1
                                    start = True
                                else:
                                    right_to = i + 1
                                counter[i] -= 1
                            else:
                                if start == True:
                                    break
                                else:
                                    continue

                        if from_idx < 0:  # reverse mapping, 1 means -1 here for from_idx < 0
                            right_from, right_to = -right_to + 1, -right_from + 1
                            left_from, left_to = -left_to + 1, -left_from + 1

                        addition_requirements = []
                        addition_requirements.append(
                            RejectUnlessLessThanLength(max_len + 1))
                        addition_requirements.append(
                            RejectUnlessGreaterThanLength(min_len - 1))

                        if read_only_depend.dependency_type == 4:
                            FeatureExtraction.handles_left_right_shares_number_for_exact(
                                left_from, left_to, right_from, right_to,
                                number, chars, read_only_depend, one_dep_list,
                                save_split_dep_lists, addition_requirements)
                        else:
                            FeatureExtraction.handles_left_right_shares_number_for_at_least(
                                left_from, left_to, right_from, right_to,
                                number, chars, read_only_depend, one_dep_list,
                                save_split_dep_lists, addition_requirements)

                        # another case, input_len >= N, do nothing
                        op_dep_list_1 = deepcopy(one_dep_list)
                        op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        op_dep_list_1.prepend_dependency(
                            RejectUnlessGreaterThanLength(max_len))
                        save_split_dep_lists.append_dependency_list(
                            op_dep_list_1)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_k_command(subrule_dependency, rule):
        """ k   Swaps first two characters: password -> apssword

        Effects on Dependency:
            no effect on length, reason about the chars swapped

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        return FeatureExtraction.extract_asterisk_N_M_command(
            subrule_dependency, ['*', 0, 1])

    @staticmethod
    def extract_K_command(subrule_dependency, rule):
        """ K   Swaps last two characters: password -> passwodr

        Effects on Dependency:
            no effect on length, reason about the chars swapped

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        return FeatureExtraction.extract_asterisk_N_M_command(
            subrule_dependency, ['*', -1, -2])

    @staticmethod
    def extract_E_command(subrule_dependency, rule):
        """ E   Lower case the whole line, then upper case the first letter and every letter after a space: "p@ssW0rd w0rld" -> "P@ssw0rd W0rld"

        Effects on Dependency:
            No effect on length, check where space is in the word

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        return FeatureExtraction.extract_e_X_command(subrule_dependency, "e ")

    @staticmethod
    def extract_P_command(subrule_dependency, rule):
        """ P   "crack" -> "cracked", etc. (lowercase only)

        Source Code
            {
                int pos;
                if ((pos = length - 1) < 2) break;
                if (in[pos] == 'd' && in[pos - 1] == 'e') break;
                if (in[pos] == 'y') in[pos] = 'i'; else
                if (strchr("bgp", in[pos]) &&
                    !strchr("bgp", in[pos - 1])) {
                    in[pos + 1] = in[pos];
                    in[pos + 2] = 0;
                }
                if (in[pos] == 'e')
                    strcat(in, "d");
                else
                    strcat(in, "ed");
            }
            length = strlen(in);
            break;

        Then This Three Rules interact with incoming rejection rules

        Decompose P:
        case0: <3, do nothing 
        case1: >=3, s[-2] in "e", s[-1] in "d", do nothing
        case2: >=3, s[-1] in "y", remove "y", append "ied"
        case3: >=3, s[-1] in "bgp", s[-2] not in "bgp", append "b/g/p" append"ed"
        case4: >=3, s[-1] in "e", append "d"
        case5: Rest: Az"ed"

        First:
        !(
        (s[-1] in "d"   and s[-2] in "e"             len >= 3) or
        (s[-1] in "y"                            and len >= 3) or
        (s[-1] in "bgp" and s[-2] not in "bgp"   and len >= 3) or
        (s[-1] in "e"   and                      and len >= 3)
        )

        Next:
        (
        !(s[-1] in "d"   and s[-2] in "e"             len >= 3) and
        !(s[-1] in "y"                            and len >= 3) and
        !(s[-1] in "bgp" and s[-2] not in "bgp"   and len >= 3) and
        !(s[-1] in "e"   and                      and len >= 3)
        )

        Then:
        (
        (s[-1] not in "d"   or s[-2] not in "e"     or len < 3) and
        (s[-1] not in "y"                           or len < 3) and
        (s[-1] not in "bgp" or s[-2] in "bgp"       or len < 3) and
        (s[-1] not in "e"   or                      or len < 3)
        )

            

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        bgp_set = set("bgp")
        d_set = set("d")
        y_set = set("y")
        e_set = set("e")

        ret_val = SubruleDependency(subrule_dependency)

        #### Cases start here
        # Case 0: <=2, do nothing
        # Call other funcs to handle
        sub_rule_dependency_1 = FeatureExtraction.extract_colon_command(
            deepcopy(subrule_dependency), ":")

        # Add case restriction
        sub_rule_dependency_1.prepend_dependency_to_all_lists(
            RejectUnlessLessThanLength(3))

        ret_val.merge(sub_rule_dependency_1)

        # Case 1: >=3, s[-2] = "e", s[-1] = "d", do nothing
        # Call other funcs to handle
        sub_rule_dependency_2 = FeatureExtraction.extract_colon_command(
            deepcopy(subrule_dependency), ":")

        # Add case restriction
        sub_rule_dependency_2.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(d_set, -1))
        sub_rule_dependency_2.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(e_set, -2))
        sub_rule_dependency_2.prepend_dependency_to_all_lists(
            RejectUnlessGreaterThanLength(2))

        ret_val.merge(sub_rule_dependency_2)

        # Case 2: >=3, ends with y, add "ied".
        # Call other funcs to handle
        sub_rule_dependency_3 = FeatureExtraction.extract_A_N_str_command(
            deepcopy(subrule_dependency), ["A", "z", "i", "e", "d"])
        sub_rule_dependency_3 = FeatureExtraction.extract_D_N_command(
            sub_rule_dependency_3, ["D", -1])

        # Add case restriction
        sub_rule_dependency_3.prepend_dependency_to_all_lists(
            RejectUnlessGreaterThanLength(2))
        sub_rule_dependency_3.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(y_set, -1))

        ret_val.merge(sub_rule_dependency_3)

        # Case 3: >=3, s[-1] in bgp, s[-2] not in bgp
        # Call other funcs to handle
        for v in bgp_set:
            tmp_rule_dependency = FeatureExtraction.extract_A_N_str_command(
                deepcopy(subrule_dependency), ["A", "z", v, "e", "d"])

            # Add case restriction
            tmp_rule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessCharInPosition(v, -1))
            tmp_rule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -2))
            tmp_rule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessGreaterThanLength(2))

            # Finally Merge
            ret_val.merge(tmp_rule_dependency)

        # Case 4: >=3, s[-1] in e, add d
        # Call other funcs to handle
        sub_rule_dependency_5 = FeatureExtraction.extract_A_N_str_command(
            deepcopy(subrule_dependency), ["A", "z", "d"])

        # Add case restriction
        sub_rule_dependency_5.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(e_set, -1))
        sub_rule_dependency_5.prepend_dependency_to_all_lists(
            RejectUnlessGreaterThanLength(2))

        # Finally Merge
        ret_val.merge(sub_rule_dependency_5)

        # Case 5, add s. Refer to above for detailed reasons
        # Call other funcs to handle
        sub_rule_dependency_6 = FeatureExtraction.extract_A_N_str_command(
            deepcopy(subrule_dependency), ["A", "z", "e", "d"])
        for idx, valid_case in enumerate(P_valid_cases):
            # copy
            tmp_rule_dependency = deepcopy(sub_rule_dependency_6)

            # add restrictions
            for dependency in valid_case.get_active():
                tmp_rule_dependency.prepend_dependency_to_all_lists(dependency)

            #Update status
            tmp_rule_dependency.clean_list()

            # It is impossible to get satisfy here.
            if tmp_rule_dependency.is_active() == 1:
                ret_val.merge(tmp_rule_dependency)

        return ret_val

    @staticmethod
    def extract_I_command(subrule_dependency, rule):
        """ I   "crack" -> "cracking", etc. (lowercase only)
        Count I command, contains possible bugs
        #Break I Into Subrules

        Source
        int pos;
            if ((pos = length - 1) < 2) break;
            if (in[pos] == 'g' && in[pos - 1] == 'n' &&
                in[pos - 2] == 'i') break;
            if (strchr("aeiou", in[pos]))
                strcpy(&in[pos], "ing");
            else {
                if (strchr("bgp", in[pos]) &&
                    !strchr("bgp", in[pos - 1])) {
                    in[pos + 1] = in[pos];
                    in[pos + 2] = 0;
                }
                strcat(in, "ing");
            }

        Decompose I:
        case0: <3 do nothing 
        case1: >=3, s[-3] in "i", s[-2] in "n", s[-1] in "g", do nothing
        case2: >=3, s[-1] in "aeiou", remove "aeiou", Az"ing"
        case3: >=3, s[-1] in "bpg", s[-2] not in "bpg", Az"b/g/p", Az"ing"
        case4: Rest: Az"ing"

        First:
        !(
        (s[-3] in "i"   and s[-2] in "n"         and s[-1] in "g"  and len >= 3) or
        (s[-1] in "aeiou"                                          and len >= 3) or
        (s[-1] in "bgp" and s[-2] not in "bgp"                     and len >= 3) or
        )

        Next:
        (
        !(s[-3] in "i"   and s[-2] in "n"         and s[-1] in "g"  and len >= 3) or
        !(s[-1] in "aeiou"                                          and len >= 3) or
        !(s[-1] in "bgp" and s[-2] not in "bgp"                     and len >= 3) or
        )

        Then:
        (
        (s[-3] not in "i"     or s[-2] not in "n"  or s[-1] in "g"  or len < 3) or
        (s[-1] not in "aeiou"                                       or len < 3) or
        (s[-1] not in "bgp"   or s[-2] in "bgp"                     or len < 3) or
        )
        """

        aeiou_set = set("aeiou")
        bgp_set = set("bgp")
        i_set = set("i")
        n_set = set("n")
        g_set = set("g")

        ret_val = SubruleDependency(subrule_dependency)

        # Basic usage
        # tmp_sub_rule_dependency = FeatureExtraction.extract_A_N_str_command(rule_dependency, ["A","z","s"])
        # ret_val.merge(tmp_sub_rule_dependency)

        #### Cases start here
        # Case 0: <=2, do nothing
        # Call other funcs to handle
        sub_rule_dependency_1 = FeatureExtraction.extract_colon_command(
            deepcopy(subrule_dependency), ":")

        # Add case restriction
        sub_rule_dependency_1.prepend_dependency_to_all_lists(
            RejectUnlessLessThanLength(3))

        ret_val.merge(sub_rule_dependency_1)

        # Case 1: >=3, s[-3] = "i", s[-2] = "n", s[-1] = "g", do nothing
        # Call other funcs to handle
        sub_rule_dependency_2 = FeatureExtraction.extract_colon_command(
            deepcopy(subrule_dependency), ":")

        # Add case restriction
        sub_rule_dependency_2.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(i_set, -3))
        sub_rule_dependency_2.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(n_set, -2))
        sub_rule_dependency_2.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(g_set, -1))
        sub_rule_dependency_2.prepend_dependency_to_all_lists(
            RejectUnlessGreaterThanLength(2))

        ret_val.merge(sub_rule_dependency_2)

        # Case 2: >=3, ends with aeiou, delete, add "ing".
        # Call other funcs to handle
        sub_rule_dependency_3 = FeatureExtraction.extract_A_N_str_command(
            deepcopy(subrule_dependency), ["A", "z", "i", "n", "g"])
        sub_rule_dependency_3 = FeatureExtraction.extract_D_N_command(
            sub_rule_dependency_3, ["D", -1])

        # Add case restriction
        sub_rule_dependency_3.prepend_dependency_to_all_lists(
            RejectUnlessGreaterThanLength(2))
        sub_rule_dependency_3.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(aeiou_set, -1))

        ret_val.merge(sub_rule_dependency_3)

        # Case 3: >=3, s[-1] in bgp, s[-2] not in bgp
        # Note: It conflicts with s[-3]=i s[-2]=n s[-1]=g
        # Call other funcs to handle
        for v in "bp":
            tmp_rule_dependency = FeatureExtraction.extract_A_N_str_command(
                deepcopy(subrule_dependency), ["A", "z", v, "i", "n", "g"])

            # Add case restriction
            tmp_rule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessCharInPosition(v, -1))
            tmp_rule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set, -2))
            tmp_rule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessGreaterThanLength(2))

            # Finally Merge
            ret_val.merge(tmp_rule_dependency)

        # s[-2] = printable - bgp - n s[-1] = "g"
        tmp_rule_dependency = FeatureExtraction.extract_A_N_str_command(
            deepcopy(subrule_dependency), ["A", "z", "g", "i", "n", "g"])

        # Add case restriction
        tmp_rule_dependency.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(g_set, -1))
        tmp_rule_dependency.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(Dicts.classes['z'] - bgp_set - n_set,
                                       -2))
        tmp_rule_dependency.prepend_dependency_to_all_lists(
            RejectUnlessGreaterThanLength(2))

        # Finally Merge
        ret_val.merge(tmp_rule_dependency)

        # s[-3] != "i" s[-2] = n s[-1] = "g"
        tmp_rule_dependency = FeatureExtraction.extract_A_N_str_command(
            deepcopy(subrule_dependency), ["A", "z", "g", "i", "n", "g"])

        # Add case restriction
        tmp_rule_dependency.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(g_set, -1))
        tmp_rule_dependency.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(n_set, -2))
        tmp_rule_dependency.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(Dicts.classes['z'] - i_set, -3))
        tmp_rule_dependency.prepend_dependency_to_all_lists(
            RejectUnlessGreaterThanLength(2))

        # Finally Merge
        ret_val.merge(tmp_rule_dependency)

        # Case 4, add ing. Refer to above for detailed reasons
        # Call other funcs to handle
        sub_rule_dependency_4 = FeatureExtraction.extract_A_N_str_command(
            deepcopy(subrule_dependency), ["A", "z", "i", "n", "g"])
        for idx, valid_case in enumerate(I_valid_cases):
            # copy
            tmp_rule_dependency = deepcopy(sub_rule_dependency_4)

            # add restrictions
            for dependency in valid_case.get_active():
                tmp_rule_dependency.prepend_dependency_to_all_lists(dependency)

            #Update status
            tmp_rule_dependency.clean_list()

            # It is impossible to get satisfy here.
            if tmp_rule_dependency.is_active():
                ret_val.merge(tmp_rule_dependency)

        return ret_val

    @staticmethod
    def extract_V_command(subrule_dependency, rule):
        """ V Command. Lowercase vowels, uppercase consonants: "Crack96" -> "CRaCK96"

        Effects on Dependency:
            No effect on length, switch cases

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        # Remove uppercase_vowels as it can only contain lower vowel
                        # Remove lowercase_cons as it can only contain upper con
                        # Make lower_upper_vowels as we invert the rule
                        # Make lower_upper_cons as we invert the rule
                        # Add non-letter chars

                        depend = deepcopy(read_only_depend)
                        ori_chars = depend.get_chars()

                        lower_vow = set(c for c in ori_chars
                                        if c in Dicts.classes['l'] and
                                        c in Dicts.classes['v'])
                        lower_upper_vow = lower_vow | set(
                            c.upper() for c in lower_vow)

                        upper_cons = set(c for c in ori_chars
                                         if c in Dicts.classes['u'] and
                                         c in Dicts.classes['c'])
                        lower_upper_cons = upper_cons | set(
                            c.lower() for c in upper_cons)

                        others = set(
                            x for x in ori_chars
                            if not x in Dicts.classes['a'])  #Not a letter

                        dest_chars = others | lower_upper_cons | lower_upper_vow

                        depend.set_chars(dest_chars)
                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        # Remove uppercase_vowels as it can only contain lower vowel
                        # Remove lowercase_cons as it can only contain upper con
                        # Make lower_upper_vowels as we invert the rule
                        # Make lower_upper_cons as we invert the rule
                        # Add non-letter chars

                        depend = deepcopy(read_only_depend)
                        ori_chars = depend.get_chars()

                        lower_vow = set(c for c in ori_chars
                                        if c in Dicts.classes['l'] and
                                        c in Dicts.classes['v'])
                        lower_upper_vow = lower_vow | set(
                            c.upper() for c in lower_vow)

                        upper_cons = set(c for c in ori_chars
                                         if c in Dicts.classes['u'] and
                                         c in Dicts.classes['c'])
                        lower_upper_cons = upper_cons | set(
                            c.lower() for c in upper_cons)

                        others = set(
                            x for x in ori_chars
                            if not x in Dicts.classes['a'])  #Not a letter

                        dest_chars = others | lower_upper_cons | lower_upper_vow

                        depend.set_chars(dest_chars)
                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        #Shift case command does not affect length dependency
                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        #Shift case command does not affect length dependency
                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        # Remove uppercase_vowels as it can only contain lower vowel
                        # Remove lowercase_cons as it can only contain upper con
                        # Make lower_upper_vowels as we invert the rule
                        # Make lower_upper_cons as we invert the rule
                        # Add non-letter chars

                        depend = deepcopy(read_only_depend)
                        ori_chars = depend.get_chars()

                        lower_vow = set(c for c in ori_chars
                                        if c in Dicts.classes['l'] and
                                        c in Dicts.classes['v'])
                        lower_upper_vow = lower_vow | set(
                            c.upper() for c in lower_vow)

                        upper_cons = set(c for c in ori_chars
                                         if c in Dicts.classes['u'] and
                                         c in Dicts.classes['c'])
                        lower_upper_cons = upper_cons | set(
                            c.lower() for c in upper_cons)

                        others = set(
                            x for x in ori_chars
                            if not x in Dicts.classes['a'])  #Not a letter

                        dest_chars = others | lower_upper_cons | lower_upper_vow

                        depend.set_chars(dest_chars)
                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_S_command(subrule_dependency, rule):
        """ S Command. shift case: "Crack96" -> "cRACK(^"

        Effects on Dependency:
            no effect on length, switch cases

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        #Same as above. Change the case of chars in char set.
                        depend = deepcopy(read_only_depend)
                        ori_chars = depend.get_chars()
                        dest_chars = set(
                            Dicts.shift[x] for x in depend.get_chars())
                        depend.set_chars(dest_chars)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        #Same as above. Change the case of chars in char set.
                        depend = deepcopy(read_only_depend)
                        ori_chars = depend.get_chars()
                        dest_chars = set(
                            Dicts.shift[x] for x in depend.get_chars())
                        depend.set_chars(dest_chars)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        #Shift case command does not affect length dependency
                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        #Shift case command does not affect length dependency
                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        #Same as above. Change the case of chars in char set.
                        depend = deepcopy(read_only_depend)
                        ori_chars = depend.get_chars()
                        dest_chars = set(
                            Dicts.shift[x] for x in depend.get_chars())
                        depend.set_chars(dest_chars)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_p_command(subrule_dependency, rule):
        """ p   pluralize: "crack" -> "cracks", etc. (lowercase only)

        Count p command, contains possible bugs
        #Assume Append s. Could be es or something.
        #Break p Into Subrules
        Source:
        if (length < 2) break;
            {
                int pos = length - 1;
                if (strchr("sxz", in[pos]) ||
                    (pos > 1 && in[pos] == 'h' &&
                    (in[pos - 1] == 'c' || in[pos - 1] == 's')))
                    strcat(in, "es");
                else
                if (in[pos] == 'f' && in[pos - 1] != 'f')
                    strcpy(&in[pos], "ves");
                else
                if (pos > 1 &&
                    in[pos] == 'e' && in[pos - 1] == 'f')
                    strcpy(&in[pos - 1], "ves");
                else
                if (pos > 1 && in[pos] == 'y') {
                    if (strchr("aeiou", in[pos - 1]))
                        strcat(in, "s");
                    else
                        strcpy(&in[pos], "ies");
                } else
                    strcat(in, "s");
            }
            length = strlen(in);
            break;

        The idea here is to decompose p and let other rules handle it, so it is critical that other rules are correct

        Decompose p:
        case0: <2
        case1: =(-1)(sxz) Az"es"
        case2: >2 =(-1)h =(-2)(cs) Az"es"
        case3: =(-1)f =(-2)(a,b,c...e,g,...) D(-1) Az"ves"
        case4: >2 =(-1)e =(-2)f D(-1) D(-1) Az"ves" -- several ways to represent this.
        case5: >2 =(-1)y =(-2)(aeiou) Az"s"
        case6: >2 =(-1)y =(-2)(b,c,d,f,g...) D(-1) Az"ies"
        case7: Az"s"

        First:
        !(
        (s[-1] in "sxz" and                          len >= 2) or
        (s[-1] in "h"   and s[-2] in "cs"        and len >= 3) or
        (s[-1] in "f"   and s[-2] not in "f"     and len >= 2) or
        (s[-1] in "e"   and s[-2] in "f"         and len >= 3) or
        (s[-1] in "y    and s[-2] not in "aeiou  and len >= 3)
        )

        Next:
        (
        !(s[-1] in "sxz" and                          len >= 2) and
        !(s[-1] in "h"   and s[-2] in "cs"        and len >= 3) and
        !(s[-1] in "f"   and s[-2] not in "f"     and len >= 2) and
        !(s[-1] in "e"   and s[-2] in "f"         and len >= 3) and
        !(s[-1] in "y    and s[-2] not in "aeiou  and len >= 3)
        )

        Then:
        (
        (s[-1] not in "sxz" or                             len < 2) and
        (s[-1] not in "h"   or s[-2] not in "cs"        or len < 3) and
        (s[-1] not in "f"   or s[-2] in "f"             or len < 2) and
        (s[-1] not in "e"   or s[-2] not in "f"         or len < 3) and
        (s[-1] not in "y    or s[-2] in "aeiou          or len < 3)
        )

        Finally make what's within a bracket disjoint.

        Expand it to "or" major you will get 9 * 9 * 2 = 182 types of combinations
        """
        aeiou_set = set("aeiou")
        sxz_set = set("sxz")
        cs_set = set("cs")
        h_set = set("h")
        y_set = set("y")
        f_set = set("f")
        e_set = set("e")

        ret_val = SubruleDependency(subrule_dependency)

        # Basic usage
        # tmp_sub_rule_dependency = FeatureExtraction.extract_A_N_str_command(rule_dependency, ["A","z","s"])
        # ret_val.merge(tmp_sub_rule_dependency)

        #### Cases start here
        # Case 1: <=1, do nothing
        # Call other funcs to handle
        sub_rule_dependency_1 = FeatureExtraction.extract_colon_command(
            deepcopy(subrule_dependency), ":")

        # Add case restriction
        sub_rule_dependency_1.prepend_dependency_to_all_lists(
            RejectUnlessLessThanLength(2))

        ret_val.merge(sub_rule_dependency_1)

        # Case 2: >=2, ends with (sxz), add "es"
        # Call other funcs to handle
        sub_rule_dependency_2 = FeatureExtraction.extract_A_N_str_command(
            deepcopy(subrule_dependency), ["A", "z", "e", "s"])

        # Add case restriction
        sub_rule_dependency_2.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(sxz_set, -1))
        sub_rule_dependency_2.prepend_dependency_to_all_lists(
            RejectUnlessGreaterThanLength(1))

        ret_val.merge(sub_rule_dependency_2)

        # Case 3: >=3, ends with (ch/sh), add "es". Should merge with case 2 for efficiency.
        # Call other funcs to handle
        sub_rule_dependency_3 = FeatureExtraction.extract_A_N_str_command(
            deepcopy(subrule_dependency), ["A", "z", "e", "s"])

        # Add case restriction
        sub_rule_dependency_3.prepend_dependency_to_all_lists(
            RejectUnlessGreaterThanLength(2))
        sub_rule_dependency_3.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(cs_set, -2))
        sub_rule_dependency_3.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(h_set, -1))

        ret_val.merge(sub_rule_dependency_3)

        # Case 4: >=2, last one f, second to last not f, add ves
        # Call other funcs to handle
        sub_rule_dependency_4 = FeatureExtraction.extract_A_N_str_command(
            deepcopy(subrule_dependency), ["A", "z", "v", "e", "s"])
        sub_rule_dependency_4 = FeatureExtraction.extract_D_N_command(
            sub_rule_dependency_4, ["D", -1])

        # Add case restriction
        sub_rule_dependency_4.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(f_set, -1))
        sub_rule_dependency_4.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(Dicts.classes['z'] - f_set, -2))

        # Finally Merge
        ret_val.merge(sub_rule_dependency_4)

        # Case 5: >=3, ends with fe, add ves
        # Call other funcs to handle
        sub_rule_dependency_5 = FeatureExtraction.extract_A_N_str_command(
            deepcopy(subrule_dependency), ["A", "z", "v", "e", "s"])
        sub_rule_dependency_5 = FeatureExtraction.extract_D_N_command(
            sub_rule_dependency_5, ["D", -1])
        sub_rule_dependency_5 = FeatureExtraction.extract_D_N_command(
            sub_rule_dependency_5, ["D", -1])

        # Add case restriction
        sub_rule_dependency_5.prepend_dependency_to_all_lists(
            RejectUnlessGreaterThanLength(1))
        sub_rule_dependency_5.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(f_set, -2))
        sub_rule_dependency_5.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(e_set, -1))

        # Finally Merge
        ret_val.merge(sub_rule_dependency_5)

        # Case 6: >=3, ends with (not-vowel)y, ies.
        # Call other funcs to handle
        sub_rule_dependency_6 = FeatureExtraction.extract_A_N_str_command(
            deepcopy(subrule_dependency), ["A", "z", "i", "e", "s"])
        sub_rule_dependency_6 = FeatureExtraction.extract_D_N_command(
            sub_rule_dependency_6, ["D", -1])

        # Add case restriction
        sub_rule_dependency_6.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(Dicts.classes['z'] - aeiou_set, -2))
        sub_rule_dependency_6.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(y_set, -1))
        sub_rule_dependency_6.prepend_dependency_to_all_lists(
            RejectUnlessGreaterThanLength(2))

        # Finally Merge
        ret_val.merge(sub_rule_dependency_6)

        # Case 7, add s. Refer to above for detailed reasons
        # Call other funcs to handle
        sub_rule_dependency_7 = FeatureExtraction.extract_A_N_str_command(
            deepcopy(subrule_dependency), ["A", "z", "s"])
        for idx, valid_case in enumerate(p_valid_cases):
            # copy
            tmp_rule_dependency = deepcopy(sub_rule_dependency_7)

            # add restrictions
            for dependency in valid_case.get_active():
                tmp_rule_dependency.prepend_dependency_to_all_lists(dependency)

            #Update status
            tmp_rule_dependency.clean_list()

            # It is impossible to get satisfy here.
            if tmp_rule_dependency.is_active():
                ret_val.merge(tmp_rule_dependency)

        return ret_val

    @staticmethod
    def extract_R_command(subrule_dependency, rule):
        """ R   shift each character right, by keyboard: "Crack96" -> "Vtsvl07"

        Effects on Dependency:
            no effect on length, switch cases.

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        depend = deepcopy(read_only_depend)

                        ori_chars = depend.get_chars()

                        # First, suppose s->d. Get d. Here it's all c in ori_char with Dicts.right[c] not None. Not none means can be shifted back
                        chars_on_right_side = set(
                            c for c in ori_chars
                            if c in Dicts.right and Dicts.right[c] != None)

                        # Shift everything back
                        dest_chars = set()
                        for x in chars_on_right_side:  #Reverse. Dicts.right[key] could be "abc"
                            dest_chars |= Dicts.right[x]

                        depend.set_chars(dest_chars)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        # same as above
                        depend = deepcopy(read_only_depend)

                        ori_chars = depend.get_chars()

                        # First, suppose s->d. Get d. Here it's all c in ori_char with Dicts.right[c] not None. Not none means can be shifted back
                        chars_on_right_side = set(
                            c for c in ori_chars
                            if c in Dicts.right and Dicts.right[c] != None)

                        # Shift everything back
                        dest_chars = set()
                        for x in chars_on_right_side:  #Reverse. Dicts.right[key] could be "abc"
                            dest_chars |= Dicts.right[x]

                        depend.set_chars(dest_chars)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Less_Than_Length
                    elif 6 <= read_only_depend.dependency_type <= 7:
                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        # same as above
                        depend = deepcopy(read_only_depend)

                        ori_chars = depend.get_chars()

                        # First, suppose s->d. Get d. Here it's all c in ori_char with Dicts.right[c] not None. Not none means can be shifted back
                        chars_on_right_side = set(
                            c for c in ori_chars
                            if c in Dicts.right and Dicts.right[c] != None)

                        # Shift everything back
                        dest_chars = set()
                        for x in chars_on_right_side:  #Reverse. Dicts.right[key] could be "abc"
                            dest_chars |= Dicts.right[x]

                        depend.set_chars(dest_chars)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_L_command(subrule_dependency, rule):
        """ L   shift each character left, by keyboard: "Crack96" -> "Xeaxj85"

        Effects on Dependency:
            no effect on length, switch cases.

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        depend = deepcopy(read_only_depend)

                        ori_chars = depend.get_chars()

                        # First, suppose s->d. Get d. Here it's all c in ori_char with Dicts.left[c] not None. Not none means can be shifted back
                        chars_on_right_side = set(
                            c for c in ori_chars
                            if c in Dicts.left and Dicts.left[c] != None)

                        # Shift everything back
                        dest_chars = set()
                        for x in chars_on_right_side:  #Reverse. Dicts.left[key] could be "abc"
                            dest_chars |= Dicts.left[x]

                        depend.set_chars(dest_chars)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        # same as above
                        depend = deepcopy(read_only_depend)

                        ori_chars = depend.get_chars()

                        # First, suppose s->d. Get d. Here it's all c in ori_char with Dicts.left[c] not None. Not none means can be shifted back
                        chars_on_right_side = set(
                            c for c in ori_chars
                            if c in Dicts.left and Dicts.left[c] != None)

                        # Shift everything back
                        dest_chars = set()
                        for x in chars_on_right_side:  #Reverse. Dicts.left[key] could be "abc"
                            dest_chars |= Dicts.left[x]

                        depend.set_chars(dest_chars)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Less_Than_Length
                    elif 6 <= read_only_depend.dependency_type <= 7:
                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        # same as above
                        depend = deepcopy(read_only_depend)

                        ori_chars = depend.get_chars()

                        # First, suppose s->d. Get d. Here it's all c in ori_char with Dicts.left[c] not None. Not none means can be shifted back
                        chars_on_right_side = set(
                            c for c in ori_chars
                            if c in Dicts.left and Dicts.left[c] != None)

                        # Shift everything back
                        dest_chars = set()
                        for x in chars_on_right_side:  #Reverse. Dicts.left[key] could be "abc"
                            dest_chars |= Dicts.left[x]

                        depend.set_chars(dest_chars)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_dollar_X_command(subrule_dependency, rule):
        """ $X  Append character X to the word 

        Effects on Dependency:
            length - 1, reason about X

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        return FeatureExtraction.extract_i_N_X_command(subrule_dependency,
                                                       ["i", "z", rule[1]])

    @staticmethod
    def extract_caret_X_command(subrule_dependency, rule):
        """ ^X prefix the word with character X

        Effects on Dependency:
            length - 1, reason about X

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        return FeatureExtraction.extract_i_N_X_command(subrule_dependency,
                                                       ["i", 0, rule[1]])

    @staticmethod
    def extract_i_N_X_command(subrule_dependency, rule):
        """ iNX insert character X in position N and shift the rest right 

        Effects on Dependency:
            length - 1, reason about X

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        if RUNTIME_CONFIG.is_hc():
            return FeatureExtraction.extract_one_insertion_HC(
                subrule_dependency, rule)
        else:
            return FeatureExtraction.extract_one_insertion_JTR(
                subrule_dependency, rule)

    @staticmethod
    def extract_A_N_str_command(subrule_dependency, rule):
        """ AN"STR" insert string STR into the word at position N

        Effects on Dependency:
            length - 1, reason about X

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        return FeatureExtraction.extract_one_insertion_JTR(
            subrule_dependency, rule)

    @staticmethod
    def _set_interact_with_number_of_chars(
            str_set, depend):  #Atom Operation. A set and A depend
        """ when append a set (e.g. [0-9]) of chars, how will it affect a dependency """
        if depend.dependency_type == 1 or depend.dependency_type == 2:
            if depend.is_satisfied():  #Satisfied. Do nothing
                return str_set, depend, None, None

            # Say Append (1,2,3) Reject (2,3,4)
            # Append should be broken into Az(1) amd Az(2/3)
            # Then Az(2/3) always satisfies (2,3,4). Set coef. remove both if necessary.
            # Then Az(1) doesn't satisfies (2,3,4). Remove Az"1", set coef

            # Can u use recurrent?
            depend_set = depend.get_chars()
            ori_set = str_set

            if ori_set.issubset(
                    depend_set):  # append 1, check (1,2,3) --> satisfied.
                depend.set_number(depend.get_number() - 1)
                return ori_set, depend, None, None

            elif ori_set & depend_set == set(
            ):  # No intersection # Add str, go on
                return ori_set, depend, None, None

            else:  #Break string, partially go on.
                satisfied_depend = deepcopy(depend)
                satisfied_depend.set_number(depend.get_number() - 1)
                not_satisfied_depend = deepcopy(depend)

                satisfied_set = ori_set & depend_set
                not_satisfied_set = ori_set - depend_set

                return satisfied_set, satisfied_depend, not_satisfied_set, not_satisfied_depend

    @staticmethod
    def _sets_interact_with_number_of_chars(str_sets, depend):
        """ a set of chars with a depend that requires some chars

        E.g.
        str_sets = [set(1-9), set(1-9)]. depend is just one dependency
        Return val is multiple str_sets with depends --
        """

        q = Queue()
        q.enqueue(([], [
            deepcopy(depend)
        ]))  # first element is list of sets associated with this depend

        for str_set in deepcopy(str_sets[::-1]):

            new_queue = Queue()

            while q.empty() != True:

                current_tuple = q.dequeue()

                if current_tuple[1] == []:
                    current_tuple[0].insert(0, str_set)
                    new_queue.enqueue(current_tuple)

                else:
                    set1, dep1, set2, dep2 = FeatureExtraction._set_interact_with_number_of_chars(
                        str_set, current_tuple[1][0])

                    tmp_list = deepcopy(current_tuple[0])
                    tmp_list.insert(0, set1)
                    tmp_tuple = (tmp_list, [dep1])

                    new_queue.enqueue(tmp_tuple)

                    if dep2 != None:

                        tmp_list = deepcopy(current_tuple[0])
                        tmp_list.insert(0, set2)
                        tmp_tuple = (tmp_list, [dep2])

                        new_queue.enqueue(tmp_tuple)

            q = new_queue

        return q

    @staticmethod
    def extract_one_insertion_JTR(subrule_dependency, rule):  # in ANStr Form
        """ handles JtR insertion

        JtR's logic: insert anyway 
        """
        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise ValueError("Illegal N")

        for i in range(2, len(rule)):
            rule[i] = set(rule[i])

        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                dependency_list.update_current_sets(rule[2:])
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            # why list here? Avoid updating current sets
            current_dep_lists = [DependencyList(extend_from=dependency_list)]
            current_dep_lists[0].update_current_sets(
                rule[2:])  # associate all chars

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = []

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        # Say Append (1,2,3) Reject if not contains (2,3,4)
                        # Append should be broken into Az(1) amd Az(2/3)
                        # Then Az(2/3) always satisfies (2,3,4). Set coef. remove both if necessary.
                        # Then Az(1) doesn't satisfies (2,3,4). Remove Az"1", set coef
                        depend = deepcopy(read_only_depend)
                        # Can u use recurrent?
                        # call function to handle it
                        result_queue = FeatureExtraction._sets_interact_with_number_of_chars(
                            one_dep_list.current_sets, depend
                        )  #Should return a list. loop_list *= len(list)

                        for val in result_queue.items:  #Each val a tuple. First part: set(). Second Part: Rule

                            #You return sets and dependencys
                            tmp = deepcopy(one_dep_list)
                            tmp.current_sets = val[0]
                            if val[1] != []:
                                tmp.prepend_dependency(val[1][0])

                            save_split_dep_lists.append(tmp)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:

                        # Case5: Negative - Pos -- not possible
                        # Case6: Negative - Negative -- not possible
                        depend = deepcopy(read_only_depend)

                        pos = depend.get_position()
                        current_sets = one_dep_list.current_sets

                        # Case1: Az - Rejection Rule Check Nagative Position
                        if N == float("inf") and pos < 0:

                            # If the append size is less than check position
                            # Then you move the check position
                            if len(current_sets) < abs(pos):
                                new_pos = pos + len(
                                    current_sets
                                )  #Az"12", check -3. -> check -1.
                                depend.set_position(new_pos)

                            # If the append the size is greater or equal than
                            # Check the position in append string
                            else:  #Check pos in str. Az"1234" check -3 -> check -3 in Az"1234"
                                depend_set = depend.get_chars()
                                ori_set = one_dep_list.current_sets[pos]

                                if ori_set.issubset(depend_set):  #Satisfied.
                                    depend.set_to_satisfied()

                                elif ori_set & depend_set == set(
                                ):  # No intersection # Rejected
                                    one_dep_list.current_sets[pos] = set()

                                    depend.set_to_rejected()

                                else:  #Break string, partially go on.
                                    one_dep_list.current_sets[
                                        pos] = ori_set & depend_set
                                    depend.set_to_satisfied()

                            one_dep_list.prepend_dependency(depend)
                            save_split_dep_lists.append(one_dep_list)

                        # Case2: Z - Positive Position
                        elif N == float("inf") and pos >= 0:
                            # Two situations: len > pos, len <= pos

                            #Az"123". Reject pos 2. If word_len >= 3, then doesnt matter.
                            depend_satisfied = RejectUnlessGreaterThanLength(
                                pos)

                            tmp_dependency_list1 = deepcopy(one_dep_list)
                            tmp_dependency_list1.prepend_dependency(depend)
                            tmp_dependency_list1.prepend_dependency(
                                depend_satisfied)
                            save_split_dep_lists.append(tmp_dependency_list1)

                            #Az"1". Reject pos 2. If word_len < 3 && word_len + len("123") >= 3
                            # For this example only length = 2 satisfies.
                            # word_len < pos + 1. Need to enumerate
                            # The word should also be at least pos + 1 - len()
                            # Since len(rule[2:]) could be super long, need max.
                            for word_length in range(
                                    max(1, pos + 1 - len(rule[2:])), pos + 1):
                                #print("here")
                                tmp_depend = deepcopy(depend)

                                new_pos = pos - word_length

                                loop_dependency_list = deepcopy(one_dep_list)

                                depend_set = depend.get_chars()

                                ori_set = loop_dependency_list.current_sets[
                                    new_pos]

                                if ori_set.issubset(depend_set):  #Satisfied.
                                    tmp_depend.set_to_satisfied()

                                elif ori_set & depend_set == set(
                                ):  # No intersection # Rejected
                                    loop_dependency_list.current_sets[
                                        new_pos] = set()
                                    tmp_depend.set_to_rejected()

                                else:  #Break string, partially go on.
                                    loop_dependency_list.current_sets[
                                        new_pos] = ori_set & depend_set
                                    tmp_depend.set_to_satisfied()

                                depend1 = RejectUnlessGreaterThanLength(
                                    word_length - 1)
                                depend2 = RejectUnlessLessThanLength(
                                    word_length + 1)

                                loop_dependency_list.prepend_dependency(depend1)
                                loop_dependency_list.prepend_dependency(depend2)
                                loop_dependency_list.prepend_dependency(
                                    tmp_depend)

                                save_split_dep_lists.append(
                                    loop_dependency_list)

                            #Az"123". Reject pos 2. If len == 1. Then, If len == 2. Then
                            #This is where you have to enumerate
                            #new_pos =
                            #raise Exception("Part Not Implemented")
                        #save_split_dep_lists.add(depend)

                        # Case3: Posi - Posi
                        elif N >= 0 and pos >= 0:
                            #Same As Above.
                            #For =31, A5"12".
                            if N > pos:
                                #If word_len >= 4, doesnt matter
                                depend_satisfied = RejectUnlessGreaterThanLength(
                                    pos)

                                tmp_dependency_list1 = deepcopy(one_dep_list)
                                tmp_dependency_list1.prepend_dependency(depend)
                                tmp_dependency_list1.prepend_dependency(
                                    depend_satisfied)
                                save_split_dep_lists.append(
                                    tmp_dependency_list1)

                                #If word_len < 4 and word_len + 2 >= 4, check position in string based on word_len
                                for word_length in range(
                                        max(1, pos + 1 - len(rule[2:])),
                                        pos + 1):
                                    #print("here")
                                    tmp_depend = deepcopy(depend)

                                    new_pos = pos - word_length

                                    loop_dependency_list = deepcopy(
                                        one_dep_list)

                                    depend_set = depend.get_chars()

                                    ori_set = loop_dependency_list.current_sets[
                                        new_pos]

                                    if ori_set.issubset(
                                            depend_set):  #Satisfied.
                                        tmp_depend.set_to_satisfied()

                                    elif ori_set & depend_set == set(
                                    ):  # No intersection # Rejected
                                        loop_dependency_list.current_sets[
                                            new_pos] = set()

                                        tmp_depend.set_to_rejected()

                                    else:  #Break string, partially go on.
                                        loop_dependency_list.current_sets[
                                            new_pos] = ori_set & depend_set
                                        tmp_depend.set_to_satisfied()

                                    depend1 = RejectUnlessGreaterThanLength(
                                        word_length - 1)
                                    depend2 = RejectUnlessLessThanLength(
                                        word_length + 1)

                                    loop_dependency_list.prepend_dependency(
                                        depend1)
                                    loop_dependency_list.prepend_dependency(
                                        depend2)
                                    loop_dependency_list.prepend_dependency(
                                        tmp_depend)

                                    save_split_dep_lists.append(
                                        loop_dependency_list)

                            #If A3"12" =9a. 3 + len("12") <= 9.
                            #Also see A2"123" =5a
                            #If word_len >= 10, check insert after or in the middle
                            #If word_len < 10 and word_len >= 8, check char in string/ Or char in some position

                            elif N + len(one_dep_list.current_sets) <= pos:
                                #The reason to use pos+2 is just to break
                                for word_length in range(
                                        max(1, pos + 1 - len(rule[2:])),
                                        pos + 2):
                                    #print("here")

                                    # N >= word_length, append. (in HC it is not realistic)
                                    # Check pos-word_length in inserted string.
                                    # Nope, it's correct because it's bounded above
                                    # *** Notice here that the inserted string is too short then an error occurs
                                    if N + 1 > word_length:  # Insert after (i.e. append), check char in str

                                        depend_len_upper = RejectUnlessLessThanLength(
                                            word_length + 1)
                                        depend_len_lower = RejectUnlessGreaterThanLength(
                                            word_length - 1)

                                        tmp_depend = deepcopy(depend)

                                        loop_dependency_list = deepcopy(
                                            one_dep_list)

                                        new_pos = pos - word_length

                                        depend_set = depend.get_chars()

                                        ori_set = loop_dependency_list.current_sets[
                                            new_pos]

                                        if ori_set.issubset(
                                                depend_set):  #Satisfied.
                                            tmp_depend.set_to_satisfied()

                                        elif ori_set & depend_set == set(
                                        ):  # No intersection # Rejected
                                            loop_dependency_list.current_sets[
                                                new_pos] = set()

                                            tmp_depend.set_to_rejected()

                                        else:  #Break string, partially go on.
                                            loop_dependency_list.current_sets[
                                                new_pos] = ori_set & depend_set
                                            tmp_depend.set_to_satisfied()

                                        if word_length < pos + 1:
                                            loop_dependency_list.prepend_dependency(
                                                tmp_depend)
                                            loop_dependency_list.prepend_dependency(
                                                depend_len_lower)
                                            loop_dependency_list.prepend_dependency(
                                                depend_len_upper)
                                            save_split_dep_lists.append(
                                                loop_dependency_list)
                                        else:
                                            loop_dependency_list.prepend_dependency(
                                                tmp_depend)
                                            loop_dependency_list.prepend_dependency(
                                                depend_len_lower)
                                            save_split_dep_lists.append(
                                                loop_dependency_list)
                                            break

                                    #Insert in the middle,
                                    #This is also wrong.
                                    #Insert in the middle, there are two possible situations.
                                    #If string not very long, Check char in new_pos in original string.
                                    #Otherwise check new_pos in string
                                    # Nope, it's correct because it's bounded above

                                    else:  #Insert in the middle, Check char in new_pos in original string.
                                        depend_len_upper = RejectUnlessLessThanLength(
                                            word_length + 1)
                                        depend_len_lower = RejectUnlessGreaterThanLength(
                                            word_length - 1)

                                        tmp_depend = deepcopy(depend)

                                        loop_dependency_list = deepcopy(
                                            one_dep_list)

                                        new_pos = pos - len(rule[2:])

                                        tmp_depend.set_position(new_pos)

                                        if word_length < pos + 1:
                                            loop_dependency_list.prepend_dependency(
                                                tmp_depend)
                                            loop_dependency_list.prepend_dependency(
                                                depend_len_lower)
                                            loop_dependency_list.prepend_dependency(
                                                depend_len_upper)
                                            save_split_dep_lists.append(
                                                loop_dependency_list)
                                        else:
                                            loop_dependency_list.prepend_dependency(
                                                tmp_depend)
                                            loop_dependency_list.prepend_dependency(
                                                depend_len_lower)
                                            save_split_dep_lists.append(
                                                loop_dependency_list)
                                            break

                            #  pos - len(one_dep_list.current_sets) < N <= pos
                            #  A5"123", =61 -- N = 5, pos = 6, len = 3.
                            #  A1"12345" =31
                            #  Length >= 7
                            else:
                                #Same thing, need to discuss length
                                for word_length in range(
                                        max(1, pos + 1 - len(rule[2:])),
                                        pos + 2):
                                    #Insert string "123" in the end. Check position in "123"
                                    if word_length < N + 1:

                                        depend_len_upper = RejectUnlessLessThanLength(
                                            word_length + 1)
                                        depend_len_lower = RejectUnlessGreaterThanLength(
                                            word_length - 1)

                                        tmp_depend = deepcopy(depend)

                                        loop_dependency_list = deepcopy(
                                            one_dep_list)

                                        new_pos = pos - word_length

                                        depend_set = depend.get_chars()

                                        ori_set = loop_dependency_list.current_sets[
                                            new_pos]

                                        if ori_set.issubset(
                                                depend_set):  #Satisfied.
                                            tmp_depend.set_to_satisfied()

                                        elif ori_set & depend_set == set(
                                        ):  # No intersection # Rejected
                                            loop_dependency_list.current_sets[
                                                new_pos] = set()
                                            tmp_depend.set_to_rejected()

                                        else:  #Break string, partially go on.
                                            loop_dependency_list.current_sets[
                                                new_pos] = ori_set & depend_set
                                            tmp_depend.set_to_satisfied()

                                        if word_length < pos + 1:
                                            loop_dependency_list.prepend_dependency(
                                                tmp_depend)
                                            loop_dependency_list.prepend_dependency(
                                                depend_len_lower)
                                            loop_dependency_list.prepend_dependency(
                                                depend_len_upper)
                                            save_split_dep_lists.append(
                                                loop_dependency_list)
                                        else:
                                            loop_dependency_list.prepend_dependency(
                                                tmp_depend)
                                            loop_dependency_list.prepend_dependency(
                                                depend_len_lower)
                                            save_split_dep_lists.append(
                                                loop_dependency_list)
                                            break

                                    #Insert str "123" in the middle. Two cases: len(str) + start_position >= pos or len(str) + start_position < pos
                                    else:
                                        #Check pos in ori_string if N + len("123") < check_position.
                                        if N + len(rule[2:]) < pos + 1:
                                            depend_len_upper = RejectUnlessLessThanLength(
                                                word_length + 1)
                                            depend_len_lower = RejectUnlessGreaterThanLength(
                                                word_length - 1)

                                            tmp_depend = deepcopy(depend)

                                            loop_dependency_list = deepcopy(
                                                one_dep_list)

                                            new_pos = pos - len(rule[2:])

                                            tmp_depend.set_position(new_pos)
                                            if word_length < pos + 1:
                                                loop_dependency_list.prepend_dependency(
                                                    tmp_depend)
                                                loop_dependency_list.prepend_dependency(
                                                    depend_len_lower)
                                                loop_dependency_list.prepend_dependency(
                                                    depend_len_upper)
                                                save_split_dep_lists.append(
                                                    loop_dependency_list)
                                            else:
                                                loop_dependency_list.prepend_dependency(
                                                    tmp_depend)
                                                loop_dependency_list.prepend_dependency(
                                                    depend_len_lower)
                                                save_split_dep_lists.append(
                                                    loop_dependency_list)
                                                break

                                        #Otherwise append string is longer than check position. Check pos in appended string "123"
                                        else:
                                            depend_len_upper = RejectUnlessLessThanLength(
                                                word_length + 1)
                                            depend_len_lower = RejectUnlessGreaterThanLength(
                                                word_length - 1)

                                            tmp_depend = deepcopy(depend)

                                            loop_dependency_list = deepcopy(
                                                one_dep_list)

                                            new_pos = pos - N

                                            depend_set = depend.get_chars()

                                            ori_set = loop_dependency_list.current_sets[
                                                new_pos]

                                            if ori_set.issubset(
                                                    depend_set):  #Satisfied.
                                                tmp_depend.set_to_satisfied()

                                            elif ori_set & depend_set == set(
                                            ):  # No intersection # Rejected
                                                loop_dependency_list.current_sets[
                                                    new_pos] = set()
                                                tmp_depend.set_to_rejected()

                                            else:  #Break string, partially go on.
                                                loop_dependency_list.current_sets[
                                                    new_pos] = ori_set & depend_set
                                                tmp_depend.set_to_satisfied()

                                            if word_length < pos + 1:
                                                loop_dependency_list.prepend_dependency(
                                                    tmp_depend)
                                                loop_dependency_list.prepend_dependency(
                                                    depend_len_lower)
                                                loop_dependency_list.prepend_dependency(
                                                    depend_len_upper)
                                                save_split_dep_lists.append(
                                                    loop_dependency_list)
                                            else:
                                                loop_dependency_list.prepend_dependency(
                                                    tmp_depend)
                                                loop_dependency_list.prepend_dependency(
                                                    depend_len_lower)
                                                save_split_dep_lists.append(
                                                    loop_dependency_list)
                                                break

                        # Case4: Posi - Nega
                        elif N >= 0 and pos < 0:
                            # First you need to add a rejection rule with word_len >= abs(pos)

                            # Check char at position -1, at least length >= 1
                            # Bugs: At lesat int(abs(pos)) - len(rule[2:])
                            word_len = int(abs(pos)) - len(rule[2:])

                            current_sets = one_dep_list.current_sets

                            while word_len < float("inf"):  #While true
                                tmp = deepcopy(one_dep_list)
                                tmp_depend = deepcopy(depend)

                                #print("Current Word Length: {}".format(word_len))
                                depend_len_upper = RejectUnlessLessThanLength(
                                    word_len + 1)
                                depend_len_lower = RejectUnlessGreaterThanLength(
                                    word_len - 1)

                                # word_len <= N：
                                # If len(str) < -pos:
                                # -pos - len(str)

                                # Else reject -pos in str
                                if word_len <= N:

                                    tmp.prepend_dependency(depend_len_upper)
                                    tmp.prepend_dependency(depend_len_lower)

                                    if len(
                                            current_sets
                                    ) < -pos:  # "abc", A3"1"/A4"1" check -3
                                        #print("1 if")
                                        #print(len(current_sets))
                                        new_pos = pos + len(rule[2:])
                                        tmp_depend.set_position(new_pos)

                                    else:  # "abc", A3"1234", =-3a check -3. Just check the -3 at str
                                        #print("1 Else")
                                        ori_set = current_sets[pos]
                                        depend_set = tmp_depend.get_chars()

                                        if ori_set.issubset(
                                                depend_set):  #Satisfied.
                                            tmp_depend.set_to_satisfied()

                                        elif ori_set & depend_set == set(
                                        ):  # No intersection # Rejected

                                            tmp.current_sets[pos] = set()

                                            tmp_depend.set_to_rejected()

                                        else:  #Break string, partially go on.
                                            tmp.current_sets[
                                                pos] = ori_set & depend_set
                                            tmp_depend.set_to_satisfied()

                                    tmp.prepend_dependency(tmp_depend)
                                    save_split_dep_lists.append(tmp)

                                elif word_len > N and word_len < N + abs(pos):

                                    tmp.prepend_dependency(depend_len_upper)
                                    tmp.prepend_dependency(depend_len_lower)

                                    if word_len + len(current_sets) - N < int(
                                            -pos):  #"abcd" A3"1" =-3a.  Check b

                                        # Update new_pos
                                        new_pos = pos + len(rule[2:])
                                        tmp_depend.set_position(new_pos)

                                    else:  # "abcd" A3"12" abc12d =-3a. Check -2 of str

                                        new_pos = pos + word_len - N

                                        ori_set = current_sets[
                                            new_pos]  #Check -2 of str
                                        depend_set = tmp_depend.get_chars()

                                        if ori_set.issubset(
                                                depend_set):  #Satisfied.
                                            tmp_depend.set_to_satisfied()

                                        elif ori_set & depend_set == set(
                                        ):  # No intersection # Rejected

                                            tmp.current_sets[new_pos] = set()

                                            tmp_depend.set_to_rejected()

                                        else:  #Break string, partially go on.
                                            tmp.current_sets[
                                                new_pos] = ori_set & depend_set
                                            tmp_depend.set_to_satisfied()

                                    tmp.prepend_dependency(tmp_depend)
                                    save_split_dep_lists.append(tmp)
                                    #print("2 Add tmp_dependency_list:{}".format(tmp))

                                else:
                                    # word_len >= N + pos # abcdefg A3"1231321a" -3. 7 > 3+3. Still Check -3
                                    tmp.prepend_dependency(depend_len_lower)
                                    tmp.prepend_dependency(tmp_depend)
                                    save_split_dep_lists.append(tmp)
                                    break

                                word_len += 1

                    # Reject_Unless_Less_Than_Length
                    elif 6 <= read_only_depend.dependency_type <= 7:

                        new_depend = deepcopy(read_only_depend)  #get a new one.

                        dest_len = new_depend.get_len()
                        #print(len(rule[2:]))
                        dest_len -= len(rule[2:])

                        new_depend.set_len(dest_len)

                        one_dep_list.prepend_dependency(new_depend)

                        save_split_dep_lists.append(one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        # Not Yet Implemented
                        raise NotCountableException("Not Countable")

                    else:
                        # Not Yet Implemented
                        raise NotCountableException("Not Countable")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        # Important
        # No Dependency List. Satisfied. Set Global coef. Only in this situation
        if len(ret_val.list_of_dep_list) == 0:
            ret_val.update_coef(rule[2:])

        return ret_val

    @staticmethod
    def extract_one_insertion_HC(subrule_dependency,
                                 rule):  # rule in the form iNX
        """ handles HC insertion, no insertion if the string is too short """
        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise ValueError("Illegal N")

        X = rule[2]

        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        if N == float("inf"):
                            #No op
                            depend_length_no_op = RejectUnlessGreaterThanLength(
                                RUNTIME_CONFIG['max_password_length'] - 1)
                            no_op_dep_list_1 = deepcopy(one_dep_list)
                            no_op_dep_list_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            no_op_dep_list_1.prepend_dependency(
                                depend_length_no_op)
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list_1)

                            #op
                            depend_length_op_upper = RejectUnlessLessThanLength(
                                RUNTIME_CONFIG['max_password_length'])

                            depend = deepcopy(read_only_depend)

                            ori_set = depend.get_chars()

                            if X in ori_set:
                                #satisfied
                                depend.set_number(depend.get_number() - 1)
                                #else do nothing

                            op_dep_list_1 = deepcopy(one_dep_list)
                            op_dep_list_1.prepend_dependency(
                                depend_length_op_upper)
                            op_dep_list_1.prepend_dependency(depend)
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list_1)

                        elif N >= 0:
                            #No op
                            depend_length_no_op = RejectUnlessGreaterThanLength(
                                RUNTIME_CONFIG['max_password_length'] - 1)
                            no_op_dep_list_1 = deepcopy(one_dep_list)
                            no_op_dep_list_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            no_op_dep_list_1.prepend_dependency(
                                depend_length_no_op)
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list_1)

                            depend_length_no_op = RejectUnlessLessThanLength(N)
                            no_op_dep_list_2 = deepcopy(one_dep_list)
                            no_op_dep_list_2.prepend_dependency(
                                deepcopy(read_only_depend))
                            no_op_dep_list_2.prepend_dependency(
                                depend_length_no_op)
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list_2)

                            #op
                            depend_length_op_lower = RejectUnlessGreaterThanLength(
                                N - 1)
                            depend_length_op_upper = RejectUnlessLessThanLength(
                                RUNTIME_CONFIG['max_password_length'])

                            depend = deepcopy(read_only_depend)

                            ori_set = depend.get_chars()

                            if X in ori_set:
                                #satisfied
                                depend.set_number(depend.get_number() - 1)
                                #else do nothing

                            op_dep_list_1 = deepcopy(one_dep_list)
                            op_dep_list_1.prepend_dependency(
                                depend_length_op_lower)
                            op_dep_list_1.prepend_dependency(
                                depend_length_op_upper)
                            op_dep_list_1.prepend_dependency(depend)
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list_1)

                        else:
                            raise ValueError("Unknown N Value")

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        if N == float("inf"):
                            #No op
                            depend_length_no_op = RejectUnlessGreaterThanLength(
                                RUNTIME_CONFIG['max_password_length'] - 1)
                            no_op_dep_list_1 = deepcopy(one_dep_list)
                            no_op_dep_list_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            no_op_dep_list_1.prepend_dependency(
                                depend_length_no_op)
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list_1)

                            #op
                            depend_length_op_upper = RejectUnlessLessThanLength(
                                RUNTIME_CONFIG['max_password_length'])

                            depend = deepcopy(read_only_depend)
                            ori_pos = depend.get_position()

                            if ori_pos >= 0:
                                # case1:
                                # Check pos 2 (actually 3), length >= 3 and append soemthing, doesn't matter
                                depend_does_not_matter = RejectUnlessGreaterThanLength(
                                    ori_pos)

                                op_dep_list_1 = deepcopy(one_dep_list)
                                op_dep_list_1.prepend_dependency(depend)
                                op_dep_list_1.prepend_dependency(
                                    depend_does_not_matter)
                                op_dep_list_1.prepend_dependency(
                                    deepcopy(depend_length_op_upper))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_1)

                                # *** Notice that here it is 0. Because valid length of HC is 0 not 1.
                                #for word_length in range(max(0,pos), pos+1):

                                #case2:
                                # Op, Length = ori_pos. append and length = ori_pos + 1
                                tmp_depend = deepcopy(depend)

                                depend_set = depend.get_chars()

                                if X in depend_set:  #Satisfied.
                                    tmp_depend.set_to_satisfied()

                                else:  # No intersection # Rejected
                                    tmp_depend.set_to_rejected()

                                depend1 = RejectUnlessGreaterThanLength(
                                    ori_pos - 1)
                                depend2 = RejectUnlessLessThanLength(ori_pos +
                                                                     1)

                                op_dep_list_2 = deepcopy(one_dep_list)
                                op_dep_list_2.prepend_dependency(tmp_depend)
                                op_dep_list_2.prepend_dependency(depend1)
                                op_dep_list_2.prepend_dependency(depend2)
                                op_dep_list_2.prepend_dependency(
                                    deepcopy(depend_length_op_upper))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_2)

                            #ori_pos < 0
                            else:
                                # check at least -2.
                                # now check ori_pos + 1
                                if abs(ori_pos) > 1:
                                    depend.set_position(ori_pos + 1)

                                else:
                                    # Check -1, append.
                                    if X in depend.get_chars():
                                        depend.set_to_satisfied()
                                    else:
                                        depend.set_to_rejected()

                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(
                                    depend_length_op_upper)
                                op_dep_list.prepend_dependency(depend)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                        elif N >= 0:
                            ori_pos = read_only_depend.get_position()

                            #No op
                            depend_length_no_op = RejectUnlessGreaterThanLength(
                                RUNTIME_CONFIG['max_password_length'] - 1)
                            no_op_dep_list_1 = deepcopy(one_dep_list)
                            no_op_dep_list_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            no_op_dep_list_1.prepend_dependency(
                                depend_length_no_op)
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list_1)

                            depend_length_no_op = RejectUnlessLessThanLength(N)
                            no_op_dep_list_2 = deepcopy(one_dep_list)
                            no_op_dep_list_2.prepend_dependency(
                                deepcopy(read_only_depend))
                            no_op_dep_list_2.prepend_dependency(
                                depend_length_no_op)
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list_2)

                            #op
                            depend_length_op_lower = RejectUnlessGreaterThanLength(
                                N - 1)
                            depend_length_op_upper = RejectUnlessLessThanLength(
                                RUNTIME_CONFIG['max_password_length'])

                            #ori_pos >= 0 and N >=0
                            if ori_pos >= 0:

                                # Idealy Insert After Check Position
                                if N > ori_pos:
                                    #If word_len >= 4, doesnt matter -- Insert After Check Position
                                    #In HC we know that length >= N
                                    depend_satisfied = RejectUnlessGreaterThanLength(
                                        ori_pos)

                                    tmp_dependency_list1 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(read_only_depend))
                                    tmp_dependency_list1.prepend_dependency(
                                        depend_satisfied)
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_length_op_lower))
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_length_op_upper))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list1)

                                #Theoratically append position + length could not reach the check position.
                                #If word_len >= 10, check insert after or in the middle
                                #If word_len < 10 and word_len >= 8, check char in string/ Or char in some position
                                elif N + 1 < ori_pos + 1:
                                    #The reason to use pos+2 is just to break
                                    #Then there are just 1 case:
                                    #length >= pos > N (so it's definitely in the middle, check the pos-1)

                                    #length + 1 >= pos + 1
                                    depend_len_lower = RejectUnlessGreaterThanLength(
                                        ori_pos - 1)

                                    tmp_depend = deepcopy(read_only_depend)
                                    tmp_depend.set_position(
                                        tmp_depend.get_position() - 1)

                                    tmp_dependency_list1 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list1.prepend_dependency(
                                        tmp_depend)
                                    tmp_dependency_list1.prepend_dependency(
                                        depend_len_lower)
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_length_op_lower))
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_length_op_upper))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list1)

                                #  pos - len(one_dep_list.current_sets) < N <= pos
                                #  Theoratically insert position is less than check point but it greater than check point - length(rule[2:]).
                                #  In hc min length is N.
                                else:

                                    word_length = max(N, ori_pos)
                                    while word_length < float("inf"):

                                        if word_length < N + 1:  # append

                                            depend_len_upper = RejectUnlessLessThanLength(
                                                word_length + 1)
                                            depend_len_lower = RejectUnlessGreaterThanLength(
                                                word_length - 1)

                                            tmp_depend = deepcopy(
                                                read_only_depend)

                                            loop_dependency_list = deepcopy(
                                                one_dep_list)

                                            #Check char in inserted str, however, len(inserted) = 1
                                            depend_set = tmp_depend.get_chars()

                                            if X in depend_set:  #Satisfied.
                                                tmp_depend.set_to_satisfied()

                                            else:  # No intersection # Rejected
                                                tmp_depend.set_to_rejected()

                                            if word_length < ori_pos + 1:
                                                loop_dependency_list.prepend_dependency(
                                                    tmp_depend)
                                                loop_dependency_list.prepend_dependency(
                                                    depend_len_lower)
                                                loop_dependency_list.prepend_dependency(
                                                    depend_len_upper)
                                                loop_dependency_list.prepend_dependency(
                                                    deepcopy(
                                                        depend_length_op_lower))
                                                loop_dependency_list.prepend_dependency(
                                                    deepcopy(
                                                        depend_length_op_upper))
                                                save_split_dep_lists.append_dependency_list(
                                                    loop_dependency_list)
                                            else:
                                                loop_dependency_list.prepend_dependency(
                                                    tmp_depend)
                                                loop_dependency_list.prepend_dependency(
                                                    depend_len_lower)
                                                loop_dependency_list.prepend_dependency(
                                                    deepcopy(
                                                        depend_length_op_lower))
                                                loop_dependency_list.prepend_dependency(
                                                    deepcopy(
                                                        depend_length_op_upper))
                                                save_split_dep_lists.append_dependency_list(
                                                    loop_dependency_list)
                                                break

                                        else:
                                            # N + len(inserted) < pos + 1
                                            # part1 - inserted - part2
                                            #                      | pos
                                            # Check position in ori string
                                            if N + 1 < ori_pos + 1:
                                                depend_len_upper = RejectUnlessLessThanLength(
                                                    word_length + 1)
                                                depend_len_lower = RejectUnlessGreaterThanLength(
                                                    word_length - 1)

                                                tmp_depend = deepcopy(
                                                    read_only_depend)

                                                loop_dependency_list = deepcopy(
                                                    one_dep_list)

                                                new_pos = ori_pos - 1

                                                tmp_depend.set_position(new_pos)
                                                if word_length < ori_pos + 1:
                                                    loop_dependency_list.prepend_dependency(
                                                        tmp_depend)
                                                    loop_dependency_list.prepend_dependency(
                                                        depend_len_lower)
                                                    loop_dependency_list.prepend_dependency(
                                                        depend_len_upper)
                                                    loop_dependency_list.prepend_dependency(
                                                        deepcopy(
                                                            depend_length_op_lower
                                                        ))
                                                    loop_dependency_list.prepend_dependency(
                                                        deepcopy(
                                                            depend_length_op_upper
                                                        ))
                                                    save_split_dep_lists.append_dependency_list(
                                                        loop_dependency_list)
                                                else:
                                                    loop_dependency_list.prepend_dependency(
                                                        tmp_depend)
                                                    loop_dependency_list.prepend_dependency(
                                                        depend_len_lower)
                                                    loop_dependency_list.prepend_dependency(
                                                        deepcopy(
                                                            depend_length_op_lower
                                                        ))
                                                    loop_dependency_list.prepend_dependency(
                                                        deepcopy(
                                                            depend_length_op_upper
                                                        ))
                                                    save_split_dep_lists.append_dependency_list(
                                                        loop_dependency_list)
                                                    break

                                            # N + len(inserted) < pos + 1
                                            # part1 - inserted - part2
                                            #               | pos
                                            #Otherwise append string is longer than check position. Check pos in appended string "123"
                                            else:
                                                depend_len_upper = RejectUnlessLessThanLength(
                                                    word_length + 1)
                                                depend_len_lower = RejectUnlessGreaterThanLength(
                                                    word_length - 1)

                                                tmp_depend = deepcopy(
                                                    read_only_depend)

                                                loop_dependency_list = deepcopy(
                                                    one_dep_list)

                                                depend_set = read_only_depend.get_chars(
                                                )

                                                if X in depend_set:  #Satisfied.
                                                    tmp_depend.set_to_satisfied(
                                                    )

                                                else:  # No intersection # Rejected
                                                    tmp_depend.set_to_rejected()

                                                if word_length < ori_pos + 1:
                                                    loop_dependency_list.prepend_dependency(
                                                        tmp_depend)
                                                    loop_dependency_list.prepend_dependency(
                                                        depend_len_lower)
                                                    loop_dependency_list.prepend_dependency(
                                                        depend_len_upper)
                                                    loop_dependency_list.prepend_dependency(
                                                        deepcopy(
                                                            depend_length_op_lower
                                                        ))
                                                    loop_dependency_list.prepend_dependency(
                                                        deepcopy(
                                                            depend_length_op_upper
                                                        ))
                                                    save_split_dep_lists.append_dependency_list(
                                                        loop_dependency_list)
                                                else:
                                                    loop_dependency_list.prepend_dependency(
                                                        tmp_depend)
                                                    loop_dependency_list.prepend_dependency(
                                                        depend_len_lower)
                                                    loop_dependency_list.prepend_dependency(
                                                        deepcopy(
                                                            depend_length_op_lower
                                                        ))
                                                    loop_dependency_list.prepend_dependency(
                                                        deepcopy(
                                                            depend_length_op_upper
                                                        ))
                                                    save_split_dep_lists.append_dependency_list(
                                                        loop_dependency_list)
                                                    break

                                        word_length += 1

                            # ori_pos < 0 and N >=0
                            else:
                                word_len = max(-ori_pos - 1,
                                               N)  #why -1? because added 1
                                while word_len < float("inf"):
                                    tmp = deepcopy(one_dep_list)
                                    tmp_depend = deepcopy(read_only_depend)
                                    #print("Current Word Length: {}".format(word_len))
                                    depend_len_upper = RejectUnlessLessThanLength(
                                        word_len + 1)
                                    depend_len_lower = RejectUnlessGreaterThanLength(
                                        word_len - 1)

                                    # part1 - inserted.
                                    if word_len <= N:  #append

                                        if 1 < -ori_pos:  #Check at least -2 (-2,-3,...)

                                            new_pos = ori_pos + len(rule[2:])
                                            tmp_depend.set_position(new_pos)

                                        else:

                                            ori_set = X
                                            depend_set = tmp_depend.get_chars()

                                            if ori_set in depend_set:  #Satisfied.
                                                tmp_depend.set_to_satisfied()

                                            else:  # No intersection # Rejected
                                                tmp_depend.set_to_rejected()

                                        tmp.prepend_dependency(tmp_depend)
                                        tmp.prepend_dependency(depend_len_upper)
                                        tmp.prepend_dependency(depend_len_lower)
                                        tmp.prepend_dependency(
                                            deepcopy(depend_length_op_lower))
                                        tmp.prepend_dependency(
                                            deepcopy(depend_length_op_upper))
                                        save_split_dep_lists.append_dependency_list(
                                            tmp)

                                    # part1 - inserted - part2. part2 < abs(pos)
                                    #Insert in the middle, cut original word into 2. But the length of inserted string will affect result
                                    elif word_len > N and word_len < N + abs(
                                            ori_pos):

                                        # Inserted string is not long enough, then check some new place in the original striing.
                                        if word_len + 1 - N < abs(
                                                ori_pos
                                        ):  #"abcd" A3"1" =-3a.  Check b (-2)

                                            # Update new_pos
                                            new_pos = ori_pos + 1
                                            tmp_depend.set_position(new_pos)

                                        # Inserted string is very long enough, then check somewhere in the inserted string
                                        else:  # "abcd" A3"12" abc12d =-3a. Check -2 of str
                                            # in this example just one case
                                            ori_set = X
                                            depend_set = tmp_depend.get_chars()

                                            if ori_set in depend_set:  #Satisfied.
                                                tmp_depend.set_to_satisfied()

                                            else:  # No intersection # Rejected
                                                tmp_depend.set_to_rejected()

                                        tmp.prepend_dependency(tmp_depend)
                                        tmp.prepend_dependency(depend_len_upper)
                                        tmp.prepend_dependency(depend_len_lower)
                                        tmp.prepend_dependency(
                                            deepcopy(depend_length_op_lower))
                                        tmp.prepend_dependency(
                                            deepcopy(depend_length_op_upper))
                                        save_split_dep_lists.append_dependency_list(
                                            tmp)

                                    # part1 - inserted - part2. part2 > abs(pos)
                                    else:
                                        # word_len >= N + pos # abcdefg A3"1231321a" -3. 7 > 3+3. Still Check -3
                                        tmp.prepend_dependency(depend_len_lower)
                                        tmp.prepend_dependency(tmp_depend)
                                        tmp.prepend_dependency(
                                            deepcopy(depend_length_op_lower))
                                        tmp.prepend_dependency(
                                            deepcopy(depend_length_op_upper))
                                        save_split_dep_lists.append_dependency_list(
                                            tmp)
                                        #print("3 Add tmp_dependency_list:{}".format(tmp))
                                        break

                                    word_len += 1

                    # Reject chars
                    elif read_only_depend.dependency_type == 6 or read_only_depend.dependency_type == 7:
                        if N == float("inf"):
                            #No op
                            depend_length_no_op = RejectUnlessGreaterThanLength(
                                RUNTIME_CONFIG['max_password_length'] - 1)
                            no_op_dep_list_1 = deepcopy(one_dep_list)
                            no_op_dep_list_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            no_op_dep_list_1.prepend_dependency(
                                depend_length_no_op)
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list_1)

                            #Op
                            depend_length_op = RejectUnlessLessThanLength(
                                RUNTIME_CONFIG['max_password_length'])

                            new_depend = deepcopy(
                                read_only_depend)  #get a new one.
                            new_depend.set_len(new_depend.get_len() - 1)

                            one_dep_list.prepend_dependency(new_depend)
                            one_dep_list.prepend_dependency(depend_length_op)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)

                        elif N >= 0:
                            #No op
                            depend_length_no_op_upper = RejectUnlessGreaterThanLength(
                                RUNTIME_CONFIG['max_password_length'] - 1)
                            depend_length_no_op_lower = RejectUnlessLessThanLength(
                                N)

                            no_op_dep_list_1 = deepcopy(one_dep_list)
                            no_op_dep_list_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            no_op_dep_list_1.prepend_dependency(
                                depend_length_no_op_upper)
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list_1)

                            no_op_dep_list_2 = deepcopy(one_dep_list)
                            no_op_dep_list_2.prepend_dependency(
                                deepcopy(read_only_depend))
                            no_op_dep_list_2.prepend_dependency(
                                depend_length_no_op_lower)
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list_2)

                            #Op
                            depend_length_op_upper = RejectUnlessLessThanLength(
                                RUNTIME_CONFIG['max_password_length'])
                            depend_length_op_lower = RejectUnlessGreaterThanLength(
                                N - 1)

                            new_depend = deepcopy(
                                read_only_depend)  #get a new one.
                            new_depend.set_len(new_depend.get_len() - 1)

                            one_dep_list.prepend_dependency(new_depend)
                            one_dep_list.prepend_dependency(
                                depend_length_op_upper)
                            one_dep_list.prepend_dependency(
                                depend_length_op_lower)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)

                        else:
                            raise Exception("Unknown N")

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        # Not Yet Implemented
                        raise NotCountableException("Not Countable")

                    else:
                        raise ValueError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_T_N_command(subrule_dependency, rule):
        """ TN  Toggles case of char at position N

        Effects on Dependency:
            No effect on length, shift chars

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """

        def get_dest_set(ori_set):
            return set(Dicts.toggle.setdefault(x, x) for x in ori_set)

        ret_val = SubruleDependency(subrule_dependency)

        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Countable")

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        # Here notice that if just toggle a set of chars, the result could still
                        # be in the set. Toggle /?a still equals /?a
                        # Two situations: Char at place N equals and char at place N not equals
                        # No memorization involved.
                        if N >= 0:
                            # T1 /a
                            # T4 /D
                            # T3 /=
                            # T3 /?a
                            # T3 /?d
                            # a fa1 cAbc16 t2fad1
                            # bvD e4hd134 vjeD34D bnmD14 vcx153ghessD
                            # =d vxw+24 vqa+ble24 fdslnwjrn+=-21 cxzfmw@*#&*-=

                            # case1: len < 4. Doesn't do anything
                            depend1 = RejectUnlessLessThanLength(N + 1)
                            depend1_1 = deepcopy(
                                read_only_depend)  #Doesn't affect the old
                            tmp_dependency_list1 = deepcopy(one_dep_list)
                            tmp_dependency_list1.prepend_dependency(depend1)
                            tmp_dependency_list1.prepend_dependency(depend1_1)

                            # case2,3,4 combined can be understood by drawing Venn diagram.
                            # case2: len > 3. Char at 3 == A. -> add one a.
                            # corner case: len > 3. Char at 3 = ?d -> add one ?d but should still be 2.
                            ori_set = read_only_depend.get_chars()
                            dest_set = get_dest_set(
                                ori_set
                            )  #So that what's in dest_set is not in ori_set
                            #if what's in the dest set is also in ori_set. it doesn't affect the number
                            difference_set = dest_set.difference(ori_set)
                            depend2_1 = RejectUnlessGreaterThanLength(N)
                            depend2_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend2_3 = deepcopy(read_only_depend)
                            depend2_3.set_number(depend2_3.get_number() - 1)

                            tmp_dependency_list2 = deepcopy(one_dep_list)
                            tmp_dependency_list2.prepend_dependency(depend2_2)
                            tmp_dependency_list2.prepend_dependency(depend2_3)

                            # case3: len > 3, Char at 3 != a/A. Doesn't Matter
                            complement_result = set(
                                x for x in set(Dicts.classes['z'])
                                if (x not in ori_set and x not in dest_set) or
                                (x in ori_set and x in dest_set))
                            depend3_1 = RejectUnlessGreaterThanLength(N)
                            depend3_2 = RejectUnlessCharInPosition(
                                complement_result, N)
                            depend3_3 = deepcopy(read_only_depend)

                            tmp_dependency_list3 = deepcopy(one_dep_list)
                            tmp_dependency_list3.prepend_dependency(depend3_2)
                            tmp_dependency_list3.prepend_dependency(depend3_3)

                            # case4: len > 3. Char at 3 == a. -> Delete one a. Need two in original.
                            ori_set = read_only_depend.get_chars()
                            dest_set = get_dest_set(ori_set)

                            # Toggle set (a,b,A)
                            # If char at 3 == A/a. Mean contains. Only use (a,b,A) - (a,B,A)
                            # Why? Because a,A still in the set. So you toggle that you get something still in the set.
                            # it is still satisfied.
                            difference_set = ori_set.difference(dest_set)

                            depend4_1 = RejectUnlessGreaterThanLength(N)
                            depend4_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend4_3 = deepcopy(read_only_depend)
                            depend4_3.set_number(depend4_3.get_number() + 1)

                            tmp_dependency_list4 = deepcopy(one_dep_list)
                            tmp_dependency_list4.prepend_dependency(depend4_2)
                            tmp_dependency_list4.prepend_dependency(depend4_3)

                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list1)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list2)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list3)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list4)

                        else:  # N < 0
                            #Tm /b
                            #Tm /E
                            #Tm /)
                            #Tm /?d
                            #Tm /?a
                            #vcxB qfb w212fE dasve fdsdf) sdfsf0 vxcsf1 bkon qjroi0fn aijs*

                            #case1: >0, char at pos -1 A. Get an extra a.
                            ori_set = read_only_depend.get_chars()
                            dest_set = get_dest_set(ori_set)
                            difference_set = dest_set.difference(ori_set)
                            depend1_1 = RejectUnlessGreaterThanLength(-N - 1)
                            depend1_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend1_3 = deepcopy(read_only_depend)
                            depend1_3.set_number(depend1_3.get_number() - 1)

                            tmp_dependency_list1 = deepcopy(one_dep_list)
                            tmp_dependency_list1.prepend_dependency(depend1_1)
                            tmp_dependency_list1.prepend_dependency(depend1_2)
                            tmp_dependency_list1.prepend_dependency(depend1_3)

                            #case2: >0, char at pos -1 not equal a/A. Doesnt matter
                            complement_result = set(
                                x for x in set(Dicts.classes['z'])
                                if (x not in ori_set and x not in dest_set) or
                                (x in ori_set and x in dest_set))
                            depend2_1 = RejectUnlessGreaterThanLength(-N - 1)
                            depend2_2 = RejectUnlessCharInPosition(
                                complement_result, N)
                            depend2_3 = deepcopy(read_only_depend)

                            tmp_dependency_list2 = deepcopy(one_dep_list)
                            tmp_dependency_list2.prepend_dependency(depend2_1)
                            tmp_dependency_list2.prepend_dependency(depend2_2)
                            tmp_dependency_list2.prepend_dependency(depend2_3)

                            #case3: >0, char at pos -1 a. Need 2
                            ori_set = read_only_depend.get_chars()
                            dest_set = dest_set = get_dest_set(ori_set)

                            # Toggle set (a,b,A)
                            # If char at 3 == A/a. Mean contains. Only use (a,b,A) - (a,B,A)
                            # Why? Because a,A still in the set. So you toggle that you get something still in the set.
                            # it is still satisfied.
                            difference_set = ori_set.difference(dest_set)
                            depend3_1 = RejectUnlessGreaterThanLength(-N - 1)
                            depend3_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend3_3 = deepcopy(read_only_depend)
                            depend3_3.set_number(depend3_3.get_number() + 1)

                            tmp_dependency_list3 = deepcopy(one_dep_list)
                            tmp_dependency_list3.prepend_dependency(depend3_1)
                            tmp_dependency_list3.prepend_dependency(depend3_2)
                            tmp_dependency_list3.prepend_dependency(depend3_3)

                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list1)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list2)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list3)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:

                        #Check Char in position
                        check_pos = read_only_depend.get_position()

                        if N >= 0:
                            # T4 =1a
                            # T4 =1?a
                            # T4 =4D
                            # T4 =4?a
                            # T0 (E
                            # T0 =0?a
                            # T0 =2a
                            # T3 (B
                            # T3 =3?a
                            # T3 =3f
                            # T2 (?a
                            # T2 =2-
                            # T4 )?a
                            # T4 )f
                            # T3 )a
                            # T3 )?a
                            # xg-1dfa hl=dfa21 cmaF214 skrf1243dz eghqFDZ21 Efds)(5)242df xbdad329Z1 Fiekd21^.
                            # zcsqF xmrqf czsA x03a xmewi fs3v fds8 vczn2 awo@

                            # No matter what position is toggled, to satisfy char at position, length has to be greater than abs(check_pos)
                            if check_pos >= 0:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    abs(check_pos))
                            else:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    -check_pos - 1)

                            # No matter where the rejection rule checks, if T9. Then introduce >9 and <=9
                            # T9, word_len <= 9
                            depend0_0 = RejectUnlessLessThanLength(
                                N + 1)  # The length from N
                            depend0_1 = deepcopy(read_only_depend)
                            tmp_dependency_list0 = deepcopy(one_dep_list)
                            tmp_dependency_list0.prepend_dependency(depend0_0)
                            tmp_dependency_list0.prepend_dependency(depend0_1)
                            tmp_dependency_list0.prepend_dependency(
                                deepcopy(depend_len_from_check_pos))
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list0)

                            # T9, word_len >9
                            depend_len_from_N = RejectUnlessGreaterThanLength(N)
                            if check_pos >= 0:  #If check char at positive position

                                if check_pos != N:  # T9, (a
                                    #Toggle position != char at positition.
                                    #Doesn't matter

                                    depend1_0 = deepcopy(read_only_depend)

                                    tmp_dependency_list1 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list1.prepend_dependency(
                                        depend1_0)
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list1)

                                else:  #T9, =9a
                                    #Toggle position = char at positition.
                                    #Literally toggle the chars here.

                                    ori_set = read_only_depend.get_chars()
                                    dest_set = get_dest_set(ori_set)
                                    depend2_0 = deepcopy(read_only_depend)
                                    depend2_0.set_chars(dest_set)

                                    tmp_dependency_list2 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list2.prepend_dependency(
                                        depend2_0)
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list2)

                            else:  # T9, )a. Only consider >= 10

                                # depend_len_from_N >= 10
                                # depend_len_from_check_pos >= 1
                                # Only when len ==
                                word_len = max(N + 1, -check_pos)
                                while True:
                                    if word_len < N - check_pos:
                                        #T9, )a. wordlen = 5
                                        #Doesn't matter

                                        depend1_0 = RejectUnlessLessThanLength(
                                            word_len + 1)
                                        depend1_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend1_2 = deepcopy(read_only_depend)

                                        tmp_dependency_list1 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_0)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_1)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list1)

                                    elif word_len == N - check_pos:  #Affect
                                        #If equals.
                                        #T9, )a. wordlen = 10
                                        #Then toggle the char

                                        depend2_0 = RejectUnlessLessThanLength(
                                            word_len + 1)
                                        depend2_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend2_2 = deepcopy(read_only_depend)
                                        ori_set = read_only_depend.get_chars()
                                        dest_set = get_dest_set(ori_set)
                                        depend2_2.set_chars(dest_set)

                                        tmp_dependency_list2 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_0)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_1)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list2)

                                    else:
                                        #Else
                                        #T9, )a. wordlen > 10
                                        #Doesnt matter
                                        depend3_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend3_2 = deepcopy(read_only_depend)

                                        tmp_dependency_list3 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list3.prepend_dependency(
                                            depend3_1)
                                        tmp_dependency_list3.prepend_dependency(
                                            depend3_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list3)
                                        break
                                    word_len += 1

                        else:  # N < 0

                            #Tm =0a
                            #Tm =0?a
                            #Tm =3d
                            #Tm =3?a
                            #Tm )a
                            #Tm )?a
                            #Tm )?d
                            #Tm )?l
                            #A X F f xbdD czdd asdfewfdDd xcmzafo xzD zmA feqa XV3 ZX* dsfmF vmce

                            # No matter what position is toggled, to satisfy char at position, length has to be greater than abs(check_pos)
                            if check_pos >= 0:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    abs(check_pos))
                            else:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    -check_pos - 1)

                            depend_len_from_N = RejectUnlessGreaterThanLength(
                                -N - 1)

                            if check_pos >= 0:  # Tm, (a

                                #Enumerate word length
                                word_len = max(-N, check_pos + 1)
                                while True:
                                    if word_len < check_pos - N:
                                        #Tm, =2a. word len 1
                                        #Doesnt matter

                                        depend1_0 = RejectUnlessLessThanLength(
                                            word_len + 1)
                                        depend1_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend1_2 = deepcopy(read_only_depend)

                                        tmp_dependency_list1 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_0)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_1)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list1)

                                    elif word_len == check_pos - N:  #Affect
                                        #Tm, =2a, wordlen = 3
                                        #Affect, toggle.

                                        depend2_0 = RejectUnlessLessThanLength(
                                            word_len + 1)
                                        depend2_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend2_2 = deepcopy(read_only_depend)
                                        ori_set = read_only_depend.get_chars()
                                        dest_set = get_dest_set(ori_set)
                                        depend2_2.set_chars(dest_set)

                                        tmp_dependency_list2 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_0)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_1)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list2)

                                    else:
                                        #Tm, =2a, wordlen > 3
                                        #Doesnt matter
                                        depend3_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend3_2 = deepcopy(read_only_depend)

                                        tmp_dependency_list3 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list3.prepend_dependency(
                                            depend3_1)
                                        tmp_dependency_list3.prepend_dependency(
                                            depend3_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list3)
                                        break
                                    word_len += 1

                            else:  #check_pos <0, N < 0

                                if check_pos != N:  # Tm, =-2a
                                    #If the Tm, =-2a,
                                    #Doesnt affect
                                    depend1_0 = deepcopy(read_only_depend)

                                    tmp_dependency_list1 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list1.prepend_dependency(
                                        depend1_0)
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list1)

                                else:  #Tm, )a
                                    #Affect, toggle

                                    ori_set = read_only_depend.get_chars()
                                    dest_set = get_dest_set(ori_set)
                                    depend2_0 = deepcopy(read_only_depend)
                                    depend2_0.set_chars(dest_set)

                                    tmp_dependency_list2 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list2.prepend_dependency(
                                        depend2_0)
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list2)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend = deepcopy(read_only_depend)

                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend = deepcopy(read_only_depend)

                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        # case1: len < 4. Doesn't do anything
                        depend1 = RejectUnlessLessThanLength(N + 1)
                        depend1_1 = deepcopy(
                            read_only_depend)  #Doesn't affect the old
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(depend1)
                        no_op_dep_list.prepend_dependency(depend1_1)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N)

                        if from_idx >= 0:
                            # Case1: N in [from, to)
                            if to_idx > N >= from_idx:
                                toggled_chars = set(
                                    Dicts.toggle.setdefault(x, x)
                                    for x in chars)

                                # case1.1: toggled_chars not in chars.
                                toggled_chars_not_in = toggled_chars - chars
                                dep_list_case_2 = deepcopy(one_dep_list)
                                dep_list_case_2.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        toggled_chars_not_in, N))
                                dep_list_case_2.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number - 1, chars))
                                dep_list_case_2.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_2)

                                # case1.3: (set(Dicts.classes['z']) - toggled_chars) & chars, +1. Say T1, %a. If T1 = a, add 1 to number
                                chars_not_in_toggled = chars - toggled_chars
                                dep_list_case_3 = deepcopy(one_dep_list)
                                dep_list_case_3.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        chars_not_in_toggled, N))
                                dep_list_case_3.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number + 1, chars))
                                dep_list_case_3.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_3)

                                # case1.2: (set(Dicts.classes['z']) - toggled_chars_not_in) - chars, doesn't change
                                dep_list_case_1 = deepcopy(one_dep_list)
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) -
                                        chars_not_in_toggled -
                                        toggled_chars_not_in, N))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                            # Case2: N not in [from, to)
                            else:
                                one_dep_list.prepend_dependency(
                                    read_only_depend)
                                one_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                        else:
                            # Case1: N in [from, to), where N - from_idx >= len > N - to_idx
                            toggled_chars = set(
                                Dicts.toggle.setdefault(x, x) for x in chars)

                            # case1.1: toggled_chars not in chars.
                            toggled_chars_not_in = toggled_chars - chars
                            dep_list_case_2 = deepcopy(one_dep_list)
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    toggled_chars_not_in, N))
                            dep_list_case_2.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number - 1, chars))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_2.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_2)

                            # case1.3: (set(Dicts.classes['z']) - toggled_chars) & chars, +1. Say T1, %a. If T1 = a, add 1 to number
                            chars_not_in_toggled = chars - toggled_chars
                            dep_list_case_3 = deepcopy(one_dep_list)
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    chars_not_in_toggled, N))
                            dep_list_case_3.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number + 1, chars))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_3.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_3)

                            # case1.2: (set(Dicts.classes['z']) - toggled_chars_not_in) - chars, doesn't change
                            dep_list_case_1 = deepcopy(one_dep_list)
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) -
                                    chars_not_in_toggled - toggled_chars_not_in,
                                    N))
                            dep_list_case_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_1.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1)

                            # case1.3 & 1.4 doesn't matter
                            dep_list_case_4 = deepcopy(one_dep_list)
                            dep_list_case_4.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_4.prepend_dependency(
                                RejectUnlessLessThanLength(N - to_idx + 1))
                            dep_list_case_4.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_4)

                            dep_list_case_5 = deepcopy(one_dep_list)
                            dep_list_case_5.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_5.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - from_idx))
                            dep_list_case_5.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_5)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_prime_N_command(subrule_dependency, rule):
        """ Truncates word at position N

        Effects on Dependency:
            Length max is now N, use [from, to) to reason about

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Countable")

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        if N == 0:
                            one_dep_list.prepend_dependency(
                                RejectUnlessLessThanLength(0))
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)
                            continue
                        # mutual exclusive cases

                        # Case1, length <= N, do nothing
                        depend_length_no_op = RejectUnlessLessThanLength(N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # Case2, from 0 to N has at least that number
                        op_dep_list_1 = deepcopy(one_dep_list)
                        op_dep_list_1.prepend_dependency(
                            RejectUnlessFromToContainsAtLeastNumberOfChars(
                                0, N, read_only_depend.get_number(),
                                read_only_depend.get_chars()))
                        op_dep_list_1.prepend_dependency(
                            RejectUnlessGreaterThanLength(N - 1))
                        save_split_dep_lists.append_dependency_list(
                            op_dep_list_1)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        if N == 0:
                            one_dep_list.prepend_dependency(
                                RejectUnlessLessThanLength(0))
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)
                            continue
                        # Case1, length <= N, do nothing
                        depend_length_no_op = RejectUnlessLessThanLength(N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # Case2, from 0 to N, enumerate.
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N - 1)

                        if read_only_depend.get_position() >= 0:
                            # char at 2 menas len = 3
                            if read_only_depend.get_position() >= N:
                                # Rejected
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(
                                    RejectUnlessLessThanLength(0))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                            else:
                                # doesn't change anything
                                depend = deepcopy(read_only_depend)
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(depend)
                                op_dep_list.prepend_dependency(
                                    depend_length_op_lower)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                        else:
                            # char at -2 menas len = 2
                            if -1 * read_only_depend.get_position() > N:
                                # Rejected
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(
                                    RejectUnlessLessThanLength(0))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                            else:
                                # now checking N + position
                                depend = deepcopy(read_only_depend)
                                depend.set_position(N + depend.get_position())
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(depend)
                                op_dep_list.prepend_dependency(
                                    depend_length_op_lower)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:

                        # case1: say '6, everything <= 6, if require < 7 or require < 8, satisfy
                        if read_only_depend.get_len() >= N + 1:
                            # Satisfy
                            depend = deepcopy(read_only_depend)
                            depend.set_len(
                                RUNTIME_CONFIG['max_password_length'] + 1)
                            op_dep_list = deepcopy(one_dep_list)
                            op_dep_list.prepend_dependency(depend)
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list)

                        # case2: say '6, if require < 3, still <3
                        else:
                            depend = deepcopy(read_only_depend)
                            op_dep_list = deepcopy(one_dep_list)
                            op_dep_list.prepend_dependency(depend)
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:

                        # case1: say '6, everything <= 6, if require > 6, reject
                        if N <= read_only_depend.get_len():
                            # Reject
                            depend = deepcopy(read_only_depend)
                            depend.set_len(
                                RUNTIME_CONFIG['max_password_length'] + 1)
                            op_dep_list = deepcopy(one_dep_list)
                            op_dep_list.prepend_dependency(depend)
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list)

                        # case2: say '6, if require > 4, still > 4
                        else:
                            depend = deepcopy(read_only_depend)
                            op_dep_list = deepcopy(one_dep_list)
                            op_dep_list.prepend_dependency(depend)
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        # Case1, length < N, do nothing
                        depend_length_no_op = RejectUnlessLessThanLength(N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # >= N,
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N - 1)

                        from_idx = read_only_depend.get_from()
                        to_idx = read_only_depend.get_to()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        if from_idx >= 0:
                            # this requires len >= to_idx, 'N requires >= N and set len to N.
                            # case1: doesn't change anything
                            if N >= to_idx:
                                one_dep_list.prepend_dependency(
                                    read_only_depend)
                                one_dep_list.prepend_dependency(
                                    depend_length_op_lower)
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)
                            # case2: Rejected
                            else:
                                pass

                        else:
                            # this requires len >= -from_idx, 'N requires >= N and set len to N.
                            if N >= -from_idx:
                                one_dep_list.prepend_dependency(
                                    read_only_depend.make_new(
                                        N + from_idx, N + to_idx, number,
                                        chars))
                                one_dep_list.prepend_dependency(
                                    depend_length_op_lower)
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                            # rejected.
                            else:
                                pass

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_p_N_command(subrule_dependency, rule):
        """ pN  Appends duplicated word N times: pass -> (p2) passpasspass

        Effects on Dependency:
            divide length by N + 1, enumerate position to further investigate

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        try:
            N = convert_str_length_to_int(rule[1]) + 1
        except:
            raise NotCountableException("Not Countable")

        # p0, n = 1,  doesn't change anything
        if N == 1:
            return subrule_dependency

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    # Reject_Unless_Contains_Number_Of_Char or Reject_If_Contains_Number_Of_Char
                    if read_only_depend.dependency_type == 2 or read_only_depend.dependency_type == 1:
                        #Play tricks
                        if read_only_depend.get_number() == 1:
                            #print("Tricks in pN")
                            depend0 = deepcopy(read_only_depend)
                            one_dep_list.prepend_dependency(depend0)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)
                            continue

                        # If Length * N >= (RUNTIME_CONFIG['max_password_length'] + 1), Nothing
                        depend_length_no_op = RejectUnlessGreaterThanLength(
                            int(
                                math.ceil((RUNTIME_CONFIG['max_password_length']
                                           + 1) / N)) - 1)
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        depend_length_op = RejectUnlessLessThanLength(
                            int(
                                math.ceil(
                                    (RUNTIME_CONFIG['max_password_length'] + 1)
                                    / N)))

                        depend = deepcopy(read_only_depend)

                        ori_number = depend.get_number()
                        dest_number = int(math.ceil(ori_number * 1.0 / N))
                        depend.set_number(dest_number)

                        one_dep_list.prepend_dependency(depend)
                        one_dep_list.prepend_dependency(depend_length_op)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        # no operation due to too long.
                        depend_length_no_op = RejectUnlessGreaterThanLength(
                            int(
                                math.ceil((RUNTIME_CONFIG['max_password_length']
                                           + 1) / N)) - 1)
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        # op
                        depend_length_op = RejectUnlessLessThanLength(
                            int(
                                math.ceil(
                                    (RUNTIME_CONFIG['max_password_length'] + 1)
                                    / N)))

                        #Original d command
                        depend = deepcopy(read_only_depend)

                        # Get check position
                        ori_pos = depend.get_position()

                        # If check -3, >= 3 duplicate doesnt chagne the result
                        # If not, other
                        if ori_pos < 0:
                            #Case1: Length >= abs(ori_pos), Doesn't matter
                            depend_case_1 = RejectUnlessGreaterThanLength(
                                abs(ori_pos) - 1)
                            dependency_list_case_1 = deepcopy(one_dep_list)
                            dependency_list_case_1.prepend_dependency(
                                depend_length_op)
                            dependency_list_case_1.prepend_dependency(
                                depend_case_1)
                            dependency_list_case_1.prepend_dependency(
                                deepcopy(depend))
                            save_split_dep_lists.append_dependency_list(
                                dependency_list_case_1)

                            #Case2: Length * N >= abs(ori_pos) && Length < abs(ori_pos)
                            #Check New Pos
                            for word_len in range(
                                    int(math.ceil(abs(ori_pos) / N)),
                                    abs(ori_pos)):
                                depend_len_lower = RejectUnlessGreaterThanLength(
                                    word_len - 1)
                                depend_len_upper = RejectUnlessLessThanLength(
                                    word_len + 1)
                                depend_case_2 = deepcopy(read_only_depend)

                                #Checked Length: abs(ori_pos)
                                #Total Length: word_len * N
                                #Suppose d r -4. -> wordlen = 2, 3

                                #if (abs(ori_pos) % word_len) == 0:
                                #new_pos = -word_len
                                #else:
                                #new_pos = - (abs(ori_pos) % word_len)
                                #depend_case_2.set_position(new_pos)
                                #Here there are 2 cases. So we use all positive.
                                #below should be simplified.
                                depend_case_2.set_position(
                                    -abs(ori_pos) % word_len)

                                dependency_list_case_2 = deepcopy(one_dep_list)
                                dependency_list_case_2.prepend_dependency(
                                    depend_length_op)
                                dependency_list_case_2.prepend_dependency(
                                    depend_len_lower)
                                dependency_list_case_2.prepend_dependency(
                                    depend_len_upper)
                                dependency_list_case_2.prepend_dependency(
                                    depend_case_2)
                                save_split_dep_lists.append_dependency_list(
                                    dependency_list_case_2)

                        elif ori_pos >= 0:

                            #Depends on the length

                            #Length at least (ori_pos + 1) / N)
                            #Otherwise char_in_pos is rejected.
                            word_len = int(math.ceil((ori_pos + 1) / N))

                            while True:  # =5a case1: >= 3, <=5. case2: >=6.
                                tmp = deepcopy(one_dep_list)

                                depend_len_lower = RejectUnlessGreaterThanLength(
                                    word_len - 1)
                                depend_len_upper = RejectUnlessLessThanLength(
                                    word_len + 1)

                                #case1.
                                # =5a, length <=5.
                                if word_len <= ori_pos:
                                    depend_char_at_pos = RejectUnlessCharInPosition(
                                        depend.get_chars(), ori_pos % word_len)
                                    tmp.prepend_dependency(depend_length_op)
                                    tmp.prepend_dependency(depend_len_lower)
                                    tmp.prepend_dependency(depend_len_upper)
                                    tmp.prepend_dependency(depend_char_at_pos)
                                    save_split_dep_lists.append_dependency_list(
                                        tmp)

                                # case2
                                # length >= 6
                                else:
                                    tmp.prepend_dependency(depend_length_op)
                                    tmp.prepend_dependency(depend_len_lower)
                                    tmp.prepend_dependency(depend)
                                    save_split_dep_lists.append_dependency_list(
                                        tmp)
                                    break

                                word_len += 1

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend_length_not_dup = RejectUnlessGreaterThanLength(
                            int(
                                math.ceil((RUNTIME_CONFIG['max_password_length']
                                           + 1) / N)) - 1)
                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(
                            depend_length_not_dup)  # >=16 do nothing
                        tmp_dependency_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                        # OP
                        depend_length_op = RejectUnlessLessThanLength(
                            int(
                                math.ceil(
                                    (RUNTIME_CONFIG['max_password_length'] + 1)
                                    / N)))

                        # original d command
                        depend = deepcopy(read_only_depend)

                        ori_len = depend.get_len()
                        dest_len = int(math.floor((ori_len - 1) * 1.0 / N) + 1)
                        depend.set_len(dest_len)

                        one_dep_list.prepend_dependency(depend)
                        one_dep_list.prepend_dependency(depend_length_op)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend_length_no_op = RejectUnlessGreaterThanLength(
                            int(
                                math.ceil((RUNTIME_CONFIG['max_password_length']
                                           + 1) / N)) - 1)
                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(
                            depend_length_no_op)  # >=16 do nothing
                        tmp_dependency_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                        # No OP
                        depend_length_op = RejectUnlessLessThanLength(
                            int(
                                math.ceil(
                                    (RUNTIME_CONFIG['max_password_length'] + 1)
                                    / N)))

                        # original d command
                        depend = deepcopy(read_only_depend)

                        ori_len = depend.get_len()
                        dest_len = int(math.ceil((ori_len + 1) * 1.0 / N) - 1)
                        depend.set_len(dest_len)

                        one_dep_list.prepend_dependency(depend)
                        one_dep_list.prepend_dependency(depend_length_op)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    elif read_only_depend.dependency_type == 4:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        # from i to j, has x nunmber of char c.
                        # need to enumerate to x
                        if from_idx >= 0:
                            min_len = (to_idx + N - 1) // N  #ceil operation
                            max_len = to_idx
                        else:
                            min_len = (-from_idx + N - 1) // N  #ceil operation
                            max_len = -from_idx

                        # first case, input_len >= N, do nothing
                        op_dep_list_1 = deepcopy(one_dep_list)
                        op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        op_dep_list_1.prepend_dependency(
                            RejectUnlessGreaterThanLength(max_len - 1))
                        save_split_dep_lists.append_dependency_list(
                            op_dep_list_1)

                        for input_len in range(min_len, max_len):
                            # count number of full duplicate, also find left bound and right bound
                            counter = [0 for _ in range(input_len)]
                            for i in range(from_idx, to_idx):
                                i_in_original = i % input_len
                                counter[i_in_original] += 1

                            # get number of full dups
                            num_full_dup = sum(counter) // input_len
                            counter = [i - num_full_dup for i in counter]
                            if sum(counter
                                  ) == 0:  # only contained in full_dups:
                                # number only valid when mutiply of num_full_dup
                                if number % num_full_dup == 0:
                                    # avoid cases where num_full_dup = 0, it doesn't involve full_dup
                                    tmp_one_dep_list = deepcopy(one_dep_list)
                                    tmp_one_dep_list.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))
                                    tmp_one_dep_list.prepend_dependency(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    tmp_one_dep_list.prepend_dependency(
                                        read_only_depend.make_new(
                                            0, input_len,
                                            math.ceil(number / num_full_dup),
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_one_dep_list)

                            else:  # there's a left bound or right bound
                                # left bound
                                left_from = 0
                                left_to = 0
                                start = False
                                for i, v in enumerate(counter):
                                    if v > 0:
                                        if start == False:
                                            left_from = i
                                            left_to = i + 1
                                            start = True
                                        else:
                                            left_to = i + 1
                                    else:
                                        if start == True:
                                            break
                                        else:
                                            continue

                                # right bound
                                right_from = 0
                                right_to = 0
                                start = False
                                for i in range(left_to, len(counter)):
                                    v = counter[i]
                                    if v > 0:
                                        if start == False:
                                            right_from = i
                                            right_to = i + 1
                                            start = True
                                        else:
                                            right_to = i + 1
                                    else:
                                        if start == True:
                                            break
                                        else:
                                            continue

                                # next enumerate number of chars in full
                                if num_full_dup > 0:
                                    # enumerate_range = [ ceil(number / num_full_dup+1), ceil(number/ num_full_dup) )
                                    # the chars needed in a full_dup
                                    enumerate_range = range(
                                        math.ceil(number / (num_full_dup + 1)),
                                        math.ceil(number / num_full_dup))
                                    for num_chars_in_full in enumerate_range:

                                        addition_requirements = []
                                        addition_requirements.append(
                                            RejectUnlessLessThanLength(
                                                input_len + 1))
                                        addition_requirements.append(
                                            RejectUnlessGreaterThanLength(
                                                input_len - 1))
                                        # full dup requirements
                                        addition_requirements.append(
                                            RejectUnlessFromToContainsExactlyNumberOfChars(
                                                0, input_len, num_chars_in_full,
                                                chars))
                                        # there is something to share by left and rights and not empty range
                                        FeatureExtraction.handles_left_right_shares_number_for_exact(
                                            left_from, left_to, right_from,
                                            right_to, number -
                                            num_full_dup * num_chars_in_full,
                                            chars, read_only_depend,
                                            one_dep_list, save_split_dep_lists,
                                            addition_requirements)

                                    # number only valid when mutiply of num_full_dup
                                    if number % num_full_dup == 0:
                                        # avoid cases where num_full_dup = 0, it doesn't involve full_dup
                                        tmp_one_dep_list = deepcopy(
                                            one_dep_list)
                                        tmp_one_dep_list.prepend_dependency(
                                            RejectUnlessGreaterThanLength(
                                                input_len - 1))
                                        tmp_one_dep_list.prepend_dependency(
                                            RejectUnlessLessThanLength(
                                                input_len + 1))
                                        # other two sides should be exactly 0
                                        if left_from != left_to:
                                            tmp_one_dep_list.prepend_dependency(
                                                RejectUnlessFromToContainsExactlyNumberOfChars(
                                                    left_from, left_to, 0,
                                                    chars))  # others are 0
                                        if right_from != right_to:
                                            tmp_one_dep_list.prepend_dependency(
                                                RejectUnlessFromToContainsExactlyNumberOfChars(
                                                    right_from, right_to, 0,
                                                    chars))  # others are 0
                                        tmp_one_dep_list.prepend_dependency(
                                            read_only_depend.make_new(
                                                0, input_len,
                                                math.ceil(
                                                    number / num_full_dup),
                                                chars))
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_one_dep_list)

                                else:  # the range [from, to) doesn't cover a full range
                                    addition_requirements = []
                                    addition_requirements.append(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    addition_requirements.append(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))
                                    FeatureExtraction.handles_left_right_shares_number_for_exact(
                                        left_from, left_to, right_from,
                                        right_to, number, chars,
                                        read_only_depend, one_dep_list,
                                        save_split_dep_lists,
                                        addition_requirements)

                    elif read_only_depend.dependency_type == 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        # from i to j, has x nunmber of char c.
                        # need to enumerate to x
                        if from_idx >= 0:
                            min_len = (to_idx + N - 1) // N  #ceil operation
                            max_len = to_idx
                        else:
                            min_len = (-from_idx + N - 1) // N  #ceil operation
                            max_len = -from_idx

                        # first case, input_len >= N, do nothing
                        op_dep_list_1 = deepcopy(one_dep_list)
                        op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        op_dep_list_1.prepend_dependency(
                            RejectUnlessGreaterThanLength(max_len - 1))
                        save_split_dep_lists.append_dependency_list(
                            op_dep_list_1)

                        for input_len in range(min_len, max_len):

                            # count number of full duplicate, also find left bound and right bound
                            counter = [0 for _ in range(input_len)]
                            for i in range(from_idx, to_idx):
                                i_in_original = i % input_len
                                counter[i_in_original] += 1

                            # get number of full dups
                            num_full_dup = sum(counter) // input_len
                            counter = [i - num_full_dup for i in counter]
                            if sum(
                                    counter
                            ) == 0:  # only contained in full_dups, each full_dup should have at least ceil(number / num_full_dup)
                                tmp_one_dep_list = deepcopy(one_dep_list)
                                tmp_one_dep_list.prepend_dependency(
                                    RejectUnlessGreaterThanLength(input_len -
                                                                  1))
                                tmp_one_dep_list.prepend_dependency(
                                    RejectUnlessLessThanLength(input_len + 1))
                                tmp_one_dep_list.prepend_dependency(
                                    read_only_depend.make_new(
                                        0, input_len,
                                        math.ceil(number / num_full_dup),
                                        chars))
                                save_split_dep_lists.append_dependency_list(
                                    tmp_one_dep_list)

                            else:  # there's a left bound or right bound
                                # left bound
                                left_from = 0
                                left_to = 0
                                start = False
                                for i, v in enumerate(counter):
                                    if v > 0:
                                        if start == False:
                                            left_from = i
                                            left_to = i + 1
                                            start = True
                                        else:
                                            left_to = i + 1
                                    else:
                                        if start == True:
                                            break
                                        else:
                                            continue

                                # right bound
                                right_from = 0
                                right_to = 0
                                start = False
                                for i in range(left_to, len(counter)):
                                    v = counter[i]
                                    if v > 0:
                                        if start == False:
                                            right_from = i
                                            right_to = i + 1
                                            start = True
                                        else:
                                            right_to = i + 1
                                    else:
                                        if start == True:
                                            break
                                        else:
                                            continue

                                # next enumerate number of chars in full
                                if num_full_dup > 0:
                                    # enumerate_range = [ ceil(number / num_full_dup+1), ceil(number/ num_full_dup) )
                                    # the chars needed in a full_dup
                                    enumerate_range = range(
                                        math.ceil(number / (num_full_dup + 1)),
                                        math.ceil(number / num_full_dup))
                                    for num_chars_in_full in enumerate_range:

                                        addition_requirements = []
                                        addition_requirements.append(
                                            RejectUnlessLessThanLength(
                                                input_len + 1))
                                        addition_requirements.append(
                                            RejectUnlessGreaterThanLength(
                                                input_len - 1))
                                        # full dup requirements
                                        addition_requirements.append(
                                            RejectUnlessFromToContainsExactlyNumberOfChars(
                                                0, input_len, num_chars_in_full,
                                                chars))
                                        # there is something to share by left and rights and not empty range
                                        FeatureExtraction.handles_left_right_shares_number_for_at_least(
                                            left_from, left_to, right_from,
                                            right_to, number -
                                            num_full_dup * num_chars_in_full,
                                            chars, read_only_depend,
                                            one_dep_list, save_split_dep_lists,
                                            addition_requirements)

                                    # avoid cases where num_full_dup = 0, it doesn't involve full_dup
                                    tmp_one_dep_list = deepcopy(one_dep_list)
                                    tmp_one_dep_list.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))
                                    tmp_one_dep_list.prepend_dependency(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    ### here we do not add left/right exactly = 0 ###
                                    tmp_one_dep_list.prepend_dependency(
                                        read_only_depend.make_new(
                                            0, input_len,
                                            math.ceil(number / num_full_dup),
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_one_dep_list)

                                else:  # only has a left_range and right range.
                                    addition_requirements = []
                                    addition_requirements.append(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    addition_requirements.append(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))
                                    FeatureExtraction.handles_left_right_shares_number_for_at_least(
                                        left_from, left_to, right_from,
                                        right_to, number, chars,
                                        read_only_depend, one_dep_list,
                                        save_split_dep_lists,
                                        addition_requirements)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_z_N_command(subrule_dependency, rule):
        """ zN  Duplicates first character N times: hi -> (z2) hhhi

        Effects on Dependency:
            Case by case study on the first char

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists

        Fixes like yN
        """
        ret_val = SubruleDependency(subrule_dependency)

        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Countable")

        if N == 0:
            return subrule_dependency

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        # Play Tricks To Speed Up. zN does not introduce new chars.
                        # In this case zN command doesn't change anything
                        if read_only_depend.get_number() == 1:
                            #print("Tricks in zN")
                            depend0 = deepcopy(read_only_depend)
                            one_dep_list.prepend_dependency(depend0)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)
                            continue

                        # No op: word_len > RUNTIME_CONFIG['max_password_length'] - N# or length = 0
                        # word_len + N >= RUNTIME_CONFIG['max_password_length']+1
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length = 0, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            0)

                        # Case1: Char_At_0 equals
                        depend_char_at_0_equals = RejectUnlessCharInPosition(
                            read_only_depend.get_chars(), 0)
                        depend = deepcopy(read_only_depend)
                        depend.set_number(depend.get_number() - N)
                        op_dep_list_1 = deepcopy(one_dep_list)
                        op_dep_list_1.prepend_dependency(
                            deepcopy(depend_length_op_upper))
                        op_dep_list_1.prepend_dependency(
                            deepcopy(depend_length_op_lower))
                        op_dep_list_1.prepend_dependency(depend)
                        op_dep_list_1.prepend_dependency(
                            depend_char_at_0_equals)
                        save_split_dep_lists.append_dependency_list(
                            op_dep_list_1)

                        # Case2: Char_At_0 NOT equals
                        depend_char_at_0_not_equals = RejectUnlessCharInPosition(
                            set(Dicts.classes['z']) -
                            read_only_depend.get_chars(), 0)
                        depend = deepcopy(read_only_depend)
                        op_dep_list_2 = deepcopy(one_dep_list)
                        op_dep_list_2.prepend_dependency(
                            deepcopy(depend_length_op_upper))
                        op_dep_list_2.prepend_dependency(
                            deepcopy(depend_length_op_lower))
                        op_dep_list_2.prepend_dependency(depend)
                        op_dep_list_2.prepend_dependency(
                            depend_char_at_0_not_equals)
                        save_split_dep_lists.append_dependency_list(
                            op_dep_list_2)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        #Think of it as prepend

                        # No op: word_len > RUNTIME_CONFIG['max_password_length'] - N# or length = 0
                        # word_len + N >= RUNTIME_CONFIG['max_password_length']+1
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length = 0, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            0)

                        ori_pos = read_only_depend.get_position()
                        if ori_pos >= 0:

                            if (N + 1) < ori_pos + 1:
                                #ori_pos = ori_pos - N -1
                                ori_pos = ori_pos - N
                                depend = deepcopy(read_only_depend)
                                depend.set_position(ori_pos)
                                op_dep_list_1 = deepcopy(one_dep_list)
                                op_dep_list_1.prepend_dependency(
                                    deepcopy(depend_length_op_upper))
                                op_dep_list_1.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                op_dep_list_1.prepend_dependency(depend)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_1)

                            else:
                                ori_pos = 0
                                depend = deepcopy(read_only_depend)
                                depend.set_position(ori_pos)
                                op_dep_list_2 = deepcopy(one_dep_list)
                                op_dep_list_2.prepend_dependency(
                                    deepcopy(depend_length_op_upper))
                                op_dep_list_2.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                op_dep_list_2.prepend_dependency(depend)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_2)

                        else:
                            #If Length >= -ori_pos, doesn't matter
                            depend = deepcopy(read_only_depend)
                            depend_length_no_op_because_long_word = RejectUnlessGreaterThanLength(
                                -ori_pos - 1)
                            op_dep_list_3 = deepcopy(one_dep_list)
                            op_dep_list_3.prepend_dependency(
                                deepcopy(depend_length_op_upper))
                            op_dep_list_3.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            op_dep_list_3.prepend_dependency(depend)
                            op_dep_list_3.prepend_dependency(
                                depend_length_no_op_because_long_word)
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list_3)

                            #If Length < -ori_pos and Length + N >= -ori_pos, Means the first one.
                            depend = deepcopy(read_only_depend)
                            depend_length_op_max_length = RejectUnlessLessThanLength(
                                -ori_pos)
                            depend_length_op_min_length = RejectUnlessGreaterThanLength(
                                -ori_pos - N -
                                1)  #You can write this because added >0 below
                            depend.set_position(0)
                            op_dep_list_4 = deepcopy(one_dep_list)
                            op_dep_list_4.prepend_dependency(
                                deepcopy(depend_length_op_upper))
                            op_dep_list_4.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            op_dep_list_4.prepend_dependency(depend)
                            op_dep_list_4.prepend_dependency(
                                depend_length_op_max_length)
                            op_dep_list_4.prepend_dependency(
                                depend_length_op_min_length)
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list_4)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length = 0, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            0)

                        # Reduce the rejection length
                        depend = deepcopy(read_only_depend)
                        depend.set_len(depend.get_len() - N)
                        op_dep_list = deepcopy(one_dep_list)
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_upper))
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_lower))
                        op_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(op_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length = 0, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            0)

                        # Reduce the rejection length
                        depend = deepcopy(read_only_depend)
                        depend.set_len(depend.get_len() - N)
                        op_dep_list = deepcopy(one_dep_list)
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_upper))
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_lower))
                        op_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(op_dep_list)

                    elif read_only_depend.dependency_type == 4:
                        # no op
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(depend_length_no_op))
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # no op
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(depend_length_no_op_greater))
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # op
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            0)
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)

                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        if from_idx >= 0:
                            if from_idx >= N:  #doesn't matter
                                from_idx -= N
                                to_idx -= N

                                op_dep_list = deepcopy(one_dep_list)
                                tmp_dep = read_only_depend.make_new(
                                    from_idx, to_idx, number, chars)
                                op_dep_list.prepend_dependency(tmp_dep)
                                op_dep_list.prepend_dependency(
                                    depend_length_op_lower)
                                op_dep_list.prepend_dependency(
                                    depend_length_op_upper)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                            else:
                                # [from_idx, N) are all first char's dups
                                # [N, to_idx) are others
                                if to_idx > N + 1:
                                    # case1: first char in chars.
                                    tmp_dep = read_only_depend.make_new(
                                        0, to_idx - N, number - (N - from_idx),
                                        chars)

                                    dep_list_case_1 = deepcopy(one_dep_list)
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, 0))
                                    dep_list_case_1.prepend_dependency(tmp_dep)
                                    dep_list_case_1.prepend_dependency(
                                        depend_length_op_lower)
                                    dep_list_case_1.prepend_dependency(
                                        depend_length_op_upper)
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_1)

                                    # case2: first char not in chars.
                                    tmp_dep = read_only_depend.make_new(
                                        0, to_idx - N, number, chars)

                                    dep_list_case_2 = deepcopy(one_dep_list)
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars, 0))
                                    dep_list_case_2.prepend_dependency(tmp_dep)
                                    dep_list_case_2.prepend_dependency(
                                        depend_length_op_lower)
                                    dep_list_case_2.prepend_dependency(
                                        depend_length_op_upper)
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_2)

                                else:  # all first char's dup

                                    # case 1: exactly to-from_idx
                                    if number == to_idx - from_idx:
                                        dep_list_case_1 = deepcopy(one_dep_list)
                                        dep_list_case_1.prepend_dependency(
                                            RejectUnlessCharInPosition(
                                                chars, 0))
                                        dep_list_case_1.prepend_dependency(
                                            depend_length_op_lower)
                                        dep_list_case_1.prepend_dependency(
                                            depend_length_op_upper)
                                        save_split_dep_lists.append_dependency_list(
                                            dep_list_case_1)

                                    # case exactly 0
                                    if number == 0:
                                        dep_list_case_1 = deepcopy(one_dep_list)
                                        dep_list_case_1.prepend_dependency(
                                            RejectUnlessCharInPosition(
                                                set(Dicts.classes['z']) - chars,
                                                0))
                                        dep_list_case_1.prepend_dependency(
                                            depend_length_op_lower)
                                        dep_list_case_1.prepend_dependency(
                                            depend_length_op_upper)
                                        save_split_dep_lists.append_dependency_list(
                                            dep_list_case_1)

                        else:
                            # if input_len >= -from, doesn't matter
                            dep_list_case_0 = deepcopy(one_dep_list)
                            dep_list_case_0.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_0.prepend_dependency(
                                RejectUnlessGreaterThanLength(-from_idx - 1))
                            dep_list_case_0.prepend_dependency(
                                deepcopy(depend_length_op_upper))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_0)

                            # else if -from > input_len >= max(1, -from-N), if char at 0, or not
                            for input_len in range(
                                    max(1, -from_idx - N), -from_idx):
                                # case1, char 0 in chars
                                dep_list_case_1 = deepcopy(one_dep_list)

                                depend1_0 = RejectUnlessCharInPosition(chars, 0)
                                dep_list_case_1.prepend_dependency(depend1_0)

                                if -to_idx < input_len:  #some extra chars in original string
                                    depend1_1 = read_only_depend.make_new(
                                        0, input_len + to_idx,
                                        number + from_idx + input_len, chars)
                                    dep_list_case_1.prepend_dependency(
                                        depend1_1)

                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessGreaterThanLength(input_len -
                                                                  1))
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessLessThanLength(input_len + 1))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                                # case2, char 0 not in chars
                                if -to_idx < input_len:  #some extra chars in original string
                                    dep_list_case_2 = deepcopy(one_dep_list)
                                    depend2_0 = RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, 0)
                                    depend2_1 = read_only_depend.make_new(
                                        0, input_len + to_idx, number, chars)
                                    dep_list_case_2.prepend_dependency(
                                        depend2_0)
                                    dep_list_case_2.prepend_dependency(
                                        depend2_1)
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_2)

                                # else rejected, bcs char 0 not satisfy, not other strings

                    # from_to_contains
                    elif read_only_depend.dependency_type == 5:
                        # no op
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(depend_length_no_op))
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # no op
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(depend_length_no_op_greater))
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # op
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            0)
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)

                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        if from_idx >= 0:
                            if from_idx >= N:  #doesn't matter
                                from_idx -= N
                                to_idx -= N

                                op_dep_list = deepcopy(one_dep_list)
                                tmp_dep = read_only_depend.make_new(
                                    from_idx, to_idx, number, chars)
                                op_dep_list.prepend_dependency(tmp_dep)
                                op_dep_list.prepend_dependency(
                                    depend_length_op_lower)
                                op_dep_list.prepend_dependency(
                                    depend_length_op_upper)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                            else:
                                # [from_idx, N) are all first char's dups
                                # [N, to_idx) are others
                                if to_idx > N + 1:
                                    # case1: first char in chars.
                                    tmp_dep = read_only_depend.make_new(
                                        0, to_idx - N, number - (N - from_idx),
                                        chars)

                                    dep_list_case_1 = deepcopy(one_dep_list)
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, 0))
                                    dep_list_case_1.prepend_dependency(tmp_dep)
                                    dep_list_case_1.prepend_dependency(
                                        depend_length_op_lower)
                                    dep_list_case_1.prepend_dependency(
                                        depend_length_op_upper)
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_1)

                                    # case2: first char not in chars.
                                    tmp_dep = read_only_depend.make_new(
                                        0, to_idx - N, number, chars)

                                    dep_list_case_2 = deepcopy(one_dep_list)
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars, 0))
                                    dep_list_case_2.prepend_dependency(tmp_dep)
                                    dep_list_case_2.prepend_dependency(
                                        depend_length_op_lower)
                                    dep_list_case_2.prepend_dependency(
                                        depend_length_op_upper)
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_2)

                                else:  # all first char's dup
                                    tmp_dep = deepcopy(read_only_depend)
                                    tmp_dep.set_number(number -
                                                       (to_idx - from_idx))

                                    dep_list_case_1 = deepcopy(one_dep_list)
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, 0))
                                    dep_list_case_1.prepend_dependency(tmp_dep)
                                    dep_list_case_1.prepend_dependency(
                                        depend_length_op_lower)
                                    dep_list_case_1.prepend_dependency(
                                        depend_length_op_upper)
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_1)

                        else:
                            # if input_len >= -from, doesn't matter
                            dep_list_case_0 = deepcopy(one_dep_list)
                            dep_list_case_0.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_0.prepend_dependency(
                                RejectUnlessGreaterThanLength(-from_idx - 1))
                            dep_list_case_0.prepend_dependency(
                                deepcopy(depend_length_op_upper))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_0)

                            # else if -from > input_len >= max(1, -from-N), if char at 0, or not
                            for input_len in range(
                                    max(1, -from_idx - N), -from_idx):
                                # case1, char 0 in chars
                                dep_list_case_1 = deepcopy(one_dep_list)

                                depend1_0 = RejectUnlessCharInPosition(chars, 0)
                                dep_list_case_1.prepend_dependency(depend1_0)

                                if -to_idx < input_len:  #some extra chars in original string
                                    depend1_1 = read_only_depend.make_new(
                                        0, input_len + to_idx,
                                        number + from_idx + input_len, chars)
                                    dep_list_case_1.prepend_dependency(
                                        depend1_1)

                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessGreaterThanLength(input_len -
                                                                  1))
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessLessThanLength(input_len + 1))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                                # case2, char 0 not in chars
                                if -to_idx < input_len:  #some extra chars in original string
                                    dep_list_case_2 = deepcopy(one_dep_list)
                                    depend2_0 = RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, 0)
                                    depend2_1 = read_only_depend.make_new(
                                        0, input_len + to_idx, number, chars)
                                    dep_list_case_2.prepend_dependency(
                                        depend2_0)
                                    dep_list_case_2.prepend_dependency(
                                        depend2_1)
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_2)

                                # else rejected, bcs char 0 not satisfy, not other strings

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_Z_N_command(subrule_dependency, rule):
        """ ZN  Duplicates last character N times: hello -> (Z2) hellooo

        Effects on Dependency:
            case by case study of last char

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Countable")

        if N == 0:
            return subrule_dependency

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        # Play Tricks To Speed Up
                        if read_only_depend.get_number() == 1:
                            #print("Tricks in zN")
                            depend0 = deepcopy(read_only_depend)
                            one_dep_list.prepend_dependency(depend0)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)
                            continue

                        # No op: word_len > RUNTIME_CONFIG['max_password_length'] - N# or length = 0
                        # word_len + N >= RUNTIME_CONFIG['max_password_length']+1
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length = 0, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            0)

                        # Case1: Char_At_0 equals
                        depend_last_char_equals = RejectUnlessCharInPosition(
                            read_only_depend.get_chars(), -1)
                        depend = deepcopy(read_only_depend)
                        depend.set_number(depend.get_number() - N)
                        op_dep_list_1 = deepcopy(one_dep_list)
                        op_dep_list_1.prepend_dependency(
                            deepcopy(depend_length_op_upper))
                        op_dep_list_1.prepend_dependency(
                            deepcopy(depend_length_op_lower))
                        op_dep_list_1.prepend_dependency(depend)
                        op_dep_list_1.prepend_dependency(
                            depend_last_char_equals)
                        save_split_dep_lists.append_dependency_list(
                            op_dep_list_1)

                        # Case2: Char_At_0 NOT equals
                        depend_last_char_not_equals = RejectUnlessCharInPosition(
                            set(Dicts.classes['z']) -
                            read_only_depend.get_chars(), -1)
                        depend = deepcopy(read_only_depend)
                        op_dep_list_2 = deepcopy(one_dep_list)
                        op_dep_list_2.prepend_dependency(
                            deepcopy(depend_length_op_upper))
                        op_dep_list_2.prepend_dependency(
                            deepcopy(depend_length_op_lower))
                        op_dep_list_2.prepend_dependency(depend)
                        op_dep_list_2.prepend_dependency(
                            depend_last_char_not_equals)
                        save_split_dep_lists.append_dependency_list(
                            op_dep_list_2)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        #Think of it as prepend

                        # No op: word_len > RUNTIME_CONFIG['max_password_length'] - N# or length = 0
                        # word_len + N >= RUNTIME_CONFIG['max_password_length']+1
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length = 0, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            0)

                        ori_pos = read_only_depend.get_position()
                        if ori_pos < 0:

                            # Check -5, double append last char. Now check -4.
                            if (N + 1) < -ori_pos:
                                #Check -5, append 3 last chars, check -2.
                                ori_pos = ori_pos + N
                                depend = deepcopy(read_only_depend)
                                depend.set_position(ori_pos)
                                op_dep_list_1 = deepcopy(one_dep_list)
                                op_dep_list_1.prepend_dependency(
                                    deepcopy(depend_length_op_upper))
                                op_dep_list_1.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                op_dep_list_1.prepend_dependency(depend)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_1)

                            # Just check the last one.
                            else:
                                ori_pos = -1
                                depend = deepcopy(read_only_depend)
                                depend.set_position(ori_pos)
                                op_dep_list_2 = deepcopy(one_dep_list)
                                op_dep_list_2.prepend_dependency(
                                    deepcopy(depend_length_op_upper))
                                op_dep_list_2.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                op_dep_list_2.prepend_dependency(depend)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_2)

                        # ori_pos >= 0
                        else:
                            #If Length > ori_pos, doesn't matter
                            depend = deepcopy(read_only_depend)
                            depend_length_no_op_because_long_word = RejectUnlessGreaterThanLength(
                                ori_pos)
                            op_dep_list_3 = deepcopy(one_dep_list)
                            op_dep_list_3.prepend_dependency(
                                deepcopy(depend_length_op_upper))
                            op_dep_list_3.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            op_dep_list_3.prepend_dependency(depend)
                            op_dep_list_3.prepend_dependency(
                                depend_length_no_op_because_long_word)
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list_3)

                            #If Length < ori_pos + 1 and Length > ori_pos + 1 - N - 1, Means the -1 one.
                            depend = deepcopy(read_only_depend)
                            depend_length_op_max_length = RejectUnlessLessThanLength(
                                ori_pos + 1)
                            depend_length_op_min_length = RejectUnlessGreaterThanLength(
                                ori_pos -
                                N)  #You can write this because added >0 below
                            depend.set_position(-1)
                            op_dep_list_4 = deepcopy(one_dep_list)
                            op_dep_list_4.prepend_dependency(
                                deepcopy(depend_length_op_upper))
                            op_dep_list_4.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            op_dep_list_4.prepend_dependency(depend)
                            op_dep_list_4.prepend_dependency(
                                depend_length_op_max_length)
                            op_dep_list_4.prepend_dependency(
                                depend_length_op_min_length)
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list_4)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length = 0, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            0)

                        # Reduce the rejection length
                        depend = deepcopy(read_only_depend)
                        depend.set_len(depend.get_len() - N)
                        op_dep_list = deepcopy(one_dep_list)
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_upper))
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_lower))
                        op_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(op_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length = 0, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            0)

                        # Reduce the rejection length
                        depend = deepcopy(read_only_depend)
                        depend.set_len(depend.get_len() - N)
                        op_dep_list = deepcopy(one_dep_list)
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_upper))
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_lower))
                        op_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(op_dep_list)

                    # from_to_contains exactly
                    elif read_only_depend.dependency_type == 4:
                        # no op
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(depend_length_no_op))
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # no op
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(depend_length_no_op_greater))
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        if from_idx >= 0:
                            # length < to_idx
                            for input_len in range(max(to_idx - N, 1), to_idx):
                                if from_idx >= input_len - 1:  # all from last char

                                    # case 1: last char in, and number equals to-from.
                                    if number == to_idx - from_idx:
                                        dep_list_case_1 = deepcopy(one_dep_list)
                                        dep_list_case_1.prepend_dependency(
                                            RejectUnlessCharInPosition(
                                                chars, -1))
                                        dep_list_case_1.prepend_dependency(
                                            RejectUnlessLessThanLength(
                                                input_len + 1))
                                        dep_list_case_1.prepend_dependency(
                                            RejectUnlessGreaterThanLength(
                                                input_len - 1))
                                        save_split_dep_lists.append_dependency_list(
                                            dep_list_case_1)

                                    # case 2: last char in, and number not equals, rejected.

                                    # case 3: last char not in, and number not equals 0
                                    if number == 0:
                                        dep_list_case_2 = deepcopy(one_dep_list)
                                        dep_list_case_2.prepend_dependency(
                                            RejectUnlessCharInPosition(
                                                set(Dicts.classes['z']) - chars,
                                                -1))
                                        dep_list_case_2.prepend_dependency(
                                            RejectUnlessLessThanLength(
                                                input_len + 1))
                                        dep_list_case_2.prepend_dependency(
                                            RejectUnlessGreaterThanLength(
                                                input_len - 1))
                                        save_split_dep_lists.append_dependency_list(
                                            dep_list_case_2)

                                    # case 4: last char not in, and number > 0, rejected

                                else:  #[from_idx, input_len-1) are others; [input_len-1, to_idx) are last char
                                    # case1: last char in chars.
                                    if read_only_depend.dependency_type == 4:
                                        tmp_dep = RejectUnlessFromToContainsExactlyNumberOfChars(
                                            from_idx, input_len - 1,
                                            number - (to_idx - input_len + 1),
                                            chars)
                                    else:
                                        tmp_dep = RejectUnlessFromToContainsAtLeastNumberOfChars(
                                            from_idx, input_len - 1,
                                            number - (to_idx - input_len + 1),
                                            chars)

                                    dep_list_case_1 = deepcopy(one_dep_list)
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, -1))
                                    dep_list_case_1.prepend_dependency(tmp_dep)
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_1)

                                    # case2: last char not in chars.
                                    if read_only_depend.dependency_type == 4:
                                        tmp_dep = RejectUnlessFromToContainsExactlyNumberOfChars(
                                            from_idx, input_len - 1, number,
                                            chars)
                                    else:
                                        tmp_dep = RejectUnlessFromToContainsAtLeastNumberOfChars(
                                            from_idx, input_len - 1, number,
                                            chars)

                                    dep_list_case_2 = deepcopy(one_dep_list)
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars,
                                            -1))
                                    dep_list_case_2.prepend_dependency(tmp_dep)
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_2)

                            # length >= to_idx, doesn't matter
                            dep_list_case_1 = deepcopy(one_dep_list)
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(to_idx - 1))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(0))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessLessThanLength(
                                    RUNTIME_CONFIG['max_password_length'] - N +
                                    1))
                            dep_list_case_1.prepend_dependency(read_only_depend)
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1)

                        else:
                            if N <= -to_idx:  #doesn't matter
                                from_idx += N
                                to_idx += N

                                op_dep_list = deepcopy(one_dep_list)
                                tmp_dep = read_only_depend.make_new(
                                    from_idx, to_idx, number, chars)
                                op_dep_list.prepend_dependency(tmp_dep)
                                op_dep_list.prepend_dependency(
                                    depend_length_op_lower)
                                op_dep_list.prepend_dependency(
                                    depend_length_op_upper)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                            else:
                                # [-N, to_idx) are all last char's dups
                                # [from_idx, -N) are others
                                if from_idx < -N:
                                    # case1: last char in chars.
                                    tmp_dep = read_only_depend.make_new(
                                        from_idx + N, 0, number - to_idx - N,
                                        chars)

                                    dep_list_case_1 = deepcopy(one_dep_list)
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, -1))
                                    dep_list_case_1.prepend_dependency(tmp_dep)
                                    dep_list_case_1.prepend_dependency(
                                        depend_length_op_lower)
                                    dep_list_case_1.prepend_dependency(
                                        depend_length_op_upper)
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_1)

                                    # case2: first char not in chars.
                                    tmp_dep = read_only_depend.make_new(
                                        from_idx + N, 0, number, chars)

                                    dep_list_case_2 = deepcopy(one_dep_list)
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars,
                                            -1))
                                    dep_list_case_2.prepend_dependency(tmp_dep)
                                    dep_list_case_2.prepend_dependency(
                                        depend_length_op_lower)
                                    dep_list_case_2.prepend_dependency(
                                        depend_length_op_upper)
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_2)

                                else:  # all first char's dup
                                    tmp_dep = deepcopy(read_only_depend)
                                    tmp_dep.set_number(number -
                                                       (to_idx - from_idx))

                                    dep_list_case_1 = deepcopy(one_dep_list)
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, -1))
                                    dep_list_case_1.prepend_dependency(tmp_dep)
                                    dep_list_case_1.prepend_dependency(
                                        depend_length_op_lower)
                                    dep_list_case_1.prepend_dependency(
                                        depend_length_op_upper)
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_1)

                    # from_to_contains at least
                    elif read_only_depend.dependency_type == 5:
                        # no op
                        depend_length_no_op = RejectUnlessLessThanLength(1)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(depend_length_no_op))
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # no op
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(depend_length_no_op_greater))
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        if from_idx >= 0:
                            # length < to_idx
                            for input_len in range(max(to_idx - N, 1), to_idx):
                                if from_idx >= input_len - 1:  # all from last char
                                    # case 1: last char in
                                    dep_list_case_1 = deepcopy(one_dep_list)
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, -1))
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_1)
                                    # case 2: rejected

                                else:  #[from_idx, input_len-1) are others; [input_len-1, to_idx) are last char
                                    # case1: last char in chars.
                                    if read_only_depend.dependency_type == 4:
                                        tmp_dep = RejectUnlessFromToContainsExactlyNumberOfChars(
                                            from_idx, input_len - 1,
                                            number - (to_idx - input_len + 1),
                                            chars)
                                    else:
                                        tmp_dep = RejectUnlessFromToContainsAtLeastNumberOfChars(
                                            from_idx, input_len - 1,
                                            number - (to_idx - input_len + 1),
                                            chars)

                                    dep_list_case_1 = deepcopy(one_dep_list)
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, -1))
                                    dep_list_case_1.prepend_dependency(tmp_dep)
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_1)

                                    # case2: last char not in chars.
                                    if read_only_depend.dependency_type == 4:
                                        tmp_dep = RejectUnlessFromToContainsExactlyNumberOfChars(
                                            from_idx, input_len - 1, number,
                                            chars)
                                    else:
                                        tmp_dep = RejectUnlessFromToContainsAtLeastNumberOfChars(
                                            from_idx, input_len - 1, number,
                                            chars)

                                    dep_list_case_2 = deepcopy(one_dep_list)
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars,
                                            -1))
                                    dep_list_case_2.prepend_dependency(tmp_dep)
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_2)

                            # length >= to_idx, doesn't matter
                            dep_list_case_1 = deepcopy(one_dep_list)
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(to_idx - 1))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(0))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessLessThanLength(
                                    RUNTIME_CONFIG['max_password_length'] - N +
                                    1))
                            dep_list_case_1.prepend_dependency(read_only_depend)
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1)

                        else:
                            if N <= -to_idx:  #doesn't matter
                                from_idx += N
                                to_idx += N

                                op_dep_list = deepcopy(one_dep_list)
                                tmp_dep = read_only_depend.make_new(
                                    from_idx, to_idx, number, chars)
                                op_dep_list.prepend_dependency(tmp_dep)
                                op_dep_list.prepend_dependency(
                                    depend_length_op_lower)
                                op_dep_list.prepend_dependency(
                                    depend_length_op_upper)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                            else:
                                # [-N, to_idx) are all last char's dups
                                # [from_idx, -N) are others
                                if from_idx < -N:
                                    # case1: last char in chars.
                                    tmp_dep = read_only_depend.make_new(
                                        from_idx + N, 0, number - to_idx - N,
                                        chars)

                                    dep_list_case_1 = deepcopy(one_dep_list)
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, -1))
                                    dep_list_case_1.prepend_dependency(tmp_dep)
                                    dep_list_case_1.prepend_dependency(
                                        depend_length_op_lower)
                                    dep_list_case_1.prepend_dependency(
                                        depend_length_op_upper)
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_1)

                                    # case2: first char not in chars.
                                    tmp_dep = read_only_depend.make_new(
                                        from_idx + N, 0, number, chars)

                                    dep_list_case_2 = deepcopy(one_dep_list)
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars,
                                            -1))
                                    dep_list_case_2.prepend_dependency(tmp_dep)
                                    dep_list_case_2.prepend_dependency(
                                        depend_length_op_lower)
                                    dep_list_case_2.prepend_dependency(
                                        depend_length_op_upper)
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_2)

                                else:  # all first char's dup
                                    tmp_dep = deepcopy(read_only_depend)
                                    tmp_dep.set_number(number -
                                                       (to_idx - from_idx))

                                    dep_list_case_1 = deepcopy(one_dep_list)
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, -1))
                                    dep_list_case_1.prepend_dependency(tmp_dep)
                                    dep_list_case_1.prepend_dependency(
                                        depend_length_op_lower)
                                    dep_list_case_1.prepend_dependency(
                                        depend_length_op_upper)
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_1)

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_L_N_command(subrule_dependency, rule):
        """ LN  Bitwise left shift char at position N

        Effects on Dependency:
            Depends on char at position N

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """

        def get_dest_set(ori_set):
            dest_set = set()

            for x in ori_set:
                #Remove not valid
                if ord(x) % 2 == 1:
                    continue

                val_1 = ord(x) >> 1
                val_2 = (ord(x) + 256) >> 1
                dest_set.add(chr(val_1))
                dest_set.add(chr(val_2))

            return dest_set

        ret_val = SubruleDependency(subrule_dependency)

        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Countable")

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        # Here notice that if just toggle a set of chars, the result could still
                        # be in the set. Toggle /?a still equals /?a
                        # Two situations: Char at place N equals and char at place N not equals
                        # No memorization involved.
                        if N >= 0:
                            # T1 /a
                            # T4 /D
                            # T3 /=
                            # T3 /?a
                            # T3 /?d
                            # a fa1 cAbc16 t2fad1
                            # bvD e4hd134 vjeD34D bnmD14 vcx153ghessD
                            # =d vxw+24 vqa+ble24 fdslnwjrn+=-21 cxzfmw@*#&*-=

                            # case1: len < 4. Doesn't do anything
                            depend1 = RejectUnlessLessThanLength(N + 1)
                            depend1_1 = deepcopy(
                                read_only_depend)  #Doesn't affect the old
                            tmp_dependency_list1 = deepcopy(one_dep_list)
                            tmp_dependency_list1.prepend_dependency(depend1)
                            tmp_dependency_list1.prepend_dependency(depend1_1)
                            #print(tmp_dependency_list1)
                            # case2,3,4 combined can be understood by drawing Venn diagram.
                            # case2: len > 3. Char at 3 == A. -> add one a.
                            # corner case: len > 3. Char at 3 = ?d -> add one ?d but should still be 2.
                            ori_set = read_only_depend.get_chars()
                            dest_set = get_dest_set(
                                ori_set
                            )  #So that what's in dest_set is not in ori_set
                            #if what's in the dest set is also in ori_set. it doesn't affect the number
                            difference_set = dest_set.difference(ori_set)
                            depend2_1 = RejectUnlessGreaterThanLength(N)
                            depend2_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend2_3 = deepcopy(read_only_depend)
                            depend2_3.set_number(depend2_3.get_number() - 1)

                            tmp_dependency_list2 = deepcopy(one_dep_list)
                            tmp_dependency_list2.prepend_dependency(depend2_2)
                            tmp_dependency_list2.prepend_dependency(depend2_3)
                            #print(tmp_dependency_list2)

                            # case3: len > 3, Char at 3 != a/A. Doesn't Matter
                            complement_result = set(
                                x for x in set(Dicts.classes['z'])
                                if ((x not in ori_set and x not in dest_set) or
                                    (x in ori_set and x in dest_set)))
                            depend3_1 = RejectUnlessGreaterThanLength(N)
                            depend3_2 = RejectUnlessCharInPosition(
                                complement_result, N)
                            depend3_3 = deepcopy(read_only_depend)

                            tmp_dependency_list3 = deepcopy(one_dep_list)
                            tmp_dependency_list3.prepend_dependency(depend3_2)
                            tmp_dependency_list3.prepend_dependency(depend3_3)
                            #print(tmp_dependency_list3)
                            # case4: len > 3. Char at 3 == a. -> Delete one a. Need two in original.
                            ori_set = read_only_depend.get_chars()
                            dest_set = get_dest_set(ori_set)

                            # Toggle set (a,b,A)
                            # If char at 3 == A/a. Mean contains. Only use (a,b,A) - (a,B,A)
                            # Why? Because a,A still in the set. So you toggle that you get something still in the set.
                            # it is still satisfied.
                            difference_set = ori_set.difference(dest_set)

                            depend4_1 = RejectUnlessGreaterThanLength(N)
                            depend4_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend4_3 = deepcopy(read_only_depend)
                            depend4_3.set_number(depend4_3.get_number() + 1)

                            tmp_dependency_list4 = deepcopy(one_dep_list)
                            tmp_dependency_list4.prepend_dependency(depend4_2)
                            tmp_dependency_list4.prepend_dependency(depend4_3)
                            #print(tmp_dependency_list4)

                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list1)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list2)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list3)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list4)

                        else:  # N < 0
                            #Tm /b
                            #Tm /E
                            #Tm /)
                            #Tm /?d
                            #Tm /?a
                            #vcxB qfb w212fE dasve fdsdf) sdfsf0 vxcsf1 bkon qjroi0fn aijs*

                            #case1: >0, char at pos -1 A. Get an extra a.
                            ori_set = read_only_depend.get_chars()
                            dest_set = get_dest_set(ori_set)
                            difference_set = dest_set.difference(ori_set)
                            depend1_1 = RejectUnlessGreaterThanLength(-N - 1)
                            depend1_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend1_3 = deepcopy(read_only_depend)
                            depend1_3.set_number(depend1_3.get_number() - 1)

                            tmp_dependency_list1 = deepcopy(one_dep_list)
                            tmp_dependency_list1.prepend_dependency(depend1_1)
                            tmp_dependency_list1.prepend_dependency(depend1_2)
                            tmp_dependency_list1.prepend_dependency(depend1_3)

                            #case2: >0, char at pos -1 not equal a/A. Doesnt matter
                            complement_result = set(
                                x for x in set(Dicts.classes['z'])
                                if (x not in ori_set and x not in dest_set) or
                                (x in ori_set and x in dest_set))
                            depend2_1 = RejectUnlessGreaterThanLength(-N - 1)
                            depend2_2 = RejectUnlessCharInPosition(
                                complement_result, N)
                            depend2_3 = deepcopy(read_only_depend)

                            tmp_dependency_list2 = deepcopy(one_dep_list)
                            tmp_dependency_list2.prepend_dependency(depend2_1)
                            tmp_dependency_list2.prepend_dependency(depend2_2)
                            tmp_dependency_list2.prepend_dependency(depend2_3)

                            #case3: >0, char at pos -1 a. Need 2
                            ori_set = read_only_depend.get_chars()
                            dest_set = dest_set = get_dest_set(ori_set)

                            # Toggle set (a,b,A)
                            # If char at 3 == A/a. Mean contains. Only use (a,b,A) - (a,B,A)
                            # Why? Because a,A still in the set. So you toggle that you get something still in the set.
                            # it is still satisfied.
                            difference_set = ori_set.difference(dest_set)
                            depend3_1 = RejectUnlessGreaterThanLength(-N - 1)
                            depend3_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend3_3 = deepcopy(read_only_depend)
                            depend3_3.set_number(depend3_3.get_number() + 1)

                            tmp_dependency_list3 = deepcopy(one_dep_list)
                            tmp_dependency_list3.prepend_dependency(depend3_1)
                            tmp_dependency_list3.prepend_dependency(depend3_2)
                            tmp_dependency_list3.prepend_dependency(depend3_3)

                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list1)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list2)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list3)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:

                        #Check Char in position
                        check_pos = read_only_depend.get_position()

                        if N >= 0:
                            # T4 =1a
                            # T4 =1?a
                            # T4 =4D
                            # T4 =4?a
                            # T0 (E
                            # T0 =0?a
                            # T0 =2a
                            # T3 (B
                            # T3 =3?a
                            # T3 =3f
                            # T2 (?a
                            # T2 =2-
                            # T4 )?a
                            # T4 )f
                            # T3 )a
                            # T3 )?a
                            # xg-1dfa hl=dfa21 cmaF214 skrf1243dz eghqFDZ21 Efds)(5)242df xbdad329Z1 Fiekd21^.
                            # zcsqF xmrqf czsA x03a xmewi fs3v fds8 vczn2 awo@

                            # No matter what position is toggled, to satisfy char at position, length has to be greater than abs(check_pos)
                            if check_pos >= 0:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    abs(check_pos))
                            else:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    -check_pos - 1)

                            # No matter where the rejection rule checks, if T9. Then introduce >9 and <=9
                            # T9, word_len <= 9
                            depend0_0 = RejectUnlessLessThanLength(
                                N + 1)  # The length from N
                            depend0_1 = deepcopy(read_only_depend)
                            tmp_dependency_list0 = deepcopy(one_dep_list)
                            tmp_dependency_list0.prepend_dependency(depend0_0)
                            tmp_dependency_list0.prepend_dependency(depend0_1)
                            tmp_dependency_list0.prepend_dependency(
                                deepcopy(depend_len_from_check_pos))
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list0)

                            # T9, word_len >9
                            depend_len_from_N = RejectUnlessGreaterThanLength(N)
                            if check_pos >= 0:  #If check char at positive position

                                if check_pos != N:  # T9, (a
                                    #Toggle position != char at positition.
                                    #Doesn't matter

                                    depend1_0 = deepcopy(read_only_depend)

                                    tmp_dependency_list1 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list1.prepend_dependency(
                                        depend1_0)
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list1)

                                else:  #T9, =9a
                                    #Toggle position = char at positition.
                                    #Literally toggle the chars here.

                                    ori_set = read_only_depend.get_chars()
                                    dest_set = get_dest_set(ori_set)
                                    depend2_0 = deepcopy(read_only_depend)
                                    depend2_0.set_chars(dest_set)

                                    tmp_dependency_list2 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list2.prepend_dependency(
                                        depend2_0)
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list2)

                            else:  # T9, )a. Only consider >= 10

                                # depend_len_from_N >= 10
                                # depend_len_from_check_pos >= 1
                                # Only when len ==
                                word_len = max(N + 1, -check_pos)
                                while True:
                                    if word_len < N - check_pos:
                                        #T9, )a. wordlen = 5
                                        #Doesn't matter

                                        depend1_0 = RejectUnlessLessThanLength(
                                            word_len + 1)
                                        depend1_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend1_2 = deepcopy(read_only_depend)

                                        tmp_dependency_list1 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_0)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_1)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list1)

                                    elif word_len == N - check_pos:  #Affect
                                        #If equals.
                                        #T9, )a. wordlen = 10
                                        #Then toggle the char

                                        depend2_0 = RejectUnlessLessThanLength(
                                            word_len + 1)
                                        depend2_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend2_2 = deepcopy(read_only_depend)
                                        ori_set = read_only_depend.get_chars()
                                        dest_set = get_dest_set(ori_set)
                                        depend2_2.set_chars(dest_set)

                                        tmp_dependency_list2 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_0)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_1)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list2)

                                    else:
                                        #Else
                                        #T9, )a. wordlen > 10
                                        #Doesnt matter
                                        depend3_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend3_2 = deepcopy(read_only_depend)

                                        tmp_dependency_list3 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list3.prepend_dependency(
                                            depend3_1)
                                        tmp_dependency_list3.prepend_dependency(
                                            depend3_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list3)
                                        break
                                    word_len += 1

                        else:  # N < 0

                            #Tm =0a
                            #Tm =0?a
                            #Tm =3d
                            #Tm =3?a
                            #Tm )a
                            #Tm )?a
                            #Tm )?d
                            #Tm )?l
                            #A X F f xbdD czdd asdfewfdDd xcmzafo xzD zmA feqa XV3 ZX* dsfmF vmce

                            # No matter what position is toggled, to satisfy char at position, length has to be greater than abs(check_pos)
                            if check_pos >= 0:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    abs(check_pos))
                            else:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    -check_pos - 1)

                            depend_len_from_N = RejectUnlessGreaterThanLength(
                                -N - 1)

                            if check_pos >= 0:  # Tm, (a

                                #Enumerate word length
                                word_len = max(-N, check_pos + 1)
                                while True:
                                    if word_len < check_pos - N:
                                        #Tm, =2a. word len 1
                                        #Doesnt matter

                                        depend1_0 = RejectUnlessLessThanLength(
                                            word_len + 1)
                                        depend1_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend1_2 = deepcopy(read_only_depend)

                                        tmp_dependency_list1 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_0)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_1)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list1)

                                    elif word_len == check_pos - N:  #Affect
                                        #Tm, =2a, wordlen = 3
                                        #Affect, toggle.

                                        depend2_0 = RejectUnlessLessThanLength(
                                            word_len + 1)
                                        depend2_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend2_2 = deepcopy(read_only_depend)
                                        ori_set = read_only_depend.get_chars()
                                        dest_set = get_dest_set(ori_set)
                                        depend2_2.set_chars(dest_set)

                                        tmp_dependency_list2 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_0)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_1)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list2)

                                    else:
                                        #Tm, =2a, wordlen > 3
                                        #Doesnt matter
                                        depend3_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend3_2 = deepcopy(read_only_depend)

                                        tmp_dependency_list3 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list3.prepend_dependency(
                                            depend3_1)
                                        tmp_dependency_list3.prepend_dependency(
                                            depend3_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list3)
                                        break
                                    word_len += 1

                            else:  #check_pos <0, N < 0

                                if check_pos != N:  # Tm, =-2a
                                    #If the Tm, =-2a,
                                    #Doesnt affect
                                    depend1_0 = deepcopy(read_only_depend)

                                    tmp_dependency_list1 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list1.prepend_dependency(
                                        depend1_0)
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list1)

                                else:  #Tm, )a
                                    #Affect, toggle

                                    ori_set = read_only_depend.get_chars()
                                    dest_set = get_dest_set(ori_set)
                                    depend2_0 = deepcopy(read_only_depend)
                                    depend2_0.set_chars(dest_set)

                                    tmp_dependency_list2 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list2.prepend_dependency(
                                        depend2_0)
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list2)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend = deepcopy(read_only_depend)

                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend = deepcopy(read_only_depend)

                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        # case1: len < 4. Doesn't do anything
                        depend1 = RejectUnlessLessThanLength(N + 1)
                        depend1_1 = deepcopy(
                            read_only_depend)  #Doesn't affect the old
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(depend1)
                        no_op_dep_list.prepend_dependency(depend1_1)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N)

                        if from_idx >= 0:
                            # Case1: N in [from, to)
                            if to_idx > N >= from_idx:
                                toggled_chars = get_dest_set(chars)

                                # case1.1: toggled_chars not in chars.
                                toggled_chars_not_in = toggled_chars - chars
                                dep_list_case_2 = deepcopy(one_dep_list)
                                dep_list_case_2.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        toggled_chars_not_in, N))
                                dep_list_case_2.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number - 1, chars))
                                dep_list_case_2.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_2)

                                # case1.3: (set(Dicts.classes['z']) - toggled_chars) & chars, +1. Say T1, %a. If T1 = a, add 1 to number
                                chars_not_in_toggled = chars - toggled_chars
                                dep_list_case_3 = deepcopy(one_dep_list)
                                dep_list_case_3.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        chars_not_in_toggled, N))
                                dep_list_case_3.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number + 1, chars))
                                dep_list_case_3.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_3)

                                # case1.2: (set(Dicts.classes['z']) - toggled_chars_not_in) - chars, doesn't change
                                dep_list_case_1 = deepcopy(one_dep_list)
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) -
                                        chars_not_in_toggled -
                                        toggled_chars_not_in, N))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                            # Case2: N not in [from, to)
                            else:
                                one_dep_list.prepend_dependency(
                                    read_only_depend)
                                one_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                        else:
                            # Case1: N in [from, to), where N - from_idx >= len > N - to_idx
                            toggled_chars = get_dest_set(chars)

                            # case1.1: toggled_chars not in chars.
                            toggled_chars_not_in = toggled_chars - chars
                            dep_list_case_2 = deepcopy(one_dep_list)
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    toggled_chars_not_in, N))
                            dep_list_case_2.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number - 1, chars))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_2.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_2)

                            # case1.3: (set(Dicts.classes['z']) - toggled_chars) & chars, +1. Say T1, %a. If T1 = a, add 1 to number
                            chars_not_in_toggled = chars - toggled_chars
                            dep_list_case_3 = deepcopy(one_dep_list)
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    chars_not_in_toggled, N))
                            dep_list_case_3.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number + 1, chars))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_3.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_3)

                            # case1.2: (set(Dicts.classes['z']) - toggled_chars_not_in) - chars, doesn't change
                            dep_list_case_1 = deepcopy(one_dep_list)
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) -
                                    chars_not_in_toggled - toggled_chars_not_in,
                                    N))
                            dep_list_case_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_1.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1)

                            # case1.3 & 1.4 doesn't matter
                            dep_list_case_4 = deepcopy(one_dep_list)
                            dep_list_case_4.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_4.prepend_dependency(
                                RejectUnlessLessThanLength(N - to_idx + 1))
                            dep_list_case_4.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_4)

                            dep_list_case_5 = deepcopy(one_dep_list)
                            dep_list_case_5.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_5.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - from_idx))
                            dep_list_case_5.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_5)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_R_N_command(subrule_dependency, rule):
        """ RN  Bitwise right shift char at position N

        Effects on Dependency:
            depends on char at N

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """

        def get_dest_set(ori_set):

            #Remove not valid
            val = set(ord(x) for x in ori_set if ord(x) <= 127)

            char_set = set(chr(x * 2) for x in val) | set(
                chr(x * 2 + 1) for x in val)

            return char_set

        ret_val = SubruleDependency(subrule_dependency)

        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Countable")

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        # Here notice that if just toggle a set of chars, the result could still
                        # be in the set. Toggle /?a still equals /?a
                        # Two situations: Char at place N equals and char at place N not equals
                        # No memorization involved.
                        if N >= 0:
                            # T1 /a
                            # T4 /D
                            # T3 /=
                            # T3 /?a
                            # T3 /?d
                            # a fa1 cAbc16 t2fad1
                            # bvD e4hd134 vjeD34D bnmD14 vcx153ghessD
                            # =d vxw+24 vqa+ble24 fdslnwjrn+=-21 cxzfmw@*#&*-=

                            # case1: len < 4. Doesn't do anything
                            depend1 = RejectUnlessLessThanLength(N + 1)
                            depend1_1 = deepcopy(
                                read_only_depend)  #Doesn't affect the old
                            tmp_dependency_list1 = deepcopy(one_dep_list)
                            tmp_dependency_list1.prepend_dependency(depend1)
                            tmp_dependency_list1.prepend_dependency(depend1_1)

                            # case2,3,4 combined can be understood by drawing Venn diagram.
                            # case2: len > 3. Char at 3 == A. -> add one a.
                            # corner case: len > 3. Char at 3 = ?d -> add one ?d but should still be 2.
                            ori_set = read_only_depend.get_chars()
                            dest_set = get_dest_set(
                                ori_set
                            )  #So that what's in dest_set is not in ori_set
                            #if what's in the dest set is also in ori_set. it doesn't affect the number
                            difference_set = dest_set.difference(ori_set)
                            depend2_1 = RejectUnlessGreaterThanLength(N)
                            depend2_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend2_3 = deepcopy(read_only_depend)
                            depend2_3.set_number(depend2_3.get_number() - 1)

                            tmp_dependency_list2 = deepcopy(one_dep_list)
                            tmp_dependency_list2.prepend_dependency(depend2_2)
                            tmp_dependency_list2.prepend_dependency(depend2_3)

                            # case3: len > 3, Char at 3 != a/A. Doesn't Matter
                            complement_result = set(
                                x for x in set(Dicts.classes['z'])
                                if (x not in ori_set and x not in dest_set) or
                                (x in ori_set and x in dest_set))
                            depend3_1 = RejectUnlessGreaterThanLength(N)
                            depend3_2 = RejectUnlessCharInPosition(
                                complement_result, N)
                            depend3_3 = deepcopy(read_only_depend)

                            tmp_dependency_list3 = deepcopy(one_dep_list)
                            tmp_dependency_list3.prepend_dependency(depend3_2)
                            tmp_dependency_list3.prepend_dependency(depend3_3)

                            # case4: len > 3. Char at 3 == a. -> Delete one a. Need two in original.
                            ori_set = read_only_depend.get_chars()
                            dest_set = get_dest_set(ori_set)

                            # Toggle set (a,b,A)
                            # If char at 3 == A/a. Mean contains. Only use (a,b,A) - (a,B,A)
                            # Why? Because a,A still in the set. So you toggle that you get something still in the set.
                            # it is still satisfied.
                            difference_set = ori_set.difference(dest_set)

                            depend4_1 = RejectUnlessGreaterThanLength(N)
                            depend4_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend4_3 = deepcopy(read_only_depend)
                            depend4_3.set_number(depend4_3.get_number() + 1)

                            tmp_dependency_list4 = deepcopy(one_dep_list)
                            tmp_dependency_list4.prepend_dependency(depend4_2)
                            tmp_dependency_list4.prepend_dependency(depend4_3)

                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list1)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list2)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list3)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list4)

                        else:  # N < 0
                            #Tm /b
                            #Tm /E
                            #Tm /)
                            #Tm /?d
                            #Tm /?a
                            #vcxB qfb w212fE dasve fdsdf) sdfsf0 vxcsf1 bkon qjroi0fn aijs*

                            #case1: >0, char at pos -1 A. Get an extra a.
                            ori_set = read_only_depend.get_chars()
                            dest_set = get_dest_set(ori_set)
                            difference_set = dest_set.difference(ori_set)
                            depend1_1 = RejectUnlessGreaterThanLength(-N - 1)
                            depend1_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend1_3 = deepcopy(read_only_depend)
                            depend1_3.set_number(depend1_3.get_number() - 1)

                            tmp_dependency_list1 = deepcopy(one_dep_list)
                            tmp_dependency_list1.prepend_dependency(depend1_1)
                            tmp_dependency_list1.prepend_dependency(depend1_2)
                            tmp_dependency_list1.prepend_dependency(depend1_3)

                            #case2: >0, char at pos -1 not equal a/A. Doesnt matter
                            complement_result = set(
                                x for x in set(Dicts.classes['z'])
                                if (x not in ori_set and x not in dest_set) or
                                (x in ori_set and x in dest_set))
                            depend2_1 = RejectUnlessGreaterThanLength(-N - 1)
                            depend2_2 = RejectUnlessCharInPosition(
                                complement_result, N)
                            depend2_3 = deepcopy(read_only_depend)

                            tmp_dependency_list2 = deepcopy(one_dep_list)
                            tmp_dependency_list2.prepend_dependency(depend2_1)
                            tmp_dependency_list2.prepend_dependency(depend2_2)
                            tmp_dependency_list2.prepend_dependency(depend2_3)

                            #case3: >0, char at pos -1 a. Need 2
                            ori_set = read_only_depend.get_chars()
                            dest_set = dest_set = get_dest_set(ori_set)

                            # Toggle set (a,b,A)
                            # If char at 3 == A/a. Mean contains. Only use (a,b,A) - (a,B,A)
                            # Why? Because a,A still in the set. So you toggle that you get something still in the set.
                            # it is still satisfied.
                            difference_set = ori_set.difference(dest_set)
                            depend3_1 = RejectUnlessGreaterThanLength(-N - 1)
                            depend3_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend3_3 = deepcopy(read_only_depend)
                            depend3_3.set_number(depend3_3.get_number() + 1)

                            tmp_dependency_list3 = deepcopy(one_dep_list)
                            tmp_dependency_list3.prepend_dependency(depend3_1)
                            tmp_dependency_list3.prepend_dependency(depend3_2)
                            tmp_dependency_list3.prepend_dependency(depend3_3)

                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list1)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list2)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list3)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:

                        #Check Char in position
                        check_pos = read_only_depend.get_position()

                        if N >= 0:
                            # T4 =1a
                            # T4 =1?a
                            # T4 =4D
                            # T4 =4?a
                            # T0 (E
                            # T0 =0?a
                            # T0 =2a
                            # T3 (B
                            # T3 =3?a
                            # T3 =3f
                            # T2 (?a
                            # T2 =2-
                            # T4 )?a
                            # T4 )f
                            # T3 )a
                            # T3 )?a
                            # xg-1dfa hl=dfa21 cmaF214 skrf1243dz eghqFDZ21 Efds)(5)242df xbdad329Z1 Fiekd21^.
                            # zcsqF xmrqf czsA x03a xmewi fs3v fds8 vczn2 awo@

                            # No matter what position is toggled, to satisfy char at position, length has to be greater than abs(check_pos)
                            if check_pos >= 0:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    abs(check_pos))
                            else:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    -check_pos - 1)

                            # No matter where the rejection rule checks, if T9. Then introduce >9 and <=9
                            # T9, word_len <= 9
                            depend0_0 = RejectUnlessLessThanLength(
                                N + 1)  # The length from N
                            depend0_1 = deepcopy(read_only_depend)
                            tmp_dependency_list0 = deepcopy(one_dep_list)
                            tmp_dependency_list0.prepend_dependency(depend0_0)
                            tmp_dependency_list0.prepend_dependency(depend0_1)
                            tmp_dependency_list0.prepend_dependency(
                                deepcopy(depend_len_from_check_pos))
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list0)

                            # T9, word_len >9
                            depend_len_from_N = RejectUnlessGreaterThanLength(N)
                            if check_pos >= 0:  #If check char at positive position

                                if check_pos != N:  # T9, (a
                                    #Toggle position != char at positition.
                                    #Doesn't matter

                                    depend1_0 = deepcopy(read_only_depend)

                                    tmp_dependency_list1 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list1.prepend_dependency(
                                        depend1_0)
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list1)

                                else:  #T9, =9a
                                    #Toggle position = char at positition.
                                    #Literally toggle the chars here.

                                    ori_set = read_only_depend.get_chars()
                                    dest_set = get_dest_set(ori_set)
                                    depend2_0 = deepcopy(read_only_depend)
                                    depend2_0.set_chars(dest_set)

                                    tmp_dependency_list2 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list2.prepend_dependency(
                                        depend2_0)
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list2)

                            else:  # T9, )a. Only consider >= 10

                                # depend_len_from_N >= 10
                                # depend_len_from_check_pos >= 1
                                # Only when len ==
                                word_len = max(N + 1, -check_pos)
                                while True:
                                    if word_len < N - check_pos:
                                        #T9, )a. wordlen = 5
                                        #Doesn't matter

                                        depend1_0 = RejectUnlessLessThanLength(
                                            word_len + 1)
                                        depend1_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend1_2 = deepcopy(read_only_depend)

                                        tmp_dependency_list1 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_0)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_1)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list1)

                                    elif word_len == N - check_pos:  #Affect
                                        #If equals.
                                        #T9, )a. wordlen = 10
                                        #Then toggle the char

                                        depend2_0 = RejectUnlessLessThanLength(
                                            word_len + 1)
                                        depend2_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend2_2 = deepcopy(read_only_depend)
                                        ori_set = read_only_depend.get_chars()
                                        dest_set = get_dest_set(ori_set)
                                        depend2_2.set_chars(dest_set)

                                        tmp_dependency_list2 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_0)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_1)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list2)

                                    else:
                                        #Else
                                        #T9, )a. wordlen > 10
                                        #Doesnt matter
                                        depend3_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend3_2 = deepcopy(read_only_depend)

                                        tmp_dependency_list3 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list3.prepend_dependency(
                                            depend3_1)
                                        tmp_dependency_list3.prepend_dependency(
                                            depend3_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list3)
                                        break
                                    word_len += 1

                        else:  # N < 0

                            #Tm =0a
                            #Tm =0?a
                            #Tm =3d
                            #Tm =3?a
                            #Tm )a
                            #Tm )?a
                            #Tm )?d
                            #Tm )?l
                            #A X F f xbdD czdd asdfewfdDd xcmzafo xzD zmA feqa XV3 ZX* dsfmF vmce

                            # No matter what position is toggled, to satisfy char at position, length has to be greater than abs(check_pos)
                            if check_pos >= 0:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    abs(check_pos))
                            else:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    -check_pos - 1)

                            depend_len_from_N = RejectUnlessGreaterThanLength(
                                -N - 1)

                            if check_pos >= 0:  # Tm, (a

                                #Enumerate word length
                                word_len = max(-N, check_pos + 1)
                                while True:
                                    if word_len < check_pos - N:
                                        #Tm, =2a. word len 1
                                        #Doesnt matter

                                        depend1_0 = RejectUnlessLessThanLength(
                                            word_len + 1)
                                        depend1_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend1_2 = deepcopy(read_only_depend)

                                        tmp_dependency_list1 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_0)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_1)
                                        tmp_dependency_list1.prepend_dependency(
                                            depend1_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list1)

                                    elif word_len == check_pos - N:  #Affect
                                        #Tm, =2a, wordlen = 3
                                        #Affect, toggle.

                                        depend2_0 = RejectUnlessLessThanLength(
                                            word_len + 1)
                                        depend2_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend2_2 = deepcopy(read_only_depend)
                                        ori_set = read_only_depend.get_chars()
                                        dest_set = get_dest_set(ori_set)
                                        depend2_2.set_chars(dest_set)

                                        tmp_dependency_list2 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_0)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_1)
                                        tmp_dependency_list2.prepend_dependency(
                                            depend2_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list2)

                                    else:
                                        #Tm, =2a, wordlen > 3
                                        #Doesnt matter
                                        depend3_1 = RejectUnlessGreaterThanLength(
                                            word_len - 1)
                                        depend3_2 = deepcopy(read_only_depend)

                                        tmp_dependency_list3 = deepcopy(
                                            one_dep_list)
                                        tmp_dependency_list3.prepend_dependency(
                                            depend3_1)
                                        tmp_dependency_list3.prepend_dependency(
                                            depend3_2)
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dependency_list3)
                                        break
                                    word_len += 1

                            else:  #check_pos <0, N < 0

                                if check_pos != N:  # Tm, =-2a
                                    #If the Tm, =-2a,
                                    #Doesnt affect
                                    depend1_0 = deepcopy(read_only_depend)

                                    tmp_dependency_list1 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list1.prepend_dependency(
                                        depend1_0)
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list1)

                                else:  #Tm, )a
                                    #Affect, toggle

                                    ori_set = read_only_depend.get_chars()
                                    dest_set = get_dest_set(ori_set)
                                    depend2_0 = deepcopy(read_only_depend)
                                    depend2_0.set_chars(dest_set)

                                    tmp_dependency_list2 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list2.prepend_dependency(
                                        depend2_0)
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list2)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend = deepcopy(read_only_depend)

                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend = deepcopy(read_only_depend)

                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        # case1: len < 4. Doesn't do anything
                        depend1 = RejectUnlessLessThanLength(N + 1)
                        depend1_1 = deepcopy(
                            read_only_depend)  #Doesn't affect the old
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(depend1)
                        no_op_dep_list.prepend_dependency(depend1_1)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N)

                        if from_idx >= 0:
                            # Case1: N in [from, to)
                            if to_idx > N >= from_idx:
                                toggled_chars = get_dest_set(chars)

                                # case1.1: toggled_chars not in chars.
                                toggled_chars_not_in = toggled_chars - chars
                                dep_list_case_2 = deepcopy(one_dep_list)
                                dep_list_case_2.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        toggled_chars_not_in, N))
                                dep_list_case_2.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number - 1, chars))
                                dep_list_case_2.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_2)

                                # case1.3: (set(Dicts.classes['z']) - toggled_chars) & chars, +1. Say T1, %a. If T1 = a, add 1 to number
                                chars_not_in_toggled = chars - toggled_chars
                                dep_list_case_3 = deepcopy(one_dep_list)
                                dep_list_case_3.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        chars_not_in_toggled, N))
                                dep_list_case_3.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number + 1, chars))
                                dep_list_case_3.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_3)

                                # case1.2: (set(Dicts.classes['z']) - toggled_chars_not_in) - chars, doesn't change
                                dep_list_case_1 = deepcopy(one_dep_list)
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) -
                                        chars_not_in_toggled -
                                        toggled_chars_not_in, N))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                            # Case2: N not in [from, to)
                            else:
                                one_dep_list.prepend_dependency(
                                    read_only_depend)
                                one_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                        else:
                            # Case1: N in [from, to), where N - from_idx >= len > N - to_idx
                            toggled_chars = get_dest_set(chars)

                            # case1.1: toggled_chars not in chars.
                            toggled_chars_not_in = toggled_chars - chars
                            dep_list_case_2 = deepcopy(one_dep_list)
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    toggled_chars_not_in, N))
                            dep_list_case_2.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number - 1, chars))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_2.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_2)

                            # case1.3: (set(Dicts.classes['z']) - toggled_chars) & chars, +1. Say T1, %a. If T1 = a, add 1 to number
                            chars_not_in_toggled = chars - toggled_chars
                            dep_list_case_3 = deepcopy(one_dep_list)
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    chars_not_in_toggled, N))
                            dep_list_case_3.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number + 1, chars))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_3.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_3)

                            # case1.2: (set(Dicts.classes['z']) - toggled_chars_not_in) - chars, doesn't change
                            dep_list_case_1 = deepcopy(one_dep_list)
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) -
                                    chars_not_in_toggled - toggled_chars_not_in,
                                    N))
                            dep_list_case_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_1.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1)

                            # case1.3 & 1.4 doesn't matter
                            dep_list_case_4 = deepcopy(one_dep_list)
                            dep_list_case_4.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_4.prepend_dependency(
                                RejectUnlessLessThanLength(N - to_idx + 1))
                            dep_list_case_4.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_4)

                            dep_list_case_5 = deepcopy(one_dep_list)
                            dep_list_case_5.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_5.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - from_idx))
                            dep_list_case_5.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_5)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_plus_N_command(subrule_dependency, rule):
        """ +N  Increment char at position N by 1 ascii value

        Effects on Dependency:
            depends on char at N

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """

        def get_dest_set(ori_set):

            #Remove not valid
            return set(chr((ord(x) - 1 + 256) % 256) for x in ori_set)

        ret_val = SubruleDependency(subrule_dependency)

        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Countable")

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        # Here notice that if just toggle a set of chars, the result could still
                        # be in the set. Toggle /?a still equals /?a
                        # Two situations: Char at place N equals and char at place N not equals
                        # No memorization involved.
                        if N >= 0:
                            # T1 /a
                            # T4 /D
                            # T3 /=
                            # T3 /?a
                            # T3 /?d
                            # a fa1 cAbc16 t2fad1
                            # bvD e4hd134 vjeD34D bnmD14 vcx153ghessD
                            # =d vxw+24 vqa+ble24 fdslnwjrn+=-21 cxzfmw@*#&*-=

                            # case1: len < 4. Doesn't do anything
                            depend1 = RejectUnlessLessThanLength(N + 1)
                            depend1_1 = deepcopy(
                                read_only_depend)  #Doesn't affect the old
                            tmp_dependency_list1 = deepcopy(one_dep_list)
                            tmp_dependency_list1.prepend_dependency(depend1)
                            tmp_dependency_list1.prepend_dependency(depend1_1)

                            # case2,3,4 combined can be understood by drawing Venn diagram.
                            # case2: len > 3. Char at 3 == A. -> add one a.
                            # corner case: len > 3. Char at 3 = ?d -> add one ?d but should still be 2.
                            ori_set = read_only_depend.get_chars()
                            dest_set = get_dest_set(
                                ori_set
                            )  #So that what's in dest_set is not in ori_set
                            #if what's in the dest set is also in ori_set. it doesn't affect the number
                            difference_set = dest_set.difference(ori_set)
                            depend2_1 = RejectUnlessGreaterThanLength(N)
                            depend2_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend2_3 = deepcopy(read_only_depend)
                            depend2_3.set_number(depend2_3.get_number() - 1)

                            tmp_dependency_list2 = deepcopy(one_dep_list)
                            tmp_dependency_list2.prepend_dependency(depend2_2)
                            tmp_dependency_list2.prepend_dependency(depend2_3)

                            # case3: len > 3, Char at 3 != a/A. Doesn't Matter
                            complement_result = set(
                                x for x in set(Dicts.classes['z'])
                                if (x not in ori_set and x not in dest_set) or
                                (x in ori_set and x in dest_set))
                            depend3_1 = RejectUnlessGreaterThanLength(N)
                            depend3_2 = RejectUnlessCharInPosition(
                                complement_result, N)
                            depend3_3 = deepcopy(read_only_depend)

                            tmp_dependency_list3 = deepcopy(one_dep_list)
                            tmp_dependency_list3.prepend_dependency(depend3_2)
                            tmp_dependency_list3.prepend_dependency(depend3_3)

                            # case4: len > 3. Char at 3 == a. -> Delete one a. Need two in original.
                            ori_set = read_only_depend.get_chars()
                            dest_set = get_dest_set(ori_set)

                            # Toggle set (a,b,A)
                            # If char at 3 == A/a. Mean contains. Only use (a,b,A) - (a,B,A)
                            # Why? Because a,A still in the set. So you toggle that you get something still in the set.
                            # it is still satisfied.
                            difference_set = ori_set.difference(dest_set)

                            depend4_1 = RejectUnlessGreaterThanLength(N)
                            depend4_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend4_3 = deepcopy(read_only_depend)
                            depend4_3.set_number(depend4_3.get_number() + 1)

                            tmp_dependency_list4 = deepcopy(one_dep_list)
                            tmp_dependency_list4.prepend_dependency(depend4_2)
                            tmp_dependency_list4.prepend_dependency(depend4_3)

                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list1)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list2)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list3)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list4)

                        else:  # N < 0
                            #Tm /b
                            #Tm /E
                            #Tm /)
                            #Tm /?d
                            #Tm /?a
                            #vcxB qfb w212fE dasve fdsdf) sdfsf0 vxcsf1 bkon qjroi0fn aijs*

                            #case1: >0, char at pos -1 A. Get an extra a.
                            ori_set = read_only_depend.get_chars()
                            dest_set = get_dest_set(ori_set)
                            difference_set = dest_set.difference(ori_set)
                            depend1_1 = RejectUnlessGreaterThanLength(-N - 1)
                            depend1_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend1_3 = deepcopy(read_only_depend)
                            depend1_3.set_number(depend1_3.get_number() - 1)

                            tmp_dependency_list1 = deepcopy(one_dep_list)
                            tmp_dependency_list1.prepend_dependency(depend1_1)
                            tmp_dependency_list1.prepend_dependency(depend1_2)
                            tmp_dependency_list1.prepend_dependency(depend1_3)

                            #case2: >0, char at pos -1 not equal a/A. Doesnt matter
                            complement_result = set(
                                x for x in set(Dicts.classes['z'])
                                if (x not in ori_set and x not in dest_set) or
                                (x in ori_set and x in dest_set))
                            depend2_1 = RejectUnlessGreaterThanLength(-N - 1)
                            depend2_2 = RejectUnlessCharInPosition(
                                complement_result, N)
                            depend2_3 = deepcopy(read_only_depend)

                            tmp_dependency_list2 = deepcopy(one_dep_list)
                            tmp_dependency_list2.prepend_dependency(depend2_1)
                            tmp_dependency_list2.prepend_dependency(depend2_2)
                            tmp_dependency_list2.prepend_dependency(depend2_3)

                            #case3: >0, char at pos -1 a. Need 2
                            ori_set = read_only_depend.get_chars()
                            dest_set = dest_set = get_dest_set(ori_set)

                            # Toggle set (a,b,A)
                            # If char at 3 == A/a. Mean contains. Only use (a,b,A) - (a,B,A)
                            # Why? Because a,A still in the set. So you toggle that you get something still in the set.
                            # it is still satisfied.
                            difference_set = ori_set.difference(dest_set)
                            depend3_1 = RejectUnlessGreaterThanLength(-N - 1)
                            depend3_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend3_3 = deepcopy(read_only_depend)
                            depend3_3.set_number(depend3_3.get_number() + 1)

                            tmp_dependency_list3 = deepcopy(one_dep_list)
                            tmp_dependency_list3.prepend_dependency(depend3_1)
                            tmp_dependency_list3.prepend_dependency(depend3_2)
                            tmp_dependency_list3.prepend_dependency(depend3_3)

                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list1)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list2)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list3)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:

                        #Check Char in position
                        check_pos = read_only_depend.get_position()

                        if N >= 0:
                            # T4 =1a
                            # T4 =1?a
                            # T4 =4D
                            # T4 =4?a
                            # T0 (E
                            # T0 =0?a
                            # T0 =2a
                            # T3 (B
                            # T3 =3?a
                            # T3 =3f
                            # T2 (?a
                            # T2 =2-
                            # T4 )?a
                            # T4 )f
                            # T3 )a
                            # T3 )?a
                            # xg-1dfa hl=dfa21 cmaF214 skrf1243dz eghqFDZ21 Efds)(5)242df xbdad329Z1 Fiekd21^.
                            # zcsqF xmrqf czsA x03a xmewi fs3v fds8 vczn2 awo@

                            # No matter what position is toggled, to satisfy char at position, length has to be greater than abs(check_pos)
                            if check_pos >= 0:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    abs(check_pos))
                            else:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    -check_pos - 1)

                            # No matter where the rejection rule checks, if T9. Then introduce >9 and <=9
                            # T9, word_len <= 9
                            depend0_0 = RejectUnlessLessThanLength(
                                N + 1)  # The length from N
                            depend0_1 = deepcopy(read_only_depend)
                            tmp_dependency_list0 = deepcopy(one_dep_list)
                            tmp_dependency_list0.prepend_dependency(depend0_0)
                            tmp_dependency_list0.prepend_dependency(depend0_1)
                            tmp_dependency_list0.prepend_dependency(
                                deepcopy(depend_len_from_check_pos))
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list0)

                            # T9, word_len >9
                            depend_len_from_N = RejectUnlessGreaterThanLength(N)
                            if check_pos >= 0:  #If check char at positive position

                                if check_pos != N:  # T9, (a
                                    #Toggle position != char at positition.
                                    #Doesn't matter

                                    depend1_0 = deepcopy(read_only_depend)

                                    tmp_dependency_list1 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list1.prepend_dependency(
                                        depend1_0)
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list1)

                                else:  #T9, =9a
                                    #Toggle position = char at positition.
                                    #Literally toggle the chars here.

                                    ori_set = read_only_depend.get_chars()
                                    dest_set = get_dest_set(ori_set)
                                    depend2_0 = deepcopy(read_only_depend)
                                    depend2_0.set_chars(dest_set)

                                    tmp_dependency_list2 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list2.prepend_dependency(
                                        depend2_0)
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list2)

                            else:  # T9, )a. Only consider >= 10

                                # depend_len_from_N >= 10
                                # depend_len_from_check_pos >= 1
                                # Only when len ==
                                min_word_len = max(N + 1, -check_pos)

                                # word_len < N - check_pos:
                                #T9, )a. wordlen = 5
                                #Doesn't matter

                                depend1_0 = RejectUnlessLessThanLength(
                                    N - check_pos)
                                depend1_1 = RejectUnlessGreaterThanLength(
                                    min_word_len - 1)
                                depend1_2 = deepcopy(read_only_depend)

                                tmp_dependency_list1 = deepcopy(one_dep_list)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_0)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_1)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_2)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list1)

                                # word_len == N - check_pos: #Affect
                                #If equals.
                                #T9, )a. wordlen = 10
                                #Then toggle the char

                                depend2_0 = RejectUnlessLessThanLength(
                                    N - check_pos + 1)
                                depend2_1 = RejectUnlessGreaterThanLength(
                                    N - check_pos - 1)
                                depend2_2 = deepcopy(read_only_depend)
                                ori_set = read_only_depend.get_chars()
                                dest_set = get_dest_set(ori_set)
                                depend2_2.set_chars(dest_set)

                                tmp_dependency_list2 = deepcopy(one_dep_list)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_0)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_1)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_2)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list2)

                                #Else
                                #T9, )a. wordlen > 10
                                #Doesnt matter
                                depend3_1 = RejectUnlessGreaterThanLength(
                                    N - check_pos)
                                depend3_2 = deepcopy(read_only_depend)

                                tmp_dependency_list3 = deepcopy(one_dep_list)
                                tmp_dependency_list3.prepend_dependency(
                                    depend3_1)
                                tmp_dependency_list3.prepend_dependency(
                                    depend3_2)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list3)

                        else:  # N < 0

                            #Tm =0a
                            #Tm =0?a
                            #Tm =3d
                            #Tm =3?a
                            #Tm )a
                            #Tm )?a
                            #Tm )?d
                            #Tm )?l
                            #A X F f xbdD czdd asdfewfdDd xcmzafo xzD zmA feqa XV3 ZX* dsfmF vmce

                            # No matter what position is toggled, to satisfy char at position, length has to be greater than abs(check_pos)
                            if check_pos >= 0:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    abs(check_pos))
                            else:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    -check_pos - 1)

                            depend_len_from_N = RejectUnlessGreaterThanLength(
                                -N - 1)

                            if check_pos >= 0:  # Tm, (a

                                #Enumerate word length
                                min_word_len = max(-N, check_pos + 1)

                                # word_len < check_pos - N:
                                #Tm, =2a. word len 1
                                #Doesnt matter

                                depend1_0 = RejectUnlessLessThanLength(
                                    check_pos - N)
                                depend1_1 = RejectUnlessGreaterThanLength(
                                    min_word_len - 1)
                                depend1_2 = deepcopy(read_only_depend)

                                tmp_dependency_list1 = deepcopy(one_dep_list)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_0)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_1)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_2)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list1)

                                # word_len == check_pos - N: #Affect
                                #Tm, =2a, wordlen = 3
                                #Affect, toggle.

                                depend2_0 = RejectUnlessLessThanLength(
                                    check_pos - N + 1)
                                depend2_1 = RejectUnlessGreaterThanLength(
                                    check_pos - N - 1)
                                depend2_2 = deepcopy(read_only_depend)
                                ori_set = read_only_depend.get_chars()
                                dest_set = get_dest_set(ori_set)
                                depend2_2.set_chars(dest_set)

                                tmp_dependency_list2 = deepcopy(one_dep_list)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_0)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_1)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_2)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list2)

                                #Tm, =2a, wordlen > 3
                                #Doesnt matter
                                depend3_1 = RejectUnlessGreaterThanLength(
                                    check_pos - N)
                                depend3_2 = deepcopy(read_only_depend)

                                tmp_dependency_list3 = deepcopy(one_dep_list)
                                tmp_dependency_list3.prepend_dependency(
                                    depend3_1)
                                tmp_dependency_list3.prepend_dependency(
                                    depend3_2)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list3)

                            else:  #check_pos <0, N < 0

                                if check_pos != N:  # Tm, =-2a
                                    #If the Tm, =-2a,
                                    #Doesnt affect
                                    depend1_0 = deepcopy(read_only_depend)

                                    tmp_dependency_list1 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list1.prepend_dependency(
                                        depend1_0)
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list1)

                                else:  #Tm, )a
                                    #Affect, toggle

                                    ori_set = read_only_depend.get_chars()
                                    dest_set = get_dest_set(ori_set)
                                    depend2_0 = deepcopy(read_only_depend)
                                    depend2_0.set_chars(dest_set)

                                    tmp_dependency_list2 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list2.prepend_dependency(
                                        depend2_0)
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list2)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend = deepcopy(read_only_depend)

                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend = deepcopy(read_only_depend)

                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        # case1: len < 4. Doesn't do anything
                        depend1 = RejectUnlessLessThanLength(N + 1)
                        depend1_1 = deepcopy(
                            read_only_depend)  #Doesn't affect the old
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(depend1)
                        no_op_dep_list.prepend_dependency(depend1_1)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N)

                        if from_idx >= 0:
                            # Case1: N in [from, to)
                            if to_idx > N >= from_idx:
                                toggled_chars = get_dest_set(chars)

                                # case1.1: toggled_chars not in chars.
                                toggled_chars_not_in = toggled_chars - chars
                                dep_list_case_2 = deepcopy(one_dep_list)
                                dep_list_case_2.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        toggled_chars_not_in, N))
                                dep_list_case_2.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number - 1, chars))
                                dep_list_case_2.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_2)

                                # case1.3: (set(Dicts.classes['z']) - toggled_chars) & chars, +1. Say T1, %a. If T1 = a, add 1 to number
                                chars_not_in_toggled = chars - toggled_chars
                                dep_list_case_3 = deepcopy(one_dep_list)
                                dep_list_case_3.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        chars_not_in_toggled, N))
                                dep_list_case_3.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number + 1, chars))
                                dep_list_case_3.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_3)

                                # case1.2: (set(Dicts.classes['z']) - toggled_chars_not_in) - chars, doesn't change
                                dep_list_case_1 = deepcopy(one_dep_list)
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) -
                                        chars_not_in_toggled -
                                        toggled_chars_not_in, N))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                            # Case2: N not in [from, to)
                            else:
                                one_dep_list.prepend_dependency(
                                    read_only_depend)
                                one_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                        else:
                            # Case1: N in [from, to), where N - from_idx >= len > N - to_idx
                            toggled_chars = get_dest_set(chars)

                            # case1.1: toggled_chars not in chars.
                            toggled_chars_not_in = toggled_chars - chars
                            dep_list_case_2 = deepcopy(one_dep_list)
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    toggled_chars_not_in, N))
                            dep_list_case_2.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number - 1, chars))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_2.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_2)

                            # case1.3: (set(Dicts.classes['z']) - toggled_chars) & chars, +1. Say T1, %a. If T1 = a, add 1 to number
                            chars_not_in_toggled = chars - toggled_chars
                            dep_list_case_3 = deepcopy(one_dep_list)
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    chars_not_in_toggled, N))
                            dep_list_case_3.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number + 1, chars))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_3.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_3)

                            # case1.2: (set(Dicts.classes['z']) - toggled_chars_not_in) - chars, doesn't change
                            dep_list_case_1 = deepcopy(one_dep_list)
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) -
                                    chars_not_in_toggled - toggled_chars_not_in,
                                    N))
                            dep_list_case_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_1.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1)

                            # case1.3 & 1.4 doesn't matter
                            dep_list_case_4 = deepcopy(one_dep_list)
                            dep_list_case_4.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_4.prepend_dependency(
                                RejectUnlessLessThanLength(N - to_idx + 1))
                            dep_list_case_4.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_4)

                            dep_list_case_5 = deepcopy(one_dep_list)
                            dep_list_case_5.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_5.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - from_idx))
                            dep_list_case_5.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_5)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_minus_N_command(subrule_dependency, rule):
        """ -N  Decrement char at position N by 1 ascii value

        Effects on Dependency:
            depends on char at N

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """

        def get_dest_set(ori_set):

            #Remove not valid
            return set(chr((ord(x) + 1) % 256) for x in ori_set)

        ret_val = SubruleDependency(subrule_dependency)

        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Countable")

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        # Here notice that if just toggle a set of chars, the result could still
                        # be in the set. Toggle /?a still equals /?a
                        # Two situations: Char at place N equals and char at place N not equals
                        # No memorization involved.
                        if N >= 0:
                            # T1 /a
                            # T4 /D
                            # T3 /=
                            # T3 /?a
                            # T3 /?d
                            # a fa1 cAbc16 t2fad1
                            # bvD e4hd134 vjeD34D bnmD14 vcx153ghessD
                            # =d vxw+24 vqa+ble24 fdslnwjrn+=-21 cxzfmw@*#&*-=

                            # case1: len < 4. Doesn't do anything
                            depend1 = RejectUnlessLessThanLength(N + 1)
                            depend1_1 = deepcopy(
                                read_only_depend)  #Doesn't affect the old
                            tmp_dependency_list1 = deepcopy(one_dep_list)
                            tmp_dependency_list1.prepend_dependency(depend1)
                            tmp_dependency_list1.prepend_dependency(depend1_1)

                            # case2,3,4 combined can be understood by drawing Venn diagram.
                            # case2: len > 3. Char at 3 == A. -> add one a.
                            # corner case: len > 3. Char at 3 = ?d -> add one ?d but should still be 2.
                            ori_set = read_only_depend.get_chars()
                            dest_set = get_dest_set(
                                ori_set
                            )  #So that what's in dest_set is not in ori_set
                            #if what's in the dest set is also in ori_set. it doesn't affect the number
                            difference_set = dest_set.difference(ori_set)
                            depend2_1 = RejectUnlessGreaterThanLength(N)
                            depend2_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend2_3 = deepcopy(read_only_depend)
                            depend2_3.set_number(depend2_3.get_number() - 1)

                            tmp_dependency_list2 = deepcopy(one_dep_list)
                            tmp_dependency_list2.prepend_dependency(depend2_2)
                            tmp_dependency_list2.prepend_dependency(depend2_3)

                            # case3: len > 3, Char at 3 != a/A. Doesn't Matter
                            complement_result = set(
                                x for x in set(Dicts.classes['z'])
                                if (x not in ori_set and x not in dest_set) or
                                (x in ori_set and x in dest_set))
                            depend3_1 = RejectUnlessGreaterThanLength(N)
                            depend3_2 = RejectUnlessCharInPosition(
                                complement_result, N)
                            depend3_3 = deepcopy(read_only_depend)

                            tmp_dependency_list3 = deepcopy(one_dep_list)
                            tmp_dependency_list3.prepend_dependency(depend3_2)
                            tmp_dependency_list3.prepend_dependency(depend3_3)

                            # case4: len > 3. Char at 3 == a. -> Delete one a. Need two in original.
                            ori_set = read_only_depend.get_chars()
                            dest_set = get_dest_set(ori_set)

                            # Toggle set (a,b,A)
                            # If char at 3 == A/a. Mean contains. Only use (a,b,A) - (a,B,A)
                            # Why? Because a,A still in the set. So you toggle that you get something still in the set.
                            # it is still satisfied.
                            difference_set = ori_set.difference(dest_set)

                            depend4_1 = RejectUnlessGreaterThanLength(N)
                            depend4_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend4_3 = deepcopy(read_only_depend)
                            depend4_3.set_number(depend4_3.get_number() + 1)

                            tmp_dependency_list4 = deepcopy(one_dep_list)
                            tmp_dependency_list4.prepend_dependency(depend4_2)
                            tmp_dependency_list4.prepend_dependency(depend4_3)

                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list1)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list2)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list3)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list4)

                        else:  # N < 0
                            #Tm /b
                            #Tm /E
                            #Tm /)
                            #Tm /?d
                            #Tm /?a
                            #vcxB qfb w212fE dasve fdsdf) sdfsf0 vxcsf1 bkon qjroi0fn aijs*

                            #case1: >0, char at pos -1 A. Get an extra a.
                            ori_set = read_only_depend.get_chars()
                            dest_set = get_dest_set(ori_set)
                            difference_set = dest_set.difference(ori_set)
                            depend1_1 = RejectUnlessGreaterThanLength(-N - 1)
                            depend1_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend1_3 = deepcopy(read_only_depend)
                            depend1_3.set_number(depend1_3.get_number() - 1)

                            tmp_dependency_list1 = deepcopy(one_dep_list)
                            tmp_dependency_list1.prepend_dependency(depend1_1)
                            tmp_dependency_list1.prepend_dependency(depend1_2)
                            tmp_dependency_list1.prepend_dependency(depend1_3)

                            #case2: >0, char at pos -1 not equal a/A. Doesnt matter
                            complement_result = set(
                                x for x in set(Dicts.classes['z'])
                                if (x not in ori_set and x not in dest_set) or
                                (x in ori_set and x in dest_set))
                            depend2_1 = RejectUnlessGreaterThanLength(-N - 1)
                            depend2_2 = RejectUnlessCharInPosition(
                                complement_result, N)
                            depend2_3 = deepcopy(read_only_depend)

                            tmp_dependency_list2 = deepcopy(one_dep_list)
                            tmp_dependency_list2.prepend_dependency(depend2_1)
                            tmp_dependency_list2.prepend_dependency(depend2_2)
                            tmp_dependency_list2.prepend_dependency(depend2_3)

                            #case3: >0, char at pos -1 a. Need 2
                            ori_set = read_only_depend.get_chars()
                            dest_set = dest_set = get_dest_set(ori_set)

                            # Toggle set (a,b,A)
                            # If char at 3 == A/a. Mean contains. Only use (a,b,A) - (a,B,A)
                            # Why? Because a,A still in the set. So you toggle that you get something still in the set.
                            # it is still satisfied.
                            difference_set = ori_set.difference(dest_set)
                            depend3_1 = RejectUnlessGreaterThanLength(-N - 1)
                            depend3_2 = RejectUnlessCharInPosition(
                                difference_set, N)
                            depend3_3 = deepcopy(read_only_depend)
                            depend3_3.set_number(depend3_3.get_number() + 1)

                            tmp_dependency_list3 = deepcopy(one_dep_list)
                            tmp_dependency_list3.prepend_dependency(depend3_1)
                            tmp_dependency_list3.prepend_dependency(depend3_2)
                            tmp_dependency_list3.prepend_dependency(depend3_3)

                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list1)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list2)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list3)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:

                        #Check Char in position
                        check_pos = read_only_depend.get_position()

                        if N >= 0:
                            # T4 =1a
                            # T4 =1?a
                            # T4 =4D
                            # T4 =4?a
                            # T0 (E
                            # T0 =0?a
                            # T0 =2a
                            # T3 (B
                            # T3 =3?a
                            # T3 =3f
                            # T2 (?a
                            # T2 =2-
                            # T4 )?a
                            # T4 )f
                            # T3 )a
                            # T3 )?a
                            # xg-1dfa hl=dfa21 cmaF214 skrf1243dz eghqFDZ21 Efds)(5)242df xbdad329Z1 Fiekd21^.
                            # zcsqF xmrqf czsA x03a xmewi fs3v fds8 vczn2 awo@

                            # No matter what position is toggled, to satisfy char at position, length has to be greater than abs(check_pos)
                            if check_pos >= 0:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    abs(check_pos))
                            else:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    -check_pos - 1)

                            # No matter where the rejection rule checks, if T9. Then introduce >9 and <=9
                            # T9, word_len <= 9
                            depend0_0 = RejectUnlessLessThanLength(
                                N + 1)  # The length from N
                            depend0_1 = deepcopy(read_only_depend)
                            tmp_dependency_list0 = deepcopy(one_dep_list)
                            tmp_dependency_list0.prepend_dependency(depend0_0)
                            tmp_dependency_list0.prepend_dependency(depend0_1)
                            tmp_dependency_list0.prepend_dependency(
                                deepcopy(depend_len_from_check_pos))
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list0)

                            # T9, word_len >9
                            depend_len_from_N = RejectUnlessGreaterThanLength(N)
                            if check_pos >= 0:  #If check char at positive position

                                if check_pos != N:  # T9, (a
                                    #Toggle position != char at positition.
                                    #Doesn't matter

                                    depend1_0 = deepcopy(read_only_depend)

                                    tmp_dependency_list1 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list1.prepend_dependency(
                                        depend1_0)
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list1)

                                else:  #T9, =9a
                                    #Toggle position = char at positition.
                                    #Literally toggle the chars here.

                                    ori_set = read_only_depend.get_chars()
                                    dest_set = get_dest_set(ori_set)
                                    depend2_0 = deepcopy(read_only_depend)
                                    depend2_0.set_chars(dest_set)

                                    tmp_dependency_list2 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list2.prepend_dependency(
                                        depend2_0)
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list2)

                            else:  # T9, )a. Only consider >= 10

                                # depend_len_from_N >= 10
                                # depend_len_from_check_pos >= 1
                                # Only when len ==
                                min_word_len = max(N + 1, -check_pos)

                                #length < N - check_pos
                                #T9, )a. wordlen = 5
                                #Doesn't matter

                                depend1_0 = RejectUnlessLessThanLength(
                                    N - check_pos)
                                depend1_1 = RejectUnlessGreaterThanLength(
                                    min_word_len - 1)
                                depend1_2 = deepcopy(read_only_depend)

                                tmp_dependency_list1 = deepcopy(one_dep_list)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_0)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_1)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_2)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list1)

                                #length = N - check_pos
                                #If equals.
                                #T9, )a. wordlen = 10
                                #Then toggle the char

                                depend2_0 = RejectUnlessLessThanLength(
                                    N - check_pos + 1)
                                depend2_1 = RejectUnlessGreaterThanLength(
                                    N - check_pos - 1)
                                depend2_2 = deepcopy(read_only_depend)
                                ori_set = read_only_depend.get_chars()
                                dest_set = get_dest_set(ori_set)
                                depend2_2.set_chars(dest_set)

                                tmp_dependency_list2 = deepcopy(one_dep_list)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_0)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_1)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_2)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list2)

                                #length > N - check_pos
                                #Else
                                #T9, )a. wordlen > 10
                                #Doesnt matter
                                depend3_1 = RejectUnlessGreaterThanLength(
                                    N - check_pos)
                                depend3_2 = deepcopy(read_only_depend)

                                tmp_dependency_list3 = deepcopy(one_dep_list)
                                tmp_dependency_list3.prepend_dependency(
                                    depend3_1)
                                tmp_dependency_list3.prepend_dependency(
                                    depend3_2)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list3)

                        else:  # N < 0

                            #Tm =0a
                            #Tm =0?a
                            #Tm =3d
                            #Tm =3?a
                            #Tm )a
                            #Tm )?a
                            #Tm )?d
                            #Tm )?l
                            #A X F f xbdD czdd asdfewfdDd xcmzafo xzD zmA feqa XV3 ZX* dsfmF vmce

                            # No matter what position is toggled, to satisfy char at position, length has to be greater than abs(check_pos)
                            if check_pos >= 0:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    abs(check_pos))
                            else:
                                depend_len_from_check_pos = RejectUnlessGreaterThanLength(
                                    -check_pos - 1)

                            depend_len_from_N = RejectUnlessGreaterThanLength(
                                -N - 1)

                            if check_pos >= 0:  # Tm, (a

                                #Enumerate word length
                                min_word_len = max(-N, check_pos + 1)

                                # word_len < check_pos - N:
                                #Tm, =2a. word len 1
                                #Doesnt matter

                                depend1_0 = RejectUnlessLessThanLength(
                                    check_pos - N)
                                depend1_1 = RejectUnlessGreaterThanLength(
                                    min_word_len - 1)
                                depend1_2 = deepcopy(read_only_depend)

                                tmp_dependency_list1 = deepcopy(one_dep_list)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_0)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_1)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_2)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list1)

                                # word_len == check_pos - N: #Affect
                                #Tm, =2a, wordlen = 3
                                #Affect, toggle.

                                depend2_0 = RejectUnlessLessThanLength(
                                    check_pos - N + 1)
                                depend2_1 = RejectUnlessGreaterThanLength(
                                    check_pos - N - 1)
                                depend2_2 = deepcopy(read_only_depend)
                                ori_set = read_only_depend.get_chars()
                                dest_set = get_dest_set(ori_set)
                                depend2_2.set_chars(dest_set)

                                tmp_dependency_list2 = deepcopy(one_dep_list)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_0)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_1)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_2)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list2)

                                #Tm, =2a, wordlen > 3
                                #Doesnt matter
                                depend3_1 = RejectUnlessGreaterThanLength(
                                    check_pos - N)
                                depend3_2 = deepcopy(read_only_depend)

                                tmp_dependency_list3 = deepcopy(one_dep_list)
                                tmp_dependency_list3.prepend_dependency(
                                    depend3_1)
                                tmp_dependency_list3.prepend_dependency(
                                    depend3_2)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list3)

                            else:  #check_pos <0, N < 0

                                if check_pos != N:  # Tm, =-2a
                                    #If the Tm, =-2a,
                                    #Doesnt affect
                                    depend1_0 = deepcopy(read_only_depend)

                                    tmp_dependency_list1 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list1.prepend_dependency(
                                        depend1_0)
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list1)

                                else:  #Tm, )a
                                    #Affect, toggle

                                    ori_set = read_only_depend.get_chars()
                                    dest_set = get_dest_set(ori_set)
                                    depend2_0 = deepcopy(read_only_depend)
                                    depend2_0.set_chars(dest_set)

                                    tmp_dependency_list2 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list2.prepend_dependency(
                                        depend2_0)
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_N))
                                    tmp_dependency_list2.prepend_dependency(
                                        deepcopy(depend_len_from_check_pos))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list2)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend = deepcopy(read_only_depend)

                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend = deepcopy(read_only_depend)

                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        # case1: len < 4. Doesn't do anything
                        depend1 = RejectUnlessLessThanLength(N + 1)
                        depend1_1 = deepcopy(
                            read_only_depend)  #Doesn't affect the old
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(depend1)
                        no_op_dep_list.prepend_dependency(depend1_1)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N)

                        if from_idx >= 0:
                            # Case1: N in [from, to)
                            if to_idx > N >= from_idx:
                                toggled_chars = get_dest_set(chars)

                                # case1.1: toggled_chars not in chars.
                                toggled_chars_not_in = toggled_chars - chars
                                dep_list_case_2 = deepcopy(one_dep_list)
                                dep_list_case_2.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        toggled_chars_not_in, N))
                                dep_list_case_2.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number - 1, chars))
                                dep_list_case_2.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_2)

                                # case1.3: (set(Dicts.classes['z']) - toggled_chars) & chars, +1. Say T1, %a. If T1 = a, add 1 to number
                                chars_not_in_toggled = chars - toggled_chars
                                dep_list_case_3 = deepcopy(one_dep_list)
                                dep_list_case_3.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        chars_not_in_toggled, N))
                                dep_list_case_3.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number + 1, chars))
                                dep_list_case_3.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_3)

                                # case1.2: (set(Dicts.classes['z']) - toggled_chars_not_in) - chars, doesn't change
                                dep_list_case_1 = deepcopy(one_dep_list)
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) -
                                        chars_not_in_toggled -
                                        toggled_chars_not_in, N))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                            # Case2: N not in [from, to)
                            else:
                                one_dep_list.prepend_dependency(
                                    read_only_depend)
                                one_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                        else:
                            # Case1: N in [from, to), where N - from_idx >= len > N - to_idx
                            toggled_chars = get_dest_set(chars)

                            # case1.1: toggled_chars not in chars.
                            toggled_chars_not_in = toggled_chars - chars
                            dep_list_case_2 = deepcopy(one_dep_list)
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    toggled_chars_not_in, N))
                            dep_list_case_2.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number - 1, chars))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_2.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_2)

                            # case1.3: (set(Dicts.classes['z']) - toggled_chars) & chars, +1. Say T1, %a. If T1 = a, add 1 to number
                            chars_not_in_toggled = chars - toggled_chars
                            dep_list_case_3 = deepcopy(one_dep_list)
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    chars_not_in_toggled, N))
                            dep_list_case_3.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number + 1, chars))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_3.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_3)

                            # case1.2: (set(Dicts.classes['z']) - toggled_chars_not_in) - chars, doesn't change
                            dep_list_case_1 = deepcopy(one_dep_list)
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) -
                                    chars_not_in_toggled - toggled_chars_not_in,
                                    N))
                            dep_list_case_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_1.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1)

                            # case1.3 & 1.4 doesn't matter
                            dep_list_case_4 = deepcopy(one_dep_list)
                            dep_list_case_4.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_4.prepend_dependency(
                                RejectUnlessLessThanLength(N - to_idx + 1))
                            dep_list_case_4.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_4)

                            dep_list_case_5 = deepcopy(one_dep_list)
                            dep_list_case_5.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_5.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - from_idx))
                            dep_list_case_5.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_5)

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_period_N_command(subrule_dependency, rule):
        """ .N  Replace char at position N with the char at position N + 1

        Effects on Dependency:
            reason about char at N and N + 1

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Countable")

        M = N + 1

        min_word_length = max(N, M) + 1

        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        #No op
                        depend_length_no_op = RejectUnlessLessThanLength(
                            min_word_length)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        #OP
                        depend_length_op = RejectUnlessGreaterThanLength(
                            min_word_length - 1)
                        ori_set = read_only_depend.get_chars()

                        ##Be careful what you do here.
                        ##4 Cases
                        ### 1. M equals set, N equals set, doesn't change
                        ### 2. M equals set, N not equals set, change. num = num - 1 # M is also counted, so it is not num - 2
                        ### 3. M not equals, N equals. num = num + 1
                        ### 4. M not equals, N not equals. doesn't change

                        #### case1
                        depend_M_equal = RejectUnlessCharInPosition(ori_set, M)
                        depend_N_equal = RejectUnlessCharInPosition(ori_set, N)
                        depend = deepcopy(read_only_depend)
                        dep_list_case_1 = deepcopy(one_dep_list)
                        dep_list_case_1.prepend_dependency(
                            deepcopy(depend_length_op))
                        dep_list_case_1.prepend_dependency(depend)
                        dep_list_case_1.prepend_dependency(depend_M_equal)
                        dep_list_case_1.prepend_dependency(depend_N_equal)

                        #### case4
                        depend_M_not_equal = RejectUnlessCharInPosition(
                            set(Dicts.classes['z']) - ori_set, M)
                        depend_N_not_equal = RejectUnlessCharInPosition(
                            set(Dicts.classes['z']) - ori_set, N)
                        depend = deepcopy(read_only_depend)
                        dep_list_case_4 = deepcopy(one_dep_list)
                        dep_list_case_4.prepend_dependency(
                            deepcopy(depend_length_op))
                        dep_list_case_4.prepend_dependency(depend)
                        dep_list_case_4.prepend_dependency(depend_M_not_equal)
                        dep_list_case_4.prepend_dependency(depend_N_not_equal)

                        #### case2
                        depend_M_equal = RejectUnlessCharInPosition(ori_set, M)
                        depend_N_not_equal = RejectUnlessCharInPosition(
                            set(Dicts.classes['z']) - ori_set, N)
                        depend = deepcopy(read_only_depend)
                        depend.set_number(depend.get_number() - 1)
                        dep_list_case_2 = deepcopy(one_dep_list)
                        dep_list_case_2.prepend_dependency(
                            deepcopy(depend_length_op))
                        dep_list_case_2.prepend_dependency(depend)
                        dep_list_case_2.prepend_dependency(depend_M_equal)
                        dep_list_case_2.prepend_dependency(depend_N_not_equal)

                        #### case3
                        depend_M_not_equal = RejectUnlessCharInPosition(
                            set(Dicts.classes['z']) - ori_set, M)
                        depend_N_equal = RejectUnlessCharInPosition(ori_set, N)
                        depend = deepcopy(read_only_depend)
                        depend.set_number(depend.get_number() + 1)
                        dep_list_case_3 = deepcopy(one_dep_list)
                        dep_list_case_3.prepend_dependency(
                            deepcopy(depend_length_op))
                        dep_list_case_3.prepend_dependency(depend)
                        dep_list_case_3.prepend_dependency(depend_M_not_equal)
                        dep_list_case_3.prepend_dependency(depend_N_equal)

                        save_split_dep_lists.append_dependency_list(
                            dep_list_case_1)
                        save_split_dep_lists.append_dependency_list(
                            dep_list_case_2)
                        save_split_dep_lists.append_dependency_list(
                            dep_list_case_3)
                        save_split_dep_lists.append_dependency_list(
                            dep_list_case_4)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:

                        ori_pos = read_only_depend.get_position()
                        # N, M >= 0
                        if N >= 0 and M >= 0:

                            if ori_pos >= 0:  #ori_pos >= 0 and NM >=0

                                #ori_pos != N and ori_pos != M
                                if ori_pos != N and ori_pos != M:
                                    #Doesn't matter
                                    dep_list = deepcopy(one_dep_list)
                                    dep_list.prepend_dependency(
                                        deepcopy(read_only_depend))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list)

                                else:
                                    #No op
                                    depend_length_no_op = RejectUnlessLessThanLength(
                                        min_word_length)
                                    no_op_dep_list_1 = deepcopy(one_dep_list)
                                    no_op_dep_list_1.prepend_dependency(
                                        deepcopy(read_only_depend))
                                    no_op_dep_list_1.prepend_dependency(
                                        depend_length_no_op)
                                    save_split_dep_lists.append_dependency_list(
                                        no_op_dep_list_1)

                                    #Op
                                    #Dont' Forget To Test Boundary Cases!
                                    depend_length_op = RejectUnlessGreaterThanLength(
                                        min_word_length - 1)
                                    depend = deepcopy(read_only_depend)
                                    if ori_pos == N:
                                        depend.set_position(M)
                                    elif ori_pos == M:  # use M to replace N, =M do nothing
                                        pass
                                    else:
                                        raise ValueError("Wrong ori_pos")
                                    op_dep_list = deepcopy(one_dep_list)
                                    op_dep_list.prepend_dependency(
                                        depend_length_op)
                                    op_dep_list.prepend_dependency(depend)
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list)

                            else:
                                #No op
                                depend_length_no_op = RejectUnlessLessThanLength(
                                    min_word_length)
                                no_op_dep_list_1 = deepcopy(one_dep_list)
                                no_op_dep_list_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                no_op_dep_list_1.prepend_dependency(
                                    depend_length_no_op)
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list_1)

                                #op
                                depend_length_op = RejectUnlessGreaterThanLength(
                                    min_word_length - 1)
                                #Only affect when word_len == N - ori_pos

                                #case1: word_len == N - ori_pos
                                equal_len = N - ori_pos
                                depend_len_equal_lower = RejectUnlessLessThanLength(
                                    equal_len + 1)
                                depend_len_equal_upper = RejectUnlessGreaterThanLength(
                                    equal_len - 1)
                                depend = deepcopy(read_only_depend)
                                depend.set_position(M)
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(
                                    depend_len_equal_lower)
                                op_dep_list.prepend_dependency(
                                    depend_len_equal_upper)
                                op_dep_list.prepend_dependency(depend)
                                op_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                                #case2: word_len != N - ori_pos. no op
                                depend_len_no_equal_lower = RejectUnlessLessThanLength(
                                    equal_len)
                                depend_len_no_equal_upper = RejectUnlessGreaterThanLength(
                                    equal_len)

                                no_op_dep_list_1 = deepcopy(one_dep_list)
                                no_op_dep_list_1.prepend_dependency(
                                    depend_len_no_equal_lower)
                                no_op_dep_list_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                no_op_dep_list_1.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list_1)

                                no_op_dep_list_2 = deepcopy(one_dep_list)
                                no_op_dep_list_2.prepend_dependency(
                                    depend_len_no_equal_upper)
                                no_op_dep_list_2.prepend_dependency(
                                    deepcopy(read_only_depend))
                                no_op_dep_list_2.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list_2)

                        else:
                            raise ValueError("N in count_period_N_command")

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        M = N + 1

                        if from_idx >= 0:
                            # case -1: no operation for length < max(N,M) + 1
                            no_op_dep_list = deepcopy(one_dep_list)
                            no_op_dep_list.prepend_dependency(
                                RejectUnlessLessThanLength(max(N, M) + 1))
                            no_op_dep_list.prepend_dependency(
                                deepcopy(read_only_depend))
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list)

                            depend_length_op_lower = RejectUnlessGreaterThanLength(
                                max(N, M))

                            # N is in [from, to)
                            if to_idx > N >= from_idx:
                                # if M also in.
                                #if to_idx > M >= from_idx:

                                # 4 cases: M = chars, N = chars; M != chars, N != chars;
                                dep_list_case_1 = deepcopy(one_dep_list)
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, M))
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, N))
                                dep_list_case_1.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number, chars))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                                dep_list_case_2 = deepcopy(one_dep_list)
                                dep_list_case_2.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, M))
                                dep_list_case_2.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, N))
                                dep_list_case_2.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number, chars))
                                dep_list_case_2.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_2)

                                dep_list_case_3 = deepcopy(one_dep_list)
                                dep_list_case_3.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, M))
                                dep_list_case_3.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, N))
                                dep_list_case_3.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number + 1, chars))
                                dep_list_case_3.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_3)

                                dep_list_case_4 = deepcopy(one_dep_list)
                                dep_list_case_4.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, M))
                                dep_list_case_4.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, N))
                                dep_list_case_4.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number - 1, chars))
                                dep_list_case_4.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_4)
                                #else:
                                #pass

                            else:  # doesn't matter
                                one_dep_list.prepend_dependency(
                                    read_only_depend)
                                one_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                        else:
                            # case -1: no operation for length < max(N,M) + 1
                            no_op_dep_list = deepcopy(one_dep_list)
                            no_op_dep_list.prepend_dependency(
                                RejectUnlessLessThanLength(max(N, M) + 1))
                            no_op_dep_list.prepend_dependency(
                                deepcopy(read_only_depend))
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list)

                            depend_length_op_lower = RejectUnlessGreaterThanLength(
                                max(N, M))

                            # Case1: N in [from, to), where N - from_idx >= len > N - to_idx
                            dep_list_case_1 = deepcopy(one_dep_list)
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessCharInPosition(chars, M))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessCharInPosition(chars, N))
                            dep_list_case_1.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number, chars))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_1.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1)

                            dep_list_case_2 = deepcopy(one_dep_list)
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) - chars, M))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) - chars, N))
                            dep_list_case_2.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number, chars))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_2.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_2)

                            dep_list_case_3 = deepcopy(one_dep_list)
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) - chars, M))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessCharInPosition(chars, N))
                            dep_list_case_3.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number + 1, chars))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_3.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_3)

                            dep_list_case_4 = deepcopy(one_dep_list)
                            dep_list_case_4.prepend_dependency(
                                RejectUnlessCharInPosition(chars, M))
                            dep_list_case_4.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) - chars, N))
                            dep_list_case_4.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number - 1, chars))
                            dep_list_case_4.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_4.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_4.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_4)

                            # case1.3 & 1.4 doesn't matter
                            dep_list_case_5 = deepcopy(one_dep_list)
                            dep_list_case_5.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_5.prepend_dependency(
                                RejectUnlessLessThanLength(N - to_idx + 1))
                            dep_list_case_5.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_5)

                            dep_list_case_6 = deepcopy(one_dep_list)
                            dep_list_case_6.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_6.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - from_idx))
                            dep_list_case_6.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_6)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_comma_N_command(subrule_dependency, rule):
        """ ,N  Replace char at position N with the char at position N - 1

        Effects on Dependency:
            reason about char at N and N - 1

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Countable")

        if N == 0:
            return subrule_dependency  #Doesn't do anything

        M = N - 1

        min_word_length = max(N, M) + 1

        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        #No op
                        depend_length_no_op = RejectUnlessLessThanLength(
                            min_word_length)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        #OP
                        depend_length_op = RejectUnlessGreaterThanLength(
                            min_word_length - 1)
                        ori_set = read_only_depend.get_chars()

                        ##Be careful what you do here.
                        ##4 Cases
                        ### 1. M equals set, N equals set, doesn't change
                        ### 2. M equals set, N not equals set, change. num = num - 1 # M is also counted, so it is not num - 2
                        ### 3. M not equals, N equals. num = num + 1
                        ### 4. M not equals, N not equals. doesn't change

                        #### case1
                        depend_M_equal = RejectUnlessCharInPosition(ori_set, M)
                        depend_N_equal = RejectUnlessCharInPosition(ori_set, N)
                        depend = deepcopy(read_only_depend)
                        dep_list_case_1 = deepcopy(one_dep_list)
                        dep_list_case_1.prepend_dependency(
                            deepcopy(depend_length_op))
                        dep_list_case_1.prepend_dependency(depend)
                        dep_list_case_1.prepend_dependency(depend_M_equal)
                        dep_list_case_1.prepend_dependency(depend_N_equal)

                        #### case4
                        depend_M_not_equal = RejectUnlessCharInPosition(
                            set(Dicts.classes['z']) - ori_set, M)
                        depend_N_not_equal = RejectUnlessCharInPosition(
                            set(Dicts.classes['z']) - ori_set, N)
                        depend = deepcopy(read_only_depend)
                        dep_list_case_4 = deepcopy(one_dep_list)
                        dep_list_case_4.prepend_dependency(
                            deepcopy(depend_length_op))
                        dep_list_case_4.prepend_dependency(depend)
                        dep_list_case_4.prepend_dependency(depend_M_not_equal)
                        dep_list_case_4.prepend_dependency(depend_N_not_equal)

                        #### case2
                        depend_M_equal = RejectUnlessCharInPosition(ori_set, M)
                        depend_N_not_equal = RejectUnlessCharInPosition(
                            set(Dicts.classes['z']) - ori_set, N)
                        depend = deepcopy(read_only_depend)
                        depend.set_number(depend.get_number() - 1)
                        dep_list_case_2 = deepcopy(one_dep_list)
                        dep_list_case_2.prepend_dependency(
                            deepcopy(depend_length_op))
                        dep_list_case_2.prepend_dependency(depend)
                        dep_list_case_2.prepend_dependency(depend_M_equal)
                        dep_list_case_2.prepend_dependency(depend_N_not_equal)

                        #### case3
                        depend_M_not_equal = RejectUnlessCharInPosition(
                            set(Dicts.classes['z']) - ori_set, M)
                        depend_N_equal = RejectUnlessCharInPosition(ori_set, N)
                        depend = deepcopy(read_only_depend)
                        depend.set_number(depend.get_number() + 1)
                        dep_list_case_3 = deepcopy(one_dep_list)
                        dep_list_case_3.prepend_dependency(
                            deepcopy(depend_length_op))
                        dep_list_case_3.prepend_dependency(depend)
                        dep_list_case_3.prepend_dependency(depend_M_not_equal)
                        dep_list_case_3.prepend_dependency(depend_N_equal)

                        save_split_dep_lists.append_dependency_list(
                            dep_list_case_1)
                        save_split_dep_lists.append_dependency_list(
                            dep_list_case_2)
                        save_split_dep_lists.append_dependency_list(
                            dep_list_case_3)
                        save_split_dep_lists.append_dependency_list(
                            dep_list_case_4)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:

                        ori_pos = read_only_depend.get_position()
                        # N, M >= 0
                        if N >= 0 and M >= 0:

                            if ori_pos >= 0:  #ori_pos >= 0 and NM >=0

                                #ori_pos != N and ori_pos != M
                                if ori_pos != N and ori_pos != M:
                                    #Doesn't matter
                                    dep_list = deepcopy(one_dep_list)
                                    dep_list.prepend_dependency(
                                        deepcopy(read_only_depend))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list)

                                else:
                                    #No op
                                    depend_length_no_op = RejectUnlessLessThanLength(
                                        min_word_length)
                                    no_op_dep_list_1 = deepcopy(one_dep_list)
                                    no_op_dep_list_1.prepend_dependency(
                                        deepcopy(read_only_depend))
                                    no_op_dep_list_1.prepend_dependency(
                                        depend_length_no_op)
                                    save_split_dep_lists.append_dependency_list(
                                        no_op_dep_list_1)

                                    #Op
                                    #Dont' Forget To Test Boundary Cases!
                                    depend_length_op = RejectUnlessGreaterThanLength(
                                        min_word_length - 1)
                                    depend = deepcopy(read_only_depend)
                                    if ori_pos == N:
                                        depend.set_position(M)
                                    elif ori_pos == M:  # use M to replace N, =M do nothing
                                        pass
                                    else:
                                        raise ValueError("Wrong ori_pos")
                                    op_dep_list = deepcopy(one_dep_list)
                                    op_dep_list.prepend_dependency(
                                        depend_length_op)
                                    op_dep_list.prepend_dependency(depend)
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list)

                            else:
                                #No op
                                depend_length_no_op = RejectUnlessLessThanLength(
                                    min_word_length)
                                no_op_dep_list_1 = deepcopy(one_dep_list)
                                no_op_dep_list_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                no_op_dep_list_1.prepend_dependency(
                                    depend_length_no_op)
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list_1)

                                #op
                                depend_length_op = RejectUnlessGreaterThanLength(
                                    min_word_length - 1)
                                #Only affect when word_len == N - ori_pos

                                #case1: word_len == N - ori_pos
                                equal_len = N - ori_pos
                                depend_len_equal_lower = RejectUnlessLessThanLength(
                                    equal_len + 1)
                                depend_len_equal_upper = RejectUnlessGreaterThanLength(
                                    equal_len - 1)
                                depend = deepcopy(read_only_depend)
                                depend.set_position(M)
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(
                                    depend_len_equal_lower)
                                op_dep_list.prepend_dependency(
                                    depend_len_equal_upper)
                                op_dep_list.prepend_dependency(depend)
                                op_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                                #case2: word_len != N - ori_pos. no op
                                depend_len_no_equal_lower = RejectUnlessLessThanLength(
                                    equal_len)
                                depend_len_no_equal_upper = RejectUnlessGreaterThanLength(
                                    equal_len)

                                no_op_dep_list_1 = deepcopy(one_dep_list)
                                no_op_dep_list_1.prepend_dependency(
                                    depend_len_no_equal_lower)
                                no_op_dep_list_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                no_op_dep_list_1.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list_1)

                                no_op_dep_list_2 = deepcopy(one_dep_list)
                                no_op_dep_list_2.prepend_dependency(
                                    depend_len_no_equal_upper)
                                no_op_dep_list_2.prepend_dependency(
                                    deepcopy(read_only_depend))
                                no_op_dep_list_2.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list_2)

                        else:
                            raise ValueError("N in count_period_N_command")

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        M = N - 1

                        if from_idx >= 0:
                            # case -1: no operation for length < max(N,M) + 1
                            no_op_dep_list = deepcopy(one_dep_list)
                            no_op_dep_list.prepend_dependency(
                                RejectUnlessLessThanLength(max(N, M) + 1))
                            no_op_dep_list.prepend_dependency(
                                deepcopy(read_only_depend))
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list)

                            depend_length_op_lower = RejectUnlessGreaterThanLength(
                                max(N, M))

                            # N is in [from, to)
                            if to_idx > N >= from_idx:
                                # if M also in.
                                #if to_idx > M >= from_idx:

                                # 4 cases: M = chars, N = chars; M != chars, N != chars;
                                dep_list_case_1 = deepcopy(one_dep_list)
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, M))
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, N))
                                dep_list_case_1.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number, chars))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                                dep_list_case_2 = deepcopy(one_dep_list)
                                dep_list_case_2.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, M))
                                dep_list_case_2.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, N))
                                dep_list_case_2.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number, chars))
                                dep_list_case_2.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_2)

                                dep_list_case_3 = deepcopy(one_dep_list)
                                dep_list_case_3.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, M))
                                dep_list_case_3.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, N))
                                dep_list_case_3.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number + 1, chars))
                                dep_list_case_3.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_3)

                                dep_list_case_4 = deepcopy(one_dep_list)
                                dep_list_case_4.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, M))
                                dep_list_case_4.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, N))
                                dep_list_case_4.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number - 1, chars))
                                dep_list_case_4.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_4)
                                #else:
                                #pass

                            else:  # doesn't matter
                                one_dep_list.prepend_dependency(
                                    read_only_depend)
                                one_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                        else:
                            # case -1: no operation for length < max(N,M) + 1
                            no_op_dep_list = deepcopy(one_dep_list)
                            no_op_dep_list.prepend_dependency(
                                RejectUnlessLessThanLength(max(N, M) + 1))
                            no_op_dep_list.prepend_dependency(
                                deepcopy(read_only_depend))
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list)

                            depend_length_op_lower = RejectUnlessGreaterThanLength(
                                max(N, M))

                            # Case1: N in [from, to), where N - from_idx >= len > N - to_idx
                            dep_list_case_1 = deepcopy(one_dep_list)
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessCharInPosition(chars, M))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessCharInPosition(chars, N))
                            dep_list_case_1.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number, chars))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_1.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1)

                            dep_list_case_2 = deepcopy(one_dep_list)
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) - chars, M))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) - chars, N))
                            dep_list_case_2.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number, chars))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_2.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_2)

                            dep_list_case_3 = deepcopy(one_dep_list)
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) - chars, M))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessCharInPosition(chars, N))
                            dep_list_case_3.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number + 1, chars))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_3.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_3.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_3)

                            dep_list_case_4 = deepcopy(one_dep_list)
                            dep_list_case_4.prepend_dependency(
                                RejectUnlessCharInPosition(chars, M))
                            dep_list_case_4.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) - chars, N))
                            dep_list_case_4.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number - 1, chars))
                            dep_list_case_4.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - to_idx))
                            dep_list_case_4.prepend_dependency(
                                RejectUnlessLessThanLength(N - from_idx + 1))
                            dep_list_case_4.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_4)

                            # case1.3 & 1.4 doesn't matter
                            dep_list_case_5 = deepcopy(one_dep_list)
                            dep_list_case_5.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_5.prepend_dependency(
                                RejectUnlessLessThanLength(N - to_idx + 1))
                            dep_list_case_5.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_5)

                            dep_list_case_6 = deepcopy(one_dep_list)
                            dep_list_case_6.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_6.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - from_idx))
                            dep_list_case_6.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_6)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_y_N_command(subrule_dependency, rule):
        """ yN  Duplicates first N characters: hello -> (y2) hehello

        Effects on Dependency:
            Reduce length by N, shift positions

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Countable")

        if N == 0:
            return subrule_dependency

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        if read_only_depend.get_number() == 1:
                            #If only check contains
                            #No matter you apply the operation or not.
                            #It does not affect the result of whether contains one or not.
                            no_op_dep_list_1 = deepcopy(one_dep_list)
                            no_op_dep_list_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list_1)

                        else:
                            # Needs to break into multiple mutual exclusive cases
                            # Case1: Length < N or Length > MAX - N, do nothing
                            #No op
                            depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                                RUNTIME_CONFIG['max_password_length'] - N)
                            no_op_dep_list_1 = deepcopy(one_dep_list)
                            no_op_dep_list_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            no_op_dep_list_1.prepend_dependency(
                                depend_length_no_op_greater)
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list_1)

                            # or length < N, do nothing.
                            depend_length_no_op = RejectUnlessLessThanLength(N)
                            no_op_dep_list_2 = deepcopy(one_dep_list)
                            no_op_dep_list_2.prepend_dependency(
                                deepcopy(read_only_depend))
                            no_op_dep_list_2.prepend_dependency(
                                depend_length_no_op)
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list_2)

                            # Case2: Length >= N
                            # Say contains at least 5 a.
                            # Duplicate the first N chars.
                            # case1: first N, 0 a.
                            # case2: first N, 1 a.
                            # ...
                            # case5: first N, 4 a.
                            # case6: first N, >= 5 a.
                            depend_length_op_upper = RejectUnlessLessThanLength(
                                RUNTIME_CONFIG['max_password_length'] - N + 1)
                            depend_length_op_lower = RejectUnlessGreaterThanLength(
                                N - 1)

                            # nums contained by first N
                            for num in range(0, read_only_depend.get_number()):
                                tmp_dep_list = deepcopy(one_dep_list)
                                tmp_dep = deepcopy(read_only_depend)
                                tmp_dep.set_number(tmp_dep.get_number() - num)

                                tmp_dep_list.prepend_dependency(
                                    RejectUnlessFromToContainsExactlyNumberOfChars(
                                        0, N, num,
                                        read_only_depend.get_chars()))
                                tmp_dep_list.prepend_dependency(tmp_dep)
                                tmp_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_upper))
                                tmp_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dep_list)

                            tmp_dep_list = deepcopy(one_dep_list)
                            tmp_dep_list.prepend_dependency(
                                RejectUnlessFromToContainsAtLeastNumberOfChars(
                                    0, N, read_only_depend.get_number(),
                                    read_only_depend.get_chars()))
                            tmp_dep_list.prepend_dependency(
                                depend_length_op_upper)
                            tmp_dep_list.prepend_dependency(
                                depend_length_op_lower)
                            save_split_dep_lists.append_dependency_list(
                                tmp_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        #No op
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length < N, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(N)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N - 1)

                        ori_pos = read_only_depend.get_position()

                        if ori_pos >= 0:

                            # y2 =4a. abc -> ababc. Check c
                            if N * 2 <= ori_pos + 1:
                                depend = deepcopy(read_only_depend)
                                depend.set_position(ori_pos - N)
                                op_dep_list_1 = deepcopy(one_dep_list)
                                op_dep_list_1.prepend_dependency(depend)
                                op_dep_list_1.prepend_dependency(
                                    depend_length_op_upper)
                                op_dep_list_1.prepend_dependency(
                                    depend_length_op_lower)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_1)
                            # y2 =1a. -> =0a

                            # -- N -- N -- rest --
                            # ori_pos + 1 < 2N
                            else:
                                depend = deepcopy(read_only_depend)
                                depend.set_position(ori_pos % N)  #not - N
                                op_dep_list_2 = deepcopy(one_dep_list)
                                op_dep_list_2.prepend_dependency(depend)
                                op_dep_list_2.prepend_dependency(
                                    depend_length_op_upper)
                                op_dep_list_2.prepend_dependency(
                                    depend_length_op_lower)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_2)

                        elif ori_pos < 0:

                            #Doesn't affect if length >= -ori
                            depend = deepcopy(read_only_depend)
                            depend_len_lower = RejectUnlessGreaterThanLength(
                                -ori_pos - 1)

                            op_dep_list_3 = deepcopy(one_dep_list)
                            op_dep_list_3.prepend_dependency(depend)
                            op_dep_list_3.prepend_dependency(
                                deepcopy(depend_len_lower))
                            op_dep_list_3.prepend_dependency(
                                deepcopy(depend_length_op_upper))
                            op_dep_list_3.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list_3)
                            #print(save_split_dep_lists)

                            #word < ori_pos
                            #Does affect
                            #iF Length >= N  and Length < -ori_pos
                            #New_pos = ori_pos + N
                            depend = deepcopy(read_only_depend)
                            depend_len_lower = RejectUnlessGreaterThanLength(N -
                                                                             1)
                            depend_len_upper = RejectUnlessLessThanLength(
                                -ori_pos)

                            depend.set_position(ori_pos + N)
                            op_dep_list_4 = deepcopy(one_dep_list)
                            op_dep_list_4.prepend_dependency(depend)
                            op_dep_list_4.prepend_dependency(
                                deepcopy(depend_len_lower))
                            op_dep_list_4.prepend_dependency(
                                deepcopy(depend_len_upper))
                            op_dep_list_4.prepend_dependency(
                                deepcopy(depend_length_op_upper))
                            op_dep_list_4.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list_4)

                        else:
                            raise ValueError("ValueError: {}".format(ori_pos))

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        #No op
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length = 0, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(N)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N - 1)

                        # Reduce the rejection length
                        depend = deepcopy(read_only_depend)
                        depend.set_len(depend.get_len() - N)
                        op_dep_list = deepcopy(one_dep_list)
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_upper))
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_lower))
                        op_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(op_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        #No op
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length < N, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(N)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP >= N
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N - 1)

                        # Reduce the rejection length
                        depend = deepcopy(read_only_depend)
                        depend.set_len(depend.get_len() - N)
                        op_dep_list = deepcopy(one_dep_list)
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_upper))
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_lower))
                        op_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(op_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        #No op
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length < N, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(N)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP >= N
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N - 1)

                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        if from_idx >= 0:
                            if from_idx >= N:  # doesn't matter, shift window
                                tmp_dep = read_only_depend.make_new(
                                    from_idx - N, to_idx - N, number, chars)

                                tmp_dep_list = deepcopy(one_dep_list)
                                tmp_dep_list.prepend_dependency(tmp_dep)
                                tmp_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                tmp_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_upper))
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dep_list)

                            else:  # part of N is copied, plus original
                                if to_idx > N:
                                    # [from_idx, N) is duplicated
                                    # [N, to_idx) can just shift
                                    for partial_num in range(0, number):
                                        tmp_dep_1 = RejectUnlessFromToContainsExactlyNumberOfChars(
                                            from_idx, N, partial_num, chars)
                                        tmp_dep_2 = read_only_depend.make_new(
                                            0, to_idx - N, number - partial_num,
                                            chars)

                                        tmp_dep_list = deepcopy(one_dep_list)
                                        tmp_dep_list.prepend_dependency(
                                            tmp_dep_1)
                                        tmp_dep_list.prepend_dependency(
                                            tmp_dep_2)
                                        tmp_dep_list.prepend_dependency(
                                            deepcopy(depend_length_op_lower))
                                        tmp_dep_list.prepend_dependency(
                                            deepcopy(depend_length_op_upper))
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dep_list)

                                    tmp_dep_1 = read_only_depend.make_new(
                                        from_idx, N, number, chars)
                                    tmp_dep_2 = read_only_depend.make_new(
                                        0, to_idx - N, 0, chars)

                                    tmp_dep_list = deepcopy(one_dep_list)
                                    tmp_dep_list.prepend_dependency(tmp_dep_1)
                                    tmp_dep_list.prepend_dependency(tmp_dep_2)
                                    tmp_dep_list.prepend_dependency(
                                        deepcopy(depend_length_op_lower))
                                    tmp_dep_list.prepend_dependency(
                                        deepcopy(depend_length_op_upper))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dep_list)

                                else:
                                    # from to are included in N
                                    # so they are mapped to save place in original
                                    tmp_dep_list = deepcopy(one_dep_list)
                                    tmp_dep_list.prepend_dependency(
                                        read_only_depend)
                                    tmp_dep_list.prepend_dependency(
                                        deepcopy(depend_length_op_lower))
                                    tmp_dep_list.prepend_dependency(
                                        deepcopy(depend_length_op_upper))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dep_list)

                        else:
                            # if input_len >= -from, doesn't matter
                            dep_list_case_0 = deepcopy(one_dep_list)
                            dep_list_case_0.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_0.prepend_dependency(
                                RejectUnlessGreaterThanLength(-from_idx - 1))
                            dep_list_case_0.prepend_dependency(
                                deepcopy(depend_length_op_upper))
                            dep_list_case_0.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_0)

                            # else if -from > input_len >= max(N, -from-N), if first N char, else
                            for input_len in range(
                                    max(N, -from_idx - N), -from_idx):
                                #some extra chars in original string, together with first N, have number
                                if -to_idx < input_len:
                                    addition_requirements = []
                                    addition_requirements.append(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    addition_requirements.append(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))
                                    if read_only_depend.dependency_type == 4:
                                        FeatureExtraction.handles_left_right_shares_number_for_exact(
                                            0, to_idx + input_len,
                                            input_len + N + from_idx, N, number,
                                            chars, read_only_depend,
                                            one_dep_list, save_split_dep_lists,
                                            addition_requirements)
                                    else:
                                        FeatureExtraction.handles_left_right_shares_number_for_at_least(
                                            0, to_idx + input_len,
                                            input_len + N + from_idx, N, number,
                                            chars, read_only_depend,
                                            one_dep_list, save_split_dep_lists,
                                            addition_requirements)

                                # shift the window
                                # the [from, to) are in the extra N range
                                # map back
                                else:
                                    dep_list_case_0 = deepcopy(one_dep_list)
                                    depend0_0 = read_only_depend.make_new(
                                        input_len + N + from_idx,
                                        input_len + N + to_idx, number, chars)
                                    dep_list_case_0.prepend_dependency(
                                        depend0_0)
                                    dep_list_case_0.prepend_dependency(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    dep_list_case_0.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_0)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_Y_N_command(subrule_dependency, rule):
        """ YN  Duplicates last N characters: hello -> (Y2) hellolo

        Effects on Dependency:
            reason about the last N chars

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Countable")

        if N == 0:
            return subrule_dependency

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        if read_only_depend.get_number() == 1:
                            #If only check contains
                            #No matter you apply the operation or not.
                            #It does not affect the result of whether contains one or not.
                            no_op_dep_list_1 = deepcopy(one_dep_list)
                            no_op_dep_list_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            save_split_dep_lists.append_dependency_list(
                                no_op_dep_list_1)

                        else:
                            if read_only_depend.get_number() == 1:
                                #If only check contains
                                #No matter you apply the operation or not.
                                #It does not affect the result of whether contains one or not.
                                no_op_dep_list_1 = deepcopy(one_dep_list)
                                no_op_dep_list_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list_1)

                            else:
                                # Case1: Length < N or Length > MAX - N, do nothing
                                #No op
                                depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                                    RUNTIME_CONFIG['max_password_length'] - N)
                                no_op_dep_list_1 = deepcopy(one_dep_list)
                                no_op_dep_list_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                no_op_dep_list_1.prepend_dependency(
                                    depend_length_no_op_greater)
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list_1)

                                # or length < N, do nothing.
                                depend_length_no_op = RejectUnlessLessThanLength(
                                    N)
                                no_op_dep_list_2 = deepcopy(one_dep_list)
                                no_op_dep_list_2.prepend_dependency(
                                    deepcopy(read_only_depend))
                                no_op_dep_list_2.prepend_dependency(
                                    depend_length_no_op)
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list_2)

                                # Case2: Length >= N
                                # Say contains at least 5 a.
                                # Duplicate the first N chars.
                                # case1: first N, 0 a.
                                # case2: first N, 1 a.
                                # ...
                                # case5: first N, 4 a.
                                # case6: first N, >= 5 a.
                                depend_length_op_upper = RejectUnlessLessThanLength(
                                    RUNTIME_CONFIG['max_password_length'] - N +
                                    1)
                                depend_length_op_lower = RejectUnlessGreaterThanLength(
                                    N - 1)

                                # nums contained by last N
                                for num in range(0,
                                                 read_only_depend.get_number()):
                                    tmp_dep_list = deepcopy(one_dep_list)
                                    tmp_dep = deepcopy(read_only_depend)
                                    tmp_dep.set_number(tmp_dep.get_number() -
                                                       num)

                                    tmp_dep_list.prepend_dependency(
                                        RejectUnlessFromToContainsExactlyNumberOfChars(
                                            -N, 0, num,
                                            read_only_depend.get_chars()))
                                    tmp_dep_list.prepend_dependency(tmp_dep)
                                    tmp_dep_list.prepend_dependency(
                                        deepcopy(depend_length_op_upper))
                                    tmp_dep_list.prepend_dependency(
                                        deepcopy(depend_length_op_lower))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dep_list)

                                tmp_dep_list = deepcopy(one_dep_list)
                                tmp_dep_list.prepend_dependency(
                                    RejectUnlessFromToContainsAtLeastNumberOfChars(
                                        -N, 0, read_only_depend.get_number(),
                                        read_only_depend.get_chars()))
                                tmp_dep_list.prepend_dependency(
                                    depend_length_op_upper)
                                tmp_dep_list.prepend_dependency(
                                    depend_length_op_lower)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        #No op
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length < N, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(N)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N - 1)

                        ori_pos = read_only_depend.get_position()

                        if ori_pos >= 0:
                            #Doesn't affect if length >= ori_pos + 1
                            depend = deepcopy(read_only_depend)
                            depend_len_lower = RejectUnlessGreaterThanLength(
                                ori_pos)

                            op_dep_list_3 = deepcopy(one_dep_list)
                            op_dep_list_3.prepend_dependency(depend)
                            op_dep_list_3.prepend_dependency(
                                deepcopy(depend_len_lower))
                            op_dep_list_3.prepend_dependency(
                                deepcopy(depend_length_op_upper))
                            op_dep_list_3.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list_3)
                            #print(save_split_dep_lists)

                            #length < ori_pos + 1
                            #Does affect
                            #iF Length >= N  and Length < ori_pos + 1
                            #New_pos = ori_pos - N
                            depend = deepcopy(read_only_depend)
                            depend_len_lower = RejectUnlessGreaterThanLength(N -
                                                                             1)
                            depend_len_upper = RejectUnlessLessThanLength(
                                ori_pos + 1)

                            depend.set_position(ori_pos - N)
                            op_dep_list_4 = deepcopy(one_dep_list)
                            op_dep_list_4.prepend_dependency(depend)
                            op_dep_list_4.prepend_dependency(
                                deepcopy(depend_len_lower))
                            op_dep_list_4.prepend_dependency(
                                deepcopy(depend_len_upper))
                            op_dep_list_4.prepend_dependency(
                                deepcopy(depend_length_op_upper))
                            op_dep_list_4.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list_4)

                        elif ori_pos < 0:

                            # Y2 =-4a. abc -> abcbc. Check c
                            if N * 2 <= -ori_pos:
                                depend = deepcopy(read_only_depend)
                                depend.set_position(ori_pos + N)
                                op_dep_list_1 = deepcopy(one_dep_list)
                                op_dep_list_1.prepend_dependency(depend)
                                op_dep_list_1.prepend_dependency(
                                    depend_length_op_upper)
                                op_dep_list_1.prepend_dependency(
                                    depend_length_op_lower)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_1)

                            # Y2 =-1a. -> =-1a
                            #  -- rest-- N -- N --
                            #  -ori_pos < 2N
                            else:
                                depend = deepcopy(read_only_depend)
                                if -ori_pos <= N:
                                    depend.set_position(
                                        ori_pos)  # N = 5, -1 ~ -5.Keep it
                                else:
                                    depend.set_position(
                                        ori_pos + N)  # N = 5, -6 - -9 + 5.

                                op_dep_list_2 = deepcopy(one_dep_list)
                                op_dep_list_2.prepend_dependency(depend)
                                op_dep_list_2.prepend_dependency(
                                    depend_length_op_upper)
                                op_dep_list_2.prepend_dependency(
                                    depend_length_op_lower)
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list_2)

                        else:
                            raise ValueError("ValueError: {}".format(ori_pos))

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        #No op
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length = 0, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(N)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N - 1)

                        # Reduce the rejection length
                        depend = deepcopy(read_only_depend)
                        depend.set_len(depend.get_len() - N)
                        op_dep_list = deepcopy(one_dep_list)
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_upper))
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_lower))
                        op_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(op_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        #No op
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length < N, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(N)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP >= N
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N - 1)

                        # Reduce the rejection length
                        depend = deepcopy(read_only_depend)
                        depend.set_len(depend.get_len() - N)
                        op_dep_list = deepcopy(one_dep_list)
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_upper))
                        op_dep_list.prepend_dependency(
                            deepcopy(depend_length_op_lower))
                        op_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(op_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        #No op
                        depend_length_no_op_greater = RejectUnlessGreaterThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(
                            depend_length_no_op_greater)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # or length < N, do nothing.
                        depend_length_no_op = RejectUnlessLessThanLength(N)
                        no_op_dep_list_2 = deepcopy(one_dep_list)
                        no_op_dep_list_2.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_2.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_2)

                        # OP >= N
                        depend_length_op_upper = RejectUnlessLessThanLength(
                            RUNTIME_CONFIG['max_password_length'] - N + 1)
                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N - 1)
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        if from_idx < 0:
                            if N <= -to_idx:  # doesn't matter, shift window
                                tmp_dep = read_only_depend.make_new(
                                    from_idx + N, to_idx + N, number, chars)

                                tmp_dep_list = deepcopy(one_dep_list)
                                tmp_dep_list.prepend_dependency(tmp_dep)
                                tmp_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                tmp_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_upper))
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dep_list)

                            else:  # part of N is copied, plus original
                                if -from_idx > N:
                                    # [from_idx, -N) can just shift
                                    # [-N, to_idx) duplicated -> map to the same place in original
                                    for partial_num in range(0, number):
                                        tmp_dep_1 = RejectUnlessFromToContainsExactlyNumberOfChars(
                                            -N, to_idx, partial_num, chars)
                                        tmp_dep_2 = read_only_depend.make_new(
                                            from_idx + N, 0,
                                            number - partial_num, chars)

                                        tmp_dep_list = deepcopy(one_dep_list)
                                        tmp_dep_list.prepend_dependency(
                                            tmp_dep_1)
                                        tmp_dep_list.prepend_dependency(
                                            tmp_dep_2)
                                        tmp_dep_list.prepend_dependency(
                                            deepcopy(depend_length_op_lower))
                                        tmp_dep_list.prepend_dependency(
                                            deepcopy(depend_length_op_upper))
                                        save_split_dep_lists.append_dependency_list(
                                            tmp_dep_list)

                                    tmp_dep_1 = read_only_depend.make_new(
                                        -N, to_idx, number, chars)
                                    tmp_dep_2 = read_only_depend.make_new(
                                        from_idx + N, 0, 0, chars)

                                    tmp_dep_list = deepcopy(one_dep_list)
                                    tmp_dep_list.prepend_dependency(tmp_dep_1)
                                    tmp_dep_list.prepend_dependency(tmp_dep_2)
                                    tmp_dep_list.prepend_dependency(
                                        deepcopy(depend_length_op_lower))
                                    tmp_dep_list.prepend_dependency(
                                        deepcopy(depend_length_op_upper))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dep_list)

                                else:
                                    # from to are included in N
                                    # so they are mapped to save place in original
                                    tmp_dep_list = deepcopy(one_dep_list)
                                    tmp_dep_list.prepend_dependency(
                                        read_only_depend)
                                    tmp_dep_list.prepend_dependency(
                                        deepcopy(depend_length_op_lower))
                                    tmp_dep_list.prepend_dependency(
                                        deepcopy(depend_length_op_upper))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dep_list)

                        # from_idx > 0
                        else:
                            # if input_len >= to_idx, doesn't matter
                            dep_list_case_0 = deepcopy(one_dep_list)
                            dep_list_case_0.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_0.prepend_dependency(
                                RejectUnlessGreaterThanLength(to_idx - 1))
                            dep_list_case_0.prepend_dependency(
                                deepcopy(depend_length_op_upper))
                            dep_list_case_0.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_0)

                            # else if to_idx > input_len >= max(1, to_idx-N), if last N char, else
                            for input_len in range(max(N, to_idx - N), to_idx):

                                #some extra chars in original string, together with last N, have number
                                if from_idx < input_len:
                                    addition_requirements = []
                                    addition_requirements.append(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    addition_requirements.append(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))
                                    if read_only_depend.dependency_type == 4:
                                        FeatureExtraction.handles_left_right_shares_number_for_exact(
                                            from_idx, input_len, input_len - N,
                                            to_idx - N, number, chars,
                                            read_only_depend, one_dep_list,
                                            save_split_dep_lists,
                                            addition_requirements)
                                    else:
                                        FeatureExtraction.handles_left_right_shares_number_for_at_least(
                                            from_idx, input_len, input_len - N,
                                            to_idx - N, number, chars,
                                            read_only_depend, one_dep_list,
                                            save_split_dep_lists,
                                            addition_requirements)

                                # shift the window
                                # the [from, to) are in the extra N range
                                # map back
                                else:
                                    dep_list_case_0 = deepcopy(one_dep_list)
                                    depend0_0 = read_only_depend.make_new(
                                        from_idx - N, to_idx - N, number, chars)
                                    dep_list_case_0.prepend_dependency(
                                        depend0_0)
                                    dep_list_case_0.prepend_dependency(
                                        RejectUnlessLessThanLength(input_len +
                                                                   1))
                                    dep_list_case_0.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            input_len - 1))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_0)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_x_N_M_command_HC(subrule_dependency, rule):
        """ xNM Extracts M chars, starting at position N

        Effects on Dependency:
            depends on the char from M to M + N
            HC logic: pos < length && pos+pos2 <= length

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        try:
            N = convert_str_length_to_int(rule[1])
            M = convert_str_length_to_int(rule[2])
        except:
            raise NotCountableException("Not Countable")

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if read_only_depend.dependency_type == 1:
                        # Case1, length <= N, do nothing
                        depend_length_no_op = RejectUnlessLessThanLength(
                            max(N + 1, N + M))
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # special case
                        if M == 0:
                            # Rejected
                            if read_only_depend.dependency_type == 2:
                                rej_dep_list = deepcopy(one_dep_list)
                                rej_dep_list.prepend_dependency(
                                    RejectUnlessLessThanLength(0))
                                continue
                            # Satisfied
                            else:
                                rej_dep_list = deepcopy(one_dep_list)
                                rej_dep_list.prepend_dependency(
                                    RejectUnlessGreaterThanLength(-1))
                                continue

                        # Case2, from 0 to N has at most read_only_depend.get_number() number - 1
                        for number in range(read_only_depend.get_number()):
                            op_dep_list_1 = deepcopy(one_dep_list)
                            op_dep_list_1.prepend_dependency(
                                RejectUnlessFromToContainsExactlyNumberOfChars(
                                    N, N + M, number,
                                    read_only_depend.get_chars()))
                            op_dep_list_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(
                                    max(N, N + M - 1)))
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list_1)

                    elif read_only_depend.dependency_type == 2:
                        # Case1, length <= N, do nothing
                        depend_length_no_op = RejectUnlessLessThanLength(
                            max(N + 1, N + M))
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # special case
                        if M == 0:
                            # Rejected
                            if read_only_depend.dependency_type == 2:
                                rej_dep_list = deepcopy(one_dep_list)
                                rej_dep_list.prepend_dependency(
                                    RejectUnlessLessThanLength(0))
                                continue
                            # Satisfied
                            else:
                                rej_dep_list = deepcopy(one_dep_list)
                                rej_dep_list.prepend_dependency(
                                    RejectUnlessGreaterThanLength(-1))
                                continue

                        # Case2, from 0 to N has at least that number
                        op_dep_list_1 = deepcopy(one_dep_list)
                        op_dep_list_1.prepend_dependency(
                            RejectUnlessFromToContainsAtLeastNumberOfChars(
                                N, N + M, read_only_depend.get_number(),
                                read_only_depend.get_chars()))
                        op_dep_list_1.prepend_dependency(
                            RejectUnlessGreaterThanLength(max(N, N + M - 1)))
                        save_split_dep_lists.append_dependency_list(
                            op_dep_list_1)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        # Case1, length < M+N, do nothing
                        depend_length_no_op = RejectUnlessLessThanLength(
                            max(N + 1, N + M))
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        if M == 0:
                            # Rejected
                            rej_dep_list = deepcopy(one_dep_list)
                            rej_dep_list.prepend_dependency(
                                RejectUnlessLessThanLength(0))
                            continue

                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            max(N, N + M - 1))
                        # xNM set len to M (for len >= M + N). Char at pos also requires len >= pos + 1
                        # So we have that

                        # Impossible
                        ori_pos = read_only_depend.get_position()

                        if ori_pos >= 0:
                            # valid M
                            if M >= ori_pos + 1:
                                one_dep_list.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        read_only_depend.get_chars(),
                                        ori_pos + N))
                                one_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                            # rejected
                            else:
                                pass

                        else:
                            # valid M
                            if M >= -ori_pos:
                                one_dep_list.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        read_only_depend.get_chars(),
                                        ori_pos + N + M))
                                one_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                            # rejected
                            else:
                                pass

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        # Case1, length < M+N, do nothing
                        depend_length_no_op = RejectUnlessLessThanLength(
                            max(N + 1, N + M))
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            max(N, N + M - 1))

                        # case1: say x?6, everything = 6, if require < 7 or require < 8, satisfy
                        if read_only_depend.get_len() >= M + 1:
                            # Satisfy
                            depend = deepcopy(read_only_depend)
                            depend.set_len(
                                RUNTIME_CONFIG['max_password_length'] + 1)
                            op_dep_list = deepcopy(one_dep_list)
                            op_dep_list.prepend_dependency(depend)
                            op_dep_list.prepend_dependency(
                                depend_length_op_lower)
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list)

                        # case2: say x?6, everything = 6, if require < 6, rejected
                        else:
                            pass

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        # Case1, length < M+N, do nothing
                        depend_length_no_op = RejectUnlessLessThanLength(
                            max(N + 1, N + M))
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            max(N, N + M - 1))

                        # case1: say '6, everything = 6, if require > 6, reject
                        if M <= read_only_depend.get_len():
                            # Reject
                            depend = deepcopy(read_only_depend)
                            depend.set_len(
                                RUNTIME_CONFIG['max_password_length'] + 1)
                            op_dep_list = deepcopy(one_dep_list)
                            op_dep_list.prepend_dependency(depend)
                            op_dep_list.prepend_dependency(
                                depend_length_op_lower)
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list)

                        # case2: say '6, if require > 5, accept
                        else:
                            depend = deepcopy(read_only_depend)
                            depend.set_len(-1)
                            op_dep_list = deepcopy(one_dep_list)
                            op_dep_list.prepend_dependency(depend)
                            op_dep_list.prepend_dependency(
                                depend_length_op_lower)
                            save_split_dep_lists.append_dependency_list(
                                op_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        # Case1, length < M+N, do nothing
                        depend_length_no_op = RejectUnlessLessThanLength(
                            max(N + 1, N + M))
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        if M == 0:  # rejected
                            rej_dep_list = deepcopy(one_dep_list)
                            rej_dep_list.prepend_dependency(
                                RejectUnlessLessThanLength(0))
                            continue

                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            max(N, N + M - 1))

                        from_idx = read_only_depend.get_from()
                        to_idx = read_only_depend.get_to()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        if from_idx >= 0:
                            # this requires len >= to_idx, xNM requires >= N + M and set len to M.
                            # case1: doesn't change anything
                            if M >= to_idx:
                                one_dep_list.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx + N, to_idx + N, number,
                                        chars))
                                one_dep_list.prepend_dependency(
                                    depend_length_op_lower)
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                            # case2: Rejected
                            else:
                                pass

                        else:
                            # this requires len >= -from_idx, 'N requires >= N and set len to N.
                            if M >= -from_idx:
                                one_dep_list.prepend_dependency(
                                    read_only_depend.make_new(
                                        M + N + from_idx, M + N + to_idx,
                                        number, chars))
                                one_dep_list.prepend_dependency(
                                    depend_length_op_lower)
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                            # rejected.
                            else:
                                pass

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_x_N_M_command_JTR(subrule_dependency, rule):
        """ xNM Extracts M chars, starting at position N

        Effects on Dependency:
            JtR logic: pos < length
                case1: reject if length <= N
                case2: XN(length-N) if N < length < N + M
                case3: XNM if length >= N + M


        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        try:
            N = convert_str_length_to_int(rule[1])
            M = convert_str_length_to_int(rule[2])
        except:
            raise NotCountableException("Not Countable")

        #### Cases start here
        # Case 0: <=N, reject
        # Call other funcs to handle
        #sub_rule_dependency_1 = FeatureExtraction.extract_colon_command(deepcopy(subrule_dependency), ":")
        # Add case restriction
        #sub_rule_dependency_1.prepend_dependency_to_all_lists(RejectUnlessLessThanLength(N+1))
        #ret_val.merge(sub_rule_dependency_1)

        # Case 1: N < length < N + M
        # xN(length-N)
        for input_len in range(N + 1, N + M):
            sub_rule_dependency_2 = FeatureExtraction.extract_x_N_M_command_HC(
                deepcopy(subrule_dependency), ["x", N, input_len - N])
            # Add case restriction
            sub_rule_dependency_2.prepend_dependency_to_all_lists(
                RejectUnlessGreaterThanLength(input_len - 1))
            sub_rule_dependency_2.prepend_dependency_to_all_lists(
                RejectUnlessLessThanLength(input_len + 1))
            ret_val.merge(sub_rule_dependency_2)

        # Case 2: length >= N + M
        # xNM
        sub_rule_dependency_3 = FeatureExtraction.extract_x_N_M_command_HC(
            deepcopy(subrule_dependency), ["x", N, M])
        # Add case restriction
        sub_rule_dependency_3.prepend_dependency_to_all_lists(
            RejectUnlessGreaterThanLength(N + M - 1))

        ret_val.merge(sub_rule_dependency_3)

        return ret_val

    @staticmethod
    def extract_x_N_M_command(subrule_dependency, rule):
        """ xNM Extracts M chars, starting at position N

        Effects on Dependency:
            JtR logic: pos < length
            HC logic: pos < length && pos+pos2 <= length

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        if RUNTIME_CONFIG.is_jtr():
            return FeatureExtraction.extract_x_N_M_command_JTR(
                subrule_dependency, rule)
        else:
            return FeatureExtraction.extract_x_N_M_command_HC(
                subrule_dependency, rule)

    @staticmethod
    def extract_o_N_X_command(subrule_dependency, rule):
        """ oNX Overwrites char at position N with char X

        Effects on Dependency:
            depends on char at N

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Countable")

        X = rule[2]

        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        min_word_length = N + 1 if N >= 0 else -N

                        ori_set = read_only_depend.get_chars()
                        ori_number = read_only_depend.get_number()

                        # case1: len < min_word_length. Doesn't do anything
                        depend1 = RejectUnlessLessThanLength(min_word_length)
                        depend1_1 = deepcopy(
                            read_only_depend)  #Doesn't affect the old
                        tmp_dependency_list1 = deepcopy(one_dep_list)
                        tmp_dependency_list1.prepend_dependency(depend1)
                        tmp_dependency_list1.prepend_dependency(depend1_1)

                        # case2: len > min_word_length - 1. Char at N is in check_set. (which means overstirke removes one candidate)
                        depend2 = RejectUnlessGreaterThanLength(
                            min_word_length - 1)
                        depend2_1 = RejectUnlessCharInPosition(ori_set, N)

                        if X in ori_set:  #Deosn't matter.
                            depend2_2 = read_only_depend.make_new(
                                ori_set, ori_number)
                        else:
                            depend2_2 = read_only_depend.make_new(
                                ori_set, ori_number + 1)

                        tmp_dependency_list2 = deepcopy(one_dep_list)
                        tmp_dependency_list2.prepend_dependency(depend2)
                        tmp_dependency_list2.prepend_dependency(depend2_1)
                        tmp_dependency_list2.prepend_dependency(depend2_2)

                        # case3: len > min_word_length - 1. Char at N is not in check_set. (which means overstirke dose not remove one candidate)
                        depend3 = RejectUnlessGreaterThanLength(
                            min_word_length - 1)
                        depend3_1 = RejectUnlessCharInPosition(
                            set(Dicts.classes['z']) - ori_set, N)

                        if X in ori_set:  #Deosn't matter.
                            depend3_2 = read_only_depend.make_new(
                                ori_set, ori_number - 1)
                        else:  #Not -> Not mapping. Doesn't matter
                            depend3_2 = read_only_depend.make_new(
                                ori_set, ori_number)

                        tmp_dependency_list3 = deepcopy(one_dep_list)
                        tmp_dependency_list3.prepend_dependency(depend3)
                        tmp_dependency_list3.prepend_dependency(depend3_1)
                        tmp_dependency_list3.prepend_dependency(depend3_2)

                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list1)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list2)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list3)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:

                        #If Length < Min Op Length.
                        depend0_0 = RejectUnlessLessThanLength(
                            N + 1)  # The length from N
                        depend0_1 = deepcopy(read_only_depend)
                        tmp_dependency_list0 = deepcopy(one_dep_list)
                        tmp_dependency_list0.prepend_dependency(depend0_0)
                        tmp_dependency_list0.prepend_dependency(depend0_1)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list0)

                        #Length >= N
                        depend_length_op_min_length = RejectUnlessGreaterThanLength(
                            N)

                        ori_pos = read_only_depend.get_position()
                        ori_set = read_only_depend.get_chars()

                        if ori_pos >= 0 and N >= 0:
                            if ori_pos != N:  #Doesn't change anything
                                tmp_dependency_list1 = deepcopy(one_dep_list)
                                depend1_1 = deepcopy(read_only_depend)
                                tmp_dependency_list1.prepend_dependency(
                                    depend1_1)
                                tmp_dependency_list1.prepend_dependency(
                                    deepcopy(depend_length_op_min_length))
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list1)

                            else:  #Either reject or satisfy
                                if X in ori_set:
                                    #Satisfied
                                    tmp_dependency_list1 = deepcopy(
                                        one_dep_list)
                                    tmp_dependency_list1.prepend_dependency(
                                        deepcopy(depend_length_op_min_length))
                                    save_split_dep_lists.append_dependency_list(
                                        tmp_dependency_list1)
                                else:  #Rejected. Add Nothing
                                    pass

                        elif ori_pos < 0 and N >= 0:
                            #hit_len = N - ori_pos
                            hit_length = N - ori_pos
                            #If Length == hit_length
                            depend2_0 = RejectUnlessLessThanLength(hit_length +
                                                                   1)
                            depend2_1 = RejectUnlessGreaterThanLength(
                                hit_length - 1)
                            if X in ori_set:
                                #Satisfied
                                tmp_dependency_list2 = deepcopy(one_dep_list)
                                tmp_dependency_list2.prepend_dependency(
                                    deepcopy(depend_length_op_min_length))
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_0)
                                tmp_dependency_list2.prepend_dependency(
                                    depend2_1)
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dependency_list2)
                            else:  #Rejected. Add Nothing
                                pass

                            #If Length < hit_length. Doesn't matter
                            depend3_0 = RejectUnlessLessThanLength(hit_length)
                            tmp_dependency_list3 = deepcopy(one_dep_list)
                            tmp_dependency_list3.prepend_dependency(depend3_0)
                            tmp_dependency_list3.prepend_dependency(
                                deepcopy(depend_length_op_min_length))
                            tmp_dependency_list3.prepend_dependency(
                                deepcopy(read_only_depend))
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list3)

                            #If Length > hit_length. Doesn't matter
                            depend4_0 = RejectUnlessGreaterThanLength(
                                hit_length)
                            tmp_dependency_list4 = deepcopy(one_dep_list)
                            tmp_dependency_list4.prepend_dependency(depend4_0)
                            tmp_dependency_list4.prepend_dependency(
                                deepcopy(depend_length_op_min_length))
                            tmp_dependency_list4.prepend_dependency(
                                deepcopy(read_only_depend))
                            save_split_dep_lists.append_dependency_list(
                                tmp_dependency_list4)

                        # N < 0 not supported (Memorization)
                        else:  #Bug?
                            raise ValueError(
                                "Ended Up In Stange Position: {}\t{}".format(
                                    ori_pos, N))

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend = deepcopy(read_only_depend)

                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend = deepcopy(read_only_depend)

                        tmp_dependency_list = deepcopy(one_dep_list)
                        tmp_dependency_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            tmp_dependency_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        # no op
                        depend_length_no_op = RejectUnlessLessThanLength(N + 1)
                        no_op_dep_list = deepcopy(one_dep_list)
                        no_op_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list)

                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N)

                        if from_idx >= 0:
                            # the N'th char is not X
                            # case1: N in the range of [from,to)
                            if to_idx > N >= from_idx:
                                if X in chars:
                                    # case1.1: if x in chars, original in chars. Doesn't matter
                                    dep_list_case_0 = deepcopy(one_dep_list)
                                    dep_list_case_0.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx, number, chars))
                                    dep_list_case_0.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, N))
                                    dep_list_case_0.prepend_dependency(
                                        deepcopy(depend_length_op_lower))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_0)

                                    # case1.1: if x in chars, original not in chars. -1
                                    dep_list_case_1 = deepcopy(one_dep_list)
                                    dep_list_case_1.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx, number - 1,
                                            chars))
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars, N))
                                    dep_list_case_1.prepend_dependency(
                                        deepcopy(depend_length_op_lower))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_1)

                                else:
                                    # case1.2: if x not in chars, original in chars.
                                    dep_list_case_0 = deepcopy(one_dep_list)
                                    dep_list_case_0.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx, number + 1,
                                            chars))
                                    dep_list_case_0.prepend_dependency(
                                        RejectUnlessCharInPosition(chars, N))
                                    dep_list_case_0.prepend_dependency(
                                        deepcopy(depend_length_op_lower))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_0)

                                    # case1.2: if x not in chars, original not in chars.
                                    dep_list_case_1 = deepcopy(one_dep_list)
                                    dep_list_case_1.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx, number, chars))
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars, N))
                                    dep_list_case_1.prepend_dependency(
                                        deepcopy(depend_length_op_lower))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_1)

                            # case2: N outside [From,to)
                            else:
                                dep_list_case_0 = deepcopy(one_dep_list)
                                dep_list_case_0.prepend_dependency(
                                    deepcopy(read_only_depend))
                                dep_list_case_0.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_0)

                        else:
                            # same old thing, see if it falls in the range
                            # case1: N + 1 - to_idx  <= len < N + 1 - from_idx

                            if X in chars:
                                # case1.1: if x in chars, original in chars
                                dep_list_case_0 = deepcopy(one_dep_list)
                                dep_list_case_0.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, N))
                                dep_list_case_0.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number, chars))
                                dep_list_case_0.prepend_dependency(
                                    RejectUnlessLessThanLength(N - from_idx +
                                                               1))
                                dep_list_case_0.prepend_dependency(
                                    RejectUnlessGreaterThanLength(N - to_idx))
                                dep_list_case_0.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_0)

                                # case1.1: if x in chars, original not in chars
                                dep_list_case_1 = deepcopy(one_dep_list)
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, N))
                                dep_list_case_1.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number - 1, chars))
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessLessThanLength(N - from_idx +
                                                               1))
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessGreaterThanLength(N - to_idx))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                            else:
                                # case1.1: if x not in chars, original in chars
                                dep_list_case_0 = deepcopy(one_dep_list)
                                dep_list_case_0.prepend_dependency(
                                    RejectUnlessCharInPosition(chars, N))
                                dep_list_case_0.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number + 1, chars))
                                dep_list_case_0.prepend_dependency(
                                    RejectUnlessLessThanLength(N - from_idx +
                                                               1))
                                dep_list_case_0.prepend_dependency(
                                    RejectUnlessGreaterThanLength(N - to_idx))
                                dep_list_case_0.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_0)

                                # case1.1: if x not in chars, original not in chars
                                dep_list_case_1 = deepcopy(one_dep_list)
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        set(Dicts.classes['z']) - chars, N))
                                dep_list_case_1.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx, to_idx, number, chars))
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessLessThanLength(N - from_idx +
                                                               1))
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessGreaterThanLength(N - to_idx))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                            # case2: len >= N - from_idx + 1, doens't matter
                            dep_list_case_1 = deepcopy(one_dep_list)
                            dep_list_case_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(N - from_idx))
                            dep_list_case_1.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1)

                            # case3: len < N - to_idx + 1, shift window.
                            dep_list_case_2 = deepcopy(one_dep_list)
                            dep_list_case_2.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessLessThanLength(N - to_idx + 1))
                            dep_list_case_2.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_2)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def handles_left_right_shares_number_for_exact(left_from,
                                                   left_to,
                                                   right_from,
                                                   right_to,
                                                   number,
                                                   chars,
                                                   read_only_depend,
                                                   one_dep_list,
                                                   save_split_dep_lists,
                                                   additional_dep_lists=[]):
        """ handles the case that two ranges together should have exactly some number of chars

        range 1: [left_from, left_to)
        range 2: [right_from, right_to)
        total number required: number
        """
        # Requirement: x + y == 4

        if left_from != left_to and right_from != right_to:
            #First check if two ranges overlap
            left_range = set(range(left_from, left_to))
            right_range = set(range(right_from, right_to))
            inter_range = left_range.intersection(right_range)
            if left_range == right_range:  # same thing, divide by two
                if number % 2 != 0:  #rejected
                    return
                tmp_one_dep_list = deepcopy(one_dep_list)
                tmp_one_dep_list.prepend_dependency(
                    RejectUnlessFromToContainsExactlyNumberOfChars(
                        left_from, left_to, number // 2, chars))
                for v in additional_dep_lists:
                    tmp_one_dep_list.prepend_dependency(deepcopy(v))
                save_split_dep_lists.append_dependency_list(tmp_one_dep_list)

            # x + y == 4 & x >= y; => x >= 2 => (x = 2, y = 2; x = 3, y = 1; x = 4, y = 0)
            elif left_range.issubset(
                    right_range
            ):  # super set always has the same dependency, subset iterate.
                #print("right major")
                for right_share in range(
                        math.ceil(number / 2),
                        number):  # right share at least this number.
                    #print(right_share)
                    left_share = number - right_share
                    # a = 4, b >= 1; ..
                    tmp_one_dep_list = deepcopy(one_dep_list)
                    tmp_one_dep_list.prepend_dependency(
                        RejectUnlessFromToContainsExactlyNumberOfChars(
                            left_from, left_to, left_share, chars))
                    # right side stays the same dependency
                    tmp_one_dep_list.prepend_dependency(
                        RejectUnlessFromToContainsExactlyNumberOfChars(
                            right_from, right_to, right_share, chars))
                    for v in additional_dep_lists:
                        tmp_one_dep_list.prepend_dependency(deepcopy(v))
                    save_split_dep_lists.append_dependency_list(
                        tmp_one_dep_list)

                # a >= 5;
                tmp_one_dep_list = deepcopy(one_dep_list)
                # left side iterates
                tmp_one_dep_list.prepend_dependency(
                    RejectUnlessFromToContainsExactlyNumberOfChars(
                        left_from, left_to, 0, chars))
                # right side stays the same dependency
                tmp_one_dep_list.prepend_dependency(
                    RejectUnlessFromToContainsExactlyNumberOfChars(
                        right_from, right_to, number, chars))
                for v in additional_dep_lists:
                    tmp_one_dep_list.prepend_dependency(deepcopy(v))
                save_split_dep_lists.append_dependency_list(tmp_one_dep_list)

            # x + y == 4 & x >= y; => x >= 2 => (x = 2, y = 2; x = 3, y = 1; x = 4, y = 0)
            elif right_range.issubset(
                    left_range
            ):  # super set always has the same dependency, subset iterate.
                for left_share in range(
                        math.ceil(number / 2),
                        number):  # right share at least this number.
                    right_share = number - left_share
                    # a = 4, b = 1; ..
                    tmp_one_dep_list = deepcopy(one_dep_list)
                    tmp_one_dep_list.prepend_dependency(
                        RejectUnlessFromToContainsExactlyNumberOfChars(
                            right_from, right_to, right_share, chars))
                    # right side stays the same dependency
                    tmp_one_dep_list.prepend_dependency(
                        RejectUnlessFromToContainsExactlyNumberOfChars(
                            left_from, left_to, left_share, chars))
                    for v in additional_dep_lists:
                        tmp_one_dep_list.prepend_dependency(deepcopy(v))
                    save_split_dep_lists.append_dependency_list(
                        tmp_one_dep_list)

                # a == 5;
                tmp_one_dep_list = deepcopy(one_dep_list)
                # left side iterates
                tmp_one_dep_list.prepend_dependency(
                    RejectUnlessFromToContainsExactlyNumberOfChars(
                        right_from, right_to, 0, chars))
                # right side stays the same dependency
                tmp_one_dep_list.prepend_dependency(
                    RejectUnlessFromToContainsExactlyNumberOfChars(
                        left_from, left_to, number, chars))
                for v in additional_dep_lists:
                    tmp_one_dep_list.prepend_dependency(deepcopy(v))
                save_split_dep_lists.append_dependency_list(tmp_one_dep_list)

            elif len(inter_range
                    ) != 0:  # there are non-trivial intersection, three parts?
                new_left_from = min(left_range - inter_range)
                new_left_to = max(left_range - inter_range) + 1
                new_right_from = min(right_range - inter_range)
                new_right_to = max(right_range - inter_range) + 1

                # first, check how many in the intersection, break the range
                for chars_in_intersect in range(
                        0,
                        len(left_range.intersection(right_range)) + 1):
                    dep_chars_in_intersect = RejectUnlessFromToContainsExactlyNumberOfChars(
                        min(inter_range),
                        max(inter_range) + 1, chars_in_intersect, chars)
                    additional_dep_lists.append(dep_chars_in_intersect)
                    # resurively handles this
                    if number - chars_in_intersect * 2 >= 0:
                        FeatureExtraction.handles_left_right_shares_number_for_exact(
                            new_left_from, new_left_to, new_right_from,
                            new_right_to, number - chars_in_intersect * 2,
                            chars, read_only_depend, one_dep_list,
                            save_split_dep_lists, additional_dep_lists)

            else:
                # x + y == 2 => (x == 2, y == 0; x == 1, y == 1; x == 0, y == 2)
                for left_share in range(0, number + 1):
                    right_share = number - left_share  # get x, y value

                    tmp_one_dep_list = deepcopy(one_dep_list)
                    tmp_one_dep_list.prepend_dependency(
                        RejectUnlessFromToContainsExactlyNumberOfChars(
                            left_from, left_to, left_share, chars))
                    tmp_one_dep_list.prepend_dependency(
                        RejectUnlessFromToContainsExactlyNumberOfChars(
                            right_from, right_to, right_share, chars))
                    for v in additional_dep_lists:
                        tmp_one_dep_list.prepend_dependency(deepcopy(v))
                    save_split_dep_lists.append_dependency_list(
                        tmp_one_dep_list)

        # there's only one side
        elif left_from == left_to and right_from != right_to:
            tmp_one_dep_list = deepcopy(one_dep_list)
            tmp_one_dep_list.prepend_dependency(
                RejectUnlessFromToContainsExactlyNumberOfChars(
                    right_from, right_to, number, chars))
            for v in additional_dep_lists:
                tmp_one_dep_list.prepend_dependency(deepcopy(v))
            save_split_dep_lists.append_dependency_list(tmp_one_dep_list)

        # there's only one side
        elif left_from != left_to and right_from == right_to:
            tmp_one_dep_list = deepcopy(one_dep_list)
            tmp_one_dep_list.prepend_dependency(
                RejectUnlessFromToContainsExactlyNumberOfChars(
                    left_from, left_to, number, chars))
            for v in additional_dep_lists:
                tmp_one_dep_list.prepend_dependency(deepcopy(v))
            save_split_dep_lists.append_dependency_list(tmp_one_dep_list)

        else:
            raise Exception("Should fall into here")

    @staticmethod
    def handles_left_right_shares_number_for_at_least(left_from,
                                                      left_to,
                                                      right_from,
                                                      right_to,
                                                      number,
                                                      chars,
                                                      read_only_depend,
                                                      one_dep_list,
                                                      save_split_dep_lists,
                                                      additional_dep_lists=[]):
        """handles the case that two ranges together should have at least some number of chars

        range 1: [left_from, left_to)
        range 2: [right_from, right_to)
        total number required: number
        """
        # x + y >= 4
        if left_from != left_to and right_from != right_to:
            #First check if two ranges overlap
            left_range = set(range(left_from, left_to))
            right_range = set(range(right_from, right_to))
            inter_range = left_range.intersection(right_range)

            if left_range == right_range:  # same thing, divide by two
                tmp_one_dep_list = deepcopy(one_dep_list)
                tmp_one_dep_list.prepend_dependency(
                    RejectUnlessFromToContainsAtLeastNumberOfChars(
                        left_from, left_to, (number + 1) // 2, chars))
                for v in additional_dep_lists:
                    tmp_one_dep_list.prepend_dependency(deepcopy(v))
                save_split_dep_lists.append_dependency_list(tmp_one_dep_list)

            # x + y >= 4 & x >= y; => x >= 2 => (x = 2, y >= 2; x = 3, y >= 1; x >= 4, no requirement on y)
            elif left_range.issubset(
                    right_range
            ):  # super set always has the same dependency, subset iterate.
                for right_share in range(
                        math.ceil(number / 2),
                        number):  # right share at least this number.
                    left_share = number - right_share
                    tmp_one_dep_list = deepcopy(one_dep_list)
                    # x = 2
                    tmp_one_dep_list.prepend_dependency(
                        RejectUnlessFromToContainsExactlyNumberOfChars(
                            right_from, right_to, right_share, chars))
                    # y >= 2
                    tmp_one_dep_list.prepend_dependency(
                        RejectUnlessFromToContainsAtLeastNumberOfChars(
                            left_from, left_to, left_share, chars))
                    for v in additional_dep_lists:
                        tmp_one_dep_list.prepend_dependency(deepcopy(v))
                    save_split_dep_lists.append_dependency_list(
                        tmp_one_dep_list)

                # x >= 4;
                tmp_one_dep_list = deepcopy(one_dep_list)
                tmp_one_dep_list.prepend_dependency(
                    RejectUnlessFromToContainsAtLeastNumberOfChars(
                        right_from, right_to, number, chars))
                for v in additional_dep_lists:
                    tmp_one_dep_list.prepend_dependency(deepcopy(v))
                save_split_dep_lists.append_dependency_list(tmp_one_dep_list)

            # x + y >= 4 & x >= y; => x >= 2 => (x = 2, y >= 2; x = 3, y >= 1; x >= 4, no requirement on y)
            elif right_range.issubset(
                    left_range
            ):  # super set always has the same dependency, subset iterate.
                for left_share in range(
                        math.ceil(number / 2),
                        number):  # right share at least this number.
                    right_share = number - left_share
                    tmp_one_dep_list = deepcopy(one_dep_list)
                    # x = 2
                    tmp_one_dep_list.prepend_dependency(
                        RejectUnlessFromToContainsExactlyNumberOfChars(
                            left_from, left_to, left_share, chars))
                    # y >= 2
                    tmp_one_dep_list.prepend_dependency(
                        RejectUnlessFromToContainsAtLeastNumberOfChars(
                            right_from, right_to, right_share, chars))
                    for v in additional_dep_lists:
                        tmp_one_dep_list.prepend_dependency(deepcopy(v))
                    save_split_dep_lists.append_dependency_list(
                        tmp_one_dep_list)

                # x >= 4;
                tmp_one_dep_list = deepcopy(one_dep_list)
                tmp_one_dep_list.prepend_dependency(
                    RejectUnlessFromToContainsAtLeastNumberOfChars(
                        left_from, left_to, number, chars))
                for v in additional_dep_lists:
                    tmp_one_dep_list.prepend_dependency(deepcopy(v))
                save_split_dep_lists.append_dependency_list(tmp_one_dep_list)

            elif len(inter_range
                    ) != 0:  # there are non-trivial intersection, three parts?
                new_left_from = min(left_range - inter_range)
                new_left_to = max(left_range - inter_range) + 1
                new_right_from = min(right_range - inter_range)
                new_right_to = max(right_range - inter_range) + 1

                # first, check how many in the intersection, break the range
                for chars_in_intersect in range(
                        0,
                        len(left_range.intersection(right_range)) + 1):
                    dep_chars_in_intersect = RejectUnlessFromToContainsExactlyNumberOfChars(
                        min(inter_range),
                        max(inter_range) + 1, chars_in_intersect, chars)
                    additional_dep_lists.append(dep_chars_in_intersect)
                    # resurively handles this
                    if number - chars_in_intersect * 2 >= 0:
                        FeatureExtraction.handles_left_right_shares_number_for_at_least(
                            new_left_from, new_left_to, new_right_from,
                            new_right_to, number - chars_in_intersect * 2,
                            chars, read_only_depend, one_dep_list,
                            save_split_dep_lists, additional_dep_lists)

            else:
                # exclusive ranges
                # Total number of Left + Right >= 5
                # a >= 5; a = 4, b >= 1; ...
                # Same for Left + Right == 5
                for left_share in range(0, number):
                    right_share = number - left_share
                    # a = 4, b >= 1; ..
                    tmp_one_dep_list = deepcopy(one_dep_list)
                    tmp_one_dep_list.prepend_dependency(
                        RejectUnlessFromToContainsExactlyNumberOfChars(
                            left_from, left_to, left_share, chars))
                    tmp_one_dep_list.prepend_dependency(
                        RejectUnlessFromToContainsAtLeastNumberOfChars(
                            right_from, right_to, right_share, chars))
                    for v in additional_dep_lists:
                        tmp_one_dep_list.prepend_dependency(deepcopy(v))
                    save_split_dep_lists.append_dependency_list(
                        tmp_one_dep_list)

                # a >= 5;
                tmp_one_dep_list = deepcopy(one_dep_list)
                tmp_one_dep_list.prepend_dependency(
                    RejectUnlessFromToContainsAtLeastNumberOfChars(
                        left_from, left_to, number, chars))
                for v in additional_dep_lists:
                    tmp_one_dep_list.prepend_dependency(deepcopy(v))
                save_split_dep_lists.append_dependency_list(tmp_one_dep_list)

        # there's only one side
        elif left_from == left_to and right_from != right_to:
            tmp_one_dep_list = deepcopy(one_dep_list)
            tmp_one_dep_list.prepend_dependency(
                RejectUnlessFromToContainsAtLeastNumberOfChars(
                    right_from, right_to, number, chars))
            for v in additional_dep_lists:
                tmp_one_dep_list.prepend_dependency(deepcopy(v))
            save_split_dep_lists.append_dependency_list(tmp_one_dep_list)

        # there's only one side
        elif left_from != left_to and right_from == right_to:
            tmp_one_dep_list = deepcopy(one_dep_list)
            tmp_one_dep_list.prepend_dependency(
                RejectUnlessFromToContainsAtLeastNumberOfChars(
                    left_from, left_to, number, chars))
            for v in additional_dep_lists:
                tmp_one_dep_list.prepend_dependency(deepcopy(v))
            save_split_dep_lists.append_dependency_list(tmp_one_dep_list)

        else:
            raise Exception("Should fall into here")

    @staticmethod
    def extract_O_N_M_command(subrule_dependency, rule):
        """ ONM Deletes M chars, starting at position N

        Effects on Dependency:
            Depends on char from N to M + N

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        try:
            N = convert_str_length_to_int(rule[1])
            M = convert_str_length_to_int(rule[2])
        except:
            raise NotCountableException("Not Countable")

        if M == 0:
            return subrule_dependency

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:
                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        # Case1, length < M+N, do nothing
                        depend_length_no_op = RejectUnlessLessThanLength(N + M)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        # Case2, from N to N + M has at least that number
                        for removed_number in range(M + 1):
                            tmp_dep = deepcopy(read_only_depend)
                            tmp_dep.set_number(tmp_dep.get_number() +
                                               removed_number)

                            tmp_dep_list = deepcopy(one_dep_list)
                            tmp_dep_list.prepend_dependency(
                                RejectUnlessFromToContainsExactlyNumberOfChars(
                                    N, N + M, removed_number,
                                    read_only_depend.get_chars()))
                            tmp_dep_list.prepend_dependency(tmp_dep)
                            tmp_dep_list.prepend_dependency(
                                RejectUnlessGreaterThanLength(N + M - 1))
                            save_split_dep_lists.append_dependency_list(
                                tmp_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:

                        # Case1, length < M+N, do nothing
                        depend_length_no_op = RejectUnlessLessThanLength(N + M)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        depend_length_op = RejectUnlessGreaterThanLength(N + M -
                                                                         1)

                        ori_pos = read_only_depend.get_position()

                        if ori_pos >= 0:
                            # delete what's after it.
                            if ori_pos < N:
                                one_dep_list.prepend_dependency(
                                    read_only_depend)
                                one_dep_list.prepend_dependency(
                                    depend_length_op)
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                            # delete what's before it.
                            else:
                                one_dep_list.prepend_dependency(
                                    RejectUnlessCharInPosition(
                                        read_only_depend.get_chars(),
                                        ori_pos + M))
                                one_dep_list.prepend_dependency(
                                    depend_length_op)
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                        else:
                            # case1: len >= M + N - ori_pos. Doens't matter
                            dep_list_case_1 = deepcopy(one_dep_list)
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(M + N - ori_pos -
                                                              1))
                            dep_list_case_1.prepend_dependency(depend_length_op)
                            dep_list_case_1.prepend_dependency(read_only_depend)
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1)

                            # case2: len < M + N - ori_pos, ori_pos = ori_pos - M
                            dep_list_case_2 = deepcopy(one_dep_list)
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessLessThanLength(M + N - ori_pos))
                            dep_list_case_2.prepend_dependency(depend_length_op)
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    read_only_depend.get_chars(), ori_pos - M))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_2)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        # Case1, length < M+N, do nothing
                        depend_length_no_op = RejectUnlessLessThanLength(N + M)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N + M - 1)

                        # everything >= N. O42
                        depend = deepcopy(read_only_depend)
                        depend.set_len(depend.get_len() + M)
                        op_dep_list = deepcopy(one_dep_list)
                        op_dep_list.prepend_dependency(depend)
                        op_dep_list.prepend_dependency(depend_length_op_lower)
                        save_split_dep_lists.append_dependency_list(op_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        # Case1, length < M+N, do nothing
                        depend_length_no_op = RejectUnlessLessThanLength(N + M)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N + M - 1)

                        depend = deepcopy(read_only_depend)
                        depend.set_len(depend.get_len() + M)
                        op_dep_list = deepcopy(one_dep_list)
                        op_dep_list.prepend_dependency(depend)
                        op_dep_list.prepend_dependency(depend_length_op_lower)
                        save_split_dep_lists.append_dependency_list(op_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        # Case1, length < M+N, do nothing
                        depend_length_no_op = RejectUnlessLessThanLength(N + M)
                        no_op_dep_list_1 = deepcopy(one_dep_list)
                        no_op_dep_list_1.prepend_dependency(
                            deepcopy(read_only_depend))
                        no_op_dep_list_1.prepend_dependency(depend_length_no_op)
                        save_split_dep_lists.append_dependency_list(
                            no_op_dep_list_1)

                        depend_length_op_lower = RejectUnlessGreaterThanLength(
                            N + M - 1)

                        from_idx = read_only_depend.get_from()
                        to_idx = read_only_depend.get_to()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        if from_idx >= 0:
                            # case1: from, to are right
                            if from_idx >= N:
                                one_dep_list.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx + M, to_idx + M, number,
                                        chars))
                                one_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                            # case2: from, to are left
                            elif to_idx <= N:
                                one_dep_list.prepend_dependency(
                                    read_only_depend)
                                one_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    one_dep_list)

                            # case3: from, to in the middle
                            else:
                                left_from = from_idx
                                left_to = N
                                right_from = N + M
                                right_to = M + to_idx

                                if read_only_depend.dependency_type == 4:
                                    FeatureExtraction.handles_left_right_shares_number_for_exact(
                                        left_from, left_to, right_from,
                                        right_to, number, chars,
                                        read_only_depend, one_dep_list,
                                        save_split_dep_lists,
                                        [depend_length_op_lower])
                                else:
                                    FeatureExtraction.handles_left_right_shares_number_for_at_least(
                                        left_from, left_to, right_from,
                                        right_to, number, chars,
                                        read_only_depend, one_dep_list,
                                        save_split_dep_lists,
                                        [depend_length_op_lower])

                        else:
                            # case1: from, to are right. len >= M + N - from_idx
                            dep_list_case_1 = deepcopy(one_dep_list)
                            dep_list_case_1.prepend_dependency(
                                deepcopy(read_only_depend))
                            dep_list_case_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(M + N - from_idx -
                                                              1))
                            dep_list_case_1.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1)

                            # case2: from, to are left. shift right window. len <= M + N - to_idx
                            dep_list_case_2 = deepcopy(one_dep_list)
                            dep_list_case_2.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx - M, to_idx - M, number, chars))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessLessThanLength(M + N - to_idx + 1))
                            dep_list_case_2.prepend_dependency(
                                deepcopy(depend_length_op_lower))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_2)

                            # M + N - from_idx > length > M + N - to_idx
                            # case3: [from, to) and [N,N+M) have intersection
                            # extend [from, to) to [from-M, to)
                            # Enumerate what's in [N, N+M)
                            for removed_number in range(M + 1):
                                tmp_dep_list = deepcopy(one_dep_list)
                                tmp_dep_list.prepend_dependency(
                                    RejectUnlessFromToContainsExactlyNumberOfChars(
                                        N, M + N, removed_number, chars))
                                tmp_dep_list.prepend_dependency(
                                    read_only_depend.make_new(
                                        from_idx - M, to_idx,
                                        number + removed_number, chars))
                                tmp_dep_list.prepend_dependency(
                                    RejectUnlessGreaterThanLength(M + N -
                                                                  to_idx))
                                tmp_dep_list.prepend_dependency(
                                    RejectUnlessLessThanLength(M + N -
                                                               from_idx))
                                tmp_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op_lower))
                                save_split_dep_lists.append_dependency_list(
                                    tmp_dep_list)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_asterisk_N_M_command(subrule_dependency, rule):
        """ *NM Swaps character at position N with a character at position M. (indexing starting at 0)

        Effects on Dependency:
            Doesn't affect length, swap positions.

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        try:
            N = convert_str_length_to_int(rule[1])
            M = convert_str_length_to_int(rule[2])
        except:
            raise NotCountableException("Not Countable")

        if ((N >= 0 and M >= 0) or (N < 0 and M < 0)) != True:
            raise ValueError("NM in count_asterisk_NM_command")

        if N == M:  #Same doesn't affect
            return subrule_dependency

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.

        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        depend = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:

                        min_word_length = max(N, M) + 1 if (
                            N >= 0 and M >= 0) else max(-N, -M)

                        ori_pos = read_only_depend.get_position()
                        # N, M >= 0
                        if N >= 0 and M >= 0:

                            if ori_pos >= 0:  #ori_pos >= 0 and NM >=0
                                #ori_pos != N and ori_pos != M
                                if ori_pos != N and ori_pos != M:

                                    dep_list = deepcopy(one_dep_list)
                                    dep_list.prepend_dependency(
                                        deepcopy(read_only_depend))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list)

                                else:
                                    #No op
                                    depend_length_no_op = RejectUnlessLessThanLength(
                                        min_word_length)
                                    no_op_dep_list_1 = deepcopy(one_dep_list)
                                    no_op_dep_list_1.prepend_dependency(
                                        deepcopy(read_only_depend))
                                    no_op_dep_list_1.prepend_dependency(
                                        depend_length_no_op)
                                    save_split_dep_lists.append_dependency_list(
                                        no_op_dep_list_1)

                                    #Op
                                    #Dont' Forget To Test Boundary Cases!
                                    depend_length_op = RejectUnlessGreaterThanLength(
                                        min_word_length - 1)
                                    depend = deepcopy(read_only_depend)
                                    if ori_pos == N:
                                        depend.set_position(M)
                                    elif ori_pos == M:
                                        depend.set_position(N)
                                    else:
                                        raise ValueError("Wrong ori_pos")
                                    op_dep_list = deepcopy(one_dep_list)
                                    op_dep_list.prepend_dependency(
                                        depend_length_op)
                                    op_dep_list.prepend_dependency(depend)
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list)

                            else:
                                #No op
                                depend_length_no_op = RejectUnlessLessThanLength(
                                    min_word_length)
                                no_op_dep_list_1 = deepcopy(one_dep_list)
                                no_op_dep_list_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                no_op_dep_list_1.prepend_dependency(
                                    depend_length_no_op)
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list_1)

                                #op
                                depend_length_op = RejectUnlessGreaterThanLength(
                                    min_word_length - 1)

                                # word_len == N - ori_pos:
                                depend_len_lower = RejectUnlessGreaterThanLength(
                                    N - ori_pos - 1)
                                depend_len_upper = RejectUnlessLessThanLength(
                                    N - ori_pos + 1)
                                depend = deepcopy(read_only_depend)
                                depend.set_position(M)
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(depend_len_lower)
                                op_dep_list.prepend_dependency(depend_len_upper)
                                op_dep_list.prepend_dependency(depend)
                                op_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                                # word_len == M - ori_pos:
                                depend_len_lower = RejectUnlessGreaterThanLength(
                                    M - ori_pos - 1)
                                depend_len_upper = RejectUnlessLessThanLength(
                                    M - ori_pos + 1)
                                depend = deepcopy(read_only_depend)
                                depend.set_position(N)
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(depend_len_lower)
                                op_dep_list.prepend_dependency(depend_len_upper)
                                op_dep_list.prepend_dependency(depend)
                                op_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                                # word_len < min(N,M) - ori_pos
                                depend_len_upper = RejectUnlessLessThanLength(
                                    min(N, M) - ori_pos)
                                depend = deepcopy(read_only_depend)
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(depend_len_upper)
                                op_dep_list.prepend_dependency(depend)
                                op_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                                # word_len > max(N,M) - ori_pos
                                depend_len_lower = RejectUnlessGreaterThanLength(
                                    max(N, M) - ori_pos)
                                depend = deepcopy(read_only_depend)
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(depend_len_lower)
                                op_dep_list.prepend_dependency(depend)
                                op_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                                #  min(N,M) - ori_pos < word_len < max(N,M) - ori_pos
                                depend_len_lower = RejectUnlessGreaterThanLength(
                                    min(N, M) - ori_pos)
                                depend_len_upper = RejectUnlessLessThanLength(
                                    max(N, M) - ori_pos)
                                depend = deepcopy(read_only_depend)
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(depend_len_lower)
                                op_dep_list.prepend_dependency(depend_len_upper)
                                op_dep_list.prepend_dependency(depend)
                                op_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                        # M,N < 0
                        elif N < 0 and M < 0:
                            if ori_pos >= 0:
                                #print(M)
                                #print(N)
                                #print(ori_pos)
                                #No op
                                depend_length_no_op = RejectUnlessLessThanLength(
                                    min_word_length)
                                no_op_dep_list_1 = deepcopy(one_dep_list)
                                no_op_dep_list_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                no_op_dep_list_1.prepend_dependency(
                                    depend_length_no_op)
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list_1)

                                #op
                                depend_length_op = RejectUnlessGreaterThanLength(
                                    min_word_length - 1)

                                # word_len == -N + ori_pos:
                                depend_len_lower = RejectUnlessGreaterThanLength(
                                    -N + ori_pos - 1)
                                depend_len_upper = RejectUnlessLessThanLength(
                                    -N + ori_pos + 1)
                                depend = deepcopy(read_only_depend)
                                depend.set_position(M)
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(depend_len_lower)
                                op_dep_list.prepend_dependency(depend_len_upper)
                                op_dep_list.prepend_dependency(depend)
                                op_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                                # word_len == -M + ori_pos:
                                depend_len_lower = RejectUnlessGreaterThanLength(
                                    -M + ori_pos - 1)
                                depend_len_upper = RejectUnlessLessThanLength(
                                    -M + ori_pos + 1)
                                depend = deepcopy(read_only_depend)
                                depend.set_position(N)
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(depend_len_lower)
                                op_dep_list.prepend_dependency(depend_len_upper)
                                op_dep_list.prepend_dependency(depend)
                                op_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                                # word_len < min(N,M) + ori_pos
                                depend_len_upper = RejectUnlessLessThanLength(
                                    min(-N, -M) + ori_pos)
                                depend = deepcopy(read_only_depend)
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(depend_len_upper)
                                op_dep_list.prepend_dependency(depend)
                                op_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                                # word_len > max(-N,-M) + ori_pos
                                depend_len_lower = RejectUnlessGreaterThanLength(
                                    max(-N, -M) + ori_pos)
                                depend = deepcopy(read_only_depend)
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(depend_len_lower)
                                op_dep_list.prepend_dependency(depend)
                                op_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                                #  min(-N,-M) + ori_pos < word_len < max(-N,-M) + ori_pos
                                depend_len_lower = RejectUnlessGreaterThanLength(
                                    min(-N, -M) + ori_pos)
                                depend_len_upper = RejectUnlessLessThanLength(
                                    max(-N, -M) + ori_pos)
                                depend = deepcopy(read_only_depend)
                                op_dep_list = deepcopy(one_dep_list)
                                op_dep_list.prepend_dependency(depend_len_lower)
                                op_dep_list.prepend_dependency(depend_len_upper)
                                op_dep_list.prepend_dependency(depend)
                                op_dep_list.prepend_dependency(
                                    deepcopy(depend_length_op))
                                save_split_dep_lists.append_dependency_list(
                                    op_dep_list)

                            #ori_pos < 0 and NM < 0
                            else:
                                #ori_pos != N and ori_pos != M
                                if ori_pos != N and ori_pos != M:

                                    dep_list = deepcopy(one_dep_list)
                                    dep_list.prepend_dependency(
                                        deepcopy(read_only_depend))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list)

                                else:
                                    #No op
                                    depend_length_no_op = RejectUnlessLessThanLength(
                                        min_word_length)
                                    no_op_dep_list_1 = deepcopy(one_dep_list)
                                    no_op_dep_list_1.prepend_dependency(
                                        deepcopy(read_only_depend))
                                    no_op_dep_list_1.prepend_dependency(
                                        depend_length_no_op)
                                    save_split_dep_lists.append_dependency_list(
                                        no_op_dep_list_1)

                                    #Op
                                    #Dont' Forget To Test Boundary Cases!
                                    depend_length_op = RejectUnlessGreaterThanLength(
                                        min_word_length - 1)
                                    depend = deepcopy(read_only_depend)
                                    if ori_pos == N:
                                        depend.set_position(M)
                                    elif ori_pos == M:
                                        depend.set_position(N)
                                    else:
                                        raise ValueError("Wrong ori_pos")

                                    op_dep_list = deepcopy(one_dep_list)
                                    op_dep_list.prepend_dependency(
                                        depend_length_op)
                                    op_dep_list.prepend_dependency(depend)
                                    save_split_dep_lists.append_dependency_list(
                                        op_dep_list)
                        else:
                            raise ValueError("NM in count_asterisk_NM_command")

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        depend = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        depend = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:

                        def only_one_in_range(less_than, greater_than,
                                              pos_in_range, pos_not_in_range,
                                              from_idx, to_idx, number, chars,
                                              one_dep_list, read_only_depend,
                                              save_split_dep_lists, dep_len_op):
                            """ case where N,M only one in the range """
                            dep_list_case_1_1 = deepcopy(one_dep_list)
                            dep_list_case_1_1.prepend_dependency(
                                RejectUnlessLessThanLength(less_than))
                            dep_list_case_1_1.prepend_dependency(
                                RejectUnlessGreaterThanLength(greater_than))
                            dep_list_case_1_1.prepend_dependency(
                                deepcopy(dep_len_op))
                            dep_list_case_1_1.prepend_dependency(
                                RejectUnlessCharInPosition(chars, pos_in_range))
                            dep_list_case_1_1.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) - chars,
                                    pos_not_in_range))
                            dep_list_case_1_1.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number + 1, chars))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1_1)

                            dep_list_case_1_2 = deepcopy(one_dep_list)
                            dep_list_case_1_2.prepend_dependency(
                                RejectUnlessLessThanLength(less_than))
                            dep_list_case_1_2.prepend_dependency(
                                RejectUnlessGreaterThanLength(greater_than))
                            dep_list_case_1_2.prepend_dependency(
                                deepcopy(dep_len_op))
                            dep_list_case_1_2.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) - chars,
                                    pos_in_range))
                            dep_list_case_1_2.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    chars, pos_not_in_range))
                            dep_list_case_1_2.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number - 1, chars))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1_2)

                            dep_list_case_1_3 = deepcopy(one_dep_list)
                            dep_list_case_1_3.prepend_dependency(
                                RejectUnlessLessThanLength(less_than))
                            dep_list_case_1_3.prepend_dependency(
                                RejectUnlessGreaterThanLength(greater_than))
                            dep_list_case_1_3.prepend_dependency(
                                deepcopy(dep_len_op))
                            dep_list_case_1_3.prepend_dependency(
                                RejectUnlessCharInPosition(chars, pos_in_range))
                            dep_list_case_1_3.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    chars, pos_not_in_range))
                            dep_list_case_1_3.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number, chars))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1_3)

                            dep_list_case_1_4 = deepcopy(one_dep_list)
                            dep_list_case_1_4.prepend_dependency(
                                RejectUnlessLessThanLength(less_than))
                            dep_list_case_1_4.prepend_dependency(
                                RejectUnlessGreaterThanLength(greater_than))
                            dep_list_case_1_4.prepend_dependency(
                                deepcopy(dep_len_op))
                            dep_list_case_1_4.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) - chars,
                                    pos_in_range))
                            dep_list_case_1_4.prepend_dependency(
                                RejectUnlessCharInPosition(
                                    set(Dicts.classes['z']) - chars,
                                    pos_not_in_range))
                            dep_list_case_1_4.prepend_dependency(
                                read_only_depend.make_new(
                                    from_idx, to_idx, number, chars))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_1_4)

                        def both_in_range(
                                less_than, greater_than, one_dep_list,
                                read_only_depend, save_split_dep_lists,
                                dep_len_op
                        ):  # N,M both in or both not in, do nothing
                            dep_list_case_2 = deepcopy(one_dep_list)
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessLessThanLength(less_than))
                            dep_list_case_2.prepend_dependency(
                                RejectUnlessGreaterThanLength(greater_than))
                            dep_list_case_2.prepend_dependency(
                                deepcopy(dep_len_op))
                            dep_list_case_2.prepend_dependency(
                                deepcopy(read_only_depend))
                            save_split_dep_lists.append_dependency_list(
                                dep_list_case_2)

                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        chars = read_only_depend.get_chars()

                        if from_idx >= 0:
                            # from, to are positive, switch N,M are positive
                            if N >= 0:  # change positive position
                                if (M in range(from_idx, to_idx) and N in range(from_idx, to_idx)) or \
                                (M not in range(from_idx, to_idx) and N not in range(from_idx, to_idx)): # both in all both out, doesn't matter
                                    one_dep_list.prepend_dependency(
                                        read_only_depend)
                                    save_split_dep_lists.append_dependency_list(
                                        one_dep_list)
                                else:
                                    # case1: operation min length = max(N+1,M+1,to_idx)
                                    # case1.1: pos_in_range in chars and pos_not_in_range not in char
                                    pos_in_range = N if N >= from_idx and N < to_idx else M
                                    pos_not_in_range = M if pos_in_range == N else N

                                    dep_list_case_1 = deepcopy(one_dep_list)
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            chars, pos_in_range))
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars,
                                            pos_not_in_range))
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            max(N + 1, M + 1, to_idx) - 1))
                                    dep_list_case_1.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx, number + 1,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_1)

                                    # case1.2: the other way around
                                    dep_list_case_2 = deepcopy(one_dep_list)
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars,
                                            pos_in_range))
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            chars, pos_not_in_range))
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            max(N + 1, M + 1, to_idx) - 1))
                                    dep_list_case_2.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx, number - 1,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_2)

                                    # case1.3:doesn't change
                                    dep_list_case_3 = deepcopy(one_dep_list)
                                    dep_list_case_3.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars,
                                            pos_in_range))
                                    dep_list_case_3.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars,
                                            pos_not_in_range))
                                    dep_list_case_3.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            max(N + 1, M + 1, to_idx) - 1))
                                    dep_list_case_3.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx, number, chars))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_3)

                                    # case1.4:doesn't change
                                    dep_list_case_4 = deepcopy(one_dep_list)
                                    dep_list_case_4.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            chars, pos_in_range))
                                    dep_list_case_4.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            chars, pos_not_in_range))
                                    dep_list_case_4.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            max(N + 1, M + 1, to_idx) - 1))
                                    dep_list_case_4.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx, number, chars))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_4)

                                    # case2: no operation, do nothing
                                    # if max = to_idx, the rest it is not possible.
                                    if max(N + 1, M + 1, to_idx) != to_idx:
                                        dep_list_case_3 = deepcopy(one_dep_list)
                                        dep_list_case_3.prepend_dependency(
                                            read_only_depend)
                                        dep_list_case_3.prepend_dependency(
                                            RejectUnlessLessThanLength(
                                                max(N + 1, M + 1, to_idx)))
                                        save_split_dep_lists.append_dependency_list(
                                            dep_list_case_3)

                            # from, to are positive, switch N,M are negative
                            else:
                                # case -1: no operation for length < max(-N,-M)
                                no_op_dep_list = deepcopy(one_dep_list)
                                no_op_dep_list.prepend_dependency(
                                    RejectUnlessLessThanLength(max(-N, -M)))
                                no_op_dep_list.prepend_dependency(
                                    deepcopy(read_only_depend))
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list)

                                dep_len_op = RejectUnlessGreaterThanLength(
                                    max(-N, -M) - 1)

                                # case0: 0 intersect, len > max(-N,-M) + to_idx - 1
                                dep_list_case_0 = deepcopy(one_dep_list)
                                dep_list_case_0.prepend_dependency(
                                    RejectUnlessGreaterThanLength(
                                        max(-N, -M) + to_idx - 1))
                                dep_list_case_0.prepend_dependency(
                                    deepcopy(read_only_depend))
                                dep_list_case_0.prepend_dependency(dep_len_op)
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_0)

                                # case4: 0 intersect, len < min(-N,-M) + from_idx
                                dep_list_case_1 = deepcopy(one_dep_list)
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessLessThanLength(
                                        min(-N, -M) + from_idx))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                dep_list_case_1.prepend_dependency(dep_len_op)
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                                range_start = min(-N, -M) + from_idx
                                range_end = max(-N, -M) + to_idx

                                # Previously whether N or M are in range [from, to)
                                prev_type = None
                                prev_start = range_start
                                # input length range from [min(-N,-M) + from_idx + 1, max(-N,-M) + to_idx - 1] inclusive
                                for input_len in range(range_start, range_end):
                                    # 0 means 0 intersect, 1 mean only M, 2 means only N, 3 means both.
                                    type_this_len = 0
                                    if input_len + M in range(from_idx, to_idx):
                                        type_this_len += 1
                                    if input_len + N in range(from_idx, to_idx):
                                        type_this_len += 2

                                    if prev_type == None or prev_type == type_this_len:
                                        prev_type = type_this_len
                                    else:  # prev_type != type_this_len
                                        # if only n/m is in range
                                        if 1 <= prev_type <= 2:
                                            pos_in_range = M if prev_type == 1 else N
                                            pos_not_in_range = N if prev_type == 1 else M
                                            only_one_in_range(
                                                input_len, prev_start - 1,
                                                pos_in_range, pos_not_in_range,
                                                from_idx, to_idx, number, chars,
                                                one_dep_list, read_only_depend,
                                                save_split_dep_lists,
                                                dep_len_op)
                                        else:
                                            both_in_range(
                                                input_len, prev_start - 1,
                                                one_dep_list, read_only_depend,
                                                save_split_dep_lists,
                                                dep_len_op)

                                        # reset flags
                                        prev_type = type_this_len
                                        prev_start = input_len

                                # add the last one
                                if 1 <= prev_type <= 2:
                                    pos_in_range = M if prev_type == 1 else N
                                    pos_not_in_range = N if prev_type == 1 else M
                                    only_one_in_range(
                                        range_end, prev_start - 1, pos_in_range,
                                        pos_not_in_range, from_idx, to_idx,
                                        number, chars, one_dep_list,
                                        read_only_depend, save_split_dep_lists,
                                        dep_len_op)
                                else:
                                    both_in_range(
                                        range_end, prev_start - 1, one_dep_list,
                                        read_only_depend, save_split_dep_lists,
                                        dep_len_op)

                        else:
                            # from, to are negative, switch N,M are positive
                            if N >= 0:
                                # case -1: no operation for length < max(N,M) + 1
                                no_op_dep_list = deepcopy(one_dep_list)
                                no_op_dep_list.prepend_dependency(
                                    RejectUnlessLessThanLength(max(N, M) + 1))
                                no_op_dep_list.prepend_dependency(
                                    deepcopy(read_only_depend))
                                save_split_dep_lists.append_dependency_list(
                                    no_op_dep_list)

                                dep_len_op = RejectUnlessGreaterThanLength(
                                    max(N, M))

                                # case0: 0 intersect, len > max(N,M) + abs(from_idx)
                                dep_list_case_0 = deepcopy(one_dep_list)
                                dep_list_case_0.prepend_dependency(
                                    RejectUnlessGreaterThanLength(
                                        max(N, M) - from_idx))
                                dep_list_case_0.prepend_dependency(
                                    deepcopy(read_only_depend))
                                dep_list_case_0.prepend_dependency(
                                    deepcopy(dep_len_op))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_0)

                                # case1: 0 intersect, len <= min(N,M) + abs(to_idex)
                                dep_list_case_1 = deepcopy(one_dep_list)
                                dep_list_case_1.prepend_dependency(
                                    RejectUnlessLessThanLength(
                                        min(N, M) - to_idx + 1))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(read_only_depend))
                                dep_list_case_1.prepend_dependency(
                                    deepcopy(dep_len_op))
                                save_split_dep_lists.append_dependency_list(
                                    dep_list_case_1)

                                range_start = min(N, M) - to_idx + 1
                                range_end = max(N, M) - from_idx + 1
                                # Previously whether N or M are in range [from, to)
                                prev_type = None
                                prev_start = range_start
                                # input length range from [min(N,M) + abs(to_idex) + 1, max(N,M) + abs(from_idx)] inclusive
                                for input_len in range(range_start, range_end):
                                    # 0 means 0 intersect, 1 mean only M, 2 means only N, 3 means both.
                                    type_this_len = 0
                                    if M in range(input_len + from_idx,
                                                  input_len + to_idx):
                                        type_this_len += 1
                                    if N in range(input_len + from_idx,
                                                  input_len + to_idx):
                                        type_this_len += 2

                                    if prev_type == None or prev_type == type_this_len:
                                        prev_type = type_this_len
                                    else:  # prev_type != type_this_len
                                        # if only n/m is in range
                                        if 1 <= prev_type <= 2:
                                            pos_in_range = M if prev_type == 1 else N
                                            pos_not_in_range = N if prev_type == 1 else M
                                            only_one_in_range(
                                                input_len, prev_start - 1,
                                                pos_in_range, pos_not_in_range,
                                                from_idx, to_idx, number, chars,
                                                one_dep_list, read_only_depend,
                                                save_split_dep_lists,
                                                dep_len_op)
                                        else:
                                            both_in_range(
                                                input_len, prev_start - 1,
                                                one_dep_list, read_only_depend,
                                                save_split_dep_lists,
                                                dep_len_op)

                                        # reset flags
                                        prev_type = type_this_len
                                        prev_start = input_len

                                # add the last one
                                if 1 <= prev_type <= 2:
                                    pos_in_range = M if prev_type == 1 else N
                                    pos_not_in_range = N if prev_type == 1 else M
                                    only_one_in_range(
                                        range_end, prev_start - 1, pos_in_range,
                                        pos_not_in_range, from_idx, to_idx,
                                        number, chars, one_dep_list,
                                        read_only_depend, save_split_dep_lists,
                                        dep_len_op)
                                else:
                                    both_in_range(
                                        range_end, prev_start - 1, one_dep_list,
                                        read_only_depend, save_split_dep_lists,
                                        dep_len_op)

                            # from, to are negative, switch N,M are negative
                            else:
                                if (M in range(from_idx, to_idx) and N in range(from_idx, to_idx)) or \
                                (M not in range(from_idx, to_idx) and N not in range(from_idx, to_idx)): # doesn't matter
                                    one_dep_list.prepend_dependency(
                                        read_only_depend)
                                    save_split_dep_lists.append_dependency_list(
                                        one_dep_list)
                                else:
                                    # case1: operation min length = max(-N,-M,-from_idx)
                                    # case1.1: pos_in_range in chars and pos_not_in_range not in char
                                    pos_in_range = N if N >= from_idx and N < to_idx else M
                                    pos_not_in_range = M if pos_in_range == N else N

                                    dep_list_case_1 = deepcopy(one_dep_list)
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            chars, pos_in_range))
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars,
                                            pos_not_in_range))
                                    dep_list_case_1.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            max(-N, -M, -from_idx) - 1))
                                    dep_list_case_1.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx, number + 1,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_1)

                                    # case1.2: the other way around
                                    dep_list_case_2 = deepcopy(one_dep_list)
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars,
                                            pos_in_range))
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            chars, pos_not_in_range))
                                    dep_list_case_2.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            max(-N, -M, -from_idx) - 1))
                                    dep_list_case_2.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx, number - 1,
                                            chars))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_2)

                                    # case1.3:doesn't change
                                    dep_list_case_3 = deepcopy(one_dep_list)
                                    dep_list_case_3.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars,
                                            pos_in_range))
                                    dep_list_case_3.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            set(Dicts.classes['z']) - chars,
                                            pos_not_in_range))
                                    dep_list_case_3.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            max(-N, -M, -from_idx) - 1))
                                    dep_list_case_3.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx, number, chars))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_3)

                                    # case1.4:doesn't change
                                    dep_list_case_4 = deepcopy(one_dep_list)
                                    dep_list_case_4.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            chars, pos_in_range))
                                    dep_list_case_4.prepend_dependency(
                                        RejectUnlessCharInPosition(
                                            chars, pos_not_in_range))
                                    dep_list_case_4.prepend_dependency(
                                        RejectUnlessGreaterThanLength(
                                            max(-N, -M, -from_idx) - 1))
                                    dep_list_case_4.prepend_dependency(
                                        read_only_depend.make_new(
                                            from_idx, to_idx, number, chars))
                                    save_split_dep_lists.append_dependency_list(
                                        dep_list_case_4)

                                    # case2: no operation, do nothing
                                    # if max = to_idx, the rest it is not possible.
                                    if max(-N, -M, -from_idx) != -from_idx:
                                        dep_list_case_3 = deepcopy(one_dep_list)
                                        dep_list_case_3.prepend_dependency(
                                            read_only_depend)
                                        dep_list_case_3.prepend_dependency(
                                            RejectUnlessLessThanLength(
                                                max(-N, -M, -from_idx)))
                                        save_split_dep_lists.append_dependency_list(
                                            dep_list_case_3)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_M_command(subrule_dependency, rule):
        """ Not Countable """
        raise NotCountableException("Not Countable")

    @staticmethod
    def extract_Q_command(subrule_dependency, rule):
        """ Not Countable """
        raise NotCountableException("Not Countable")

    @staticmethod
    def extract_X_N_M_I_command(subrule_dependency, rule):
        """ Not Countable """
        raise NotCountableException("Not Countable")

    @staticmethod
    def extract_4_command(subrule_dependency, rule):
        """ Not Countable """
        raise NotCountableException("Not Countable")

    @staticmethod
    def extract_6_command(subrule_dependency, rule):
        """ Not Countable """
        raise NotCountableException("Not Countable")

    @staticmethod
    def extract_v_V_N_M_command(subrule_dependency, rule):
        """ Not Countable """
        raise NotCountableException("Not Countable")

    @staticmethod
    def extract_mode_command(subrule_dependency, rule):
        """ Mode Commands 1 or 2

        Effects on Dependency:
            Rejected

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        subrule_dependency.prepend_dependency_to_all_lists(
            RejectUnlessLessThanLength(0))  # reject everything
        return subrule_dependency

    @staticmethod
    def extract_less_than_N_command(subrule_dependency, rule):
        """ <N   Reject unless word is less than N chars long

        Effects on Dependency:
            Add this spefic dependency type to all existing dep_lists

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Parsable N")

        if RUNTIME_CONFIG.is_jtr():  # JTR definition
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessLessThanLength(N))
        else:  # Reject unless word is less or equal than N chars long
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessLessThanLength(N + 1))

        return subrule_dependency

    @staticmethod
    def extract_greater_than_N_command(subrule_dependency, rule):
        """ >N   Reject unless word is greater than N chars long

        Effects on Dependency:
            Add this spefic dependency type to all existing dep_lists

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Parsable N")

        if RUNTIME_CONFIG.is_jtr():  # JTR definition
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessGreaterThanLength(N))
        else:  # Reject unless word is less or equal than N chars long
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessGreaterThanLength(N - 1))

        return subrule_dependency

    @staticmethod
    def extract_underscore_N_command(subrule_dependency, rule):
        """ _N  Reject if word length is not equal to N

        Effects on Dependency:
            > (N-1) && < (N+1)

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise NotCountableException("Not Parsable N")

        subrule_dependency.prepend_dependency_to_all_lists(
            RejectUnlessGreaterThanLength(N - 1))
        subrule_dependency.prepend_dependency_to_all_lists(
            RejectUnlessLessThanLength(N + 1))

        return subrule_dependency

    @staticmethod
    def extract_bang_X_command(subrule_dependency, rule):
        """ !X  Reject if word contains X

        Effects on Dependency:
            Add a dependency

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        subrule_dependency.prepend_dependency_to_all_lists(
            RejectIfContainsNumberChars(set(rule[1]), 1))
        return subrule_dependency

    @staticmethod
    def extract_bang_question_C_command(subrule_dependency, rule):
        """ !?C  Reject if word contains ?C

        Effects on Dependency:
            Add a dependency

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        if rule[2] in CHAR_CLASSES:
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectIfContainsNumberChars(set(Dicts.classes[rule[2]]), 1))
        else:
            raise FatalRuntimeError("Unknown Class Type: {}".format(rule[2]))

        return subrule_dependency

    @staticmethod
    def extract_slash_X_command(subrule_dependency, rule):
        """ /X - reject the word unless it contains character X

        Effects on Dependency:
            Add a dependency

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        subrule_dependency.prepend_dependency_to_all_lists(
            RejectUnlessContainsNumberChars(set(rule[1]), 1))
        return subrule_dependency

    @staticmethod
    def extract_slash_question_C_command(subrule_dependency, rule):
        """ /?C - reject the word unless it contains a character in class C

        Effects on Dependency:
            Add a dependency

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        if rule[2] in CHAR_CLASSES:
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessContainsNumberChars(set(Dicts.classes[rule[2]]), 1))
        else:
            raise FatalRuntimeError("Unknown Class Type: {}".format(rule[2]))

        return subrule_dependency

    @staticmethod
    def extract_equal_N_X_command(subrule_dependency, rule):
        """ =NX - reject the word unless character in position N is equal to X

        Effects on Dependency:
            Add a dependency

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise FatalRuntimeError("Not Parsable N")

        subrule_dependency.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(rule[2], N))

        return subrule_dependency

    @staticmethod
    def extract_equal_N_question_C_command(subrule_dependency, rule):
        """ =N?C - reject the word unless character in position N is in class C 

        Effects on Dependency:
            Add a dependency

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise FatalRuntimeError("Not Parsable N")

        if rule[3] in CHAR_CLASSES:
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessCharInPosition(set(Dicts.classes[rule[3]]), N))
        else:
            raise FatalRuntimeError("Unknown Class Type: {}".format(rule[3]))

        return subrule_dependency

    @staticmethod
    def extract_left_paren_X_command(subrule_dependency, rule):
        """ (X - reject the word unless its first character is X

        Effects on Dependency:
            Add a dependency

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        subrule_dependency.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(rule[1], 0))

        return subrule_dependency

    @staticmethod
    def extract_left_paren_question_C_command(subrule_dependency, rule):
        """ (?C - reject the word unless its first character is in class C 

        Effects on Dependency:
            Add a dependency

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        if rule[2] in CHAR_CLASSES:
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessCharInPosition(set(Dicts.classes[rule[2]]), 0))
        else:
            raise FatalRuntimeError("Unknown Class Type: {}".format(rule[2]))

        return subrule_dependency

    @staticmethod
    def extract_right_paren_X_command(subrule_dependency, rule):
        """ )X - reject the word unless its last character is X

        Effects on Dependency:
            Add a dependency

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        subrule_dependency.prepend_dependency_to_all_lists(
            RejectUnlessCharInPosition(rule[1], -1))

        return subrule_dependency

    @staticmethod
    def extract_right_paren_question_C_command(subrule_dependency, rule):
        """ )?C - reject the word unless its last character is in class C 

        Effects on Dependency:
            Add a dependency

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        if rule[2] in CHAR_CLASSES:
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessCharInPosition(set(Dicts.classes[rule[2]]), -1))
        else:
            raise FatalRuntimeError("Unknown Class Type: {}".format(rule[2]))

        return subrule_dependency

    @staticmethod
    def extract_percent_N_X_command(subrule_dependency, rule):
        """ %NX - reject the word unless it contains at least N instances of X

        Effects on Dependency:
            Add a dependency

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise FatalRuntimeError("Not Parsable N")

        subrule_dependency.prepend_dependency_to_all_lists(
            RejectUnlessContainsNumberChars(rule[2], N))

        return subrule_dependency

    @staticmethod
    def extract_percent_N_question_C_command(subrule_dependency, rule):
        """ %N?C - reject the word unless it contains at least N characters of class C 

        Effects on Dependency:
            Add a dependency

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        try:
            N = convert_str_length_to_int(rule[1])
        except:
            raise FatalRuntimeError("Not Parsable N")

        if rule[3] in CHAR_CLASSES:
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessContainsNumberChars(set(Dicts.classes[rule[3]]), N))
        else:
            raise FatalRuntimeError("Unknown Class Type: {}".format(rule[3]))

        return subrule_dependency

    @staticmethod
    def extract_at_X_command(subrule_dependency, rule):
        """ Not Countable """
        raise NotCountableException("Not Countable")

    @staticmethod
    def extract_at_question_C_command(subrule_dependency, rule):
        """ Not Countable """
        raise NotCountableException("Not Countable")

    @staticmethod
    def extract_s_X_Y_command(subrule_dependency, rule):
        """ sXY replace all characters X in the word with Y

        Effects on Dependency:
            

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        X = rule[1]
        Y = rule[2]

        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                depend = deepcopy(read_only_depend)

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        dest_set = depend.get_chars()

                        if X in dest_set and Y not in dest_set:  # X in dest Y not in
                            dest_set -= set(X)
                        elif X not in dest_set and Y in dest_set:  # X not in dest Y in dest
                            dest_set |= set(X)
                        else:
                            pass

                        depend.set_chars(dest_set)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        dest_set = depend.get_chars()

                        if X in dest_set and Y not in dest_set:
                            dest_set -= set(X)
                        elif X not in dest_set and Y in dest_set:
                            dest_set |= set(X)
                        else:
                            pass

                        depend.set_chars(dest_set)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        to_idx = read_only_depend.get_to()
                        from_idx = read_only_depend.get_from()
                        number = read_only_depend.get_number()
                        dest_set = read_only_depend.get_chars()

                        if X in dest_set and Y not in dest_set:  # X in dest Y not in
                            dest_set -= set(X)
                        elif X not in dest_set and Y in dest_set:  # X not in dest Y in dest
                            dest_set |= set(X)
                        else:
                            pass

                        one_dep_list.prepend_dependency(
                            read_only_depend.make_new(from_idx, to_idx, number,
                                                      dest_set))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_s_question_C_Y_command(subrule_dependency, rule):
        """ s?CY replace all characters of class C in the word with Y

        Effects on Dependency:
            

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        X_set = set(Dicts.classes[rule[2]])
        Y = rule[3]

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        depend = deepcopy(read_only_depend)

                        dest_set = depend.get_chars()

                        inter_set = dest_set & X_set

                        if inter_set != set(
                        ) and Y not in dest_set:  #X in Y not in
                            dest_set -= set(X_set)
                        elif inter_set == set(
                        ) and Y in dest_set:  # X not in Y in
                            dest_set |= set(X_set)
                        elif inter_set != set() and Y in dest_set:  #X in Y in
                            dest_set |= set(X_set)
                        else:  #X not in Y not in
                            pass

                        depend.set_chars(dest_set)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        depend = deepcopy(read_only_depend)

                        dest_set = depend.get_chars()

                        inter_set = dest_set & X_set

                        if inter_set != set(
                        ) and Y not in dest_set:  #X in Y not in
                            dest_set -= set(X_set)
                        elif inter_set == set(
                        ) and Y in dest_set:  # X not in Y in
                            dest_set |= set(X_set)
                        elif inter_set != set() and Y in dest_set:  #X in Y in
                            dest_set |= set(X_set)
                        else:  #X not in Y not in
                            pass

                        depend.set_chars(dest_set)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        depend = deepcopy(read_only_depend)

                        dest_set = depend.get_chars()

                        inter_set = dest_set & X_set

                        if inter_set != set(
                        ) and Y not in dest_set:  #X in Y not in
                            dest_set -= set(X_set)
                        elif inter_set == set(
                        ) and Y in dest_set:  # X not in Y in
                            dest_set |= set(X_set)
                        elif inter_set != set() and Y in dest_set:  #X in Y in
                            dest_set |= set(X_set)
                        else:  #X not in Y not in
                            pass

                        depend.set_chars(dest_set)

                        one_dep_list.prepend_dependency(depend)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_e_X_command(subrule_dependency, rule):
        """ eX  Lower case the whole line, then upper case the first letter and every letter after a custom separator character\
        p@ssW0rd-w0rld -> (e-) P@ssw0rd-W0rld

        Effects on Dependency:
            General case not countable

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        #A Trick to play
                        ori_set = read_only_depend.get_chars()
                        upper_set = set(x for x in ori_set
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in ori_set
                                        if x in Dicts.classes['l'])  # lower
                        #In this case c command doesn't change anything
                        if (lower_set | set(x.upper() for x in lower_set)) == (
                                upper_set | set(x.lower() for x in upper_set)):
                            #print("Play Trick In c Command\n")
                            depend0 = deepcopy(read_only_depend)
                            one_dep_list.prepend_dependency(depend0)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)
                            continue

                        else:
                            raise NotCountableException("Not Countable")

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        #A Trick to play
                        ori_set = read_only_depend.get_chars()
                        upper_set = set(x for x in ori_set
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in ori_set
                                        if x in Dicts.classes['l'])  # lower
                        #In this case c command doesn't change anything
                        if (lower_set | set(x.upper() for x in lower_set)) == (
                                upper_set | set(x.lower() for x in upper_set)):
                            #print("Play Trick In c Command\n")
                            depend0 = deepcopy(read_only_depend)
                            one_dep_list.prepend_dependency(depend0)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)
                            continue

                        else:
                            raise NotCountableException("Not Countable")

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        # doesn't affect length. Do Nothing
                        depend0 = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend0)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        # doesn't affect length. Do Nothing
                        depend0 = deepcopy(read_only_depend)

                        one_dep_list.prepend_dependency(depend0)
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list)

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        ori_set = read_only_depend.get_chars()
                        upper_set = set(x for x in ori_set
                                        if x in Dicts.classes['u'])  # upper
                        lower_set = set(x for x in ori_set
                                        if x in Dicts.classes['l'])  # lower
                        #In this case c command doesn't change anything
                        if (lower_set | set(x.upper() for x in lower_set)) == (
                                upper_set | set(x.lower() for x in upper_set)):
                            #print("Play Trick In c Command\n")
                            depend0 = deepcopy(read_only_depend)
                            one_dep_list.prepend_dependency(depend0)
                            save_split_dep_lists.append_dependency_list(
                                one_dep_list)
                            continue

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

    @staticmethod
    def extract_flag_command(subrule_dependency, rule):
        if rule[1] in "ps8":  # -p, -s reject
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessLessThanLength(0))  # reject everything
        # -c, -:, ->N, -<N. Don't do anything
        return subrule_dependency


def get_extraction_function(transformation):
    """ Based on tokenized transformation, get the corresponding extraction function """
    corresponding_function = getattr(
        FeatureExtraction, "extract_{}_command".format(
            get_name_of_a_rule(transformation)))
    return corresponding_function


def initialize_subrule_dependency():
    """ Initialize SubruleDependency while take password policy into consideration """
    pwd_policy = RUNTIME_CONFIG['password_policy']
    subrule_dependency = SubruleDependency()

    if pwd_policy.to_debug_string() != "None":
        if pwd_policy.length >= 1:
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessGreaterThanLength(pwd_policy.length - 1))
        if pwd_policy.digit == True:
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessContainsNumberChars(set(Dicts.classes['d']), 1))
        if pwd_policy.letter == True:
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessContainsNumberChars(set(Dicts.classes['l']), 1))
        if pwd_policy.upper == True:
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessContainsNumberChars(set(Dicts.classes['u']), 1))
        if pwd_policy.lower == True:
            subrule_dependency.prepend_dependency_to_all_lists(
                RejectUnlessContainsNumberChars(set(Dicts.classes['l']), 1))

    return subrule_dependency


def get_dependency_for_single_rule(one_rule):
    """ get dependency for a rule """
    try:
        # Create a global RuleDependency. Doing this because of parallelism
        rule_dependency = RuleDependency()

        for subrule in one_rule.rules:  # in reversed order
            #For each unparalleled subrule, get its dependency
            subrule_dependency = initialize_subrule_dependency()

            for transformation in subrule[::-1]:
                extract_function = get_extraction_function(transformation)
                subrule_dependency = extract_function(subrule_dependency,
                                                      transformation)

            #Add Final Result
            rule_dependency.add_sub_rule_dep(subrule_dependency)

    except NotCountableException:
        # Not Countable, return none for rule_dependency
        return None

    except Exception:
        # Some other bugs, raise
        raise

    return rule_dependency


def get_dependencies_for_rules(rules):
    """ Add dependency property to each rule
    
    If Rule Dependency is None, means not countable

    Args:
        rules: a parsed rulelist.
    """
    for i in range(len(rules)):

        #Return countability and rule dependency.
        rules[i].rule_dependency = get_dependency_for_single_rule(rules[i])

    return rules


def get_special_countability(rulelist):
    """ Find special countability in rules """
    for r in rulelist:
        if r.rule_dependency != None:
            continue

        transformation_at_0 = None
        for subrule in r.rules:  #For Each Subrule
            # special case where starts with D_ or \[ or \] and followed by Q.
            if subrule[0][0] in "D[]lu" and subrule[1][0] == "Q":
                if transformation_at_0 == None:
                    transformation_at_0 = subrule[0][0]
                elif transformation_at_0 != subrule[0][
                        0]:  # not the same thing, break
                    break
            else:
                break

        # special case triggered
        else:
            tmp_new_rule = deepcopy(r)
            for subrule in tmp_new_rule.rules:
                if subrule[0] == "D":
                    additional_rejection = RejectUnlessGreaterThanLength(
                        convert_str_length_to_int(rule[1]))
                elif subrule[0] == "[":
                    additional_rejection = RejectUnlessGreaterThanLength(0)
                elif subrule[0] == "]":
                    additional_rejection = RejectUnlessGreaterThanLength(0)
                elif subrule[0] == "l":
                    additional_rejection = RejectUnlessContainsNumberChars(
                        set(Dicts.classes['u']), 1)
                else:  # u
                    additional_rejection = RejectUnlessContainsNumberChars(
                        set(Dicts.classes['l']), 1)
                # remove Q
                subrule[1], subrule[0] = subrule[0], subrule[1]
                subrule.pop(0)
            tmp_new_rule.rule_dependency = get_dependency_for_single_rule(
                tmp_new_rule)
            for subrule_dependency in tmp_new_rule.rule_dependency.list_of_sub_rule_dep:
                subrule_dependency.prepend_dependency_to_all_lists(
                    additional_rejection)
            r.rule_dependency = deepcopy(tmp_new_rule.rule_dependency)

    return rulelist


class Demo():
    """ a demo, not used in real situation """

    @staticmethod
    def extract_xxx_command(subrule_dependency, rule):
        """ 

        Effects on Dependency:
            

        Args:
            subrule_dependency: dependency_lists from previous transformations

            rule: the tokenized transformation.

        Returns:
            An instance of SubruleDependency containing all possible dependency_lists
        """
        ret_val = SubruleDependency(subrule_dependency)

        #Initialize save_split_dep_lists.
        #A list of dep_list
        save_split_dep_lists = SubruleDependency()

        # For each dependency_list from previous transformations.
        # Apply the same transformation to all elements dependency_list
        # This operation may result in multiple new parallel dependency_lists.
        for dependency_list in subrule_dependency:
            # the dependency_list is already rejected or satisfied. this tranformation doesn't matter
            if dependency_list.is_rejected() or dependency_list.is_satisfied():
                ret_val.append_dependency_list(dependency_list)
                continue

            # a list of dep_lists
            # initialized with an empty dep_list that inherets previous coef.
            # because applying transformation on one dependency may result in several parallel dep_lists
            # All parallel dep_lists are saved in this list here.
            # used together with save_split_dep_lists
            current_dep_lists = SubruleDependency()
            current_dep_lists.append_dependency_list(
                DependencyList(extend_from=dependency_list))

            # For each depend in the dependency_list
            # change the depend based on current transformation, and add to save_split_dep_lists
            for read_only_depend in dependency_list:

                # a list of dep_list. used to save tmp results
                # it is necessary because applying transformation on one dependency may result in several parallel dep_lists
                save_split_dep_lists = SubruleDependency()

                # add transformed dependency to all existing parallel dep_lists.
                for one_dep_list in current_dep_lists:
                    # Not an active dependency, add nd Continue. There Should Be No Rejection Here
                    if read_only_depend.is_rejected(
                    ) or read_only_depend.is_satisfied():

                        one_dep_list.prepend_dependency(
                            deepcopy(read_only_depend))
                        save_split_dep_lists.append_dependency_list(
                            one_dep_list
                        )  #Add to satisfied to list and continue
                        continue

                    if 1 <= read_only_depend.dependency_type <= 2:
                        pass

                    # Reject_Unless_Char_In_Position_Equals
                    elif read_only_depend.dependency_type == 3:
                        pass

                    # Reject_Unless_Less_Than_Length
                    elif read_only_depend.dependency_type == 6:
                        pass

                    # Reject_Unless_Greater_Than_Length
                    elif read_only_depend.dependency_type == 7:
                        pass

                    # from_to_contains
                    elif 4 <= read_only_depend.dependency_type <= 5:
                        pass

                    else:
                        raise FatalRuntimeError("Unknown Dependency Type")

                current_dep_lists = save_split_dep_lists

            #Finally Add Every Dep List in current_dep_lists to ret_val
            for dep_list in current_dep_lists:
                ret_val.append_dependency_list(dep_list)

        return ret_val

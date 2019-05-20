"""This file contains a set of preprocessing functions."""
from feature_extraction import get_dependencies_for_rules, get_special_countability
from utility import convert_str_length_to_int, store_generated_data_hash, has_generated_data
from invert_rule import check_is_invertible, get_special_invertibility
from time import perf_counter
from feasibility import FeasibleType
from config import RUNTIME_CONFIG
import os
from utility import forward_a_rule_to_an_address_count_only, forward_a_rule_to_an_address_and_forward_count


def get_is_feasible(rulelist, enable_regex=False):
    """ add attribute to a rule that denotes if each rule is feasible """
    for r in rulelist:
        is_invertible = check_is_invertible(r, enable_regex)
        is_countable = True if r.rule_dependency != None else False
        r.feasibility = FeasibleType(is_invertible, is_countable)
    return rulelist


def precomputation(rulelist, enable_regex=False):
    """ A series of precomputations before you start inversion

    1. get rule countability
    2. get feasibility (countability + invertibility)
    """

    # 1. get rule countability
    if RUNTIME_CONFIG['debug'] == True:
        print("Getting Dependencies and Countability\n")
    rulelist = get_dependencies_for_rules(rulelist)

    # special count for D1 Q
    rulelist = get_special_countability(rulelist)

    # 2. get feasibility
    rulelist = get_is_feasible(rulelist, enable_regex)

    # 3. get special feasibility / special_checking(HC)
    rulelist = get_special_invertibility(rulelist, enable_regex)

    #for r in rulelist:
    #print("{}\n{}".format(r.raw, r.feasibility))

    # 4. pipe data (with memorization)
    if RUNTIME_CONFIG['debug'] == True:
        print("Calling JtR/HC to Enumerate Uninvertible Rules\n")

    stime = perf_counter()
    if has_generated_data() == False:
        if RUNTIME_CONFIG['debug'] == True:
            print("Start Calling JtR/HC To Generate Data:\n")

        for i, r in enumerate(rulelist):
            if r.feasibility.is_invertible() and r.feasibility.is_countable(
            ):  # If Both, Continue
                continue
            # only get a guess number
            elif r.feasibility.is_invertible() and r.feasibility.is_countable(
            ) == False:  # Only invertible, get count only
                forward_a_rule_to_an_address_count_only(
                    RUNTIME_CONFIG['wordlist_path']['name'], r,
                    "{}/count/rule{}.txt".format(
                        RUNTIME_CONFIG['preprocess_path'],
                        i), RUNTIME_CONFIG['wordlist_path']['prefix'])
            # pipe both guesses and number
            else:
                forward_a_rule_to_an_address_and_forward_count(
                    RUNTIME_CONFIG['wordlist_path']['name'], r,
                    RUNTIME_CONFIG['preprocess_path'], i,
                    RUNTIME_CONFIG['wordlist_path']['prefix'])

        store_generated_data_hash()

    else:
        if RUNTIME_CONFIG['debug'] == True:
            print("Already Has Data, Skipping Enumeration\n")

    data_generation_time = perf_counter() - stime
    if RUNTIME_CONFIG['debug'] == True:
        print("Data Generation (Enumeration) Time: {}\n".format(
            data_generation_time))

    return rulelist

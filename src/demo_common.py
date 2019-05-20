""" functions used for demo """
from utility import get_look_cmd
from config import RUNTIME_CONFIG
import os


def match_inversion_result(result, wordlist, is_regex=False):
    """ Return All Mathced Results in wordlist """
    if result.is_null():
        return []

    if is_regex == False:
        ret_vals = [
            one_string for one_string in result.get_all_strings()
            if (one_string in wordlist)
        ]

        if result.has_memory():
            ret_vals = [
                one_string for one_string in ret_vals
                if result.is_memorized(one_string) == False
            ]

        return ret_vals

    else:
        raise Exception("No Regex Implementation")


def search_exist_data(password, enumerated_data_addr, external_bash_process):
    """ Binary search on files """
    ret_vals = []

    look_cmd = get_look_cmd(password, enumerated_data_addr)  # -b

    external_bash_process.stdin.write(bytes(look_cmd, 'utf-8'))
    external_bash_process.stdin.flush()

    while True:
        result = external_bash_process.stdout.readline().decode()
        result = result.strip("\r\n")
        if result == "":
            break
        else:
            pwd, original = result.split("\t")
            if pwd != password:
                raise Exception(
                    "Searched Returned Result:{} Doesn't Match Input:{}".format(
                        pwd, password))
            ret_vals.append(original)

    return ret_vals


def search_trie(result, trie):
    """ trie search """
    if result.is_null():
        return []

    # output
    ret_vals = []

    for token_str in result:
        ret_vals += trie.find(token_str)

    if result.has_memory():
        ret_vals = [
            one_string for one_string in ret_vals
            if result.is_memorized(one_string) == False
        ]

    return ret_vals


def estimate_guess_number(counts, cumsum, word, rule_idx, wordlist):
    """ estimate guess number given word and rule and other info """

    word_idx = wordlist[word]

    if RUNTIME_CONFIG.is_jtr():
        # get lower and upper bound and estimate
        lower_bound = cumsum[rule_idx - 1]
        upper_bound = cumsum[rule_idx]
        estimated = lower_bound + int(counts[rule_idx] * (
            (word_idx + 1) * 1.0 / len(wordlist)))

    else:
        # specify which batch it is
        word_batch_number = word_idx // RUNTIME_CONFIG['batch_size_of_words']
        rule_batch_number = rule_idx // RUNTIME_CONFIG['batch_size_of_rules']

        # get lower and upper bound and estimate
        lower_bound = cumsum[word_batch_number * len(
            RUNTIME_CONFIG['number_of_rules_in_each_batch']) + rule_batch_number
                             - 1]
        upper_bound = cumsum[word_batch_number * len(
            RUNTIME_CONFIG['number_of_rules_in_each_batch']) +
                             rule_batch_number]
        # first part to estimate the number
        estimated_part_1 = int(
            counts[word_batch_number, rule_batch_number] *
            (word_idx % RUNTIME_CONFIG['batch_size_of_words']) /
            RUNTIME_CONFIG['number_of_words_in_each_batch'][word_batch_number])
        estimated_part_2 = int(
            counts[word_batch_number, rule_batch_number] * (
                (rule_idx % RUNTIME_CONFIG['batch_size_of_rules']) + 1) /
            RUNTIME_CONFIG['number_of_words_in_each_batch'][word_batch_number] /
            RUNTIME_CONFIG['number_of_rules_in_each_batch'][rule_batch_number])
        estimated = lower_bound + estimated_part_1 + estimated_part_2

    return estimated, lower_bound, upper_bound


def clean_hashes():
    """ remove saved hash file hashes.txt/count_hashes.txt """
    os.remove("{}/hashes.txt".format(
        RUNTIME_CONFIG['preprocess_path'])) if os.path.exists(
            "{}/hashes.txt".format(RUNTIME_CONFIG['preprocess_path'])) else None
    os.remove("{}/count_hashes.txt".format(
        RUNTIME_CONFIG['preprocess_path'])) if os.path.exists(
            "{}/count_hashes.txt".format(
                RUNTIME_CONFIG['preprocess_path'])) else None
    os.remove("{}/saved_counts.npy".format(
        RUNTIME_CONFIG['preprocess_path'])) if os.path.exists(
            "{}/saved_counts.npy".format(
                RUNTIME_CONFIG['preprocess_path'])) else None
    os.remove("{}/saved_cumsum.npy".format(
        RUNTIME_CONFIG['preprocess_path'])) if os.path.exists(
            "{}/saved_cumsum.npy".format(
                RUNTIME_CONFIG['preprocess_path'])) else None

    if os.path.isdir("{}/count".format(RUNTIME_CONFIG['preprocess_path'])):
        for f in os.listdir("{}/count".format(
                RUNTIME_CONFIG['preprocess_path'])):
            if f.endswith("txt"):
                os.remove("{}/count/{}".format(
                    RUNTIME_CONFIG['preprocess_path'], f))

    if os.path.isdir("{}/enumerated".format(RUNTIME_CONFIG['preprocess_path'])):
        for f in os.listdir("{}/enumerated".format(
                RUNTIME_CONFIG['preprocess_path'])):
            if f.endswith("txt"):
                os.remove("{}/enumerated/{}".format(
                    RUNTIME_CONFIG['preprocess_path'], f))

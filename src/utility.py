"""This file contains utility functions and methods used across different modules"""
from config import RUNTIME_CONFIG
from common import RunningStyle
from sys import platform
import subprocess
import os
from parse import RulelistReader
import numpy as np
import sys
from collections import OrderedDict
import hashlib

sys.path.append('../trie')

from chartrie_wrapper import CharTrieWrapper


def convert_str_length_to_int(length):
    """ Convert a position in char to integer """
    if type(length) is int:
        return length
    if length in "0123456789":
        return int(length)
    elif length <= "Z" and length >= "A":
        return ord(length) - ord("A") + 10
    elif length == "z":
        return float("inf")
    elif length == "*":
        return RUNTIME_CONFIG['min_cut_length']
    elif length == "-":
        return RUNTIME_CONFIG['min_cut_length'] - 1
    elif length == "+":
        return RUNTIME_CONFIG['min_cut_length'] + 1
    elif length == "l":  # We Reject Q directly. So no memorization, then l serves same func as z
        return float("inf")
    elif length == "m":
        raise Exception("Unhandled Length Char")
    elif length >= "a" and length <= "k":
        raise Exception("Unhandled Length Char")
    elif length == "p":
        raise Exception("p with positional rules is not handleable")
    else:
        raise Exception("Unknown Length Char:{}".format(length))


def char_is_printable(char):
    """ Check if char is ascii number (<128) and printable """
    if ord(char) >= 32 and ord(char) <= 126:
        return True
    else:
        return False


def write_rules_to_file(out_addr, rules, batch_id):
    """ write a rule to file, HC only
    
    Args:
        out_addr: output directory

        rules: a list of rules

        batch_id: idx of the batch, starting from 0. Should not be used
    """
    policy_in_rule_string = RUNTIME_CONFIG['password_policy'].to_rule_string(
        RUNTIME_CONFIG.is_jtr())

    with open(out_addr, 'w+') as f:
        if RUNTIME_CONFIG.is_jtr():
            raise Exception("Not Intended For JtR")

        else:
            for r in rules:
                f.write("{}\n".format(
                    r.raw))  # HC use external checking for password policy


def write_rule_to_file(out_addr, rule, rule_idx):
    """ write a rule to file, based on JtR/HC style. 
    
    Args:
        out_addr: output directory

        rule: the parsed rule

        rule_idx: idx of the rule, starting from 0.
    """
    policy_in_rule_string = RUNTIME_CONFIG['password_policy'].to_rule_string(
        RUNTIME_CONFIG.is_jtr())

    with open(out_addr, 'w+') as f:
        if RUNTIME_CONFIG.is_jtr():
            f.write("[List.Rules:rule{}]\n".format(rule_idx))
            f.write("{}{}\n".format(
                rule.raw,
                policy_in_rule_string))  # JTR embeds password policy in rules
        else:
            f.write("{}\n".format(
                rule.raw))  # HC use external checking for password policy


def forward_batched_words_and_batched_rules(
        wordlist_name, number_of_rule_batches, count_for_this_batch_of_words,
        preprocess_path, external_bash_process):
    """ HC only """
    # Call JtR to Forward
    if RUNTIME_CONFIG.is_jtr():
        raise Exception("Not Intended For JtR")

    # Call HC to Forward
    else:
        for rule_batch_id in range(number_of_rule_batches):
            cmd = RUNTIME_CONFIG[
                'executable_path'] + " {}/{} -r {}/rulesbatch{}.rule --stdout {} --no_filter_input --count_only\n".format(
                    preprocess_path, wordlist_name, preprocess_path,
                    rule_batch_id,
                    RUNTIME_CONFIG['password_policy'].to_arg_string())

            external_bash_process.stdin.write(bytes(cmd, 'utf-8'))
            external_bash_process.stdin.flush()

            line = external_bash_process.stdout.readline().decode()

            try:
                number = int(line.strip())
            except:
                raise Exception("Parsing Number Error {}".format(line))

            count_for_this_batch_of_words[rule_batch_id] += number

    # Clean Workspace


def forward_a_rule_to_an_address(wordlist_addr,
                                 rule,
                                 out_addr,
                                 word_list_prefix="../data/wordlists",
                                 debug=False):
    """ Given a wordlist address, rule in string format, and out_address, call executable to enumerate the results.

    Args:
        wordlist_addr: the wordlist address

        rule: the parsed rule

        out_addr: output file address

        word_list_prefix: wordlist directory

        debug: debug mode, safe intermediate results.
    """
    idx = 0  # tmp use

    os.remove(out_addr) if os.path.exists(out_addr) else None  # cleaning

    # Prepare JtR running Config
    write_rule_to_file("tmp_rule_generate.lst", rule, idx)

    # Call JtR to Forward
    if RUNTIME_CONFIG.is_jtr():
        cmd = RUNTIME_CONFIG[
            'executable_path'] + ' --config=tmp_rule_generate.lst --stdout --wordlist="{}/{}" --rules="rule{}"'.format(
                word_list_prefix, wordlist_addr, idx)

    # Call HC to Forward
    else:
        cmd = RUNTIME_CONFIG[
            'executable_path'] + ' {}/{} -r tmp_rule_generate.lst --stdout {}'.format(
                word_list_prefix, wordlist_addr,
                RUNTIME_CONFIG['password_policy'].to_arg_string())

    with open(out_addr,
              'w+') as fout:  # context manager is OK since `call` blocks :)
        if platform != "win32":  # platform spefic cmd
            subprocess.call(
                cmd, shell=True, stdout=fout, executable='/bin/bash')
        else:
            subprocess.call(cmd, stdout=fout)

    # Clean Workspace
    if debug == False:
        os.remove("tmp_rule_generate.lst") if os.path.exists(
            "tmp_rule_generate.lst") else None


def forward_a_rule_to_an_address_and_forward_count(
        wordlist_addr,
        rule,
        out_prefix,
        rule_idx,
        word_list_prefix="../data/wordlists",
        debug=False):
    """ forward a rule to file and get count as well """
    idx = 0  # tmp use

    out_addr = "{}/enumerated/rule{}.txt".format(out_prefix, rule_idx)
    count_addr = "{}/count/rule{}.txt".format(out_prefix, rule_idx)
    tmp_1_file_addr = "{}/tmp_1.txt".format(out_prefix)

    os.remove(out_addr) if os.path.exists(out_addr) else None  # cleaning
    os.remove(count_addr) if os.path.exists(count_addr) else None  # cleaning
    os.remove(tmp_1_file_addr) if os.path.exists(
        tmp_1_file_addr) else None  # cleaning

    # Prepare JtR running Config
    write_rule_to_file("tmp_rule_generate.lst", rule, idx)

    # Call JtR to Forward
    if RUNTIME_CONFIG.is_jtr():
        cmd = RUNTIME_CONFIG[
            'executable_path'] + ' --config=tmp_rule_generate.lst --stdout --wordlist="{}/{}" --rules="rule{}"'.format(
                word_list_prefix, wordlist_addr, idx)

    # Call HC to Forward
    else:
        cmd = RUNTIME_CONFIG[
            'executable_path'] + ' {}/{} -r tmp_rule_generate.lst --stdout {}'.format(
                word_list_prefix, wordlist_addr,
                RUNTIME_CONFIG['password_policy'].to_arg_string())

    with open(tmp_1_file_addr,
              'w+') as fout:  # context manager is OK since `call` blocks :)
        if platform != "win32":  # platform spefic cmd
            subprocess.call(
                cmd, shell=True, stdout=fout, executable='/bin/bash')
        else:
            subprocess.call(cmd, stdout=fout)

    # Sort File
    sort_cmd = "LC_ALL=C sort " + tmp_1_file_addr
    with open(out_addr,
              'w+') as fout:  #context manager is OK since `call` blocks :)
        subprocess.call(
            sort_cmd, shell=True, stdout=fout, executable='/bin/bash')

    cmd_count = 'wc -l < {}'.format(out_addr)
    with open(count_addr, "w+") as fout:
        if platform != "win32":  # platform spefic cmd
            subprocess.call(
                cmd_count, shell=True, stdout=fout, executable='/bin/bash')
        else:
            subprocess.call(cmd_count, stdout=fout)

    # Clean Workspace
    if debug == False:
        os.remove("tmp_rule_generate.lst") if os.path.exists(
            "tmp_rule_generate.lst") else None
        os.remove(tmp_1_file_addr) if os.path.exists(
            tmp_1_file_addr) else None  # cleaning


def forward_a_rule_to_an_address_count_only(
        wordlist_addr,
        rule,
        out_addr,
        word_list_prefix="../data/wordlists",
        debug=False):
    """ Given a wordlist address, rule in string format, and out_address, call executable to count number of guesses and write to file

    Args:
        wordlist_addr: the wordlist address
        rule: rule in string form
        out_addr: output file address
        word_list_prefix: wordlist directory
    """
    idx = 0  # tmp use

    os.remove(out_addr) if os.path.exists(out_addr) else None  # cleaning

    write_rule_to_file("tmp_rule_generate.lst", rule, idx)

    # Call JtR to Forward
    if RUNTIME_CONFIG.is_jtr():
        cmd = RUNTIME_CONFIG[
            'executable_path'] + ' --config=tmp_rule_generate.lst --stdout --wordlist="{}/{}" --rules="rule{}" | wc -l'.format(
                word_list_prefix, wordlist_addr, idx)

    # Call HC to Forward
    else:
        cmd = RUNTIME_CONFIG[
            'executable_path'] + ' {}/{} -r tmp_rule_generate.lst --stdout {} --no_filter_input --count_only'.format(
                word_list_prefix, wordlist_addr,
                RUNTIME_CONFIG['password_policy'].to_arg_string())

    with open(out_addr,
              'w+') as fout:  # context manager is OK since `call` blocks :)
        if platform != "win32":  # platform spefic cmd
            subprocess.call(
                cmd, shell=True, stdout=fout, executable='/bin/bash')
        else:
            subprocess.call(cmd, stdout=fout)

    # Clean Workspace
    if debug == False:
        os.remove("tmp_rule_generate.lst") if os.path.exists(
            "tmp_rule_generate.lst") else None


def forward_a_rule_and_get_count(wordlist_addr,
                                 rule,
                                 out_addr,
                                 word_list_prefix="../data/wordlists",
                                 debug=False):
    """ Given a wordlist address, parsed rule, and out_address, call executable to count number of guesses and write to file

    Args:
        wordlist_addr: the wordlist address
        rule: rule in string form
        out_addr: output file address
        word_list_prefix: wordlist directory
    """
    forward_a_rule_to_an_address_count_only(wordlist_addr, rule, out_addr,
                                            word_list_prefix, debug)

    with open(out_addr, "r") as f:
        lines = f.readlines()
        try:
            number = int(lines[0].strip())
        except:
            number = 0

    # Clean Workspace
    if debug == False:
        os.remove(out_addr) if os.path.exists(out_addr) else None

    return number


mpa = dict.fromkeys(range(32))


def clean_word(word):
    """ remove non-ascii printables """
    word = word.translate(mpa)
    word.replace("\n", "")
    word.replace("\r", "")
    return word


def read_wordlist(wordlist_name,
                  wordlist_dir="../data/wordlists/",
                  remove_hash=True):
    """ Read word into dict.

    Args:
        wordlist_name: the filename of the wordlist.

        wordlist_dir: the directory the wordlist is in.

        remove_hash: Whether to remove lines that start with "#!comment:".

    Returns:
        Dictionary of words. Indexing starts from 0.
    """

    wordlist_addr = "{}/{}".format(wordlist_dir, wordlist_name)
    wordlist = {} if RUNTIME_CONFIG.is_jtr() else OrderedDict()

    with open(wordlist_addr) as f:
        for line in f:
            line = clean_word(line)

            if len(line) > RUNTIME_CONFIG['max_password_length']:
                print(
                    "Oversize Word: {} in wordlist file, ignored".format(line))
            if remove_hash == True and line.startswith('#!comment:'):
                print(
                    "Comments: {} found in wordlist file, ignored".format(line))

            if line == "" and RUNTIME_CONFIG.is_jtr(
            ):  # JtR doesn't take in empty line.
                continue

            if line not in wordlist:
                wordlist[line] = len(wordlist)
            else:
                if line != "":
                    print("Duplicate Word: {} in wordlist file, ignored".format(
                        line))

    return wordlist


def read_rulelist(rulelist_name, rulelist_prefix):
    """ read rulelist and parse them """
    return RulelistReader.read_and_parse_rule_list(rulelist_name,
                                                   rulelist_prefix)


def get_name_of_a_rule(transformation):
    """ get a transformation, return its name in string. """
    if transformation[0] == ":":
        return "colon"
    elif transformation[0] == "{":
        return "left_curly_bracket"
    elif transformation[0] == "}":
        return "right_curly_bracket"
    elif transformation[0] == "[":
        return "left_square_bracket"
    elif transformation[0] == "]":
        return "right_square_bracket"
    elif transformation[0] in "lucCtrdfqkKEPISVMQ46":
        return transformation[0]
    elif transformation[0] in "pRL":
        if RUNTIME_CONFIG.is_jtr():  # JTR
            return transformation[0]
        else:  # ELSE HASHCAT, pN, LN, RN
            return "{}_N".format(transformation[0])
    elif transformation[0] in "'":
        return "prime_N"
    elif transformation[0] in "TDzZyY":
        return "{}_N".format(transformation[0])
    elif transformation[0] == "+":
        if RUNTIME_CONFIG.is_hc():
            return "plus_N"
        else:
            return "mode"
    elif transformation[0] == "-":
        if RUNTIME_CONFIG.is_hc():
            return "minus_N"
        else:
            return "flag"
    elif transformation[0] == ".":
        return "period_N"
    elif transformation[0] == ",":
        return "comma_N"
    elif transformation[0] == "$":
        return "dollar_X"
    elif transformation[0] == "^":
        return "caret_X"
    elif transformation[0] in "io":
        return "{}_N_X".format(transformation[0])
    elif transformation[0] == "A":
        return "A_N_str"
    elif transformation[0] in "xO":
        return "{}_N_M".format(transformation[0])
    elif transformation[0] == '*':
        return "asterisk_N_M"
    elif transformation[0] in "12":
        return "mode"
    elif transformation[0] == "X":
        return "X_N_M_I"
    elif transformation[0] == "v":
        return "v_V_N_M"
    elif transformation[0] == ">":
        return "greater_than_N"
    elif transformation[0] == "<":
        return "less_than_N"
    elif transformation[0] == "_":
        return "underscore_N"
    elif transformation[0] == "!":
        if RUNTIME_CONFIG[
                'running_style'] == RunningStyle.JTR and transformation[
                    1] == "?":
            return "bang_question_C"
        else:
            return "bang_X"
    elif transformation[0] == "/":
        if RUNTIME_CONFIG[
                'running_style'] == RunningStyle.JTR and transformation[
                    1] == "?":
            return "slash_question_C"
        else:
            return "slash_X"
    elif transformation[0] == "=":
        if RUNTIME_CONFIG[
                'running_style'] == RunningStyle.JTR and transformation[
                    2] == "?":
            return "equal_N_question_C"
        else:
            return "equal_N_X"
    elif transformation[0] == "(":
        if RUNTIME_CONFIG[
                'running_style'] == RunningStyle.JTR and transformation[
                    1] == "?":
            return "left_paren_question_C"
        else:
            return "left_paren_X"
    elif transformation[0] == ")":
        if RUNTIME_CONFIG[
                'running_style'] == RunningStyle.JTR and transformation[
                    1] == "?":
            return "right_paren_question_C"
        else:
            return "right_paren_X"
    elif transformation[0] == "%":
        if RUNTIME_CONFIG[
                'running_style'] == RunningStyle.JTR and transformation[
                    2] == "?":
            return "percent_N_question_C"
        else:
            return "percent_N_X"
    elif transformation[0] == "@":
        if RUNTIME_CONFIG[
                'running_style'] == RunningStyle.JTR and transformation[
                    1] == "?":
            return "at_question_C"
        else:
            return "at_X"
    elif transformation[0] == "e":
        if RUNTIME_CONFIG[
                'running_style'] == RunningStyle.JTR and transformation[
                    1] == "?":
            return "e_question_C"
        else:
            return "e_X"
    elif transformation[0] == "s":
        if RUNTIME_CONFIG[
                'running_style'] == RunningStyle.JTR and transformation[
                    1] == "?":
            return "s_question_C_Y"
        else:
            return "s_X_Y"
    else:
        raise Exception(
            "Not implemented for transformation: {}".format(transformation))


def sizeof_fmt(num, suffix='B'):
    """ Convert Memory Usage To Byte size """
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def read_passwords(addr):
    """ read passwords as list from a file """
    with open(addr) as f:
        lines = f.readlines()

    pwlist = [clean_word(line) for line in lines]
    pwlist = [x for x in pwlist if x != ""]

    return pwlist


def filter_passwords_with_password_policy(pwlist):
    """ filter passwords that don't meet password policy """
    pw_policy = RUNTIME_CONFIG['password_policy']

    def check_all_ascii(line):
        return all(ord(c) < 128 for c in line)

    def check_non_control(line):
        return all(ord(c) > 31 for c in line)

    filtered_pwds = []  # not meet pw policy
    not_filtered_pwds = []  # pwds meet pw policy
    for idx, pw in enumerate(pwlist):
        filtered = False

        if (len(pw) >= pw_policy.length) == False:
            filtered = True

        if pw_policy.digit == True:
            if any(char.isdigit() for char in pw) == False:
                filtered = True

        if pw_policy.letter == True:
            if any(char.isalpha() for char in pw) == False:
                filtered = True

        if pw_policy.lower == True:
            if any(char.islower() for char in pw) == False:
                filtered = True

        if pw_policy.upper == True:
            if any(char.isupper() for char in pw) == False:
                filtered = True

        if filtered == True:
            filtered_pwds.append((idx, pw))

        else:
            not_filtered_pwds.append((idx, pw))

    return not_filtered_pwds, filtered_pwds


def escape_pw_for_look(string):
    """ escape a password for look cmd """
    string = string.replace("\\", "\\\\")
    string = string.replace('"', '\\"')
    string = string.replace("'", "\\'")
    return string


def get_look_cmd(string, password_addr):
    """ generate look command in string for binary search """
    if platform == "linux" or platform == "linux2":  # linux
        first_part = r"LC_ALL=C {} -b -- ".format(
            RUNTIME_CONFIG['binary_search_file_executable'])
    elif platform == "darwin":
        first_part = r"LC_ALL=C {} -- ".format(
            RUNTIME_CONFIG['binary_search_file_executable'])
    elif platform == "win32":
        first_part = r"LC_ALL=C {} -b -- ".format(
            RUNTIME_CONFIG['binary_search_file_executable'])

    string = escape_pw_for_look(string)

    second_part = r"$'{}\t' {}".format(string, password_addr)

    return "{}{};echo ''\n".format(
        first_part, second_part)  # adding echo to avoid empty output


def build_trie_from_wordlist(wordlist):
    """ build a char trie from wordlist """
    t = CharTrieWrapper(wordlist)
    os.remove("dump.trie") if os.path.exists("dump.trie") else None
    return t


def has_generated_data():
    """ Check if one configuration has generated data """
    # Compute Hashes
    wordlist_hash = hashlib.md5(
        open(RUNTIME_CONFIG['wordlist_path']['addr'],
             'rb').read()).hexdigest()  # get md5 hash
    rulelist_hash = hashlib.md5(
        open(RUNTIME_CONFIG['rulelist_path']['addr'],
             'rb').read()).hexdigest()  # get md5 hash
    password_policy_string = RUNTIME_CONFIG['password_policy'].to_debug_string()
    type_j = "1" if RUNTIME_CONFIG.is_jtr() else "0"

    hash_file_addr = "{}/hashes.txt".format(RUNTIME_CONFIG['preprocess_path'])

    if os.path.exists(hash_file_addr):
        with open(hash_file_addr) as f:
            content = f.readlines()

        if len(content) >= 4 and content[0].strip(
        ) == wordlist_hash and content[1].strip() == rulelist_hash and content[
                2].strip("\r\n") == password_policy_string and content[3].strip(
                    "\r\n") == type_j:
            return True

    return False


def store_generated_data_hash():
    """ Store hashes for one configuration """
    # Compute Hashes
    wordlist_hash = hashlib.md5(
        open(RUNTIME_CONFIG['wordlist_path']['addr'],
             'rb').read()).hexdigest()  # get md5 hash
    rulelist_hash = hashlib.md5(
        open(RUNTIME_CONFIG['rulelist_path']['addr'],
             'rb').read()).hexdigest()  # get md5 hash
    password_policy_string = RUNTIME_CONFIG['password_policy'].to_debug_string()
    type_j = "1" if RUNTIME_CONFIG.is_jtr() else "0"

    hash_file_addr = "{}/hashes.txt".format(RUNTIME_CONFIG['preprocess_path'])
    f = open(hash_file_addr, 'w')
    f.write(wordlist_hash + "\n")  # python will convert \n to os.linesep
    f.write(rulelist_hash + "\n")  # python will convert \n to os.linesep
    f.write(password_policy_string + "\n")
    f.write(type_j + "\n")
    f.close()


def has_count_data():
    """ Check if one configuration has generated data """
    # Compute Hashes
    wordlist_hash = hashlib.md5(
        open(RUNTIME_CONFIG['wordlist_path']['addr'],
             'rb').read()).hexdigest()  # get md5 hash
    rulelist_hash = hashlib.md5(
        open(RUNTIME_CONFIG['rulelist_path']['addr'],
             'rb').read()).hexdigest()  # get md5 hash
    password_policy_string = RUNTIME_CONFIG['password_policy'].to_debug_string()
    type_j = "1" if RUNTIME_CONFIG.is_jtr() else "0"

    hash_file_addr = "{}/count_hashes.txt".format(
        RUNTIME_CONFIG['preprocess_path'])

    if os.path.exists(hash_file_addr):
        with open(hash_file_addr) as f:
            content = f.readlines()

        if len(content) >= 4 and content[0].strip(
        ) == wordlist_hash and content[1].strip() == rulelist_hash and content[
                2].strip("\r\n") == password_policy_string and content[3].strip(
                    "\r\n") == type_j:
            return True

    return False


def store_count_data_hash():
    """ Store hashes for one configuration """
    # Compute Hashes
    wordlist_hash = hashlib.md5(
        open(RUNTIME_CONFIG['wordlist_path']['addr'],
             'rb').read()).hexdigest()  # get md5 hash
    rulelist_hash = hashlib.md5(
        open(RUNTIME_CONFIG['rulelist_path']['addr'],
             'rb').read()).hexdigest()  # get md5 hash
    password_policy_string = RUNTIME_CONFIG['password_policy'].to_debug_string()
    type_j = "1" if RUNTIME_CONFIG.is_jtr() else "0"

    hash_file_addr = "{}/count_hashes.txt".format(
        RUNTIME_CONFIG['preprocess_path'])
    f = open(hash_file_addr, 'w')
    f.write(wordlist_hash + "\n")  # python will convert \n to os.linesep
    f.write(rulelist_hash + "\n")  # python will convert \n to os.linesep
    f.write(password_policy_string + "\n")
    f.write(type_j + "\n")
    f.close()


def store_counts_to_file(counts, cumsum):
    """  store counts to files """
    preprocess = RUNTIME_CONFIG['preprocess_path']
    np.save("{}/saved_counts".format(preprocess), counts)
    np.save("{}/saved_cumsum".format(preprocess), cumsum)


def restore_counts_from_file():
    """ restore counts/cumsum from files """
    preprocess = RUNTIME_CONFIG['preprocess_path']
    counts = np.load("{}/saved_counts.npy".format(preprocess))
    cumsum = np.load("{}/saved_cumsum.npy".format(preprocess))
    return counts, cumsum

import sys
from sys import path as sys_path
from os import path as os_path
import unittest
from time import time
import shutil
from subprocess import Popen, PIPE

sys_path.append(os_path.abspath('../src'))

from config import RUNTIME_CONFIG
from config import john_nick_names, hc_nick_names
from common import PasswordPolicyConf, FilePath
from argparsing import setup_args, parse_args
from guess_count import GuessCount
from tokenstr import TokenString
from utility import read_passwords,read_wordlist,read_rulelist,get_look_cmd,build_trie_from_wordlist
from preprocess import precomputation
from invert_rule import invert_one_rule
from demo_common import match_inversion_result, search_exist_data, search_trie, estimate_guess_number, clean_hashes


class CountTest(unittest.TestCase):

    def run_guess_count(self):
        external_bash_process = Popen(['/bin/bash'], stdin=PIPE, stdout=PIPE)

        try:
            rulelist = read_rulelist(RUNTIME_CONFIG['rulelist_path']['name'], RUNTIME_CONFIG['rulelist_path']['prefix'])

            rulelist = precomputation(rulelist)

            wordlist = read_wordlist(RUNTIME_CONFIG['wordlist_path']['name'], RUNTIME_CONFIG['wordlist_path']['prefix'])

            # Computing Guess Count
            counts, cumsum = GuessCount.get_counts(wordlist, rulelist, RUNTIME_CONFIG['preprocess_path'])

            # Read other things
            pwlist = read_passwords(RUNTIME_CONFIG['pwlist_path']['addr'])
            trie = build_trie_from_wordlist(wordlist)

            # Start inverting rules
            is_guessable = [False] * len(pwlist)
            is_enable_regex = RUNTIME_CONFIG['enable_regex']
            is_debug = RUNTIME_CONFIG['debug']
            lookup_threshold = RUNTIME_CONFIG['lookup_threshold']
            tokenized_pwds = [TokenString(password) for password in pwlist]

            # Invert rules (with special memory handling and other staff)
            for r_idx, r in enumerate(rulelist):

                if r.feasibility.is_invertible(): # Invertible. If the number of preimages blows up, use the trie.
                    for pw_idx, (token_pwd, pwd) in enumerate(zip(tokenized_pwds,pwlist)):
                        result = invert_one_rule(token_pwd,r,is_enable_regex,r.feasibility.special_idx)
                        if result.is_normal():
                            if result.get_number_of_strings() <= lookup_threshold:
                                ret_vals = match_inversion_result(result, wordlist)
                            else:
                                ret_vals = search_trie(result, trie)

                            if len(ret_vals) != 0:
                                for v in ret_vals:
                                    estimated, _, _ = estimate_guess_number(counts, cumsum, v, r_idx, wordlist)
                                    if estimated != pw_idx + 1:
                                        raise Exception("Test Failed")

                        elif result.is_out_of_scope():
                            raise Exception("Test Failed")

                        else:
                            raise Exception("Test Failed")

                elif r.feasibility.is_optimizable(): # Uninvertible. If it cannot be handled, do a binary search.
                    # Where the binary file is stored:
                    enumerated_data_addr = "{}/enumerated/rule{}.txt".format(RUNTIME_CONFIG['preprocess_path'],r_idx)
                    for pw_idx, (token_pwd, pwd) in enumerate(zip(tokenized_pwds,pwlist)):
                        result = invert_one_rule(token_pwd,r,is_enable_regex)

                        if result.is_normal():
                            if result.get_number_of_strings() <= lookup_threshold:
                                ret_vals = match_inversion_result(result, wordlist)
                            else:
                                ret_vals = search_exist_data(pwd,enumerated_data_addr,external_bash_process)
                            if len(ret_vals) != 0:
                                for v in ret_vals:
                                    estimated, _, _ = estimate_guess_number(counts, cumsum, v, r_idx, wordlist)
                                    if estimated != pw_idx + 1:
                                        raise Exception("Test Failed")

                        elif result.is_out_of_scope():
                            ret_vals = search_exist_data(pwd,enumerated_data_addr,external_bash_process)
                            if len(ret_vals) != 0:
                                for v in ret_vals:
                                    estimated, _, _ = estimate_guess_number(counts, cumsum, v, r_idx, wordlist)
                                    if estimated != pw_idx + 1:
                                        print(pw_idx, pwd)
                                        raise Exception("Test Failed")
                        else:
                            raise Exception("Test Failed")

                else: # Fall back to binary search.
                    # Where the binary file is stored
                    enumerated_data_addr = "{}/enumerated/rule{}.txt".format(RUNTIME_CONFIG['preprocess_path'],r_idx)
                    for pw_idx, (token_pwd, pwd) in enumerate(zip(tokenized_pwds,pwlist)):
                        ret_vals = search_exist_data(pwd,enumerated_data_addr,external_bash_process)

                        if len(ret_vals) != 0:
                            for v in ret_vals:
                                estimated, _, _ = estimate_guess_number(counts, cumsum, v, r_idx, wordlist)
                                if estimated != pw_idx + 1:
                                    raise Exception("Test Failed")

        except:
            raise

        finally:
            clean_hashes()

    def test_hc_file_one(self):
        import argparse, sys
        sys.argv = ['demo_guess_count_file.py', '-w', '../data/wordlists/test_demo_file_HC.lst', '-r', '../data/rulelists/test_demo_file_HC.rule', '-p', '../data/testsets/test_demo_file_HC1.txt', '-s', 'h']
        args = setup_args() # set up args
        parse_args(args)
        RUNTIME_CONFIG['batch_size_of_words'] = 1

        self.run_guess_count()      

    def test_hc_file_two(self): 
        import argparse, sys
        sys.argv = ['demo_guess_count_file.py', '-w', '../data/wordlists/test_demo_file_HC.lst', '-r', '../data/rulelists/test_demo_file_HC.rule', '-p', '../data/testsets/test_demo_file_HC2.txt', '-s', 'h', '--length=20']
        args = setup_args() # set up args
        parse_args(args)
        RUNTIME_CONFIG['batch_size_of_words'] = 1

        self.run_guess_count()

    def test_hc_file_three(self): 
        import argparse, sys
        sys.argv = ['demo_guess_count_file.py', '-w', '../data/wordlists/test_demo_file_HC.lst', '-r', '../data/rulelists/test_demo_file_HC.rule', '-p', '../data/testsets/test_demo_file_HC3.txt', '-s', 'h']
        args = setup_args() # set up args
        parse_args(args)
        RUNTIME_CONFIG['batch_size_of_words'] = 1024 * 1024

        self.run_guess_count()


    def test_jtr_file_one(self):
        import argparse, sys
        sys.argv = ['demo_guess_count_file.py', '-w', '../data/wordlists/test_demo_file_JtR.lst', '-r', '../data/rulelists/test_demo_file_JtR.rule', '-p', '../data/testsets/test_demo_file_JtR1.txt', '-s', 'j']
        args = setup_args() # set up args
        parse_args(args)

        self.run_guess_count()
        
    def test_jtr_file_two(self):
        import argparse, sys
        sys.argv = ['demo_guess_count_file.py', '-w', '../data/wordlists/test_demo_file_JtR.lst', '-r', '../data/rulelists/test_demo_file_JtR.rule', '-p', '../data/testsets/test_demo_file_JtR2.txt', '-s', 'j', '--length=20']
        args = setup_args() # set up args
        parse_args(args)

        self.run_guess_count()

if __name__ == "__main__":

    #Run Unit Test
    rule_suite = unittest.TestLoader().loadTestsFromTestCase(CountTest)
    rule_runner = unittest.TextTestRunner()
    rule_runner.run(rule_suite)


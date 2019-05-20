from sys import path as sys_path
from os import path as os_path
from subprocess import Popen, PIPE
import time
import logging
import warnings
import numpy as np

sys_path.append(os_path.abspath('../src'))

from config import RUNTIME_CONFIG
from config import john_nick_names, hc_nick_names
from common import PasswordPolicyConf, FilePath
from argparsing import setup_args, parse_args
from guess_count import GuessCount
from tokenstr import TokenString
from utility import read_passwords,read_wordlist,read_rulelist,get_look_cmd,build_trie_from_wordlist
from utility import filter_passwords_with_password_policy
from preprocess import precomputation
from invert_rule import invert_one_rule
from demo_common import match_inversion_result, search_exist_data, search_trie, estimate_guess_number


def start_processing():
    """ Take in a wordlist, rulelist and test set, outputs the guessability and guess number of each pwd in the test set.

    Steps:
        1. read rulelist and do precomputation (detect invertibility)
        2. read wordlist/pwlist, and get count for each rule
        3. Rule Inversion (for each rule, invert all pwds)
    """

    stime = time.perf_counter()

    ##################### Precomputation and Other Preparation #####################
    # initialize a bash exe for communication
    external_bash_process = Popen(['/bin/bash'], stdin=PIPE, stdout=PIPE)

    # Logging Basic Info
    logging.basicConfig(filename=RUNTIME_CONFIG.get_log_addr(),level=logging.DEBUG)
    logging.info("Starting Time: {}\n\nConfigurations: {}\n".format(time.strftime("%Y-%m-%d %H:%M"), RUNTIME_CONFIG.short_config_string()))
    logging.info("PasswordPolicy: {}\n".format(RUNTIME_CONFIG['password_policy'].to_debug_string()))

    print("Reading Rulelist\n")
    rulelist = read_rulelist(RUNTIME_CONFIG['rulelist_path']['name'], RUNTIME_CONFIG['rulelist_path']['prefix'])

    print("Start Precomputation\n")
    rulelist = precomputation(rulelist)

    print("Reading Wordlist and Password Set\n")
    wordlist = read_wordlist(RUNTIME_CONFIG['wordlist_path']['name'], RUNTIME_CONFIG['wordlist_path']['prefix'])

    # Computing Guess Count
    counts, cumsum = GuessCount.get_counts(wordlist, rulelist, RUNTIME_CONFIG['preprocess_path'])

    # read other things
    pwlist = read_passwords(RUNTIME_CONFIG['pwlist_path']['addr'])
    # filter out pwds not consistent with the policy
    not_filtered_pwds, filtered_pwds = filter_passwords_with_password_policy(pwlist)
    trie = build_trie_from_wordlist(wordlist)

    ##################### Start Inversion #####################
    print("Start Inverting Rules\n")
    i_time = time.perf_counter()
    # guessability of pwds
    is_guessable = [False] * len(pwlist)
    is_enable_regex = RUNTIME_CONFIG['enable_regex']
    is_debug = RUNTIME_CONFIG['debug']
    lookup_threshold = RUNTIME_CONFIG['lookup_threshold']
    # tokenize pwds once.
    tokenized_pwds = [TokenString(pwd) for pw_idx, pwd in not_filtered_pwds]

    # invert rules (with special memory handling and other staff)
    for r_idx, r in enumerate(rulelist):
        if is_debug == True:
            print(r.raw)
            
        if r.feasibility.is_invertible(): # invertible, if blow up, use trie
            for token_pwd, (pw_idx, pwd) in zip(tokenized_pwds,not_filtered_pwds):
                result = invert_one_rule(token_pwd,r,is_enable_regex,r.feasibility.special_idx)
                if result.is_normal():
                    if result.get_number_of_strings() <= lookup_threshold:
                        ret_vals = match_inversion_result(result, wordlist)
                    else:
                        ret_vals = search_trie(result, trie)

                    if len(ret_vals) != 0:
                        is_guessable[pw_idx] = True
                        for v in ret_vals:
                            logging.info("\nPasswordIdx:{}\nPassword:{}\nRule:{}\nWord:{}\nGuess:{} ( {} - {} )\n".format(pw_idx, pwd, r.raw, v, *estimate_guess_number(counts, cumsum, v, r_idx, wordlist)))

                elif result.is_out_of_scope():
                    ret_vals = []
                    logging.info("Inversion error for {}(RL) {}(pw), error msg: {}\n".format(r.raw, pwd, "out_of_scope"))
                    print("Inversion error for {}(RL) {}(pw), error msg: {}".format(r.raw, pwd, "out_of_scope"))

                else:
                    ret_vals = []
                    logging.info("Inversion error for {}(RL) {}(pw), error msg: {}\n".format(r.raw, pwd, result.error_msg))
                    print("Inversion error for {}(RL) {}(pw), error msg: {}".format(r.raw, pwd, result.error_msg))

        elif r.feasibility.is_optimizable(): # uninvertible, if cannot handle, binary
            # where the binary file is stored
            enumerated_data_addr = "{}/enumerated/rule{}.txt".format(RUNTIME_CONFIG['preprocess_path'],r_idx)
            for token_pwd, (pw_idx, pwd) in zip(tokenized_pwds,not_filtered_pwds):
                result = invert_one_rule(token_pwd,r,is_enable_regex)

                if result.is_normal():
                    if result.get_number_of_strings() <= lookup_threshold:
                        ret_vals = match_inversion_result(result, wordlist)
                    else:
                        ret_vals = search_exist_data(pwd,enumerated_data_addr,external_bash_process)
                    
                    if len(ret_vals) != 0:
                        is_guessable[pw_idx] = True
                        for v in ret_vals:
                            logging.info("\nPasswordIdx:{}\nPassword:{}\nRule:{}\nWord:{}\nGuess:{} ( {} - {} )\n".format(pw_idx, pwd, r.raw, v, *estimate_guess_number(counts, cumsum, v, r_idx, wordlist)))

                elif result.is_out_of_scope():
                    ret_vals = search_exist_data(pwd,enumerated_data_addr,external_bash_process)
                    if len(ret_vals) != 0:
                        is_guessable[pw_idx] = True
                        for v in ret_vals:
                            logging.info("\nPasswordIdx:{}\nPassword:{}\nRule:{}\nWord:{}\nGuess:{} ( {} - {} )\n".format(pw_idx, pwd, r.raw, v, *estimate_guess_number(counts, cumsum, v, r_idx, wordlist)))
                else:
                    ret_vals = []
                    logging.info("Inversion error for {}(RL) {}(pw), error msg: {}\n".format(r.raw, pwd, result.error_msg))
                    print("Inversion error for {}(RL) {}(pw), error msg: {}".format(r.raw, pwd, result.error_msg))

        else: # binary
            # where the binary file is stored
            enumerated_data_addr = "{}/enumerated/rule{}.txt".format(RUNTIME_CONFIG['preprocess_path'],r_idx)
            for token_pwd, (pw_idx, pwd) in zip(tokenized_pwds,not_filtered_pwds):
                ret_vals = search_exist_data(pwd,enumerated_data_addr,external_bash_process)

                if len(ret_vals) != 0:
                    is_guessable[pw_idx] = True
                    for v in ret_vals:
                        logging.info("\nPasswordIdx:{}\nPassword:{}\nRule:{}\nWord:{}\nGuess:{} ( {} - {} )\n".format(pw_idx, pwd, r.raw, v, *estimate_guess_number(counts, cumsum, v, r_idx, wordlist)))
    ##################### End of Inversion #####################
    
    # Write Not Guessable Data
    for pw_idx, pwd in filtered_pwds:
        logging.info("\nPasswordIdx:{}\nPassword:{}\nNot Guessable\n".format(pw_idx, pwd))

    for is_guessed, (pw_idx, pwd) in zip(is_guessable, not_filtered_pwds):
        if is_guessed == False:
            logging.info("\nPasswordIdx:{}\nPassword:{}\nNot Guessable\n".format(pw_idx, pwd))

    logging.info("Total guesses made by this configuration: {}\n".format(np.sum(counts)))

    print("Finished Inverting Rules, Total Time: {}".format(time.perf_counter()-i_time))

def main():

    args = setup_args() # set up args

    try:
        parse_args(args) # parse args

    except:
        raise

    print("Your Running Configuration: {}\n".format(RUNTIME_CONFIG.short_config_string()))

    start_processing()


if __name__ == "__main__":
    main()
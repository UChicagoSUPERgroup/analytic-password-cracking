import sys
from sys import path as sys_path
from os import path as os_path
import unittest
from time import time
import logging
import shutil

sys_path.append(os_path.abspath('../src'))

from config import RUNTIME_CONFIG
from guess_count import JTRGuessCount
from parse import RulelistReader
from invert_helper import Dicts
from feature_extraction import get_dependencies_for_rules
from utility import read_wordlist, forward_a_rule_and_get_count, forward_a_rule_to_an_address

class CountTest(unittest.TestCase):

    def setUp(self):
        """ set up logging info """
        logging.basicConfig(filename="../results/test_guess_count.log", level=logging.DEBUG)

    def switch_to_hc(self):
        """ switch context to HC """
        RUNTIME_CONFIG.reset_to_hc()
        Dicts.classes['z'] = set(chr(x) for x in range(256))

    def switch_to_jtr(self):
        """ switch context to JTR """
        RUNTIME_CONFIG.reset_to_jtr()
        Dicts.classes['z'] = set(chr(x) for x in range(32, 127))

    @unittest.skip
    def test_count_simple_rules_JTR(self):
        """ Guess count on each rule in HC """
        self.switch_to_jtr()

        if shutil.which(RUNTIME_CONFIG['executable_path']) == None:
            return

        ### Test Configuration ###
        wordlist_name = 'test_counting.lst'
        rulelist_name = 'test_counting_JtR_simple.rule'
        tmp_file_address = "tmp.txt"  # tmp output, will be removed after running
        ##########################

        # Simple Unittesting On Generate Dependencies and Get Count
        logging.info("Running {}\n".format(rulelist_name))
        test_successful = True

        logging.info("Reading Data\n")
        wordlist = read_wordlist(wordlist_name)
        rulelist = RulelistReader.read_and_parse_rule_list(rulelist_name, safe_mode = False)

        for r_idx, one_rule in enumerate(rulelist):
            
            one_rule = get_dependencies_for_rules([one_rule])[0]
            
            if one_rule.rule_dependency == None:
                logging.info("{} Not Countable".format(one_rule.raw))
                continue
            
            stime = time()
            # Program estimated answer
            program_count, _ = JTRGuessCount.count_rules(wordlist,[one_rule])
            program_count = program_count[0]

            # correct answer, ground truth
            true_count = forward_a_rule_and_get_count(wordlist_name,one_rule,tmp_file_address)
            
            if program_count != true_count:
                logging.info("Failed:{}\tprogram:{}\ttrue:{}\ttime:{}\n".format(one_rule.raw,program_count,true_count,time()-stime ))
                test_successful = False
            else:
                logging.info("Passed:{}\ttime:{}\n".format(one_rule.raw, time()-stime))

        if test_successful == True:
            logging.info("Successful Test: {} + {}".format(wordlist_name, rulelist_name))

        else:
            logging.info("Fail Test: {} + {}".format(wordlist_name, rulelist_name))

    @unittest.skip
    def test_count_random_rules_JTR(self):
        """ Guess count on each rule in HC """
        self.switch_to_jtr()

        if shutil.which(RUNTIME_CONFIG['executable_path']) == None:
            return

        ### Test Configuration ###
        wordlist_name = 'test_counting.lst'
        rulelist_name = 'test_counting_JtR.rule'
        tmp_file_address = "tmp.txt"  # tmp output, will be removed after running
        ##########################

        # Simple Unittesting On Generate Dependencies and Get Count
        logging.info("Running {}\n".format(rulelist_name))
        test_successful = True

        logging.info("Reading Data\n")
        wordlist = read_wordlist(wordlist_name)
        rulelist = RulelistReader.read_and_parse_rule_list(rulelist_name, safe_mode = False)

        for r_idx, one_rule in enumerate(rulelist):
            
            one_rule = get_dependencies_for_rules([one_rule])[0]
            
            if one_rule.rule_dependency == None:
                logging.info("{} Not Countable".format(one_rule.raw))
                continue
            
            stime = time()
            # Program estimated answer
            program_count, _ = JTRGuessCount.count_rules(wordlist,[one_rule])
            program_count = program_count[0]

            # correct answer, ground truth
            true_count = forward_a_rule_and_get_count(wordlist_name,one_rule,tmp_file_address)
            
            if program_count != true_count:
                logging.info("Failed:{}\tprogram:{}\ttrue:{}\ttime:{}\n".format(one_rule.raw,program_count,true_count,time()-stime ))
                test_successful = False
            else:
                logging.info("Passed:{}\ttime:{}\n".format(one_rule.raw, time()-stime))

        if test_successful == True:
            logging.info("Successful Test: {} + {}".format(wordlist_name, rulelist_name))

        else:
            logging.info("Fail Test: {} + {}".format(wordlist_name, rulelist_name))

    @unittest.skip
    def test_count_simple_rules_HC(self):
        """ Guess count on each rule in HC """
        self.switch_to_hc()

        if shutil.which(RUNTIME_CONFIG['executable_path']) == None:
            return

        ### Test Configuration ###
        wordlist_name = 'test_counting.lst'
        rulelist_name = 'test_counting_HC_simple.rule'
        tmp_file_address = "tmp.txt"  # tmp output, will be removed after running
        ##########################

        # Simple Unittesting On Generate Dependencies and Get Count
        logging.info("Running {}\n".format(rulelist_name))
        test_successful = True

        logging.info("Reading Data\n")
        wordlist = read_wordlist(wordlist_name)
        rulelist = RulelistReader.read_and_parse_rule_list(rulelist_name, safe_mode = False)

        for r_idx, one_rule in enumerate(rulelist):

            one_rule = get_dependencies_for_rules([one_rule])[0]
            if one_rule.rule_dependency == None:
                logging.info("{} Not Countable".format(one_rule.raw))
                continue
            
            stime = time()
            # Program estimated answer
            program_count, _ = JTRGuessCount.count_rules(wordlist,[one_rule])
            program_count = program_count[0]

            # correct answer, ground truth
            true_count = forward_a_rule_and_get_count(wordlist_name,one_rule,tmp_file_address)
            
            if program_count != true_count:
                logging.info("Failed:{}\tprogram:{}\ttrue:{}\ttime:{}\n".format(one_rule.raw,program_count,true_count,time()-stime ))
                test_successful = False
            else:
                logging.info("Passed:{}\ttime:{}\n".format(one_rule.raw, time()-stime))

        if test_successful == True:
            logging.info("Successful Test: {} + {}".format(wordlist_name, rulelist_name))

        else:
            logging.info("Fail Test: {} + {}".format(wordlist_name, rulelist_name))

    @unittest.skip
    def test_count_random_rules_HC(self):
        """ Guess count on each rule in HC """
        self.switch_to_hc()

        if shutil.which(RUNTIME_CONFIG['executable_path']) == None:
            return

        ### Test Configuration ###
        wordlist_name = 'test_counting.lst'
        rulelist_name = 'test_counting_HC.rule'
        tmp_file_address = "tmp.txt"  # tmp output, will be removed after running
        ##########################

        # Simple Unittesting On Generate Dependencies and Get Count
        logging.info("Running {}\n".format(rulelist_name))
        test_successful = True

        logging.info("Reading Data\n")
        wordlist = read_wordlist(wordlist_name)
        rulelist = RulelistReader.read_and_parse_rule_list(rulelist_name, safe_mode = False)

        for r_idx, one_rule in enumerate(rulelist):

            one_rule = get_dependencies_for_rules([one_rule])[0]
            if one_rule.rule_dependency == None:
                logging.info("{} Not Countable".format(one_rule.raw))
                continue
            
            stime = time()
            # Program estimated answer
            program_count, _ = JTRGuessCount.count_rules(wordlist,[one_rule])
            program_count = program_count[0]

            # correct answer, ground truth
            true_count = forward_a_rule_and_get_count(wordlist_name,one_rule,tmp_file_address)
            
            if program_count != true_count:
                logging.info("Failed:{}\tprogram:{}\ttrue:{}\ttime:{}\n".format(one_rule.raw,program_count,true_count,time()-stime ))
                test_successful = False
            else:
                logging.info("Passed:{}\ttime:{}\n".format(one_rule.raw, time()-stime))

        if test_successful == True:
            logging.info("Successful Test: {} + {}".format(wordlist_name, rulelist_name))

        else:
            logging.info("Fail Test: {} + {}".format(wordlist_name, rulelist_name))

if __name__ == "__main__":

    #Run Unit Test
    rule_suite = unittest.TestLoader().loadTestsFromTestCase(CountTest)
    rule_runner = unittest.TextTestRunner()
    rule_runner.run(rule_suite)


""" arg parsing for main function """

import argparse
from config import john_nick_names, hc_nick_names, RUNTIME_CONFIG
from common import PasswordPolicyConf, FilePath


def setup_args():
    """ set up valid args and parse them. """
    parser = argparse.ArgumentParser()
    # Parse Command Line Flags
    # pointing to the wordlist
    parser.add_argument(
        '-w',
        '--word',
        action='store',
        dest='wordlist_addr',
        help='Pointing To wordlist',
        required=True)
    # pointing to the rule list
    parser.add_argument(
        '-r',
        '--rule',
        action='store',
        dest='rulelist_addr',
        help='Pointing To rule list',
        required=True)
    # pointing to the test set
    parser.add_argument(
        '-p',
        '--pw',
        action='store',
        dest='pwlist_addr',
        help='Pointing to test/victim set',
        required=True)
    # debug lvl
    parser.add_argument(
        "-d",
        "--debug",
        help="more debug information",
        action="store_true",
        default=False)
    # running style lvl
    parser.add_argument(
        "-s",
        "--style",
        help="Run the program in JtR/HC style",
        choices=john_nick_names + hc_nick_names,
        required=True)
    # whether to enable regex
    # parser.add_argument('--enable_regex', action='store_true', help='Whether to enable regex', default=False)

    # Password Policy Specified
    # require at least (>=) length N
    parser.add_argument(
        '--length',
        action="store",
        help='Require at least (>=) length N to make the guess',
        type=int,
        choices=range(1, 35))
    # require a digit to make the guess
    parser.add_argument(
        '--digit',
        action="store_true",
        help='Require a digit to make the guess',
        default=False)
    # require a letter to make the guess
    parser.add_argument(
        '--letter',
        action="store_true",
        help='Require a letter to make the guess',
        default=False)
    # require an lower letter to make the guess
    parser.add_argument(
        '--lower',
        action="store_true",
        help='Require an lower letter to make the guess',
        default=False)
    # require an upper letter to make the guess
    parser.add_argument(
        '--upper',
        action="store_true",
        help='Require an upper letter to make the guess',
        default=False)

    args = parser.parse_args()
    return args


def parse_args(args):
    """ parse cmd line args """
    # set running style
    if args.style in john_nick_names:
        RUNTIME_CONFIG.reset_to_jtr()
    else:
        RUNTIME_CONFIG.reset_to_hc()

    # set password_policy
    password_policy = PasswordPolicyConf(args.length, args.digit, args.letter,
                                         args.lower, args.upper)
    RUNTIME_CONFIG['password_policy'] = password_policy

    # parse pathes
    RUNTIME_CONFIG['wordlist_path'] = FilePath(args.wordlist_addr)
    RUNTIME_CONFIG['rulelist_path'] = FilePath(args.rulelist_addr)
    RUNTIME_CONFIG['pwlist_path'] = FilePath(args.pwlist_addr)

    # parse other flags
    # if args.enable_regex:
    #RUNTIME_CONFIG['enable_regex'] = True
    #print("Warning: Regex Is Slow and Only For Demo Purpose, Should Be Disabled in Real Running\n")

    if args.debug == True:
        RUNTIME_CONFIG['debug'] = True
        print("Enabling Extra Debug Information\n")

    if RUNTIME_CONFIG.is_hc() and password_policy.to_compact_string() != "":
        print(
            "Warning: Enabling Password Policy Is Slow in HC Mode and Only For Demo Purpose, Should Be Disabled in Real Running\n"
        )

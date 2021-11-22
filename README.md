<div align='center'>
  <a href='https://super.cs.uchicago.edu' target='_blank'>
    <img src='docs/screenshots/supergroup.jpg' alt='SUPERgroup Logo' />
  </a>
</div>

# Reasoning Analytically About Password-Cracking Software

**In this repository we provide software to reason analytically and efficiently about transformation-based password cracking in software tools like John the Ripper (JtR) and Hashcat (HC).**

 - Our implementation is able to reduce the time it takes to estimate password strength via JtR / HC by orders of magnitude.
 - Our software can leverage revealed password data to improve orderings of transformation rules and to identify rules and words potentially missing from an attack configuration.

## Table of Contents
- [Reasoning Analytically About Password-Cracking Software](#reasoning-analytically-about-password-cracking-software)

  * [Installation](#installation)
    + [Quick Installation](#quick-installation)
    + [Manual Installation](#manual-installation)
  * [Getting Started](#getting-started)
  * [More Running Examples](#more-running-examples)
    + [Guess Number Estimation of a Password File](#guess-number-estimation-of-a-password-file)
    + [Guess Number Estimation of a Password File with Policy](#guess-number-estimation-of-a-password-file-with-policy)
  * [Running Configurations](#running-configurations)
    + [Command line options](#command-line-options)
    + [Runtime Options](#runtime-options)
  * [High-Level Workflow](#high-level-workflow)
  * [Project Structure](#project-structure)
    + [Top-level Directory Layout](#top-level-directory-layout)
    + [Source files](#source-files)
    + [Test files](#test-files)
    + [Data](#data)
    + [Demo files](#demo-files)
  * [FAQ](#faq)
    + [Installation](#installation-1)
    + [Running](#running)
  * [Bugs](#bugs)
  * [Cite the Paper](#cite-the-paper)
  * [Acknowledgment](#acknowledgment)
  * [License](#license)
  * [Contact](#contact)

## Installation
Our software uses:

* [John the Ripper](https://github.com/magnumripper/JohnTheRipper)
* [HashcatRulesEngine](https://github.com/llamasoft/HashcatRulesEngine)

Thus, your system must be capable of compiling both. While we take care of this crucial step, you likely will need to install:

```bash
# To compile JtR we need
sudo apt-get install build-essential
sudo apt-get install libssl-dev
sudo apt-get install ocl-icd-opencl-dev opencl-headers pocl-opencl-icd
```

If you encounter any issues, please refer to JtR's [installation guide](https://github.com/magnumripper/JohnTheRipper/blob/bleeding-jumbo/doc/INSTALL-UBUNTU).

### Dependencies: OS and Python Versions
Our tools are tested on **Ubuntu 18.04** but might work on macOS, too.
Our tools should support Python 3.5+, but are only tested on **Python 3.6**.

### Quick Installation

Generally you need to do:
```bash
# Our tool needs
sudo apt-get install build-essential python3-pip git

```
After this, we've built a script for you to one-click install our tool. Simple download the [setup.sh](setup.sh) file and run.
```bash
# Do not clone this repository yourself, setup.sh will do this for you!
wget https://raw.githubusercontent.com/UChicagoSUPERgroup/analytic-password-cracking/master/setup.sh
chmod +x setup.sh
# Super user permissions not required
./setup.sh
```
### Manual Installation
Please follow the steps in `setup.sh`. If you have problem building JtR's source code, please refer to their repository for [building help](https://github.com/magnumripper/JohnTheRipper/blob/bleeding-jumbo/doc/INSTALL-UBUNTU).

## Getting Started

First enter the demo directory
```bash
cd analytic-password-cracking/demo
```
We've put some demo wordlists, rulelists and testsets there for you to play with. For example, you can run the following cmds to output an estimated guess number for each password in `demo.txt`, assuming the wordlist is `demo.lst` and the rulelist is `demo_HC.rule` / `demo_JtR.rule`.
```bash
# For a Hashcat Rulelist
python3 demo_guess_count_file.py --word ../data/wordlists/demo.lst --rule ../data/rulelists/demo_HC.rule --pw ../data/testsets/demo.txt -s h
```

```bash
# For a John the Ripper Rulelist
python3 demo_guess_count_file.py --word ../data/wordlists/demo.lst --rule ../data/rulelists/demo_JtR.rule --pw ../data/testsets/demo.txt -s j
```
The result is saved in the ``results`` directory with filename starting with `demo_file-<wordlist>-<rulefile>-<passwordfile>.log`.

Example result:
```
INFO:root:                # Debug Info
PasswordIdx:17            # Password ID
Password:panther1         # The correctly guessed password (from password file)
Rule:$1                   # The successful rule used to produce the guess (from rule file)
Word:panther              # The successful base word that was mangled (from wordlist)
Guess:19926 ( 0 - 70920 ) # Estimated guess number (lower - upper bounds)
```

## More Running Examples
### Guess Number Estimation of a Password File
Suppose you have a wordlist, rulelist and a file of passwords, you want to know the guess number, you could run the following commands. **Note that many time for large wordlists it would take hours to preprocess.**
```bash
# For a Hashcat Style
python3 demo_guess_count_file.py --word /path/to/wordlist --rule /path/to/rulelist --pw /path/to/passwordfile -s h

# For a John the Ripper Style
python3 demo_guess_count_file.py --word /path/to/wordlist --rule /path/to/rulelist --pw /path/to/passwordfile -s j
```
### Guess Number Estimation of a Password File with Policy
Suppose you have a wordlist, rulelist and a file of passwords. You you want to know the guess number, and you also want to filter out passwords that don't meet with the password policy. Suppose the password policy is `length >= 6`, has a `digit`, and has a `letter`.
```bash
# For a Hashcat Style
python3 demo_guess_count_file.py --word /path/to/wordlist --rule /path/to/rulelist --pw /path/to/passwordfile -s h --length=6 --digit --letter

# For a John the Ripper Style
python3 demo_guess_count_file.py --word /path/to/wordlist --rule /path/to/rulelist --pw /path/to/passwordfile -s j --length=6 --digit --letter
```

#### Specifying Password Policy
There are 5 types of password policies we support: length, digits, letters, uppercase letters, lowercase letters. You can use command line flags to set each type to true. For example:
```
A policy that requires passwords to have a uppercase letter:
--upper
A policy that requires passwords to have length >= 8:
--length=8
A policy that requires passwords to have length >= 6, have a digit, and have a letter:
--length=6 --digit --letter
```

## Running Configurations
### Command line options
```
demo_guess_count_file.py [-h] -w WORDLIST_ADDR -r RULELIST_ADDR -p
                                PWLIST_ADDR [-d] -s
                                {j,jtr,JTR,JtR,John,john,J,John The
                                Ripper,Jtr,h,hc,HC,hashcat,H,Hashcat,Hc}
                                [--length {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34}]
                                [--digit] [--letter] [--lower] [--upper]

optional arguments:
  -h, --help            Show this help message and exit
  -w WORDLIST_ADDR, --word WORDLIST_ADDR
                        Pointing to wordlist (Required)
  -r RULELIST_ADDR, --rule RULELIST_ADDR
                        Pointing to rule list (Required)
  -p PWLIST_ADDR, --pw PWLIST_ADDR
                        Pointing to test/victim set (Required)
  -d, --debug           More debug information
  -s  --style           Can use: j/jtr for John the Ripper and h/hc for Hashcat
                        Run the program in JtR/HC style (Required)
  --length              Adding a password policy that require at least (>=) length N to make the guess
                        (Must be an integer from [1-34])
  --digit               Adding a password policy that require a digit to make the guess
  --letter              Adding a password policy that require a letter to make the guess
  --lower               Adding a password policy that require an lowercase letter to make the guess
  --upper               Adding a password policy that require an uppercase letter to make the guess
```

### Runtime Options
To specify runtime configurations, edit [config.py](./src/config.py).

**Caution: By default we use ``look`` command for binary search files, which is built-in for macOS and Ubuntu. However, the ``look`` command in Linux only supports files < 2GB, so you should patch it for large datasets.**

### John the Ripper: Configuration Options
```
'running_style': Running style. Don't use this for now.
'max_password_length': An integer. Inputs/outputs greater than this are ignored
'min_cut_length': max_password_length + 1
'm_threshold': Threshold for inverting `ONM  | Omit range` command
'executable_path': External JtR executable
'password_policy': The password policy specified. Use cmd line options, don't configure it here, use args instead.
'preprocess_path': Linked to preprocess root directory
'enable_regex': Whether to enable_regex or not. Only for internal testing
'debug': If in debug mode or not.
'binary_search_file_executable': The program to perform binary search. Use `look` by default (built-in on Ubuntu and macOS).
'lookup_threshold': If the number of preimages are more than this, use trie search.
```

### Hashcat: Configuration Options
```
'running_style': Running style. Don't use this for now.
'max_password_length': An integer. Inputs/outputs greater than this are ignored
'min_cut_length': max_password_length + 1
'm_threshold': Threshold for inverting `ONM  | Omit range` command
'executable_path': External HC executable
'password_policy': The password policy specified. Use cmd line options, don't configure it here, use args instead.
'preprocess_path': Linked to preprocess root directory
'enable_regex': Whether to enable_regex or not. Only for internal testing
'debug': If in debug mode or not.
'binary_search_file_executable': The program to perform binary search. Use `look` by default (built-in on Ubuntu and macOS).
'lookup_threshold': If the number of preimages are more than this, use trie search.
'batch_size_of_words': An integer, how many words in a batch
'batch_size_of_rules': An integer or "auto", how many rules in a batch
```

## High-Level Workflow
The high-level workflow of [demo_guess_count_file.py](./demo/demo_guess_count_file.py) is like this:
1. Read wordlist/rulelist/testset
2. Do preprocessing on the rulelist.
    1. Identify special rules. Determine whether each rule is invertible/countable.
    2. If the rule is uninvertible, pipe data to disk (enumeration).
    3. If the rule is uncountable, pipe just a number to disk (just a number).
    4. If the rule is countable, figure out all the dependencies, build the tensor, make a pass on the wordlist, fill the tensor.
    5. Get count for countable rules.
    6. Other running-specific preparations.
3. Inversion
    1. If invertible, invert the password through the rule, get the preimages, do constant time lookups on the wordlist or trie search (if too many preimages)
    2. If uninvertible, generally do binary search on the piped file.
4. Output results (stored in ``results`` directory).

## Project Structure
### Top-level Directory Layout
    Reasoning Analytically About Password-Cracking Software
    ├── data                           # Input/Intermediate data
    ├── demo                           # Built-in demos
    ├── src                            # Source files
    ├── tests                          # Automated tests
    ├── results                        # Results
    ├── trie                           # External library
    ├── HashcatRulesEngine             # External library
    ├── JohnTheRipper                  # External library
    └── README.md

### Source files
    .
    ├── ...
    ├── src
    │   ├── argparsing.py              # Parse args for demo/
    │   ├── clean_hashes.py            # Clean fingerprint of last run
    │   ├── common.py                  # Common classes used across different modules
    │   ├── config.py                  # Runtime configurations
    │   ├── demo_common.py             # Common functions for demo/
    │   ├── feature.py                 # Definition of different features
    │   ├── feature_extraction.py      # Feature extraction
    │   ├── guess_count.py             # Guess_count and related functions
    │   ├── invert_helper.py           # Utility functions and definitions for invert_rule
    │   ├── invert_rule.py             # Invert transformation rules
    │   ├── parse.py                   # Rule parser
    │   ├── preprocess.py              # Preprocess
    │   ├── tokenstr.py                # Additional data structure used in invert_rule
    │   └── utility.py                 # Utility functions used across different modules
    └── ...

### Test files
    .
    ├── ...
    ├── tests
    │   ├── test_guess_count.py        # Test guess_count module in src directory
    │   ├── test_guess_count_file      # Test guess_count_file module in demo directory
    │   ├── test_invert_rule.py        # Test invert_rule module in src directory
    │   └── test_parse.py              # Test parse module in src directory
    └── ...

### Data
    .
    ├── ...
    ├── preprocess                     # Save preprocess data, mostly enumerated data and count
    │   ├── count                      # Counts for uncountable rules
    │   └── enumerated                 # Enumerated data of uninvertible rules
    ├── rulelists                      # Built-in rulelists
    ├── testsets                       # Built-in testsets
    ├── wordlists                      # Built-in wordlists
    └── ...

### Demo files
    .
    ├── ...
    ├── demo
    │   └── demo_guess_count_file.py   # Guess number estimation given a file of passwords
    └── ...

## FAQ
### Installation
#### What if I fail to install your code?
We recommend that you look at the `setup.sh` script and execute the commands there one by one and see where you fail. Our code is mostly written in Python 3 and should be compatible with Python 3.5 and Python 3.6. However, we do run external programs by building them from source. Namely *John the Ripper (JtR)* and *HashcatRulesEngine*. **HashcatRulesEngine** is written in C and should be compiled easily. **JtR** has more complex dependencies. If you fail to build JtR, please refer to [JtR's repository](https://github.com/magnumripper/JohnTheRipper). For all the libraries and dependencies we use, please look at the dependencies section below.

#### What dependencies do you reply on?
Python libraries:
* `numpy ('1.13.1')`
* `pyparsing ('2.2.0')`
* `cython ('0.26.1')`
* [chartrie](https://github.com/buriy/python-chartrie)

External libraries:
* [John the Ripper](https://github.com/magnumripper/JohnTheRipper)
* [HashcatRulesEngine](https://github.com/llamasoft/HashcatRulesEngine)

### Running
#### Why don't you support other password policy types (like symbols)?
We express password policies using rejection rules (in JtR's character class style), currently there's no character class that captures all the symbols. Also, the definition of symbols varies. So we decide not to support symbols.

#### Why don't you support complex password policies (like 2 of the 4 character classes)?
It's impossible to represent complex password policies in rejection rules, so we don't support them.

#### Where is the output file?
The results are stored in ``result`` directory.

#### Where can I find guesses made by each rule (including uncountable rules)?
The guesses made by each rule is saved at ``preprocess_path/saved_counts.py``

#### Where can I find enumerated results for uninvertible rules?
The piped results for uninvertible rules are saved at ``preprocess_path/enumerated/*.txt``

#### Do you have to preprocess every time you start?
This depends. If you change the wordlist, rulelist, or password policy, then yes, you have to preprocess again. However, we realize that you might want to run one configuration with multiple test sets. So if the wordlist, rulelist, password policy and running style are exactly the same as last run, we don't preprocess again. That is, if you only change test set every time you run it, it doesn't preprocess every time. And for where to find the preprocess data, please look at the sections above.

#### What are these ``hashes.txt`` and ``count_hashes.txt`` files used for in ``preprocess/`` directory?
This saves the fingerprint of your last runtime configuration (aka wordlist, rulelist, password policy and running style), so that if you specify the same runtime configuration, we don't preprocess again.

#### How do I get ride of ``hashes.txt`` and ``count_hashes.txt`` to force preprocessing every time?
Two options.
1. Delete them by manually
2. ``cd src; python3 clean_hashes.py``

#### How do I speed up the program?
I want it to be FASTER! Well, reasonable request. Using [PyPy3.6](https://pypy.org/download.html) will give quite a lot speedup. You can also potentially parallelize the process for better performance.

## Bugs
This is software used and maintained for a research project and likely will have many bugs and issues.

## Cite the Paper
[Reasoning Analytically About Password-Cracking Software](https://www.blaseur.com/papers/sp19-pwcracking.pdf)
```
@inproceedings{liu-19-mangling-rules,
    author = {Liu, Enze and Nakanishi, Amanda and Golla, Maximilian and Cash, David and Ur, Blase},
    title = {{Reasoning Analytically About Password-Cracking Software}},
    booktitle = {IEEE Symposium on Security and Privacy},
    year = {2019},
    series = {SP~'19},
    pages = {1272--1289},
    address = {San Francisco, California, USA},
    month = may,
    publisher = {IEEE}
}
```

## Acknowledgment
We'd like to express our gratefulness to whoever has the many people who helped our project, including but not limited to: Nasr Maswood; the authors of `JtR` and `HC`; other members of the `JtR` and `HC` communities who provided valuable feedback; the authors of `chartrie`; the tech staff at UChicago; and Chameleon Cloud.

## License
This software is licensed under the MIT license.
Refer to [docs/LICENSE](docs/LICENSE) for more information.

## Contact
Technical questions? Contact [Enze (Alex) Liu](mailto:alexliu0809@uchicago.edu).
You can also visit our [website](https://super.cs.uchicago.edu).
If you are interested in passwords, consider contributing.

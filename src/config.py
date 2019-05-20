"""This file contains runtime configurations"""

from common import RunningStyle, PasswordPolicyConf
from copy import deepcopy
from sys import platform

# possible jtr names
john_nick_names = [
    'j', 'jtr', 'JTR', 'JtR', 'John', 'john', 'J', 'John The Ripper', 'Jtr'
]
# possible hc names
hc_nick_names = ['h', 'hc', 'HC', 'hashcat', 'H', 'Hashcat', 'Hc']

# For detailed information about what each field means, please refer to readme.md

# jtr's default configuration
jtr_default_config = {
    'running_style':
    RunningStyle.JTR,
    'max_password_length':
    127,  # input/output greater than this are ignored
    'min_cut_length':
    128,  # max_password_length + 1
    'm_threshold':
    2,
    'executable_path':
    "../JohnTheRipper/run/john"
    if platform != "win32" else "../JohnTheRipper/run/john.exe",
    'password_policy':
    PasswordPolicyConf(),
    'preprocess_path':
    '../data/preprocess/',
    'enable_regex':
    False,
    'debug':
    False,
    'binary_search_file_executable': # pointing to the executable for binary searching a sorted file
    'look',
    'lookup_threshold':
    131073, #2^17 + 1

}

# hc's default configuration
hc_default_config = {
    'running_style':
    RunningStyle.HC,
    'max_password_length':
    255,  # input/output greater than this are ignored
    'min_cut_length':
    256,  # max_password_length + 1
    'm_threshold':
    2,
    'executable_path':
    "../HashcatRulesEngine/hcre"
    if platform != "win32" else "../HashcatRulesEngine/hcre.exe",
    'password_policy':
    PasswordPolicyConf(),
    'preprocess_path':
    '../data/preprocess/',
    'enable_regex':
    False,
    'debug':
    False,
    'binary_search_file_executable': # pointing to the executable for binary searching a sorted file
    'look',
    'lookup_threshold':
    131073, #2^17 + 1
    'batch_size_of_words':
    1024 * 1024,
    'batch_size_of_rules':
    'auto', # either an int or auto
}

# caution, unix default look only supports look up on file < 2GB


class Configuration():
    """ Contains the running config, it constructs a dictioanry """

    def __init__(self, running_style=RunningStyle.JTR, **kwargs):
        """ Initialize a configuration dict.

        Args:
            running_style: either JTR/HC
            kwargs: optional args, set specific field in the dictionary.
        """
        self.config = deepcopy(
            hc_default_config
        ) if running_style == RunningStyle.HC else deepcopy(jtr_default_config)
        for k, v in kwargs.items():
            self.config[k] = v

    def __setitem__(self, key, item):
        self.config[key] = item

    def __getitem__(self, key):
        return self.config[key]

    def reset_to_hc(self, **kwargs):
        """ reset configuration to HC default, also support setting specific field """
        self.config = deepcopy(hc_default_config)
        for k, v in kwargs.items():
            self.config[k] = v

    def reset_to_jtr(self, **kwargs):
        """ reset configuration to JTR default, also support setting specific field """
        self.config = deepcopy(jtr_default_config)
        for k, v in kwargs.items():
            self.config[k] = v

    def is_jtr(self):
        """ return True if running on JTR mode """
        return self.config['running_style'] == RunningStyle.JTR

    def is_hc(self):
        """ return True if running on HC mode """
        return self.config['running_style'] == RunningStyle.HC

    def short_config_string(self):
        """ get quick info of configuration """
        return "{}(WL) {}(RL) {}(Testset) {}".format(
            self['wordlist_path']['name'], self['rulelist_path']['name'],
            self['pwlist_path']['name'], self['running_style'])

    def get_log_addr(self):
        """ get log file addr"""
        return "../results/demo_file-{}-{}-{}.log".format(
            self['wordlist_path']['name'], self['rulelist_path']['name'],
            self['pwlist_path']['name'])


RUNTIME_CONFIG = Configuration()

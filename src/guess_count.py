"""This file contains functions to do guess_count given a rulelist and a wordlist."""
from common import FatalRuntimeError
from warnings import warn
from config import RUNTIME_CONFIG
from enum import Enum
from subprocess import Popen, PIPE
from time import perf_counter
from collections import OrderedDict, Counter
from utility import sizeof_fmt, write_rules_to_file, forward_batched_words_and_batched_rules
from utility import has_count_data, store_count_data_hash, restore_counts_from_file, store_counts_to_file
from invert_helper import CHARS_LETTERS, CHARS_DIGITS
import numpy as np
import os


class MatrixList():
    """ A list of matrix """

    def __init__(self):
        self.mat_list = []

    def add(self, mat):
        """ add a matrix to the list """
        self.mat_list.append(mat)
        return len(self.mat_list) - 1

    def __iter__(self):
        yield from self.mat_list

    def __getitem__(self, key):
        return self.mat_list[key]


class Matrix():
    """ A class that holds all auxiliary information

    its internal data structure is a multi dimensional array

    each multi dimensional array has all the information required to count at least one dep_list
    many times it has enough info to count multiple dep_lists.

    Attr:
        dim_attributes: an OrderDict(<attribute tup, max_number_supported>)
        
        dim_size: size of each dimension
        
        dim_len: total number of dimensions

        mat: actual multi dimensional array
    """

    def __init__(self, dim_attributes):
        """ initialize an instance of Matrix
        
        create corresponding matrix given a list of features

        Attr:
            dim_attributes: a list of features, 
        """
        self.dim_attributes = dim_attributes  #A Dict
        self.dim_size = []
        self.saved_slice_result = (None, None)

        mat_size = 1
        for val in dim_attributes.values():
            self.dim_size.append(val)
            mat_size *= val

        self.dim_len = len(dim_attributes)

        #You can use dtype = u64. As total size <= Wordlist size
        #We Assume That A SubRule Doesn't Make Guesses More Than 18446744073709551615
        #Another General Solution is to set it to "object"
        self.mat = np.zeros(mat_size, dtype="uint64").reshape(self.dim_size)

    def __repr__(self):
        string = ""
        string += "Attributes:\n{}\n".format(self.attributes_to_str())
        string += "Dim_size:\n{}\n".format(self.dim_size)
        return string

    def attributes_to_str(self):
        """ convert list of features to string """
        string = ""
        for k, v in self.dim_attributes.items():
            if k[0] == 6 or k[0] == 7:
                string += "Length\n"
            elif k[0] == 3:
                string += "Char At {} Equals {}\n".format(k[2], k[1])
            elif k[0] == 2:
                string += "Contains Instances of {}, Max Value {}\n".format(
                    k[1], v)
            elif k[0] == 1:
                string += "Contains Instances of {}, Max Value {}\n".format(
                    k[1], v)
            elif k[0] == 4:
                string += "[ - ) Contains Instances of {}, Max Value {}\n".format(
                    k[1], v)
            elif k[0] == 5:
                string += "[ - ) Contains Instances of {}, Max Value {}\n".format(
                    k[1], v)
            else:
                raise FatalRuntimeError("Unknown Type")

        return string

    def get_sum_for_a_slice(self, a_slice):
        """ for a slice that slices the matrix, get the sum. 

        Bsically: sum(matrix[slice])
        """
        if a_slice != self.saved_slice_result[0]:
            val = int(np.sum(self.mat[tuple(a_slice)]).item())
            self.saved_slice_result = (a_slice, val)
            return val
        else:
            return self.saved_slice_result[1]


class AttributeType(Enum):
    """ Denote the attribute of the word tracked """
    LENGTH = 100,  # length
    CHARS = 200,  # contains number of chars
    CHARS_AT_POS = 300,  # chars at position
    CHARS_RANGE = 400,  # chars in a range


class JTRGuessCount():

    def dep_to_tuple(dep):
        """ Convery a dependency to hashable tuple 
        
        Each tuple denotes an unique attribute (e.g. length, number of 'a's, etc.) of the input word.
        
        Use this tup for grouping attributes.
        """
        if 4 <= dep.get_type(
        ) <= 5:  # 4,5 capture the same info, [from, to) has N.
            tup = (AttributeType.CHARS_RANGE, frozenset(dep.get_chars()),
                   dep.get_from(), dep.get_to())

        elif dep.get_type() == 6 or dep.get_type(
        ) == 7:  # 6,7 capture the same info, length
            tup = (AttributeType.LENGTH, None)

        elif dep.get_type() == 3:
            tup = (AttributeType.CHARS_AT_POS, frozenset(dep.get_chars()),
                   dep.get_position())

        elif 1 <= dep.get_type(
        ) <= 2:  # 1,2 capture the same info, number of chars.
            tup = (AttributeType.CHARS, frozenset(dep.get_chars()))

        else:
            raise FatalRuntimeError("Unknown Dep Type : {}".format(
                dep.get_type()))

        return tup

    def get_slice_for_dep_list_in_matrix_attr(matrix, dep_list):
        """ Build slice for dep_list to slice a matrix knowing which matrix it is"""

        matrix_attr = matrix.dim_attributes

        matrix_attr_keys = list(matrix_attr.keys())

        dep_list_index_in_matrix = [slice(None, None, 1)] * len(matrix_attr)

        for dep in dep_list.get_active():
            tup = JTRGuessCount.dep_to_tuple(dep)

            dep_index = matrix_attr_keys.index(tup)

            old_slice = dep_list_index_in_matrix[dep_index]

            if dep.get_type() == 7:  # Greater Than
                dep_list_index_in_matrix[dep_index] = slice(
                    dep.get_len() + 1, old_slice.stop, old_slice.step)
            elif dep.get_type() == 6:  #Less than
                dep_list_index_in_matrix[dep_index] = slice(
                    old_slice.start, dep.get_len(), old_slice.step)
            elif dep.get_type() == 5:  #from to at least N
                if old_slice.start != None:
                    dep_list_index_in_matrix[dep_index] = slice(
                        max(old_slice.start, dep.get_number()), old_slice.stop,
                        old_slice.step)
                else:
                    dep_list_index_in_matrix[dep_index] = slice(
                        dep.get_number(), old_slice.stop, old_slice.step)
            elif dep.get_type() == 4:  #from to exactly N
                if old_slice.start != None:
                    dep_list_index_in_matrix[dep_index] = slice(
                        max(old_slice.start, dep.get_number()),
                        dep.get_number() + 1, old_slice.step)
                else:
                    dep_list_index_in_matrix[dep_index] = slice(
                        dep.get_number(),
                        dep.get_number() + 1, old_slice.step)
            elif dep.get_type() == 3:  #Char at pos
                dep_list_index_in_matrix[dep_index] = slice(
                    1, old_slice.stop, old_slice.step)
            elif dep.get_type() == 2:  #Number of chars
                if old_slice.start != None:
                    dep_list_index_in_matrix[dep_index] = slice(
                        max(old_slice.start, dep.get_number()), old_slice.stop,
                        old_slice.step)
                else:
                    dep_list_index_in_matrix[dep_index] = slice(
                        dep.get_number(), old_slice.stop, old_slice.step)
            elif dep.get_type() == 1:
                if old_slice.stop != None:
                    dep_list_index_in_matrix[dep_index] = slice(
                        old_slice.start, min(old_slice.stop, dep.get_number()),
                        old_slice.step)
                else:
                    dep_list_index_in_matrix[dep_index] = slice(
                        old_slice.start, dep.get_number(), old_slice.step)
            else:
                raise FatalRuntimeError("Unknown Dep List Index")

        return dep_list_index_in_matrix

    def check_in_prev_matrix(matrix_list, dep_list):
        """ Check if a dep_list is covered by previous matrices. 

        Dont need to add to new matrix
        """
        for idx, matrix in enumerate(matrix_list.mat_list):

            matrix_attr = matrix.dim_attributes

            is_contained = True

            matrix_attr_keys = matrix_attr.keys()

            for dep in dep_list.get_active():

                tup = JTRGuessCount.dep_to_tuple(dep)

                if tup not in matrix_attr_keys:
                    is_contained = False
                    break

                #Additional Check
                # If num of chars/ [from, to) num of chars
                if tup[0] in (AttributeType.CHARS, AttributeType.CHARS_RANGE):
                    if matrix_attr[tup] < dep.get_number(
                    ) + 1:  #If the matrix does not count that many.
                        is_contained = False
                        break

            if is_contained == True:
                return idx

        return -1

    def build_matrix(rules, has_feasibility):
        """ Given a set of parsed rules, build corresponding multi-demensional arrays 
        
        Args:
            rules: a list of rules

            has_feasibility: Denoting the feasibility of each rule.
        """

        #Read all active dep_lists in rules
        dep_lists = []

        for i, rule in enumerate(rules):
            if has_feasibility == False:
                if rule.rule_dependency == None:  # no countable
                    continue

                sub_rules = rule.rule_dependency.get_sub_rules()
                for sub_rule in sub_rules:
                    list_of_dep_list = sub_rule.get_list_of_dep_list()
                    for dep_list in list_of_dep_list:
                        if dep_list.is_active():
                            dep_lists.append(dep_list)
            else:
                #If Rule is feasible
                if rule.feasibility.is_invertible(
                ) and rule.feasibility.is_countable():
                    sub_rules = rule.rule_dependency.get_sub_rules()
                    for sub_rule in sub_rules:
                        list_of_dep_list = sub_rule.get_list_of_dep_list()
                        for dep_list in list_of_dep_list:
                            if dep_list.is_active():
                                dep_lists.append(dep_list)
                else:
                    continue

        ######################## Grouping Algorithm Starts Here ########################
        #Start Grouping Algorithm To Build Large Matrix.

        #Initialize Matrix List
        matrix_list = MatrixList()

        #Initialize Some Vars
        memory_threshold = 16 * 1024 * 1024 * 1024  # 16GB of memory for counting
        memory_used = 0

        matrix_threshold = 64 * 1024 * 1024  # Any Matrix using more than 64MB of space shoud stop.

        #Grouping Strategy 1 -- Build Longest Dep_List First
        #dep_lists.sort(key=lambda x: x.get_active_number())

        #Grouping Strategy 2: -- Give Each Dep_List A Pri, Group High Pri First.
        #Either total / max
        #Looks like total is better
        occurence = {}
        for dep_list in dep_lists:
            for dep in dep_list.get_active():
                tup = JTRGuessCount.dep_to_tuple(dep)
                tup_count = occurence.get(tup, 0)
                occurence[tup] = tup_count + 1
        #print(occurence)
        for dep_list in dep_lists:
            for dep in dep_list.get_active():
                tup = JTRGuessCount.dep_to_tuple(dep)
                tup_count = occurence.get(tup)
                dep_list.priority = tup_count + dep_list.priority
                #dep_list.priority = max(tup_count,dep_list.priority)

        # sort dep_list by priority, build those with high priority first
        dep_lists.sort(key=lambda x: (x.priority, x.get_active_number()))

        #Debug
        #Initalize Vars
        matrix_attr = OrderedDict()
        matrix_id = 0
        matrix_memeory_usage = 1

        #While there's still dep_list in dep_lists
        while (len(dep_lists) > 0):

            #Get this value
            current_dep_list = dep_lists.pop()
            #print("Current Dep List:\n{}".format(current_dep_list))

            #Check if dep_list included in previous mat
            check_result = JTRGuessCount.check_in_prev_matrix(
                matrix_list, current_dep_list)
            #print("Check Result: {}".format(check_result))

            if check_result != -1:
                current_dep_list.mat_idx = check_result
                continue

            #print(current_dep_list)
            #Add New Dependecies To Current Matrix
            for dep in current_dep_list.get_active():
                if dep.get_type() == 6 or dep.get_type() == 7:  # length
                    tup = JTRGuessCount.dep_to_tuple(dep)

                    if tup not in matrix_attr:
                        matrix_attr[tup] = RUNTIME_CONFIG[
                            'max_password_length'] + 1  # max length + 1, because of 0

                elif dep.get_type() == 2 or dep.get_type(
                ) == 1:  # number of char
                    tup = JTRGuessCount.dep_to_tuple(dep)

                    current_val = matrix_attr.get(
                        tup, -1)  # check current value supported
                    if current_val < dep.get_number() + 1:
                        current_val = dep.get_number() + 1

                    matrix_attr[tup] = current_val

                elif dep.get_type() == 3:  # char at position
                    tup = JTRGuessCount.dep_to_tuple(dep)

                    if tup not in matrix_attr:
                        matrix_attr[tup] = 2

                elif 4 <= dep.get_type() <= 5:  # from to contains
                    tup = JTRGuessCount.dep_to_tuple(dep)

                    current_val = matrix_attr.get(tup, -1)
                    if current_val < dep.get_number() + 2:
                        current_val = dep.get_number(
                        ) + 2  # >2, because of reject_exactly.

                    matrix_attr[tup] = current_val

                else:
                    raise FatalRuntimeError("Unknown Type")

            #Give associated matrix_id and slice with current_dep_list
            current_dep_list.mat_idx = matrix_id

            #Finish Adding New Dependencies.
            #Repopulate Matrix Memory usage everytime
            matrix_memeory_usage = 1
            for val in matrix_attr.values():
                matrix_memeory_usage *= val
            matrix_memeory_usage *= 8  #Assume 64 bits

            #This is one matrix. Build A New one
            if matrix_memeory_usage >= matrix_threshold:
                #print("A New Matrix Is Generated")
                #Build A Matrix
                matrix_list.add(Matrix(matrix_attr))

                #Add Current Memory Usage
                memory_used += matrix_memeory_usage

                #Reset
                matrix_attr = OrderedDict()
                matrix_id += 1

                if memory_used > memory_threshold:
                    raise FatalRuntimeError(
                        "Memory Usage Exceeded Threshold 16GB: {}\n".format(
                            sizeof_fmt(memory_used)))

        #Clean the last one (Add the last matrix to matrix list)
        if len(matrix_attr) != 0:
            #Repopulate usage everytime
            matrix_memeory_usage = 1
            for val in matrix_attr.values():
                matrix_memeory_usage *= val
            matrix_memeory_usage *= 8  #Assume 64 bits

            matrix_list.add(Matrix(matrix_attr))

            #Add Current Memory Usage
            memory_used += matrix_memeory_usage

            #Reset
            matrix_attr = OrderedDict()
            matrix_id += 1

            if memory_used > memory_threshold:
                raise FatalRuntimeError(
                    "Memory Usage Exceeded Threshold 16GB: {}\n".format(
                        sizeof_fmt(memory_used)))

        #print("Generating Slices For Dep List To Index Matrices\n")
        for i, rule in enumerate(rules):
            if has_feasibility == False:
                if rule.rule_dependency == None:
                    continue

                sub_rules = rule.rule_dependency.get_sub_rules()
                for sub_rule in sub_rules:
                    list_of_dep_list = sub_rule.get_list_of_dep_list()
                    for dep_list in list_of_dep_list:
                        if dep_list.is_active():
                            dep_list.mat_slice = JTRGuessCount.get_slice_for_dep_list_in_matrix_attr(
                                matrix_list[dep_list.mat_idx], dep_list)

            else:
                #If Rule is feasible
                if rule.feasibility.is_invertible(
                ) and rule.feasibility.is_countable():
                    sub_rules = rule.rule_dependency.get_sub_rules()
                    for sub_rule in sub_rules:
                        list_of_dep_list = sub_rule.get_list_of_dep_list()
                        for dep_list in list_of_dep_list:
                            if dep_list.is_active():
                                dep_list.mat_slice = JTRGuessCount.get_slice_for_dep_list_in_matrix_attr(
                                    matrix_list[dep_list.mat_idx], dep_list)

                else:
                    continue
        if RUNTIME_CONFIG['debug'] == True:
            print("Total Memory Usage For Counting: {}\n".format(
                sizeof_fmt(memory_used)))
        ######################## Grouping Algorithm Ends Here ########################
        return matrix_list

    def fill_matrices(wordlist, matrix_list):
        """ After building the matrix, fill in matrix 
        
        Attr:
            wordlist: wordlist
            matrix_list: prebuilt matrix list
        """
        #print("Doing Optimization For Filling Matrices\n")

        #lower_minus_something = []
        #upper_minus_something = []

        # Optimization on some cases
        # set(digits) - set(something)
        digit_set = frozenset(CHARS_DIGITS)
        digit_minus_something = []
        digit_minus_something_sets = []
        # set(letters) - set(something)
        letter_set = frozenset(CHARS_LETTERS)
        letter_minus_something = []
        letter_minus_something_sets = []
        # all ranges
        all_from_to_ranges = set()

        for mat in matrix_list:
            for k, v in mat.dim_attributes.items():
                if k[0] == AttributeType.CHARS and len(
                        k[1]) >= len(letter_set) - 5 and len(
                            k[1]) <= len(letter_set) - 1 and k[1].issubset(
                                letter_set):
                    val = "".join(letter_set - k[1])
                    if (val, frozenset(k[1])) not in letter_minus_something:
                        letter_minus_something.append((val, frozenset(k[1])))

                if k[0] == AttributeType.CHARS and len(
                        k[1]) >= len(digit_set) - 5 and len(
                            k[1]) <= len(digit_set) - 1 and k[1].issubset(
                                digit_set):
                    val = "".join(digit_set - k[1])
                    if (val, frozenset(k[1])) not in digit_minus_something:
                        digit_minus_something.append((val, frozenset(k[1])))

                if k[0] == AttributeType.CHARS_RANGE:
                    all_from_to_ranges.add((k[2], k[3]))

        # optimization precomputation ends

        ######### Start Filling Matrix #########
        # print("Filling Matrices\n")
        for word in wordlist:
            char_counter = Counter(word)
            # v[1] can be negative
            chat_counter_of_ranges = {
                v: Counter(word[v[0]:v[1]] if v[1] != 0 else word[v[0]:])
                for v in all_from_to_ranges
            }  # precompute charcounter on all ranges
            word_len = len(word)

            #Caching is Shared Among Mats.
            cached_result = {}

            #Some Special Optimization For sxy
            #Letter -- Vary From Password Policy
            if letter_minus_something == []:
                pass
            else:
                num_letters = sum(c.isalpha() for c in word)
                cached_result[(AttributeType.CHARS,
                               frozenset(letter_set))] = num_letters
                for (val, corresponding_set) in letter_minus_something:
                    tmp_count = num_letters
                    tmp_count -= sum(char_counter[c] for c in val)
                    cached_result[(AttributeType.CHARS,
                                   corresponding_set)] = tmp_count

            #Digit -- Vary From Password Policy
            if digit_minus_something == []:
                pass
            else:
                num_digits = sum(char_counter[c] for c in digit_set)
                #num_digits = sum(c.isdigit() for c in word)
                cached_result[(AttributeType.CHARS,
                               frozenset(digit_set))] = num_digits
                for (val, corresponding_set) in digit_minus_something:
                    tmp_count = num_digits
                    tmp_count -= sum(char_counter[c] for c in val)
                    cached_result[(AttributeType.CHARS,
                                   corresponding_set)] = tmp_count

            for mat in matrix_list:
                if mat.dim_len == 0:
                    continue

                lst = []
                for k, v in mat.dim_attributes.items():

                    # get attr_type
                    attr_type = k[0]

                    if attr_type == AttributeType.CHARS:  #Reject unless # of instances of char
                        #Optimize using caching
                        if k in cached_result:
                            num_count = cached_result[k]

                        else:
                            num_count = sum(char_counter[val] for val in k[1])

                            if len(k[1]) >= 5:  # save cached result
                                cached_result[k] = num_count

                        if num_count >= v - 1:
                            num_count = v - 1

                        lst.append(num_count)

                    elif attr_type == AttributeType.CHARS_AT_POS:  #Reject unless char in position
                        #Optimize using caching too?
                        #It should be very fast
                        min_len = k[2] + 1 if k[2] >= 0 else -k[2]

                        if word_len >= min_len and word[k[2]] in k[1]:
                            lst.append(1)
                        else:
                            lst.append(0)

                    elif attr_type == AttributeType.LENGTH:  #Length
                        lst.append(word_len)

                    elif attr_type == AttributeType.CHARS_RANGE:
                        if k in cached_result:
                            num_count = cached_result[k]

                        else:
                            num_count = sum(chat_counter_of_ranges[(k[2],
                                                                    k[3])][val]
                                            for val in k[1])

                            if len(k[1]) >= 5:
                                cached_result[k] = num_count

                        if num_count > v - 1:  # oversized
                            num_count = v - 1

                        lst.append(num_count)

                    else:
                        raise FatalRuntimeError("Unhandled attr_type")

                mat.mat[tuple(lst)] += 1  #Add word
        ################### Filling Matrix Ends Here ###################

    def count_rules(wordlist,
                    rules,
                    preprocess_path="../data/preprocess/",
                    safe_mode=False):
        """ Count rules.
        
        if feasibility is None, determine countability based on rule.rule_depenency
        otherwise determine countability based on feasibility

        If not countable, should have precomputed count data in file, otherwise raise exception (unless safe = True)

        Args:
            rules: parsed rules
            
            wordlist: wordlist
            
            preprocess_path: where to read data for not countable
            
            has_feasibility: additional feasibility information.

            safe_mode: whether to ignore errors. 
        """
        if len(rules) == 0:
            return []

        has_feasibility = True if hasattr(rules[0], 'feasibility') else False

        stime = perf_counter()
        matrix_list = JTRGuessCount.build_matrix(
            rules, has_feasibility)  # First build matrix

        fillstime = perf_counter()
        JTRGuessCount.fill_matrices(wordlist, matrix_list)  # make one pass
        filletime = perf_counter()

        ################## Counting all the rules using the matrix ##################
        counts = []
        for i, rule in enumerate(rules):

            # if countable:
            if (has_feasibility == False and rule.rule_dependency != None) or (
                    has_feasibility == True and
                    rule.feasibility.is_invertible() and
                    rule.feasibility.is_countable() == True):
                total_count = 0

                for sub_rule_dependency in rule.rule_dependency.list_of_sub_rule_dep:
                    sub_count = 0

                    if sub_rule_dependency.is_satisfied():
                        #Subrule is somehow satisfied.
                        if sub_rule_dependency.list_of_dep_list == []:
                            sub_count += sub_rule_dependency.get_coef() * len(
                                wordlist)

                        else:
                            for dependency_list in sub_rule_dependency.list_of_dep_list:
                                sub_count += dependency_list.get_coef() * len(
                                    wordlist)
                            sub_count *= sub_rule_dependency.get_coef()

                    elif sub_rule_dependency.is_rejected():
                        pass

                    elif sub_rule_dependency.is_active():
                        for dependency_list in sub_rule_dependency.list_of_dep_list:
                            if dependency_list.is_satisfied():
                                sub_count += dependency_list.get_coef() * len(
                                    wordlist)
                            elif dependency_list.is_rejected():
                                continue
                            elif dependency_list.is_active():
                                sub_count += int(dependency_list.get_coef(
                                )) * matrix_list[dependency_list.
                                                 mat_idx].get_sum_for_a_slice(
                                                     dependency_list.mat_slice)
                                #Debug:
                                #print(matrix_list[dependency_list.mat_idx])
                                #print(dependency_list.mat_slice)
                                #print(dependency_list.mat_idx)
                            else:
                                raise FatalRuntimeError(
                                    "Unknown Status in Guess Count")

                        sub_count *= sub_rule_dependency.get_coef()

                    else:
                        raise FatalRuntimeError("Unknown Status in Guess Count")

                    total_count += sub_count

                counts.append(int(total_count))

            else:
                #Not Both. Read From File To Assure 100% Accuracy
                count_addr = preprocess_path + "count/rule{}.txt".format(
                    i)  #Starts With One.
                if os.path.exists(count_addr):
                    with open(count_addr) as f:
                        count_str = f.readlines()[0].strip()
                        counts.append(int(count_str))
                        continue

                else:
                    if safe_mode == True:
                        continue
                    else:
                        raise FatalRuntimeError(
                            "Not PreExisiting Data For Not Countable Rules")

        if RUNTIME_CONFIG['debug'] == True:
            print(
                "Total Time For Filling Matrices: [%.3f secs]\tTotal Time For Counting (Building + Filling): [%.3f secs]\n"
                % (filletime - fillstime, perf_counter() - stime))

        #return data_addr for verification
        counts = np.array(counts)  # count for each batch of words
        cumsum = np.cumsum(counts)
        cumsum = np.append(cumsum, 0)
        ####################### counting rules ends here ###################

        return counts, cumsum


class HashcatGuessCount():

    def get_batch_rule_size(kernel_loops_orig):
        """ get how many rules in a batch using HC's algorithm """
        #https://github.com/alexliu0809/hashcat/blob/master/src/autotune.c#L44

        kernel_loops = kernel_loops_orig
        kernel_accel_orig = 512
        diff = np.uint32(kernel_loops_orig - kernel_accel_orig)
        #print("diff: {}".format(diff))
        for f in range(1, 1024):

            kernel_accel_try = kernel_accel_orig * f
            kernel_loops_try = kernel_loops_orig // f
            if (kernel_accel_try > 1024):
                break
            diff_new = np.uint32(kernel_loops_try - kernel_accel_try)
            #print("diff_new:{}".format(diff_new))
            if (diff_new > diff):
                break
            kernel_accel = kernel_accel_try
            kernel_loops = kernel_loops_try

        if kernel_loops >= 1024:
            kernel_loops = 1024

        if kernel_loops < 1:
            kernel_loops = 1

        return kernel_loops

    def dep_to_tuple(dep):
        """ Convery a dependency to hashable tuple """
        attr_type = dep.get_type()

        if attr_type == 1:
            return (1, dep.get_number(), frozenset(dep.get_chars()))

        elif attr_type == 2:  #Reject unless # of instances of char
            return (2, dep.get_number(), frozenset(dep.get_chars()))

        elif attr_type == 3:  #Reject unless char in position
            return (3, dep.get_position(), frozenset(dep.get_chars()))

        elif attr_type == 4:
            return (4, dep.get_from(), dep.get_to(), dep.get_number(),
                    frozenset(dep.get_chars()))

        elif attr_type == 5:
            return (5, dep.get_from(), dep.get_to(), dep.get_number(),
                    frozenset(dep.get_chars()))

        elif attr_type == 6:  #RejectUnlessLessThanLength
            return (6, dep.get_len())

        elif attr_type == 7:  #RejectUnlessGreaterThanLength
            return (7, dep.get_len())

        else:
            raise Exception("attr_type error")

        return dep_tuple

    def pipe_batched_rules_to_disk(batch_not_countable_rules,
                                   preprocess_path="../data/preprocess/"):
        """ pipe a batch of rules to disk """
        for batch_id, batched_rules in enumerate(batch_not_countable_rules):
            write_rules_to_file(
                "{}/rulesbatch{}.rule".format(preprocess_path, batch_id),
                batched_rules, batch_id)

    def count_words(wordlist,
                    rulelist,
                    preprocess_path="../data/preprocess/",
                    safe_mode=False):
        """ given a wordlist address and a parsed (with dependencies) rulelist, get count for words

        The Core Logic is first unique all dependencies. If one dep in dep_list is false, this dep_list is False.
        Thus, this dep_list will not make a guess. 
        All dep_lists having this dep will not make a guess.

        Args:
            wordlist: a wordlist that is OrderedDict

            rulelist: the parsed rulelist with dependencies


        """
        ######### Setting up some variables related to running #########
        external_bash_process = Popen(['/bin/bash'], stdin=PIPE, stdout=PIPE)

        # number of words in a batch
        batch_size_of_words = RUNTIME_CONFIG['batch_size_of_words']

        # number of rules in a batch
        if RUNTIME_CONFIG['batch_size_of_rules'] == "auto":
            batch_size_of_rules = HashcatGuessCount.get_batch_rule_size(
                len(rulelist))  #One count for each batch of rules
            RUNTIME_CONFIG['batch_size_of_rules'] = batch_size_of_rules
        else:
            batch_size_of_rules = RUNTIME_CONFIG['batch_size_of_rules']

        # how many rules in each rule batch
        t = len(rulelist)
        number_of_rules_in_each_batch = []
        while t - batch_size_of_rules > 0:
            number_of_rules_in_each_batch.append(batch_size_of_rules)
            t -= batch_size_of_rules
        if t != 0:
            number_of_rules_in_each_batch.append(t)

        RUNTIME_CONFIG[
            'number_of_rules_in_each_batch'] = number_of_rules_in_each_batch

        # how many words in each word batch
        t = len(wordlist)
        number_of_words_in_each_batch = []
        while t - batch_size_of_words > 0:
            number_of_words_in_each_batch.append(batch_size_of_words)
            t -= batch_size_of_words
        if t != 0:
            number_of_words_in_each_batch.append(t)

        RUNTIME_CONFIG[
            'number_of_words_in_each_batch'] = number_of_words_in_each_batch
        #################################################################

        ######### Get all active dependencies and unique them. #########
        if RUNTIME_CONFIG['debug'] == True:
            print("Start Counting Preparation\n")

        #Save All dependencies
        all_deps = OrderedDict()
        unique_dep_list_id = 0  # Count Total dep_list across all batches

        # saves the mapping from either dep to dep_list if dep_type == 2/3 or from dep to dep_list if dep_type = 4/5.
        mapping_from_dep_to_dep_list = []
        mapping_from_max_length_to_dep_list = [
            [] for i in range(RUNTIME_CONFIG['min_cut_length'] + 1)
        ]
        mapping_from_min_length_to_dep_list = [
            [] for i in range(RUNTIME_CONFIG['min_cut_length'] + 1)
        ]

        # Save for all batches of rules how many dep_lists are involved
        batch_satisfied_counts = []
        batch_dep_list_counts = []

        # Saves not countable rules in different batches.
        batch_not_countable_rules = []

        #count how many dep_lists for current batch of rules
        current_batch_not_countable_rules = None
        current_batch_dep_list_count = None  # active dep this batch
        current_batch_satisfied_count = None  # satisfied dep this batch
        current_batch_id = -1  # current batch number.

        # Precal the total number of chars for some sets.
        # For rule type 1 and 2.
        add_from_digit = []
        reduce_from_digit = []
        add_from_letter = []
        reduce_from_letter = []
        digit_set = frozenset(CHARS_DIGITS)
        letter_set = frozenset(CHARS_LETTERS)
        precalc_range = 3  # denote how many chars are different from the standard set.
        all_from_to_ranges = set()

        # Start processing all dep_lists now.
        # Will extract all the information related to counting
        # Get all active deps in this part.
        for r_idx, rule in enumerate(rulelist):
            # if a new batch starts
            if r_idx % batch_size_of_rules == 0:
                if current_batch_dep_list_count != None:
                    batch_dep_list_counts.append(current_batch_dep_list_count)
                if current_batch_satisfied_count != None:
                    batch_satisfied_counts.append(current_batch_satisfied_count)
                if current_batch_not_countable_rules != None:
                    batch_not_countable_rules.append(
                        current_batch_not_countable_rules)

                #Create new batch
                current_batch_not_countable_rules = []
                current_batch_dep_list_count = 0
                current_batch_satisfied_count = 0
                current_batch_id += 1

            # Not Countable
            if rule.rule_dependency == None:
                #For right now do nothing to no countable.
                current_batch_not_countable_rules.append(rule)
                continue

            for subrule_dependency in rule.rule_dependency.get_sub_rules():
                if subrule_dependency.is_satisfied():
                    current_batch_satisfied_count += subrule_dependency.get_coef(
                    )
                    continue

                # for each active dependency_list
                for dep_list in subrule_dependency:
                    # active dep_list
                    if dep_list.is_active():
                        # active deps
                        for dep in dep_list.get_active():

                            dep_tuple = HashcatGuessCount.dep_to_tuple(dep)

                            # establish a link from the dep (<N) to the dep_list
                            if dep_tuple[0] == 6:
                                mapping_from_max_length_to_dep_list[
                                    dep_tuple[1]].append((unique_dep_list_id,
                                                          current_batch_id))

                            # establish a link from the dep (>N) to the dep_list
                            # the length deps are not saved anymore
                            elif dep_tuple[0] == 7:
                                mapping_from_min_length_to_dep_list[
                                    dep_tuple[1]].append((unique_dep_list_id,
                                                          current_batch_id))

                            # other types of deps, there is no way to optimize now.
                            elif 5 >= dep_tuple[0] >= 1:
                                # If this dep is saved in all_deps, get the saved index and link to this dep_list
                                if dep_tuple in all_deps:
                                    mapping_from_dep_to_dep_list[
                                        all_deps[dep_tuple]].append(
                                            (unique_dep_list_id,
                                             current_batch_id))

                                # Not saved before
                                else:
                                    #Create a new list
                                    mapping_from_dep_to_dep_list.append(
                                        [(unique_dep_list_id,
                                          current_batch_id)])
                                    #Add to dep list
                                    all_deps[dep_tuple] = None

                                # track from, to ranges
                                if 5 >= dep_tuple[0] >= 4:
                                    all_from_to_ranges.add(
                                        dep_tuple[1], dep_tuple[2])

                                elif 2 >= dep_tuple[0] >= 1:
                                    # if set = digit + some
                                    if len(digit_set) < len(
                                            dep_tuple[2]
                                    ) and len(dep_tuple[2]) <= len(
                                            digit_set
                                    ) + precalc_range and digit_set.issubset(
                                            dep_tuple[2]):
                                        if (dep_tuple[2],
                                                dep_tuple[2] - digit_set
                                           ) not in add_from_digit:
                                            add_from_digit.append(
                                                (dep_tuple[2],
                                                 dep_tuple[2] - digit_set))
                                    # if set = digit - some
                                    elif len(digit_set) > len(
                                            dep_tuple[2]) and len(
                                                dep_tuple[2]) >= len(
                                                    digit_set
                                                ) - precalc_range and dep_tuple[
                                                    2].issubset(digit_set):
                                        if (dep_tuple[2],
                                                digit_set - dep_tuple[2]
                                           ) not in reduce_from_digit:
                                            reduce_from_digit.append(
                                                (dep_tuple[2],
                                                 digit_set - dep_tuple[2]))
                                    # if set = letter + some
                                    elif len(letter_set) < len(
                                            dep_tuple[2]
                                    ) and len(dep_tuple[2]) <= len(
                                            letter_set
                                    ) + precalc_range and letter_set.issubset(
                                            dep_tuple[2]):
                                        if (dep_tuple[2],
                                                dep_tuple[2] - letter_set
                                           ) not in add_from_letter:
                                            add_from_letter.append(
                                                (dep_tuple[2],
                                                 dep_tuple[2] - letter_set))
                                    # if set = letter - some
                                    elif len(letter_set) > len(
                                            dep_tuple[2]) and len(
                                                dep_tuple[2]) >= len(
                                                    letter_set
                                                ) - precalc_range and dep_tuple[
                                                    2].issubset(letter_set):
                                        if (dep_tuple[2],
                                                letter_set - dep_tuple[2]
                                           ) not in reduce_from_letter:
                                            reduce_from_letter.append(
                                                (dep_tuple[2],
                                                 letter_set - dep_tuple[2]))

                            else:
                                raise Exception("dep_tuple[0] error")

                        unique_dep_list_id += 1
                        current_batch_dep_list_count += 1

                    elif dep_list.is_rejected():  #Rejected
                        continue

                    elif dep_list.is_satisfied():  #Satisfied
                        current_batch_satisfied_count += 1

                    else:
                        raise Exception("Unknown Status")

        # add the last batch
        batch_dep_list_counts.append(current_batch_dep_list_count)
        batch_satisfied_counts.append(current_batch_satisfied_count)
        batch_not_countable_rules.append(current_batch_not_countable_rules)

        # convert to numpy array
        batch_dep_list_counts = np.array(batch_dep_list_counts)
        batch_satisfied_counts = np.array(batch_satisfied_counts)

        unique_dep_list_count = unique_dep_list_id

        if has_count_data() == True:
            if RUNTIME_CONFIG['debug'] == True:
                print("Restoring Count Data From Saved Files\n")
            return restore_counts_from_file()
        #############################################################

        ###### Get ready and start getting count for each word here ######
        # convert all_deps to a list
        all_deps = list(all_deps.keys())
        """
        _, word_list_name = os.path.split(word_list_addr)
        _, rule_list_name = os.path.split(rule_list_addr)
        

        # Read saved information  
        wordlist_hash = hashlib.md5(open(word_list_addr, 'rb').read()).hexdigest()
        rulelist_hash = hashlib.md5(open(rule_list_addr, 'rb').read()).hexdigest()
        f = open(data_addr, 'w+')
        f.write("Wordlist Hash:{}\n".format(wordlist_hash))
        f.write("Rulelist Hash:{}\n".format(rulelist_hash))
        #f.write("Password_Policy:{}\t{}\t{}\t{}\t{}\t{}\n".format(policyinfo_length,policyinfo_digits,policyinfo_letters,policyinfo_lowers,policyinfo_uppers,policyinfo_symbols))
        f.write("CountModel:{}\n".format(count_model))
        """

        # actual counting part.
        stime = perf_counter()

        # Write uncountable rules to disk as batches
        HashcatGuessCount.pipe_batched_rules_to_disk(batch_not_countable_rules,
                                                     preprocess_path)

        if RUNTIME_CONFIG['debug'] == True:
            print("Start Counting\n")
        # In-Line Function Def
        def count_each_word(word):
            """ This function counts the guesses made by each word for each batch of rules """
            # Mark whether the dep_list is rejected or not
            not_rejected_dep_lists = [True] * unique_dep_list_count

            # Save the count for each word with each batch
            count_for_this_word = np.array(batch_dep_list_counts, copy=True)

            # Counter
            char_counter = Counter(word)
            chat_counter_of_ranges = {
                v: Counter(word[v[0]:v[1]] if v[1] != 0 else word[v[0]:])
                for v in all_from_to_ranges
            }  # precompute charcounter on all ranges

            # Length
            length = len(word)

            # Save pre_calced set data.
            pre_calced = {}

            # doing some precalculation
            count = 0
            for c in digit_set:
                count += char_counter[c]
            pre_calced[digit_set] = count

            for chars, diff in add_from_digit:
                digit_count = count
                for c in diff:
                    digit_count += char_counter[c]
                pre_calced[chars] = digit_count

            for chars, diff in reduce_from_digit:
                digit_count = count
                for c in diff:
                    digit_count -= char_counter[c]
                pre_calced[chars] = digit_count

            count = 0
            for c in letter_set:
                count += char_counter[c]
            pre_calced[letter_set] = count

            for chars, diff in add_from_letter:
                letter_count = count
                for c in diff:
                    letter_count += char_counter[c]
                pre_calced[chars] = letter_count

            for chars, diff in reduce_from_letter:
                letter_count = count
                for c in diff:
                    letter_count -= char_counter[c]
                pre_calced[chars] = letter_count

            # Start counting here
            # Handle dep type 6. unless <something
            # if len = 10, rejections like <10, <9, <8, etc are not satisfied.
            for val in range(0, length + 1):
                for dep_list_idx, batch_idx in mapping_from_max_length_to_dep_list[
                        val]:
                    if not_rejected_dep_lists[dep_list_idx] == True:
                        not_rejected_dep_lists[dep_list_idx] = False
                        count_for_this_word[batch_idx] -= 1

            #Handle dep type 7. unless >something
            for val in range(length, len(mapping_from_min_length_to_dep_list)):
                for dep_list_idx, batch_idx in mapping_from_min_length_to_dep_list[
                        val]:
                    if not_rejected_dep_lists[dep_list_idx] == True:
                        not_rejected_dep_lists[dep_list_idx] = False
                        count_for_this_word[batch_idx] -= 1

            # Handle dep type 1 - 5
            for dep_idx, dep_tuple in enumerate(all_deps):

                #Set dep value based on word
                if dep_tuple[0] == 1:
                    nums = dep_tuple[1]
                    chars = dep_tuple[2]

                    #Hit
                    try:
                        nums -= pre_calced[chars]
                    #Not hit
                    except KeyError:
                        for c in chars:
                            nums -= char_counter[c]
                            if nums <= 0:
                                break

                    # Means not satisfied
                    if nums <= 0:
                        for dep_list_idx, batch_idx in mapping_from_dep_to_dep_list[
                                dep_idx]:
                            if not_rejected_dep_lists[dep_list_idx] == True:
                                not_rejected_dep_lists[dep_list_idx] = False
                                count_for_this_word[batch_idx] -= 1

                elif dep_tuple[0] == 2:
                    nums = dep_tuple[1]
                    chars = dep_tuple[2]

                    #Hit
                    try:
                        nums -= pre_calced[chars]
                    #Not hit
                    except KeyError:
                        for c in chars:
                            nums -= char_counter[c]
                            if nums <= 0:
                                break

                    # Means not satisfied
                    if nums > 0:
                        for dep_list_idx, batch_idx in mapping_from_dep_to_dep_list[
                                dep_idx]:
                            if not_rejected_dep_lists[dep_list_idx] == True:
                                not_rejected_dep_lists[dep_list_idx] = False
                                count_for_this_word[batch_idx] -= 1

                elif dep_tuple[0] == 3:
                    pos = dep_tuple[1]
                    chars = dep_tuple[2]

                    if pos >= 0:
                        # Means not satisfied
                        if pos >= length or word[pos] not in chars:
                            for dep_list_idx, batch_idx in mapping_from_dep_to_dep_list[
                                    dep_idx]:
                                if not_rejected_dep_lists[dep_list_idx] == True:
                                    not_rejected_dep_lists[dep_list_idx] = False
                                    count_for_this_word[batch_idx] -= 1
                    else:
                        # Means not satisfied
                        if -pos > length or word[pos] not in chars:
                            for dep_list_idx, batch_idx in mapping_from_dep_to_dep_list[
                                    dep_idx]:
                                if not_rejected_dep_lists[dep_list_idx] == True:
                                    not_rejected_dep_lists[dep_list_idx] = False
                                    count_for_this_word[batch_idx] -= 1

                elif dep_tuple[0] == 4:  # not equal to k[3]
                    counter_of_this_range = chat_counter_of_ranges[(k[1], k[2])]
                    if length < max(k[2], -k[1]) or sum(
                            counter_of_this_range[val]
                            for val in k[4]) != k[3]:  # not satisfied.
                        for dep_list_idx, batch_idx in mapping_from_dep_to_dep_list[
                                dep_idx]:
                            if not_rejected_dep_lists[dep_list_idx] == True:
                                not_rejected_dep_lists[dep_list_idx] = False
                                count_for_this_word[batch_idx] -= 1

                elif dep_tuple[0] == 5:  # at least k[3]
                    counter_of_this_range = chat_counter_of_ranges[(k[1], k[2])]
                    if length < max(k[2], -k[1]) or sum(
                            counter_of_this_range[val]
                            for val in k[4]) < k[3]:  # not satisfied.
                        for dep_list_idx, batch_idx in mapping_from_dep_to_dep_list[
                                dep_idx]:
                            if not_rejected_dep_lists[dep_list_idx] == True:
                                not_rejected_dep_lists[dep_list_idx] = False
                                count_for_this_word[batch_idx] -= 1

                elif dep_tuple[0] == 6:
                    raise ValueError("KeyError")

                elif dep_tuple[0] == 7:
                    raise ValueError("KeyError")

                else:
                    raise Exception("Unknown Val")

            return count_for_this_word

        # an empty list to save result
        counts_for_batches_of_words = []
        f = None
        for i, (word, _) in enumerate(wordlist.items()):
            # if a batch is full
            if i % batch_size_of_words == 0:
                if f != None:
                    # stop writing
                    f.close()
                    # Get count for not countable rules for this batch of words
                    forward_batched_words_and_batched_rules(
                        "tmp_wordlist.lst",
                        len(accumuate_count_for_this_batch_of_words),
                        accumuate_count_for_this_batch_of_words,
                        preprocess_path, external_bash_process)
                    # add total guesses for this batch of words
                    counts_for_batches_of_words.append(
                        np.array(
                            accumuate_count_for_this_batch_of_words, copy=True))

                # each batch reset everything
                f = open("{}/tmp_wordlist.lst".format(preprocess_path),
                         "w+")  # re-initialize f
                accumuate_count_for_this_batch_of_words = np.zeros_like(
                    batch_dep_list_counts)  # re-initialize

            f.write(word + "\n")
            count_for_this_word = count_each_word(word)
            accumuate_count_for_this_batch_of_words += count_for_this_word
            accumuate_count_for_this_batch_of_words += batch_satisfied_counts

        # consider that last batch
        # stop writing
        f.close()
        forward_batched_words_and_batched_rules(
            "tmp_wordlist.lst", len(accumuate_count_for_this_batch_of_words),
            accumuate_count_for_this_batch_of_words, preprocess_path,
            external_bash_process)
        counts_for_batches_of_words.append(
            np.array(accumuate_count_for_this_batch_of_words,
                     copy=True))  # add total guesses for this batch of words
        #print(counts_for_batches_of_words)
        if RUNTIME_CONFIG['debug'] == True:
            print("Total Time in Couting (including fwrite): {}\n".format(
                perf_counter() - stime))

        # cleaning
        for i in range(len(accumuate_count_for_this_batch_of_words)):
            os.remove("{}/rulesbatch{}.rule".format(
                preprocess_path, i)) if os.path.exists(
                    "{}/rulesbatch{}.rule".format(preprocess_path, i)) else None
        os.remove(
            "{}/tmp_wordlist.lst".format(preprocess_path)) if os.path.exists(
                "{}/tmp_wordlist.lst".format(preprocess_path)) else None
        ############################################################

        #return data_addr for verification
        counts = np.array(
            counts_for_batches_of_words)  # count for each batch of words
        cumsum = np.cumsum(counts)
        cumsum = np.append(cumsum, 0)

        #save data
        if RUNTIME_CONFIG['debug'] == True:
            print("Storing Count Data To Files\n")
        store_counts_to_file(counts, cumsum)
        store_count_data_hash()

        return counts, cumsum


class GuessCount():

    def get_counts(wordlist,
                   rules,
                   preprocess_path="../data/preprocess/",
                   safe_mode=False):
        if RUNTIME_CONFIG.is_jtr():
            if has_count_data() == False:
                counts, cumsum = JTRGuessCount.count_rules(
                    wordlist, rules, preprocess_path, safe_mode)
                if RUNTIME_CONFIG['debug'] == True:
                    print("Storing Count Data To Files\n")
                store_counts_to_file(counts, cumsum)
                store_count_data_hash()
                return counts, cumsum
            else:
                if RUNTIME_CONFIG['debug'] == True:
                    print("Restoring Count Data From Saved Files\n")
                return restore_counts_from_file()
        else:
            # hashcat's has_data detection is in the function
            return HashcatGuessCount.count_words(wordlist, rules,
                                                 preprocess_path, safe_mode)

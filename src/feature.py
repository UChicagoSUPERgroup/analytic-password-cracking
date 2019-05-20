"""This file contains definitions of different features and associated functions."""
from abc import ABCMeta, abstractmethod
from enum import Enum
from common import FatalRuntimeError
from utility import char_is_printable
from copy import deepcopy
from itertools import combinations
from config import RUNTIME_CONFIG


class RejectionRuleType(Enum):
    """ An enum that defines rejection rule type 

    Attr:
        REJECT_IF_CONTAINS_NUMBER_Of_CHAR: has < N instances of chars C.
        REJECT_UNLESS_CONTAINS_NUMBER_OF_CHAR: has >= N instances of chars C.
        Reject_Unless_Char_In_Position_Equals: chat at position N = C
        Reject_Unless_From_To_Has_Exactly_N_Chars: Range [from, to) contains N instances of chars C.
        Reject_Unless_From_To_Has_Atleast_N_Chars: Range [from, to) contains >= N instances of chars C.
        Reject_Unless_Less_Than_Length: Length < N
        Reject_Unless_Greater_Than_Length: Length > N
    """
    REJECT_IF_CONTAINS_NUMBER_Of_CHAR = 1
    REJECT_UNLESS_CONTAINS_NUMBER_OF_CHAR = 2
    REJECT_UNLESS_CHAR_IN_POSITION_EQUALS = 3
    REJECT_UNLESS_FROM_TO_HAS_EXACTLY_N_CHARS = 4
    REJECT_UNLESS_FROM_TO_HAS_ATLEAST_N_CHARS = 5
    REJECT_UNLESS_LESS_THAN_LENGTH = 6
    REJECT_UNLESS_GREATER_THAN_LENGTH = 7


class DependencyStatus(Enum):
    """ An enum that defines dependency status

    Attr:
        ACTIVE: The dependency/dependency list is active, accepts some specific input.
        REJECTED: The dependency/dependency list is rejected, rejects any input
        SATISFIED: The dependency/dependency list is satisfied, accepts any input
    """
    ACTIVE = 1
    REJECTED = 2
    SATISFIED = 3

    def __gt__(self, other):
        if type(other) != DependencyStatus:
            raise Exception("Error")

        return self.value > other.value

    def __eq__(self, other):
        if type(other) != DependencyStatus:
            raise Exception("Error")

        return self.value == other.value


class RuleDependency():
    """ Class that holds all subrule dependencies for a rule. """

    def __init__(self):
        """ Initialize RuleDependency """
        self.list_of_sub_rule_dep = []

    def __repr__(self):
        """ Get string repr of this class """
        string = "Rule Dependency:\n"
        for idx, val in enumerate(self.list_of_sub_rule_dep):
            #string += "\tDependency List #{}, Status {}, Associated Chars {}, Dependencies:\n".format(idx,Status(val.status).name,val.current_sets)
            string += "\tSubRule #{}, ".format(idx) + repr(val) + "\n"
            #string += "\n\n"
        return string

    def add_sub_rule_dep(self, sub_rule_dep):
        """ Add sub_rule dependency. 
    
        Args:
            sub_rule_dep: an instance of SubruleRuleDependency to be added
        """
        sub_rule_dep.clean_list()
        self.list_of_sub_rule_dep.append(sub_rule_dep)

    def get_sub_rules(self):
        """ return all subrule instances """
        return self.list_of_sub_rule_dep


class SubruleDependency():
    """ Class that holds all dependency lists for a subrule.
    
    Attr:
        list_of_dep_list: a list of DependencyList elements

        status: current status, an instance of DependencyStatus

        coef: coefficiency used when counting, introduced by transformations like AN"[1-9]".
    """

    def __len__(self):
        return len(self.list_of_dep_list)

    def __init__(self, extend_from=None):
        """ Initialize an instance of SubruleRuleDependency

        Args:
            extend_from: extend the coefficency from this instance.
        """
        self.list_of_dep_list = []
        self.status = DependencyStatus.SATISFIED

        # coefficiency used when counting, introduced by transformations like AN"[1-9]".
        if extend_from == None:
            self.coef = 1

        else:
            self.coef = extend_from.coef

    def merge(self, another_sub_rule_dependency):
        """ merge another sub_rule_dependency """
        if type(another_sub_rule_dependency) != SubruleDependency:
            raise Exception("another_sub_rule_dependency type wrong")

        if another_sub_rule_dependency.coef != self.coef:
            raise Exception("Merge Failed, coef not match")

        # Merge and Update Data
        self.list_of_dep_list += deepcopy(
            another_sub_rule_dependency.list_of_dep_list)
        self.clean_list()

    def set_status(self, status):
        """ set current status """
        self.status = status

    def get_status(self):
        """ get current status """
        return self.status

    def get_list_of_dep_list(self):
        """ get list_of_dep_list attribute """
        return self.list_of_dep_list

    def append_dependency_list(self, dependency_list):
        """ append a dependency list to current list_of_dep_list, and perform clean_list() """
        dependency_list.update_current_sets()  #Accumulate coef
        self.list_of_dep_list.append(dependency_list)
        self.clean_list()

    def prepend_dependency_to_all_lists(self, dependency):
        """ prepend a dependency to all dependency_lists in list_of_dep_list. """
        if self.list_of_dep_list == []:
            self.list_of_dep_list = [DependencyList()]

        for single_list in self.list_of_dep_list:
            single_list.prepend_dependency(deepcopy(dependency))

        self.clean_list()

    def update_coef(self, char_sets):
        """ update the coef of this subrule"""
        if len(self.list_of_dep_list) != 0:
            raise Exception("Dont Set Rule Coef For None Empty Rule")
        else:
            for val in char_sets:
                self.coef *= len(val)

    def clean_list(self, final_round=False):
        """ Clean the list 
        
        Note:
            This is a high level clean, mostly recomputing the status of all dependency_lists.
        
            The status of this instance depends on whether the dependency lists it has are rejected/active/satisfied.
        
            Turn off clean if you want to debug raw dependency list

        Args:
            final_round: denote if this will be the last time calling clean_list()
        """

        is_totally_satisfied = True  # only contains satisfied elements
        is_totally_rejected = True  # only contains rejected elements
        is_active = True  # still active

        if self.list_of_dep_list == []:  #satisfied
            self.status = DependencyStatus.SATISFIED
            return

        # go over the list and set flags
        for depend_list in self.list_of_dep_list:
            depend_list.clean_list(final_round)  # Do lower level cleaning

            if depend_list.status == DependencyStatus.ACTIVE:
                is_totally_rejected = False
                is_totally_satisfied = False

            elif depend_list.status == DependencyStatus.SATISFIED:
                is_totally_rejected = False

            # depend_list.status == DependencyStatus.REJECTED
            else:
                is_totally_satisfied = False

        self.list_of_dep_list.sort(key=lambda x: (x.status))

        ### Extra cleaning in rule_dep
        # Kepp all active and satisfied depend_list, keep one rejected depend_list.
        new_list = []  # store the new result.
        added_rejection = False
        for depend_list in self.list_of_dep_list:
            if depend_list.status in (DependencyStatus.ACTIVE,
                                      DependencyStatus.SATISFIED):
                new_list.append(depend_list)
            elif added_rejection == False:
                new_list.append(depend_list)
                added_rejection = True

        self.list_of_dep_list = new_list  # update the list

        # recompute status
        if is_totally_satisfied == True or is_totally_rejected == True:
            is_active = False

        if is_active == True:
            self.status = DependencyStatus.ACTIVE
        elif is_totally_rejected == True:
            self.status = DependencyStatus.REJECTED
        elif is_totally_satisfied == True:
            self.status = DependencyStatus.SATISFIED
        else:
            raise Exception("Unknown Status: {} {} {}", is_active,
                            is_totally_rejected, is_totally_satisfied)

    def __iter__(self):
        """ yield from self.list_of_dep_list """
        yield from self.list_of_dep_list

    def __repr__(self):
        """ Get string repr """
        self.clean_list()
        string = "Rule Dependency Status: {} \n".format(
            DependencyStatus(self.status).name)
        for idx, val in enumerate(self.list_of_dep_list):
            string += "\t\tDependency List #{}, ".format(idx) + repr(val) + "\n"
        return string

    def is_rejected(self):
        """ return True if current status is rejected """
        return self.status == DependencyStatus.REJECTED

    def is_active(self):
        """ return True if current status is active """
        return self.status == DependencyStatus.ACTIVE

    def is_satisfied(self):
        """ return True if current status is satisfied """
        return self.status == DependencyStatus.SATISFIED

    def get_coef(self):
        """ return associated coef """
        return self.coef


class DependencyList():
    """ A class that contains a list of dependencies. 

    It is an intermediate Data Structure.

    Attr:
        this_list: a list of dependencies.

        status: dependency status

        current_sets: current parameter sets associated with this dependency_list
            Introduced by transformations like Az"[0-9][a-z]"

        mat_idx: an int, used in feature_extraction

        mat_slice: a slice, used in feature_extraction

        priority: an int, used in feature_extraction

        coef: coefficiency used when counting, introduced by transformations like AN"[1-9]".
    """

    def __init__(self, current_sets=[], extend_from=None):
        """ Initialize an instance of DependencyList
        
        Args:
            current_sets: a list of current parameter sets associated with this dependency_list
                Introduced by transformations like Az"[0-9][a-z]"
            
            extend_from: extend the coefficency from this instance.
        """

        # Actual Dependency List
        self.this_list = []
        # Initial Status: Satisfied, Add any active become active.
        self.status = DependencyStatus.SATISFIED
        self.current_sets = current_sets
        # For future use (build guess count matrix).
        self.mat_idx = None
        self.mat_slice = None
        self.priority = 0

        # extend prev coef
        if extend_from == None:
            self.coef = 1
        else:
            self.coef = extend_from.coef

    def update_current_sets(self, new_sets=[]):
        """ Move the current sets to history. Set current_sets to new_sets """

        # Move the current sets to history by updating coef.
        # Time cost is affordatble.
        for val in self.current_sets:
            self.coef *= len(val)

        self.current_sets = new_sets

    def get_coef(self):
        """ return associated coef """
        return self.coef

    def get_active(self):
        """ Get the list of dependencies that are still active. Assume sorted """
        for idx, val in enumerate(self.this_list):
            if val.is_active() != True:
                return self.this_list[:idx]
        else:
            return self.this_list

    def get_active_number(self):
        """ Get number of dependencies that are still active. Assume sorted """
        for idx, val in enumerate(self.this_list):
            if val.is_active() != True:
                return idx
        else:
            return len(self.this_list)

    def get_status(self):
        """ Get DependencyStatus """
        return self.status

    def set_status(self, status):
        """ Set DependencyStatus """
        self.status = status

    def is_rejected(self):
        """ return True if current status is rejected """
        return self.status == DependencyStatus.REJECTED

    def is_active(self):
        """ return True if current status is active """
        return self.status == DependencyStatus.ACTIVE

    def is_satisfied(self):
        """ return True if current status is satisfied """
        return self.status == DependencyStatus.SATISFIED

    def prepend_dependency(self, dependency):
        """ Invert one dependency to the front of the list, update the status of this list """
        if self.status == DependencyStatus.REJECTED:  # If the list is rejected. There's No Need To Add Anything
            return

        if dependency.status == DependencyStatus.SATISFIED:  # If dependency is satisfied. Add it, does not change the status of this dep_list.
            self.this_list.insert(0, dependency)
            return

        if dependency.status == DependencyStatus.REJECTED:  # If add a reject dependency. Reject entire list
            self.status = DependencyStatus.REJECTED
            self.this_list.insert(0, dependency)
            return

        # Add an active dpendency.
        self.this_list.insert(0, dependency)

        # If this dep_list is satisfied, it is no longer satisfied
        if self.status == DependencyStatus.SATISFIED:  # Now new dependency comes, list no longer satisfied
            self.status = DependencyStatus.ACTIVE

        self.clean_list()

    def __len__(self):
        """ Return length of the list """
        return len(self.this_list)

    def __iter__(self):
        """ yield from self.this_list """
        yield from self.this_list

    def __repr__(self):
        """ Get string repr """
        string = "Status {}, Dependencies:\n".format(
            DependencyStatus(self.status).name)
        for idx, val in enumerate(self.this_list):
            string += "\t\t\tDependency {}: ".format(idx) + repr(val) + "\n"
        return string

    def clean_list(self, final_round=False):
        """ Lower Level Cleaning.
        
        Reject if there are two conflict dependencies. Like length/Char in position.
        
        3 Rounds of Cleaning:
            1. Clean Length, Reject if Length Conflict
            2. Clean Chars, Reject if Chars Conflict
            3. Sort and scan, set status.
        
        Note:
            Turn off clean if you want to debug raw dependency list
            To debug this, print input list and output list.

        Args:
            final_round: Additional Non-Ascii Removal and sort.
                Final Round Should Be Called ONLY Once.
        """

        # Sort list in the order of status and then reverse order of dependency_type
        self.this_list.sort(key=lambda x: (x.status, 6 - x.dependency_type))

        ################ Round 1: Length ################
        new_list = []

        #Merge length right now.
        current_greater = -1000000
        current_less = float("inf")

        idx = 0

        for depend in self.this_list:
            if depend.get_status() != DependencyStatus.ACTIVE:
                break

            if depend.dependency_type == 3:
                #Implies word length > ori_pos (if >= 0)
                ori_pos = depend.get_position()
                min_len = ori_pos if ori_pos >= 0 else -(ori_pos + 1)
                if min_len > current_greater:
                    current_greater = min_len

            elif depend.dependency_type == 6:
                #Not need to check length anymore. Indicate number of length deps
                idx += 1
                ori_len = depend.get_len()
                if ori_len < current_less:
                    current_less = ori_len

            elif depend.dependency_type == 7:
                #Not need to check length anymore. Indicate number of length deps
                idx += 1
                ori_len = depend.get_len()
                if ori_len > current_greater:
                    current_greater = ori_len

            elif 2 >= depend.dependency_type >= 1:
                break

            elif 5 >= depend.dependency_type >= 4:
                #Not need to check length anymore. Indicate number of length deps
                min_len = depend.get_min_len()
                if min_len - 1 > current_greater:
                    current_greater = min_len - 1

            else:
                raise Exception("Unknown dependency_type")

        #If there is a dependency that requires > something
        if current_greater != -1000000:
            new_list.append(RejectUnlessGreaterThanLength(current_greater))

        #If there is a dependency that requires < something
        if current_less != float("inf"):
            new_list.append(RejectUnlessLessThanLength(current_less))

        #Test if it is rejected already
        #Short Circuit Here If Length Is A Problem
        if current_greater >= current_less - 1:
            self.this_list = new_list
            self.this_list[0].set_status(DependencyStatus.REJECTED)
            self.this_list[1].set_status(DependencyStatus.REJECTED)
            self.set_status(DependencyStatus.REJECTED)
            return

        if current_greater == current_less - 2:  #Of Length 1.
            for i in range(idx, len(self.this_list)):
                if self.this_list[i].get_status(
                ) != DependencyStatus.ACTIVE:  #Not Valid Anymore
                    break

                #If Length == something, if some certain length, change negative to positive
                elif self.this_list[i].get_type() == 3:
                    ori_pos = self.this_list[i].get_position()
                    if ori_pos < 0:
                        new_pos = ori_pos + current_less - 1  #Get Positive position
                        self.this_list[i].set_position(new_pos)

        ################ Round 2: Chars ################
        ### Additional Check For Final Round
        if final_round == True:
            for i in range(idx, len(self.this_list)):
                if self.this_list[i].get_status(
                ) != DependencyStatus.ACTIVE:  #Not Valid Anymore
                    break

                #Remove non-ascii in final round
                elif self.this_list[i].get_type(
                ) == 2 or self.this_list[i].get_type() == 3:
                    ori_set = self.this_list[i].get_chars()
                    dest_set = set(
                        x for x in ori_set if char_is_printable(x) == True)
                    self.this_list[i].set_chars(dest_set)

            self.this_list.sort(key=lambda x: (x.status, 6 - x.dependency_type))

        #Merge Other dependencies. Only Merge When chars are subset.
        #Double Check This Logic Simplifier.
        len_initial_new_list = len(new_list)

        for i in range(idx, len(self.this_list)):

            if self.this_list[i].get_status(
            ) != DependencyStatus.ACTIVE:  #Not Valid Anymore
                new_list += self.this_list[
                    i:i +
                    1]  #Add one rejection/satisfaction to denote satisfied/rejected.
                break

            merged = False

            #Ignore Length Dependencies. Already simplified
            for j in range(len_initial_new_list, len(
                    new_list)):  # Go check with what's added to the new_list
                dep_i = self.this_list[i]  # current dep to be added

                dep_j = new_list[j]  # One old dep in new_list

                if dep_i.get_type() == dep_j.get_type():  #same type
                    if dep_i.get_type() == 1:
                        if dep_i.get_number() == dep_j.get_number(
                        ):  #same number

                            chars_i = dep_i.get_chars()
                            chars_j = dep_j.get_chars()

                            if chars_j.issubset(chars_i):
                                new_list[j] = dep_i  # i contains j, use i.
                                merged = True
                                break

                            elif chars_i.issuperset(chars_j):
                                # j contains i, pass
                                merged = True
                                break

                            else:  #Not subset or superset. Add Both. j is already in
                                pass

                    elif dep_i.get_type() == 2:  #Unless/If Contains

                        if dep_i.get_number() == dep_j.get_number(
                        ):  #same number

                            chars_i = dep_i.get_chars()
                            chars_j = dep_j.get_chars()

                            if chars_i.issubset(chars_j):
                                new_list[
                                    j] = dep_i  # j contains i, use i instead.
                                merged = True
                                break

                            elif chars_i.issuperset(chars_j):
                                # i contains j, pass
                                merged = True
                                break

                            else:  #Not subset or superset. Add Both. j is already in
                                pass

                    elif dep_i.get_type() == 3:  #Unless Char in Pos

                        if dep_i.get_position() == dep_j.get_position(
                        ):  #same pos

                            chars_i = dep_i.get_chars()
                            chars_j = dep_j.get_chars()

                            # Set To Intersection.
                            new_list[j].set_chars(chars_i.intersection(chars_j))
                            merged = True
                            break

                    elif 5 >= dep_i.get_type(
                    ) >= 4:  #[from, to) contains N instance of C
                        if dep_i.get_from() == dep_j.get_from() and\
                            dep_i.get_to() == dep_j.get_to() and\
                            dep_i.get_number() == dep_j.get_number(): #same number

                            chars_i = dep_i.get_chars()
                            chars_j = dep_j.get_chars()

                            if chars_i.issubset(chars_j):
                                new_list[
                                    j] = dep_i  # j contains i, use i instead.
                                merged = True
                                break

                            elif chars_i.issuperset(chars_j):
                                # i contains j, pass
                                merged = True
                                break

                            else:  #Not subset or superset. Add Both. j is already in
                                pass

                    elif 7 >= dep_i.get_type() >= 6:
                        pass

                    else:
                        raise Exception("Unknown get_type Or Sort Error")

            if merged == True:  #If after the entire iteration, it is merged somewhere. do nothing.
                pass
            else:  #If it is not merged. Then add it to the new list
                new_list.append(self.this_list[i])

        ### Another round, merge dependencies with same chars that are only different in number
        # update this_list
        self.this_list = new_list  #Update current list
        self.this_list.sort(key=lambda x: (x.status, 6 - x.dependency_type))
        #print("Before:{}".format(self.this_list))
        new_list = []

        for i in range(len(self.this_list)):

            if self.this_list[i].get_status(
            ) != DependencyStatus.ACTIVE:  #Not Valid Anymore
                new_list += self.this_list[
                    i:i +
                    1]  #Add one rejection/satisfaction to denote satisfied/rejected.
                break

            merged = False

            #Ignore Length Dependencies. Already simplified
            for j in range(len(
                    new_list)):  # Go check with what's added to the new_list
                dep_i = self.this_list[i]  # current dep to be added

                dep_j = new_list[j]  # One old dep in new_list

                if dep_i.get_type() == dep_j.get_type():  #same type
                    if dep_i.get_type() == 1:  # If Contains, get smaller number
                        if dep_i.get_chars() == dep_j.get_chars(
                        ):  #same type, merge number

                            num_i = dep_i.get_number()
                            num_j = dep_j.get_number()

                            if num_i < num_j:
                                new_list[j] = dep_i  # lower number for if.
                                merged = True
                                break

                            else:
                                # i contains j, pass
                                merged = True
                                break

                    elif dep_i.get_type(
                    ) == 2:  # #Unless contains, get higher number
                        if dep_i.get_chars() == dep_j.get_chars(
                        ):  #same type, merge number

                            num_i = dep_i.get_number()
                            num_j = dep_j.get_number()

                            if num_i > num_j:
                                new_list[j] = dep_i  # higher number
                                merged = True
                                break

                            else:
                                # i contains j, pass
                                merged = True
                                break

                    elif dep_i.get_type() == 3:  #Unless Char in Pos
                        pass

                    elif dep_i.get_type() == 4:
                        if dep_i.get_from() == dep_j.get_from() and\
                            dep_i.get_to() == dep_j.get_to() and\
                            dep_i.get_chars() == dep_j.get_chars(): #same type

                            num_i = dep_i.get_number()
                            num_j = dep_j.get_number()

                            if num_i != num_j:  # two exactly with different number. Rejected
                                self.this_list = [dep_i, dep_j]
                                self.this_list[0].set_status(
                                    DependencyStatus.REJECTED)
                                self.this_list[1].set_status(
                                    DependencyStatus.REJECTED)
                                self.set_status(DependencyStatus.REJECTED)
                                return
                            else:  # merged.
                                merged = True
                                break

                    elif dep_i.get_type(
                    ) == 5:  #[from, to) contains N instance of C
                        if dep_i.get_from() == dep_j.get_from() and\
                            dep_i.get_to() == dep_j.get_to() and\
                            dep_i.get_chars() == dep_j.get_chars(): #same type

                            num_i = dep_i.get_number()
                            num_j = dep_j.get_number()

                            if num_i > num_j:
                                new_list[j] = dep_i  # higher number
                                merged = True
                                break

                            else:
                                # i contains j, pass
                                merged = True
                                break

                    elif 7 >= dep_i.get_type() >= 6:
                        pass

                    else:
                        raise Exception("Unknown get_type Or Sort Error")

            if merged == True:  #If after the entire iteration, it is merged somewhere. do nothing.
                pass
            else:  #If it is not merged. Then add it to the new list
                new_list.append(self.this_list[i])

        ################ Round 3: Sort Again And Check Status ################
        self.this_list = new_list  #Update current list
        self.this_list.sort(key=lambda x: (x.status, 6 - x.dependency_type))

        #Only Contains Satisfied.
        if len(self.this_list) == 0 or self.this_list[0].is_satisfied():
            self.status = DependencyStatus.SATISFIED
            return

        for i in range(0, len(self.this_list)):
            #Contains Rejected
            if self.this_list[i].is_rejected():
                #Only Get Rejected Part
                self.this_list = self.this_list[i:]
                self.status = DependencyStatus.REJECTED
                return

        # If mix of satisfied and active
        # Set Active
        self.status = DependencyStatus.ACTIVE


class BaseDependencyType(metaclass=ABCMeta):
    """ A base class for DependencyType. Implemented by other children classes """

    def __init__(self, dependency_type):
        self.dependency_type = dependency_type
        self.status = DependencyStatus.ACTIVE  #Active

    def set_status(self, status):
        if type(status) != DependencyStatus:
            raise FatalRuntimeError("Error Status Val: {}".format(status))
        self.status = status

    def get_status(self):
        return self.status

    def get_type(self):
        return self.dependency_type

    def is_rejected(self):
        return self.status == DependencyStatus.REJECTED

    def is_active(self):
        return self.status == DependencyStatus.ACTIVE

    def is_satisfied(self):
        return self.status == DependencyStatus.SATISFIED

    @abstractmethod
    def __repr__(self):
        pass


class RejectUnlessFromToContainsNumberOfChars(BaseDependencyType):
    """ Abstract class that has a range [From, to), a number N, and a set of chars C.
        Implemented by other children classes.

    Note:
        this class should be used together with length boundary.
        It implies that length is at least max(to_idx,-from_idx)

    Attr:
        from_idx: the start of a range (inclusive)

        to_idx: the end of a range (exclusive)

        number: int N, denote the number of chars needed

        charset: set of chars, denote the set of chars allowed.
    """

    def __init__(self, dependency_type, from_idx, to_idx, number, charset):
        """ Initialze an instance

        Args:
            dependency_type: the dependency_type of this instance
            
            from_idx: the start of a range (inclusive)
            
            to_idx: the end of a range (exclusive)
            
            number: int N, denote the number of chars needed
            
            charset: set of chars, denote the set of chars allowed.
        """
        BaseDependencyType.__init__(self, dependency_type)

        # [from, to)
        if from_idx >= to_idx:
            raise Exception("Initialization Error")

        if not ((from_idx >= 0 and to_idx >= 0) or
                (from_idx < 0 and to_idx <= 0)):
            raise Exception("Initialization Error")

        self.from_idx = from_idx
        self.to_idx = to_idx
        self.set_number(number)
        self.set_chars(charset)

    @abstractmethod
    def set_number(self):
        pass

    @abstractmethod
    def set_chars(self):
        """ set the charset """
        pass

    def get_from(self):
        """ get from_idx """
        return self.from_idx

    def get_to(self):
        """ get to_idx """
        return self.to_idx

    def get_min_len(self):
        """ get the minimum length requirement """
        return max(-self.from_idx, self.to_idx)

    def get_slice(self):
        """ convert range [from, to) to slice """
        start = None if self.from_idx == 0 else self.from_idx
        end = None if self.to_idx == 0 else self.to_idx
        return slice(start, end, None)


class RejectUnlessFromToContainsExactlyNumberOfChars(
        RejectUnlessFromToContainsNumberOfChars):
    """ Reject unless in range [From, to) contains EXACTLY N instances of char C.
    
    Note:
        this class should be used together with length boundary.
        It implies that length is at least max(to_idx,-from_idx).
        Number <= -1, rejected.
        set == set(): rejected if number > 0 else satisfied.
        Number <= -1 and set == set() should not happend at the same time.

    Attr:
        from_idx: the start of a range (inclusive)

        to_idx: the end of a range (exclusive)

        number: int N, denote the number of chars needed

        charset: set of chars, denote the set of chars allowed.
    """

    def __init__(self, from_idx, to_idx, number, charset):
        """ Initialze an instance

        Args:            
            from_idx: the start of a range (inclusive)
            
            to_idx: the end of a range (exclusive)
            
            number: int N, denote the number of chars needed
            
            charset: set of chars, denote the set of chars allowed.
        """
        if number <= -1 and charset == set():
            raise Exception("Initialization Error")

        RejectUnlessFromToContainsNumberOfChars.__init__(
            self, 4, from_idx, to_idx, number, charset)

    def __repr__(self):
        """ Get string repr """
        return "[{} - {}) Contains Exactly {} of {}, Status: {}".format(
            self.from_idx, self.to_idx, self.number, self.charset,
            DependencyStatus(self.status).name)

    def make_new(self, from_idx, to_idx, number, charset):
        """ make a new instance of this type by specifying the parameters 
        
        Args:            
            from_idx: the start of a range (inclusive)
            
            to_idx: the end of a range (exclusive)
            
            number: int N, denote the number of chars needed
            
            charset: set of chars, denote the set of chars allowed.
        """
        return RejectUnlessFromToContainsExactlyNumberOfChars(
            from_idx, to_idx, number, charset)

    def set_chars(self, charset):
        """ set the charset """
        self.charset = set(charset)
        #Empty set means there's no way for you to contain this char
        if charset == set():
            # number >= 0 guaranteed
            if self.number == 0:
                self.status = DependencyStatus.SATISFIED
            else:
                self.status = DependencyStatus.REJECTED

    def get_chars(self):
        """ get the charset """
        return self.charset

    def set_number(self, number):
        """ set the number """
        self.number = number
        #num=0 means it is auto contained
        if number <= -1:  #Rejected, either 0 or more that char
            self.status = DependencyStatus.REJECTED

        if number > self.to_idx - self.from_idx:  # greater than max possible
            self.status = DependencyStatus.REJECTED

    def get_number(self):
        """ get the number """
        return self.number


class RejectUnlessFromToContainsAtLeastNumberOfChars(
        RejectUnlessFromToContainsNumberOfChars):
    """ Reject unless in range [From, to) contains AT LEAST N instances of char C.

    Note:
        this class should be used together with length boundary.
        It implies that length is at least max(to_idx,-from_idx).
        If number <= 0, satisfied.
        If set == set(), rejected.
        set == set() and number <= 0 should not happend at the same time.

    Attr:
        from_idx: the start of a range (inclusive)

        to_idx: the end of a range (exclusive)

        number: int N, denote the number of chars needed

        charset: set of chars, denote the set of chars allowed.
    """

    def __init__(self, from_idx, to_idx, number, charset):
        """ Initialze an instance

        Args:            
            from_idx: the start of a range (inclusive)
            
            to_idx: the end of a range (exclusive)
            
            number: int N, denote the number of chars needed
            
            charset: set of chars, denote the set of chars allowed.
        """
        if number <= 0 and charset == set():
            raise Exception("Initialization Error")

        RejectUnlessFromToContainsNumberOfChars.__init__(
            self, 5, from_idx, to_idx, number, charset)

    def __repr__(self):
        """ Get string repr """
        return "[{} - {}) Contains At Least {} of {}, Status: {}".format(
            self.from_idx, self.to_idx, self.number, self.charset,
            DependencyStatus(self.status).name)

    def make_new(self, from_idx, to_idx, number, charset):
        """ make a new instance of this type by specifying the parameters 
        
        Args:            
            from_idx: the start of a range (inclusive)
            
            to_idx: the end of a range (exclusive)
            
            number: int N, denote the number of chars needed
            
            charset: set of chars, denote the set of chars allowed.
        """
        return RejectUnlessFromToContainsAtLeastNumberOfChars(
            from_idx, to_idx, number, charset)

    def set_chars(self, charset):
        """ set the charset """
        self.charset = set(charset)
        #Empty set means there's no way for you to contain this char
        if charset == set():
            self.status = DependencyStatus.REJECTED

    def get_chars(self):
        """ get the charset """
        return self.charset

    def set_number(self, number):
        """ set the number """
        self.number = number
        #num=0 means it is auto contained
        if number <= 0:  #Satisfied
            self.status = DependencyStatus.SATISFIED

        if number > self.to_idx - self.from_idx:  # greater than max possible
            self.status = DependencyStatus.REJECTED

    def get_number(self):
        """ get the number """
        return self.number


class RejectNumberChars(BaseDependencyType, metaclass=ABCMeta):
    """ Abstract class that has a number N and a set of chars C.
        Implemented by other children classes.

    Attr:
        dependency_type: the dependency type of this class

        number: int N, denote the number of chars needed

        charset: set of chars, denote the set of chars allowed.
    """

    def __init__(self, dependency_type, charset, number):
        """ Initialize the instance """
        if number <= 0 and charset == set():
            raise ValueError("Both 0 Same Time")

        BaseDependencyType.__init__(self, dependency_type)
        self.set_chars(charset)  # Could input a single char "a" or set.
        self.set_number(number)

    def get_chars(self):
        """ get the charset """
        return self.charset

    @abstractmethod
    def set_chars(self, charset):
        """ set the charset """
        pass

    def get_number(self):
        """ get the number """
        return self.number

    @abstractmethod
    def set_number(self, number):
        """ set the number """
        pass

    @abstractmethod
    def make_new(self, charset, number):
        """ return an new instance of this class """
        pass


class RejectUnlessContainsNumberChars(RejectNumberChars):
    """ Reject unless the word contains AT LEAST N instances of char C.
    
    Note:
        if number <= 0, satisfied.
        if set is set(), rejected.
        set is set() and number <= 0 should not happen at the same time.

    Attr:
        number: int N, denote the number of chars needed

        charset: set of chars, denote the set of chars allowed.
    """

    def __init__(self, charset, number):
        """ Initialize an instance
        
        Args:
            number: int N, denote the number of chars needed

            charset: set of chars, denote the set of chars allowed.
        """
        RejectNumberChars.__init__(self, 2, charset, number)

    def set_chars(self, charset):
        """ set the charset """
        self.charset = set(charset)
        # Empty set means there's no way for you to contain this char
        if charset == set():
            self.status = DependencyStatus.REJECTED

    def set_number(self, number):
        """ set the number """
        self.number = number
        # num=0 means it is auto contained
        if number <= 0:  #Satisfied
            self.status = DependencyStatus.SATISFIED

    def __repr__(self):
        """ Get string repr """
        return "Dependency: Reject Unless Contains {} instances of {}, Status: {}".format(
            self.number, sorted(self.charset),
            DependencyStatus(self.status).name)

    def make_new(self, charset, number):
        """ return an new instance of this class """
        return RejectUnlessContainsNumberChars(charset, number)


class RejectIfContainsNumberChars(RejectNumberChars):
    """ Reject if the word contains AT LEAST N instances of char C.
    
    Note:
        if number <= 0, rejected.
        if set is set(), satisfied.
        set is set() and number <= 0 should not happen at the same time.

    Attr:
        number: int N, denote the number of chars needed

        charset: set of chars, denote the set of chars allowed.
    """

    def __init__(self, charset, number):
        """ Initialize an instance
        
        Args:
            number: int N, denote the number of chars needed

            charset: set of chars, denote the set of chars allowed.
        """
        RejectNumberChars.__init__(self, 1, charset, number)

    def set_chars(self, charset):
        """ set the charset """
        self.charset = set(charset)
        #Empty set means there's no way for you to contain this char
        if charset == set():  #Satisfied
            self.status = DependencyStatus.SATISFIED

    def set_number(self, number):
        """ set the number """
        self.number = number
        #num=0 means it is auto contained
        if number <= 0:  #Rejected
            self.status = DependencyStatus.REJECTED

    def make_new(self, charset, number):
        """ return an new instance of this class """
        return RejectIfContainsNumberChars(charset, number)

    def __repr__(self):
        """ Get string repr """
        return "Dependency: Reject If Contains {} instances of {}, Status: {}".format(
            self.number, sorted(self.charset),
            DependencyStatus(self.status).name)


class RejectCharInPosition(BaseDependencyType, metaclass=ABCMeta):
    """ Abstract class that has a position N and a set of chars C.
        Implemented by other children classes.

    Note:
        this class should be used together with length boundary.
        It implies that length is at least N.

    Attr:
        dependency_type: the dependency type of this class

        position: int N, denote the position checked

        charset: set of chars, denote the set of chars allowed.
    """

    def __init__(self, dependency_type, charset, position):
        """ Initialize an instance
        
        Args:
            position: int N, denote the position checked

            charset: set of chars, denote the set of chars allowed.
        """
        BaseDependencyType.__init__(self, dependency_type)
        self.set_chars(charset)
        self.set_position(position)

    def get_chars(self):
        """ get the charset """
        return self.charset

    @abstractmethod
    def set_chars(self, charset):
        """ set the charset """
        pass

    def get_position(self):
        """ get the position """
        return self.position

    @abstractmethod
    def set_position(self, position):
        """ set the position """
        pass


class RejectUnlessCharInPosition(RejectCharInPosition):
    """ Reject unless the word has char C at position N

    Note:
        this class should be used together with length boundary.
        It implies that length is at least N, otherwise rejected.
        If charset is set(), then rejected.

    Attr:
        position: int N, denote the position checked

        charset: set of chars, denote the set of chars allowed.
    """

    def __init__(self, charset, position):
        RejectCharInPosition.__init__(self, 3, charset, position)

    def set_chars(self, charset):
        """ set the charset """
        self.charset = set(charset)
        if self.charset == set():
            self.status = DependencyStatus.REJECTED

    def set_position(self, position):
        """ set the position """
        self.position = position

    def set_to_rejected(self):
        """ set status to rejected, not recommended """
        self.status = DependencyStatus.REJECTED

    def set_to_satisfied(self):
        """ set status to rejected, not recommended """
        self.status = DependencyStatus.SATISFIED

    def __repr__(self):
        """ Get string repr """
        #return "Dependency: Reject Unless Charset {} Is In Position {}, Status: {}".format(sorted(self.charset),self.position, Status(self.status).name)
        valid_chars = set(
            x for x in self.charset if char_is_printable(x) == True)
        return "Dependency: Reject Unless Charset {} Is In Position {}, Status: {}".format(
            sorted(valid_chars), self.position,
            DependencyStatus(self.status).name)


## Reject length family
class RejectLength(BaseDependencyType, metaclass=ABCMeta):
    """ Abstract class that has a length N.
        Implemented by other children classes.

    Attr:
        dependency_type: the dependency type of this class

        length: int N, denote the number of chars needed
    """

    def __init__(self, dependency_type, length):
        """ Initialize an instance

        Args:
            dependency_type: the dependency type of this class

            length: int N, denote the number of chars needed
        """
        BaseDependencyType.__init__(self, dependency_type)
        self.set_len(length)  # Could input a single char "a" or set.

    def get_len(self):
        """ get the length N """
        return self.length

    @abstractmethod
    def set_len(self, length):
        """ set the length N """
        pass


class RejectUnlessLessThanLength(RejectLength):

    def __init__(self, length):
        """ Initialize an instance
        
        Note:
            If length < 0, then it is rejected.
            If length > max_password_length, satisfied.

        Args:
            length: int N, denote the number of chars needed
        """
        RejectLength.__init__(self, 6, length)
        self.set_len(length)

    def set_len(self, length):
        """ set the length N """
        self.length = length
        if length < 0:  # Less Than 0 then it is rejected.
            self.set_status(DependencyStatus.REJECTED)
        elif length > RUNTIME_CONFIG['max_password_length']:
            self.set_status(
                DependencyStatus.SATISFIED)  #Less than 32. satisfied
        else:
            self.set_status(DependencyStatus.ACTIVE)

    def __repr__(self):
        """ Get string repr """
        return "Dependency: Reject Unless Length <{}, Status: {}".format(
            self.length,
            DependencyStatus(self.status).name)


class RejectUnlessGreaterThanLength(RejectLength):

    def __init__(self, length):
        """ Initialize an instance
        
        Note:
            If length < 0, then it is rejected.
            If length > max_password_length, satisfied.

        Args:
            length: int N, denote the number of chars needed
        """
        RejectLength.__init__(self, 7, length)
        self.set_len(length)

    def set_len(self, length):
        """ set the length N """
        self.length = length
        if length <= -1:
            self.set_status(
                DependencyStatus.SATISFIED
            )  #Greater Than -1 then it is satisfied. (0 is possible for HC)
        elif length >= RUNTIME_CONFIG[
                'max_password_length']:  # Greater than max_password_length.
            self.set_status(DependencyStatus.REJECTED)
        else:
            self.set_status(DependencyStatus.ACTIVE)

    def __repr__(self):
        """ Get string repr """
        return "Dependency: Reject Unless Length >{}, Status: {}".format(
            self.length,
            DependencyStatus(self.status).name)

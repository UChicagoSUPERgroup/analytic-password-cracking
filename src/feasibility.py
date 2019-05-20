""" Some class defs for rule invertibility"""

from enum import Enum


class Invertibility(Enum):
    """ An enum that represents the invertibility of a transformation

    Attr:
        INVERTIBLE: the transformation is fully invertible
        UNINVERTIBLEOPTIMIZATBLE: the transformation is uninvertible, but can be optimized for performance
        UNINVERTIBLE: the transformation is uninvertible
    """
    INVERTIBLE = 10,
    UNINVERTIBLEOPTIMIZATBLE = 5,
    UNINVERTIBLE = 0,

    def __gt__(self, other):
        # compare two invertibility.

        if type(other) != Invertibility:
            raise Exception("Error")

        return self.value > other.value


class SpecialFeasibleType(Enum):
    """ denote some special feasibility in invertible rules"""
    NOT_SPECIAL = 0
    SPECIAL_START_WITH_SHIFT = 1
    SPECIAL_MEMORY = 2


class FeasibleType():
    """ feasibility type 

    Attr:
        invertibility: if the rule is invertible
        countability: if the rule is countable
        is_special: is this rule special case, only used when the rule is invertible
        special_idx: if is special, where the special transformation is in the rule
    """

    def __init__(self, invertibility, countability):
        self.invertibility = invertibility
        self.countability = countability
        self.is_special = SpecialFeasibleType.NOT_SPECIAL
        self.special_idx = None

    def is_invertible(self):
        """ is this rule invertible """
        return self.invertibility == Invertibility.INVERTIBLE

    def is_uninvertible(self):
        """ is this rule uninvertible """
        return self.invertibility == Invertibility.UNINVERTIBLE

    def is_optimizable(self):
        """ is this rule optimizable """
        return self.invertibility == Invertibility.UNINVERTIBLEOPTIMIZATBLE

    def is_countable(self):
        """ is this rule countable """
        return self.countability == True

    def set_to_optimizable(self):
        """ set to optimizable """
        self.invertibility = Invertibility.UNINVERTIBLEOPTIMIZATBLE
        self.is_special = SpecialFeasibleType.NOT_SPECIAL

    def set_to_uninvertible(self):
        """ set rule to uninvertible """
        self.invertibility = Invertibility.UNINVERTIBLE
        self.is_special = SpecialFeasibleType.NOT_SPECIAL

    def set_to_special_memory(self, special_idx):
        """ set the rule to special type: memory """
        self.invertibility = Invertibility.INVERTIBLE
        self.is_special = SpecialFeasibleType.SPECIAL_MEMORY
        self.special_idx = special_idx

    def __repr__(self):
        if self.is_special == SpecialFeasibleType.NOT_SPECIAL:
            return "{} Countability:{}".format(self.invertibility,
                                               self.countability)
        else:
            return "{} Countability:{}".format(self.is_special,
                                               self.countability)

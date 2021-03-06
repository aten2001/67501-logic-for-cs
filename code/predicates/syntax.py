# (c) This file is part of the course
# Mathematical Logic through Programming
# by Gonczarowski and Nisan.
# File name: predicates/syntax.py

"""Syntactic handling of first-order formulas and terms."""

from __future__ import annotations

import re
from typing import AbstractSet, Mapping, Optional, Sequence, Set, Tuple, Union

from logic_utils import fresh_variable_name_generator, frozen

from propositions.syntax import Formula as PropositionalFormula, \
    is_variable as is_propositional_variable

UNDERSCORE = '_'

R_BRACK = ')'

COMMA = ','

L_BRACK = '('

PREFIX_ERR_MSG = 'Not a valid prefix of a term'


class ForbiddenVariableError(Exception):
    """Raised by `Term.substitute` and `Formula.substitute` when a substituted
    term contains a variable name that is forbidden in that context."""

    def __init__(self, variable_name: str) -> None:
        """Initializes a `ForbiddenVariableError` from its offending variable
        name.

        Parameters:
            variable_name: variable name that is forbidden in the context in
                which a term containing it was to be substituted.
        """
        assert is_variable(variable_name)
        self.variable_name = variable_name


def is_constant(s: str) -> bool:
    """Checks if the given string is a constant name.

    Parameters:
        s: string to check.

    Returns:
        ``True`` if the given string is a constant name, ``False`` otherwise.
    """
    return (((s[0] >= '0' and s[0] <= '9') or (s[0] >= 'a' and s[0] <= 'd'))
            and s.isalnum()) or s == '_'


def is_variable(s: str) -> bool:
    """Checks if the given string is a variable name.

    Parameters:
        s: string to check.

    Returns:
        ``True`` if the given string is a variable name, ``False`` otherwise.
    """
    return s[0] >= 'u' and s[0] <= 'z' and s.isalnum()


def is_function(s: str) -> bool:
    """Checks if the given string is a function name.

    Parameters:
        s: string to check.

    Returns:
        ``True`` if the given string is a function name, ``False`` otherwise.
    """
    return s[0] >= 'f' and s[0] <= 't' and s.isalnum()


@frozen
class Term:
    """An immutable first-order term in tree representation, composed from
    variable names and constant names, and function names applied to them.

    Attributes:
        root (`str`): the constant name, variable name, or function name at the
            root of the term tree.
        arguments (`~typing.Optional`\\[`~typing.Tuple`\\[`Term`, ...]]): the
            arguments to the root, if the root is a function name.
    """
    root: str
    arguments: Optional[Tuple[Term, ...]]

    def __init__(self, root: str,
                 arguments: Optional[Sequence[Term]] = None) -> None:
        """Initializes a `Term` from its root and root arguments.

        Parameters:
            root: the root for the formula tree.
            arguments: the arguments to the root, if the root is a function
                name.
        """
        if is_constant(root) or is_variable(root):
            assert arguments is None
            self.root = root
        else:
            assert is_function(root)
            assert arguments is not None
            self.root = root
            self.arguments = tuple(arguments)
            assert len(self.arguments) > 0

    def __repr__(self) -> str:
        """Computes the string representation of the current term.

        Returns:
            The standard string representation of the current term.
        """
        # Task 7.1
        if is_constant(self.root) or is_variable(self.root):
            return self.root
        else:
            repr = f'{self.root}({str(self.arguments[0])}'
            for arg in self.arguments[1:]:
                repr += f',{str(arg)}'
            return f'{repr})'

    def __eq__(self, other: object) -> bool:
        """Compares the current term with the given one.

        Parameters:
            other: object to compare to.

        Returns:
            ``True`` if the given object is a `Term` object that equals the
            current term, ``False`` otherwise.
        """
        return isinstance(other, Term) and str(self) == str(other)

    def __ne__(self, other: object) -> bool:
        """Compares the current term with the given one.

        Parameters:
            other: object to compare to.

        Returns:
            ``True`` if the given object is not a `Term` object or does not
            equal the current term, ``False`` otherwise.
        """
        return not self == other

    def __hash__(self) -> int:
        return hash(str(self))

    @staticmethod
    def parse_prefix(s: str) -> Tuple[Term, str]:
        """Parses a prefix of the given string into a term.

        Parameters:
            s: string to parse, which has a prefix that is a valid
                representation of a term.

        Returns:
            A pair of the parsed term and the unparsed suffix of the string. If
            the given string has as a prefix a constant name (e.g., ``'c12'``)
            or a variable name (e.g., ``'x12'``), then the parsed prefix will be
            that entire name (and not just a part of it, such as ``'x1'``).
        """
        # Task 7.3.1

        # Base case
        if s == '':
            return None, PREFIX_ERR_MSG
        elif is_constant(s) or is_variable(s):
            return Term(s), ''
        elif s[0] == UNDERSCORE:
            return Term(UNDERSCORE), s[1:]
        elif 'f' <= s[0] <= 't':  # prefix is function
            root, args, start_marker = '', [], 0
            # finding the root of the function
            for i, c in enumerate(s):
                if c == L_BRACK:
                    root, start_marker = s[0:i], i + 1
                    break

            arg, remainder = Term.parse_prefix(s[start_marker:])
            while remainder[0] == COMMA:
                args.append(arg)
                arg, remainder = Term.parse_prefix(remainder[1:])
            args.append(arg)
            return Term(root, args), remainder[1:]
        else:
            valid_prefix_regex = '[a-zA-Z0-9]*'
            p = re.compile(valid_prefix_regex)
            result = p.search(s)
            # Means we found something that matches the pattern:
            if result != None:
                prefix = result.group(0)
                return Term(prefix), s[len(prefix):]

    @staticmethod
    def parse(s: str) -> Term:
        """Parses the given valid string representation into a term.

        Parameters:
            s: string to parse.

        Returns:
            A term whose standard string representation is the given string.
        """

        # Task 7.3.2
        term, remainder = Term.parse_prefix(s)
        return term

    def constants(self) -> Set[str]:
        """Finds all constant names in the current term.

        Returns:
            A set of all constant names used in the current term.
        """
        # Task 7.5.1
        if is_constant(self.root):
            return {self.root}
        elif is_variable(self.root):
            return set()
        elif is_function(self.root):
            constants = set()
            for term in self.arguments:
                constants = constants.union(term.constants())
            return constants

    def variables(self) -> Set[str]:
        """Finds all variable names in the current term.

        Returns:
            A set of all variable names used in the current term.
        """

        # Task 7.5.2
        if is_variable(self.root):
            return {self.root}
        elif is_constant(self.root):
            return set()
        elif is_function(self.root):
            variables = set()
            for term in self.arguments:
                variables = variables.union(term.variables())
            return variables

    def functions(self) -> Set[Tuple[str, int]]:
        """Finds all function names in the current term, along with their
        arities.

        Returns:
            A set of pairs of function name and arity (number of arguments) for
            all function names used in the current term.
        """

        # Task 7.5.3
        if is_variable(self.root) or is_constant(self.root):
            return set()
        elif is_function(self.root):
            functions = {(self.root, len(self.arguments))}
            for term in self.arguments:
                functions = functions.union(term.functions())
            return functions

    def substitute(self, substitution_map: Mapping[str, Term],
                   forbidden_variables: AbstractSet[str] = frozenset()) -> Term:
        """Substitutes in the current term, each constant name `name` or
        variable name `name` that is a key in `substitution_map` with the term
        `substitution_map[name]`.

        Parameters:
            substitution_map: mapping defining the substitutions to be
                performed.
            forbidden_variables: variables not allowed in substitution terms.

        Returns:
            The term resulting from performing all substitutions. Only
            constant names and variable names originating in the current term
            are substituted (i.e., those originating in one of the specified
            substitutions are not subjected to additional substitutions).

        Raises:
            ForbiddenVariableError: If a term that is used in the requested
                substitution contains a variable from `forbidden_variables`.

        Examples:
            >>> Term.parse('f(x,c)').substitute(
            ...     {'c': Term.parse('plus(d,x)'), 'x': Term.parse('c')}, {'y'})
            f(c,plus(d,x))
            >>> Term.parse('f(x,c)').substitute(
            ...     {'c': Term.parse('plus(d,y)')}, {'y'})
            Traceback (most recent call last):
              ...
            predicates.syntax.ForbiddenVariableError: y
        """
        for element_name in substitution_map:
            assert is_constant(element_name) or is_variable(element_name)
        for variable in forbidden_variables:
            assert is_variable(variable)

        # Task 9.1

        if is_constant(self.root) or is_variable(self.root):
            if self.root in substitution_map.keys():
                sub_term = substitution_map[self.root]
                bad_vars = sub_term.variables().intersection(forbidden_variables)
                if len(bad_vars) > 0:
                    raise ForbiddenVariableError(list(bad_vars)[0])
                else:
                    return sub_term
            else:
                return self
        if is_function(self.root):
            sub_args = []
            for arg in self.arguments:
                sub_args.append(arg.substitute(substitution_map, forbidden_variables))
            sub_func = Term(self.root, sub_args)
            return sub_func


def is_equality(s: str) -> bool:
    """Checks if the given string is the equality relation.

    Parameters:
        s: string to check.

    Returns:
        ``True`` if the given string is the equality relation, ``False``
        otherwise.
    """
    return s == '='


def is_relation(s: str) -> bool:
    """Checks if the given string is a relation name.

    Parameters:
        s: string to check.

    Returns:
        ``True`` if the given string is a relation name, ``False`` otherwise.
    """
    return s[0] >= 'F' and s[0] <= 'T' and s.isalnum()


def is_unary(s: str) -> bool:
    """Checks if the given string is a unary operator.

    Parameters:
        s: string to check.

    Returns:
        ``True`` if the given string is a unary operator, ``False`` otherwise.
    """
    return s == '~'


def is_binary(s: str) -> bool:
    """Checks if the given string is a binary operator.

    Parameters:
        s: string to check.

    Returns:
        ``True`` if the given string is a binary operator, ``False`` otherwise.
    """
    return s == '&' or s == '|' or s == '->'


def is_quantifier(s: str) -> bool:
    """Checks if the given string is a quantifier.

    Parameters:
        s: string to check.

    Returns:
        ``True`` if the given string is a quantifier, ``False`` otherwise.
    """
    return s == 'A' or s == 'E'


@frozen
class Formula:
    """An immutable first-order formula in tree representation, composed from
    relation names applied to first-order terms, and operators and
    quantifications applied to them.

    Attributes:
        root (`str`): the relation name, equality relation, operator, or
            quantifier at the root of the formula tree.
        arguments (`~typing.Optional`\\[`~typing.Tuple`\\[`Term`, ...]]): the
            arguments to the root, if the root is a relation name or the
            equality relation.
        first (`~typing.Optional`\\[`Formula`]): the first operand to the root,
            if the root is a unary or binary operator.
        second (`~typing.Optional`\\[`Formula`]): the second
            operand to the root, if the root is a binary operator.
        variable (`~typing.Optional`\\[`str`]): the variable name quantified by
            the root, if the root is a quantification.
        predicate (`~typing.Optional`\\[`Formula`]): the predicate quantified by
            the root, if the root is a quantification.
    """
    root: str
    arguments: Optional[Tuple[Term, ...]]
    first: Optional[Formula]
    second: Optional[Formula]
    variable: Optional[str]
    predicate: Optional[Formula]

    def __init__(self, root: str,
                 arguments_or_first_or_variable: Union[Sequence[Term],
                                                       Formula, str],
                 second_or_predicate: Optional[Formula] = None) -> None:
        """Initializes a `Formula` from its root and root arguments, root
        operands, or root quantified variable and predicate.

        Parameters:
            root: the root for the formula tree.
            arguments_or_first_or_variable: the arguments to the the root, if
                the root is a relation name or the equality relation; the first
                operand to the root, if the root is a unary or binary operator;
                the variable name quantified by the root, if the root is a
                quantification.
            second_or_predicate: the second operand to the root, if the root is
                a binary operator; the predicate quantified by the root, if the
                root is a quantification.
        """
        if is_equality(root) or is_relation(root):
            # Populate self.root and self.arguments
            assert second_or_predicate is None
            assert isinstance(arguments_or_first_or_variable, Sequence) and \
                   not isinstance(arguments_or_first_or_variable, str)
            self.root, self.arguments = \
                root, tuple(arguments_or_first_or_variable)
            if is_equality(root):
                assert len(self.arguments) == 2
        elif is_unary(root):
            # Populate self.first
            assert isinstance(arguments_or_first_or_variable, Formula) and \
                   second_or_predicate is None
            self.root, self.first = root, arguments_or_first_or_variable
        elif is_binary(root):
            # Populate self.first and self.second
            assert isinstance(arguments_or_first_or_variable, Formula) and \
                   second_or_predicate is not None
            self.root, self.first, self.second = \
                root, arguments_or_first_or_variable, second_or_predicate
        else:
            assert is_quantifier(root)
            # Populate self.variable and self.predicate
            assert isinstance(arguments_or_first_or_variable, str) and \
                   is_variable(arguments_or_first_or_variable) and \
                   second_or_predicate is not None
            self.root, self.variable, self.predicate = \
                root, arguments_or_first_or_variable, second_or_predicate

    def __repr__(self) -> str:
        """Computes the string representation of the current formula.

        Returns:
            The standard string representation of the current formula.
        """
        # Task 7.2
        if is_constant(self.root) or is_variable(self.root):
            return self.root
        elif is_unary(self.root):
            return f'~{str(self.first)}'
        elif is_binary(self.root):
            return f'({str(self.first)}{str(self.root)}{str(self.second)})'
        elif is_equality(self.root):
            return f'{str(self.arguments[0])}={str(self.arguments[1])}'
        elif is_relation(self.root):
            if self.arguments:
                repr = f'{self.root}({str(self.arguments[0])}'
                if self.arguments:
                    for arg in self.arguments[1:]:
                        repr += f',{str(arg)}'
                    return f'{repr})'
            else:
                return f'{self.root}()'
        elif is_quantifier(self.root):
            return f'{str(self.root)}{str(self.variable)}[{str(self.predicate)}]'

    def __eq__(self, other: object) -> bool:
        """Compares the current formula with the given one.

        Parameters:
            other: object to compare to.

        Returns:
            ``True`` if the given object is a `Formula` object that equals the
            current formula, ``False`` otherwise.
        """
        return isinstance(other, Formula) and str(self) == str(other)

    def __ne__(self, other: object) -> bool:
        """Compares the current formula with the given one.

        Parameters:
            other: object to compare to.

        Returns:
            ``True`` if the given object is not a `Formula` object or does not
            equal the current formula, ``False`` otherwise.
        """
        return not self == other

    def __hash__(self) -> int:
        return hash(str(self))

    @staticmethod
    def parse_prefix(s: str) -> Tuple[Formula, str]:
        """Parses a prefix of the given string into a formula.

        Parameters:
            s: string to parse, which has a prefix that is a valid
                representation of a formula.

        Returns:
            A pair of the parsed formula and the unparsed suffix of the string.
            If the given string has as a prefix a term followed by an equality
            followed by a constant name (e.g., ``'c12'``) or by a variable name
            (e.g., ``'x12'``), then the parsed prefix will include that entire
            name (and not just a part of it, such as ``'x1'``).
        """

        # Task 7.4.1
        if is_quantifier(s[0]):
            quantifier = s[0]
            s = s[1:]
            valid_prefix_regex = '[a-zA-Z0-9]*'
            p = re.compile(valid_prefix_regex)
            result = p.search(s)
            # Means we found something that matches the pattern:
            variable = result.group(0)
            predicate, remainder = Formula.parse_prefix(s[len(variable) + 1:])
            remainder = remainder[1:]
            return Formula(quantifier, variable, predicate), remainder

        # If the formula is of a binary operator, then it has to start with a '(':
        elif s[0] == L_BRACK:
            # ff and ff2 are the left and right hand sides of the formula, respectively
            l_formula, remainder = Formula.parse_prefix(s[1:])
            if is_binary(remainder[0]):
                end_len = 1
            elif is_binary(remainder[0:2]):
                end_len = 2
            root = remainder[:end_len]
            r_formula, remainder = Formula.parse_prefix(remainder[end_len:])
            remainder = remainder[1:]
            return Formula(root, l_formula, r_formula), remainder

        # If the formula is of a unary operator, then we only need to operate on the part that comes after the '~':
        elif is_unary(s[0]):
            formula, remainder = Formula.parse_prefix(s[1:])
            return Formula(s[0], formula), remainder

        # If the formula starts with 'F'...'T', then it's a relation (which is like the case of a function in "Term"),
        # we'll   ---<==3, respectively
        elif 'F' <= s[0] <= 'T':  # prefix is function
            root, args, start_marker = '', [], 0
            # finding the root of the function
            for i, c in enumerate(s):
                if c == L_BRACK:
                    root, start_marker = s[0:i], i + 1
                    break
            if s[i + 1] == R_BRACK:
                return Formula(root, []), s[i + 2:]
            arg, remainder = Term.parse_prefix(s[start_marker:])
            while remainder[0] == COMMA:
                args.append(arg)
                arg, remainder = Term.parse_prefix(remainder[1:])
            args.append(arg)
            return Formula(root, args), remainder[1:]

        else:
            l_formula, remainder = Term.parse_prefix(s)
            root = remainder[0]
            r_formula, remainder = Term.parse_prefix(remainder[1:])
            return Formula(root, [l_formula, r_formula]), remainder

    @staticmethod
    def parse(s: str) -> Formula:
        """Parses the given valid string representation into a formula.

        Parameters:
            s: string to parse.

        Returns:
            A formula whose standard string representation is the given string.
        """
        formula, remainder = Formula.parse_prefix(s)
        return formula

    # Task 7.4.2

    def constants(self) -> Set[str]:
        """Finds all constant names in the current formula.

        Returns:
            A set of all constant names used in the current formula.
        """

        # Task 7.6.1
        if is_equality(self.root):
            return self.arguments[0].constants().union(self.arguments[1].constants())
        elif is_relation(self.root):
            constants = set()
            for term in self.arguments:
                constants = constants.union(term.constants())
            return constants
        elif is_unary(self.root):
            return self.first.constants()
        elif is_binary(self.root):
            return self.first.constants().union(self.second.constants())
        elif is_quantifier(self.root):
            return self.predicate.constants()

    def variables(self) -> Set[str]:
        """Finds all variable names in the current formula.

        Returns:
            A set of all variable names used in the current formula.
        """

        # Task 7.6.2
        if is_equality(self.root):
            return self.arguments[0].variables().union(self.arguments[1].variables())
        elif is_relation(self.root):
            variables = set()
            for term in self.arguments:
                variables = variables.union(term.variables())
            return variables
        elif is_unary(self.root):
            return self.first.variables()
        elif is_binary(self.root):
            return self.first.variables().union(self.second.variables())
        elif is_quantifier(self.root):
            return self.predicate.variables().union({self.variable})

    def free_variables(self) -> Set[str]:
        """Finds all variable names that are free in the current formula.

        Returns:
            A set of all variable names used in the current formula not only
            within a scope of a quantification on those variable names.
        """

        # Task 7.6.3
        if is_equality(self.root):
            return self.arguments[0].variables().union(self.arguments[1].variables())
        elif is_relation(self.root):
            free_variables = set()
            for term in self.arguments:
                free_variables = free_variables.union(term.variables())
            return free_variables
        elif is_unary(self.root):
            return self.first.free_variables()
        elif is_binary(self.root):
            return self.first.free_variables().union(self.second.free_variables())
        elif is_quantifier(self.root):
            return self.predicate.free_variables().difference({self.variable})

    def functions(self) -> Set[Tuple[str, int]]:
        """Finds all function names in the current formula, along with their
        arities.

        Returns:
            A set of pairs of function name and arity (number of arguments) for
            all function names used in the current formula.
        """

        # Task 7.6.4
        if is_equality(self.root):
            return self.arguments[0].functions().union(self.arguments[1].functions())
        elif is_relation(self.root):
            functions = set()
            for term in self.arguments:
                functions = functions.union(term.functions())
            return functions
        elif is_unary(self.root):
            return self.first.functions()
        elif is_binary(self.root):
            return self.first.functions().union(self.second.functions())
        elif is_quantifier(self.root):
            return self.predicate.functions()

    def relations(self) -> Set[Tuple[str, int]]:
        """Finds all relation names in the current formula, along with their
        arities.

        Returns:
            A set of pairs of relation name and arity (number of arguments) for
            all relation names used in the current formula.
        """

        # Task 7.6.5
        if is_equality(self.root):
            return set()
        elif is_relation(self.root):
            return {(self.root, len(self.arguments))}
        elif is_unary(self.root):
            return self.first.relations()
        elif is_binary(self.root):
            return self.first.relations().union(self.second.relations())
        elif is_quantifier(self.root):
            return self.predicate.relations()

    def substitute(self, substitution_map: Mapping[str, Term],
                   forbidden_variables: AbstractSet[str] = frozenset()) -> \
            Formula:
        """Substitutes in the current formula, each constant name `name` or free
        occurrence of variable name `name` that is a key in `substitution_map`
        with the term `substitution_map[name]`.

        Parameters:
            substitution_map: mapping defining the substitutions to be
                performed.
            forbidden_variables: variables not allowed in substitution terms.

        Returns:
            The formula resulting from performing all substitutions. Only
            constant names and variable names originating in the current formula
            are substituted (i.e., those originating in one of the specified
            substitutions are not subjected to additional substitutions).

        Raises:
            ForbiddenVariableError: If a term that is used in the requested
                substitution contains a variable from `forbidden_variables`
                or a variable occurrence that becomes bound when that term is
                substituted into the current formula.

        Examples:
            >>> Formula.parse('Ay[x=c]').substitute(
            ...     {'c': Term.parse('plus(d,x)'), 'x': Term.parse('c')}, {'z'})
            Ay[c=plus(d,x)]
            >>> Formula.parse('Ay[x=c]').substitute(
            ...     {'c': Term.parse('plus(d,z)')}, {'z'})
            Traceback (most recent call last):
              ...
            predicates.syntax.ForbiddenVariableError: z
            >>> Formula.parse('Ay[x=c]').substitute(
            ...     {'c': Term.parse('plus(d,y)')})
            Traceback (most recent call last):
              ...
            predicates.syntax.ForbiddenVariableError: y
        """
        for element_name in substitution_map:
            assert is_constant(element_name) or is_variable(element_name)
        for variable in forbidden_variables:
            assert is_variable(variable)

        # Task 9.2
        if is_equality(self.root):
            args = [self.arguments[i].substitute(substitution_map, forbidden_variables) for i in [0, 1]]
            return Formula(self.root, args)
        elif is_unary(self.root):
            sub_first = self.first.substitute(substitution_map, forbidden_variables)
            return Formula(self.root, sub_first)
        elif is_binary(self.root):
            sub_first, sub_second = [arg.substitute(substitution_map, forbidden_variables) for arg in
                                     [self.first, self.second]]
            return Formula(self.root, sub_first, sub_second)
        elif is_relation(self.root):
            sub_args = []
            for arg in self.arguments:
                sub_args.append(arg.substitute(substitution_map, forbidden_variables))
            return Formula(self.root, sub_args)
        elif is_quantifier(self.root):
            new_sub_map = dict(substitution_map)
            if self.variable in substitution_map.keys():
                del new_sub_map[self.variable]
            new_forbidden = set(forbidden_variables).union({self.variable})
            sub_predicate = self.predicate.substitute(new_sub_map, new_forbidden)
            return Formula(self.root, self.variable, sub_predicate)

    def propositional_skeleton(self) -> Tuple[PropositionalFormula,
                                              Mapping[str, Formula]]:
        """Computes a propositional skeleton of the current formula.

        Returns:
            A pair. The first element of the pair is a propositional formula
            obtained from the current formula by substituting every (outermost)
            subformula that has a relation or quantifier at its root with an
            atomic propositional formula, consistently such that multiple equal
            such (outermost) subformulas are substituted with the same atomic
            propositional formula. The atomic propositional formulas used for
            substitution are obtained, from left to right, by calling
            `next`\ ``(``\ `~logic_utils.fresh_variable_name_generator`\ ``)``.
            The second element of the pair is a map from each atomic
            propositional formula to the subformula for which it was
            substituted.
        """

        # Task 9.6
        return self._skeleton_helper(dict())

    def _skeleton_helper(self, mapping):
        if is_constant(self.root) or is_variable(self.root):
            return self, mapping
        elif is_relation(self.root) or is_equality(self.root) or is_quantifier(self.root):
            if self in mapping.values():
                for key, val in mapping.items():
                    if val == self:
                        var_name = key
            else:
                var_name = next(fresh_variable_name_generator)
                mapping[var_name] = self
            return PropositionalFormula(var_name), mapping
        elif is_unary(self.root):
            sub_formula, sub_mapping = self.first._skeleton_helper(mapping)
            return PropositionalFormula(self.root, sub_formula), mapping
        elif is_binary(self.root):
            first_sub_formula, first_sub_mapping = self.first._skeleton_helper(mapping)
            second_sub_formula, second_sub_mapping = self.second._skeleton_helper(mapping)
            return PropositionalFormula(self.root, first_sub_formula, second_sub_formula), mapping

    @staticmethod
    def from_propositional_skeleton(skeleton: PropositionalFormula,
                                    substitution_map: Mapping[str, Formula]) -> \
            Formula:
        """Computes a first-order formula from a propositional skeleton and a
        substitution map.

        Arguments:
            skeleton: propositional skeleton for the formula to compute.
            substitution_map: a map from each atomic propositional subformula
                of the given skeleton to a first-order formula.

        Returns:
            A first-order formula obtained from the given propositional skeleton
            by substituting each atomic propositional subformula with the formula
            mapped to it by the given map.
        """
        for key in substitution_map:
            assert is_propositional_variable(key)
            # Task 9.10
            root = skeleton.root
            if is_constant(root) or is_variable(root):
                if root in substitution_map.keys():
                    return substitution_map[root]
                else:
                    return Formula(root)
            elif is_unary(root):
                return Formula(root, Formula.from_propositional_skeleton(skeleton.first, substitution_map))
            elif is_binary(root):
                l_arg = Formula.from_propositional_skeleton(skeleton.first, substitution_map)
                r_arg = Formula.from_propositional_skeleton(skeleton.second, substitution_map)
                return Formula(root, l_arg, r_arg)

# (c) This file is part of the course
# Mathematical Logic through Programming
# by Gonczarowski and Nisan.
# File name: predicates/prover.py

from typing import AbstractSet, Collection, FrozenSet, List, Mapping, \
    Sequence, Tuple, Union

from logic_utils import fresh_variable_name_generator

from predicates.syntax import *
from predicates.proofs import *


class Prover:
    """A class for gradually creating a first-order logic proof from given
    assumptions as well as from the six axioms (`AXIOMS`) Universal
    Instantiation (`UI`), Existential Introduction (`EI`), Universal
    Simplification (`US`), Existential Simplification (`ES`), Reflexivity
    (`RX`), and Meaning of Equality (`ME`).

    Attributes:
        _assumptions (`~typing.FrozenSet`\\[`~predicates.proofs.Schema`]): the
            assumptions/axioms of the proof being created, which include
            `AXIOMS`.
        _lines (`~typing.List`\\[`~predicates.proofs.Proof.Line`]): the current
            lines of the proof being created.
        _print_as_proof_forms (`bool`): flag specifying whether the proof being
            created is being printed in real time as it forms.
    """
    _assumptions: FrozenSet[Schema]
    _lines: List[Proof.Line]
    _print_as_proof_forms: bool

    #: Axiom schema of universal instantiation
    UI = Schema(Formula.parse('(Ax[R(x)]->R(c))'), {'R', 'x', 'c'})
    #: Axiom schema of existential introduction
    EI = Schema(Formula.parse('(R(c)->Ex[R(x)])'), {'R', 'x', 'c'})
    #: Axiom schema of universal simplification
    US = Schema(Formula.parse('(Ax[(Q()->R(x))]->(Q()->Ax[R(x)]))'),
                {'Q', 'R', 'x'})
    #: Axiom schema of existential simplification
    ES = Schema(Formula.parse('((Ax[(R(x)->Q())]&Ex[R(x)])->Q())'),
                {'Q', 'R', 'x'})
    #: Axiom schema of reflexivity
    RX = Schema(Formula.parse('c=c'), {'c'})
    #: Axiom schema of meaning of equality
    ME = Schema(Formula.parse('(c=d->(R(c)->R(d)))'), {'R', 'c', 'd'})
    #: Axiomatic system for first-order predicate logic
    AXIOMS = frozenset({UI, EI, US, ES, RX, ME})

    def __init__(self, assumptions: Collection[Union[Schema, Formula, str]],
                 print_as_proof_forms: bool = False) -> None:
        """Initializes a `Prover` from its assumptions/additional axioms. The
        proof created by the prover initially has no lines.

        Parameters:
            assumptions: the assumptions/axioms beyond `AXIOMS` for the proof
                to be created, each specified as either a schema, a formula that
                constitutes the unique instance of the assumption, or the string
                representation of the unique instance of the assumption.
            print_as_proof_forms: flag specifying whether the proof is to be
                printed in real time as it forms.
        """
        self._assumptions = \
            Prover.AXIOMS.union(
                {assumption if isinstance(assumption, Schema)
                 else Schema(assumption) if isinstance(assumption, Formula)
                else Schema(Formula.parse(assumption))
                 for assumption in assumptions})
        self._lines = []
        self._print_as_proof_forms = print_as_proof_forms
        if self._print_as_proof_forms:
            print('Proving from assumptions/axioms:\n'
                  '  AXIOMS')
            for assumption in self._assumptions - Prover.AXIOMS:
                print('  ' + str(assumption))
            print('Lines:')

    def qed(self) -> Proof:
        """Concludes the proof created by the current prover.

        Returns:
            A valid proof, from the assumptions of the current prover as well as
            `AXIOMS`', of the formula justified by the last line appended to the
            current prover.
        """
        conclusion = self._lines[-1].formula
        if self._print_as_proof_forms:
            print('Conclusion:', str(conclusion) + '. QED\n')
        return Proof(self._assumptions, conclusion, self._lines)

    def _add_line(self, line: Proof.Line) -> int:
        """Appends to the proof being created by the current prover the given
        validly justified line.

        Parameters:
            line: a proof line that that is validly justified when appended to
                the lines of the proof being created by the current prover.

        Returns:
            The line number of the appended line in the proof being created by
            the current prover.
        """
        line_number = len(self._lines)
        self._lines.append(line)
        assert line.is_valid(self._assumptions, self._lines, line_number)
        if self._print_as_proof_forms:
            print(('%3d) ' % line_number) + str(line.formula))
        return line_number

    def add_instantiated_assumption(self, instance: Union[Formula, str],
                                    assumption: Schema,
                                    instantiation_map: InstantiationMap) -> \
            int:
        """Appends to the proof being created by the current prover a line that
        validly justifies the given instance of the given assumptions/axioms of
        the current prover.

        Parameters:
            instance: instance to be appended, specified as either a formula or
                its string representation.
            assumption: assumption/axiom of the current prover that instantiates
                the given instance.
            instantiation_map: map instantiating the given instance from the
                given assumption/axiom. Each value of this map may also be given
                as a string representation (instead of a term or a formula).

        Returns:
            The line number of the newly appended line that justifies the given
            instance in the proof being created by the current prover.
        """
        if isinstance(instance, str):
            instance = Formula.parse(instance)
        instantiation_map = dict(instantiation_map)
        for key in instantiation_map:
            value = instantiation_map[key]
            if is_variable(key):
                assert is_variable(value)
            elif is_constant(key):
                if isinstance(value, str):
                    instantiation_map[key] = Term.parse(value)
                else:
                    assert isinstance(value, Term)
            else:
                assert is_relation(key)
                if isinstance(value, str):
                    instantiation_map[key] = Formula.parse(value)
                else:
                    assert isinstance(value, Formula)
        return self._add_line(Proof.AssumptionLine(instance, assumption,
                                                   instantiation_map))

    def add_assumption(self, unique_instance: Union[Formula, str]) -> int:
        """Appends to the proof being created by the current prover a line that
        validly justifies the unique instance of one of the assumptions/axioms
        of the current prover.

        Parameters:
            unique_instance: unique instance of one of the assumptions/axioms
                of the current prover, to be appended, specified as either a
                formula or its string representation.

        Returns:
            The line number of the newly appended line that justifies the given
            instance in the proof being created by the current prover.
        """
        if isinstance(unique_instance, str):
            unique_instance = Formula.parse(unique_instance)
        return self.add_instantiated_assumption(unique_instance,
                                                Schema(unique_instance), {})

    def add_tautology(self, tautology: Union[Formula, str]) -> int:
        """Appends to the proof being created by the current prover a line that
        validly justifies the given tautology.

        Parameters:
            tautology: tautology to be appended, specified as either a formula
                or its string representation.

        Returns:
            The line number of the newly appended line that justifies the given
            tautology in the proof being created by the current prover.
        """
        if isinstance(tautology, str):
            tautology = Formula.parse(tautology)
        return self._add_line(Proof.TautologyLine(tautology))

    def add_mp(self, consequent: Union[Formula, str],
               antecedent_line_number: int, conditional_line_number: int) -> \
            int:
        """Appends to the proof being created by the current prover a line that
        validly justifies the given consequent of an MP inference from the
        specified already existing lines of the proof.

        Parameters:
            consequent: consequent of MP inference to be appended, specified as
                either a formula or its string representation.
            antecedent_line_number: line number in the proof of the antecedent
                of the MP inference that derives the given formula.
            conditional_line_number: line number in the proof of the conditional
                of the MP inference that derives the given formula.

        Returns:
            The line number of the newly appended line that justifies the given
            formula in the proof being created by the current prover.
        """
        if isinstance(consequent, str):
            consequent = Formula.parse(consequent)
        return self._add_line(Proof.MPLine(consequent, antecedent_line_number,
                                           conditional_line_number))

    def add_ug(self, quantified: Union[Formula, str],
               unquantified_line_number: int) -> int:
        """Appends to the proof being created by the current prover a line that
        validly justifies the given universally quantified formula, whose
        predicate is the specified already existing line of the proof.

        Parameters:
            quantified: universally quantified formula to be appended, specified
                as either a formula or its string representation.
            unquantified_line_number: line number in the proof of the predicate
                of the given quantified formula.

        Returns:
            The line number of the newly appended line that justifies the given
            formula in the proof being created by the current prover.
        """
        if isinstance(quantified, str):
            quantified = Formula.parse(quantified)
        return self._add_line(Proof.UGLine(quantified,
                                           unquantified_line_number))

    def add_proof(self, conclusion: Union[Formula, str], proof: Proof) -> int:
        """Appends to the proof being created by the current prover a validly
        justified inlined version of the given proof of the given conclusion,
        the last line of which validly justifies the given formula.

        Parameters:
            conclusion: conclusion of the sequence of lines to be appended,
                specified as either a formula or its string representation.
            proof: valid proof of the given formula from a subset of the
                assumptions/axioms of the current prover.

        Returns:
            The line number of the newly appended line that justifies the given
            formula in the proof being created by the current prover.
        """
        if isinstance(conclusion, str):
            conclusion = Formula.parse(conclusion)
        assert proof.conclusion == conclusion
        assert proof.assumptions.issubset(self._assumptions)
        line_shift = len(self._lines)
        for line in proof.lines:
            if type(line) in {Proof.AssumptionLine, Proof.TautologyLine}:
                self._add_line(line)
            elif isinstance(line, Proof.MPLine):
                self.add_mp(line.formula,
                            line.antecedent_line_number + line_shift,
                            line.conditional_line_number + line_shift)
            else:
                assert isinstance(line, Proof.UGLine)
                self.add_ug(line.formula,
                            line.predicate_line_number + line_shift)
        line_number = len(self._lines) - 1
        assert self._lines[line_number].formula == conclusion
        return line_number

    def add_universal_instantiation(self, instantiation: Union[Formula, str],
                                    line_number: int, term: Union[Term, str]) \
            -> int:
        """Appends to the proof being created by the current prover a sequence
        of validly justified lines, the last of which validly justifies the
        given formula, which is the result of substituting a term for the
        outermost universally quantified variable name of the formula of the
        specified already existing line of the proof.

        Parameters:
            instantiation: conclusion of the sequence of lines to be appended,
                specified as either a formula or its string representation.
            line_number: line number in the proof of a universally quantified
                formula of the form ``'A``\ `x`\ ``[``\ `predicate`\ ``]'``.
            term: term, specified as either a term or its string representation,
                that when substituted into the free occurrences of `x` in
                `predicate` yields the given formula.

        Returns:
            The line number of the newly appended line that justifies the given
            formula in the proof being created by the current prover.

        Examples:
            If Line `line_number` contains the formula
            ``'Ay[Az[f(x,y)=g(z,y)]]'`` and `term` is ``'h(w)'``, then
            `instantiation` should be ``'Az[f(x,h(w))=g(z,h(w))]'``.
        """
        if isinstance(instantiation, str):
            instantiation = Formula.parse(instantiation)
        assert line_number < len(self._lines)
        quantified = self._lines[line_number].formula
        assert quantified.root == 'A'
        if isinstance(term, str):
            term = Term.parse(term)
        assert instantiation == \
               quantified.predicate.substitute({quantified.variable: term})
        # Task 10.1

        line_formula = self._lines[line_number].formula
        inst_assump = f'({line_formula}->{instantiation})'
        inst_pred = line_formula.predicate.substitute({line_formula.variable: Term('_')})
        inst_mapping = {'x': line_formula.variable, 'R': inst_pred, 'c': term}
        step0 = self.add_instantiated_assumption(inst_assump, self.UI, inst_mapping)
        step1 = self.add_mp(instantiation, line_number, step0)
        return step1

    def _add_tau_implication_three_args(self, implication: Union[Formula, str],
                                        line_numbers: AbstractSet[int]) -> int:
        line_numbers = sorted(list(line_numbers))
        base_pred = f'({self._lines[line_numbers[-1]].formula}->{implication})'
        curr_pred = base_pred
        formula0, formula1 = [self._lines[i].formula for i in line_numbers[:-1]]
        and_formula = Formula.parse(f'({formula0}&{formula1})')
        curr_pred = Formula.parse(f'({and_formula}->{curr_pred})')
        step0 = self.add_tautology(curr_pred)
        x_line = line_numbers[0]
        y_line = line_numbers[1]
        x_implies_y_implies_x_and_y_line = self.add_tautology(f'({formula0}->({formula1}->{and_formula}))')

        y_implies_x_and_y_line = self.add_mp(f'({formula1}->{and_formula})', x_line, x_implies_y_implies_x_and_y_line)
        x_and_y = self.add_mp(f'{and_formula}', y_line, y_implies_x_and_y_line)
        tau_formula = Formula.parse(f'({and_formula}->{base_pred})')
        step1 = self.add_tautology(tau_formula)
        step2 = self.add_mp(base_pred, x_and_y, step1)
        step3 = self.add_mp(implication, line_numbers[-1], step2)
        return step3

    def add_tautological_implication(self, implication: Union[Formula, str],
                                     line_numbers: AbstractSet[int]) -> int:
        """Appends to the proof being created by the current prover a sequence
        of validly justified lines, the last of which validly justifies the
        given formula, which is the conclusion of a tautological inference whose
        assumptions are the specified already existing lines of the proof.

        Parameters:
            implication: conclusion of the sequence of lines to be appended,
                specified as either a formula or its string representation.
            line_numbers: line numbers in the proof of formulas from which
                conclusion can be a tautologically inferred.

        Returns:
            The line number of the newly appended line that justifies the given
            formula in the proof being created by the current prover.
        """
        if isinstance(implication, str):
            implication = Formula.parse(implication)
        for line_number in line_numbers:
            assert line_number < len(self._lines)
        # Task 10.2

        # line_numbers = sorted(list(line_numbers))
        line_numbers = list(line_numbers)
        curr_pred = implication
        for line_number in line_numbers:
            formula = self._lines[line_number].formula
            curr_pred = Formula.parse(f'({formula}->{curr_pred})')

        step = self.add_tautology(curr_pred)
        for line_number in reversed(line_numbers):
            # curr_pred = curr_pred.second
            step = self.add_mp(self._lines[-1].formula.second, line_number, step)

        return step

        #
        #
        #
        #
        # if len(list(line_numbers)) == 3:
        #     return self._add_tau_implication_three_args(implication, line_numbers)
        #
        # line_numbers = sorted(list(line_numbers))
        # base_pred = f'({self._lines[line_numbers[-1]].formula}->{implication})'
        # curr_pred = base_pred
        # for line_number in reversed(line_numbers[:-1]):
        #     formula = self._lines[line_number].formula
        #     curr_pred = Formula.parse(f'({formula}->{curr_pred})')
        #
        #
        #
        #
        # step2 = implication
        #
        # for line_number in line_numbers[:-1]:
        #     formula = self._lines[line_number].formula
        #     cond_line = self.add_tautology(curr_pred)
        #     curr_pred = curr_pred.second
        #     step2 = self.add_mp(curr_pred, line_number, cond_line)
        #
        # step2 = self.add_mp(implication, line_numbers[-1], step2)
        #
        # return step2

    def add_existential_derivation(self, consequent: Union[Formula, str],
                                   line_number1: int, line_number2: int) -> int:
        """Appends to the proof being created by the current prover a sequence
        of validly justified lines, the last of which validly justifies the
        given formula, which is the consequent of the second specified already
        existing line of the proof, whose antecedent is existentially quantified
        in the first specified already existing line of the proof.

        Parameters:
            consequent: conclusion of the sequence of lines to be appended,
                specified as either a formula or its string representation.
            line_number1: line number in the proof of an existentially
                quantified formula of the form
                ``'E``\ `x`\ ``[``\ `antecedent(x)`\ ``]'``, where `x`
                is a variable name that may have free occurrences in
                `antecedent(x)` but has no free occurrences in `consequent`.
            line_number2: line number in the proof of the formula
                ``'(``\ `antecedent(x)`\\ ``->``\ `consequent`\ ``)'``.

        Returns:
            The line number of the newly appended line that justifies the given
            formula in the proof being created by the current prover.
        """
        if isinstance(consequent, str):
            consequent = Formula.parse(consequent)
        assert line_number1 < len(self._lines)
        quantified = self._lines[line_number1].formula
        assert quantified.root == 'E'
        assert quantified.variable not in consequent.free_variables()
        assert line_number2 < len(self._lines)
        conditional = self._lines[line_number2].formula
        assert conditional == Formula('->', quantified.predicate, consequent)
        # Task 10.3

        # line_number1, line_number2 = sorted([line_number1, line_number2])

        line1_f, line2_f = [self._lines[i].formula for i in [line_number1, line_number2]]
        ug_var = self._lines[line_number1].formula.variable
        ug_line1_f = Formula.parse(f'A{ug_var}[{line2_f}]')
        step0 = self.add_ug(ug_line1_f, line_number2)

        es_line_f = Formula.parse(f'(({ug_line1_f}&{line1_f})->{consequent})')
        es_line_mapping = {'x': ug_var, 'R': line2_f.first.substitute({ug_var: Term('_')}), 'Q': consequent}
        step1 = self.add_instantiated_assumption(es_line_f, self.ES, es_line_mapping)
        step2 = self.add_tautological_implication(consequent, {line_number1, step0, step1})

        return step2

    def add_flipped_equality(self, flipped: Union[Formula, str],
                             line_number: int) -> int:
        """Appends to the proof being created by the current prover a sequence
        of validly justified lines, the last of which validly justifies the
        given equality, which is the result of exchanging the two sides of an
        equality from the specified already existing line of the proof.

        Parameters:
            flipped: conclusion of the sequence of lines to be appended,
                specified as either a formula or its string representation.
            line_number: line number in the proof of an equality that is the
                same as the given equality, except that the two sides of the
                equality are exchanged.

        Returns:
            The line number of the newly appended line that justifies the given
            equality in the proof being created by the current prover.
        """
        if isinstance(flipped, str):
            flipped = Formula.parse(flipped)
        assert is_equality(flipped.root)
        assert line_number < len(self._lines)
        equality = self._lines[line_number].formula
        assert equality == Formula('=', [flipped.arguments[1],
                                         flipped.arguments[0]])
        # Task 10.6
        flipped_first, flipped_second = [flipped.arguments[i] for i in [0, 1]]

        consq = f'({flipped_second}={flipped_second}->{flipped_first}={flipped_second})'
        f0 = Formula.parse(f'({flipped_second}={flipped_first}->{consq})')
        step0 = self.add_instantiated_assumption(f0, Prover.ME,
                                                 {'R': f'_={flipped_second}', 'c': flipped_second, 'd': flipped_first})
        step1 = self.add_mp(consq, line_number, step0)
        obv = f'{flipped_second}={flipped_second}'
        step2 = self.add_instantiated_assumption(obv, Prover.RX, {'c': flipped_second})
        step3 = self.add_mp(flipped, step2, step1)
        return step3

    def add_free_instantiation(self, instantiation: Union[Formula, str],
                               line_number: int,
                               substitution_map:
                               Mapping[str, Union[Term, str]]) -> int:
        """Appends to the proof being created by the current prover a sequence
        of validly justified lines, the last of which validly justifies the
        given formula, which is the result of substituting terms for the free
        variable names of the formula of the specified already existing line of
        the proof.

        Parameters:
            instantiation: conclusion of the sequence of lines to be appended,
                which contains no variable names starting with ``z``, specified
                as either a formula or its string representation.
            line_number: line number in the proof of a formula with free
                variables, which contains no variable names starting with ``z``.
            substitution_map: mapping from free variable names of the formula
                with the given line number to terms that contain no variable
                names starting with ``z``, to be substituted for them to obtain
                the given formula. Each value of this map may also be given as a
                string representation (instead of a term). Only variable names
                originating in the formula with the given line number are
                substituted (i.e., variable names originating in one of the
                specified substitutions are not subjected to additional
                substitutions).

        Returns:
            The line number of the newly appended line that justifies the given
            formula in the the proof being created by the current prover.
            
        Examples:
            If Line `line_number` contains the formula
            ``'Ay[Az[f(x,y)=g(z,y)]]'`` and `substitution_map` is
            ``{'y': Term.parse('h(w)')}``, then `instantiation` should be
            ``'Az[f(x,h(w))=g(z,h(w))]'``.
        """
        if isinstance(instantiation, str):
            instantiation = Formula.parse(instantiation)
        assert line_number < len(self._lines)
        substitution_map = dict(substitution_map)
        for variable in substitution_map:
            assert is_variable(variable)
            term = substitution_map[variable]
            if isinstance(term, str):
                substitution_map[variable] = Term.parse(term)
        assert instantiation == \
               self._lines[line_number].formula.substitute(substitution_map)

        # Task 10.7
        inter_mapping_vals = [next(fresh_variable_name_generator) for i in range(len(substitution_map))]
        inter_mapping = dict(zip(substitution_map.keys(), inter_mapping_vals))
        final_mapping = dict(zip(inter_mapping_vals, substitution_map.values()))

        orig_formula = self._lines[line_number]

        curr_formula = orig_formula
        curr_step = line_number

        quant_dummy_var = next(fresh_variable_name_generator)

        for mapping in [inter_mapping, final_mapping]:
            for key, val in mapping.items():
                quant_formula = Formula.parse(f'A{key}[{curr_formula}]')
                curr_step = self.add_ug(quant_formula, curr_step)
                curr_formula = quant_formula.predicate.substitute({key: Term(val) if isinstance(val, str) else val})
                curr_step = self.add_universal_instantiation(curr_formula, curr_step, val)

        return curr_step

    def add_substituted_equality(self, substituted: Union[Formula, str],
                                 line_number: int,
                                 parametrized_term: Union[Term, str]) -> \
            int:
        """Appends to the proof being created by the current prover a sequence
        of validly justified lines, the last of which validly justifies the
        given equality, whose two sides are the results of substituting the
        two respective sides of an equality from the specified already existing
        line of the proof into the given parametrized term.

        Parameters:
            substituted: conclusion of the sequence of lines to be appended,
                specified as either a formula or its string representation.
            line_number: line number in the proof of an equality.
            parametrized_term: term parametrized by the constant name ``'_'``,
                specified as either a term or its string representation, such
                that substituting each of the two sides of the equality with the
                given line number into this parametrized term respectively
                yields each of the two sides of the given equality.

        Returns:
            The line number of the newly appended line that justifies the given
            equality in the proof being created by the current prover.

        Examples:
            If Line `line_number` contains the formula ``'g(x)=h(y)'`` and
            `parametrized_term` is ``'_+7'``, then `substituted` should be
            ``'g(x)+7=h(y)+7'``.
        """
        if isinstance(substituted, str):
            substituted = Formula.parse(substituted)
        assert is_equality(substituted.root)
        assert line_number < len(self._lines)
        equality = self._lines[line_number].formula
        assert is_equality(equality.root)
        if isinstance(parametrized_term, str):
            parametrized_term = Term.parse(parametrized_term)
        assert substituted == \
               Formula('=', [parametrized_term.substitute(
                   {'_': equality.arguments[0]}),
                   parametrized_term.substitute(
                       {'_': equality.arguments[1]})])

        # Task 10.8
        orig_formula = self._lines[line_number].formula

        c, d = orig_formula.arguments
        sub_c = parametrized_term.substitute({'_': c})
        sub_d = parametrized_term.substitute({'_': d})
        consq_l = f'{sub_c}={sub_c}'
        consq_r = f'{sub_c}={sub_d}'
        consq = f'({consq_l}->{consq_r})'
        r = f'{sub_c}={parametrized_term}'
        inst_map = {'c': c, 'd': d, 'R': r}

        f0 = f'({orig_formula}->{consq})'
        step0 = self.add_instantiated_assumption(f0, Prover.ME, inst_map)

        f1 = consq
        step1 = self.add_mp(f1, line_number, step0)

        obv = consq_l
        step2 = self.add_instantiated_assumption(obv, Prover.RX, {'c': sub_c})

        f3 = consq_r
        step3 = self.add_mp(f3, step2, step1)

        return step3

        flipped_first, flipped_second = [flipped.arguments[i] for i in [0, 1]]

        consq = f'({flipped_second}={flipped_second}->{flipped_first}={flipped_second})'
        f0 = Formula.parse(f'({flipped_second}={flipped_first}->{consq})')
        step0 = self.add_instantiated_assumption(f0, Prover.ME,
                                                 {'R': f'_={flipped_second}', 'c': flipped_second, 'd': flipped_first})
        step1 = self.add_mp(consq, line_number, step0)
        obv = f'{flipped_second}={flipped_second}'
        step2 = self.add_instantiated_assumption(obv, Prover.RX, {'c': flipped_second})
        step3 = self.add_mp(flipped, step2, step1)
        return step3

    def _add_chaining_of_two_equalities(self, line_number1: int,
                                        line_number2: int) -> int:
        """Appends to the proof being created by the current prover a sequence
        of validly justified lines, the last of which validly justifies an
        equality that is the result of chaining together two equalities from
        the specified already existing lines of the proof.

        Parameters:
            line_number1: line number in the proof of an equality of the form
                ``'``\ `first`\ ``=``\ `second`\ ``'``.
            line_number2: line number in the proof of an equality of the form
                ``'``\ `second`\ ``=``\ `third`\ ``'``.

        Returns:
            The line number of the newly appended line that justifies the
            equality ``'``\ `first`\ ``=``\ `third`\ ``'`` in the proof being
            created by the current prover.

        Examples:
            If Line `line_number1` contains the formula ``'a=b'`` and Line
            `line_number2` contains the formula ``'b=f(b)'``, then the last
            appended line will contain the formula ``'a=f(b)'``.
        """
        assert line_number1 < len(self._lines)
        equality1 = self._lines[line_number1].formula
        assert is_equality(equality1.root)
        assert line_number2 < len(self._lines)
        equality2 = self._lines[line_number2].formula
        assert is_equality(equality2.root)
        assert equality1.arguments[1] == equality2.arguments[0]

        # Task 10.9.1
        f1, f2 = [self._lines[i].formula for i in [line_number1, line_number2]]
        a, b, c = f1.arguments[0], f1.arguments[1], f2.arguments[1]

        consq_l = f2
        consq_r = f'{a}={c}'
        consq = f'({consq_l}->{consq_r})'

        f0 = f'{b}={a}'
        s0 = self.add_flipped_equality(f0, line_number1)

        f1 = f'({f0}->{consq})'
        m1 = {'c': b, 'd': a, 'R': f'_={c}'}
        s1 = self.add_instantiated_assumption(f1, Prover.ME, m1)

        f2 = consq
        s2 = self.add_mp(f2, s0, s1)

        f3 = consq_r
        s3 = self.add_mp(f3, line_number2, s2)

        return s3

    def add_chained_equality(self, chained: Union[Formula, str],
                             line_numbers: Sequence[int]) -> int:
        """Appends to the proof being created by the current prover a sequence
        of validly justified lines, the last of which validly justifies the
        given equality, which is the result of chaining together equalities
        from the specified already existing lines of the proof.

        Parameters:
            chained: conclusion of the sequence of lines to be appended,
                specified as either a formula or its string representation,
                of the form ``'``\ `first`\ ``=``\ `last`\ ``'``.
            line_numbers: line numbers in the proof of equalities of the form
                ``'``\ `first`\ ``=``\ `second`\ ``'``,
                ``'``\ `second`\ ``=``\ `third`\ ``'``, ...,
                ``'``\ `before_last`\ ``=``\ `last`\ ``'``, i.e., the left-hand
                side of the first equality is the left-hand side of the given
                equality, the right-hand of each equality (except for the last)
                is the left-hand side of the next equality, and the right-hand
                side of the last equality is the right-hand side of the given
                equality.

        Returns:
            The line number of the newly appended line that justifies the given
            equality in the proof being created by the current prover.

            Examples:
            If `line_numbers` is ``[7,3,9]``, Line 7 contains the formula
            ``'a=b'``, Line 3 contains the formula ``'b=f(b)'``, and Line 9
            contains the formula ``'f(b)=0'``, then `chained` should be
            ``'a=0'``.
        """
        if isinstance(chained, str):
            chained = Formula.parse(chained)
        assert is_equality(chained.root)
        assert len(line_numbers) >= 2
        current_term = chained.arguments[0]
        for line_number in line_numbers:
            assert line_number < len(self._lines)
            equality = self._lines[line_number].formula
            assert is_equality(equality.root)
            assert equality.arguments[0] == current_term
            current_term = equality.arguments[1]
        assert chained.arguments[1] == current_term
        # Task 10.9.2

        curr_step = line_numbers[0]
        for ln in line_numbers[1:]:
            curr_step = self._add_chaining_of_two_equalities(curr_step, ln)

        return curr_step

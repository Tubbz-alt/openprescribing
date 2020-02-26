"""
Defines a list of "substitution sets" which are groups of presentations which
can, in our opinion, be substituted for one another.

The most common kind of set is just a generic presentation plus all its brands,
and we use this as the starting point for defining all the substitutions.
However in some cases there are clinical reasons why brands can't be
substituted for one another so we have to remove these cases (see
EXCLUSIONS_RE).

There are also cases where distinct generic presentations *can* be substitued
for one another. For instance, a drug may come in both tablet and capsule form
and these will have distinct generic codes but they may well be interchangeable
for most purposes. We maintain a manually curated spreadsheet which lists these
kind of substitution (see FORMULATION_SWAPS_FILE).
"""
import csv
from collections import defaultdict
import os.path
import re

from functools import lru_cache

from matrixstore.db import get_db
from frontend.models import Presentation


# This would be a good candidate for a dataclass when we move to Python 3.7
class SubstitutionSet:
    """
    Represents a set of presentations which we believe can be reasonably
    substituted for one another
    """

    def __init__(self, id, presentations, name=None, formulation_swaps=None):
        # The code which identifies this set of substitutions. As it happens we
        # define this as the lexically smallest generic BNF code in the set but the
        # rest of the codebase just treats this as an opaque string identifier.
        self.id = id
        # The BNF codes for all presentations contained within the set
        self.presentations = presentations
        # Human readable name to represent this set (usually the name of the generic)
        self.name = name
        # Where a substitution set involves multiple formulations (e.g tablets and
        # capsules) this is a string representating a short, human-readable
        # description of the formulation swaps involved e.g 'Tab / Cap'. If no
        # formulation changes are involved then this is None.
        self.formulation_swaps = formulation_swaps


# Create a memoize decorator (i.e. a decorator which caches the return value
# for a given set of arguments). Here `maxsize=None` means "don't apply any
# cache eviction, just keep values for ever"
memoize = lru_cache(maxsize=None)


# The below file defines groups of generics of different formulations which we
# believe can be substituted for each other (e.g tramadol tablets and
# capsules). The canonical version is maintained as a Google Sheet at:
#  https://docs.google.com/spreadsheets/d/e/
#  2PACX-1vSsTrjEdRekkcR0H8myL8RwP3XKg2YvTgQwGb5ypNei0IYn4ofrayVZJibLfN
#  _lnpm6Q9qu_t0yXU5Z/pub?gid=1784930737&single=true&output=csv
#
# The local copy can be updated using the command:
#   curl -L https://tinyurl.com/uwzg8qc > frontend/price_per_unit/formulation_swaps.csv
FORMULATION_SWAPS_FILE = os.path.join(
    os.path.dirname(__file__), "formulation_swaps.csv"
)


# BNF codes which we can't map to generics for various reasons. Issue numbers
# below refer to https://github.com/ebmdatalab/price-per-dose/issues
EXCLUSIONS_RE = re.compile(
    r"""
    (
      0302000C0....BE |  # issue #10
      0302000C0....BF |  # issue #10
      0302000C0....BH |  # issue #10
      0302000C0....BG |  # issue #10
      0904010H0.*     |  # issue #9
      1311070S0....AA |  # issue #9
      1311020L0....BS |  # issue #9
      0301020S0....AA |  # issue #12
      190700000BBCJA0 |  # issue #12
      0604011L0BGAAAH |  # issue #12
      1502010J0....BY |  # issue #12
      1201010F0AAAAAA |  # issue #12
      0107010S0AAAGAG |  # issue #12
      060016000BBAAA0 |  # issue #14
      190201000AABJBJ |  # issue #14
      190201000AABKBK |  # issue #14
      190201000AABLBL |  # issue #14
      190201000AABMBM |  # issue #14
      190201000AABNBN |  # issue #14
      190202000AAADAD    # issue #14
    )
    """,
    re.VERBOSE,
)


# These are BNF code prefixes where all presentations within the sub-paragraph
# can be considered substitutable. See
# https://github.com/ebmdatalab/price-per-dose/issues/1.
GENERIC_SUB_PARAGRAPHS = {
    "0601060U0": "Urine Testing Reagents",
    "0601060D0": "Glucose Blood Testing Reagents",
}


@memoize
def get_substitution_sets():
    bnf_codes = [row[0] for row in get_db().query("SELECT bnf_code FROM presentation")]
    substitution_sets = get_substitution_sets_from_bnf_codes(bnf_codes)
    return {s.id: s for s in substitution_sets}


def get_substitution_sets_from_bnf_codes(bnf_codes):
    """
    Given a list of BNF codes return a list of SubstitutionSets over those BNF
    codes
    """
    swaps, swap_descriptions = get_formulation_swaps(FORMULATION_SWAPS_FILE)
    presentation_sets = defaultdict(list)
    for bnf_code in bnf_codes:
        generic_code = generic_equivalent_for_bnf_code(bnf_code)
        if generic_code:
            generic_code = swaps.get(generic_code, generic_code)
            presentation_sets[generic_code].append(bnf_code)
    names = get_names_for_bnf_codes(presentation_sets.keys())
    return [
        SubstitutionSet(
            id=code,
            name=names.get(code, "unknown"),
            presentations=sorted(presentations),
            formulation_swaps=swap_descriptions.get(code),
        )
        for code, presentations in presentation_sets.items()
        # There's no point in a substitution set with only one member
        if len(presentations) > 1
    ]


def get_names_for_bnf_codes(bnf_codes):
    names = Presentation.names_for_bnf_codes(list(bnf_codes))
    # Add in names for our invented BNF codes which represent their entire BNF
    # sub-paragraph
    for sub_para, name in GENERIC_SUB_PARAGRAPHS.items():
        names[sub_para + "AAA0A0"] = name
    return names


def generic_equivalent_for_bnf_code(bnf_code):
    """
    Return the generic equivalent BNF code for a supplied BNF code or None if
    there is no such equivalent
    """
    # Exclude devices etc.
    if len(bnf_code) != 15:
        return
    # Exclude BNF codes where we have identified an issue
    if EXCLUSIONS_RE.match(bnf_code):
        return
    sub_paragraph_and_chemical = bnf_code[0:9]
    generic_strength_and_formulation = bnf_code[13:15]
    has_generic_equivalent = generic_strength_and_formulation != "A0"
    if has_generic_equivalent or sub_paragraph_and_chemical in GENERIC_SUB_PARAGRAPHS:
        return "{0}AA{1}{1}".format(
            sub_paragraph_and_chemical, generic_strength_and_formulation
        )


def get_formulation_swaps(filename):
    """
    Reads a "formulation swaps" CSV file and returns a pair of dicts:

        swaps: maps generic BNF codes to alternative generic BNF codes (which
               would usually be of a different formulation) to which they
               should be considered equivalent

        swap_descriptions: maps generic BNF codes to a short text description
                           of the formulation changes involved e.g for tablets
                           and capsules we'd have "Tabs / Caps"
    """
    swaps = {}
    swap_descriptions = {}
    for codes, formulations in read_formulation_swaps_file(filename):
        # We use the lexically smallest code from a group of equivalent
        # generics to represent the group
        primary_code = sorted(codes)[0]
        for code in codes:
            swaps[code] = primary_code
        if len(formulations) > 1:
            swap_descriptions[primary_code] = " / ".join(sorted(formulations))
    return swaps, swap_descriptions


def read_formulation_swaps_file(filename):
    """
    Reads a "formulation swaps" CSV file and yields groups of substitutable
    generic presentations as tuples of the form:

        ([<list of generic BNF codes], [<list of formulations>])

    For instance, Tramadol tablets and capsules are distinct generic
    presentations, but are almost always substitutable for each other so the
    response might include:

        # 100mg tablets and capsules
        (['040702040AAACAC', '040702040AAAHAH'], ['Tab', 'Cap'])

        # 200mg tablets and capsules
        (['040702040AAAEAE', '040702040AAAJAJ'], ['Tab', 'Cap'])

    The swaps file must be manually curated to ensure that the substitutions
    are clinically sensible.
    """
    with open(filename, "rt") as handle:
        data = list(csv.DictReader(handle))
    code_pairs = []
    formulations = {}
    for row in data:
        if row["Really equivalent?"].strip() != "Y":
            continue
        code = row["Code"].strip()
        alternative_code = row["Alternative code"].strip()
        # Check that all codes in the substitutions table are generics
        assert code == generic_equivalent_for_bnf_code(code)
        assert alternative_code == generic_equivalent_for_bnf_code(alternative_code)
        assert code != alternative_code
        code_pairs.append((code, alternative_code))
        formulations[code] = row["Formulation"].strip()
        formulations[alternative_code] = row["Alternative formulation"].strip()
    # We combine pairs of equivalent codes into groups of equivalent codes.
    # This means if our substitutions table says "A and B are equivalent" and
    # "B and C are equivalent" then we can handle this correctly.
    for code_group in groups_from_pairs(code_pairs):
        # Get the unique formulations involved in this group
        formulations_for_group = [
            f for f in set(map(formulations.get, code_group)) if f
        ]
        yield code_group, formulations_for_group


def groups_from_pairs(pairs):
    """
    Accepts a list of pairs and combines any overlapping pairs into groups

    >>> list(groups_from_pairs([
    ...     (1, 2),
    ...     (3, 4),
    ...     (5, 6),
    ...     (1, 3),
    ... ]))
    [[1, 2, 3, 4], [5, 6]]

    In set theoretic terms, `pairs` is an equivalence relation and `groups` are
    the equivalence classes it induces.
    """
    groups = {}
    for element, other_element in pairs:
        group = groups.setdefault(element, [element])
        other_group = groups.get(other_element, [other_element])
        if other_group is not group:
            group.extend(other_group)
            for member in other_group:
                groups[member] = group
    for element, group in groups.items():
        # Each group will occur multiple times in this loop, once for each of
        # its elements. But we want to return just the unique groups, so we
        # pick (arbitrarily) the first element of each group to identify it
        # with.
        if element == group[0]:
            yield group

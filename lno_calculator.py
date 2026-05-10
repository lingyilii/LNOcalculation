"""
LNO Calculation Engine
Core calculation logic for spent powder and precursor mass calculations.
"""

import re
from dataclasses import dataclass
from typing import Optional

# Molar masses dictionary (g/mol)
ELEMENT_MOLAR_MASS = {
    'Li': 6.941,
    'Ni': 58.693,
    'Co': 58.933,
    'Mn': 54.938,
    'O':  15.999,
    'H':  1.008,
    'F':  18.998,
    'Br': 79.904,
    'S':  32.065,
    'I':  126.904,
    'N':  14.007,
    'C':  12.011,
    'Na': 22.990,
    'K':  39.098,
    'Ca': 40.078,
    'Mg': 24.305,
    'Al': 26.982,
    'Si': 28.086,
    'P':  30.974,
    'Cl': 35.453,
    'Ti': 47.867,
    'V':  50.942,
    'Cr': 51.996,
    'Fe': 55.845,
    'Cu': 63.546,
    'Zn': 65.38,
    'Zr': 91.224,
    'Mo': 95.96,
    'W':  183.84,
}


def parse_formula(formula: str) -> dict:
    """
    Parse a chemical formula string into {element: stoichiometry} dict.
    Supports: Li0.7Ni0.63Co0.15Mn0.19O2, Ni(OH)1.84(FBrSI)0.04, LiOH*H2O, LiOH·H2O
    """
    # Normalize hydrate notation: * or · → explicit expansion
    formula = formula.strip()

    # Handle hydrate notation (e.g., LiOH*H2O or LiOH·H2O)
    hydrate_pattern = r'[*·]'
    if re.search(hydrate_pattern, formula):
        parts = re.split(hydrate_pattern, formula)
        result = {}
        for part in parts:
            coeff_match = re.match(r'^(\d+(?:\.\d+)?)(.*)', part.strip())
            if coeff_match:
                coeff = float(coeff_match.group(1))
                sub = coeff_match.group(2)
            else:
                coeff = 1.0
                sub = part.strip()
            sub_elements = _parse_simple(sub)
            for el, ratio in sub_elements.items():
                result[el] = result.get(el, 0) + ratio * coeff
        return result

    return _parse_simple(formula)


def _parse_simple(formula: str) -> dict:
    """
    Parse formula handling parentheses groups with float stoichiometry.
    e.g. Ni(OH)1.84(FBrSI)0.04
    """
    elements = {}

    def add_elements(src_dict, multiplier=1.0):
        for el, val in src_dict.items():
            elements[el] = elements.get(el, 0) + val * multiplier

    # Iteratively expand parenthetical groups
    i = 0
    tokens = []
    while i < len(formula):
        if formula[i] == '(':
            # Find matching closing paren
            depth = 1
            j = i + 1
            while j < len(formula) and depth > 0:
                if formula[j] == '(':
                    depth += 1
                elif formula[j] == ')':
                    depth -= 1
                j += 1
            inner = formula[i+1:j-1]
            # Check for float/int multiplier after )
            mult_match = re.match(r'(\d+(?:\.\d+)?)', formula[j:])
            if mult_match:
                mult = float(mult_match.group(1))
                i = j + len(mult_match.group(1))
            else:
                mult = 1.0
                i = j
            inner_elements = _parse_simple(inner)
            add_elements(inner_elements, mult)
        else:
            # Match element + optional float
            m = re.match(r'([A-Z][a-z]?)(\d+(?:\.\d+)?)?', formula[i:])
            if m:
                el = m.group(1)
                ratio = float(m.group(2)) if m.group(2) else 1.0
                elements[el] = elements.get(el, 0) + ratio
                i += len(m.group(0))
            else:
                i += 1  # skip unknown chars

    return elements


def calculate_molar_mass(formula_dict: dict) -> float:
    """Calculate molar mass from parsed formula dict."""
    total = 0.0
    for element, ratio in formula_dict.items():
        if element not in ELEMENT_MOLAR_MASS:
            raise ValueError(f"Unknown element: '{element}'. Please check the formula.")
        total += ELEMENT_MOLAR_MASS[element] * ratio
    return total


@dataclass
class PrecursorResult:
    precursor_mass_per_g: float        # g precursor per 1g spent powder
    spent_powder_mass: float
    precursor_mass: float
    ni_final_percentage: float
    formula_spent: dict
    formula_precursor: dict
    molar_mass_spent: float
    molar_mass_precursor: float


@dataclass
class LiSourceResult:
    li_source_mass_per_ni_rich: float  # g Li source per g Ni-rich
    li_source_mass: float
    ni_rich_mass: float
    add_li_source_mass_per_target: float  # for Ni_rich_mass_new
    ni_rich_mass_new: float


def calculate_precursor(
    spent_formula: str,
    precursor_formula: str,
    ni_final_pct: float,
    spent_mass: Optional[float] = None,
    precursor_mass_input: Optional[float] = None
) -> PrecursorResult:
    """
    Calculate how much precursor (Ni source) to add to spent powder
    to achieve target Ni final percentage.
    """
    f_spent = parse_formula(spent_formula)
    f_precursor = parse_formula(precursor_formula)

    mm_spent = calculate_molar_mass(f_spent)
    mm_precursor = calculate_molar_mass(f_precursor)

    # Get stoichiometry ratios from spent powder
    ni_spent_ratio = f_spent.get('Ni', 0)
    # TM = total transition metals (Ni+Co+Mn typically, represented as 1 per formula unit)
    tm_spent_ratio = 1.0  # per formula unit of spent powder

    # Get Ni ratio in precursor
    ni_precursor_ratio = f_precursor.get('Ni', 0)
    if ni_precursor_ratio == 0:
        raise ValueError("Precursor formula does not contain Ni.")

    ni_target = ni_final_pct / 100.0

    # Basis: 1g spent powder
    spent_basis = 1.0
    spent_mol = spent_basis / mm_spent
    ni_spent_mol = spent_mol * ni_spent_ratio
    tm_spent_mol = spent_mol * tm_spent_ratio

    # Solve: (ni_spent_mol + add_ni_mol) / (tm_spent_mol + add_ni_mol) = ni_target
    # ni_spent_mol + add_ni = ni_target * (tm_spent_mol + add_ni)
    # ni_spent_mol + add_ni = ni_target*tm_spent_mol + ni_target*add_ni
    # add_ni*(1 - ni_target) = ni_target*tm_spent_mol - ni_spent_mol
    denom = 1.0 - ni_target
    if abs(denom) < 1e-10:
        raise ValueError("Ni final percentage cannot be 100%.")

    add_ni_mol = (ni_target * tm_spent_mol - ni_spent_mol) / denom

    if add_ni_mol < 0:
        raise ValueError(
            f"The spent powder already has Ni ratio {ni_spent_ratio:.3f} "
            f"({ni_spent_ratio*100:.1f}%), which exceeds target {ni_final_pct:.1f}%. "
            "Cannot reduce Ni by adding precursor."
        )

    add_precursor_mol = add_ni_mol / ni_precursor_ratio
    precursor_mass_per_g = add_precursor_mol * mm_precursor

    # Scale to actual masses
    if spent_mass is not None and precursor_mass_input is None:
        actual_spent = spent_mass
        actual_precursor = spent_mass * precursor_mass_per_g
    elif precursor_mass_input is not None and spent_mass is None:
        actual_precursor = precursor_mass_input
        actual_spent = precursor_mass_input / precursor_mass_per_g
    elif spent_mass is not None and precursor_mass_input is not None:
        # Both given – use spent as primary
        actual_spent = spent_mass
        actual_precursor = spent_mass * precursor_mass_per_g
    else:
        actual_spent = 1.0
        actual_precursor = precursor_mass_per_g

    return PrecursorResult(
        precursor_mass_per_g=precursor_mass_per_g,
        spent_powder_mass=actual_spent,
        precursor_mass=actual_precursor,
        ni_final_percentage=ni_final_pct,
        formula_spent=f_spent,
        formula_precursor=f_precursor,
        molar_mass_spent=mm_spent,
        molar_mass_precursor=mm_precursor,
    )


def calculate_li_source(
    precursor_result: PrecursorResult,
    li_source_formula: str,
    li_final_ratio: float,
    ni_rich_mass_new: float,
) -> LiSourceResult:
    """
    Calculate how much Li source to add to Ni-rich mixed powder.
    """
    f_li = parse_formula(li_source_formula)
    mm_li = calculate_molar_mass(f_li)

    li_li_source_ratio = f_li.get('Li', 0)
    if li_li_source_ratio == 0:
        raise ValueError("Li source formula does not contain Li.")

    spent_mass = precursor_result.spent_powder_mass
    precursor_mass = precursor_result.precursor_mass
    f_spent = precursor_result.formula_spent
    f_precursor = precursor_result.formula_precursor
    mm_spent = precursor_result.molar_mass_spent
    mm_precursor = precursor_result.molar_mass_precursor

    ni_precursor_ratio = f_precursor.get('Ni', 0)
    ni_spent_ratio = f_spent.get('Ni', 0)
    li_spent_ratio = f_spent.get('Li', 0)

    ni_final_ratio = precursor_result.ni_final_percentage / 100.0

    # Moles of Ni contributed by precursor and spent
    ni_from_precursor = ni_precursor_ratio * (precursor_mass / mm_precursor)
    ni_from_spent = ni_spent_ratio * (spent_mass / mm_spent)
    ni_rich_mol_total = ni_from_precursor + ni_from_spent

    # Li already in spent powder
    li_from_spent = li_spent_ratio * (spent_mass / mm_spent)

    # Required total Li moles: Li/Ni_final = li_final_ratio
    li_final_mol = li_final_ratio * ni_rich_mol_total / ni_final_ratio

    add_li_mol = li_final_mol - li_from_spent
    if add_li_mol < 0:
        add_li_mol = 0  # Already enough Li

    add_li_source_mol = add_li_mol / li_li_source_ratio
    add_li_source_mass = add_li_source_mol * mm_li

    ni_rich_mass = spent_mass + precursor_mass

    # Scale to target batch
    scale = ni_rich_mass_new / ni_rich_mass if ni_rich_mass > 0 else 0
    add_li_source_mass_new = add_li_source_mass * scale

    return LiSourceResult(
        li_source_mass_per_ni_rich=add_li_source_mass / ni_rich_mass if ni_rich_mass > 0 else 0,
        li_source_mass=add_li_source_mass,
        ni_rich_mass=ni_rich_mass,
        add_li_source_mass_per_target=add_li_source_mass_new,
        ni_rich_mass_new=ni_rich_mass_new,
    )

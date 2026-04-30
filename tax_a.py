# australia_marginal_rate.py
# Returns AU marginal income-tax rate (decimal) for 2024–25.
# Defaults match your simplified model (flat +2% Medicare; no LITO; no MLS).
# Turn on flags to include ATO low-income Medicare shading, LITO clawback, and MLS tiers.

from typing import Union

# --- Brackets (resident, 2024–25: Stage 3) ---
def _base_marginal(income: float) -> float:
    x = float(max(0.0, income))
    if x <= 18_200:
        return 0.0
    elif x <= 45_000:
        return 0.16
    elif x <= 135_000:
        return 0.30
    elif x <= 190_000:
        return 0.37
    else:
        return 0.45

# Medicare levy marginal component 
# Singles low-income thresholds for 2024–25 (ATO): lower 27,222; full levy reached by 34,027.
_SINGLE_MEDICARE_LOWER = 27_222.0
_SINGLE_MEDICARE_FULL  = 34_027.0

def _medicare_marginal(income: float, apply_shading: bool) -> float:
    if not apply_shading:
        return 0.02  # flat 2% like your original
    x = float(income)
    if x <= _SINGLE_MEDICARE_LOWER:
        return 0.0
    elif x < _SINGLE_MEDICARE_FULL:
        return 0.10  # “10c per $” phase-in in the shade band
    else:
        return 0.02

#  LITO clawback marginal 
# ATO LITO (2024–25): max $700; phases out:
#  - 5% from $37,500 to $45,000
#  - 1.5% from $45,001 to $66,667
def _lito_marginal(income: float) -> float:
    x = float(income)
    if 37_500 < x <= 45_000:
        return 0.05
    elif 45_000 < x <= 66_667:
        return 0.015
    else:
        return 0.0

# Medicare Levy Surcharge marginal (optional; assumes SINGLE status)
# 2024–25 MLS tiers (ATO): <=97k: 0%; 97,001–113,000: 1%; 113,001–151,000: 1.25%; >=151,001: 1.5%
def _mls_marginal(income: float) -> float:
    x = float(income)
    if x <= 97_000:
        return 0.0
    elif x <= 113_000:
        return 0.01
    elif x <= 151_000:
        return 0.0125
    else:
        return 0.015

def get_australia_marginal_rate(
    income: Union[int, float],
    *,
    medicare_flat_2pct: bool = True,   # keep True to match your original behaviour
    include_lito: bool = False,        # set True to include LITO clawback bands
    include_mls: bool = False,         # set True if NO private hospital cover (single)
) -> float:
    """
    Return the marginal tax rate (decimal) at 'income' for AU residents, 2024–25.
    - Default mimics your simple model: income-tax marginal + flat 2% Medicare.
    - Set medicare_flat_2pct=False to apply low-income Medicare shading (singles).
    - Set include_lito=True to add LITO clawback to the marginal rate where it applies.
    - Set include_mls=True to add MLS (assumes SINGLE and no private cover).
    """
    x = float(max(0.0, income))
    m = _base_marginal(x)
    m += _medicare_marginal(x, apply_shading=not medicare_flat_2pct)
    if include_lito:
        m += _lito_marginal(x)
    if include_mls:
        m += _mls_marginal(x)
    return float(m)

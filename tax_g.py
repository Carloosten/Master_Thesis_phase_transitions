
# german_marginal_rate.py
# Minimal function to return Germany's marginal income-tax rate (decimal) for 2025,
# incl. Solidaritätszuschlag phase-in, excl. church tax.
# Usage (from another notebook):
#   from german_marginal_rate import get_german_marginal_rate
#   m = get_german_marginal_rate(60_000, joint=False)  # -> e.g., 0.39...
from typing import Dict, List, Tuple
#  Soli parameters (2025) 
_SOLI_RATE_FULL = 0.055       # 5.5% of income tax (full zone)
_SOLI_PHASE_RATE = 0.119      # 11.9% of (ESt - threshold) in the "Milderungszone"
_SOLI_FREE_SINGLE = 19_950.0  # Freigrenze (ESt) single (Grundtabelle)
_SOLI_FREE_JOINT  = 39_900.0  # Freigrenze (ESt) married (Splittingtabelle)

def _income_tax_2025(x: float) -> float:
    """Income tax T(x) for 2025 (Grundtabelle), §32a EStG. x = zvE in EUR."""
    x = float(max(0.0, x))
    if x <= 12_096:
        return 0.0
    if x <= 17_443:
        y = (x - 12_096) / 10_000.0
        return (932.30 * y + 1_400.0) * y
    if x <= 68_480:
        z = (x - 17_443) / 10_000.0
        return (176.64 * z + 2_397.0) * z + 1_015.13
    if x <= 277_825:
        return 0.42 * x - 10_911.92
    return 0.45 * x - 19_246.67

def _income_tax_marginal_2025(x: float) -> float:
    """dT/dx (decimal) for §32a EStG 2025 (before Soli)."""
    x = float(max(0.0, x))
    if x <= 12_096:
        return 0.0
    if x <= 17_443:
        y = (x - 12_096) / 10_000.0
        return (2 * 932.30 * y + 1_400.0) / 10_000.0
    if x <= 68_480:
        z = (x - 17_443) / 10_000.0
        return (2 * 176.64 * z + 2_397.0) / 10_000.0
    if x <= 277_825:
        return 0.42
    return 0.45

def _soli_derivative_and_amount(est: float, joint: bool) -> Tuple[float, float]:
    """
    Given income tax 'est', return (dS/dT, soli_amount).
    dS/dT is the derivative of Soli w.r.t. income tax, needed to adjust the marginal rate.
    """
    thresh = _SOLI_FREE_JOINT if joint else _SOLI_FREE_SINGLE
    if est <= thresh:
        return 0.0, 0.0  # none
    phase = _SOLI_PHASE_RATE * (est - thresh)
    full  = _SOLI_RATE_FULL * est
    if phase <= full:
        return _SOLI_PHASE_RATE, phase  # phase-in
    return _SOLI_RATE_FULL, full        # full zone

def get_german_marginal_rate(income: float, joint: bool = False) -> float:
    """
    Return the total marginal income-tax rate (decimal) for Germany 2025 at 'income' (EUR),
    including Solidaritätszuschlag phase-in; church tax is excluded.
    """
    T = _income_tax_2025(income)
    dTdx = _income_tax_marginal_2025(income)
    dS_dT, _soli_amt = _soli_derivative_and_amount(T, joint)
    # Total marginal = d/dx [T + S(T)] = dT/dx * (1 + dS/dT)
    return float(dTdx * (1.0 + dS_dT))
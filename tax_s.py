# swiss_marginal_rate.py
# Minimal utility to return the Swiss marginal income-tax rate (decimal) for a given income and canton,
# using your pasted table of average tax rates by income for each canton.
#
# Usage from another notebook:
#   from swiss_marginal_rate import get_swiss_marginal_rate
#   m = get_swiss_marginal_rate(60000, "Zürich")   # -> 0.1459 (example)
#
# Returns a float (e.g., 0.1459 for 14.59%). No printing, no side effects.

from typing import Dict, List, Tuple
import bisect
import re

#  Canonical income grid (CHF) 
_INCOMES: List[float] = [35_000, 40_000, 45_000, 50_000, 60_000, 70_000, 80_000, 100_000, 125_000, 150_000, 200_000, 500_000]

#  Canton synonyms for input normalization 
_CANTON_SYNONYMS: Dict[str, List[str]] = {
    "ZH": ["ZH","zürich","zurich","zuerich"],
    "BE": ["BE","bern","berne"],
    "LU": ["LU","luzern","lucerne"],
    "UR": ["UR","uri","altdorf"],
    "SZ": ["SZ","schwyz"],
    "OW": ["OW","obwalden","sarnen"],
    "NW": ["NW","nidwalden","stans"],
    "GL": ["GL","glarus"],
    "ZG": ["ZG","zug"],
    "FR": ["FR","fribourg","freiburg"],
    "SO": ["SO","solothurn"],
    "BS": ["BS","basel-stadt","basel city","basel"],
    "BL": ["BL","basel-landschaft","basel country","liestal"],
    "SH": ["SH","schaffhausen"],
    "AR": ["AR","appenzell ausserrhoden","appenzell ausserrh.","herisau","appenzell outer rhodes"],
    "AI": ["AI","appenzell innerrhoden","appenzell innerrh.","appenzell"],
    "SG": ["SG","st. gallen","saint gallen","st gallen"],
    "GR": ["GR","graubünden","grisons","grigioni","chur"],
    "AG": ["AG","aargau","aarau"],
    "TG": ["TG","thurgau","frauenfeld"],
    "TI": ["TI","ticino","tessin","bellinzona"],
    "VD": ["VD","vaud","waadt","lausanne"],
    "VS": ["VS","valais","wallis","sion","sitten"],
    "NE": ["NE","neuchâtel","neuchatel"],
    "GE": ["GE","genève","geneva","genf"],
    "JU": ["JU","jura","delémont","delemont"],
}

#  Embedded table (exactly your data). We will parse only the average-rate columns. 
_TABLE = r"""
Canton	SFO Commune ID	Commune	35,000	40,000	Margin at 40k	45,000	Margin at 45k	50,000	Margin at 50k	60,000	Margin at 60k	70,000	Margin at 70k	80,000	Margin at 80k	100,000	Margin at 100k	125,000	Margin at 125k	150,000	Margin at 150k	200,000	Margin at 200k	500,000	Margin at 500k
ZH	261	Zürich	4.66	5.35	10.22	6.00	11.16	6.62	12.24	7.95	14.59	9.07	15.79	10.12	17.47	12.12	20.13	14.25	22.78	16.26	26.27	19.87	30.69	30.08	36.90
BE	351	Bern	8.45	9.70	18.48	10.77	19.34	11.56	18.60	12.96	19.97	14.00	20.27	14.82	20.57	16.64	23.92	18.74	27.11	20.65	30.19	23.96	33.92	32.52	38.23
LU	1061	Luzern	5.50	6.69	14.98	7.62	15.08	8.36	15.08	9.73	16.56	10.72	16.69	11.45	16.53	12.81	18.23	14.23	19.93	15.60	22.42	18.02	25.31	24.68	29.12
UR	1201	Altdorf (UR)	5.73	6.63	12.90	7.34	12.98	7.90	13.00	8.97	14.31	9.77	14.60	10.37	14.55	11.52	16.14	12.78	17.81	13.93	19.70	16.00	22.18	21.16	24.60
SZ	1372	Schwyz	2.76	3.69	10.16	4.60	11.90	5.39	12.52	6.47	11.87	7.34	12.53	8.08	13.25	9.55	15.46	11.06	17.11	12.39	19.04	14.57	21.11	21.04	25.35
OW	1407	Sarnen	6.34	7.19	13.12	7.89	13.50	8.42	13.24	9.47	14.69	10.09	13.81	10.54	13.71	11.51	15.41	12.62	17.07	13.68	18.94	15.61	21.39	20.53	23.81
NW	1509	Stans	5.27	6.20	12.64	6.95	12.98	7.55	12.98	8.67	14.24	9.57	15.01	10.27	15.18	11.62	17.01	13.09	18.98	14.45	21.21	16.77	23.75	21.43	24.54
GL	1632	Glarus	5.39	6.27	12.38	7.13	14.04	7.82	14.00	9.10	15.49	10.25	17.21	11.16	17.48	12.76	19.19	14.42	21.06	15.98	23.77	18.77	27.15	26.63	31.86
ZG	1711	Zug	1.37	1.74	4.34	2.06	4.64	2.36	5.06	3.13	6.93	3.84	8.16	4.43	8.52	5.63	10.46	7.25	13.69	8.96	17.52	11.90	20.72	17.82	21.76
FR	2196	Fribourg	5.89	7.34	17.50	8.75	20.04	9.89	20.12	11.82	21.49	13.13	21.02	14.31	22.51	16.48	25.20	18.57	26.94	20.58	30.58	24.39	35.85	30.31	34.26
SO	2601	Solothurn	6.31	7.81	18.30	8.99	18.46	9.97	18.84	11.76	20.71	13.15	21.48	14.23	21.75	16.05	23.32	17.98	25.73	19.78	28.80	22.76	31.68	28.99	33.14
BS	2701	Basel	2.99	5.02	19.16	6.60	19.26	7.86	19.26	10.02	20.78	11.57	20.87	12.75	21.03	14.77	22.87	16.73	24.57	18.37	26.53	20.95	28.71	29.99	36.01
BL	2829	Liestal	5.25	6.57	15.80	7.80	17.62	8.93	19.10	11.09	21.88	12.83	23.27	14.27	24.34	16.89	27.37	19.62	30.56	21.91	33.33	25.44	36.04	33.90	39.53
SH	2939	Schaffhausen	4.56	5.45	11.62	6.34	13.46	6.94	12.42	8.26	14.84	9.36	15.98	10.37	17.43	12.32	20.14	14.28	22.09	15.90	24.03	18.87	27.78	24.27	27.87
AR	3001	Herisau	6.47	7.52	14.88	8.36	15.12	9.04	15.10	10.48	17.67	11.63	18.55	12.61	19.48	14.43	21.69	16.38	24.20	18.05	26.40	20.82	29.13	26.42	30.16
AI	3101	Appenzell	4.70	5.41	10.40	6.03	10.98	6.53	11.00	7.57	12.76	8.38	13.25	9.01	13.40	10.35	15.71	11.88	18.01	13.22	19.94	15.30	21.54	20.00	23.14
SG	3203	St. Gallen	5.87	6.83	13.50	7.76	15.26	8.78	17.90	10.55	19.40	11.83	19.50	13.04	21.55	15.25	24.07	17.39	25.96	19.19	28.19	21.99	30.39	27.66	31.45
GR	3901	Chur	2.65	4.02	13.60	5.16	14.26	6.15	15.08	8.10	17.86	9.66	19.02	10.85	19.18	12.97	21.46	15.04	23.29	16.86	25.96	19.70	28.25	26.43	30.92
AG	4001	Aarau	4.05	5.29	13.90	6.41	15.42	7.13	13.60	8.72	16.66	10.01	17.76	11.03	18.17	13.00	20.87	15.00	22.99	16.77	25.63	19.71	28.52	27.22	32.23
TG	4566	Frauenfeld	4.97	6.11	14.04	7.00	14.14	7.89	15.88	9.55	17.86	10.75	17.97	11.63	17.78	13.21	19.50	15.02	22.30	16.55	24.17	19.23	27.27	25.95	30.44
TI	5002	Bellinzona	3.82	4.87	12.18	6.15	16.40	7.22	16.86	9.26	19.47	10.86	20.44	12.29	22.31	14.70	24.36	17.12	26.80	19.25	29.89	22.58	32.58	31.07	36.73
VD	5586	Lausanne	2.43	4.41	18.28	6.28	21.22	8.16	25.10	11.89	30.53	13.96	26.42	15.01	22.36	17.00	24.95	19.37	28.83	21.53	32.37	25.32	36.70	35.87	42.90
VS	6266	Sion	2.27	4.56	20.54	7.32	29.44	8.07	14.80	9.70	17.83	11.23	20.47	12.46	21.01	14.95	24.90	17.87	29.58	20.63	34.40	24.90	37.72	31.47	35.85
NE	6458	Neuchâtel	7.25	9.04	21.62	10.51	22.28	11.73	22.72	13.67	23.33	15.06	23.41	16.15	23.76	18.21	26.46	20.45	29.43	22.43	32.34	25.92	36.37	31.94	35.95
GE	6621	Genève	3.97	5.72	17.94	7.21	19.10	8.54	20.58	11.06	23.63	13.09	25.27	14.69	25.87	17.35	28.02	19.94	30.26	21.99	32.26	25.33	35.36	34.33	40.33
JU	6711	Delémont	5.67	6.69	13.86	7.82	16.84	8.80	17.62	10.49	18.95	11.98	20.90	13.36	23.07	15.70	25.05	18.17	28.07	20.36	31.28	23.68	33.63	31.63	36.94
Total Average			4.79	6.00	14.47	7.11	15.96	7.99	15.87	9.63	17.86	10.89	18.45	11.90	18.93	13.76	21.22	15.74	23.66	17.51	26.35	20.48	29.37	27.44	32.08
"""

def _try_float(tok: str):
    try:
        return float(tok)
    except Exception:
        return None

def _parse_table(raw: str) -> Dict[str, List[float]]:
    """Parse the embedded table and return {canton_code: [avg_rate_% at each income]}."""
    out: Dict[str, List[float]] = {}
    lines = [ln.strip() for ln in raw.strip().splitlines()]
    header_seen = False
    for ln in lines:
        if not ln:
            continue
        if not header_seen:
            header_seen = True
            continue  # skip header
        if ln.lower().startswith("total average"):
            continue
        toks = re.split(r"\s+", ln)
        if len(toks) < 5:
            continue
        code = toks[0]
        if code.upper() not in _CANTON_SYNONYMS:
            continue
        # commune spans from index 2 to first numeric
        num_idx = None
        for i in range(2, len(toks)):
            if _try_float(toks[i]) is not None:
                num_idx = i
                break
        if num_idx is None:
            continue
        nums = [_try_float(x) for x in toks[num_idx:]]
        nums = [x for x in nums if x is not None]
        # pick the average-rate positions (skip the "Margin at ..." columns)
        avg_positions = [0,1,3,5,7,9,11,13,15,17,19,21]
        avgs = []
        for pos in avg_positions:
            if pos < len(nums):
                avgs.append(nums[pos])
        if len(avgs) == len(_INCOMES):
            out[code.upper()] = avgs
    return out

_DATA_AVG_RATES_PCT: Dict[str, List[float]] = _parse_table(_TABLE)

def _normalize_canton(canton: str) -> str:
    u = (canton or "").strip().lower()
    # direct 2-letter code
    if len(u) == 2:
        for code in _CANTON_SYNONYMS:
            if u == code.lower():
                return code
    # name matching
    for code, names in _CANTON_SYNONYMS.items():
        for nm in names:
            if u == nm:
                return code
    # loose contains match
    for code, names in _CANTON_SYNONYMS.items():
        for nm in names:
            if nm in u:
                return code
    raise ValueError(f"Unknown canton '{canton}'. Use a 2-letter code (e.g., 'ZH') or a known name (e.g., 'Zürich').")

def _tax_points_for_canton(code: str) -> Tuple[List[float], List[float]]:
    """Return (incomes, taxes) using T(I)=avg_rate(I)*I, avg_rate from table (percent -> decimal)."""
    rates_pct = _DATA_AVG_RATES_PCT.get(code)
    if rates_pct is None:
        raise ValueError(f"No data found for canton code '{code}'.")
    rates_dec = [r/100.0 for r in rates_pct]
    taxes = [r * inc for r, inc in zip(rates_dec, _INCOMES)]
    return _INCOMES, taxes

def _local_slope(income: float, xs: List[float], ys: List[float]) -> float:
    """Local slope dT/dI (decimal) at income using bracketing interval; extrapolate at ends."""
    x = float(income)
    if x <= xs[0]:
        return (ys[1]-ys[0])/(xs[1]-xs[0])
    if x >= xs[-1]:
        return (ys[-1]-ys[-2])/(xs[-1]-xs[-2])
    j = bisect.bisect_left(xs, x)
    if j == 0:
        j = 1
    i = j - 1
    return (ys[j]-ys[i])/(xs[j]-xs[i])

def get_swiss_marginal_rate(income: float, canton: str) -> float:
    """
    Return the marginal income-tax rate (decimal, e.g., 0.1459) at 'income' for the given 'canton'.
    - 'income' in CHF (float/int)
    - 'canton' like 'ZH', 'Zürich', 'Geneva', etc.
    Uses piecewise-linear slope from your canton-specific average-rate table.
    """
    code = _normalize_canton(canton)
    xs, ys = _tax_points_for_canton(code)
    return float(_local_slope(float(income), xs, ys))

from typing import List
from .models import SimulationResult
from .equations import calculate_Lm_max

def validate_result(res: SimulationResult) -> List[str]:
    """
    Check engineering constraints.
    """
    warnings = []
    
    # 1. ZVS Start-up Check (Eq 11)
    # Lm <= Lm_max
    lm_max = calculate_Lm_max(res.specs.deadtime, res.specs.Coss, res.specs.fsw_min)
    if res.tank.Lm > lm_max:
        warnings.append(f"LM ({res.tank.Lm*1e6:.1f}uH) > LM_MAX ({lm_max*1e6:.1f}uH): No ZVS at startup")
        
    # 2. Min Frequency
    if res.fsw < res.specs.fsw_min:
        warnings.append(f"fSW ({res.fsw/1000:.1f}kHz) < fsw_min ({res.specs.fsw_min/1000:.1f}kHz)")
        
    # 3. fN Range
    if res.fN < 0.5 or res.fN > 2.5:
         warnings.append(f"fN ({res.fN:.2f}) outside typical range [0.5, 2.5]")

    # 4. Design Constraints Drift (Ln, Qe)
    # Allow small tolerance (e.g. 1%) for rounding drift, but warn if excessive
    tol = 0.01
    if res.tank.Ln_real < res.specs.Ln_min * (1 - tol) or res.tank.Ln_real > res.specs.Ln_max * (1 + tol):
        warnings.append(f"Ln_real ({res.tank.Ln_real:.2f}) out of bounds [{res.specs.Ln_min}, {res.specs.Ln_max}]")
        
    if res.tank.Qe_real < res.specs.Qe_min * (1 - tol) or res.tank.Qe_real > res.specs.Qe_max * (1 + tol):
        warnings.append(f"Qe_real ({res.tank.Qe_real:.3f}) out of bounds [{res.specs.Qe_min}, {res.specs.Qe_max}]")
         
    return warnings

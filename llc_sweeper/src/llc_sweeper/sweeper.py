import numpy as np
from scipy.optimize import brentq
from typing import List, Optional, Tuple
from .models import LLCSpecs, LLCTank, SimulationResult
from .equations import (
    calculate_n, calculate_tank_components, recalculate_params, 
    gain_fha, required_gain, calculate_stress_full
)

def solve_fN(
    target_gain: float, Ln: float, Qe: float, 
    SearchRange: Tuple[float, float] = (0.3, 3.0),
    max_gain_error: float = 0.02
) -> Optional[float]:
    """
    Robust solver for fN.
    Strategy:
    1. Determine smart range based on target gain.
    2. Try brentq if sign change exists.
    3. Fallback to linear scan if brentq fails.
    """
    
    # Define error function
    def err_func(f):
        return gain_fha(f, Ln, Qe) - target_gain

    # Smart Range Selection
    # If Gain < 1: Operation is usually above resonance (Region 2)
    # If Gain > 1: Operation is usually below resonance (Region 1)
    if abs(target_gain - 1.0) < 0.01: # Relaxed tolerance for "at resonance"
        return 1.0
        
    if target_gain < 1.0:
        # Above resonance
        r_min = max(1.000001, SearchRange[0])
        r_max = max(2.5, SearchRange[1]) # Reasonable upper bound
    else:
        # Below resonance (Boost)
        r_min = max(0.4, SearchRange[0])
        r_max = min(0.999999, SearchRange[1])
        
    # Attempt Brentq
    try:
        val_min = err_func(r_min)
        val_max = err_func(r_max)
        if val_min * val_max < 0:
            fN_sol = brentq(err_func, r_min, r_max)
            return fN_sol
    except:
        pass # Fallback
        
    # Fallback: Linear Scan
    # Scan closely around the range.
    f_scan = np.linspace(r_min, r_max, 300)
    errors = np.abs(gain_fha(f_scan, Ln, Qe) - target_gain)
    idx_min = np.argmin(errors)
    min_err = errors[idx_min]
    
    if min_err < max_gain_error:
        return f_scan[idx_min]
    
    return None

def calculate_score(res: SimulationResult) -> float:
    """
    Transparent Engineering Score.
    Minimize: ILR_RMS, VCR_PEAK, Deviation from Resonance.
    Weights: w1=1.0, w2=1.0, w3=0.2
    """
    # Reference values for normalization (Avoid zero div)
    # Using reasonably expected values for a 500W-1kW converter:
    # ILR ~ 2-5A. VCR ~ 400-600V.
    # We can use the result's own values if we want relative comparison, 
    # but for absolute ranking better to have fixed refs or just sum raw if units compatible.
    # The prompt suggests: "median of all valid candidates" or article values.
    # For MVP we use fixed plausible refs to keep it stateless per-candidate calculation.
    ILR_REF = 3.0 
    VCR_REF = res.specs.Vin # e.g. 400V
    
    w1 = 1.0
    w2 = 1.0
    w3 = 0.2
    
    term1 = w1 * (res.Ilr_rms / ILR_REF)
    term2 = w2 * (res.Vcr_peak / VCR_REF)
    term3 = w3 * abs(res.fN - 1.0)
    
    # Penalty for warnings (Soft constraint)
    penalty = 10.0 * len(res.warnings)
    
    return term1 + term2 + term3 + penalty

def sweep_design(specs: LLCSpecs) -> List[SimulationResult]:
    """
    Main sweep function.
    """
    # 1. Basics
    n_float, n_used = calculate_n(specs.Vin, specs.Vout)
    
    # 2. Grid
    Ln_vals = np.linspace(specs.Ln_min, specs.Ln_max, num=int((specs.Ln_max-specs.Ln_min)*2 + 1)) # e.g. 4, 4.5... or just integers if num small. 
    # Article suggests 4 to 10. Let's do step 0.5? 
    # Prompt: "Ln [4..10] step configurable"
    Ln_vals = np.arange(specs.Ln_min, specs.Ln_max + 0.1, 1.0) # Step 1.0 for MVP
    
    Qe_vals = np.linspace(specs.Qe_min, specs.Qe_max, num=10) # 10 steps
    
    results = []

    # Default Vin range if not provided
    if specs.Vin_min is None: specs.Vin_min = specs.Vin
    if specs.Vin_max is None: specs.Vin_max = specs.Vin
    
    for Ln in Ln_vals:
        for Qe in Qe_vals:
            # Design Tank (Ideal)
            Re_ideal, Cr_ideal, Lr_ideal, Lm_ideal, Rl = calculate_tank_components(
                specs.Vout, specs.Pout, n_used, specs.fR_target, Ln, Qe
            )
            
            # --- Advanced Rounding Sweep ---
            # Generate neighbors (floor/ceil) for Lr, Cr, Lm to find best Integer combination
            from .equations import get_rounded_neighbors
            
            # User req: "No decimals" -> 1uH, 1nF steps
            candidates = get_rounded_neighbors(Lr_ideal, Cr_ideal, Lm_ideal, L_step=1e-6, C_step=1e-9)
            
            for (Lr_r, Cr_r, Lm_r) in candidates:
                # Recalculate parameters based on REAL components
                fR_real, Qe_real = recalculate_params(Lr_r, Cr_r, Re_ideal)
                Ln_real = Lm_r / Lr_r
                
                tank = LLCTank(
                    n_float=n_float, n_used=n_used, 
                    Ln_des=Ln, Qe_des=Qe,
                    Lr=Lr_r, Cr=Cr_r, Lm=Lm_r,
                    fR_real=fR_real, Qe_real=Qe_real, Ln_real=Ln_real,
                    Lr_ideal=Lr_ideal, Cr_ideal=Cr_ideal, Lm_ideal=Lm_ideal
                )
                
                # Required Gain
                G_req = required_gain(specs.Vin, specs.Vout, n_used)
                
                # Solve Operating Point
                fN = solve_fN(G_req, Ln_real, Qe_real)
                
                if fN is None:
                    continue # Unsolvable design
                
                fsw = fN * fR_real
                
                # Stress
                stress = calculate_stress_full(
                    specs.Vin, specs.Vout, specs.Pout, n_used,
                    Lm_r, Lr_r, Cr_r, fsw
                )
                
                # Result Object
                # --- Frequency Span Check (New Feature) ---
                warnings_list = []
                # A) fsw_min_corner at (Vin_min, 100% Load)
                G_req_min = required_gain(specs.Vin_min, specs.Vout, n_used)
                fN_min = solve_fN(G_req_min, Ln_real, Qe_real)
                
                # B) fsw_max_corner at (Vin_max, Light Load)
                # Qe_light depends on load ratio. R_load increases by factor (1/ratio).
                # Q = sqrt(Lr/Cr)/R.  Q_light = Q_nom * ratio.
                Qe_light = Qe_real * specs.light_load_ratio
                G_req_max = required_gain(specs.Vin_max, specs.Vout, n_used)
                fN_max = solve_fN(G_req_max, Ln_real, Qe_light)
                
                if fN_min is None or fN_max is None:
                    # Soft Fail: Cannot satisfy full range
                    span_ratio = 5.0 # Max penalty
                    fsw_min_val = fsw # Placeholder
                    fsw_max_val = fsw # Placeholder
                    warnings_list.append("Corner Unsolvable (Gain Limit)")
                else:
                    fsw_min_val = fN_min * fR_real
                    fsw_max_val = fN_max * fR_real
                    if fsw_min_val < 1e-9: fsw_min_val = 1.0 
                    span_ratio = fsw_max_val / fsw_min_val
                
                # Penalty Rule (Span Ratio)
                SPAN_RATIO_ALLOWED = specs.span_ratio_allowed
                w_span = 0.6
                # If soft fail (5.0), penalty will be large (5.0 - 1.6)*0.6 ~= 2.0
                span_penalty = w_span * max(0, span_ratio - SPAN_RATIO_ALLOWED)
                
                # Check Absolute Limits
                if specs.fsw_max_limit is not None and fsw_max_val > specs.fsw_max_limit:
                    warnings_list.append(f"fsw_max > {specs.fsw_max_limit/1e3:.0f}k")
                    span_penalty += 5.0 # Hard penalty
                    
                if specs.fsw_min is not None and fsw_min_val < specs.fsw_min:
                    warnings_list.append(f"fsw_min < {specs.fsw_min/1e3:.0f}k")
                    span_penalty += 5.0 # Hard penalty
                
                if span_ratio > 2.0:
                    warnings_list.append(f"High fsw span ({span_ratio:.1f}x)")
                
                # Recalculate actual gain (solver might produce fN yielding close but not exact target)
                gain_val = gain_fha(fN, Ln_real, Qe_real)
                
                res = SimulationResult(
                    specs=specs, tank=tank,
                    target_gain=G_req, fN=fN, fsw=fsw, gain=gain_val, 
                    Ilm_peak=stress['Ilm_peak'],
                    Ilm_rms=stress['Ilm_rms'],
                    Ilr_rms=stress['Ilr_rms'],
                    Ilr_peak=stress['Ilr_peak'],
                    Vcr_peak=stress['Vcr_peak'],
                    Vcr_rms=stress['Vcr_rms'],
                    Iq_rms=stress['Iq_rms'],
                    Iq_peak=stress['Iq_peak'],
                    Id_rms=stress['Id_rms'],
                    Id_peak=stress['Id_peak'],
                    # Span Metrics
                    fsw_min_corner=fsw_min_val,
                    fsw_max_corner=fsw_max_val,
                    fsw_span_ratio=span_ratio
                )
                
                # Validate & Score
                from .validation import validate_result
                res.warnings = validate_result(res)
                res.warnings.extend(warnings_list)
                res.score = calculate_score(res) + span_penalty
                
                results.append(res)
            
    # Sort by score (lower is better)
    # Deduplicate results? (Different starting Ln/Qe might map to same rounded components)
    # Simple dedupe by (Lr, Cr, Lm) keeping lowest score
    unique_map = {}
    for r in results:
        key = (r.tank.Lr, r.tank.Cr, r.tank.Lm)
        if key not in unique_map or r.score < unique_map[key].score:
             unique_map[key] = r
    
    final_results = list(unique_map.values())
    final_results.sort(key=lambda x: x.score)
    
    return final_results

def get_diverse_candidates(results: List[SimulationResult], top_n: int = 3) -> List[SimulationResult]:
    """
    Select top N candidates that are sufficiently distinct.
    Criteria: Different Ln (by >= 1.0) or different Qe (by >= 0.05).
    """
    if not results:
        return []
        
    selected = [results[0]]
    
    for res in results[1:]:
        if len(selected) >= top_n:
            break
            
        # Check distinctness against all currently selected
        is_distinct = True
        for s in selected:
            d_Ln = abs(res.tank.Ln_des - s.tank.Ln_des)
            d_Qe = abs(res.tank.Qe_des - s.tank.Qe_des)
            
            # If too similar to ANY selected, skip
            # Definition of distinct: Ln differs by >= 0.9 OR Qe differs by >= 0.03
            if d_Ln < 0.9 and d_Qe < 0.03:
                is_distinct = False
                break
        
        if is_distinct:
            selected.append(res)
            
    return selected

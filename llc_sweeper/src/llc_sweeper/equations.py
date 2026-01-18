import numpy as np
from typing import List

def calculate_n(Vin: float, Vout: float) -> tuple[float, int]:
    """
    Step 2: Transformer turns ratio.
    Eq (1): n = Vin / (2 * Vout * G_resonant)
    At resonance, G = 1.
    
    Returns:
        n_float: calculated value
        n_used: integer rounded value (half-up)
    """
    n_float = Vin / (2 * Vout)
    n_used = int(n_float + 0.5)
    return n_float, n_used

def calculate_Lm_max(t_dead: float, Coss: float, fsw_min: float) -> float:
    """
    Step 3: Maximum magnetizing inductance for ZVS.
    Eq (2): t_sw_min = 1 / (3 * fsw_start_up) approx 1 / (3 * fsw_min) -> Article says tSW_MIN = 1/fSTART_UP
    Article Eq (3): LM_MAX = tSW_MIN * tDEAD_MAX / (16 * COSS)
    
    Warning: Article text says "fSTART_UP is usually 3 times fSW".
    So tSW_MIN term represents the period at max frequency (start up).
    
    The article formula is:
    LM_MAX = (t_dead * T_min) / (16 * Coss)
    """
    # Assuming f_start_up = 3 * fsw_min (typical soft start)
    # The article actually uses fsw_min in the example calculation to derive Lm_max?
    # No, in Step 3 it says "fSTART_UP... approximately 3 x fSW".
    # And "tSW_MIN = 1 / fSTART_UP".
    
    # Example Article: f_sw = 100k. f_start = 300k. t_sw_min = 3.33us.
    # Lm_max = 3.33us * 2us / (16 * 80pF) = 5.2 mH.
    
    f_startup = 3 * fsw_min
    t_sw_min = 1.0 / f_startup
    lm_max = (t_sw_min * t_dead) / (16 * Coss)
    return lm_max

def calculate_required_deadtime(Lm: float, Coss: float, fsw_min: float) -> float:
    """
    Calculate minimum required deadtime for ZVS with given Lm.
    Derived from Eq (3): t_dead = (16 * Coss * Lm) / t_sw_min
    t_sw_min = 1 / (3 * fsw_min) approx (Startup condition)
    """
    f_startup = 3 * fsw_min
    t_sw_min = 1.0 / f_startup
    t_dead_req = (16 * Coss * Lm) / t_sw_min
    return t_dead_req

def calculate_tank_components(
    Vout: float, Pout: float, n: int, fR: float, Ln: float, Qe: float
) -> tuple[float, float, float, float, float]:
    """
    Step 5: Resonant tank selection.
    
    Returns:
        Re, Cr, Lr, Lm, Rl
    """
    # Eq (6)
    Rl = (Vout**2) / Pout
    
    # Eq (7)
    Re = (8 * n**2 / np.pi**2) * Rl
    
    # Eq (8)
    Cr = 1 / (2 * np.pi * fR * Re * Qe)
    
    # Eq (9)
    Lr = 1 / ((2 * np.pi * fR)**2 * Cr)
    
    # Eq (10)
    Lm = Ln * Lr
    
    return Re, Cr, Lr, Lm, Rl

    return Re, Cr, Lr, Lm, Rl

def get_rounded_neighbors(
    Lr: float, Cr: float, Lm: float, 
    L_step: float = 1.0e-6, C_step: float = 1.0e-9
) -> List[tuple[float, float, float]]:
    """
    Get neighbor integer-rounded components (floor and ceil).
    Returns list of (Lr_new, Cr_new, Lm_new) tuples.
    Step: 1uH (1e-6) and 1nF (1e-9) forces 'no decimals' in uH/nF units.
    """
    def get_opts(val, step):
        d = val / step
        lower = int(np.floor(d)) * step
        upper = int(np.ceil(d)) * step
        if lower == upper:
            return [lower]
        return [lower, upper]

    Lr_opts = get_opts(Lr, L_step)
    Cr_opts = get_opts(Cr, C_step)
    Lm_opts = get_opts(Lm, L_step)
    
    import itertools
    combinations = list(itertools.product(Lr_opts, Cr_opts, Lm_opts))
    return combinations

def recalculate_params(Lr: float, Cr: float, Re: float) -> tuple[float, float]:
    """
    Step 6: Recalculation after component selection.
    Returns:
        fR_new, Qe_new
    """
    # Eq (12)
    fR_new = 1 / (2 * np.pi * np.sqrt(Lr * Cr))
    
    # Eq (13)
    Qe_new = 1 / (2 * np.pi * fR_new * Re * Cr)
    
    return fR_new, Qe_new

def gain_fha(fN: float, Ln: float, Qe: float) -> float:
    """
    Step 7: Tank transfer function (M_gain).
    Eq (14):
    M = 1 / sqrt( (1 + 1/Ln * (1 - 1/fN^2))^2 + Qe^2 * (fN - 1/fN)^2 )
    """
    term1 = (1 + (1/Ln) * (1 - 1/(fN**2)))**2
    term2 = (Qe**2) * (fN - 1/fN)**2
    gain = 1 / np.sqrt(term1 + term2)
    return gain

def required_gain(Vin: float, Vout: float, n: int) -> float:
    """
    Eq (16): Required gain to achieve Vout.
    """
    return (Vout * 2 * n) / Vin



def calculate_stress_full(
    Vin: float, Vout: float, Pout: float, n: int, 
    Lm: float, Lr: float, Cr: float, fsw: float
) -> dict:
    """
    Implements Eqs (19) - (28).
    """
    Iout = Pout / Vout
    
    # Eq (19) Peak Magnetizing Current
    Ilm_peak = (n * Vout) / (4 * fsw * Lm)
    Ilm_rms = Ilm_peak / np.sqrt(2) # FHA Sinusoidal Approximation
    
    # Eq (20) Primary Resonant Current RMS
    # Vector sum of Magnetizing RMS (Inductive) and Reflected Load RMS (Resistive)
    # Reflected Load Fundamental RMS:
    # I_load_sq_peak = Iout / n
    # I_load_fund_peak = (4/pi) * I_load_sq_peak
    # I_load_fund_rms = I_load_fund_peak / sqrt(2) = (2*sqrt(2)/pi) * (Iout/n)
    # Wait, (2*sqrt(2)/pi) approx 0.9003.
    # User article form: sqrt( Ilm_rms^2 + (pi^2/8)*(Iout/n)^2 ) ?
    # Let's check: (pi^2/8) = 1.233. sqrt(1.233) = 1.11. 
    # (4/pi * 1/sqrt(2))? No. 
    # Let's use the standard analytical FHA form:
    # I_load_rms_pri = (np.pi / (2 * np.sqrt(2))) * (Iout / n)
    # This matches commonly accepted FHA.
    I_load_rms_pri = (np.pi * Iout) / (2 * np.sqrt(2) * n)
    
    Ilr_rms = np.sqrt(Ilm_rms**2 + I_load_rms_pri**2)
    
    # Eq (21) Peak Primary Current
    Ilr_peak = np.sqrt(2) * Ilr_rms
    
    # Eq (22) Resonant Capacitor Voltage
    # VCR (AC RMS) = ILR_RMS / (2 * pi * fsw * Cr)
    Vcr_rms = Ilr_rms / (2 * np.pi * fsw * Cr)
    
    # Physical Peak Voltage (DC Bias + AC Peak)
    Vcr_peak = (Vin / 2) + (np.sqrt(2) * Vcr_rms)
    
    # Secondary Currents (Rectified Sine approximation)
    Id_peak = (Iout * np.pi) / 2
    Id_rms = Id_peak / 2 
    
    # Primary Switch Currents
    Iq_peak = Ilr_peak
    Iq_rms = Ilr_rms / np.sqrt(2)
    
    return {
        "Ilm_peak": Ilm_peak,
        "Ilm_rms": Ilm_rms,
        "Ilr_rms": Ilr_rms,
        "Ilr_peak": Ilr_peak,
        "Vcr_peak": Vcr_peak,
        "Vcr_rms": Vcr_rms, # Added for completeness
        "Iq_rms": Iq_rms,
        "Iq_peak": Iq_peak,
        "Id_rms": Id_rms,
        "Id_peak": Id_peak
    }


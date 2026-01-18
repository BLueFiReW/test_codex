from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np

@dataclass
class LLCSpecs:
    """
    Input specifications for the LLC Converter.
    Units: Volts, Watts, Hz, Farads, Henrys, seconds.
    """
    Vin: float       # Input voltage (V)
    Vout: float      # Output voltage (V)
    Pout: float      # Output power (W)
    fR_target: float # Target resonant frequency (Hz)
    fsw_min: float   # Minimum switching frequency (Hz)
    Coss: float      # Output capacitance of MOSFETs (F)
    deadtime: float  # Dead time (s)
    
    # Optional constraints / config
    Ln_min: float = 4.0
    Ln_max: float = 10.0
    Qe_min: float = 0.33
    Qe_max: float = 0.50
    
    # Range Inputs for Span Check
    Vin_min: float = None
    Vin_max: float = None
    fsw_max_limit: float = None # Max allowed switching frequency (e.g. at light load)
    # Penalty Config
    span_ratio_allowed: float = 1.6
    light_load_ratio: float = 0.20 # 20%
    @property
    def Iout(self) -> float:
        return self.Pout / self.Vout

@dataclass
class LLCTank:
    """
    Designed tank parameters.
    """
    # Primary inputs
    n_float: float
    n_used: int
    Ln_des: float
    Qe_des: float
    
    # Components
    Lr: float # Henry (Selected/Real)
    Cr: float # Farad (Selected/Real)
    Lm: float # Henry (Selected/Real)
    
    # Recalculated values
    fR_real: float # Hz
    Qe_real: float
    Ln_real: float

    # Ideal Values (for reference)
    Lr_ideal: float = 0.0
    Cr_ideal: float = 0.0
    Lm_ideal: float = 0.0

@dataclass
class SimulationResult:
    """
    Simulation results for a specific operating point.
    """
    specs: LLCSpecs
    tank: LLCTank
    
    # Operating point
    target_gain: float
    fN: float
    fsw: float
    gain: float
    
    # Stress values
    Ilm_peak: float
    Ilm_rms: float # Added
    Ilr_rms: float
    Ilr_peak: float
    Vcr_peak: float # DC + AC Peak
    Vcr_rms: float  # AC RMS (Article Eq 22)
    Iq_rms: float # Primary switch RMS (Q1, Q2)
    Iq_peak: float # Primary switch Peak (Q1, Q2)
    Id_rms: float # Secondary rectifier RMS (Q3, Q4)
    Id_peak: float # Secondary rectifier Peak (Q3, Q4)
    
    # Frequency Span Metrics
    fsw_min_corner: float = 0.0
    fsw_max_corner: float = 0.0
    fsw_span_ratio: float = 1.0
    
    # Scoring
    score: float = 0.0
    valid: bool = True
    warnings: List[str] = field(default_factory=list)


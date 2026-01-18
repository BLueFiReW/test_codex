
import pytest
from llc_sweeper.models import LLCSpecs
from llc_sweeper.sweeper import sweep_design

def test_span_penalty_calculation():
    """
    Test that wide frequency span increases score via penalty.
    """
    # 1. Wide Specs (but realistic enough to have solutions)
    specs = LLCSpecs(
        Vin=400.0, Vout=48.0, Pout=600.0,
        fR_target=100e3, fsw_min=50e3,
        Coss=100e-12, deadtime=200e-9,
        Ln_min=2.0, Ln_max=8.0, 
        Qe_min=0.15, Qe_max=0.5,
        # 395-405V check
        Vin_min=395.0, Vin_max=405.0
    )
    
    results_wide = sweep_design(specs)
    print(f"Wide Results count: {len(results_wide)}")
    assert len(results_wide) > 0, "No valid designs found for range 395-405V"
    
    res_wide = results_wide[0]
    print(f"Wide Span Ratio: {res_wide.fsw_span_ratio:.2f}")
    
    assert res_wide.fsw_span_ratio > 1.0, f"Span ratio {res_wide.fsw_span_ratio} should be > 1.0"
    
    # 2. Narrow Specs (Basically fixed Vin)
    specs_narrow = LLCSpecs(
        Vin=400.0, Vout=48.0, Pout=600.0,
        fR_target=100e3, fsw_min=50e3,
        Coss=100e-12, deadtime=200e-9,
        Ln_min=2.0, Ln_max=8.0,
        Qe_min=0.15, Qe_max=0.5,
        # Very narrow range
        Vin_min=399.9, Vin_max=400.1
    )
    
    results_narrow = sweep_design(specs_narrow)
    print(f"Narrow Results count: {len(results_narrow)}")
    assert len(results_narrow) > 0
    
    res_narrow = results_narrow[0]
    print(f"Narrow Span Ratio: {res_narrow.fsw_span_ratio:.2f}")
    
    assert res_wide.fsw_span_ratio > res_narrow.fsw_span_ratio, "Wide span should be greater than narrow span"
    
    # Check that fsw_max_corner (Light Load, High Vin) is indeed high
    print(f"Corner check: Min {res_wide.fsw_min_corner/1e3:.1f}k, Max {res_wide.fsw_max_corner/1e3:.1f}k")
    assert res_wide.fsw_max_corner > res_wide.fsw_min_corner

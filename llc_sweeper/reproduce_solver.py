
import numpy as np
from llc_sweeper.sweeper import sweep_design
from llc_sweeper.models import LLCSpecs

def test_full_sweep():
    # Failing Wide Specs from test_span.py
    specs = LLCSpecs(
        Vin=400.0, Vout=48.0, Pout=600.0,
        fR_target=100e3, fsw_min=50e3,
        Coss=100e-12, deadtime=200e-9,
        Ln_min=2.0, Ln_max=8.0, 
        Qe_min=0.15, Qe_max=0.5,
        # 395-405V
        Vin_min=395.0, Vin_max=405.0
    )
    
    print("Running Sweep...")
    results = sweep_design(specs)
    print(f"Results: {len(results)}")
    
    if len(results) > 0:
        best = results[0]
        print(f"Best Span: {best.fsw_span_ratio}")
        print(f"Best fN_min: {best.fsw_min_corner/100e3:.2f}")
        print(f"Best fN_max: {best.fsw_max_corner/100e3:.2f}")
        if best.warnings:
            print(f"Warnings: {best.warnings}")

if __name__ == "__main__":
    test_full_sweep()

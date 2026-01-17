import argparse
import sys
from .models import LLCSpecs
from .sweeper import sweep_design
from .plotting import plot_gain_curves
import matplotlib.pyplot as plt

def main():
    parser = argparse.ArgumentParser(description="LLC Design Sweeper")
    parser.add_argument("--example", action="store_true", help="Run with article example specs")
    parser.add_argument("--vin", type=float, help="Input Voltage", default=400)
    parser.add_argument("--vout", type=float, help="Output Voltage", default=48)
    parser.add_argument("--pout", type=float, help="Power Output", default=600)
    parser.add_argument("--fr", type=float, help="Target Resonant Freq (Hz)", default=100e3)
    parser.add_argument("--fsw-min", type=float, help="Min Switching Freq (Hz)", default=50e3)
    
    args = parser.parse_args()
    
    if args.example:
        print("Running Article Example...")
        specs = LLCSpecs(
            Vin=400, Vout=48, Pout=600,
            fR_target=100e3,
            fsw_min=50e3,
            Coss=80e-12,
            deadtime=2e-6, # 2us
            Ln_min=4, Ln_max=10
        )
    else:
        # Minimal CLI input support
        specs = LLCSpecs(
            Vin=args.vin, Vout=args.vout, Pout=args.pout,
            fR_target=args.fr,
            fsw_min=args.fsw_min,
            Coss=80e-12, # Hardcoded defaults for MVP
            deadtime=2e-6
        )

    print(f"\n--- Design Specifications ---")
    print(f"Vin: {specs.Vin} V, Vout: {specs.Vout} V, Pout: {specs.Pout} W")
    print(f"fR: {specs.fR_target/1000} kHz, fsw_min: {specs.fsw_min/1000} kHz")
    
    results = sweep_design(specs)
    
    if not results:
        print("No valid designs found!")
        sys.exit(1)

    print(f"\nFound {len(results)} candidates. Top 3 (Diverse):")
    
    from .sweeper import get_diverse_candidates
    top_candidates = get_diverse_candidates(results, top_n=3)
    
    for i, res in enumerate(top_candidates):
        t = res.tank
        print(f"\nCandidate #{i+1} (Score: {res.score:.4f})")
        print(f"  Tank: Ln={t.Ln_real:.2f} (des {t.Ln_des}), Qe={t.Qe_real:.3f} (des {t.Qe_des})")
        print(f"  Components: n={t.n_used}, "
              f"Lr={t.Lr*1e6:.1f}uH, "
              f"Cr={t.Cr*1e9:.1f}nF, "
              f"Lm={t.Lm*1e6:.1f}uH")
        print(f"  Operating Point: fN={res.fN:.3f}, fsw={res.fsw/1000:.2f} kHz, Gain={res.gain:.3f}")
        print(f"  Stress: ILR_RMS={res.Ilr_rms:.2f}A, VCR_PK={res.Vcr_peak:.1f}V")
        
        if res.warnings:
            print(f"  Warnings: {res.warnings}")

    # Plot
    # plot_gain_curves(results)
    # plt.show() # Not in headless

if __name__ == "__main__":
    main()

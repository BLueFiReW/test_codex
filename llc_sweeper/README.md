LLC Design Sweeper ⚡

A Python tool for designing and sweeping parameters for a Half-Bridge LLC Resonant Converter with a Center-Tapped Transformer.

This project solves the LLC operating point using an FHA gain model and ranks candidate tanks using an engineering-oriented score (stress + resonance + frequency-span constraints).

Features

Engineering-Grade Physics

FHA gain model: Gain(fN, Ln, Qe)

Explicit checks for ZVS feasibility and component stress

Clear separation between:

Article-level AC RMS stress

Component-rating peak stress (includes DC bias)

Robust Sweeper

Sweeps and ranks Ln and Qe

Uses a robust solver (brentq + fallback scan) to avoid crashes and keep near-miss solutions visible

Multiple Interfaces

CLI for fast engineering workflows

Jupyter Notebook (notebooks/P2_demo.ipynb) for exploration and plots

Streamlit Web UI for an interactive design experience

Quickstart
1) Install (CLI / Core Logic)
pip install -e .

2) Install (Web UI / Streamlit)
pip install -r requirements.txt
pip install -e .

Run Streamlit

Launch the interactive web app:

streamlit run streamlit_app.py

Usage
CLI

Run the reference example:

python -m llc_sweeper.cli --example

Notebook

Open:

notebooks/P2_demo.ipynb

Scoring Methodology ("The Score")

Each valid design is ranked using a weighted Cost Function.
A lower score means a better (more practical) design.

Base Score Formula
Score = w1*(ILR_rms / Iref)
      + w2*(VCr_peak / Vref)
      + w3*abs(fN - 1.0)
      + Penalty

What each term means

Efficiency Metric (w1 = 1.0)
Minimizes Primary RMS Current (ILR_rms), which typically dominates conduction losses (MOSFETs + transformer).

Cost/Size Metric (w2 = 1.0)
Minimizes peak voltage on the resonant capacitor (VCr_peak), allowing smaller/cheaper capacitors.

Resonance Fidelity (w3 = 0.2)
Favors operation close to fN = 1.0 (peak-efficiency region), while still allowing deviation if needed.

Penalty (+10.0 per warning)
Soft constraints: if rounding pushes Ln or Qe slightly outside user limits (>1%), the design is penalized but not discarded, so you can still inspect near-miss options.

Frequency Span Penalty (Engineering Constraint)

In real hardware, a good LLC tank is not only low-stress at one operating point, but also does not require an excessive switching-frequency span across realistic conditions.

Why frequency span matters

Designs that require a very large switching-frequency span often:

complicate control and compensation,

increase EMI and audible noise risks,

operate far from resonance more often,

and may increase losses and stress in real hardware.

How fsw span is estimated

We estimate the required frequency range using two operating corners per candidate:

Minimum frequency corner (fsw_min_corner)

Vin = Vin_min

Pout = 100% rated load

Maximum frequency corner (fsw_max_corner)

Vin = Vin_max

Pout = 20% rated load

The 20% load point is used as a practical threshold where most LLC controllers still operate in continuous steady-state switching.
Below this level, many controllers enter burst/skip modes, where an effective continuous switching frequency is not well-defined.

For each corner:

Compute required gain G_req

Solve normalized frequency fN (robust root finding: brentq + fallback scan)

Compute switching frequency:
fsw = fN * fR_real

Span metrics

We compute:

fsw_span_ratio = fsw_max_corner / fsw_min_corner

fsw_span_kHz = (fsw_max_corner - fsw_min_corner) / 1e3

Penalty rule

A soft penalty is applied when the span ratio exceeds a recommended threshold:

SPAN_RATIO_ALLOWED = 1.6

span_penalty = w_span * max(0, fsw_span_ratio - SPAN_RATIO_ALLOWED)
TotalScore   = BaseScore + span_penalty


The UI shows fsw_min_corner, fsw_max_corner, and fsw_span_ratio for each candidate.

Notes & Limitations

The model is based on FHA equations and is intended for fast feasibility ranking.

Final designs should be validated with time-domain simulation and hardware measurements.

Light-load behavior depends on the controller (burst/skip transitions), so the 20% threshold is an engineering approximation.


OpenMagnetics Integration (P2.1)

This tool includes an experimental integration with **OpenMagnetics** to propose real core/winding stacks for the top candidates.

### Key Features
- **Separate Design Approach (MVP)**: Designs the Transformer and Resonant Inductor as distinct components to ensure robustness.
- **Physics-Driven**: Uses the swept $L_m$, $L_r$, turns ratio $n$, and calculated RMS currents ($I_{Lr,rms}$, $I_{Lm,rms}$) as inputs.
- **Waveform Approximation**: Models excitation as Sinusoidal (currents) and Square-wave (voltages) for estimating core and winding losses using the OpenMagnetics MKF engine.

### How to Enable
1. Install the optional dependency:
   ```bash
   pip install PyOpenMagnetics
   ```
   *(Also included in `requirements.txt`)*
2. Run the Streamlit UI.
3. In the "Results" area, verify the **Best Candidate**.
4. Go to the **🧲 Magnetics** tab and click **"Design Magnetics for Best Candidate"**.
5. The tool will propose top core/winding combinations and update the efficiency score with estimated magnetic losses.

License


MIT
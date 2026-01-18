# LLC Design Sweeper

A Python tool for designing and sweeping parameters for a Half-Bridge LLC Resonant Converter with a Center-Tapped Transformer.

## Features
- **Engineering-Grade Physics**: Follows strict equations for Gain, ZVS, and Stress.
- **Robust Sweeper**: Optimizes $L_n$ and $Q_e$ to minimize stress and deviation from resonance.
- **Interactive**: CLI for quick design, Jupyter Notebook for full analysis.

## Installation

**For CLI (Core Logic):**
```bash
pip install -e .
```

**For Web UI (Streamlit):**
```bash
pip install -r requirements.txt
pip install -e .
```

## Run Streamlit
To launch the interactive web application:
```bash
streamlit run streamlit_app.py
```

## Usage

### CLI
Run with the article example:
```bash
python -m llc_sweeper.cli --example
```

### Notebook
Explore designs in `notebooks/P2_demo.ipynb`.

## Scoring Methodology ("The Score")
The tool ranks every valid design using a weighted **Cost Function**. A **lower score** means a better design.

$$ Score = w_1 \cdot \frac{I_{LR,rms}}{I_{ref}} + w_2 \cdot \frac{V_{Cr,peak}}{V_{ref}} + w_3 \cdot |f_N - 1.0| + Penalty $$

Where:
1.  **Efficiency Metric ($w_1=1.0$)**: Minimizes Primary RMS Current ($I_{LR}$), which dominates conduction losses (MOSFETs + Transformer).
2.  **Cost/Size Metric ($w_2=1.0$)**: Minimizes Peak Voltage on the Resonant Capacitor ($V_{Cr}$), allowing for smaller/cheaper capacitors.
3.  **Resonance Fidelity ($w_3=0.2$)**: Favors designs operating close to $f_N=1.0$ (Peak Efficiency point), though some deviation is allowed.
4.  **Penalty ($+10.0$ per warning)**: Soft constraints. If a design requires rounding that pushes $L_n$ or $Q_e$ slightly outside the user's limits ($>1\%$), it is heavily penalized but not discarded, so you can see "near-miss" options.

## Frequency Span Penalty (Engineering Constraint)

This tool ranks LLC tank candidates not only by electrical stress (RMS currents / capacitor voltage) but also by **how much switching frequency variation** is required across realistic operating conditions.

### Why frequency span matters
Designs that require a very large switching-frequency span often:
- complicate control and compensation,
- increase EMI and audible noise risks,
- operate far from resonance more often,
- and may increase losses or stress in real hardware.

### How fsw span is estimated
We estimate the required frequency range using two operating corners per candidate:

- **Minimum frequency corner (fsw_min_corner):**
  - `Vin = Vin_min`
  - `Pout = 100% rated load`

- **Maximum frequency corner (fsw_max_corner):**
  - `Vin = Vin_max`
  - `Pout = 20% rated load`

> The 20% load point is used as a practical threshold where most LLC controllers operate in continuous steady-state switching.
> Below this level, many controllers enter burst/skip modes, where an effective continuous switching frequency is not well-defined.

For each corner:
1. Compute required gain `G_req`
2. Solve normalized frequency `fN` with robust root finding (brentq + fallback scan)
3. Compute switching frequency:
   `fsw = fN * fR_real`

### Span metrics
We compute:
- `fsw_span_ratio = fsw_max_corner / fsw_min_corner`
- `fsw_span_kHz = (fsw_max_corner - fsw_min_corner)/1e3`

### Penalty rule
A soft penalty is applied when the span ratio exceeds a recommended threshold:

- `SPAN_RATIO_ALLOWED = 1.6`

Penalty:
`span_penalty = w_span * max(0, fsw_span_ratio - SPAN_RATIO_ALLOWED)`

Total score:
`TotalScore = BaseScore + span_penalty`

The UI shows `fsw_min_corner`, `fsw_max_corner`, and `fsw_span_ratio` for each candidate.

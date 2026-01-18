# LLC Design Sweeper

A Python tool for designing and sweeping parameters for a Half-Bridge LLC Resonant Converter with a Center-Tapped Transformer.

## Features
- **Engineering-Grade Physics**: Follows strict equations for Gain, ZVS, and Stress.
- **Robust Sweeper**: Optimizes $L_n$ and $Q_e$ to minimize stress and deviation from resonance.
- **Interactive**: CLI for quick design, Jupyter Notebook for full analysis.

## Installation

```bash
pip install -e .
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

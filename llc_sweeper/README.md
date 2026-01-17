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

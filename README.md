# Power Electronics Design Tools

Welcome to this repository containing advanced engineering tools for Power Electronics design.

## 🚀 Featured Projects

### 1. [LLC Design Sweeper](llc_sweeper/)
**A Robust, Engineering-Grade Design Tool for Half-Bridge LLC Resonant Converters.**

This tool automates the design process of LLC converters with Center-Tapped transformers, replacing manual Excel calculations with a rigorous Python-based sweep.

**Key Features:**
*   **Physics-Based Solver**: Uses strict FHA equations to guarantee ZVS and Gain.
*   **Smart Sweeper**: Optimizes $L_n$ and $Q_e$ for efficiency and stability.
*   **Interactive UI**: Full Streamlit Web App with dynamic metric cards and data sheets.
*   **Advanced Constraints**: Handles Frequency Span Penalty, Light Load regulation, and Component Stress analysis.

#### Quick Start (Web UI)
```bash
cd llc_sweeper
pip install -r requirements.txt
streamlit run streamlit_app.py
```

<div align="center">
  <em>Navigate to the <code>llc_sweeper</code> directory for full documentation.</em>
</div>

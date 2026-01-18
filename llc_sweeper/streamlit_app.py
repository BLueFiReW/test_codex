import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Import our package
# Assuming the file is running from the root where 'src' is available or installed
try:
    from llc_sweeper.models import LLCSpecs
    from llc_sweeper.sweeper import sweep_design, get_diverse_candidates, solve_fN
    from llc_sweeper.equations import gain_fha, calculate_stress_full, calculate_required_deadtime
except ImportError:
    # Handle case where src is local but not installed (e.g. Streamlit Cloud standard repo structure)
    import sys
    import os
    # Robustly add 'src' relative to this script file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(current_dir, "src")
    if src_path not in sys.path:
        sys.path.append(src_path)
    from llc_sweeper.models import LLCSpecs
    from llc_sweeper.sweeper import sweep_design, get_diverse_candidates, solve_fN
    from llc_sweeper.equations import gain_fha, calculate_stress_full, calculate_required_deadtime

st.set_page_config(
    page_title="LLC Design Sweeper",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Aesthetics ---
# Custom CSS for "bonito pero sencillo"
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        border-radius: 8px;
        height: 3em;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 10px;
        color: #000000; /* Force black text */
    }
    .metric-card h3 { color: #000000 !important; }
    .metric-card p { color: #000000 !important; }
    h1 { color: inherit; } /* Let Streamlit handle main headers */
    h2 { color: inherit; } 
    h3 { color: inherit; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ LLC Design Sweeper")
st.markdown("Automated design and parameter sweep for Half-Bridge LLC Resonant Converters.")

# --- Sidebar: Specifications ---
with st.sidebar:
    st.header("1. Design Specifications")
    
    with st.expander("Input/Output", expanded=True):
        col1, col2 = st.columns(2)
        Vin = col1.number_input("Vin (V)", value=400.0, step=10.0)
        Vout = col2.number_input("Vout (V)", value=48.0, step=1.0)
        Pout = st.number_input("Pout (W)", value=600.0, step=50.0)
    
    with st.expander("Frequencies & Components", expanded=True):
        fR_target = st.number_input("Target Resonance fR (kHz)", value=100.0, step=5.0) * 1e3
        fsw_min = st.number_input("Min Switching fsw (kHz)", value=50.0, step=5.0) * 1e3
        Coss_pF = st.number_input("MOSFET Coss (pF)", value=80.0, step=10.0)
        t_dead_us = st.number_input("Max Deadtime (us)", value=2.0, step=0.1)
    
    with st.expander("Sweep Range", expanded=False):
        Ln_min = st.slider("Ln Min", 2.0, 10.0, 4.0)
        Ln_max = st.slider("Ln Max", 5.0, 20.0, 10.0)
        Qe_min = st.slider("Qe Min", 0.1, 1.0, 0.33)
        Qe_max = st.slider("Qe Max", 0.2, 2.0, 0.5)

    run_btn = st.button("🚀 Run Sweep")

# --- Logic ---

if run_btn:
    with st.spinner("Sweeping designs..."):
        # 1. Specs
        specs = LLCSpecs(
            Vin=Vin, Vout=Vout, Pout=Pout,
            fR_target=fR_target, fsw_min=fsw_min,
            Coss=Coss_pF * 1e-12, deadtime=t_dead_us * 1e-6,
            Ln_min=Ln_min, Ln_max=Ln_max,
            Qe_min=Qe_min, Qe_max=Qe_max
        )
        
        # 2. Run
        results = sweep_design(specs)
        
        if not results:
            st.error("No valid designs found within these constraints. Try widening the sweep range.")
        else:
            top_candidates = get_diverse_candidates(results, top_n=3)
            
            # --- Results Area ---
            st.success(f"Sweep Complete! Found {len(results)} valid candidates. Showing Top {len(top_candidates)} Diverse Options.")
            
            # Store in session state for persistence if needed (simple app doesn't need it if running on button)
            
            # Display Top Candidates in Cards
            cols = st.columns(len(top_candidates))
            
            selected_cand = None
            
            for i, (col, res) in enumerate(zip(cols, top_candidates)):
                t = res.tank
                with col:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Candidate #{i+1}</h3>
                        <p><b>Score:</b> {res.score:.3f}</p>
                        <hr>
                        <p><b>Ln:</b> {t.Ln_real:.2f} | <b>Qe:</b> {t.Qe_real:.3f}</p>
                        <p>n = {t.n_used}</p>
                        <p>Lr = {t.Lr*1e6:.1f} uH</p>
                        <p>Cr = {t.Cr*1e9:.1f} nF</p>
                        <p>Lm = {t.Lm*1e6:.1f} uH</p>
                        <hr>
                        <p><b>Stress (RMS):</b></p>
                        <p>Pri: {res.Ilr_rms:.2f} A</p>
                        <p>Cap: {res.Vcr_peak:.0f} V</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Tabs for Analysis
            tab1, tab2, tab3 = st.tabs(["📈 Gain Curves", "🔧 Resonance Tuner (Vin Adjust)", "📋 Data Sheet"])
            
            # --- Tab 1: Plots ---
            with tab1:
                st.subheader("Gain vs Normalized Frequency")
                
                fig, ax = plt.subplots(figsize=(10, 5))
                fN_range = np.linspace(0.4, 2.5, 500)
                
                for i, res in enumerate(top_candidates):
                    curve = gain_fha(fN_range, res.tank.Ln_real, res.tank.Qe_real)
                    ax.plot(fN_range, curve, label=f"Cand #{i+1} (Ln={res.tank.Ln_real:.1f}, Qe={res.tank.Qe_real:.2f})")
                    ax.scatter([res.fN], [res.gain], marker='o')
                    
                ax.axhline(top_candidates[0].target_gain, color='r', linestyle='--', label='Target Gain')
                ax.set_ylim(bottom=0)
                ax.grid(True, alpha=0.3)
                ax.set_xlabel("Normalized Frequency ($f_N$)")
                ax.set_ylabel("Gain (M)")
                ax.legend()
                ax.autoscale(enable=True, axis='y')
                
                st.pyplot(fig)
                
            # --- Tab 2: Resonance Tuner ---
            with tab2:
                st.subheader("Achieving Perfect Resonance ($f_N=1$)")
                st.markdown("""
                Due to integer rounding of the transformer turns ratio ($n$), the operating point ($f_N$) often drifts from 1.0. 
                We can adjust the **Input Voltage** to restore perfect resonance.
                """)
                
                # Pick best candidate
                best = top_candidates[0]
                n_used = best.tank.n_used
                Vin_ideal = 2 * n_used * specs.Vout
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.info(f"**Current Input:** {specs.Vin} V")
                    st.write(f"Operating $f_N$: **{best.fN:.3f}**")
                    st.write(f"Turns Ratio usage: **n={n_used}**")
                
                with col_b:
                    st.success(f"**Ideal Input:** {Vin_ideal:.1f} V")
                    st.write("Target $f_N$: **1.000**")
                    st.write("(Matching $M=1$ for $n={{{}}}$)".format(n_used))
                
                # Recalculate
                fsw_new = best.tank.fR_real
                new_stress = calculate_stress_full(
                    Vin=Vin_ideal, Vout=specs.Vout, Pout=specs.Pout,
                    n=best.tank.n_used, Lm=best.tank.Lm, Lr=best.tank.Lr, Cr=best.tank.Cr, fsw=fsw_new
                )
                
                st.markdown("### Recalculated Stresses at Resonance")
                st.metric("Primary RMS Current", f"{new_stress['Ilr_rms']:.2f} A", delta=f"{new_stress['Ilr_rms'] - best.Ilr_rms:.2f} A", delta_color="inverse")
                
            # --- Tab 3: Data Sheet ---
            with tab3:
                st.subheader("Detailed Parameters (Best Candidate)")
                
                # Calculate Deadtime Req
                t_dead_req = calculate_required_deadtime(best.tank.Lm, specs.Coss, specs.fsw_min)
                
                ds_data = {
                    "Parameter": [
                        "Input Voltage (Nominal)", "Input Voltage (Ideal Resonance)", "Output Voltage", "Output Power",
                        "Transformer Ratio (n)", "Resonant Inductor (Lr)", "Resonant Capacitor (Cr)", "Magnetizing Inductor (Lm)",
                        "Resonant Freq (fR)", "Quality Factor (Qe)", "Inductance Ratio (Ln)",
                        "Pri RMS Current", "Mag RMS Current", "Res Cap Peak Volts", "Required Deadtime (ZVS)"
                    ],
                    "Value": [
                        f"{specs.Vin} V", f"{Vin_ideal:.1f} V", f"{specs.Vout} V", f"{specs.Pout} W",
                        f"{best.tank.n_used}", f"{best.tank.Lr*1e6:.1f} uH", f"{best.tank.Cr*1e9:.1f} nF", f"{best.tank.Lm*1e6:.1f} uH",
                        f"{best.tank.fR_real/1e3:.2f} kHz", f"{best.tank.Qe_real:.3f}", f"{best.tank.Ln_real:.2f}",
                        f"{best.Ilr_rms:.2f} A", f"{best.Ilm_rms:.2f} A", f"{best.Vcr_peak:.1f} V", 
                        f"{t_dead_req*1e6:.3f} us (Max {specs.deadtime*1e6:.1f})"
                    ]
                }
                
                st.table(pd.DataFrame(ds_data))

else:
    st.info("👈 Adjust specifications in the sidebar and click **Run Sweep** to start.")

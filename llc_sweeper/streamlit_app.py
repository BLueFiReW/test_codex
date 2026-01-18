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
        c3, c4 = st.columns(2)
        Ln_min = c3.number_input("Ln Min", value=4.0, min_value=1.5, max_value=20.0, step=0.5)
        Ln_max = c4.number_input("Ln Max", value=10.0, min_value=1.5, max_value=20.0, step=0.5)
        
        c5, c6 = st.columns(2)
        Qe_min = c5.number_input("Qe Min", value=0.33, min_value=0.1, max_value=2.0, step=0.01)
        Qe_max = c6.number_input("Qe Max", value=0.50, min_value=0.1, max_value=2.0, step=0.01)

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
            best = top_candidates[0] # Define 'best' globally for all tabs
            
            # --- Results Area ---
            st.success(f"Sweep Complete! Found {len(results)} valid candidates. Showing Top {len(top_candidates)} Diverse Options.")
            
            # Store in session state for persistence if needed (simple app doesn't need it if running on button)
            
            # Display Top Candidates in Cards
            cols = st.columns(len(top_candidates))
            
            selected_cand = None
            
            for i, (col, res) in enumerate(zip(cols, top_candidates)):
                t = res.tank
                warn_html = ""
                if res.warnings:
                    warn_html = f"<div style='color:red; font-size:0.8em; margin-top:5px; border-top:1px solid #ffcccc; padding-top:2px;'>⚠️ {', '.join(res.warnings)}</div>"

                with col:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Candidate #{i+1}</h3>
                        {warn_html}
                        <p><b>Score:</b> {res.score:.3f}</p>
                        <hr style="margin: 5px 0;">
                        <p><b>Ln:</b> {t.Ln_real:.2f} | <b>Qe:</b> {t.Qe_real:.3f}</p>
                        <p>n = {t.n_used} <span style='font-size:0.8em; color:#666;'>(id. {t.n_float:.2f})</span></p>
                        <p>Lr = {t.Lr*1e6:.1f} uH</p>
                        <p>Cr = {t.Cr*1e9:.1f} nF</p>
                        <p>Lm = {t.Lm*1e6:.1f} uH</p>
                        <hr style="margin: 5px 0;">
                        <p><b>Stress:</b></p>
                        <p>Pri RMS: {res.Ilr_rms:.2f} A</p>
                        <p>Cap RMS: {res.Vcr_rms:.1f} V</p>
                        <p>Cap Pk: {res.Vcr_peak:.0f} V</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Tabs for Analysis
            tab1, tab2, tab3, tab4 = st.tabs(["📈 Gain Curves", "🔧 Resonance Tuner (Vin Adjust)", "📋 Data Sheet", "🏆 Full Leaderboard"])
            
            # --- Tab 1: Plots ---
            with tab1:
                st.subheader("Gain vs Normalized Frequency")
                
                # Futuristic Style Context
                with plt.style.context('dark_background'):
                    fig, ax = plt.subplots(figsize=(10, 5))
                    fig.patch.set_facecolor('#0E1117') 
                    ax.set_facecolor('#0E1117')
                    
                    fN_range = np.linspace(0.4, 2.5, 500)
                    colors = ['#00FFFF', '#FF00FF', '#00FF00'] # Cyan, Magenta, Lime
                    
                    for i, res in enumerate(top_candidates):
                        color = colors[i % len(colors)]
                        curve = gain_fha(fN_range, res.tank.Ln_real, res.tank.Qe_real)
                        
                        # "Glow" effect
                        ax.plot(fN_range, curve, color=color, linewidth=4, alpha=0.3)
                        ax.plot(fN_range, curve, color=color, linewidth=2, label=f"#{i+1}: Ln={res.tank.Ln_real:.1f}, Qe={res.tank.Qe_real:.2f}")
                        
                        # Neon Scatter
                        ax.scatter([res.fN], [res.gain], color='white', edgecolor=color, s=80, zorder=5)
                        
                    ax.axhline(top_candidates[0].target_gain, color='#FF4B4B', linestyle='--', linewidth=1, label='Target Gain')
                    ax.set_ylim(bottom=0)
                    
                    # Custom Grid
                    ax.grid(True, color='#444444', linestyle='--', linewidth=0.5, alpha=0.5)
                    
                    # Remove spines
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['left'].set_color('#888888')
                    ax.spines['bottom'].set_color('#888888')
                    ax.tick_params(colors='#888888')
                    
                    ax.set_xlabel("Normalized Frequency ($f_N$)", color='white', fontsize=10)
                    ax.set_ylabel("Gain (M)", color='white', fontsize=10)
                    
                    # Legend with dark background
                    legend = ax.legend(frameon=False)
                    plt.setp(legend.get_texts(), color='#CCCCCC')
                    
                    ax.autoscale(enable=True, axis='y')
                    
                    st.pyplot(fig)
            
            # --- Tab 2: Resonance Tuner ---
            with tab2:
                st.subheader("Achieving Perfect Resonance ($f_N=1$)")
                st.markdown("""
                Due to integer rounding of the transformer turns ratio ($n$), the operating point ($f_N$) often drifts from 1.0. 
                We can adjust the **Input Voltage** to restore perfect resonance.
                """)
                
                # 'best' is already defined above
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
                
                # Plot Adjustment
                st.markdown("### Operating Point Shift")
                
                with plt.style.context('dark_background'):
                    fig2, ax2 = plt.subplots(figsize=(10, 5))
                    fig2.patch.set_facecolor('#0E1117')
                    ax2.set_facecolor('#0E1117')
                    
                    fN_range = np.linspace(0.4, 2.5, 500)
                    curve = gain_fha(fN_range, best.tank.Ln_real, best.tank.Qe_real)
                    
                    # Solve exact fN for ideal case (should be 1.0 but verifying)
                    fN_new = 1.0 
                    
                    # Neon Curve
                    color_curve = '#00FFFF' # Cyan
                    ax2.plot(fN_range, curve, color=color_curve, linewidth=4, alpha=0.3) # Glow
                    ax2.plot(fN_range, curve, color=color_curve, linewidth=2, label='Gain Curve')
                    
                    # Points with Glow
                    # Red Original
                    ax2.scatter([best.fN], [best.gain], color='#FF4B4B', s=150, zorder=5, label=f'Original: fN={best.fN:.2f}')
                    ax2.scatter([best.fN], [best.gain], color='#FF4B4B', s=400, alpha=0.3, zorder=4) # Glow ring
                    
                    # Green Adjusted
                    ax2.scatter([fN_new], [1.0], color='#00FF00', marker='*', s=200, zorder=5, label=f'Adjusted: fN=1.00')
                    ax2.scatter([fN_new], [1.0], color='#00FF00', marker='*', s=500, alpha=0.3, zorder=4) # Glow ring
                    
                    ax2.axhline(1.0, linestyle='--', color='#888888', linewidth=1, alpha=0.5)
                    ax2.axvline(1.0, linestyle='--', color='#888888', linewidth=1, alpha=0.5)
                    
                    # Styling
                    ax2.grid(True, color='#444444', linestyle='--', linewidth=0.5, alpha=0.5)
                    ax2.spines['top'].set_visible(False)
                    ax2.spines['right'].set_visible(False)
                    ax2.spines['left'].set_color('#888888')
                    ax2.spines['bottom'].set_color('#888888')
                    ax2.tick_params(colors='#888888')
                    
                    ax2.set_xlabel("Normalized Frequency ($f_N$)", color='white')
                    ax2.set_ylabel("Gain (M)", color='white')
                    
                    legend = ax2.legend(frameon=False)
                    plt.setp(legend.get_texts(), color='#CCCCCC')
                    
                    ax2.autoscale(enable=True, axis='y')
                    
                    st.pyplot(fig2)
                
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
                        "Pri RMS Current (Total)", "Mag RMS Current", "Res Cap Peak Volts", "Required Deadtime (ZVS)",
                        "Pri Switch Current (Peak)", "Pri Switch Current (RMS)",
                        "Sec Diode Current (Peak)", "Sec Diode Current (RMS)"
                    ],
                    "Value": [
                        f"{specs.Vin} V", f"{Vin_ideal:.1f} V", f"{specs.Vout} V", f"{specs.Pout} W",
                        f"{best.tank.n_used}", f"{best.tank.Lr*1e6:.1f} uH", f"{best.tank.Cr*1e9:.1f} nF", f"{best.tank.Lm*1e6:.1f} uH",
                        f"{best.tank.fR_real/1e3:.2f} kHz", f"{best.tank.Qe_real:.3f}", f"{best.tank.Ln_real:.2f}",
                        f"{best.Ilr_rms:.2f} A", f"{best.Ilm_rms:.2f} A", f"{best.Vcr_peak:.1f} V", 
                        f"{t_dead_req*1e6:.3f} us (Max {specs.deadtime*1e6:.1f})",
                        f"{best.Iq_peak:.2f} A", f"{best.Iq_rms:.2f} A",
                        f"{best.Id_peak:.2f} A", f"{best.Id_rms:.2f} A"
                    ]
                }
                
                st.table(pd.DataFrame(ds_data))

            # --- Tab 4: Leaderboard ---
            with tab4:
                st.subheader("Top 20 Candidates")
                
                # Create DataFrame
                # Flatten objects
                lb_data = []
                for r in results[:20]: # Top 20
                    lb_data.append({
                        "Rank": len(lb_data)+1,
                        "Score": f"{r.score:.3f}",
                        "Ln": f"{r.tank.Ln_real:.2f}",
                        "Qe": f"{r.tank.Qe_real:.3f}",
                        "Lr (uH)": f"{r.tank.Lr*1e6:.1f}",
                        "Cr (nF)": f"{r.tank.Cr*1e9:.1f}",
                        "Lm (uH)": f"{r.tank.Lm*1e6:.1f}",
                        "fN": f"{r.fN:.3f}",
                        "fsw (kHz)": f"{r.fsw/1e3:.1f}",
                        "Pri RMS (A)": f"{r.Ilr_rms:.2f}",
                        "Warnings": ", ".join(r.warnings) if r.warnings else "OK"
                    })
                
                st.dataframe(pd.DataFrame(lb_data), use_container_width=True)

else:
    st.info("👈 Adjust specifications in the sidebar and click **Run Sweep** to start.")

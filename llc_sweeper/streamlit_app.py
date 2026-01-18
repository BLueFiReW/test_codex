import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import textwrap

# Import our package
# Assuming the file is running from the root where 'src' is available or installed
try:
    from llc_sweeper.models import LLCSpecs
    from llc_sweeper.sweeper import sweep_design, get_diverse_candidates, solve_fN, calculate_score
    from llc_sweeper.equations import gain_fha, calculate_stress_full, calculate_required_deadtime
    from llc_sweeper.magnetics.openmagnetics_adapter import design_transformer_openmagnetics, design_resonant_inductor_openmagnetics, is_openmagnetics_available
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
        background-color: #161616;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
        margin-bottom: 10px;
        color: #ffffff;
    }
    .metric-card h3 { color: #ffffff !important; margin-bottom: 5px; }
    .metric-card p { color: #e0e0e0 !important; margin: 2px 0; }
    .metric-card hr { border-color: #333; margin: 8px 0; }
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
        Vin = col1.number_input("Vin Nom (V)", value=400.0, step=10.0)
        Vout = col2.number_input("Vout (V)", value=48.0, step=1.0)
        
        c3, c4 = st.columns(2)
        Vin_min = c3.number_input("Vin Min (V)", value=380.0, step=10.0)
        Vin_max = c4.number_input("Vin Max (V)", value=420.0, step=10.0)
        
        Pout = st.number_input("Pout (W)", value=600.0, step=50.0)
    
    with st.expander("Frequencies & Components", expanded=True):
        fR_target = st.number_input("Target Resonance fR (kHz)", value=100.0, step=5.0) * 1e3
        fsw_min = st.number_input("Min Switching fsw (kHz)", value=50.0, step=5.0) * 1e3
        Coss_pF = st.number_input("MOSFET Coss (pF)", value=80.0, step=10.0)
        t_dead_us = st.number_input("Max Deadtime (us)", value=2.0, step=0.1)
    
    with st.expander("Sweep Range & Constraints", expanded=False):
        c3, c4 = st.columns(2)
        Ln_min = c3.number_input("Ln Min", value=4.0, min_value=1.5, max_value=20.0, step=0.5)
        Ln_max = c4.number_input("Ln Max", value=10.0, min_value=1.5, max_value=20.0, step=0.5)
        
        c5, c6 = st.columns(2)
        Qe_min = c5.number_input("Qe Min", value=0.33, min_value=0.1, max_value=2.0, step=0.01)
        Qe_max = c6.number_input("Qe Max", value=0.50, min_value=0.1, max_value=2.0, step=0.01)
        
        st.markdown("**Frequency Limits**")
        c7, c8 = st.columns(2)
        # fsw_min is already in Frequencies section, but maybe user wants it here?
        # Let's just add fsw_max_limit here.
        fsw_max_limit = c7.number_input("Max fsw (kHz) @ Light Load", value=300.0, step=10.0) * 1e3

    with st.expander("Advanced Config", expanded=False):
         span_ratio_allowed = st.slider("Max Allowed Span Ratio (Score Penalty)", 1.0, 3.0, 1.6, 0.1)
         light_load_pct = st.slider("Light Load Definition (%)", 5, 50, 20, 5)
         light_load_ratio = light_load_pct / 100.0

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
            Qe_min=Qe_min, Qe_max=Qe_max,
            Vin_min=Vin_min, Vin_max=Vin_max,
            fsw_max_limit=fsw_max_limit,
            span_ratio_allowed=span_ratio_allowed,
            light_load_ratio=light_load_ratio
        )
        
        # 2. Run
        results = sweep_design(specs)
        
        if not results:
            st.error("No valid designs found within these constraints. Try widening the sweep range.")
        else:
            # --- Results Area ---
            st.success(f"Sweep Complete! Found {len(results)} valid candidates.")
            
            # Top Summary
            best = results[0]
            m1, m2, m3 = st.columns(3)
            m1.metric("Best Candidate Span", f"{best.fsw_span_ratio:.2f}x")
            warn_count = len(best.warnings)
            m2.metric("Warnings", f"{warn_count}", delta_color="inverse" if warn_count > 0 else "normal")
            m3.metric("Efficiency Score", f"{best.score:.3f}")
            st.markdown("---")
            
            top_candidates = get_diverse_candidates(results, top_n=3)
            # best is results[0], usually same as top_candidates[0] if logic aligns
            
            st.markdown(f"**Showing Top {len(top_candidates)} Diverse Options:**")
            
            # Display Top Candidates in Cards
            cols = st.columns(len(top_candidates))
            
            selected_cand = None
            
            for i, (col, res) in enumerate(zip(cols, top_candidates)):
                t = res.tank
                warn_html = ""
                if res.warnings:
                    warn_html = f"<div style='color:#FF6666; font-size:0.8em; margin-top:5px; border-top:1px solid #550000; padding-top:2px;'>⚠️ {', '.join(res.warnings)}</div>"

                with col:
                    # Use list join to prevent markdown indentation issues
                    html_list = [
                        '<div class="metric-card">',
                        f'<h3>Candidate #{i+1}</h3>',
                        f'{warn_html}',
                        f'<p><b>Score:</b> {res.score:.3f}</p>',
                        '<hr>',
                        f'<p><b>L<sub>n</sub>:</b> {t.Ln_real:.2f} | <b>Q<sub>e</sub>:</b> {t.Qe_real:.3f}</p>',
                        f'<p>n = {t.n_used} <span style="font-size:0.8em; color:#888;">(id. {t.n_float:.2f})</span></p>',
                        f'<p>L<sub>r</sub> = {t.Lr*1e6:.1f} &mu;H</p>',
                        f'<p>C<sub>r</sub> = {t.Cr*1e9:.1f} nF</p>',
                        f'<p>L<sub>m</sub> = {t.Lm*1e6:.1f} &mu;H</p>',
                        '<hr>',
                        f'<p><b>Span:</b> {res.fsw_span_ratio:.2f}x <span style="font-size:0.8em; color:#888;">({res.fsw_min_corner/1e3:.0f}-{res.fsw_max_corner/1e3:.0f} kHz)</span></p>',
                        '<hr>',
                        f'<p><b>Stress:</b></p>',
                        f'<p>Pri RMS: {res.Ilr_rms:.2f} A</p>',
                        f'<p>Cap RMS: {res.Vcr_rms:.1f} V</p>',
                        f'<p>Cap Pk: {res.Vcr_peak:.0f} V</p>',
                        '</div>'
                    ]
                    st.markdown("\n".join(html_list), unsafe_allow_html=True)
            
            # Tabs for Analysis
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Gain Curves", "🔧 Resonance Tuner (Vin Adjust)", "📋 Data Sheet", "🏆 Full Leaderboard", "🧲 Magnetics (OpenMagnetics)"])
            
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
                        "fsw Min (Corner)", "fsw Max (Corner)", "Span Ratio",
                        "Lr RMS Current", "Lm RMS Current", 
                        "Res Cap RMS Voltage (Article Eq 22)", "Res Cap Peak Voltage (Component Rating)",
                        "Required Deadtime (ZVS)",
                        "Pri Switch Current (Peak)", "Pri Switch Current (RMS)",
                        "Sec Diode Current (Peak)", "Sec Diode Current (RMS)"
                    ],
                    "Value": [
                        f"{specs.Vin} V", f"{Vin_ideal:.1f} V", f"{specs.Vout} V", f"{specs.Pout} W",
                        f"{best.tank.n_used} (ideal eps: {abs(best.tank.n_float - best.tank.n_used):.3f})", 
                        f"{best.tank.Lr*1e6:.1f} uH", f"{best.tank.Cr*1e9:.1f} nF", f"{best.tank.Lm*1e6:.1f} uH",
                        f"{best.tank.fR_real/1e3:.2f} kHz", f"{best.tank.Qe_real:.3f}", f"{best.tank.Ln_real:.2f}",
                        f"{best.fsw_min_corner/1e3:.1f} kHz (@ {specs.Vin_min}V, 100%)",
                        f"{best.fsw_max_corner/1e3:.1f} kHz (@ {specs.Vin_max}V, {light_load_pct}%)",
                        f"{best.fsw_span_ratio:.2f}x",
                        f"{best.Ilr_rms:.2f} A", f"{best.Ilm_rms:.2f} A", 
                        f"{best.Vcr_rms:.2f} V", f"{best.Vcr_peak:.1f} V", 
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
                        "fsw Max": f"{r.fsw_max_corner/1e3:.1f}",
                        "Span (x)": f"{r.fsw_span_ratio:.2f}",
                        "Pri RMS (A)": f"{r.Ilr_rms:.2f}",
                        "Warnings": ", ".join(r.warnings) if r.warnings else "OK"
                    })
                
                st.dataframe(pd.DataFrame(lb_data), use_container_width=True)

            # --- Tab 5: Magnetics ---
            with tab5:
                st.subheader("🧲 Automated Magnetics Design")
                
                if not is_openmagnetics_available():
                    st.warning("OpenMagnetics is not available. This feature requires the `PyOpenMagnetics` library.")
                    st.info("To enable this feature, install optional dependencies:\n\n`pip install -r requirements.txt`")
                else:
                    st.markdown("""
                    **Experimental Feature (P2.1)**: Uses OpenMagnetics to propose core and winding configurations.
                    
                    **Targets:**
                    *   **Transformer**: Split-Bobbin or Standard (ETD, PQ, RM) to match $L_m$ and turns ratio $n$.
                    *   **Resonant Inductor**: Gapped core options to match $L_r$.
                    """)
                    
                    if st.button("✨ Design Magnetics for Best Candidate"):
                        with st.spinner("Calling OpenMagnetics Design Adviser..."):
                            # Run Design
                            # Transformer
                            tx_res = design_transformer_openmagnetics(specs, best, corner="full_load")
                            best.transformer_design = tx_res
                            
                            # Inductor
                            ind_res = design_resonant_inductor_openmagnetics(specs, best, corner="full_load")
                            best.resonant_inductor_design = ind_res
                            
                            # Update Score (if valid)
                            # We assume metrics are populated
                            # Calculate total magnetics loss
                            tx_loss = tx_res["metrics"].get("total_loss_W", 0.0)
                            ind_loss = ind_res["metrics"].get("total_loss_W", 0.0)
                            total_mag_loss = tx_loss + ind_loss
                            best.magnetics_loss_total_W = total_mag_loss
                            
                            # Calc penalty
                            # w_mag = 0.5, ref = 10W
                            best.magnetics_penalty = 0.5 * (total_mag_loss / 10.0)
                            
                            # Check adapter warnings
                            if tx_res.get("warnings"): best.magnetics_warnings.extend(tx_res["warnings"])
                            if ind_res.get("warnings"): best.magnetics_warnings.extend(ind_res["warnings"])
                            
                            # Re-Score
                            best.score = calculate_score(best)
                            
                            st.success(f"Magnetics Designed! Total Loss: {total_mag_loss:.2f} W. New Score: {best.score:.3f}")
                            
                            if tx_res["status"] == "fail":
                                st.error(f"Transformer Design Failed: {tx_res['errors']}")
                            if ind_res["status"] == "fail":
                                st.error(f"Inductor Design Failed: {ind_res['errors']}")
                                
                            # Display Details
                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown("### Transformer Design")
                                st.json(tx_res)
                            with c2:
                                st.markdown("### Resonant Inductor")
                                st.json(ind_res)

else:
    st.info("👈 Adjust specifications in the sidebar and click **Run Sweep** to start.")

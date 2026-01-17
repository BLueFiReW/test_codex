import matplotlib.pyplot as plt
import numpy as np
from typing import List
from .models import SimulationResult
from .equations import gain_fha

def plot_gain_curves(candidates: List[SimulationResult], top_n: int = 3, ylim: tuple = None):
    """
    Plot Gain vs fN for top candidates.
    """
    plt.figure(figsize=(10, 6))
    
    fN_range = np.linspace(0.4, 2.5, 500)
    
    for i, res in enumerate(candidates[:top_n]):
        gain_curve = gain_fha(fN_range, res.tank.Ln_real, res.tank.Qe_real)
        
        label = (f"#{i+1}: Ln={res.tank.Ln_real:.2f}, Qe={res.tank.Qe_real:.3f}, "
                 f"fN={res.fN:.2f}")
        plt.plot(fN_range, gain_curve, label=label)
        
        # Mark operating point
        plt.scatter([res.fN], [res.gain], marker='o')
        
    # Target Gain Line (using the first candidate's target, they should be similar)
    if candidates:
        target = candidates[0].target_gain
        plt.axhline(y=target, color='r', linestyle='--', label=f'Target G={target:.2f}')
        
    plt.xlabel("Normalized Frequency ($f_N$)")
    plt.ylabel("Voltage Gain (M)")
    plt.title("Gain Curves of Top Candidates")
    plt.grid(True, which='both', alpha=0.3)
    plt.legend()
    
    if ylim:
        plt.ylim(ylim)
    else:
        # Fully dynamic: Matplotlib will autoscale both limits to fit the data
        plt.autoscale(enable=True, axis='y')
    
    # Save or Show?
    # CLI tool will probably not show window. 
    # We leave it to the caller (Notebook or savefig).
    return plt.gcf()

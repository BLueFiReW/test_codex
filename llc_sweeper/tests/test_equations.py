import pytest
import numpy as np
from llc_sweeper.equations import (
    calculate_n, calculate_Lm_max, calculate_tank_components, 
    recalculate_params, gain_fha, calculate_stress_full
)

# Article Example Values
VIN = 400.0
VOUT = 48.0
POUT = 600.0
FR = 100e3
FSW_MIN = 50e3
COSS = 80e-12
DEADTIME = 2e-6 # 2us - wait article says deadtime max 2us? 
# Article Step 3: tDEAD_MAX = 2us.

def test_unit_conversions():
    """Verify basic SI unit assumptions."""
    assert 100e3 == 100000
    assert 47e-9 == 0.000000047
    assert 2e-6 == 0.000002

def test_step2_n():
    """Test Transformer Ratio (Eq 1)."""
    n_float, n_used = calculate_n(VIN, VOUT)
    # 400 / (2 * 48 * 1) = 4.1666...
    assert n_float == pytest.approx(4.1666, 0.001)
    assert n_used == 4

def test_step3_lm_max():
    """Test Lm Max (Eq 2, 3)."""
    # f_start = 3 * 50k = 150k. t_sw_min = 6.66us? 
    # Wait, Article Example:
    # "f_START_UP is usually 3 x f_SW" -> f_SW here refers to resonant freq? or min freq?
    # "t_SW_MIN = 1 / f_START_UP"
    # "LM_MAX = t_SW_MIN * t_DEAD_MAX / (16 * COSS)"
    #
    # Let's check article example numbers if present.
    # The article doesn't explicitly compute Lm_max in the example text, 
    # but later selects Lm = 243uH. 
    # The constraint usually yields something larger (e.g. 1-5 mH).
    # Let's just trust valid inputs.
    
    lm_max = calculate_Lm_max(DEADTIME, COSS, FSW_MIN)
    # f_startup = 150k. t_sw_min = 6.66e-6.
    # lm_max = 6.66e-6 * 2e-6 / (16 * 80e-12)
    # = 1.33e-11 / 1.28e-9 ~= 10.4e-3 (10.4 mH)
    assert lm_max > 0.001

def test_step5_tank_selection():
    """Test Tank Selection (Eq 6-10) with Article inputs."""
    # From Article:
    # n=4
    # Ln=9 (selected)
    # Qe=0.35 (selected)
    # fR=100k
    
    n = 4
    Ln = 9.0
    Qe = 0.35
    
    Re, Cr_calc, Lr_calc, Lm_calc, Rl = calculate_tank_components(
        VOUT, POUT, n, FR, Ln, Qe
    ) 
    
    # Rl = 48^2 / 600 = 3.84
    assert Rl == pytest.approx(3.84, 0.01)
    
    # Re = (8 * 16 / 9.86) * 3.84 = (128/9.86)*3.84 ~= 12.97 * 3.84 ~= 49.8
    # Article says Re=49.8
    assert Re == pytest.approx(49.8, 0.1)
    
    # Cr = 1 / (2pi * 100k * 49.8 * 0.35) 
    # = 1 / (628318 * 17.43) = 1 / 10951582 ~= 91.3 nF
    # Article selects Cr = 94nF (2x 47nF).
    assert Cr_calc == pytest.approx(91.3e-9, 0.1e-9)
    
    # Lr = ? 
    # From Eq 9: 1/((2pi*100k)^2 * 91.3e-9)
    # = 1 / (3.94e11 * 9.13e-8) = 1 / 36000 ~= 27.7 uH
    # Article says 27uH.
    assert Lr_calc == pytest.approx(27.7e-6, 0.5e-6)
    
    # Lm = 9 * 27.7 = 249 uH
    # Article says 243uH (using 27uH).
    assert Lm_calc == pytest.approx(249e-6, 5e-6)

def test_gain_fha_resonance():
    """Test Gain at resonance (fN=1)."""
    # G(1, Ln, Qe) should be 1.0 regardless of Ln/Qe
    g = gain_fha(1.0, 9.0, 0.35)
    assert g == pytest.approx(1.0, 0.0001)

def test_gain_fha_example_point():
    """Test Gain at off-resonance point."""
    # From article plot or logic
    # Try fN=1.2, Ln=9, Qe=0.35
    g = gain_fha(1.2, 9.0, 0.35)
    # Expected behavior: Gain < 1
    assert g < 1.0
    assert g > 0.8
    
    # Try fN=0.8 (Boost)
    g_boost = gain_fha(0.8, 9.0, 0.35)
    assert g_boost > 1.0


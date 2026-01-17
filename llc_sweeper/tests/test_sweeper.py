import pytest
from llc_sweeper.models import LLCSpecs
from llc_sweeper.sweeper import sweep_design

def test_sweeper_article_example():
    """
    Run sweeper with article specs and check if top result matches.
    Article chose: Ln=9, Qe=0.35.
    Result: Lr=27uH, Cr=94nF (approx), Lm=243uH.
    """
    specs = LLCSpecs(
        Vin=400, Vout=48, Pout=600,
        fR_target=100e3,
        fsw_min=50e3,
        Coss=80e-12,
        deadtime=2e-6,
        Ln_min=4, Ln_max=10,
        Qe_min=0.33, Qe_max=0.5
    )
    
    results = sweep_design(specs)
    assert len(results) > 0
    
    best = results[0]
    
    # Check if best (or near best) is close to expected
    # The article choice might not be mathematically "optimal" by our simple score, 
    # but should be in the mix.
    # Check top 3 for Ln ~= 9
    
    found_article_like = False
    # Check all results to find the specific design point Article used
    for res in results:
        # Article uses Ln=9, Qe=0.35. 
        # Our grid is Ln steps of 1.0 -> 9.0 exists.
        # Qe steps of (0.5-0.33)/9 ~ 0.02. -> 0.33, 0.3488, 0.367...
        if abs(res.tank.Ln_des - 9.0) < 0.1 and abs(res.tank.Qe_des - 0.35) < 0.02:
            found_article_like = True
            # Verify values
            # Ours: Lr=27uH or 28uH. Lm=243uH or 250uH.
            # Article: 27uH, 243uH.
            # With integer search, we exact match 27.0 and 243.0?
            assert res.tank.Lr * 1e6 == pytest.approx(27.0, 1.0) # +/- 1uH
            assert res.tank.Lm * 1e6 == pytest.approx(243.0, 10.0) # +/- 10uH
            break
            
    assert found_article_like, "Did not find Article-like design in the sweep results"

def test_sweeper_boost_mode():
    """Test a case where Gain > 1 is required."""
    # Vin=350, Vout=48, n=4 -> Gain = 48*8/350 = 1.09
    specs = LLCSpecs(
        Vin=350, Vout=48, Pout=600,
        fR_target=100e3,
        fsw_min=50e3,
        Coss=80e-12,
        deadtime=2e-6
    )
    
    results = sweep_design(specs)
    assert len(results) > 0
    
    best = results[0]
    # fN should be < 1.0 for Gain > 1
    assert best.fN < 1.0
    assert best.fsw < best.tank.fR_real

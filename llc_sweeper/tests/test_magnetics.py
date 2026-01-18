
import pytest
from unittest.mock import MagicMock
from llc_sweeper.magnetics.openmagnetics_adapter import design_transformer_openmagnetics, design_resonant_inductor_openmagnetics, is_openmagnetics_available

def test_adapter_failure_mode_safe():
    """
    Test that the adapter handles missing dependencies or internal errors 
    gracefully by returning a strict dictionary with 'status': 'fail'.
    """
    # Mock specs and res
    specs = MagicMock()
    res = MagicMock()
    
    # 1. Test Transformer
    tx_res = design_transformer_openmagnetics(specs, res)
    assert isinstance(tx_res, dict)
    assert "status" in tx_res
    assert "metrics" in tx_res
    # If OM is not installed, it should fail
    if not is_openmagnetics_available():
         assert tx_res["status"] == "fail"
         assert "OpenMagnetics not installed" in tx_res["errors"][0]
    else:
         # If it is installed (unlikely in this env), it returns fail or stub 
         # unless we implemented the real logic.
         # Current stub logic returns fail.
         assert tx_res["status"] == "fail"

    # 2. Test Inductor
    ind_res = design_resonant_inductor_openmagnetics(specs, res)
    assert isinstance(ind_res, dict)
    assert ind_res["status"] == "fail"

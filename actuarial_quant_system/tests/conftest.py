import os
import sys

# Put the package root (actuarial_quant_system/) on the path so `import src...`
# resolves and the modules' relative imports work.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.risk_gate import pre_trade_check as gate


@pytest.fixture(autouse=True)
def _reset_kill_switch():
    """The kill switch is a module-level latch; reset around every test."""
    gate.reset_kill_switch()
    yield
    gate.reset_kill_switch()

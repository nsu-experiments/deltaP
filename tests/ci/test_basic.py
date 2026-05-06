"""Basic CI tests for ΔP interpreter"""
import pytest
from pathlib import Path

def test_import_interpreter():
    """Test that interpreter module can be imported"""
    from interpreter.deltaP_interpreter import DeltaPInterpreter
    assert DeltaPInterpreter is not None

def test_examples_exist():
    """Test that example files exist"""
    examples = Path('examples')
    assert examples.exists()
    assert (examples / 'traffic_simulation.dp').exists()
    assert (examples / 'emergency_decision.dp').exists()
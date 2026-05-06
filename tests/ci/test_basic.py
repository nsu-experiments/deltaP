"""Basic CI tests for ΔP interpreter"""
import pytest
from pathlib import Path

def test_import_interpreter():
    """Test that interpreter module can be imported"""
    from interpreter.delta_interpreter import DeltaInterpreter
    assert DeltaInterpreter is not None

def test_interpreter_file_exists():
    """Test that interpreter file exists"""
    interpreter_file = Path('interpreter/delta_interpreter.py')
    assert interpreter_file.exists()

def test_example_files_exist():
    """Test that example .dp files exist"""
    root = Path('.')
    dp_files = list(root.rglob('*.dp'))
    assert len(dp_files) > 0, "No .dp example files found"
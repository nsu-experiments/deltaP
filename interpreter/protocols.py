# interpreter/protocols.py
from __future__ import annotations
from typing import Protocol, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .hdf5_manager import HDF5Manager

class InterpreterProtocol(Protocol):
    vars: Dict[str, Any]
    hdf5: HDF5Manager 
    warnings_enabled: bool
# interpreter/protocols.py
from typing import Protocol, Dict, Any

class InterpreterProtocol(Protocol):
    vars: Dict[str, Any]
    hdf5: 'HDF5Manager'
    warnings_enabled: bool
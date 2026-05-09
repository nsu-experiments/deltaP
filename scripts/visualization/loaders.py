# scripts/visualization/loaders.py
"""
Data loading utilities for ΔP visualization pipeline.
Handles CSV and HDF5 formats with metadata extraction.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
import h5py


def load_csv_with_metadata(path: Path) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load CSV and extract embedded metadata from comment lines.
    
    Returns:
        (DataFrame, metadata_dict)
    """
    metadata = {}
    
    with open(path, 'r') as f:
        for line in f:
            if line.startswith('# META:'):
                # Parse metadata (future: JSON format)
                meta_str = line.replace('# META:', '').strip()
                # For now, just store raw string
                metadata['raw'] = meta_str
            elif not line.startswith('#'):
                break
    
    df = pd.read_csv(path, comment='#')
    return df, metadata


def load_simulation_results(results_dir: Path) -> Dict[str, pd.DataFrame]:
    """
    Load all result CSVs from a results directory.
    
    Returns:
        dict mapping filename stem to DataFrame
    """
    results = {}
    
    for csv_file in results_dir.glob('*.csv'):
        df, metadata = load_csv_with_metadata(csv_file)
        results[csv_file.stem] = df
    
    return results


def load_hdf5_table(path: Path, table_name: str) -> pd.DataFrame:
    """
    Load a specific table from HDF5 database.
    """
    with h5py.File(path, 'r') as f:
        if table_name not in f:
            raise KeyError(f"Table '{table_name}' not found in {path}")
        
        dataset = f[table_name]
        # Convert HDF5 compound dtype to DataFrame
        df = pd.DataFrame(dataset[:])
    
    return df
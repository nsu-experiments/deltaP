#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HDF5 database manager for storing dynamic predicate data.
"""

from typing import Tuple, List, Dict
import h5py
import numpy as np


class HDF5Manager:
    """Manages HDF5 database for dynamic predicate storage"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.h5file = h5py.File(filename, 'a')

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self) -> None:
        """Close the HDF5 file"""
        self.h5file.close()

    def create_predicate(self, name: str, arity: int) -> None:
        """Create a dataset for a dynamic predicate"""
        if name in self.h5file:
            return
        fields = [(f'arg{i}', 'int64') for i in range(arity)] + [('value', 'int8')]
        self.h5file.create_dataset(
            name, 
            shape=(0,), 
            dtype=np.dtype(fields), 
            maxshape=(None,)
        )

    def set_value(self, pred: str, args: Tuple[int, ...], value: int) -> None:
        """
        Set a value for a predicate with given arguments.
        value: 0 (false), 1 (true), 2 (undef/delete)
        """
        ds = self.h5file[pred]
        arity = len([f for f in ds.dtype.names if f.startswith('arg')])
        
        # Find existing entry
        idx = None
        for i, row in enumerate(ds):
            if all(row[f'arg{j}'] == args[j] for j in range(arity)):
                idx = i
                break
        
        # Delete if undef
        if value == 2:
            if idx is not None:
                new_data = np.delete(ds[:], idx, axis=0)
                ds.resize((len(new_data),))
                ds[:] = new_data
            return
        
        # Update or insert
        row = tuple(args) + (value,)
        if idx is not None:
            ds[idx] = row
        else:
            ds.resize((ds.shape[0] + 1,))
            ds[-1] = row

    def get_all_entries(self, pred: str) -> List[Tuple[Tuple[int, ...], int]]:
        """
        Get all entries for a predicate.
        Returns: [(args_tuple, value), ...]
        """
        ds = self.h5file[pred]
        arity = len([f for f in ds.dtype.names if f.startswith('arg')])
        result = []
        for row in ds:
            if row['value'] in (0, 1):
                args = tuple(row[f'arg{i}'] for i in range(arity))
                result.append((args, int(row['value'])))
        return result

    def get_stats(self, pred: str) -> Dict[str, int]:
        """Return statistics about predicate data"""
        ds = self.h5file[pred]
        true_count = sum(1 for row in ds if row['value'] == 1)
        false_count = sum(1 for row in ds if row['value'] == 0)
        undef_count = sum(1 for row in ds if row['value'] == 2)
        return {
            'true': true_count,
            'false': false_count,
            'undef': undef_count,
            'total': true_count + false_count + undef_count
        }
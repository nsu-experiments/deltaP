#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV exporter for simulation and decision results.
"""

from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
import os


class CSVExporter:
    """Exports interpreter results to timestamped CSV files"""
    
    def __init__(self, base_name: str):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Check for custom results directory from environment
        results_dir = os.environ.get('DELTAP_RESULTS_DIR', 'results')
        
        # Create results directory if it doesn't exist
        os.makedirs(results_dir, exist_ok=True)
        
        self.filename = f"{results_dir}/{base_name}_{timestamp}.csv"
        self.rows: List[Dict[str, Any]] = []

    def add_row(self, data: Dict[str, Any]) -> None:
        """Add a row of data to be exported"""
        self.rows.append(data)
    
    def write(self) -> None:
        """Write collected rows to CSV file"""
        if not self.rows:
            return
        df = pd.DataFrame(self.rows)
        df.to_csv(self.filename, index=False)
        print(f"Results exported to {self.filename}")
    
    def clear(self) -> None:
        """Clear collected rows"""
        self.rows = []
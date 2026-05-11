#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
populate_logistics_data.py

"""

import sys
sys.path.insert(0, 'interpreter')

from interpreter.hdf5_manager import HDF5Manager

def populate_data(db_file='delta_db_synthetic.h5'):
    """Populate database with training data for logistics predicates"""
    
    with HDF5Manager(db_file) as db:
        # Create predicates for simulation mode (arity = 3: route, scenario, month)
        db.create_predicate('meets_efficiency', 3)
        db.create_predicate('meets_service_quality', 3)
        db.create_predicate('meets_carbon_limit', 3)
        db.create_predicate('shows_adaptability', 3)
        db.create_predicate('maintains_resilience', 3)
        
        # Create predicates for decision mode (arity = 2: route, scenario)
        # These need multiple rows with SAME args to create probabilities
        db.create_predicate('prob_meets_efficiency', 2)
        db.create_predicate('prob_meets_service_quality', 2)
        db.create_predicate('prob_meets_carbon_limit', 2)
        db.create_predicate('prob_shows_adaptability', 2)
        db.create_predicate('prob_maintains_resilience', 2)
        
        print("Populating database with training data...")
        print()
        
        # =====================================================================
        # SIMULATION MODE DATA (3 arguments: route, scenario, month)
        # Use different months to create variation
        # =====================================================================
        
        print("Simulation mode: Populating monthly data...")
        
        
        # =====================================================================
        # DECISION MODE DATA (2 arguments: route, scenario)
        # TRICK: We can't have multiple rows with same args in HDF5
        # So we populate ONE row per (route, scenario) with aggregated result
        # The interpreter will use these as-is
        # =====================================================================
        
        print("Decision mode: Creating aggregated probability data...")
        print("Note: Using single representative values per (route, scenario)")
        print()
        
        # Since HDF5 only stores one row per unique args, we set the DOMINANT value
        # Based on our target probabilities
        # R1 baseline: 67% efficiency, 67% service (different months), 58% carbon
        for month in range(1, 13):
            # Efficiency: months 1-8 (winter/spring good)
            val_eff = 1 if month <= 8 else 0  # 67%
            db.set_value('meets_efficiency', (1, 1, month), val_eff)
            
            # Service: months 1-4, 6-9 (skip month 5, add month 9) - different pattern!
            val_sq = 1 if (month <= 4 or (month >= 6 and month <= 9)) else 0  # 67%
            db.set_value('meets_service_quality', (1, 1, month), val_sq)
            
            # Carbon: months 1-7
            val_su = 1 if month <= 7 else 0  # 58%
            db.set_value('meets_carbon_limit', (1, 1, month), val_su)

        # R1 border_tight: 42% efficiency, 42% service (different months)
        for month in range(1, 13):
            # Efficiency: months 1-5
            val_eff = 1 if month <= 5 else 0  # 42%
            db.set_value('meets_efficiency', (1, 3, month), val_eff)
            
            # Service: months 2-6 (shifted by 1)
            val_sq = 1 if month >= 2 and month <= 6 else 0  # 42%
            db.set_value('meets_service_quality', (1, 3, month), val_sq)

        # R2 baseline: 42% efficiency, 50% service (different months)
        for month in range(1, 13):
            # Efficiency: months 1-5
            val_eff = 1 if month <= 5 else 0  # 42%
            db.set_value('meets_efficiency', (2, 1, month), val_eff)
            
            # Service: months 1-3, 8-10 (scattered)
            val_sq = 1 if (month <= 3 or (month >= 8 and month <= 10)) else 0  # 50%
            db.set_value('meets_service_quality', (2, 1, month), val_sq)
            
            # Carbon: months 1-6
            val_su = 1 if month <= 6 else 0  # 50%
            db.set_value('meets_carbon_limit', (2, 1, month), val_su)

        # R2 border_tight: 25% efficiency, 50% service
        for month in range(1, 13):
            # Efficiency: months 1-3 (degraded)
            val_eff = 1 if month <= 3 else 0  # 25%
            db.set_value('meets_efficiency', (2, 3, month), val_eff)
            
            # Service: months 1-6 (maintains service!)
            val_sq = 1 if month <= 6 else 0  # 50%
            db.set_value('meets_service_quality', (2, 3, month), val_sq)

        # R3 baseline: 58% efficiency, 58% service (different), HIGH adaptability/resilience
        for month in range(1, 13):
            # Efficiency: months 1-7
            val_eff = 1 if month <= 7 else 0  # 58%
            db.set_value('meets_efficiency', (3, 1, month), val_eff)
            
            # Service: months 1-5, 8-9 (different pattern)
            val_sq = 1 if (month <= 5 or month == 8 or month == 9) else 0  # 58%
            db.set_value('meets_service_quality', (3, 1, month), val_sq)
            
            # Carbon: months 2-7 (slightly offset)
            val_su = 1 if month >= 2 and month <= 7 else 0  # 50%
            db.set_value('meets_carbon_limit', (3, 1, month), val_su)
            
            # Adaptability: months 1-8 (70%)
            val_ad = 1 if month <= 8 else 0
            db.set_value('shows_adaptability', (3, 1, month), val_ad)
            
            # Resilience: months 1-9 (75%)
            val_sr = 1 if month <= 9 else 0
            db.set_value('maintains_resilience', (3, 1, month), val_sr)

        # R3 border_tight: MAINTAINS performance (58% efficiency, 58% service)
        for month in range(1, 13):
            # Efficiency: months 1-7
            val_eff = 1 if month <= 7 else 0  # 58%
            db.set_value('meets_efficiency', (3, 3, month), val_eff)
            
            # Service: months 2-8 (shifted, still 58%)
            val_sq = 1 if month >= 2 and month <= 8 else 0  # 58%
            db.set_value('meets_service_quality', (3, 3, month), val_sq)
        print("=" * 60)
        print("Database populated successfully!")
        print(f"File: {db_file}")
        print()
        print("IMPORTANT NOTE:")
        print("  Decision mode probabilities are based on SIMULATION data")
        print("  The interpreter calculates P(success) from monthly records")
        print()
        print("Expected outcomes:")
        print("  SIMULATION: Sample true/false each iteration")
        print("  DECISION: Calculate probabilities from monthly data")
        print("    - R1 baseline: ~67% success rate from monthly data")
        print("    - R3 border_tight: ~58% (maintains performance)")
        print("    - R2 border_tight: ~25% (degrades severely)")
        print("=" * 60)

if __name__ == '__main__':
    db_file = sys.argv[1] if len(sys.argv) > 1 else 'delta_db_synthetic.h5'
    populate_data(db_file)
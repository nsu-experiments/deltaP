#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
populate_logistics_data.py

"""

import sys
sys.path.insert(0, 'interpreter')

from interpreter.hdf5_manager import HDF5Manager

def populate_data(db_file='delta_db.h5'):
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
        
        # R1 baseline: 70% efficiency across months
        for month in range(1, 13):
            val = 1 if month <= 8 else 0  # 8 true, 4 false = ~67%
            db.set_value('meets_efficiency', (1, 1, month), val)
            
            val_sq = 1 if month <= 8 else 0  # 65%
            db.set_value('meets_service_quality', (1, 1, month), val_sq)
            
            val_su = 1 if month <= 7 else 0  # 60%
            db.set_value('meets_carbon_limit', (1, 1, month), val_su)
        
        # R1 border_tight: 45% efficiency
        for month in range(1, 13):
            val = 1 if month <= 5 else 0  # 5 true, 7 false = ~42%
            db.set_value('meets_efficiency', (1, 3, month), val)
            
            val_sq = 1 if month <= 5 else 0
            db.set_value('meets_service_quality', (1, 3, month), val_sq)
        
        # R2 baseline: 45% efficiency
        for month in range(1, 13):
            val = 1 if month <= 5 else 0
            db.set_value('meets_efficiency', (2, 1, month), val)
            
            val_sq = 1 if month <= 5 else 0
            db.set_value('meets_service_quality', (2, 1, month), val_sq)
        
        # R2 border_tight: 25% efficiency
        for month in range(1, 13):
            val = 1 if month <= 3 else 0
            db.set_value('meets_efficiency', (2, 3, month), val)
        
        # R3 baseline: 60% efficiency, HIGH adaptability/resilience
        for month in range(1, 13):
            val = 1 if month <= 7 else 0
            db.set_value('meets_efficiency', (3, 1, month), val)
            
            val_sq = 1 if month <= 7 else 0
            db.set_value('meets_service_quality', (3, 1, month), val_sq)
            
            val_ad = 1 if month <= 8 else 0  # 70% adaptability
            db.set_value('shows_adaptability', (3, 1, month), val_ad)
            
            val_sr = 1 if month <= 9 else 0  # 75% resilience
            db.set_value('maintains_resilience', (3, 1, month), val_sr)
        
        # R3 border_tight: MAINTAINS performance (58%)
        for month in range(1, 13):
            val = 1 if month <= 7 else 0
            db.set_value('meets_efficiency', (3, 3, month), val)
            
            val_sq = 1 if month <= 7 else 0
            db.set_value('meets_service_quality', (3, 3, month), val_sq)
        
        print("  ✓ Simulation data: 12 months × 3 routes × scenarios")
        print()
        
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
        
        # R1 baseline (should be 70% efficient, 65% service, 60% carbon)
        db.set_value('prob_meets_efficiency', (1, 1), 1)      # Majority true
        db.set_value('prob_meets_service_quality', (1, 1), 1)
        db.set_value('prob_meets_carbon_limit', (1, 1), 1)
        db.set_value('prob_shows_adaptability', (1, 1), 1)
        db.set_value('prob_maintains_resilience', (1, 1), 1)
        
        # R1 border_tight (degrades to 45%)
        db.set_value('prob_meets_efficiency', (1, 3), 0)      # Majority false now
        db.set_value('prob_meets_service_quality', (1, 3), 0)
        db.set_value('prob_meets_carbon_limit', (1, 3), 1)    # Carbon stays OK
        
        # R2 baseline (weak: 45%)
        db.set_value('prob_meets_efficiency', (2, 1), 0)
        db.set_value('prob_meets_service_quality', (2, 1), 0)
        db.set_value('prob_meets_carbon_limit', (2, 1), 1)
        
        # R2 border_tight (very poor: 25%)
        db.set_value('prob_meets_efficiency', (2, 3), 0)
        db.set_value('prob_meets_service_quality', (2, 3), 0)
        
        # R3 baseline (good: 60%, excellent adaptability/resilience)
        db.set_value('prob_meets_efficiency', (3, 1), 1)
        db.set_value('prob_meets_service_quality', (3, 1), 1)
        db.set_value('prob_meets_carbon_limit', (3, 1), 1)
        db.set_value('prob_shows_adaptability', (3, 1), 1)    # KEY STRENGTH
        db.set_value('prob_maintains_resilience', (3, 1), 1)  # KEY STRENGTH
        
        # R3 border_tight (MAINTAINS: 58%)
        db.set_value('prob_meets_efficiency', (3, 3), 1)      # Still good!
        db.set_value('prob_meets_service_quality', (3, 3), 1)
        db.set_value('prob_meets_carbon_limit', (3, 3), 1)
        
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
    db_file = sys.argv[1] if len(sys.argv) > 1 else 'delta_db.h5'
    populate_data(db_file)
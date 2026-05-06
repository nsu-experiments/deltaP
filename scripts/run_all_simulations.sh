#!/bin/bash
# =============================================================================
# Example Simulation Runs for ΔP Logistics Research
# =============================================================================
# This script demonstrates how to run different simulation configurations
# for publication-quality results.

set -e  # Exit on error

echo "=================================================="
echo "ΔP Logistics Simulation Suite"
echo "=================================================="
echo ""

# =============================================================================
# Configuration
# =============================================================================

INTERPRETER="python3 -m interpreter"
DP_SIMULATION="examples/supply_chain_simulation.dp"
DP_DECISION="examples/logistics_decision.dp"
OUTPUT_BASE="results"

# Create output directory structure
mkdir -p "${OUTPUT_BASE}"/{quick,standard,publication,plots}

# =============================================================================
# Run 1: Quick Test (10 iterations)
# =============================================================================

read -p "Run quick test first (10 iterations)? [Y/n]: " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    echo "📊 Run 1: Quick Test (10 iterations)"
    echo "Purpose: Verify everything works before long runs"
    echo ""
    
    python examples/run_logistics_simulation.py \
        --iterations 10 \
        --output "${OUTPUT_BASE}/quick" \
        --dp-file "${DP_SIMULATION}" \
        --interpreter "${INTERPRETER}"
    
    echo ""
    echo "✅ Quick test complete. Check: ${OUTPUT_BASE}/quick/"
    echo ""
fi

# =============================================================================
# Run 2: Standard Simulation (100 iterations)
# =============================================================================

echo "📊 Run 2: Standard Simulation (100 iterations)"
echo "Purpose: Research-grade results with statistical validity"
echo ""

python examples/run_logistics_simulation.py \
    --iterations 100 \
    --output "${OUTPUT_BASE}/standard" \
    --dp-file "${DP_SIMULATION}" \
    --interpreter "${INTERPRETER}"

echo ""
echo "✅ Standard simulation complete."
echo ""

# =============================================================================
# Run 3: Decision Mode Analysis
# =============================================================================

echo "📊 Run 3: Decision Mode Analysis"
echo "Purpose: Compute exact probabilities from database"
echo ""

${INTERPRETER} "${DP_DECISION}" > "${OUTPUT_BASE}/standard/decision_output.txt"

echo "✅ Decision analysis complete."
echo ""

# =============================================================================
# Run 4: Generate Visualizations
# =============================================================================

echo "📊 Run 4: Generating Visualizations"
echo ""

# Find the most recent stats file
STATS_FILE=$(ls -t "${OUTPUT_BASE}/standard"/simulation_stats_*.csv | head -1)

if [ -f "${STATS_FILE}" ]; then
    echo "Using stats file: ${STATS_FILE}"
    
    python utils/visualize_results.py \
        "${STATS_FILE}" \
        --output-dir "${OUTPUT_BASE}/standard/plots"
    
    echo ""
    echo "✅ Visualizations complete."
else
    echo "⚠️  No stats file found. Skipping visualization."
fi

echo ""
echo "=================================================="
echo "All runs complete!"
echo "=================================================="
echo ""
echo "📁 Results saved to: ${OUTPUT_BASE}/standard/"
echo ""
echo "Files generated:"
echo "  - simulation_raw_*.csv       (Raw iteration data)"
echo "  - simulation_stats_*.csv     (Statistical summary)"
echo "  - simulation_report_*.txt    (Human-readable report)"
echo "  - decision_output.txt        (Decision mode results)"
echo "  - plots/*.png                (Visualizations)"
echo ""

# =============================================================================
# Optional: Publication-Grade Run (1000 iterations)
# =============================================================================

read -p "Run publication-grade simulation (1000 iterations)? [y/N]: " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📊 Publication-Grade Simulation (1000 iterations)"
    echo "⏱️  This will take several minutes..."
    echo ""
    
    python run_logistics_simulation.py \
        --iterations 1000 \
        --output "${OUTPUT_BASE}/publication" \
        --dp-file "${DP_SIMULATION}" \
        --interpreter "${INTERPRETER}"
    
    # Generate plots for publication version
    STATS_FILE_PUB=$(ls -t "${OUTPUT_BASE}/publication"/simulation_stats_*.csv | head -1)
    
    if [ -f "${STATS_FILE_PUB}" ]; then
        python utils/visualize_results.py \
            "${STATS_FILE_PUB}" \
            --output-dir "${OUTPUT_BASE}/publication/plots"
    fi
    
    echo ""
    echo "✅ Publication-grade simulation complete!"
    echo "📁 Results: ${OUTPUT_BASE}/publication/"
fi

echo ""
echo "Done! 🎉"
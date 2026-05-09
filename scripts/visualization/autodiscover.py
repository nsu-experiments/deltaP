# scripts/visualization/autodiscover.py
"""
Metadata discovery and automatic chart generation for ΔP results.

Parses CSV metadata comments to automatically generate appropriate visualizations.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import re


@dataclass
class ChartSpec:
    """Specification for a chart extracted from metadata."""
    chart_type: str
    x: Optional[str] = None
    y: Optional[str] = None
    group_by: Optional[str] = None
    metrics: Optional[List[str]] = None
    ci: bool = False
    title: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None


def parse_meta_comment(comment_line: str) -> Dict[str, Any]:
    """
    Parse a metadata comment line from CSV.
    
    Expected format:
        # META: {"chart_type": "bar", "x": "route", "y": "success_rate"}
    
    Args:
        comment_line: Comment line starting with '# META:'
    
    Returns:
        Dictionary with metadata
    """
    if not comment_line.startswith('# META:'):
        return {}
    
    meta_str = comment_line.replace('# META:', '').strip()
    
    try:
        # Try JSON format
        return json.loads(meta_str)
    except json.JSONDecodeError:
        # Fallback: parse key=value pairs
        metadata = {}
        pairs = re.findall(r'(\w+)=([^,\s]+)', meta_str)
        for key, value in pairs:
            # Try to parse as JSON types
            try:
                metadata[key] = json.loads(value)
            except:
                metadata[key] = value
        return metadata


def discover_charts(csv_path: Path) -> List[ChartSpec]:
    """
    Discover chart specifications from CSV metadata.
    
    Args:
        csv_path: Path to CSV file with metadata comments
    
    Returns:
        List of ChartSpec objects
    """
    specs = []
    
    with open(csv_path, 'r') as f:
        for line in f:
            if line.startswith('# META:'):
                metadata = parse_meta_comment(line)
                if metadata:
                    spec = ChartSpec(
                        chart_type=metadata.get('chart_type', 'unknown'),
                        x=metadata.get('x'),
                        y=metadata.get('y'),
                        group_by=metadata.get('groupby') or metadata.get('group_by'),
                        metrics=metadata.get('metrics'),
                        ci=metadata.get('ci', False),
                        title=metadata.get('title'),
                        additional_params=metadata.get('params')
                    )
                    specs.append(spec)
            elif not line.startswith('#'):
                # Stop at first data line
                break
    
    return specs


def infer_chart_type(df: pd.DataFrame, 
                     x_col: Optional[str] = None,
                     y_col: Optional[str] = None) -> str:
    """
    Infer appropriate chart type from data structure.
    
    Args:
        df: DataFrame with data
        x_col: Optional X column name
        y_col: Optional Y column name
    
    Returns:
        Suggested chart type
    """
    # Check for common patterns in column names
    cols_lower = [c.lower() for c in df.columns]
    
    # Time series pattern
    if any('time' in c or 'date' in c or 'iteration' in c for c in cols_lower):
        return 'line'
    
    # Success/failure pattern
    if any('success' in c or 'failure' in c for c in cols_lower):
        return 'bar'
    
    # Correlation pattern (multiple numeric columns)
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) >= 3:
        return 'heatmap'
    
    # Default to bar for categorical x
    if x_col and df[x_col].dtype == 'object':
        return 'bar'
    
    # Default to scatter for numeric x and y
    if x_col and y_col:
        if df[x_col].dtype in ['int64', 'float64'] and df[y_col].dtype in ['int64', 'float64']:
            return 'scatter'
    
    return 'bar'  # Safe default


def detect_result_type(csv_path: Path) -> str:
    """
    Detect type of results file based on filename and structure.
    
    Args:
        csv_path: Path to CSV file
    
    Returns:
        Result type: 'raw', 'stats', 'aggregated', 'unknown'
    """
    filename = csv_path.stem.lower()
    
    if 'raw' in filename:
        return 'raw'
    elif 'stats' in filename or 'statistics' in filename:
        return 'stats'
    elif 'agg' in filename or 'summary' in filename:
        return 'aggregated'
    
    # Infer from structure
    df = pd.read_csv(csv_path, nrows=5, comment='#')
    
    # Raw has many rows, iteration columns
    if 'iteration' in df.columns or len(df) > 100:
        return 'raw'
    
    # Stats has aggregated metrics
    if any('mean' in c or 'std' in c or 'ci_' in c for c in df.columns):
        return 'stats'
    
    return 'unknown'


def suggest_charts_for_results(csv_path: Path) -> List[ChartSpec]:
    """
    Suggest appropriate charts based on results file type.
    
    Args:
        csv_path: Path to results CSV
    
    Returns:
        List of suggested ChartSpec objects
    """
    result_type = detect_result_type(csv_path)
    df = pd.read_csv(csv_path, nrows=10, comment='#')
    
    suggestions = []
    
    if result_type == 'raw':
        # Raw simulation data -> distributions, boxplots
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if 'route' in df.columns and any('success' in c for c in df.columns):
            suggestions.append(ChartSpec(
                chart_type='comparison',
                x='route',
                y='composite_success',
                title='Route Performance Comparison'
            ))
        
        for col in numeric_cols[:3]:  # Limit to first 3
            suggestions.append(ChartSpec(
                chart_type='histogram',
                x=col,
                title=f'Distribution of {col}'
            ))
    
    elif result_type == 'stats':
        # Aggregated statistics -> bar charts with CI, scenario comparisons
        if 'route' in df.columns and 'success_rate' in df.columns:
            suggestions.append(ChartSpec(
                chart_type='bar',
                x='route',
                y='success_rate',
                ci=True,
                title='Route Success Rates'
            ))
        
        if 'scenario' in df.columns:
            suggestions.append(ChartSpec(
                chart_type='line',
                x='scenario',
                y='success_rate',
                group_by='route',
                title='Scenario Sensitivity Analysis'
            ))
    
    return suggestions
#!/usr/bin/env python3
"""Generic CSV visualizer for ΔP results"""
import pandas as pd
import matplotlib.pyplot as plt
import sys
from pathlib import Path

def visualize_csv(csv_path, output_dir):
    """Auto-detect chart type and visualize"""
    df = pd.read_csv(csv_path)
    
    # Strip whitespace from column names and values
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set dark theme
    plt.style.use('dark_background')
    
    filename = Path(csv_path).stem
    
    # Decision results: bar chart by route
    if 'route' in df.columns and 'composite' in df.columns and 'month' not in df.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        routes = df['route'].astype(int)
        composite = df['composite'].astype(float)
        
        bars = ax.bar(routes, composite, color='#0e639c', edgecolor='#1177bb', linewidth=2, width=0.6)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}',
                   ha='center', va='bottom', fontsize=10)
        
        ax.set_xlabel('Route', fontsize=12)
        ax.set_ylabel('Composite Score', fontsize=12)
        ax.set_title('Decision Analysis: Composite Score by Route', fontsize=14, pad=20)
        ax.set_xticks(routes)
        ax.set_xticklabels([f'Route {r}' for r in routes])
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_ylim(0, max(composite) * 1.2)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'chart.png', dpi=150, bbox_inches='tight', facecolor='#1e1e1e')
        
    # Simulation results
    elif 'scenario' in df.columns and 'route' in df.columns and 'month' in df.columns:
        scenarios = df['scenario'].unique()
        routes = sorted(df['route'].unique())
        
        fig, axes = plt.subplots(1, len(scenarios), figsize=(6*len(scenarios), 5), squeeze=False)
        axes = axes.flatten()
        
        colors = ['#0e639c', '#e74c3c', '#2ecc71']
        
        for idx, scenario in enumerate(scenarios):
            ax = axes[idx]
            scenario_data = df[df['scenario'] == int(scenario)]
            
            for route_idx, route in enumerate(routes):
                route_data = scenario_data[scenario_data['route'] == int(route)]
                route_data = route_data.sort_values('month')
                
                ax.plot(route_data['month'], route_data['composite'], 
                       marker='o', label=f'Route {route}', 
                       linewidth=2, markersize=6, color=colors[route_idx % len(colors)])
            
            ax.set_xlabel('Month', fontsize=11)
            ax.set_ylabel('Composite Success', fontsize=11)
            ax.set_title(f'Scenario {int(scenario)}', fontsize=12, pad=10)
            ax.grid(alpha=0.3, linestyle='--')
            ax.legend(fontsize=9)
            ax.set_xticks(range(1, 13))
        
        plt.suptitle('Simulation Results', fontsize=14, y=1.02)
        plt.tight_layout()
        plt.savefig(output_dir / 'chart.png', dpi=150, bbox_inches='tight', facecolor='#1e1e1e')

if __name__ == '__main__':
    visualize_csv(sys.argv[1], sys.argv[2])

"""
Plotly Dashboard Generator for ACC Test Results

Creates an interactive HTML dashboard visualizing CAN signals over time
with pass/fail overlay markers from test results.

Author: ACC Test Suite
Version: 1.0.0
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

from parse_log import load_dbc, parse_asc_log, decode_signals, get_signal_timeseries
from test_cases import run_all_tests, summarize_results, TestResult


def create_signal_plot(df: pd.DataFrame, 
                       signal_name: str,
                       display_name: str,
                       unit: str,
                       color: str) -> go.Scatter:
    """
    Create a Plotly scatter trace for a signal time series.
    
    Args:
        df: Decoded signals DataFrame
        signal_name: Signal name in DataFrame
        display_name: Human-readable name for legend
        unit: Unit string for hover text
        color: Line color
        
    Returns:
        Plotly Scatter trace
    """
    signal_df = get_signal_timeseries(df, signal_name)
    
    if signal_df.empty:
        return go.Scatter(x=[], y=[], name=display_name)
    
    return go.Scatter(
        x=signal_df['timestamp'],
        y=signal_df['value'],
        mode='lines+markers',
        name=display_name,
        line=dict(color=color, width=2),
        marker=dict(size=4),
        hovertemplate=f'<b>{display_name}</b><br>' +
                      'Time: %{x:.3f}s<br>' +
                      f'Value: %{{y:.2f}} {unit}<extra></extra>'
    )


def create_violation_markers(results: List[TestResult],
                             y_position: float,
                             test_name: str) -> go.Scatter:
    """
    Create markers for test violations at specific timestamps.
    
    Args:
        results: List of TestResult objects
        y_position: Y-axis position for markers
        test_name: Name of test to show markers for
        
    Returns:
        Plotly Scatter trace with violation markers
    """
    # Find the specific test result
    result = next((r for r in results if r.name == test_name), None)
    
    if not result or not result.timestamps:
        return go.Scatter(x=[], y=[], name=f"{test_name} Violations")
    
    return go.Scatter(
        x=result.timestamps,
        y=[y_position] * len(result.timestamps),
        mode='markers',
        name=f"⚠ {test_name}",
        marker=dict(
            symbol='x',
            size=12,
            color='red',
            line=dict(width=2, color='darkred')
        ),
        hovertemplate=f'<b>{test_name} Violation</b><br>' +
                      'Time: %{x:.3f}s<extra></extra>'
    )


def generate_dashboard(df: pd.DataFrame,
                       results: List[TestResult],
                       output_path: str = "test_results_dashboard.html") -> str:
    """
    Generate an interactive Plotly dashboard HTML file.
    
    Args:
        df: Decoded signals DataFrame
        results: List of TestResult from test execution
        output_path: Path for output HTML file
        
    Returns:
        Path to generated HTML file
    """
    # Create subplot figure with 3 rows
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(
            '🚗 Vehicle Speed (km/h)',
            '⛽ Throttle Position (%)',
            '🛑 Brake Pressure (bar)',
            '📊 Test Results Timeline'
        ),
        row_heights=[0.28, 0.24, 0.24, 0.24]
    )
    
    # ========== Speed Plot (Row 1) ==========
    speed_trace = create_signal_plot(
        df, 'Speed', 'Vehicle Speed', 'km/h', '#3366CC'
    )
    fig.add_trace(speed_trace, row=1, col=1)
    
    # Add overspeed threshold line
    fig.add_hline(
        y=100, line_dash="dash", line_color="red",
        annotation_text="Speed Limit (100 km/h)",
        annotation_position="top right",
        row=1, col=1
    )
    
    # Add overspeed violation markers
    overspeed_result = next((r for r in results if r.name == "Overspeed Detection"), None)
    if overspeed_result and overspeed_result.timestamps:
        # Get actual speed values at violation times
        speed_df = get_signal_timeseries(df, 'Speed')
        violation_speeds = []
        for t in overspeed_result.timestamps:
            closest = speed_df.iloc[(speed_df['timestamp'] - t).abs().argsort()[:1]]
            if not closest.empty:
                violation_speeds.append(closest['value'].values[0])
            else:
                violation_speeds.append(100)
        
        fig.add_trace(go.Scatter(
            x=overspeed_result.timestamps,
            y=violation_speeds,
            mode='markers',
            name='⚠ Overspeed',
            marker=dict(symbol='circle-x', size=14, color='red', 
                       line=dict(width=2, color='darkred')),
            hovertemplate='<b>OVERSPEED!</b><br>Time: %{x:.3f}s<br>Speed: %{y:.1f} km/h<extra></extra>'
        ), row=1, col=1)
    
    # ========== Throttle Plot (Row 2) ==========
    throttle_trace = create_signal_plot(
        df, 'ThrottlePosition', 'Throttle', '%', '#109618'
    )
    fig.add_trace(throttle_trace, row=2, col=1)
    
    # ========== Brake Plot (Row 3) ==========
    brake_trace = create_signal_plot(
        df, 'BrakePressure', 'Brake Pressure', 'bar', '#DC3912'
    )
    fig.add_trace(brake_trace, row=3, col=1)
    
    # Add emergency brake threshold
    fig.add_hline(
        y=200, line_dash="dash", line_color="orange",
        annotation_text="Emergency Threshold",
        annotation_position="top right",
        row=3, col=1
    )
    
    # Add emergency stop markers
    emergency_result = next((r for r in results if r.name == "Emergency Stop Detection"), None)
    if emergency_result and emergency_result.timestamps:
        brake_df = get_signal_timeseries(df, 'BrakePressure')
        violation_brakes = []
        for t in emergency_result.timestamps:
            closest = brake_df.iloc[(brake_df['timestamp'] - t).abs().argsort()[:1]]
            if not closest.empty:
                violation_brakes.append(closest['value'].values[0])
            else:
                violation_brakes.append(200)
        
        fig.add_trace(go.Scatter(
            x=emergency_result.timestamps,
            y=violation_brakes,
            mode='markers',
            name='⚠ Emergency Stop',
            marker=dict(symbol='star', size=14, color='orange',
                       line=dict(width=2, color='darkorange')),
            hovertemplate='<b>EMERGENCY STOP!</b><br>Time: %{x:.3f}s<br>Brake: %{y:.0f} bar<extra></extra>'
        ), row=3, col=1)
    
    # ========== Test Results Timeline (Row 4) ==========
    test_names = [r.name for r in results]
    test_colors = ['#2ECC71' if r.passed else '#E74C3C' for r in results]
    test_statuses = ['PASS ✓' if r.passed else 'FAIL ✗' for r in results]
    
    # Create horizontal bar chart for test results
    fig.add_trace(go.Bar(
        y=test_names,
        x=[1] * len(results),
        orientation='h',
        marker=dict(color=test_colors),
        text=test_statuses,
        textposition='inside',
        hovertemplate='<b>%{y}</b><br>Status: %{text}<extra></extra>',
        showlegend=False
    ), row=4, col=1)
    
    # ========== Layout Configuration ==========
    fig.update_layout(
        title=dict(
            text='<b>🚗 ACC CAN Signal Analysis Dashboard</b>',
            font=dict(size=24, color='#2C3E50'),
            x=0.5
        ),
        height=1000,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        template='plotly_white',
        hovermode='x unified'
    )
    
    # Update axes
    fig.update_xaxes(title_text="Time (seconds)", row=3, col=1)
    fig.update_yaxes(title_text="Speed (km/h)", row=1, col=1)
    fig.update_yaxes(title_text="Throttle (%)", row=2, col=1)
    fig.update_yaxes(title_text="Brake (bar)", row=3, col=1)
    fig.update_yaxes(title_text="", row=4, col=1)
    fig.update_xaxes(showticklabels=False, row=4, col=1)
    
    # Add summary annotation
    summary = summarize_results(results)
    summary_text = (
        f"<b>Test Summary:</b> {summary['passed']}/{summary['total']} passed "
        f"({summary['pass_rate']:.0f}%)"
    )
    
    fig.add_annotation(
        text=summary_text,
        xref="paper", yref="paper",
        x=0.01, y=-0.05,
        showarrow=False,
        font=dict(size=14),
        align="left"
    )
    
    # Save to HTML
    fig.write_html(
        output_path,
        include_plotlyjs=True,
        full_html=True,
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }
    )
    
    return output_path


def generate_summary_json(results: List[TestResult],
                          output_path: str = "test_results.json") -> str:
    """
    Generate a JSON file with test results for external consumption.
    
    Args:
        results: List of TestResult objects
        output_path: Path for output JSON file
        
    Returns:
        Path to generated JSON file
    """
    summary = summarize_results(results)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    return output_path


if __name__ == "__main__":
    # Standalone execution
    script_dir = Path(__file__).parent
    dbc_path = script_dir / "acc_signals.dbc"
    log_path = script_dir / "sample_can_log.asc"
    output_path = script_dir / "test_results_dashboard.html"
    
    print("=" * 60)
    print("ACC CAN Signal Dashboard Generator")
    print("=" * 60)
    
    if dbc_path.exists() and log_path.exists():
        print("\n📂 Loading data files...")
        dbc = load_dbc(str(dbc_path))
        messages = parse_asc_log(str(log_path))
        df = decode_signals(messages, dbc)
        
        print(f"   Loaded {len(dbc.messages)} message definitions")
        print(f"   Parsed {len(messages)} CAN messages")
        print(f"   Decoded {len(df)} signal values")
        
        print("\n🧪 Running test cases...")
        results = run_all_tests(df, dbc)
        
        for result in results:
            status = "✓" if result.passed else "✗"
            print(f"   {status} {result.name}")
        
        print("\n📊 Generating dashboard...")
        html_path = generate_dashboard(df, results, str(output_path))
        print(f"   Dashboard saved to: {html_path}")
        
        json_path = generate_summary_json(results, str(script_dir / "test_results.json"))
        print(f"   JSON results saved to: {json_path}")
        
        summary = summarize_results(results)
        print(f"\n📈 Summary: {summary['passed']}/{summary['total']} tests passed "
              f"({summary['pass_rate']:.0f}%)")
        
        print("\n✅ Dashboard generation complete!")
        print(f"   Open {output_path} in your browser to view results.")
    else:
        print("❌ Error: DBC or log file not found.")
        print(f"   Expected: {dbc_path}")
        print(f"   Expected: {log_path}")

"""
ACC CAN Test Suite - Main Orchestration Script

This script runs the complete test pipeline:
1. Parse CAN log files
2. Execute pytest test suite with coverage
3. Generate interactive dashboard
4. Print summary report

Usage:
    python run_all.py [--log LOG_FILE] [--dbc DBC_FILE]

Author: ACC Test Suite
Version: 1.0.0
"""

import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

from parse_log import load_dbc, parse_asc_log, decode_signals
from test_cases import run_all_tests, summarize_results
from dashboard import generate_dashboard, generate_summary_json


def print_banner():
    """Print the application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🚗  ACC CAN Signal Test Suite  🚗                        ║
║                                                              ║
║     Automotive Adaptive Cruise Control Validation            ║
║     Version 1.0.0                                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_pytest_with_coverage(project_dir: Path) -> bool:
    """
    Run pytest with coverage reporting.
    
    Args:
        project_dir: Path to project directory
        
    Returns:
        True if all tests passed, False otherwise
    """
    print("\n" + "=" * 60)
    print("📋 RUNNING PYTEST WITH COVERAGE")
    print("=" * 60)
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(project_dir / "test_acc.py"),
        "-v",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=80"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_dir),
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running pytest: {e}")
        return False


def run_analysis(log_path: Path, dbc_path: Path, output_dir: Path) -> dict:
    """
    Run the complete analysis pipeline.
    
    Args:
        log_path: Path to CAN log file
        dbc_path: Path to DBC file
        output_dir: Directory for output files
        
    Returns:
        Summary dictionary with results
    """
    print("\n" + "=" * 60)
    print("📂 LOADING DATA FILES")
    print("=" * 60)
    
    # Load DBC
    print(f"\n   Loading DBC: {dbc_path.name}")
    dbc = load_dbc(str(dbc_path))
    print(f"   ✓ Loaded {len(dbc.messages)} message definitions")
    
    for msg in dbc.messages:
        print(f"     • {msg.name} (0x{msg.frame_id:X}): {len(msg.signals)} signals")
    
    # Parse log
    print(f"\n   Parsing log: {log_path.name}")
    messages = parse_asc_log(str(log_path))
    print(f"   ✓ Parsed {len(messages)} raw CAN messages")
    
    # Decode signals
    print(f"\n   Decoding signals...")
    df = decode_signals(messages, dbc)
    print(f"   ✓ Decoded {len(df)} signal values")
    
    # Show signal summary
    print("\n   Signal Statistics:")
    for signal in ['Speed', 'ThrottlePosition', 'BrakePressure']:
        signal_df = df[df['signal_name'] == signal]['value']
        if not signal_df.empty:
            print(f"     • {signal}: min={signal_df.min():.1f}, "
                  f"max={signal_df.max():.1f}, points={len(signal_df)}")
    
    # Run test cases
    print("\n" + "=" * 60)
    print("🧪 RUNNING TEST CASES")
    print("=" * 60)
    
    results = run_all_tests(df, dbc)
    
    print()
    for result in results:
        status = "✓ PASS" if result.passed else "✗ FAIL"
        color_code = "\033[92m" if result.passed else "\033[91m"
        reset_code = "\033[0m"
        
        # For Windows compatibility, just use text
        print(f"   {status}: {result.name}")
        print(f"           {result.message}")
        if not result.passed and result.details:
            print(f"           Violations: {len(result.details)}")
    
    # Generate dashboard
    print("\n" + "=" * 60)
    print("📊 GENERATING DASHBOARD")
    print("=" * 60)
    
    dashboard_path = output_dir / "test_results_dashboard.html"
    generate_dashboard(df, results, str(dashboard_path))
    print(f"\n   ✓ Dashboard: {dashboard_path}")
    
    json_path = output_dir / "test_results.json"
    generate_summary_json(results, str(json_path))
    print(f"   ✓ JSON Results: {json_path}")
    
    return summarize_results(results)


def print_summary(summary: dict, pytest_passed: bool):
    """Print the final summary report."""
    print("\n" + "=" * 60)
    print("📈 FINAL SUMMARY")
    print("=" * 60)
    
    print(f"""
   Test Cases:    {summary['passed']}/{summary['total']} passed ({summary['pass_rate']:.0f}%)
   Pytest:        {'✓ PASSED' if pytest_passed else '✗ FAILED'}
   Coverage:      See htmlcov/index.html
   Dashboard:     test_results_dashboard.html
   
   Timestamp:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)
    
    if summary['pass_rate'] >= 80 and pytest_passed:
        print("   🎉 All validation criteria met!")
    else:
        print("   ⚠️  Some validation criteria failed. Review results.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='ACC CAN Signal Test Suite - Run complete validation pipeline'
    )
    parser.add_argument(
        '--log', '-l',
        type=str,
        default='sample_can_log.asc',
        help='Path to ASC log file (default: sample_can_log.asc)'
    )
    parser.add_argument(
        '--dbc', '-d',
        type=str,
        default='acc_signals.dbc',
        help='Path to DBC file (default: acc_signals.dbc)'
    )
    parser.add_argument(
        '--skip-pytest',
        action='store_true',
        help='Skip pytest execution (only run analysis)'
    )
    
    args = parser.parse_args()
    
    # Determine paths
    project_dir = Path(__file__).parent
    log_path = project_dir / args.log
    dbc_path = project_dir / args.dbc
    
    # Print banner
    print_banner()
    
    # Validate inputs
    if not log_path.exists():
        print(f"❌ Error: Log file not found: {log_path}")
        sys.exit(1)
    if not dbc_path.exists():
        print(f"❌ Error: DBC file not found: {dbc_path}")
        sys.exit(1)
    
    print(f"   Project:  {project_dir}")
    print(f"   Log file: {log_path.name}")
    print(f"   DBC file: {dbc_path.name}")
    
    # Run pytest
    pytest_passed = True
    if not args.skip_pytest:
        pytest_passed = run_pytest_with_coverage(project_dir)
    else:
        print("\n   ⏭️  Skipping pytest (--skip-pytest flag)")
    
    # Run analysis
    summary = run_analysis(log_path, dbc_path, project_dir)
    
    # Print final summary
    print_summary(summary, pytest_passed)
    
    # Exit code
    if summary['pass_rate'] < 80:
        sys.exit(1)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

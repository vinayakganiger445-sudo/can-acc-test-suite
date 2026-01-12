"""
Test Cases Module for ACC CAN Signal Validation

This module contains the core test case implementations for validating
Adaptive Cruise Control (ACC) CAN signals. Each test returns a result
dictionary with pass/fail status and detailed findings.

Author: ACC Test Suite
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import cantools


@dataclass
class TestResult:
    """Container for test case results."""
    name: str
    passed: bool
    message: str
    details: List[Dict[str, Any]]
    timestamps: List[float]  # Timestamps of violations for visualization
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'passed': self.passed,
            'message': self.message,
            'details': self.details,
            'violation_count': len(self.timestamps),
            'timestamps': self.timestamps
        }


def check_overspeed(df: pd.DataFrame, threshold_kmh: float = 100.0) -> TestResult:
    """
    Test Case 1: Detect overspeed conditions.
    
    Checks if vehicle speed exceeds the defined threshold at any point.
    For ACC systems, overspeed may indicate control system failure.
    
    Args:
        df: Decoded signals DataFrame
        threshold_kmh: Maximum allowed speed in km/h (default: 100)
        
    Returns:
        TestResult with pass/fail and violation details
    """
    # Handle empty DataFrame
    if df.empty or 'signal_name' not in df.columns:
        return TestResult(
            name="Overspeed Detection",
            passed=False,
            message="No data available for analysis",
            details=[],
            timestamps=[]
        )
    
    speed_df = df[df['signal_name'] == 'Speed'].copy()
    
    if speed_df.empty:
        return TestResult(
            name="Overspeed Detection",
            passed=False,
            message="No speed signal data found in log",
            details=[],
            timestamps=[]
        )
    
    # Find overspeed violations
    violations = speed_df[speed_df['value'] > threshold_kmh]
    
    if violations.empty:
        return TestResult(
            name="Overspeed Detection",
            passed=True,
            message=f"No overspeed conditions detected (threshold: {threshold_kmh} km/h)",
            details=[],
            timestamps=[]
        )
    
    # Collect violation details
    details = []
    for _, row in violations.iterrows():
        details.append({
            'timestamp': row['timestamp'],
            'speed': row['value'],
            'threshold': threshold_kmh,
            'excess': row['value'] - threshold_kmh
        })
    
    max_speed = violations['value'].max()
    
    return TestResult(
        name="Overspeed Detection",
        passed=False,
        message=f"Overspeed detected: {len(violations)} violations, max {max_speed:.1f} km/h",
        details=details,
        timestamps=violations['timestamp'].tolist()
    )


def check_timeout(df: pd.DataFrame, 
                  timeout_seconds: float = 2.0,
                  message_name: str = None) -> TestResult:
    """
    Test Case 2: Detect message timeout conditions.
    
    Checks for gaps in CAN message transmission exceeding the timeout threshold.
    Message timeouts may indicate ECU failure or communication issues.
    
    Args:
        df: Decoded signals DataFrame
        timeout_seconds: Maximum allowed gap between messages (default: 2.0s)
        message_name: Specific message to check, or None to check all
        
    Returns:
        TestResult with pass/fail and timeout details
    """
    # Handle empty DataFrame
    if df.empty or 'timestamp' not in df.columns:
        return TestResult(
            name="Message Timeout Detection",
            passed=False,
            message="No data available for analysis",
            details=[],
            timestamps=[]
        )
    
    if message_name:
        msg_df = df[df['message_name'] == message_name].copy()
    else:
        msg_df = df.copy()
    
    if msg_df.empty:
        return TestResult(
            name="Message Timeout Detection",
            passed=False,
            message="No message data found in log",
            details=[],
            timestamps=[]
        )
    
    # Get unique timestamps and sort
    timestamps = sorted(msg_df['timestamp'].unique())
    
    if len(timestamps) < 2:
        return TestResult(
            name="Message Timeout Detection",
            passed=True,
            message="Insufficient data to check timeouts",
            details=[],
            timestamps=[]
        )
    
    # Calculate intervals and find timeouts
    violations = []
    violation_timestamps = []
    
    for i in range(len(timestamps) - 1):
        interval = timestamps[i + 1] - timestamps[i]
        if interval > timeout_seconds:
            violations.append({
                'start_time': timestamps[i],
                'end_time': timestamps[i + 1],
                'gap_duration': interval,
                'threshold': timeout_seconds
            })
            violation_timestamps.append(timestamps[i])
    
    if not violations:
        return TestResult(
            name="Message Timeout Detection",
            passed=True,
            message=f"No message timeouts detected (threshold: {timeout_seconds}s)",
            details=[],
            timestamps=[]
        )
    
    max_gap = max(v['gap_duration'] for v in violations)
    
    return TestResult(
        name="Message Timeout Detection",
        passed=False,
        message=f"Message timeout detected: {len(violations)} gaps, max {max_gap:.2f}s",
        details=violations,
        timestamps=violation_timestamps
    )


def check_emergency_stop(df: pd.DataFrame,
                         brake_threshold: int = 200,
                         decel_threshold_kmh_per_s: float = 20.0) -> TestResult:
    """
    Test Case 3: Detect emergency stop events.
    
    An emergency stop is characterized by:
    - Brake pressure exceeding threshold (hard braking)
    - Speed deceleration exceeding threshold (rapid slowdown)
    
    Args:
        df: Decoded signals DataFrame
        brake_threshold: Minimum brake pressure for emergency (default: 200 bar)
        decel_threshold_kmh_per_s: Minimum deceleration rate (default: 20 km/h/s)
        
    Returns:
        TestResult with emergency stop events detected
    """
    speed_df = df[df['signal_name'] == 'Speed'][['timestamp', 'value']].copy()
    brake_df = df[df['signal_name'] == 'BrakePressure'][['timestamp', 'value']].copy()
    
    if speed_df.empty or brake_df.empty:
        return TestResult(
            name="Emergency Stop Detection",
            passed=True,  # No data = no emergency detected
            message="Insufficient speed or brake data for analysis",
            details=[],
            timestamps=[]
        )
    
    speed_df = speed_df.sort_values('timestamp').reset_index(drop=True)
    brake_df = brake_df.sort_values('timestamp').reset_index(drop=True)
    
    # Calculate speed deceleration (derivative)
    speed_df['decel'] = -speed_df['value'].diff() / speed_df['timestamp'].diff()
    
    # Find high brake pressure events
    high_brake = brake_df[brake_df['value'] > brake_threshold]
    
    violations = []
    violation_timestamps = []
    
    for _, brake_row in high_brake.iterrows():
        t = brake_row['timestamp']
        
        # Find speed readings near this timestamp (within 0.2s)
        nearby_speed = speed_df[
            (speed_df['timestamp'] >= t - 0.2) & 
            (speed_df['timestamp'] <= t + 0.2)
        ]
        
        if not nearby_speed.empty:
            max_decel = nearby_speed['decel'].max()
            
            if pd.notna(max_decel) and max_decel > decel_threshold_kmh_per_s:
                violations.append({
                    'timestamp': t,
                    'brake_pressure': brake_row['value'],
                    'deceleration': max_decel,
                    'brake_threshold': brake_threshold,
                    'decel_threshold': decel_threshold_kmh_per_s
                })
                violation_timestamps.append(t)
    
    if not violations:
        return TestResult(
            name="Emergency Stop Detection",
            passed=True,
            message="No emergency stop events detected",
            details=[],
            timestamps=[]
        )
    
    return TestResult(
        name="Emergency Stop Detection",
        passed=False,  # Emergency stops are detected (test catches the condition)
        message=f"Emergency stop detected: {len(violations)} events",
        details=violations,
        timestamps=violation_timestamps
    )


def check_signal_bounds(df: pd.DataFrame, 
                        dbc: cantools.database.Database) -> TestResult:
    """
    Test Case 4: Validate signals are within DBC-defined bounds.
    
    Checks each decoded signal value against the min/max limits
    defined in the DBC file.
    
    Args:
        df: Decoded signals DataFrame
        dbc: cantools Database with signal definitions
        
    Returns:
        TestResult with out-of-bounds violations
    """
    violations = []
    violation_timestamps = []
    
    # Build signal bounds lookup from DBC
    signal_bounds = {}
    for message in dbc.messages:
        for signal in message.signals:
            signal_bounds[signal.name] = {
                'min': signal.minimum if signal.minimum is not None else float('-inf'),
                'max': signal.maximum if signal.maximum is not None else float('inf'),
                'message': message.name
            }
    
    # Check each signal value
    for _, row in df.iterrows():
        signal_name = row['signal_name']
        value = row['value']
        
        if signal_name not in signal_bounds:
            continue
        
        if value is None or not isinstance(value, (int, float)):
            continue
        
        bounds = signal_bounds[signal_name]
        
        if value < bounds['min'] or value > bounds['max']:
            violations.append({
                'timestamp': row['timestamp'],
                'signal': signal_name,
                'value': value,
                'min': bounds['min'],
                'max': bounds['max'],
                'message': bounds['message']
            })
            violation_timestamps.append(row['timestamp'])
    
    if not violations:
        return TestResult(
            name="Signal Bounds Validation",
            passed=True,
            message="All signal values within DBC-defined bounds",
            details=[],
            timestamps=[]
        )
    
    return TestResult(
        name="Signal Bounds Validation",
        passed=False,
        message=f"Out-of-bounds violations: {len(violations)} signals",
        details=violations,
        timestamps=list(set(violation_timestamps))
    )


def check_checksum(df: pd.DataFrame) -> TestResult:
    """
    Test Case 5: Validate message checksums.
    
    For the Brake message, validates that BrakeChecksum matches
    the expected XOR checksum of BrakePressure.
    
    Checksum algorithm: BrakeChecksum should equal BrakePressure XOR 0x00
    (simple validation - real checksums would be more complex)
    
    Args:
        df: Decoded signals DataFrame
        
    Returns:
        TestResult with checksum validation results
    """
    # Get brake messages with both pressure and checksum
    brake_pressure = df[df['signal_name'] == 'BrakePressure'][['timestamp', 'value']].copy()
    brake_checksum = df[df['signal_name'] == 'BrakeChecksum'][['timestamp', 'value']].copy()
    
    if brake_pressure.empty or brake_checksum.empty:
        return TestResult(
            name="Checksum Validation",
            passed=True,
            message="No brake checksum data available for validation",
            details=[],
            timestamps=[]
        )
    
    # Merge on timestamp
    merged = pd.merge(
        brake_pressure.rename(columns={'value': 'pressure'}),
        brake_checksum.rename(columns={'value': 'checksum'}),
        on='timestamp',
        how='inner'
    )
    
    violations = []
    violation_timestamps = []
    
    for _, row in merged.iterrows():
        pressure = int(row['pressure'])
        checksum = int(row['checksum'])
        
        # Expected checksum: pressure value itself (simple echo check)
        # In real systems, this would be CRC or XOR of multiple bytes
        expected_checksum = pressure
        
        if checksum != expected_checksum:
            violations.append({
                'timestamp': row['timestamp'],
                'pressure': pressure,
                'checksum': checksum,
                'expected': expected_checksum
            })
            violation_timestamps.append(row['timestamp'])
    
    if not violations:
        return TestResult(
            name="Checksum Validation",
            passed=True,
            message="All brake message checksums valid",
            details=[],
            timestamps=[]
        )
    
    return TestResult(
        name="Checksum Validation",
        passed=False,
        message=f"Checksum errors detected: {len(violations)} invalid messages",
        details=violations,
        timestamps=violation_timestamps
    )


def run_all_tests(df: pd.DataFrame, 
                  dbc: cantools.database.Database) -> List[TestResult]:
    """
    Run all test cases and return results.
    
    Args:
        df: Decoded signals DataFrame
        dbc: cantools Database for bounds checking
        
    Returns:
        List of TestResult objects
    """
    results = [
        check_overspeed(df),
        check_timeout(df),
        check_emergency_stop(df),
        check_signal_bounds(df, dbc),
        check_checksum(df)
    ]
    
    return results


def summarize_results(results: List[TestResult]) -> Dict[str, Any]:
    """
    Create a summary of all test results.
    
    Args:
        results: List of TestResult objects
        
    Returns:
        Summary dictionary with pass/fail counts and details
    """
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    
    return {
        'total': len(results),
        'passed': passed,
        'failed': failed,
        'pass_rate': passed / len(results) * 100 if results else 0,
        'results': [r.to_dict() for r in results]
    }


if __name__ == "__main__":
    # Demonstration with sample data
    from pathlib import Path
    from parse_log import load_dbc, parse_asc_log, decode_signals
    
    script_dir = Path(__file__).parent
    dbc_path = script_dir / "acc_signals.dbc"
    log_path = script_dir / "sample_can_log.asc"
    
    if dbc_path.exists() and log_path.exists():
        print("Loading test data...")
        dbc = load_dbc(str(dbc_path))
        messages = parse_asc_log(str(log_path))
        df = decode_signals(messages, dbc)
        
        print("\nRunning test cases...")
        results = run_all_tests(df, dbc)
        
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        
        for result in results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"\n{status}: {result.name}")
            print(f"  {result.message}")
            if result.details and not result.passed:
                print(f"  Violations: {len(result.details)}")
        
        summary = summarize_results(results)
        print(f"\n{'=' * 60}")
        print(f"OVERALL: {summary['passed']}/{summary['total']} tests passed "
              f"({summary['pass_rate']:.1f}%)")
    else:
        print("Sample data files not found. Run from project directory.")

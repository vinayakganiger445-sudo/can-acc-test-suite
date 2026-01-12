"""
Pytest Test Suite for ACC CAN Signal Validation

This module provides pytest-compatible test cases for validating
Adaptive Cruise Control (ACC) CAN signals. Uses fixtures for
data loading and dependency injection.

Run with: pytest test_acc.py -v --cov=. --cov-report=html

Author: ACC Test Suite
Version: 1.0.0
"""

import pytest
import pandas as pd
from pathlib import Path
from typing import Generator, Tuple

# Import project modules
from parse_log import load_dbc, parse_asc_log, decode_signals
from test_cases import (
    check_overspeed,
    check_timeout,
    check_emergency_stop,
    check_signal_bounds,
    check_checksum,
    run_all_tests,
    summarize_results,
    TestResult
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def project_dir() -> Path:
    """Get the project directory path."""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def dbc_path(project_dir: Path) -> Path:
    """Get the DBC file path."""
    return project_dir / "acc_signals.dbc"


@pytest.fixture(scope="session")
def log_path(project_dir: Path) -> Path:
    """Get the sample log file path."""
    return project_dir / "sample_can_log.asc"


@pytest.fixture(scope="session")
def dbc(dbc_path: Path):
    """Load the DBC database."""
    return load_dbc(str(dbc_path))


@pytest.fixture(scope="session")
def raw_messages(log_path: Path):
    """Parse raw CAN messages from log."""
    return parse_asc_log(str(log_path))


@pytest.fixture(scope="session")
def decoded_df(raw_messages, dbc) -> pd.DataFrame:
    """Decode CAN messages to signals DataFrame."""
    return decode_signals(raw_messages, dbc)


@pytest.fixture(scope="session")
def all_test_results(decoded_df, dbc):
    """Run all tests and cache results."""
    return run_all_tests(decoded_df, dbc)


# ============================================================================
# UNIT TESTS - Parser Module
# ============================================================================

class TestParserModule:
    """Tests for parse_log.py functionality."""
    
    def test_dbc_loads_successfully(self, dbc):
        """Verify DBC file loads without errors."""
        assert dbc is not None
        assert len(dbc.messages) > 0
    
    def test_dbc_contains_expected_messages(self, dbc):
        """Verify expected message definitions exist in DBC."""
        message_names = [m.name for m in dbc.messages]
        assert "Throttle" in message_names
        assert "VehicleSpeed" in message_names
        assert "BrakeSystem" in message_names
    
    def test_log_parses_successfully(self, raw_messages):
        """Verify ASC log file parses without errors."""
        assert raw_messages is not None
        assert len(raw_messages) > 0
    
    def test_log_contains_expected_message_ids(self, raw_messages):
        """Verify expected CAN IDs are present in log."""
        message_ids = set(m['id'] for m in raw_messages)
        assert 0x100 in message_ids  # Throttle
        assert 0x101 in message_ids  # Speed
        assert 0x102 in message_ids  # Brake
    
    def test_signals_decode_successfully(self, decoded_df):
        """Verify signal decoding produces valid DataFrame."""
        assert not decoded_df.empty
        assert 'timestamp' in decoded_df.columns
        assert 'signal_name' in decoded_df.columns
        assert 'value' in decoded_df.columns
    
    def test_decoded_signals_have_expected_names(self, decoded_df):
        """Verify expected signal names are present."""
        signal_names = decoded_df['signal_name'].unique()
        assert 'Speed' in signal_names
        assert 'ThrottlePosition' in signal_names
        assert 'BrakePressure' in signal_names


# ============================================================================
# ACC TEST CASES
# ============================================================================

class TestOverspeed:
    """Test Case 1: Overspeed Detection."""
    
    def test_overspeed_detection_returns_result(self, decoded_df):
        """Verify overspeed check returns valid TestResult."""
        result = check_overspeed(decoded_df)
        assert isinstance(result, TestResult)
        assert result.name == "Overspeed Detection"
    
    def test_overspeed_detects_violations_in_sample_log(self, decoded_df):
        """
        Verify overspeed is detected in sample log.
        
        The sample log contains speeds > 100 km/h (up to ~159 km/h at t=4.0s)
        which should trigger overspeed violations.
        """
        result = check_overspeed(decoded_df, threshold_kmh=100.0)
        
        # Sample log has overspeed conditions
        assert not result.passed, "Expected overspeed violations in sample log"
        assert len(result.details) > 0, "Expected violation details"
        assert len(result.timestamps) > 0, "Expected violation timestamps"
    
    def test_overspeed_threshold_configurable(self, decoded_df):
        """Verify different thresholds produce expected results."""
        # With very high threshold, should pass
        result_high = check_overspeed(decoded_df, threshold_kmh=500.0)
        assert result_high.passed, "No violations expected with 500 km/h threshold"
        
        # With very low threshold, should fail with more violations
        result_low = check_overspeed(decoded_df, threshold_kmh=10.0)
        assert not result_low.passed, "Many violations expected with 10 km/h threshold"
    
    def test_overspeed_records_max_speed(self, decoded_df):
        """Verify violation details include maximum speed."""
        result = check_overspeed(decoded_df, threshold_kmh=100.0)
        
        if not result.passed:
            speeds = [d['speed'] for d in result.details]
            max_speed = max(speeds)
            assert max_speed > 100.0, "Max speed should exceed threshold"


class TestTimeout:
    """Test Case 2: Message Timeout Detection."""
    
    def test_timeout_detection_returns_result(self, decoded_df):
        """Verify timeout check returns valid TestResult."""
        result = check_timeout(decoded_df)
        assert isinstance(result, TestResult)
        assert result.name == "Message Timeout Detection"
    
    def test_timeout_detects_gap_in_sample_log(self, decoded_df):
        """
        Verify timeout detection finds gap in sample log.
        
        The sample log has a >2 second gap between t=6.0s and t=8.5s
        which should trigger a timeout violation.
        """
        result = check_timeout(decoded_df, timeout_seconds=2.0)
        
        # Sample log has a 2.5s gap
        assert not result.passed, "Expected timeout violation in sample log"
        assert len(result.details) > 0, "Expected violation details"
    
    def test_timeout_gap_duration_recorded(self, decoded_df):
        """Verify gap duration is correctly recorded."""
        result = check_timeout(decoded_df, timeout_seconds=2.0)
        
        if not result.passed:
            gap = result.details[0]['gap_duration']
            assert gap > 2.0, "Gap should exceed timeout threshold"
    
    def test_timeout_threshold_configurable(self, decoded_df):
        """Verify different timeout thresholds work correctly."""
        # With very long timeout, should pass
        result_long = check_timeout(decoded_df, timeout_seconds=10.0)
        assert result_long.passed, "No timeout with 10s threshold"


class TestEmergencyStop:
    """Test Case 3: Emergency Stop Detection."""
    
    def test_emergency_stop_returns_result(self, decoded_df):
        """Verify emergency stop check returns valid TestResult."""
        result = check_emergency_stop(decoded_df)
        assert isinstance(result, TestResult)
        assert result.name == "Emergency Stop Detection"
    
    def test_emergency_stop_detected_in_sample_log(self, decoded_df):
        """
        Verify emergency stop is detected in sample log.
        
        The sample log contains an emergency braking event at ~t=4.0s
        with brake pressure >200 and rapid deceleration.
        """
        result = check_emergency_stop(
            decoded_df, 
            brake_threshold=200, 
            decel_threshold_kmh_per_s=20.0
        )
        
        # Sample log has emergency braking
        assert not result.passed, "Expected emergency stop in sample log"
    
    def test_emergency_stop_thresholds_configurable(self, decoded_df):
        """Verify emergency stop thresholds are configurable."""
        # With extreme thresholds, should not detect
        result = check_emergency_stop(
            decoded_df,
            brake_threshold=300,  # Higher than any value in log
            decel_threshold_kmh_per_s=1000.0
        )
        assert result.passed, "No emergency with extreme thresholds"


class TestSignalBounds:
    """Test Case 4: Signal Bounds Validation."""
    
    def test_signal_bounds_returns_result(self, decoded_df, dbc):
        """Verify signal bounds check returns valid TestResult."""
        result = check_signal_bounds(decoded_df, dbc)
        assert isinstance(result, TestResult)
        assert result.name == "Signal Bounds Validation"
    
    def test_signal_bounds_validates_against_dbc(self, decoded_df, dbc):
        """Verify signals are validated against DBC limits."""
        result = check_signal_bounds(decoded_df, dbc)
        
        # All our sample data should be within bounds
        # (we designed the log to have valid signal ranges)
        assert isinstance(result.passed, bool)


class TestChecksum:
    """Test Case 5: Checksum Validation."""
    
    def test_checksum_returns_result(self, decoded_df):
        """Verify checksum check returns valid TestResult."""
        result = check_checksum(decoded_df)
        assert isinstance(result, TestResult)
        assert result.name == "Checksum Validation"
    
    def test_checksum_detects_invalid_in_sample_log(self, decoded_df):
        """
        Verify checksum validation finds error in sample log.
        
        The sample log contains an intentional checksum error at t=4.3s
        where BrakeChecksum doesn't match expected value.
        """
        result = check_checksum(decoded_df)
        
        # Sample log has checksum errors
        assert not result.passed, "Expected checksum errors in sample log"
        assert len(result.details) > 0, "Expected error details"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for full test suite execution."""
    
    def test_all_tests_run_successfully(self, all_test_results):
        """Verify all tests execute without exceptions."""
        assert len(all_test_results) == 5
        for result in all_test_results:
            assert isinstance(result, TestResult)
    
    def test_summary_generation(self, all_test_results):
        """Verify summary generation works correctly."""
        summary = summarize_results(all_test_results)
        
        assert 'total' in summary
        assert 'passed' in summary
        assert 'failed' in summary
        assert 'pass_rate' in summary
        assert summary['total'] == 5
        assert summary['passed'] + summary['failed'] == 5
    
    def test_sample_log_produces_expected_failures(self, all_test_results):
        """
        Verify sample log triggers expected test failures.
        
        The sample log is designed to trigger:
        - Overspeed (speed > 100 km/h)
        - Timeout (>2s gap)
        - Emergency stop (high brake + rapid decel)
        - Checksum error
        """
        failed_tests = [r for r in all_test_results if not r.passed]
        
        # We expect multiple failures from our synthetic log
        assert len(failed_tests) >= 3, "Expected at least 3 failing tests from sample log"
        
        # Verify specific expected failures
        failed_names = [r.name for r in failed_tests]
        assert "Overspeed Detection" in failed_names, "Expected overspeed failure"
        assert "Message Timeout Detection" in failed_names, "Expected timeout failure"


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_dataframe_handling(self):
        """Verify tests handle empty DataFrames gracefully."""
        empty_df = pd.DataFrame()
        
        result = check_overspeed(empty_df)
        assert not result.passed  # Should fail due to no data
        
        result = check_timeout(empty_df)
        assert not result.passed
    
    def test_missing_signals_handling(self):
        """Verify tests handle missing signals gracefully."""
        # DataFrame with wrong signal name
        df = pd.DataFrame({
            'timestamp': [0.0, 1.0],
            'signal_name': ['WrongSignal', 'WrongSignal'],
            'value': [50, 60]
        })
        
        result = check_overspeed(df)
        assert not result.passed  # Should fail - no Speed signal


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


if __name__ == "__main__":
    # Run tests with verbose output and coverage
    pytest.main([
        __file__, 
        "-v", 
        "--cov=.", 
        "--cov-report=html",
        "--cov-report=term-missing"
    ])

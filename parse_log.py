"""
CAN Log Parser Module for ACC Test Suite

This module provides functionality to parse ASC (ASCII) format CAN logs
and decode signals using DBC database definitions.

Author: ACC Test Suite
Version: 1.0.0
"""

import re
import pandas as pd
import cantools
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


def load_dbc(dbc_path: str) -> cantools.database.Database:
    """
    Load a DBC (CAN Database) file using cantools.
    
    Args:
        dbc_path: Path to the DBC file
        
    Returns:
        cantools Database object
        
    Raises:
        FileNotFoundError: If DBC file doesn't exist
        cantools.database.errors.Error: If DBC parsing fails
    """
    path = Path(dbc_path)
    if not path.exists():
        raise FileNotFoundError(f"DBC file not found: {dbc_path}")
    
    return cantools.database.load_file(str(path))


def parse_asc_line(line: str) -> Optional[Tuple[float, int, bytes]]:
    """
    Parse a single line from an ASC log file.
    
    ASC format: timestamp channel id Tx/Rx d dlc byte0 byte1 ... byte7
    Example: 0.010000 1  100             Tx   d 8 E8 03 01 00 00 00 00 00
    
    Args:
        line: Single line from ASC file
        
    Returns:
        Tuple of (timestamp, can_id, data_bytes) or None if not a data line
    """
    # Skip header lines, comments, and non-data lines
    line = line.strip()
    if not line or line.startswith('date') or line.startswith('base') or \
       line.startswith('internal') or line.startswith('Begin') or \
       line.startswith('End') or 'Start of' in line:
        return None
    
    # Pattern for ASC data lines
    # Matches: timestamp channel id Tx/Rx d dlc data_bytes...
    pattern = r'^\s*(\d+\.?\d*)\s+\d+\s+([0-9A-Fa-f]+)\s+(?:Tx|Rx)\s+d\s+(\d+)\s+((?:[0-9A-Fa-f]{2}\s*)+)'
    
    match = re.match(pattern, line)
    if not match:
        return None
    
    timestamp = float(match.group(1))
    can_id = int(match.group(2), 16)
    dlc = int(match.group(3))
    data_hex = match.group(4).strip().split()
    
    # Convert hex bytes to bytes object
    data_bytes = bytes([int(b, 16) for b in data_hex[:dlc]])
    
    return timestamp, can_id, data_bytes


def parse_asc_log(log_path: str) -> List[Dict[str, Any]]:
    """
    Parse an ASC format CAN log file.
    
    Args:
        log_path: Path to ASC log file
        
    Returns:
        List of dictionaries with keys: timestamp, id, data
        
    Raises:
        FileNotFoundError: If log file doesn't exist
    """
    path = Path(log_path)
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")
    
    messages = []
    
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parsed = parse_asc_line(line)
            if parsed:
                timestamp, can_id, data = parsed
                messages.append({
                    'timestamp': timestamp,
                    'id': can_id,
                    'data': data
                })
    
    return messages


def decode_signals(messages: List[Dict[str, Any]], 
                   dbc: cantools.database.Database) -> pd.DataFrame:
    """
    Decode raw CAN messages to physical signal values using DBC.
    
    Args:
        messages: List of parsed CAN messages
        dbc: cantools Database object
        
    Returns:
        DataFrame with columns: timestamp, message_name, signal_name, value, raw_data
    """
    decoded_data = []
    
    for msg in messages:
        can_id = msg['id']
        timestamp = msg['timestamp']
        data = msg['data']
        
        try:
            # Find message definition in DBC
            message = dbc.get_message_by_frame_id(can_id)
            
            # Decode all signals in the message
            decoded_signals = message.decode(data)
            
            for signal_name, value in decoded_signals.items():
                decoded_data.append({
                    'timestamp': timestamp,
                    'message_name': message.name,
                    'message_id': can_id,
                    'signal_name': signal_name,
                    'value': value,
                    'raw_data': data.hex()
                })
                
        except KeyError:
            # Message ID not found in DBC - log as unknown
            decoded_data.append({
                'timestamp': timestamp,
                'message_name': 'UNKNOWN',
                'message_id': can_id,
                'signal_name': 'raw',
                'value': None,
                'raw_data': data.hex()
            })
        except Exception as e:
            # Decoding error - log with error info
            decoded_data.append({
                'timestamp': timestamp,
                'message_name': 'ERROR',
                'message_id': can_id,
                'signal_name': 'decode_error',
                'value': str(e),
                'raw_data': data.hex()
            })
    
    return pd.DataFrame(decoded_data)


def get_signal_timeseries(df: pd.DataFrame, signal_name: str) -> pd.DataFrame:
    """
    Extract a time series for a specific signal.
    
    Args:
        df: Decoded signals DataFrame
        signal_name: Name of the signal to extract
        
    Returns:
        DataFrame with timestamp and value columns for the signal
    """
    signal_df = df[df['signal_name'] == signal_name][['timestamp', 'value']].copy()
    signal_df = signal_df.sort_values('timestamp').reset_index(drop=True)
    return signal_df


def get_message_timeseries(df: pd.DataFrame, message_name: str) -> pd.DataFrame:
    """
    Extract all signals for a specific message as time series.
    
    Args:
        df: Decoded signals DataFrame
        message_name: Name of the CAN message
        
    Returns:
        DataFrame pivoted with timestamp as index and signals as columns
    """
    msg_df = df[df['message_name'] == message_name].copy()
    
    if msg_df.empty:
        return pd.DataFrame()
    
    # Pivot to get signals as columns
    pivot_df = msg_df.pivot_table(
        index='timestamp',
        columns='signal_name',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    return pivot_df


def calculate_message_intervals(messages: List[Dict[str, Any]], 
                                 message_id: int) -> List[float]:
    """
    Calculate time intervals between consecutive messages of the same ID.
    
    Args:
        messages: List of parsed CAN messages
        message_id: CAN message ID to analyze
        
    Returns:
        List of time intervals in seconds
    """
    timestamps = [m['timestamp'] for m in messages if m['id'] == message_id]
    timestamps.sort()
    
    if len(timestamps) < 2:
        return []
    
    intervals = [timestamps[i+1] - timestamps[i] 
                 for i in range(len(timestamps) - 1)]
    
    return intervals


def load_and_decode_log(log_path: str, dbc_path: str) -> pd.DataFrame:
    """
    Convenience function to load and decode a CAN log in one step.
    
    Args:
        log_path: Path to ASC log file
        dbc_path: Path to DBC file
        
    Returns:
        DataFrame with decoded signals
    """
    dbc = load_dbc(dbc_path)
    messages = parse_asc_log(log_path)
    return decode_signals(messages, dbc)


if __name__ == "__main__":
    # Example usage
    import os
    
    script_dir = Path(__file__).parent
    dbc_path = script_dir / "acc_signals.dbc"
    log_path = script_dir / "sample_can_log.asc"
    
    if dbc_path.exists() and log_path.exists():
        print("Loading DBC file...")
        dbc = load_dbc(str(dbc_path))
        print(f"Loaded {len(dbc.messages)} message definitions")
        
        print("\nParsing ASC log...")
        messages = parse_asc_log(str(log_path))
        print(f"Parsed {len(messages)} CAN messages")
        
        print("\nDecoding signals...")
        df = decode_signals(messages, dbc)
        print(f"Decoded {len(df)} signal values")
        
        print("\nSignal summary:")
        for signal in df['signal_name'].unique():
            signal_df = get_signal_timeseries(df, signal)
            if not signal_df.empty and signal_df['value'].dtype in ['int64', 'float64']:
                print(f"  {signal}: min={signal_df['value'].min():.2f}, "
                      f"max={signal_df['value'].max():.2f}, "
                      f"count={len(signal_df)}")
    else:
        print("DBC or log file not found. Run from project directory.")

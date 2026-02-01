import cantools

# Load DBC
db = cantools.database.load_file('example.dbc')

# Print first message details
first_msg = db.messages[0]
print(f"First message: {first_msg.name} (ID: {hex(first_msg.frame_id)})")
print("Signals:", [s.name for s in first_msg.signals])

# Test decode with fake data
fake_data = [41, 0, 0, 0, 0, 0, 0, 0]  # Common test pattern
try:
    signals = first_msg.decode(fake_data)
    print("Decoded signals:", signals)
except:
    print("Decode failed - normal for unknown DBC")

import can
bus = can.interface.Bus()  # Virtual CAN bus
overspeed = can.Message(arbitration_id=0x101, data=[255,255,10,0,0,0,0,0])  # 120kmh
bus.send(overspeed)
print("✅ Manual OVERSPEED injected - test would PASS now")

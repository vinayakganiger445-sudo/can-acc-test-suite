import can

bus = can.interface.Bus(interface='virtual', channel='test1')  

# OVERSPEED message (ID 0x101 = Speed, 120kmh)
overspeed = can.Message(arbitration_id=0x101, data=[255,255,10,0,0,0,0,0])
bus.send(overspeed)
print("✅ Manual OVERSPEED injected - 120kmh on virtual CAN bus")
print("This would make test_overspeed() PASS")

bus.shutdown()  

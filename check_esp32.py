import serial
import time

def check_esp32():
    try:
        # Open serial port
        ser = serial.Serial('COM4', 115200, timeout=1)
        print("Port opened successfully")
        
        # Send sync command
        ser.write(b'\r\n')
        time.sleep(1)
        
        # Read response
        if ser.in_waiting:
            response = ser.read(ser.in_waiting)
            print(f"Response: {response}")
        
        # Close port
        ser.close()
        print("Port closed successfully")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_esp32() 
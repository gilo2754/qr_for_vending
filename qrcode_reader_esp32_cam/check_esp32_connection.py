import serial
import time

def check_esp32():
    try:
        # Open serial port with lower baud rate
        ser = serial.Serial('COM4', 57600, timeout=1)
        print("Port opened successfully")
        
        # Send sync command
        print("Sending sync command...")
        ser.write(b'\r\n')
        time.sleep(2)  # Wait longer for response
        
        # Read response
        if ser.in_waiting:
            response = ser.read(ser.in_waiting)
            print(f"Response: {response}")
        else:
            print("No response received")
        
        # Close port
        ser.close()
        print("Port closed successfully")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_esp32() 
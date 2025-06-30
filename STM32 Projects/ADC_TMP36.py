import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import time

# === Serial Configuration ===
COM_PORT = 'COM4'           # Update as needed
BAUD_RATE = 9600

try:
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to {COM_PORT} at {BAUD_RATE} baud")
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit(1)

# === Data Setup ===
MAX_POINTS = 100
temp_data = deque([0.0] * MAX_POINTS, maxlen=MAX_POINTS)
time_data = deque(range(MAX_POINTS), maxlen=MAX_POINTS)

# === Matplotlib Setup ===
plt.ion()  # Turn on interactive mode
fig, ax = plt.subplots(figsize=(10, 6))
line, = ax.plot(time_data, temp_data, 'b-', linewidth=2)
ax.set_ylim(15, 50)  # Adjust temperature range as needed
ax.set_xlim(0, MAX_POINTS)
ax.set_title("Real-Time Temperature from STM32", fontsize=14)
ax.set_xlabel("Time (samples)")
ax.set_ylabel("Temperature (°C)")
ax.grid(True, alpha=0.3)

# Add text display for current temperature
temp_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, 
                   fontsize=12, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# === Update Function ===
def update(frame):
    try:
        if ser.in_waiting > 0:  # Check if data is available
            line_bytes = ser.readline()
            decoded = line_bytes.decode('utf-8').strip()
            
            if decoded:  # Make sure we have data
                print(f"Received: {decoded}")  # Debug output
                
                # Try different parsing methods
                temp_value = None
                
                # Method 1: Look for °C
                if "°C" in decoded:
                    temp_str = decoded.split("°")[0]
                    # Extract just the number part
                    temp_str = ''.join(c for c in temp_str if c.isdigit() or c == '.' or c == '-')
                    if temp_str:
                        temp_value = float(temp_str)
                
                # Method 2: Look for just a number (if no °C symbol)
                elif decoded.replace('.', '').replace('-', '').isdigit():
                    temp_value = float(decoded)
                
                # Method 3: Extract first number found
                else:
                    import re
                    numbers = re.findall(r'-?\d+\.?\d*', decoded)
                    if numbers:
                        temp_value = float(numbers[0])
                
                if temp_value is not None:
                    # Update data
                    temp_data.append(temp_value)
                    time_data.append(time_data[-1] + 1 if len(time_data) > 0 else 0)
                    
                    # Update plot
                    line.set_data(time_data, temp_data)
                    
                    # Auto-scale y-axis if needed
                    if temp_value < ax.get_ylim()[0] or temp_value > ax.get_ylim()[1]:
                        ax.set_ylim(min(temp_data) - 2, max(temp_data) + 2)
                    
                    # Update x-axis to show sliding window
                    ax.set_xlim(time_data[0], time_data[-1])
                    
                    # Update temperature display
                    temp_text.set_text(f'Current Temp: {temp_value:.1f}°C')
                    
                    print(f"Temperature: {temp_value}°C")  # Debug output
                
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        return line,
    except ValueError as e:
        print(f"Value error (couldn't parse temperature): {e}")
        return line,
    except Exception as e:
        print(f"Unexpected error: {e}")
        return line,
    
    return line,

# === Start Animation ===
print("Starting real-time temperature monitoring...")
print("Press Ctrl+C to stop")

try:
    ani = animation.FuncAnimation(fig, update, interval=100, blit=False, cache_frame_data=False)
    plt.tight_layout()
    plt.show()
    
    # Keep the program running
    while True:
        plt.pause(0.01)
        
except KeyboardInterrupt:
    print("\nStopping...")
finally:
    if ser.is_open:
        ser.close()
        print("Serial port closed")
    plt.close('all')

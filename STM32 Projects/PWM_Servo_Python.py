# This code belongs to the YouTube Video https://youtu.be/ueq3rqgOjj0 
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from collections import deque
import time
import re
from matplotlib.patches import Wedge, Circle
import matplotlib.patches as patches

class ServoVisualizer:
    def __init__(self, port='COM4', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.current_angle = 0
        self.start_time = time.time()
        
        # Initialize serial connection
        self.init_serial()
        
        # Setup the plot
        self.setup_plot()
    
    def init_serial(self):
        """Initialize serial connection"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"Connected to {self.port} at {self.baudrate} baud")
        except serial.SerialException as e:
            print(f"Error connecting to serial port: {e}")
            exit(1)
    
    def get_color_for_angle(self, angle):
        """Get color based on angle (0-180 degrees)"""
        # Normalize angle to 0-1 range
        normalized = angle / 180.0
        
        # Create smooth color transition: Blue -> Green -> Yellow -> Orange -> Red
        if normalized <= 0.25:  # 0-45 degrees: Blue to Green
            ratio = normalized * 4
            color = (0, ratio, 1 - ratio)
        elif normalized <= 0.5:  # 45-90 degrees: Green to Yellow
            ratio = (normalized - 0.25) * 4
            color = (ratio, 1, 0)
        elif normalized <= 0.75:  # 90-135 degrees: Yellow to Orange
            ratio = (normalized - 0.5) * 4
            color = (1, 1 - ratio * 0.5, 0)
        else:  # 135-180 degrees: Orange to Red
            ratio = (normalized - 0.75) * 4
            color = (1, 0.5 - ratio * 0.5, 0)
        
        return color
    
    def setup_plot(self):
        """Setup the matplotlib plot"""
        self.fig, self.ax = plt.subplots(1, 1, figsize=(8, 8))
        
        # Circular gauge setup
        self.ax.set_xlim(-2, 2)
        self.ax.set_ylim(-2, 2)
        self.ax.set_aspect('equal')
        self.ax.set_title('STM32 Nucleo32-F303K8 Servo Position Monitor', fontsize=20, fontweight='bold', pad=20)
        self.fig.canvas.manager.set_window_title('STM32 Nucleo32-F303K8 Servo Control Dashboard')

        self.ax.axis('off')
        
        # Set background color
        self.fig.patch.set_facecolor("#ececce")
        self.ax.set_facecolor("#0F0F0F")
        
        # Draw the gauge background
        self.draw_gauge_background()
        
        # Initialize dynamic elements
        self.servo_arm, = self.ax.plot([0, 0], [0, 1.3], linewidth=8, alpha=0.9)
        self.angle_text = self.ax.text(0, -1.7, '0°', ha='center', va='center', 
                                       fontsize=28, fontweight='bold', color='white')
        
        # Position indicator circle
        self.position_circle = Circle((0, 0), 0.15, facecolor='white', edgecolor='black', 
                                     linewidth=3, alpha=0.9, zorder=10)
        self.ax.add_patch(self.position_circle)
        
        # Create colored arc segments for the range indicator
        self.create_colored_arc()
        
        plt.tight_layout()
    
    def create_colored_arc(self):
        """Create colored arc segments showing the servo range"""
        num_segments = 36  # 5-degree segments
        self.arc_patches = []
        
        for i in range(num_segments):
            start_angle = i * 5
            end_angle = (i + 1) * 5
            color = self.get_color_for_angle(start_angle + 2.5)  # Use middle of segment
            
            # Create wedge for each segment
            wedge = Wedge(center=(0, 0), r=1.7, theta1=start_angle, theta2=end_angle,
                         facecolor=color, edgecolor='white', linewidth=0.5, alpha=0.8)
            self.ax.add_patch(wedge)
            self.arc_patches.append(wedge)
    
    def draw_gauge_background(self):
        """Draw the circular gauge background"""
        # Outer ring
        outer_ring = Circle((0, 0), 1.8, fill=False, edgecolor='black', linewidth=4, alpha=0.8)
        self.ax.add_patch(outer_ring)
        
        # Inner ring
        inner_ring = Circle((0, 0), 1.5, fill=False, edgecolor='black', linewidth=2, alpha=0.6)
        self.ax.add_patch(inner_ring)
        
        # Draw major angle markers and labels
        for angle in range(0, 181, 30):
            rad = np.radians(angle)
            
            # Major tick marks
            x1 = 1.5 * np.cos(rad)
            y1 = 1.5 * np.sin(rad)
            x2 = 1.65 * np.cos(rad)
            y2 = 1.65 * np.sin(rad)
            
            self.ax.plot([x1, x2], [y1, y2], 'black', linewidth=4, alpha=0.8)
            
            # Angle labels
            x_label = 1.9 * np.cos(rad)
            y_label = 1.9 * np.sin(rad)
            self.ax.text(x_label, y_label, f'{angle}°', ha='center', va='center', 
                         fontsize=14, fontweight='bold', color='black')
        
        # Draw minor angle markers
        for angle in range(0, 181, 15):
            if angle % 30 != 0:  # Skip major markers
                rad = np.radians(angle)
                x1 = 1.55 * np.cos(rad)
                y1 = 1.55 * np.sin(rad)
                x2 = 1.65 * np.cos(rad)
                y2 = 1.65 * np.sin(rad)
                
                self.ax.plot([x1, x2], [y1, y2], 'black', linewidth=2, alpha=0.6)
        
        # Center dot
        center_dot = Circle((0, 0), 0.05, facecolor='white', edgecolor='black', 
                           linewidth=2, zorder=15)
        self.ax.add_patch(center_dot)
        
        # Add title and info
        self.ax.text(0, 2.05, 'SERVO ANGLE', ha='center', va='center', 
                     fontsize=16, fontweight='bold', color='purple', alpha=0.8)
    
    def read_serial_data(self):
        """Read and parse serial data"""
        if self.ser and self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                
                # Parse the angle from the format "ANGLE:XXX"
                match = re.match(r'ANGLE:(\d+)', line)
                if match:
                    angle = int(match.group(1))
                    # Ensure angle is within valid range
                    if 0 <= angle <= 180:
                        self.current_angle = angle
                        return True
            except (UnicodeDecodeError, ValueError) as e:
                print(f"Error parsing serial data: {e}")
        return False
    
    def update_plot(self, frame):
        """Update the plot with new data"""
        # Read new data
        self.read_serial_data()
        
        # Get color for current angle
        current_color = self.get_color_for_angle(self.current_angle)
        
        # Update servo arm
        angle_rad = np.radians(self.current_angle)
        x = 1.3 * np.cos(angle_rad)
        y = 1.3 * np.sin(angle_rad)
        
        self.servo_arm.set_data([0, x], [0, y])
        self.servo_arm.set_color(current_color)
        
        # Update position indicator
        pos_x = 1.45 * np.cos(angle_rad)
        pos_y = 1.45 * np.sin(angle_rad)
        self.position_circle.center = (pos_x, pos_y)
        self.position_circle.set_facecolor(current_color)
        
        # Update angle text with color
        self.angle_text.set_text(f'{self.current_angle}°')
        self.angle_text.set_color(current_color)
        
        # Add glow effect to current position on arc
        current_segment = int(self.current_angle / 5)
        if 0 <= current_segment < len(self.arc_patches):
            # Reset all segments to normal alpha
            for patch in self.arc_patches:
                patch.set_alpha(0.8)
            
            # Highlight current segment
            self.arc_patches[current_segment].set_alpha(1.0)
            self.arc_patches[current_segment].set_linewidth(2)
        
        return [self.servo_arm, self.angle_text, self.position_circle] + self.arc_patches
    
    def start_animation(self):
        """Start the real-time animation"""
        self.ani = animation.FuncAnimation(self.fig, self.update_plot, 
                                         interval=50, blit=True, cache_frame_data=False)
        plt.show()
    
    def close(self):
        """Close the serial connection"""
        if self.ser:
            self.ser.close()
            print("Serial connection closed")

def main():
    """Main function"""    
    print("STM32 Servo Position Visualizer")
    print("=" * 50)    
    
    try:
        visualizer = ServoVisualizer(port='COM4', baudrate=9600)
        print("\nStarting visualization...")
        print("Color coding: Blue (0°) -> Green (45°) -> Yellow (90°) -> Orange (135°) -> Red (180°)")
        print("Close the plot window to exit.")
        visualizer.start_animation()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'visualizer' in locals():
            visualizer.close()

if __name__ == "__main__":
    main()

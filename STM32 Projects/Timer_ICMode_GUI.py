# This code belongs to the YouTube Video "Real-Time Frequency Measurement STM32 using Input Capture Mode of Timer and Python for Data Display" at https://youtu.be/mEHG08xiqEc 

import serial
from collections import deque
import numpy as np
import time
import threading
import tkinter as tk
from tkinter import ttk
import re

class FrequencyMonitor:
    def __init__(self, port='COM4', baudrate=38400):
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        self.frequencies = deque(maxlen=100)  # Store last 100 readings
        self.timestamps = deque(maxlen=100)
        self.current_frequency = 0
        self.running = False
        
        # GUI setup
        self.root = tk.Tk()
        self.root.title("STM32 Nucleo32-F303K8 Frequency Monitor- Timer Input Capture Mode")
        self.root.geometry("800x600")
        
        # Create GUI elements
        self.setup_gui()
        
        # Setup matplotlib
      #  self.setup_plot()
        
    def setup_gui(self):
        # Control frame
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10, padx=10, fill='x')
        
        # Port selection
        ttk.Label(control_frame, text="COM Port:").grid(row=0, column=0, sticky='w')
        self.port_var = tk.StringVar(value=self.port)
        port_entry = ttk.Entry(control_frame, textvariable=self.port_var, width=10)
        port_entry.grid(row=0, column=1, padx=5)
        
        # Baudrate selection
        ttk.Label(control_frame, text="Baudrate:").grid(row=0, column=2, sticky='w', padx=(20,0))
        self.baudrate_var = tk.StringVar(value=str(self.baudrate))
        baudrate_combo = ttk.Combobox(control_frame, textvariable=self.baudrate_var, 
                                     values=['9600', '38400', '115200'], width=10)
        baudrate_combo.grid(row=0, column=3, padx=5)
        
        # Control buttons       
        self.start_btn = ttk.Button(control_frame, text="Start", command=self.start_monitoring)
        self.start_btn.grid(row=0, column=4, padx=10)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.stop_monitoring, state='disabled')
        self.stop_btn.grid(row=0, column=5, padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(self.root, text="Current Reading", padding=10)
        status_frame.pack(pady=10, padx=10, fill='x')
        
        self.freq_label = ttk.Label(status_frame, text="Frequency: --- Hz", 
                                   font=('Arial', 16, 'bold'))
        self.freq_label.pack()
        
        self.status_label = ttk.Label(status_frame, text="Status: Disconnected", 
                                     font=('Arial', 10))
        self.status_label.pack()
        
        # Raw data display
        data_frame = ttk.LabelFrame(self.root, text="Raw Data", padding=10)
        data_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        self.text_display = tk.Text(data_frame, height=10, width=80)
        scrollbar = ttk.Scrollbar(data_frame, orient="vertical", command=self.text_display.yview)
        self.text_display.configure(yscrollcommand=scrollbar.set)
        
        self.text_display.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def start_monitoring(self):
        try:
            self.port = self.port_var.get()
            self.baudrate = int(self.baudrate_var.get())
            
            # Open serial connection
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            self.running = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.status_label.config(text=f"Status: Connected to {self.port}")
            
            # Start reading thread
            self.read_thread = threading.Thread(target=self.read_serial_data)
            self.read_thread.daemon = True
            self.read_thread.start()
                  
            
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            self.running = False
            
    def stop_monitoring(self):
        self.running = False
        if self.serial_connection:
            self.serial_connection.close()
            
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_label.config(text="Status: Disconnected")
        
    def read_serial_data(self):
        start_time = time.time()
        
        while self.running:
            try:
                if self.serial_connection and self.serial_connection.in_waiting:
                    line = self.serial_connection.readline().decode('utf-8').strip()
                    
                    if line:
                        # Update text display
                        self.text_display.insert(tk.END, line + '\n')
                        self.text_display.see(tk.END)
                        
                        # Extract frequency from line
                        freq_match = re.search(r'Frequency:\s*(\d+)\s*Hz', line)
                        if freq_match:
                            frequency = int(freq_match.group(1))
                            current_time = time.time() - start_time
                            
                            self.frequencies.append(frequency)
                            self.timestamps.append(current_time)
                            self.current_frequency = frequency
                            
                            # Update frequency label
                            self.freq_label.config(text=f"Frequency: {frequency} Hz")
                            
                time.sleep(0.01)  # Small delay to prevent high CPU usage
                
            except Exception as e:
                self.status_label.config(text=f"Read Error: {str(e)}")
                break                   
            
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":    
    print("STM32 Nucleo32-F303K8 Frequency Monitor- Timer Input Capture Mode")
    print()
    
    # Create and run the monitor
    monitor = FrequencyMonitor(port='COM4', baudrate=9600)  # Adjust COM port as needed
    monitor.run()

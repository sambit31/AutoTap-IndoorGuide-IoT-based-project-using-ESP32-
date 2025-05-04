import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
import serial
import time
from collections import deque
import math
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk

# Serial port configuration
ser = serial.Serial('COM10', 115200)

# Room dimensions and anchor positions
ROOM_WIDTH = 2.0  # meters
ROOM_HEIGHT = 3.0  # meters
coordinates = {
    'F2:09:0D:54:77:58': (-1, 1.5),
    '1C:69:20:A3:C4:11': (1, 1.5),
    'F0:09:0D:14:77:58': (-1, -1.5),
    'F2:09:0D:44:77:58': (1, -1.5)
}

# RSSI averaging buffers
rssi_buffers = {mac: deque(maxlen=5) for mac in coordinates.keys()}

class KalmanFilter2D:
    def __init__(self, process_variance=1e-4, measurement_variance=0.1):
        self.x = 0.0
        self.y = 0.0
        self.P = 1.0
        self.Q = process_variance
        self.R = measurement_variance

    def update(self, measured_x, measured_y):
        self.P += self.Q
        K = self.P / (self.P + self.R)
        self.x += K * (measured_x - self.x)
        self.y += K * (measured_y - self.y)
        self.P *= (1 - K)
        return self.x, self.y

# Initialize Kalman filter
kalman = KalmanFilter2D()

# Create grid for heatmap
x = np.linspace(-ROOM_WIDTH/2, ROOM_WIDTH/2, 100)
y = np.linspace(-ROOM_HEIGHT/2, ROOM_HEIGHT/2, 100)
X, Y = np.meshgrid(x, y)

# Store latest RSSI values
rssi_values = {mac: -100 for mac in coordinates.keys()}

def rssi_to_distance(rssi):
    # Simple path loss model (adjust constants based on your environment)
    return 10 ** ((-69 - rssi) / (10 * 2))

def trilaterate():
    # Get smoothed RSSI values
    smoothed_rssi = {mac: sum(buffer)/len(buffer) if buffer else -100 
                    for mac, buffer in rssi_buffers.items()}
    
    # Convert to distances
    distances = {mac: rssi_to_distance(rssi) 
                for mac, rssi in smoothed_rssi.items()}
    
    # Simple weighted average of anchor positions
    total_weight = sum(1/d for d in distances.values() if d > 0)
    if total_weight == 0:
        return 0, 0
    
    x_pos = sum(coordinates[mac][0] * (1/d) for mac, d in distances.items() if d > 0) / total_weight
    y_pos = sum(coordinates[mac][1] * (1/d) for mac, d in distances.items() if d > 0) / total_weight
    
    return x_pos, y_pos

def read_serial_data():
    if ser.in_waiting:
        try:
            line = ser.readline().decode('utf-8').strip()
            mac, rssi = line.split(',')
            if mac in rssi_buffers:
                rssi_buffers[mac].append(float(rssi))
        except:
            pass

class TrackingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Position Tracking")
        
        # Initialize variables
        self.is_calibrating = False
        self.baseline_rssi = {mac: deque(maxlen=100) for mac in coordinates.keys()}
        self.baseline_values = None
        self.rssi_buffers = {mac: deque(maxlen=5) for mac in coordinates.keys()}
        self.serial_logs = []
        
        # Print initial state
        print("Initial state:")
        for mac in coordinates.keys():
            print(f"{mac}: baseline_rssi={list(self.baseline_rssi[mac])}")
        
        # Create GUI elements
        self.setup_gui()
        
        # Initialize Kalman filter
        self.kalman = KalmanFilter2D()
        
    def setup_gui(self):
        # Create main frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure
        self.fig = plt.Figure(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Create control frame
        control_frame = tk.Frame(main_frame)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Calibration button
        self.calibrate_btn = tk.Button(control_frame, text="Calibrate", 
                                     command=self.start_calibration)
        self.calibrate_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Status label
        self.status_label = tk.Label(control_frame, text="Status: Ready")
        self.status_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Calibration progress
        self.progress_label = tk.Label(control_frame, text="")
        self.progress_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Log text widget
        self.log_text = tk.Text(control_frame, wrap=tk.NONE, height=5, width=50)
        self.log_text.pack(side=tk.LEFT, padx=5, pady=5)
        
    def start_calibration(self):
        print("\nStarting calibration...")
        self.is_calibrating = True
        self.calibrate_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Calibrating")
        
        # Clear previous calibration data
        for mac in coordinates.keys():
            self.baseline_rssi[mac].clear()
            print(f"Cleared buffer for {mac}")
        
        self.calibration_start_time = time.time()
        self.calibrate()
        
    def calibrate(self):
        # Read all available serial data
        while ser.in_waiting:
            try:
                raw_data = ser.readline()
                line = raw_data.decode('utf-8').strip()
                self.log_serial_data(line)
                
                if line.startswith('[ROOT] RSSI from MAC'):
                    # Extract MAC and RSSI using a more robust method
                    mac_start = line.find('MAC') + 4  # Find start of MAC address
                    mac_end = line.rfind(':')  # Find last colon before RSSI
                    rssi_start = mac_end + 1  # Start of RSSI value
                    
                    mac = line[mac_start:mac_end].strip()
                    rssi = float(line[rssi_start:].strip())
                    
                    print(f"Raw line: {line}")  # Debug print
                    print(f"Parsed MAC: {mac}, RSSI: {rssi}")  # Debug print
                    
                    if mac in self.baseline_rssi:
                        self.baseline_rssi[mac].append(rssi)
                        print(f"Calibration RSSI for {mac}: {rssi}")
                        print(f"Current buffer for {mac}: {list(self.baseline_rssi[mac])}")
                    else:
                        print(f"Unknown MAC: {mac}")  # Debug print
            except UnicodeDecodeError:
                print(f"Error decoding data: {raw_data}")
                continue
            except Exception as e:
                print(f"Error in calibration: {str(e)}")
                continue
        
        # Update progress
        elapsed = time.time() - self.calibration_start_time
        remaining = max(0, 5 - elapsed)
        self.progress_label.config(text=f"Calibrating... {remaining:.1f}s remaining")
        
        # Update display
        self.update_display(is_calibrating=True)
        
        # Continue calibration for 5 seconds
        if time.time() - self.calibration_start_time < 5:
            self.root.after(100, self.calibrate)
        else:
            self.finish_calibration()
    
    def finish_calibration(self):
        # Calculate baseline values from the collected RSSI data
        self.baseline_values = {}
        for mac, buffer in self.baseline_rssi.items():
            if buffer:  # Only calculate if we have data
                avg_rssi = sum(buffer) / len(buffer)
                self.baseline_values[mac] = avg_rssi
                print(f"Calibration complete for {mac}: {avg_rssi:.1f} dBm")
                print(f"Final buffer for {mac}: {list(buffer)}")
            else:
                self.baseline_values[mac] = -100  # Default value if no data
                print(f"No calibration data for {mac}")
        
        self.is_calibrating = False
        self.calibrate_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Tracking")
        
        # Start tracking animation
        self.ani = FuncAnimation(self.fig, self.update, interval=100, cache_frame_data=False)
        self.canvas.draw()
    
    def update(self, frame):
        if self.is_calibrating:
            return
        
        self.read_serial_data()
        self.update_display(is_calibrating=False)

    def read_serial_data(self):
        if ser.in_waiting:
            try:
                raw_data = ser.readline()
                line = raw_data.decode('utf-8').strip()
                
                if line.startswith('[ROOT] RSSI from MAC'):
                    # Extract MAC and RSSI using a more robust method
                    mac_start = line.find('MAC') + 4  # Find start of MAC address
                    mac_end = line.rfind(':')  # Find last colon before RSSI
                    rssi_start = mac_end + 1  # Start of RSSI value
                    
                    mac = line[mac_start:mac_end].strip()
                    rssi = float(line[rssi_start:].strip())
                    
                    if mac in self.rssi_buffers:
                        self.rssi_buffers[mac].append(rssi)
                        print(f"Tracking RSSI for {mac}: {rssi}")
            except UnicodeDecodeError:
                print(f"Error decoding data: {raw_data}")
                return
            except Exception as e:
                print(f"Error in read_serial_data: {str(e)}")
                return

    def trilaterate(self):
        # Get smoothed RSSI values
        smoothed_rssi = {mac: sum(buffer)/len(buffer) if buffer else -100 
                        for mac, buffer in self.rssi_buffers.items()}
        
        # Convert to distances
        distances = {mac: rssi_to_distance(rssi) 
                    for mac, rssi in smoothed_rssi.items()}
        
        # Simple weighted average of anchor positions
        total_weight = sum(1/d for d in distances.values() if d > 0)
        if total_weight == 0:
            return 0, 0
        
        x_pos = sum(coordinates[mac][0] * (1/d) for mac, d in distances.items() if d > 0) / total_weight
        y_pos = sum(coordinates[mac][1] * (1/d) for mac, d in distances.items() if d > 0) / total_weight
        
        return x_pos, y_pos

    def update_display(self, is_calibrating=False):
        self.fig.clf()
        ax = self.fig.add_subplot(111)
        
        # Create heatmap
        Z = np.zeros_like(X)
        for mac, (x0, y0) in coordinates.items():
            signal_strength = 0  # Initialize signal_strength
            if is_calibrating:
                # Use baseline RSSI during calibration
                if self.baseline_rssi[mac]:
                    avg_rssi = sum(self.baseline_rssi[mac])/len(self.baseline_rssi[mac])
                    signal_strength = np.exp((avg_rssi + 100) / 20)
                    print(f"Displaying calibration RSSI for {mac}: {avg_rssi:.1f} dBm")
            else:
                # Use current RSSI during tracking
                if self.rssi_buffers[mac]:
                    avg_rssi = sum(self.rssi_buffers[mac])/len(self.rssi_buffers[mac])
                    signal_strength = np.exp((avg_rssi + 100) / 20)
            
            Z += signal_strength * np.exp(-((X - x0)**2 + (Y - y0)**2))
        
        # Plot heatmap and colorbar
        mesh = ax.pcolormesh(X, Y, Z, shading='auto', cmap='hot', alpha=0.5)
        self.fig.colorbar(mesh, ax=ax, label='Signal Strength')
        
        # Plot anchors
        ax.scatter([p[0] for p in coordinates.values()], 
                  [p[1] for p in coordinates.values()], 
                  c='white', edgecolors='black', s=100)
        
        # Add RSSI values and MAC addresses
        for mac, (x0, y0) in coordinates.items():
            if is_calibrating:
                # Show calibration RSSI
                if self.baseline_rssi[mac]:
                    avg_rssi = sum(self.baseline_rssi[mac])/len(self.baseline_rssi[mac])
                    ax.text(x0, y0 + 0.2, f"{mac}\n{avg_rssi:.1f} dBm (Calibrating)", 
                           ha='center', va='bottom', color='white',
                           bbox=dict(facecolor='black', alpha=0.5, edgecolor='none'))
            else:
                # Show tracking RSSI
                if self.rssi_buffers[mac]:
                    avg_rssi = sum(self.rssi_buffers[mac])/len(self.rssi_buffers[mac])
                    ax.text(x0, y0 + 0.2, f"{mac}\n{avg_rssi:.1f} dBm", 
                           ha='center', va='bottom', color='white',
                           bbox=dict(facecolor='black', alpha=0.5, edgecolor='none'))
        
        if not is_calibrating:
            # Only show position during tracking
            raw_x, raw_y = self.trilaterate()
            x_pos, y_pos = self.kalman.update(raw_x, raw_y)
            ax.scatter(x_pos, y_pos, c='blue', s=200, marker='x')
        
        ax.set_title('Calibrating...' if is_calibrating else 'Live Position Tracking')
        ax.set_xlabel('X Coordinate (m)')
        ax.set_ylabel('Y Coordinate (m)')
        ax.grid(True)
        ax.set_xlim(-ROOM_WIDTH/2, ROOM_WIDTH/2)
        ax.set_ylim(-ROOM_HEIGHT/2, ROOM_HEIGHT/2)
        
        self.canvas.draw()

    def log_serial_data(self, line):
        self.serial_logs.append(line)
        if len(self.serial_logs) > 1000:  # Keep last 1000 lines
            self.serial_logs.pop(0)
            
        # Update log display
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, '\n'.join(self.serial_logs[-50:]))  # Show last 50 lines
        self.log_text.see(tk.END)  # Scroll to bottom
        self.log_text.config(state=tk.DISABLED)

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = TrackingApp(root)
    root.mainloop()
    ser.close()

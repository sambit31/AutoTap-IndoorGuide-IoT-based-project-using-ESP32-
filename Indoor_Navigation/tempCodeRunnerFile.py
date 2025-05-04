
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

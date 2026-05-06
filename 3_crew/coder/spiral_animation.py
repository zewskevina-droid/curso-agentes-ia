
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def generate_spiral(num_loops, points_per_loop):
    theta = np.linspace(0, num_loops * 2 * np.pi, num_loops * points_per_loop)
    r = np.linspace(0, 1, num_loops * points_per_loop)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return x, y

def animate_spiral(num_loops, points_per_loop):
    x, y = generate_spiral(num_loops, points_per_loop)
    
    fig, ax = plt.subplots()
    ax.axis('equal')
    line, = ax.plot([], [], lw=2)

    def init():
        line.set_data([], [])
        return line,

    def update(frame):
        line.set_data(x[:frame], y[:frame])
        return line,

    ani = FuncAnimation(fig, update, frames=len(x), init_func=init, blit=True)
    plt.show()

num_loops = 5
points_per_loop = 100
animate_spiral(num_loops, points_per_loop)

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
from .terrain import generate_reference_and_limits
#importing pandas package 
import pandas as pd

class Submarine:
    def __init__(self):

        self.mass = 1
        self.drag = 0.1
        self.actuator_gain = 1

        self.dt = 1 # Time step for discrete time simulation

        self.pos_x = 0
        self.pos_y = 0
        self.vel_x = 1 # Constant velocity in x direction
        self.vel_y = 0


    def transition(self, action: float, disturbance: float):
        self.pos_x += self.vel_x * self.dt
        self.pos_y += self.vel_y * self.dt

        force_y = -self.drag * self.vel_y + self.actuator_gain * (action + disturbance)
        acc_y = force_y / self.mass
        self.vel_y += acc_y * self.dt

    def get_depth(self) -> float:
        return self.pos_y
    
    def get_position(self) -> tuple:
        return self.pos_x, self.pos_y
    
    def reset_state(self):
        self.pos_x = 0
        self.pos_y = 0
        self.vel_x = 1
        self.vel_y = 0
    
class Trajectory:
    def __init__(self, position: np.ndarray):
        self.position = position  
        
    def plot(self):
        plt.plot(self.position[:, 0], self.position[:, 1])
        plt.show()

    def plot_completed_mission(self, mission: Mission):
        x_values = np.arange(len(mission.reference))
        min_depth = np.min(mission.cave_depth)
        max_height = np.max(mission.cave_height)

        plt.fill_between(x_values, mission.cave_height, mission.cave_depth, color='blue', alpha=0.3)
        plt.fill_between(x_values, mission.cave_depth, min_depth*np.ones(len(x_values)), 
                         color='saddlebrown', alpha=0.3)
        plt.fill_between(x_values, max_height*np.ones(len(x_values)), mission.cave_height, 
                         color='saddlebrown', alpha=0.3)
        plt.plot(self.position[:, 0], self.position[:, 1], label='Trajectory')
        plt.plot(mission.reference, 'r', linestyle='--', label='Reference')
        plt.legend(loc='upper right')
        plt.show()

@dataclass
class Mission:
    reference: np.ndarray
    cave_height: np.ndarray
    cave_depth: np.ndarray

    @classmethod
    def random_mission(cls, duration: int, scale: float):
        (reference, cave_height, cave_depth) = generate_reference_and_limits(duration, scale)
        return cls(reference, cave_height, cave_depth)

    @classmethod
    def from_csv(cls, file_name: str):
        #importing mission data from the csv file
        df = pd.read_csv(file_name)
        #convert the column types as arrays
        reference = df['reference'].to_numpy()
        cave_height = df['cave_height'].to_numpy()
        cave_depth = df['cave_depth'].to_numpy()
        return cls(reference, cave_height, cave_depth)


class ClosedLoop:
    def __init__(self, plant: Submarine, controller):
        self.plant = plant
        self.controller = controller

    def simulate(self, mission: Mission, disturbances: np.ndarray) -> Trajectory:

        T = len(mission.reference)
        if len(disturbances) < T:
            raise ValueError("Disturbances must be at least as long as mission duration")
        
        positions = np.zeros((T, 2))
        actions = np.zeros(T)
        self.plant.reset_state()

        for t in range(T):
            positions[t] = self.plant.get_position()
            observation_t = self.plant.get_depth()
            # Use the controller to compute the control action based on the error (reference - actual)
            actions[t] = self.controller.compute_control_action(mission.reference[t],observation_t)     
            self.plant.transition(actions[t], disturbances[t])

        return Trajectory(positions)
        
    def simulate_with_random_disturbances(self, mission: Mission, variance: float = 0.5) -> Trajectory:
        disturbances = np.random.normal(0, variance, len(mission.reference))
        trajectory = self.simulate(mission, disturbances)
        self.calculate_performance_metrics(trajectory, mission)
        return trajectory

    def calculate_performance_metrics(self, trajectory: Trajectory, mission: Mission):
        position_y = trajectory.position[:, 1]
        reference_y = mission.reference
        T = len(reference_y)

        # Overshoot calculation
        max_deviation = np.max(np.abs(position_y - reference_y))
        overshoot = (max_deviation / np.max(np.abs(reference_y))) * 100  # as a percentage

        # Steady-state error (last value error)
        steady_state_error = np.abs(position_y[-1] - reference_y[-1])

        # Settling time (using a tolerance band of 2% around the reference)
        tolerance = 0.02
        within_tolerance = np.abs(position_y - reference_y) < tolerance * np.abs(reference_y)
        settling_time = next((i for i in range(T - 1, 0, -1) if not within_tolerance[i]), T - 1) + 1

        # Output the performance metrics
        print(f"Overshoot: {overshoot:.2f}%")
        print(f"Steady-State Error: {steady_state_error:.2f}")
        print(f"Settling Time: {settling_time * self.plant.dt:.2f} seconds")
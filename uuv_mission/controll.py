#Define controller logic 
class PDController:
    def __init__(self, kp=0.15, kd=0.6):
        """
        Initialize the PD controller with default values of KP and KD.
        """
        self.kp = kp  # Proportional gain
        self.kd = kd  # Derivative gain
        self.previous_error = 0  # Initialize previous error as 0

    def compute_control_action(self, reference, current_depth):
        """
        Computes the control action `u[t]` based on the reference depth and current depth.

        Parameters:
            reference (float): The target depth for the UUV.
            current_depth (float): The current depth of the UUV.

        Returns:
            control_action (float): The control action to be applied to the UUV.
        """
        # Calculate error
        error = reference - current_depth
        
        # PD Control action
        control_action = self.kp * error + self.kd * (error - self.previous_error)

        # Update the previous error for the next time step
        self.previous_error = error

        return control_action
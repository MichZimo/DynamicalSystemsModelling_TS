import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt


def S(g, net):
    """Logistic saturation function, with slope modulated by a gain parameter g

    Inputs
    --------
    g: positive scalar neuronal gain
    net: net input to the neural processing unit
    """

    return 1 / (1 + np.exp(-g * net))


def perseverence_dynamics_model(t, x, g, alpha, gamma, input, sigma):
    """Dynamical model

    ------
    t: scalar time
    x: array [x1,x2] of activities of the neural units corresponding to tasks 1,2
    g: gain
    input: array[I1,I2] of input to neural units
    sigma: standard deviation of Gaussian noise added to the net input

    w_{12} = w{21} = 1

    Output
    -------
    dx1/dt(t,x)
    dx2/dt(t,x)

    """
    # split input I1 is for task 1 and I2 for task 2
    I1, I2 = input

    # inhibitory weights
    w1_2 = 1
    w2_1 = 1

    # perserverance weights
    w1_p = 1
    w2_p = 1  # inhibitory

    wp_1 = 1
    wp_2 = 1  # inhibitory

    # initial conditions
    x1 = x[0]
    x2 = x[1]
    P = x[2]

    # net inputs for the 3 neurons
    net_1 = -w1_2 * x2 + w1_p * P + I1 + sigma * np.random.normal()
    net_2 = -w2_1 * x1 - w2_p * P + I2 + sigma * np.random.normal()
    net_P = wp_1 * x1 - wp_2 * x2

    # differential equations for the 3 neurons
    dx1_dt = -x1 + S(g, net_1)
    dx2_dt = -x2 + S(g, net_2)
    dP_dt = -alpha * P + gamma * net_P  # the added neuron(variable) in the perseverence model

    return np.array([dx1_dt, dx2_dt, dP_dt])


def simulate_dynamics(T, x_0, g, alpha, gamma, input, sigma, num_sample_points=100):
    # integrate differential equation

    x_out = solve_ivp(
        perseverence_dynamics_model,
        np.array([0, T]),
        x_0,  # initial condition
        dense_output=True,  # dense_output = True allows us to compute x at any time points on the interval T
        args=[g, alpha, gamma, input, sigma],
    )  # pass additional arguments to the simulation functon

    # extracting simulated values
    ts = np.linspace(
        0, T, num_sample_points
    )  # list of 100 evenly spaced points in the time interval we are considering
    xt = x_out.sol(ts)  # solution of the integral at the specified time points
    x1 = xt[0, :]  # the values of x1(t) are in the first column of the matrix xt
    x2 = xt[1, :]  # the values of x2(t) are in the second column of the matrix xt
    P = xt[2, :]

    return ts, x1, x2, P


# def extract_sim_values(T, x_out, num_sample_points=100):
#     # extracting simulated values

#     ts = np.linspace(0,T,num_sample_points) # list of 100 evenly spaced points in the time interval we are considering
#     xt = x_out.sol(ts)                # solution of the integral at the specified time points
#     x1 = xt[0,:]                      # the values of x1(t) are in the first column of the matrix xt
#     x2 = xt[1,:]                      # the values of x2(t) are in the second column of the matrix xt
#     P = xt[2,:]

#     return ts, x1, x2, P


# region plotting


def plot_trajectory(T, ts, x1, x2, P, num_trials=1, ax=None):
    # Get the current figure
    fig = plt.gcf()
    fig.clf()  # Clear the figure to prevent overplotting
    # adjust size of figure based on number of trails
    fig.set_size_inches(15, 5)
    # Add an axis if not provided
    if ax:
        ax.plot(ts, x1, label="x1")  # this plots the time trajectory of x1
        ax.plot(ts, x2, label="x2")  # this plots the time trajectory of x2
        ax.plot(
            ts, P + 0.5, label="P + 0.5", linestyle="-", alpha=0.5
        )  # Time trajectory of P (shifted by 0.5 on y for better fit in the plot)
        ax.axhline(y=0.5, color="red", linestyle="--", alpha=0.3)
        ax.legend()  # show the legend
        ax.set_xlabel("t")  # this labels the horizontal axis
        ax.set_ylabel("activity (value of x_i)")  # this labels the vertical axis
        ax.set_ylim([0, 1.0])
        ax.set_title("Time Trajectories")  # Set the title of the plot

    if ax is None:
        ax = fig.add_subplot(111)
    # Plot the trajectories
    ax.plot(ts, x1, label="x1")  # Time trajectory of x1
    ax.plot(ts, x2, label="x2")  # Time trajectory of x2
    ax.plot(
        ts, P + 0.5, label="P + 0.5", linestyle="-", alpha=0.5
    )  # Time trajectory of P (shifted by 0.5 on y for better fit in the plot)
    ax.axhline(y=0.5, color="red", linestyle="--", alpha=0.3)
    ax.legend()  # Show the legend
    ax.set_xlabel("t")  # Label the horizontal axis
    ax.set_ylabel("activity (value of x_i)")  # Label the vertical axis
    ax.set_ylim([0, 1.0])  # Set the y-axis limits
    ax.set_title("Time Trajectories")  # Set the title of the plot

    # Add vertical lines for trials
    for trial_number in range(num_trials):
        trial_number += 1
        ax.axvline(T * trial_number, color="gray", linestyle="--")
    plt.draw()  # Ensure the updated plot is rendered
    plt.pause(0.001)  # Pause to allow the plot to update

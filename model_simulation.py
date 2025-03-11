import numpy as np
import pandas as pd
import random
import matplotlib.pyplot as plt

from model import simulate_dynamics, plot_trajectory


def compute_choice_probabilities(activities_n_final, trial_number, c):
    """
    This function computes the choice probabilities for the given neuron activities
    Input arguments:
      neuron_activities: a list of both neuron activities
      trial_number: number of the current trial
      c: parameter used to compute beta in the softmax function
    Output:
      choice_probs: list of choice probabilities
    """

    # compute beta
    beta = pow((trial_number + 1) / 10, c)

    # scaling factor (small differences between neuron activities are magnified, which makes the exponential terms more distinct)
    scalar = 3

    # compute softmaxed choice proabbilities
    choice_probs = np.exp(activities_n_final * scalar * beta) / np.sum(np.exp(activities_n_final * scalar * beta))

    return choice_probs


def compute_choice(activities_n_final, trial_number, c):
    """
    This function computes the choice based on the final activity levels
    Input arguments:
    activities_n_final: activity of neuron 1 (letter task) and neuron 2 (number task) at the end of trial
    trial_number: number of the current trial
    c: parameter used to compute beta in the softmax function
    Output:
    choice: chosen task to react to 0 -> letter task , 1 -> number task
    """
    # compute softmaxed choice proabbilities
    choice_probs = compute_choice_probabilities(activities_n_final, trial_number, c)

    # compute cumulated sums
    cumulated_choice_probs = np.cumsum(choice_probs)

    # draw random number between 0 and 1
    random_number = np.random.random()

    # choose deck index depending on choice probabilities
    choice = 0

    # iterate through the cumulative sums to find the first index where the random number exceeds the cumulative sum
    while choice < len(cumulated_choice_probs) and random_number > cumulated_choice_probs[choice]:
        choice += 1

    return choice


def test_trial_type(current_task, former_task):
    # determining the condition (repeat/ switch)

    if current_task == former_task:
        trial_type = "repeat"
    else:
        trial_type = "switch"

    return trial_type


def initialize_task():
    # initialization of the task
    task = random.randint(0, 1)

    if task == 0:
        I1 = 1
        I2 = 0
        input = np.array([I1, I2])
        correct_responses = np.array([1, 0])
        current_task = "letter"

    else:
        I1 = 0
        I2 = 1
        input = np.array([I1, I2])
        correct_responses = np.array([0, 1])
        current_task = "number"

    return current_task, input, correct_responses


def get_correctness(correct_responses, choice):
    # checking if the choice is correct

    if correct_responses[choice] == 1:
        correctness = 1
    else:
        correctness = 0

    return correctness


# generate an experiment with a given number of trials
def generate_experiment_trials(num_trials):
    """
    This function generates an experiment with a given number of trials.

    Input arguments:
      num_trials: number of trials
    Output:
      df: a Pandas dataframe containing the data of the experiment
    """
    trials = [initialize_task() for _ in range(num_trials)]
    trails_df = pd.DataFrame(trials, columns=["task", "input", "correct_responses"])

    return trails_df


def log_data(df, trial_number, activities_n_final, current_task, trial_type, choice, correct_responses, correctness):
    """
    This function logs several outcomes of the simulation into a data frame.

    Input arguments:
      df: a Pandas dataframe in which we write the data
      trial_index: current trial number
      activities_n_final: activity of neuron 1 (letter task) and neuron 2 (number task) at the end of trial
      task: letter or number task
      trial_type: whether the task switched from the trial before (switch) or stayed the same (repeat)
      choice: chosen task to react to 0 -> letter task , 1 -> number task
      correctness: whether the chosen task is correct
    """

    # Calculate the new index (assuming trial_number starts at 0 and aligns with DataFrame index)
    new_index = len(df)

    # Directly assign the new row to the DataFrame using `loc`
    df.loc[new_index] = {
        "trial_index": trial_number,
        "activity_n1": activities_n_final[0],
        "activity_n2": activities_n_final[1],
        "task": current_task,
        "trial_type": trial_type,
        "choice_adjusted": choice,
        "correct_responses": correct_responses,
        "response": correctness,
    }
    return df


def simulate_experiment(num_trials, T, x_0, g, c, alpha, gamma, sigma, bool_plot_trajectory=False, task_sequence=None):

    if task_sequence is not None:
        num_trials = len(task_sequence)
    if task_sequence is None:
        task_sequence = generate_experiment_trials(num_trials)

    # we will log the entire simulation in a dataframe
    df = pd.DataFrame(
        columns=[
            "task",
            "trial_type",
            "response",
            "activity_n1",
            "activity_n2",
            "choice_adjusted",
            "correct_responses",
            "trial_index",
        ]
    )

    # set initial neuron activity
    x_0 = np.asarray(x_0)
    x_1 = x_0[0]
    x_2 = x_0[1]
    P = x_0[2]

    # create arrays for plotting
    array_x1 = []
    array_x2 = []
    array_P = []
    array_ts = []

    num_sample_points_per_trial = 100
    for trial_number in range(num_trials):

        x_0 = np.array([x_1, x_2, P])

        current_task = task_sequence["task"][trial_number]  # checking wether task is letter or number, input -> [I1,I2]
        correct_responses = task_sequence["correct_responses"][trial_number]  # correct responses for the current task
        input = task_sequence["input"][trial_number]  # input to the neural units

        if trial_number > 0:
            trial_type = test_trial_type(current_task, df["task"].iloc[-1])  # checking wether type is switch or repeat

        else:  # for first trial since there is no former task
            trial_type = None

        ts_values, x1_values, x2_values, P_values = simulate_dynamics(
            T, x_0, g, alpha, gamma, input, sigma, num_sample_points=num_sample_points_per_trial
        )  # run model i.e. solve OED

        activities_n_final = np.array([x1_values[-1], x2_values[-1]])  # get last values of neuron activity

        choice = compute_choice(activities_n_final, trial_number, c)  # computing the choices

        # set the initial x_1 and x_2 for the next trail to be the last values of the current one
        x_1 = x1_values[-1]
        x_2 = x2_values[-1]
        P = P_values[-1]

        correctness = get_correctness(correct_responses, choice)

        # log results
        df = log_data(
            df, trial_number, activities_n_final, current_task, trial_type, choice, correct_responses, correctness
        )

        # plotting part ------------------------------------------------------------

        max_trails_plot = 20
        if bool_plot_trajectory == True:

            if num_trials == 1:
                array_x1 = x1_values
                array_x2 = x2_values
                array_P = P_values
                array_ts = ts_values

            else:
                array_x1 = np.concatenate((array_x1, x1_values), axis=None)
                array_x2 = np.concatenate((array_x2, x2_values), axis=None)
                array_P = np.concatenate((array_P, P_values), axis=None)
                array_ts = np.concatenate((array_ts, ts_values + (T * (trial_number))), axis=None)
    # get rid of the first trial
    df = df.iloc[1:]

    # reset index
    df.reset_index(drop=True, inplace=True)
    df["accuracy"] = (df["response"].cumsum() / (df.index + 1)).astype(float)
    # reorder the dataframe
    df = df[
        [
            "task",
            "trial_type",
            "response",
            "accuracy",
            "choice_adjusted",
            "activity_n1",
            "activity_n2",
            "correct_responses",
            "trial_index",
        ]
    ]

    if (bool_plot_trajectory == True) and (num_trials <= max_trails_plot):
        plot_trajectory(T, array_ts, array_x1, array_x2, array_P, num_trials)
    elif (bool_plot_trajectory == True) and (num_trials > max_trails_plot):
        print(f"Ploting first {max_trails_plot} trials:")
        plot_trajectory(
            T,
            array_ts[: max_trails_plot * num_sample_points_per_trial],
            array_x1[: max_trails_plot * num_sample_points_per_trial],
            array_x2[: max_trails_plot * num_sample_points_per_trial],
            array_P[: max_trails_plot * num_sample_points_per_trial],
            max_trails_plot,
        )

    return df

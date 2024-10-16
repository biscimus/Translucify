from math import prod
import os
from sys import prefix

import numpy as np
import regex
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from .preprocessor import import_csv
import pandas as pd
from pm4py import read_xes
from .transition_system import TransitionSystem, State, Transition
from pm4py.objects.log.util.dataframe_utils import convert_timestamp_columns_in_df

DataState = dict[str, float]
ObservationInstances = dict[Transition, tuple[list[DataState], list[bool]]]
RegressionModels = dict[Transition, LogisticRegression]

ACTIVITY_COLUMN = "concept:name"
CASE_COLUMN = "case:concept:name"
TIMESTAMP_COLUMN = "time:timestamp"

def generate_prefix_automaton(log: pd.DataFrame):
    prefix_automaton = TransitionSystem(name="prefix_automaton", states=set(), transitions=set())
    # Add start state
    prefix_automaton.states.add(State("<>", data={"frequency": 0}))

    print(prefix_automaton.states)

    def extend_prefix_automaton_with_trace(group: pd.DataFrame):
        trace = list(group["concept:name"].values)
        # Get start state
        curr_prefix = ""
        curr_state: State = next((state for state in prefix_automaton.states if state.name == f"<{curr_prefix}>"), None)
        curr_state.data["frequency"] += 1
        for activity in trace:
            
            next_prefix = curr_prefix + ","+ activity
            # Check if activity is already in the automaton 
            next_state = next((state for state in prefix_automaton.states if state.name == f"<{next_prefix}>"), None)
            if not next_state:
                next_state = State(f"<{next_prefix}>", data={"frequency": 0})
                print("Activity: ", activity)
                new_transition = Transition(activity, curr_state, next_state)
                curr_state.outgoing.add(new_transition)
                next_state.incoming.add(new_transition)
                prefix_automaton.states.add(next_state)
                prefix_automaton.transitions.add(new_transition)
            curr_state = next_state
            curr_prefix = next_prefix
            curr_state.data["frequency"] += 1
        return group
    
    log.groupby("case:concept:name", group_keys=False).apply(extend_prefix_automaton_with_trace, include_groups=False).reset_index()

    return prefix_automaton

# Translucent log generation with simple frequency threshold
def fill_enabled_activities(log: pd.DataFrame, prefix_automaton: TransitionSystem, threshold=0.1):

    log["enabled_activities"] = None

    def fill_enabled_activities_trace(group: pd.DataFrame):
        trace = list(group["concept:name"].values)
        curr_prefix = ""
        curr_state: State = next((state for state in prefix_automaton.states if state.name == f"<{curr_prefix}>"), None)

        for (index, _), activity in zip(group.iterrows(), trace):
            print("INDEX:", index)
            curr_prefix += activity
            print("Current state:", curr_state)
            print("Current prefix:", curr_prefix)
            frequency_sum = sum([transition.to_state.data["frequency"] for transition in curr_state.outgoing])
            print("Frequency sum:", frequency_sum)
            available_activities = [transition.name for transition in curr_state.outgoing]
            print("Available activities:", available_activities)
            enabled_activities = [transition.name for transition in curr_state.outgoing if transition.to_state.data["frequency"] / frequency_sum >= threshold]
            print("Enabled activities:", enabled_activities)
            log.at[index, 'enabled_activities'] = tuple(sorted(enabled_activities, key=str.lower))
            next_transition = next((transition for transition in curr_state.outgoing if transition.name == activity), None)
            print("Next transition:", next_transition)
            curr_state = next_transition.to_state
        return group
    
    log.groupby("case:concept:name", group_keys=False).apply(fill_enabled_activities_trace, include_groups=False).reset_index()

    return log



# Multivariate Logistic Regression with Prefix Automaton

def translucify_prefix_automaton(log_filepath: str, prefix_automaton: TransitionSystem, selected_columns: list[dict[str]], method, threshold=0.1):

    # If log flie is a CSV file, import it as a DataFrame
    # Else if log file is a XES file, import it as a log object
    if log_filepath.endswith(".csv"):
        log = pd.read_csv(log_filepath, sep=";")

        print("Event log from CSV: \n", log)
        log = convert_timestamp_columns_in_df(log)
        log[CASE_COLUMN] = log[CASE_COLUMN].astype("string")
    else:
        log = read_xes(log_filepath)

    # TODO: incorporate feature columns
    categorical_columns = [data_column["column"] for data_column in selected_columns if data_column["type"] == "categorical"]

    log = pd.get_dummies(log, columns=categorical_columns, dtype=int)

    # log = preprocess_log(log, selected_columns)
    print(f"Log after preprocessing:\n {log}")

    # # Select all log columns as features as long as their names start with a selected column name (Due to one-hot encoding)
    feature_columns = [column for column in log.columns if any([column.startswith(data_column["column"]) for data_column in selected_columns])]
    print(f"Feature Columns:\n {feature_columns}")
    observation_instances = extract_observation_instances(log, prefix_automaton, feature_columns)
    print("Observation instances: ", observation_instances)
    regression_models = create_regression_models(observation_instances, feature_columns)
    log = create_enabled_activities(prefix_automaton, log, regression_models, feature_columns, threshold)
    return log

def extract_observation_instances(log: pd.DataFrame, prefix_automaton: TransitionSystem, feature_columns: list[str]) -> ObservationInstances:
    observation_instances: ObservationInstances = { transition: ([], []) for transition in prefix_automaton.transitions}
    def fill_observation_instances(group: pd.Series) -> pd.DataFrame:
        trace = list(group[ACTIVITY_COLUMN].values)
        
        current_data_state_index = 0
        current_state: State = next((state for state in prefix_automaton.states if state.name == "<>"), None)

        for activity in trace:
            enabled_transitions = [transition for transition in current_state.outgoing]
            fired_transition = next((transition for transition in enabled_transitions if transition.name == activity), None)

            try:
                current_data_state: list[list[float | int]] = group[feature_columns].iloc[current_data_state_index].to_list()
            except IndexError:
                current_data_state: list[list[float | int]] = group[feature_columns].iloc[-1].to_list()
            
            for enabled_transition in enabled_transitions:
                # Add each instances to dictionary
                observation_instances[enabled_transition][0].append(current_data_state)
                observation_instances[enabled_transition][1].append(fired_transition == enabled_transition)

            current_data_state_index += 1
            # Increment marking by firing the transition
            current_state = fired_transition.to_state

        return group

    log.groupby(CASE_COLUMN, group_keys=False).apply(fill_observation_instances).reset_index()
    return observation_instances
    

def create_regression_models(observation_instances: ObservationInstances, feature_columns: list[str]) -> RegressionModels:
    '''
    Receives a dictionary of observation instances and creates a regression model for each transition.
    :param observation_instances: The dictionary of observation instances.
    :param feature_columns: The list of feature columns.
    '''
    regression_models: RegressionModels = {transition: None for transition in observation_instances}

    accuracy_scores: dict[Transition, float] = {}

    for transition, (data_states, labels) in observation_instances.items():
        X_dataframe = pd.DataFrame(data_states, columns=feature_columns)
        Y_dataframe = pd.DataFrame(labels, columns=["label"]).astype(int)

        print("X_dataframe: ", X_dataframe)
        print("Y_dataframe: ", Y_dataframe)

       

        try:    
            X_train, X_test, Y_train, Y_test = train_test_split(X_dataframe, Y_dataframe, test_size=0.2)
            # Add regression model to corresponding transition
            regression = LogisticRegression(solver="liblinear").fit(X_train, np.ravel(Y_train))
            regression_models[transition] = regression
            accuracy_scores[transition] = regression.score(X_test, np.ravel(Y_test))
        except ValueError:
            #print("Valueerror!")
            # Error if transition has a 100% change of firing. But there are some transitions that have 100% change of firing!
            # => Set the regression model to 1
            regression_models[transition] = 1
            accuracy_scores[transition] = 1
    
    # Convert the accuracy scores into a dataframe then store in a csv file
    accuracy_scores_dataframe = pd.DataFrame(accuracy_scores.items(), columns=["Transition", "Accuracy Score"])

    
    # Define the path
    directory = '../logs'
    file_path = os.path.join(directory, 'pa_multivariate_regression_accuracy_scores.csv')

    if not os.path.exists(directory):
        os.makedirs(directory)  # Create the directory if it does not exist

    accuracy_scores_dataframe.to_csv(file_path, index=False)

    return regression_models

def create_enabled_activities(prefix_automaton: TransitionSystem, log: pd.DataFrame, regression_models: dict[Transition, LogisticRegression], feature_columns: list[str], threshold: float) -> pd.DataFrame:

    # Add column enabled_activities
    log["enabled_activities"] = None
    print(log)

    def fill_enabled_activities_column(group: pd.Series) -> pd.DataFrame:

        trace = list(group[ACTIVITY_COLUMN].values)

        current_data_state_index = 0
        current_row_index = 0

        try:
            current_data_state: list[list[float | int]] = group[feature_columns].iloc[current_data_state_index].to_list()
        except IndexError:
            current_data_state: list[list[float | int]] = group[feature_columns].iloc[-1].to_list()

        for activity in trace:
            current_state: State = next((state for state in prefix_automaton.states if state.name == "<>"), None)
            current_data_state = group[feature_columns].iloc[[current_row_index]]
            #print("Data state df:", current_data_state)

            enabled_transitions = current_state.outgoing
            #print("Enabled transitions:", enabled_transitions)

            # Compute weighted sum of probabilities of enabled transitions
            sum_of_probs = sum([regression_models[enabled_transition].predict_proba(current_data_state)[0][0] if regression_models[enabled_transition]!=1 else 1 for enabled_transition in enabled_transitions])

            choices = []

            # Add all activities as children of the node
            for enabled_transition in enabled_transitions:
                probability = regression_models[enabled_transition].predict_proba(current_data_state)[0][0] if regression_models[enabled_transition]!=1 else 1
                probability /= sum_of_probs
                choices.append((probability, enabled_transition.name))

            choices_filtered = tuple(sorted(set([choice[1] for choice in choices if choice[0] > threshold]), key=str.lower))
            print(f"Filtered choices: {choices_filtered}")
            
            # # Add enabled activities to the DataFrame
            group["enabled_activities"].iloc[current_row_index] = choices_filtered

            current_row_index += 1
            current_data_state_index += 1
            #print("Fired transition name:", fired_transition_name)
            fired_transition: Transition = next(filter(lambda transition: transition.name == activity, enabled_transitions), None)
            # Increment marking by firing the transition
            if fired_transition is not None:
                current_state = fired_transition.to_state

        return group

    return log.groupby(CASE_COLUMN, group_keys=False).apply(fill_enabled_activities_column).reset_index()

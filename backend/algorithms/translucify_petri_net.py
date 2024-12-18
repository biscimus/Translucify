from math import prod
import os
import pandas as pd
from pm4py.objects.log.obj import Trace
import pm4py
from pandas import DataFrame, Series, read_csv
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.algo.conformance.alignments.petri_net.variants import dijkstra_less_memory
from pm4py.objects.petri_net.semantics import PetriNetSemantics
from sklearn.calibration import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import numpy as np
from anytree import Node
from .custom_logger import get_logger_by_flie_path
from pm4py.objects.log.util.dataframe_utils import convert_timestamp_columns_in_df

import warnings
# Suppress FutureWarning messages
warnings.simplefilter(action='ignore', category=FutureWarning)

# Define DataState as type for dict[str, float]
DataState = dict[str, float]
Activity = str
ObservationInstances = dict[PetriNet.Transition, tuple[list[DataState], list[bool]]]
RegressionModels = dict[PetriNet.Transition, LogisticRegression]
RandomForests = dict[PetriNet.Transition, RandomForestClassifier]

ACTIVITY_COLUMN = "concept:name"
CASE_COLUMN = "case:concept:name"
TIMESTAMP_COLUMN = "time:timestamp"



def translucify_petri_net(log_filepath: str, data_columns: list[dict[str]], method: str, threshold: float) -> DataFrame:
    '''
    Discovers a translucent log from a given log file path using a threshold.

    :param log_filepath: The file path of the log file.
    :param threshold: The cutoff percentage.
    '''

    print("Log file path: ", log_filepath)
    
    # If log flie is a CSV file, import it as a DataFrame
    # Else if log file is a XES file, import it as a log object
    if log_filepath.endswith(".csv"):
        log = read_csv(log_filepath, sep=";")
        print("Event log from CSV: \n", log)
        log = convert_timestamp_columns_in_df(log)
        print("Event log after converting timestamp columns: \n", log)
        log[CASE_COLUMN] = log[CASE_COLUMN].astype("string")
        log[ACTIVITY_COLUMN] = log[ACTIVITY_COLUMN].astype("string")
    else:
        log = pm4py.read_xes(log_filepath)


    print("Dataframe from log: \n", log)
    # check dataframe types
    print("DTYPES: ", log.dtypes)
    petri_net = pm4py.discover_petri_net_inductive(log)

    # pm4py.view_petri_net(petri_net=petri_net[0], initial_marking=petri_net[1], final_marking=petri_net[2], format="png")
    

    # Print number of traces of log
    num_traces = log[CASE_COLUMN].nunique()
    print(f"Number of traces in log: {num_traces}")
    print(f"Log data types:\n {log.dtypes}")
    # Choose (or select all) attribute columns

    
    # Preprocess log using one-hot encoding
    if method == "logistic_regression":
        categorical_columns = [data_column["column"] for data_column in data_columns if data_column["type"] == "categorical"]
        print("Categorical columns: ", categorical_columns)
        log = pd.get_dummies(log, columns=categorical_columns, dtype=int)
    # Scikit tends to perform well with categorical variables encoded as integers
    elif method == "random_forest":
        le = LabelEncoder()
        for data_column in data_columns:
            if data_column["type"] == "categorical":
                log[data_column["column"]] = le.fit_transform(log[data_column["column"]])


    print(f"Log after preprocessing:\n {log}")

    # Select all log columns as features as long as their names start with a selected column name (Due to one-hot encoding)
    feature_columns = [column for column in log.columns if any([column.startswith(data_column["column"]) for data_column in data_columns])]
    print(f"Feature Columns:\n {feature_columns}")

    observation_instances: ObservationInstances = create_observation_instances(petri_net, log, feature_columns)
    print("Observation instances: ", observation_instances)

    # Save the observation instances to a csv file
    observation_instances_dataframe = DataFrame(observation_instances.items(), columns=["Transition", "Observation Instances"])
    observation_instances_dataframe.to_csv("observation_instances.csv", index=False)

    regression_models = create_regression_models(observation_instances, feature_columns, method)
    print("Regression models: ", regression_models)

    return create_enabled_activities(petri_net, log, regression_models, feature_columns, threshold, method)

def create_observation_instances(petri_net: tuple[PetriNet, Marking, Marking], log: DataFrame, feature_columns: list[str]) -> ObservationInstances:
    '''
    This function creates observation instances for each transition in the Petri net.
    e.g.: {t1: ([datastate1, datastate2], [True, False])}
    :param petri_net: The Petri net tuple.
    :param log: The log DataFrame.
    :param feature_columns: The list of feature columns.
    '''
    net, im, fm = petri_net

    # Create a dictionary of transitions and its instances
    observation_instances: ObservationInstances = { transition: ([], []) for transition in net.transitions}

    def fill_observation_instances(group: Series) -> DataFrame:

        # Create alignments for each trace
        trace = Trace([{ACTIVITY_COLUMN: activity} for activity in group[ACTIVITY_COLUMN]])
        alignments = dijkstra_less_memory.apply(trace, net, im, fm, parameters={dijkstra_less_memory.Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE: True})
        #print("Alignment:", alignments["alignment"])
        current_marking = im
        current_data_state_index = 0

        for alignment in alignments["alignment"]:
            # Get all enabled transitions from the current marking
            enabled_transitions: set[PetriNet.Transition] = pm4py.get_enabled_transitions(net, current_marking)
            #print("Enabled transitions:", enabled_transitions)
            # Find the transition that was fired
            fired_transition_name: str = alignment[0][1]
            fired_transition: PetriNet.Transition = next(filter(lambda transition: transition.name == fired_transition_name, enabled_transitions))
            #print("Fired transition:", fired_transition)
            #print(f"Current data state index: {current_data_state_index}")
            # Get the data state of the current data state index
            try:
                current_data_state: list[list[float | int]] = group[feature_columns].iloc[current_data_state_index].to_list()
            except IndexError:
                current_data_state: list[list[float | int]] = group[feature_columns].iloc[-1].to_list()
            
            for enabled_transition in enabled_transitions:
                # Add each instances to dictionary
                observation_instances[enabled_transition][0].append(current_data_state)
                observation_instances[enabled_transition][1].append(fired_transition == enabled_transition)

            # Increment data state index if transition is not silent
            if alignment[1][1] is not None: current_data_state_index += 1
            # Increment marking by firing the transition
            current_marking = PetriNetSemantics.fire(net, fired_transition, current_marking)

    log.groupby(CASE_COLUMN, group_keys=False).apply(fill_observation_instances).reset_index()
    return observation_instances

def create_regression_models(observation_instances: ObservationInstances, feature_columns: list[str], method: str) -> RegressionModels | RandomForests:
    '''
    Receives a dictionary of observation instances and creates a regression model for each transition.
    
    :param observation_instances: The dictionary of observation instances.
    :param feature_columns: The list of feature columns.
    '''
    regression_models: RegressionModels | RandomForests = {transition: None for transition in observation_instances}

    accuracy_scores: dict[PetriNet.Transition, float] = {}

    for transition, (data_states, labels) in observation_instances.items():
        X_dataframe = DataFrame(data_states, columns=feature_columns)
        Y_dataframe = DataFrame(labels, columns=["label"]).astype(int)

        # print("X dataframe: ", X_dataframe)
        # print("Y dataframe: ", Y_dataframe)

        X_train, X_test, Y_train, Y_test = train_test_split(X_dataframe, Y_dataframe, test_size=0.2)

        try:
            if method == "logistic_regression":
                regression = LogisticRegression().fit(X_train, np.ravel(Y_train))
            elif method == "random_forest":
                print("using random forest")
                regression = RandomForestClassifier().fit(X_train, np.ravel(Y_train))
            # Add regression model to corresponding transition
            regression_models[transition] = regression
            accuracy_scores[transition] = regression.score(X_test, np.ravel(Y_test))
        except ValueError:
            #print("Valueerror!")
            # Error if transition has a 100% change of firing. But there are some transitions that have 100% change of firing!
            # => Set the regression model to 1
            regression_models[transition] = 1
            accuracy_scores[transition] = 1
    
    # Convert the accuracy scores into a dataframe then store in a csv file
    accuracy_scores_dataframe = DataFrame(accuracy_scores.items(), columns=["Transition", "Accuracy Score"])
    file_path = 'multivariate_regression_accuracy_scores.csv' if method == "logistic_regression" else 'random_forest_accuracy_scores.csv'
    accuracy_scores_dataframe.to_csv(file_path, index=False)

    return regression_models


def create_enabled_activities(petri_net: tuple[PetriNet, Marking, Marking], log: DataFrame, regression_models: RegressionModels | RandomForests, feature_columns: list[str], threshold: float, method: str) -> DataFrame:

    # Add column enabled_activities
    log["enabled_activities"] = None
    print(log)

    net, im, fm = petri_net

    def fill_enabled_activities_column(group: Series) -> DataFrame:

        # Create alignments for each trace
        trace = Trace([{ACTIVITY_COLUMN: activity} for activity in group[ACTIVITY_COLUMN]])
        alignments = dijkstra_less_memory.apply(trace, net, im, fm, parameters={dijkstra_less_memory.Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE: True})
    
        print("Trace:", trace)
        print("Alignments:", alignments)
        current_marking = im
        current_row_index = 0

        for alignment in alignments["alignment"]:
            current_data_state = group[feature_columns].iloc[[current_row_index]]
            #print("Data state df:", current_data_state)

            def traverse_petri_net(node: Node, current_marking: Marking):

                enabled_transitions: set[PetriNet.Transition] = pm4py.get_enabled_transitions(net, current_marking)                

                # Compute weighted sum of probabilities of enabled transitions
                probs_all = [regression_models[enabled_transition].predict_proba(current_data_state)[0] if regression_models[enabled_transition]!=1 else 1 for enabled_transition in enabled_transitions]
                print("Probs all: ", probs_all)

                if method == "logistic_regression":
                    probs = [regression_models[enabled_transition].predict_proba(current_data_state)[0][1] if regression_models[enabled_transition]!=1 else 1 for enabled_transition in enabled_transitions]
                elif method == "random_forest":                  
                    probs = [regression_models[enabled_transition].predict_proba(current_data_state)[0][1] if len(regression_models[enabled_transition].predict_proba(current_data_state)[0]) != 1 else 1 for enabled_transition in enabled_transitions]

                print("Probs: ", probs)



                sum_of_probs = sum(probs)

                # Add all activities as children of the node
                for enabled_transition in enabled_transitions:
                    if method == "logistic_regression":
                        probability = regression_models[enabled_transition].predict_proba(current_data_state)[0][1] if regression_models[enabled_transition]!=1 else 1
                    elif method == "random_forest":
                        probability = regression_models[enabled_transition].predict_proba(current_data_state)[0][1] if len(regression_models[enabled_transition].predict_proba(current_data_state)[0]) != 1 else 1
                    probability /= sum_of_probs
                    child_node = Node(enabled_transition.name, parent=node, transition=enabled_transition, probability=probability)
                    if child_node.transition.label is None:
                        #print("Silent transition found!")
                        traverse_petri_net(child_node, PetriNetSemantics.fire(net, enabled_transition, current_marking))
            
            root = Node("root", probability=1)
            traverse_petri_net(root, current_marking)

            def traverse_tree_dfs(node, path):
                path.append(node)
                if not node.children:
                    paths.append(path.copy())
                for child in node.children:
                    traverse_tree_dfs(child, path)
                path.pop()

            # Start DFS from the root node
            paths = []
            traverse_tree_dfs(root, [])
            print(f"Paths: {paths}")

            choices = [(prod([node.probability for node in path]), path[-1].transition.label) for path in paths]
            choices_filtered = tuple(sorted(set([choice[1] for choice in choices if choice[0] > threshold]), key=str.lower))
            print(f"Filtered choices: {choices_filtered}")
            
            # # Add enabled activities to the DataFrame
            group["enabled_activities"].iloc[current_row_index] = choices_filtered

            # Increment data state index if transition is not silent
            if alignment[1][1] is not None: current_row_index += 1

             # Find the transition that was fired
            fired_transition_name: str = alignment[0][1]
            #print("Fired transition name:", fired_transition_name)
            fired_transition: PetriNet.Transition = next(filter(lambda transition: transition.name == fired_transition_name, net.transitions))
            # Increment marking by firing the transition
            current_marking = PetriNetSemantics.fire(net, fired_transition, current_marking)
        return group

    return log.groupby(CASE_COLUMN, group_keys=False).apply(fill_enabled_activities_column).reset_index()
import argparse
from preprocessor import import_csv, user_select_columns
from pm4py.objects.log.obj import Trace
from pm4py import view_petri_net, get_enabled_transitions, discover_petri_net_inductive
from pandas import DataFrame, Series, get_dummies
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.algo.conformance.alignments.petri_net.variants import dijkstra_less_memory
from pm4py.objects.petri_net.semantics import PetriNetSemantics
from sklearn.linear_model import LogisticRegression
import numpy as np

# Define DataState as type for dict[str, float]
DataState = dict[str, float]
Activity = str
ObservationInstances = dict[PetriNet.Transition, tuple[list[DataState], list[bool]]]
RegressionModels = dict[PetriNet.Transition, LogisticRegression]

def discover_translucent_log_from_model(petri_net: tuple[PetriNet, Marking, Marking], log: DataFrame, threshold: float) -> DataFrame:
    
    print(f"Log data types: \n{log.dtypes}")
    # Choose (or select all) attribute columns
    selected_columns = user_select_columns(log)

    log = preprocess_log(log, selected_columns)
    print(f"Log after preprocessing: \n{log}")

    # Select all log columns as features as long as their names start with a selected column name 
    feature_columns = [column for column in log.columns if any([column.startswith(selected_column) for selected_column in selected_columns])]
    print(f"Feature Columns: \n{feature_columns}")

    observation_instances: ObservationInstances = create_observation_instances(petri_net, log, feature_columns)
    regression_models: RegressionModels = create_regression_models(observation_instances, feature_columns)
    return create_enabled_activities(petri_net, log, regression_models, feature_columns, threshold)

def preprocess_log(log: DataFrame, selected_columns: list[str]) -> DataFrame:
    # TODO: Preprocessing data more efficiently
    # data_log = preprocess_log(log, selected_columns)
    # Preprocess the log for data traces
    return get_dummies(log, columns=selected_columns, dtype=int)



def create_observation_instances(petri_net: tuple[PetriNet, Marking, Marking], log: DataFrame, feature_columns: list[str]) -> ObservationInstances:
    net, im, fm = petri_net

    # Create a dictionary of transitions and its instances
    observation_instances: ObservationInstances = { transition: ([], []) for transition in net.transitions}

    def fill_observation_instances(group: Series) -> DataFrame:
        # Create alignments for each trace
        trace = Trace([{"concept:name": activity} for activity in group["concept:name"]])
        alignments = dijkstra_less_memory.apply(trace, net, im, fm, parameters={dijkstra_less_memory.Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE: True})

        current_marking = im
        current_data_state_index = 0

        for alignment in alignments["alignment"]:
            # Get all enabled transitions from the current marking
            enabled_transitions: set[PetriNet.Transition] = get_enabled_transitions(net, current_marking)
            
            # Find the transition that was fired
            fired_transition_name: str = alignment[0][1]
            fired_transition: PetriNet.Transition = next(filter(lambda transition: transition.name == fired_transition_name, enabled_transitions))

            # Get the data state of the current data state index
            current_data_state: list[list[float | int]] = group[feature_columns].iloc[current_data_state_index].to_list()

            for enabled_transition in enabled_transitions:
                # Add each instances to dictionary
                observation_instances[enabled_transition][0].append(current_data_state)
                observation_instances[enabled_transition][1].append(fired_transition == enabled_transition)

            # Increment data state index if transition is not silent
            if alignment[1][1] is not None: current_data_state_index += 1
            # Increment marking by firing the transition
            current_marking = PetriNetSemantics.fire(net, fired_transition, current_marking)

    log.groupby("case:concept:name", group_keys=False).apply(fill_observation_instances).reset_index()
    print(f"observation_instances: {observation_instances}")
    return observation_instances

def create_regression_models(observation_instances, feature_columns: list[str]) -> RegressionModels:
    regression_models: RegressionModels = {transition: None for transition in observation_instances}

    for transition, (data_states, labels) in observation_instances.items():
        X_dataframe = DataFrame(data_states, columns=feature_columns)
        Y_dataframe = DataFrame(labels, columns=["label"]).astype(int)
        try:
            # Add regression model to corresponding transition
            regression = LogisticRegression().fit(X_dataframe, np.ravel(Y_dataframe))
            regression_models[transition] = regression
        except ValueError:
            # Error if transition has a 100% change of firing. But there are some transitions that have 100% change of firing!
            # Let's just set the regression model to 1
            regression_models[transition] = 1

    return regression_models

def create_enabled_activities(petri_net: tuple[PetriNet, Marking, Marking], log: DataFrame, regression_models: dict[PetriNet.Transition, LogisticRegression], feature_columns: list[str], threshold: float) -> DataFrame:

    # Add column enabled_activities
    log["enabled_activities"] = None
    print(log)

    net, im, fm = petri_net

    def fill_enabled_activities_column(group: Series) -> DataFrame:

        # Create alignments for each trace
        trace = Trace([{"concept:name": activity} for activity in group["concept:name"]])
        alignments = dijkstra_less_memory.apply(trace, net, im, fm, parameters={dijkstra_less_memory.Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE: True})
    
        current_marking = im
        current_row_index = 0

        for alignment in alignments["alignment"]:
            # Get all enabled transitions from the current marking
            enabled_transitions: set[PetriNet.Transition] = get_enabled_transitions(net, current_marking)
            print(f"Enabled transitions: {enabled_transitions}")
            # Find the transition that was fired
            fired_transition_name: str = alignment[0][1]
            fired_transition: PetriNet.Transition = next(filter(lambda transition: transition.name == fired_transition_name, enabled_transitions))

            # Get the data state of the current data state index
            current_data_state: list[list[float | int]] = group[feature_columns].iloc[current_row_index].to_list()
            print(f"Current data state: {current_data_state}")

            enabled_activities = [ enabled_transition.label for enabled_transition in enabled_transitions if regression_models[enabled_transition] == 1  or regression_models[enabled_transition].predict(np.ravel(current_data_state).reshape(1, -1)) > threshold]

            # Add enabled activities to the DataFrame
            group["enabled_activities"].iloc[current_row_index] = tuple(sorted(enabled_activities, key=str.lower))

            # Increment data state index if transition is not silent
            if alignment[1][1] is not None: current_row_index += 1
            # Increment marking by firing the transition
            current_marking = PetriNetSemantics.fire(net, fired_transition, current_marking)
        return group

    return log.groupby("case:concept:name", group_keys=False).apply(fill_enabled_activities_column).reset_index()


if __name__ == "__main__":

    parser = argparse.ArgumentParser("simple_example")
    parser.add_argument("threshold", help="The cutoff percentage.", type=float)
    args = parser.parse_args()
    threshold = args.threshold

    log = import_csv("sldpn_log.csv")
    net_with_markings = discover_petri_net_inductive(log)
    log = discover_translucent_log_from_model(net_with_markings, log, threshold=threshold)
    print(f"RESULT: \n{log}")
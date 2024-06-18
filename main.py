import pandas
import pm4py
from pm4py.objects.transition_system.obj import TransitionSystem 
from pm4py.algo.conformance.alignments.petri_net.algorithm import Variants
from pm4py.objects.petri_net.utils.check_soundness import check_source_place_presence
from IPython.display import display

from splitminer import discover_petri_net_split

def import_csv(file_path: str) -> pandas.DataFrame:
    event_log = pandas.read_csv(file_path, sep=';')
    event_log = pm4py.format_dataframe(event_log, case_id='case_id',
                                           activity_key='activity', timestamp_key='timestamp')
    return event_log

def convert_csv_to_xes(csv_file_path: str) -> None:
    event_log = import_csv(csv_file_path)
    pm4py.write_xes(event_log, f"./{csv_file_path.split('.csv')[0]}.xes")
    return pm4py.read_xes(f"./{csv_file_path.split('.csv')[0]}.xes")


def generate_minimal_translucent_log(log: pandas.DataFrame) -> pandas.DataFrame:
    translucent_log_inductive = generate_translucent_log(log, pm4py.discover_petri_net_inductive)
    print(f"INDUCTIVE: {translucent_log_inductive}")
    # Der ist mega kacke
    # translucent_log_ilp = generate_translucent_log(log, pm4py.discover_petri_net_ilp)
    translucent_log_split = generate_translucent_log(log, "split")
    print(f"SPLIT: {translucent_log_split}")

    translucent_logs = [translucent_log_inductive, translucent_log_split]

    def intersection_of_activities(translucent_logs: list[pandas.DataFrame]):
        # Initialize a DataFrame to store the results
        result_log = pandas.DataFrame.copy(translucent_logs[0])
        
        # Iterate over each row index
        for i in result_log.index:
            # Start with the set from the first DataFrame
            # print(f"\nEntry: {translucent_logs[0].at[i, 'enabled__activities']}")
            intersection_set = set(translucent_logs[0].at[i, 'enabled__activities'])
            
            # Compute intersection with sets from other DataFrames
            for df in translucent_logs[1:]:
                current_set = set(df.at[i, 'enabled__activities'])
                intersection_set &= current_set  # Update intersection
            
            # Convert the set back to a tuple and assign to the result DataFrame
            result_log.at[i, 'enabled__activities'] = tuple(intersection_set)

        return result_log

    minimal_translucent_log = intersection_of_activities(translucent_logs) 

    return minimal_translucent_log

def generate_translucent_log(log: pandas.DataFrame, discovery_func) -> pandas.DataFrame:

    # print(f"Discovering petri net using {discovery_func}...")

    if discovery_func == "split":
        # Run the split miner and retrieve the petri net
        net, im, fm = discover_petri_net_split("../log1.xes")
    else:
        # Discover the petri net
        net, im, fm = discovery_func(log)
                
    # pm4py.view_petri_net(net, im, fm, format="pdf")

    # TODO: find a way to make this better
    source_place = check_source_place_presence(net).name + "1"

    # Discover the reachability graph
    reach_graph = pm4py.convert_to_reachability_graph(net, im, fm)
    pm4py.view_transition_system(reach_graph, format="pdf")

    # print(f"\nTS STATES: {reach_graph.states}")
    # print(f"\nTS TRANSITIONS: {reach_graph.transitions}")

    # Create alignments and replay the alignment on the reachability graph
    alignments_diagnostics = pm4py.conformance_diagnostics_alignments(log, net, im, fm, variant_str=Variants.VERSION_TWEAKED_STATE_EQUATION_A_STAR)
    print(f"\nALIGNMENTS: {alignments_diagnostics}")
    alignments = [alignment["alignment"] for alignment in alignments_diagnostics]
    
    pm4py.view_alignments(log, alignments_diagnostics, format="pdf")
    # Create dictionary of traces with log traces as keys and model alignments as values
    unique_traces = set(tuple(trace) for trace in alignments)

    trace_dict: dict[tuple[str], tuple[str]] = {}
    for trace in unique_traces:
        trace_dict[tuple(t[0] for t in trace if t[0] != '>>')] = tuple(t[1] for t in trace)

    # Add enabled_activities column to DataFrame
    log["enabled__activities"] = None

    # Add the enabled activites to each trace
    def add_enabled_activities(group: pandas.DataFrame):

        trace = tuple(group["concept:name"].values)
        # print(f"\nTrace: {trace}")
        aligned_trace = trace_dict[trace]
        # print(f"\nAligned Trace: {aligned_trace}")

        tuple_enabled_activities = get_enabled_activities(aligned_trace, reach_graph, source_place)

        # Add enabled activites to log
        for (index, row), enabled_activities in zip(group.iterrows(), tuple_enabled_activities):
             group.at[index, 'enabled__activities'] = tuple(sorted(enabled_activities, key=str.lower))
        
        return group

    return log.groupby("case:concept:name").apply(add_enabled_activities, include_groups=False).reset_index()

def get_enabled_activities(trace: tuple[str], reachability_graph: TransitionSystem, source_place: str) -> tuple[set[str]]:

    # Init list of enabled activities
    list_enabled_activities = []

    # Init state: Start from the source state of reachability graph
    current_state = next((state for state in reachability_graph.states if state.name == source_place), 'No match found')
    # print(f"\nCurrent State: {current_state}")
    # Iterate over the trace
    for activity in trace:

        # Get all reachable transitions from current state
        reachable_activities = set(transition.name.strip("()").split(",")[1].strip().strip("'") for transition in current_state.outgoing)

        # Add enabled activities (except the current activity) to dictionary if transition is not silent
        if activity is not None: list_enabled_activities.append(reachable_activities - {"None"})

        # Update current state
        current_transition = next((transition for transition in current_state.outgoing if transition.name.strip("()").split(",")[1].strip().strip("'") == activity), "END")
        if current_transition != "END": current_state = current_transition.to_state
    
    return tuple(list_enabled_activities)

if __name__ == "__main__":
    log = convert_csv_to_xes("log1.csv")
    # log = generate_translucent_log(log, pm4py.discover_petri_net_heuristics)
    log = generate_minimal_translucent_log(log)
    # display(log)
    # print(log)
    # pm4py.write_xes(log, "log1_translucent.xes")
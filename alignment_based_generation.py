import pm4py
from pm4py.objects.transition_system.obj import TransitionSystem 
import pandas
from pm4py.algo.conformance.alignments.petri_net.algorithm import Variants

def generate_translucent_log(log: pandas.DataFrame) -> pandas.DataFrame:

    # Discover the petri net
    net, im, fm = pm4py.discover_petri_net_inductive(log)

    # Discover the reachability graph
    reach_graph = pm4py.convert_to_reachability_graph(net, im, fm)

    # Create alignments and replay the alignment on the reachability graph
    alignments_diagnostics = pm4py.conformance_diagnostics_alignments(log, net, im, fm, variant_str=Variants.VERSION_TWEAKED_STATE_EQUATION_A_STAR)
    alignments = [alignment["alignment"] for alignment in alignments_diagnostics]

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
        print(f"Trace: {trace}")
        aligned_trace = trace_dict[trace]

        tuple_enabled_activities = get_enabled_activities(aligned_trace, reach_graph)

        # Add enabled activites to log
        for (index, row), enabled_activities in zip(group.iterrows(), tuple_enabled_activities):
             group.at[index, 'enabled__activities'] = tuple(sorted(enabled_activities, key=str.lower))
        
        return group

    return log.groupby("case:concept:name", group_keys=False).apply(add_enabled_activities).reset_index()

def get_enabled_activities(trace: tuple[str], reachability_graph: TransitionSystem) -> tuple[set[str]]:

    # Init list of enabled activities
    list_enabled_activities = []

    # Init state: Start from the source state of reachability graph
    current_state = next((state for state in reachability_graph.states if state.name == "source1"), 'No match found')

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
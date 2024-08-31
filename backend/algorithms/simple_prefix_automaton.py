from .preprocessor import import_csv
import pandas as pd
from .transition_system import TransitionSystem, State, Transition

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
    


if __name__ == "__main__":
    log = import_csv("../logs/sldpn_log.csv", ",")
    prefix_automaton = generate_prefix_automaton(log)
    log = fill_enabled_activities(log, prefix_automaton)
    print(log)



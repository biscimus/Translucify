from .transition_system import State, Transition, TransitionSystem


def encode_prefix_automaton(transition_system: TransitionSystem):

    result = {
        "states": [{
            "id": state.id,  # Use the UUID instead of id()
            "name": state.name,
            "incoming": [transition.id for transition in state.incoming],  # Use UUIDs
            "outgoing": [transition.id for transition in state.outgoing]   # Use UUIDs
        } for state in transition_system.states],
        "transitions": [{
            "id": transition.id,  # Use the UUID instead of id()
            "name": transition.name,
            "from_state": transition.from_state.id,  # Use UUIDs
            "to_state": transition.to_state.id       # Use UUIDs
        } for transition in transition_system.transitions],
    }

    print("Result: ", result)

    return result

    # begin_state = [state for state in transition_system.states if state.name == "<>"][0]

    # result["states"].append({
    #     "id": id(begin_state),
    #     "name": begin_state.name,
    #     "incoming": []
    # })

def decode_prefix_automaton(states, transitions):
    print("States: ", states)
    print("Transitions: ", transitions)
    prefix_automaton = TransitionSystem(name="prefix_automaton", states=set(), transitions=set())

    # Add all states first
    for state in states:
        prefix_automaton.states.add(State(id=state["id"], name=state["name"], data={"frequency": 0}))

    # Add all transitions
    for transition in transitions:
        from_state = next((state for state in prefix_automaton.states if state.id == transition["from_state"]), None)
        to_state = next((state for state in prefix_automaton.states if state.id == transition["to_state"]), None)
        new_transition = Transition(id=transition["id"], name=transition["name"], from_state=from_state, to_state=to_state)
        prefix_automaton.transitions.add(new_transition)
        from_state.outgoing.add(new_transition)
        to_state.incoming.add(new_transition)
    
    print("Resulting prefix automaton: ", prefix_automaton)
    return prefix_automaton





















    return {}
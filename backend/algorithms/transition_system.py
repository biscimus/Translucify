from dataclasses import dataclass, field
import uuid

@dataclass
class State(object):

    name: str
    incoming: "set[Transition]" = field(default_factory=set)
    outgoing: "set[Transition]" = field(default_factory=set)
    data: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __repr__(self):
        return str(self.name)
    
    def __hash__(self):
        return id(self) 
    
@dataclass
class Transition(object):
    name: str
    from_state : State
    to_state: State
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data: dict = field(default_factory=dict)

    def __repr__(self):
        return self.from_state.name + " -> " + self.to_state.name
    
    def __hash__(self):
        return id(self)
        
@dataclass
class TransitionSystem(object):
    name: str = ""
    states: set[State] = field(default_factory=set)
    transitions: set[Transition] = field(default_factory=set)

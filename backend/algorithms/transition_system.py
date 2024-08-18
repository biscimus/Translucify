from dataclasses import dataclass, field

@dataclass
class State(object):

    name: str
    incoming: "set[Transition]" = field(default_factory=set)
    outgoing: "set[Transition]" = field(default_factory=set)
    data: dict = field(default_factory=dict)

    def __repr__(self):
        return str(self.name)
    
    def __hash__(self):
        return id(self) 
    
@dataclass
class Transition(object):

    name: str
    from_state : State
    to_state: State
    data: dict = field(default_factory=dict)

    def __repr__(self):
        return str(self.name)
    
    def __hash__(self):
        return id(self)
        
@dataclass
class TransitionSystem(object):
    name: str = ""
    states: set[State] = field(default_factory=set)
    transitions: set[Transition] = field(default_factory=set)

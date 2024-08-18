export interface EventLog {
    id?: string;
    name: string;
    type: "CSV" | "XES";
    value: File | string;
}

export interface ProcessModel {
    id: string;
    name: string;
    type: "PREFIX_AUTOMATON" | "PETRINET";
    value: File;
}

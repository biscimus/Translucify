export interface EventLog {
    id?: number;
    name: string;
    type: EventLogType;
    value: File | string;
    delimiter: string;
}

export interface ProcessModel {
    id: number;
    name: string;
    type: ProcessModelType;
    value: File;
}

export interface TranslucentEventLog {
    id?: number;
    name: string;
    type: EventLogType;
    file_path: string;
    is_ready: boolean;
    event_log_id: number;
}

export enum EventLogType {
    CSV = "CSV",
    XES = "XES",
}

export enum ProcessModelType {
    PETRINET = "PETRINET",
    PREFIX_AUTOMATON = "PREFIX_AUTOMATON",
}

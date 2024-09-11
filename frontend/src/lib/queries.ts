import { ColumnDefinition } from "src/routes/_layout/event-logs/$eventLogId/petri-net";
import axios from "./axios";
import { EventLog } from "./types";

export async function getEventLogs() {
    return (await axios.get<EventLog[]>("/event-logs")).data;
}

export async function getEventLog(eventLogId: string) {
    return (await axios.get<EventLog>(`/event-logs/${eventLogId}`)).data;
}

export async function getEventLogMetadata(eventLogId: string) {
    return (await axios.get(`/event-logs/${eventLogId}/metadata`)).data;
}

export async function postEventLog(eventLog: EventLog) {
    const formData = new FormData();
    formData.append("name", eventLog.name);
    formData.append("type", eventLog.type);
    formData.append("value", eventLog.value);
    formData.append("delimiter", eventLog.delimiter);
    return (await axios.post<EventLog>("/event-logs", formData)).data;
}

export async function patchColumns({
    eventLogId,
    columns,
}: {
    eventLogId: string;
    columns: {
        caseId: string;
        activity: string;
        timestamp: string;
    };
}) {
    return (await axios.patch(`/event-logs/${eventLogId}/columns`, { columns }))
        .data;
}

export async function getEventLogColumns(eventLogId: string) {
    return (await axios.get<string[]>(`/event-logs/${eventLogId}/columns`))
        .data;
}

export async function postTranslucentPetriNet({
    eventLogId,
    columns,
    threshold,
}: {
    eventLogId: string;
    columns: ColumnDefinition[];
    threshold: number;
}) {
    return (
        await axios.post(`/event-logs/${eventLogId}/petri-net`, {
            columns,
            threshold,
        })
    ).data;
}

export async function getTransluscentPrefixAutomaton(eventLogId: string) {
    return (await axios.get(`/event-logs/${eventLogId}/prefix-automaton`)).data;
}

export async function postTranslucentPrefixAutomaton({
    eventLogId,
    states,
    transitions,
    selectedColumns,
    threshold,
}: {
    eventLogId: string;
    states: any[];
    transitions: any[];
    selectedColumns: any[];
    threshold: number;
}) {
    return (
        await axios.post(`/event-logs/${eventLogId}/prefix-automaton`, {
            states,
            transitions,
            selectedColumns,
            threshold,
        })
    ).data;
}

export async function getTranslucentLogs(eventLogId: string) {
    return (await axios.get(`/event-logs/${eventLogId}/translucent-logs`)).data;
}

export async function getTranslucentLog(translucentLogId: number) {
    const response = await axios.get(
        `/translucent-event-logs/${translucentLogId}`,
        {
            responseType: "blob",
        }
    );
    console.log("Headers: ", response.headers);
    console.log("Data: ", response.data);
    return response.data;
}

export async function postTransluscnetTransformer({
    eventLogId,
    columns,
    threshold,
}: {
    eventLogId: string;
    columns: string[];
    threshold: number;
}) {
    return (
        await axios.post(`/event-logs/${eventLogId}/transformer`, {
            threshold,
            columns,
        })
    ).data;
}

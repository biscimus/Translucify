import { ColumnDefinition } from "src/routes/_layout/event-logs/$eventLogId/petri-net";
import axios from "./axios";
import { EventLog } from "./types";

export async function getEventLogs() {
    return (await axios.get<EventLog[]>("/event-logs")).data;
}

export async function getEventLog(eventLogId: string) {
    return (await axios.get<EventLog>(`/event-logs/${eventLogId}`)).data;
}

export async function postEventLog(eventLog: EventLog) {
    const formData = new FormData();
    formData.append("name", eventLog.name);
    formData.append("type", eventLog.type);
    formData.append("value", eventLog.value);
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

export async function getTranslucentPetriNetColumns(eventLogId: string) {
    return (await axios.get(`/event-logs/${eventLogId}/petri-net/columns`))
        .data;
}

export async function postTranslucentPetriNetColumns({
    eventLogId,
    columns,
    threshold,
}: {
    eventLogId: string;
    columns: ColumnDefinition[];
    threshold: number;
}) {
    return (
        await axios.post(`/event-logs/${eventLogId}/petri-net/columns`, {
            columns,
            threshold,
        })
    ).data;
}

export async function getTranslucentLogs(eventLogId: number) {
    return (await axios.get(`/event-logs/${eventLogId}/translucent-logs`)).data;
}

export async function getTranslucentLog(translucentLogId: number) {
    return (await axios.get(`/translucent-event-logs/${translucentLogId}`))
        .data;
}

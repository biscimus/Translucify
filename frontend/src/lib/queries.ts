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

import TranslucifyButton from "@components/TranslucifyButton";
import { getEventLog } from "@lib/queries";
import { EventLog } from "@lib/types";
import {
    Badge,
    Button,
    Chip,
    Flex,
    Space,
    Stack,
    Table,
    Title,
} from "@mantine/core";
import { createFileRoute, useLoaderData } from "@tanstack/react-router";
import { log } from "console";

export const Route = createFileRoute("/_layout/event-logs/$eventLogId/")({
    loader: ({ params, context: { queryClient } }) => {
        return queryClient.ensureQueryData({
            queryKey: ["event-logs", params.eventLogId],
            queryFn: () => {
                return getEventLog(params.eventLogId);
            },
        });
    },
    component: () => {
        const eventLog = Route.useLoaderData();
        return <LogDetailComponent eventLog={eventLog} />;
    },
});

function LogDetailComponent({ eventLog }: { eventLog: EventLog }) {
    const logData = JSON.parse(eventLog.value as string);
    console.log("Data: ", logData);

    function transposeSimple(data: any) {
        const keys = Object.keys(data[0]); // Get keys from the first object
        return keys.map((key) => data.map((obj: any) => obj[key]));
    }

    console.log("Transposed: ", transposeSimple(Object.values(logData)));

    return (
        <div>
            <Flex justify="space-between">
                <Stack>
                    <Title>{eventLog.name}</Title>
                </Stack>
                <TranslucifyButton />
            </Flex>
            <Space h="md" />
            <Badge
                size="md"
                variant="gradient"
                gradient={{ from: "blue", to: "cyan", deg: 90 }}
            >
                Type: {eventLog.type}
            </Badge>
            <Space h="xl" />
            <Title order={4}>Log Data</Title>
            <Space h="xs" />
            <Table>
                <Table.Thead>
                    <Table.Tr>
                        {Object.keys(logData).map((key) => (
                            <Table.Th key={key}>{key}</Table.Th>
                        ))}
                    </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                    {transposeSimple(Object.values(logData)).map((row) => (
                        <Table.Tr>
                            {row.map((value: string) => (
                                <Table.Td>{value}</Table.Td>
                            ))}
                        </Table.Tr>
                    ))}
                </Table.Tbody>
            </Table>
        </div>
    );
}

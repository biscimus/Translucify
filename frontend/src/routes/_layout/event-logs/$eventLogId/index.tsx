import TranslucifyButton from "@components/TranslucifyButton";
import {
    getEventLog,
    getTranslucentLog,
    getTranslucentLogs,
} from "@lib/queries";
import { EventLog, TranslucentEventLog } from "@lib/types";
import {
    ActionIcon,
    Badge,
    Flex,
    Group,
    Loader,
    Space,
    Stack,
    Table,
    Title,
} from "@mantine/core";
import { IconDownload, IconRefresh } from "@tabler/icons-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

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
    console.log("Event Log: ", eventLog);
    const logData = JSON.parse(eventLog.value as string);
    // console.log("Data: ", logData);
    const queryClient = useQueryClient();

    const {
        data: translucentLogs,
        isLoading,
        isError,
        isSuccess,
    } = useQuery({
        queryKey: ["event-logs", eventLog.id, "translucent-logs"],
        queryFn: () => getTranslucentLogs(eventLog.id!),
    });

    function transposeSimple(data: any) {
        const keys = Object.keys(data[0]); // Get keys from the first object
        return keys.map((key) => data.map((obj: any) => obj[key]));
    }

    return (
        <div style={{ padding: "2rem" }}>
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

            {/* Table for translucent logs */}
            <Group justify="space-between">
                <Title order={4}>Translucent Logs</Title>
                <ActionIcon
                    variant="subtle"
                    size="sm"
                    aria-label="Settings"
                    onClick={() => {
                        queryClient.invalidateQueries({
                            queryKey: [
                                "event-logs",
                                eventLog.id,
                                "translucent-logs",
                            ],
                        });
                    }}
                >
                    <IconRefresh color="white" />
                </ActionIcon>
            </Group>

            <Space h="xs" />

            {/* <LoadingOverlay
                    zIndex={1000}
                    visible={isLoading}
                    overlayProps={{ radius: "sm", blur: 2 }}
                > */}
            <Table>
                <Table.Thead>
                    <Table.Tr>
                        <Table.Th>ID</Table.Th>
                        <Table.Th>Name</Table.Th>
                        <Table.Th>Ready</Table.Th>
                        <Table.Th></Table.Th>
                    </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                    {isLoading && (
                        <Table.Tr>
                            <Table.Td colSpan={3}>
                                <Loader />
                            </Table.Td>
                        </Table.Tr>
                    )}
                    {isError && (
                        <Table.Tr>
                            <Table.Td colSpan={3}>
                                Error fetching data.
                            </Table.Td>
                        </Table.Tr>
                    )}

                    {isSuccess &&
                        (translucentLogs.length === 0 ? (
                            <Table.Tr>
                                <Table.Td colSpan={3}>No logs found.</Table.Td>
                            </Table.Tr>
                        ) : (
                            translucentLogs.map((log: TranslucentEventLog) => (
                                <Table.Tr key={log.id}>
                                    {" "}
                                    {/* Added key for list items */}
                                    <Table.Td>{log.id}</Table.Td>
                                    <Table.Td>{log.name}</Table.Td>
                                    <Table.Td>
                                        {log.is_ready ? "Yes" : "No"}
                                    </Table.Td>
                                    <Table.Td>
                                        <ActionIcon
                                            variant="subtle"
                                            size="sm"
                                            onClick={async () => {
                                                console.log("Buton clikced");
                                                const blob =
                                                    await queryClient.fetchQuery(
                                                        {
                                                            queryKey: [
                                                                "translucent-event-logs",
                                                                log.id,
                                                            ],
                                                            queryFn: () =>
                                                                getTranslucentLog(
                                                                    log.id!
                                                                ),
                                                        }
                                                    );
                                                const url =
                                                    window.URL.createObjectURL(
                                                        blob
                                                    );
                                                const a =
                                                    document.createElement("a");
                                                a.href = url;
                                                a.download = log.name;
                                                document.body.appendChild(a);
                                                a.click();
                                                a.remove();
                                                window.URL.revokeObjectURL(url);
                                            }}
                                        >
                                            <IconDownload />
                                        </ActionIcon>
                                    </Table.Td>
                                </Table.Tr>
                            ))
                        ))}
                </Table.Tbody>
            </Table>

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

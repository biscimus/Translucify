import EventLogTable from "@components/EventLogTable";
import TranslucifyButton from "@components/TranslucifyButton";
import {
    deleteTranslucentLog,
    getEventLogMetadata,
    getTranslucentLog,
    getTranslucentLogs,
} from "@lib/queries";
import { TranslucentEventLog } from "@lib/types";
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
import { IconDownload, IconRefresh, IconTrash } from "@tabler/icons-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { UUID } from "crypto";

export const Route = createFileRoute("/_layout/event-logs/$eventLogId/")({
    loader: ({ params, context: { queryClient } }) => {
        return queryClient.ensureQueryData({
            queryKey: ["event-logs", params.eventLogId, "metadata"],
            queryFn: () => {
                return getEventLogMetadata(params.eventLogId as UUID);
            },
        });
    },
    component: () => {
        const { eventLogId } = Route.useParams();
        return <LogDetailComponent eventLogId={eventLogId as UUID} />;
    },
});

function LogDetailComponent({ eventLogId }: { eventLogId: UUID }) {
    const { data: eventLogMetadata } = useQuery({
        queryKey: ["event-logs", eventLogId, "metadata"],
        queryFn: () => getEventLogMetadata(eventLogId),
    });

    const queryClient = useQueryClient();

    const {
        data: translucentLogs,
        isLoading,
        isError,
        isSuccess,
    } = useQuery({
        queryKey: ["event-logs", eventLogId, "translucent-logs"],
        queryFn: () => getTranslucentLogs(eventLogId),
    });

    const deleteTranslucentLogMutation = useMutation({
        mutationFn: deleteTranslucentLog,
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: ["event-logs", eventLogId, "translucent-logs"],
            });
        },
    });

    return (
        <div style={{ padding: "2rem" }}>
            <Flex justify="space-between">
                <Stack>
                    <Title>{eventLogMetadata.name}</Title>
                </Stack>
                <TranslucifyButton />
            </Flex>
            <Space h="md" />
            <Badge
                size="md"
                variant="gradient"
                gradient={{ from: "blue", to: "cyan", deg: 90 }}
            >
                Type: {eventLogMetadata.type}
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
                                eventLogId,
                                "translucent-logs",
                            ],
                        });
                    }}
                >
                    <IconRefresh color="white" />
                </ActionIcon>
            </Group>

            <Space h="xs" />

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
                                            disabled={!log.is_ready}
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
                                    <Table.Td>
                                        <ActionIcon
                                            variant="subtle"
                                            size="sm"
                                            onClick={() =>
                                                deleteTranslucentLogMutation.mutate(
                                                    log.id!
                                                )
                                            }
                                        >
                                            <IconTrash />
                                        </ActionIcon>
                                    </Table.Td>
                                </Table.Tr>
                            ))
                        ))}
                </Table.Tbody>
            </Table>

            <Space h="xl" />

            <EventLogTable eventLogId={eventLogId} />
        </div>
    );
}

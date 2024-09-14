import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { deleteEventLog, getEventLogs } from "@lib/queries";
import {
    ActionIcon,
    Flex,
    Loader,
    Modal,
    Paper,
    Table,
    Title,
    Text,
    Group,
    Button,
} from "@mantine/core";
import UploadEventLog from "@components/UploadEventLog";
import { IconTrash } from "@tabler/icons-react";
import { useDisclosure } from "@mantine/hooks";
import { useState } from "react";
import { UUID } from "crypto";

export const Route = createFileRoute("/_layout/event-logs/")({
    component: () => <LogsComponent />,
});

function LogsComponent() {
    const queryClient = useQueryClient();
    const { data, isSuccess, isLoading, isError } = useQuery({
        queryKey: ["event-logs"],
        queryFn: getEventLogs,
    });

    const navigate = useNavigate();

    const handleRowClick = (id: string) => {
        navigate({
            to: `/event-logs/${id}`,
        });
    };

    const deleteEventLogMutation = useMutation({
        mutationFn: deleteEventLog,
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: ["event-logs"],
            });
        },
    });

    const [opened, { open, close }] = useDisclosure(false);
    const [deleteLogId, setDeleteLogId] = useState<UUID | null>(null);

    if (isLoading) return <Loader />;
    if (isError) return <>Unexpected error. Please try reloading the page.</>;
    if (isSuccess) {
        return (
            <div>
                <Modal
                    opened={opened}
                    onClose={close}
                    title="Delete Event Log?"
                >
                    <Text>
                        All event log data & corresponding translucent logs will
                        be deleted!
                    </Text>
                    <Group justify="end">
                        <Button onClick={close}>Cancel</Button>
                        <Button
                            color="red"
                            onClick={() => {
                                deleteEventLogMutation.mutate(deleteLogId!);
                                close();
                            }}
                        >
                            Delete
                        </Button>
                    </Group>
                </Modal>
                <Paper shadow="md" p="xl">
                    <Flex justify="space-between">
                        <Title order={3}>All Event Logs</Title>
                        <UploadEventLog>Upload an Event Log</UploadEventLog>
                    </Flex>

                    <Table stickyHeader>
                        <Table.Thead>
                            <Table.Tr>
                                <Table.Th>Name</Table.Th>
                                <Table.Th>Type</Table.Th>
                            </Table.Tr>
                        </Table.Thead>
                        <Table.Tbody>
                            {data.map((log) => (
                                <Table.Tr
                                    key={log.id}
                                    onClick={() => handleRowClick(log.id!)}
                                >
                                    <Table.Td>{log.name}</Table.Td>
                                    <Table.Td>{log.type}</Table.Td>
                                    <Table.Td>
                                        <ActionIcon
                                            variant="subtle"
                                            size="sm"
                                            onClick={(e) => {
                                                open();
                                                e.stopPropagation();

                                                setDeleteLogId(log.id!);
                                            }}
                                        >
                                            <IconTrash />
                                        </ActionIcon>
                                    </Table.Td>
                                </Table.Tr>
                            ))}
                        </Table.Tbody>
                    </Table>
                    {data.length == 0 && (
                        <div
                            style={{
                                textAlign: "center",
                                padding: "1rem",
                            }}
                        >
                            No event logs found.
                        </div>
                    )}
                </Paper>
            </div>
        );
    }
}

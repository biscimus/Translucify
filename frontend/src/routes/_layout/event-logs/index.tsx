import { useMutation, useQuery } from "@tanstack/react-query";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { getEventLogs, postEventLog } from "@lib/queries";
import {
    Button,
    FileButton,
    Flex,
    Loader,
    Paper,
    Table,
    Title,
} from "@mantine/core";
import UploadEventLog from "@components/UploadEventLog";

export const Route = createFileRoute("/_layout/event-logs/")({
    component: () => <LogsComponent />,
});

function LogsComponent() {
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

    if (isLoading) return <Loader />;
    if (isError) return <>Unexpected error. Please try reloading the page.</>;
    if (isSuccess) {
        return (
            <div>
                <Paper shadow="xs" p="xl">
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
    return <>Helo</>;
}

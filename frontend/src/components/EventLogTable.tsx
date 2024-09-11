import { getEventLog } from "@lib/queries";
import { Loader, Pagination, Space, Stack, Table, Title } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

export default function EventLogTable({ eventLogId }: { eventLogId: string }) {
    function transposeSimple(data: any) {
        const keys = Object.keys(data[0]); // Get keys from the first object
        return keys.map((key) => data.map((obj: any) => obj[key]));
    }

    const [activePage, setPage] = useState(1);

    const {
        data: eventLog,
        isLoading,
        isError,
        isSuccess,
    } = useQuery({
        queryKey: ["event-logs", eventLogId],
        queryFn: () => getEventLog(eventLogId),
    });

    if (isLoading) {
        return <Loader />;
    }

    if (isError) {
        return <Title order={4}>Error loading log data</Title>;
    }

    if (isSuccess) {
        console.log("Value: ", eventLog.value);
        const logData = JSON.parse(eventLog.value as string);
        const logDataRows = transposeSimple(Object.values(logData));
        console.log("Event log rows: ", logDataRows);

        const paginationTotal = logDataRows.length / 20 + 1;

        return (
            <>
                <Title order={4}>Log Data</Title>
                <Space h="xs" />

                <Table.ScrollContainer minWidth={200}>
                    <Table>
                        <Table.Thead>
                            <Table.Tr>
                                {Object.keys(logData).map((key) => (
                                    <Table.Th key={key}>{key}</Table.Th>
                                ))}
                            </Table.Tr>
                        </Table.Thead>
                        <Table.Tbody>
                            {logDataRows
                                .slice((activePage - 1) * 20, activePage * 20)
                                .map((row) => (
                                    <Table.Tr>
                                        {row.map((value: string) => (
                                            <Table.Td>{value}</Table.Td>
                                        ))}
                                    </Table.Tr>
                                ))}
                        </Table.Tbody>
                    </Table>
                </Table.ScrollContainer>
                <Space h="md" />
                <Stack align="center">
                    <Pagination
                        total={paginationTotal}
                        value={activePage}
                        onChange={setPage}
                    />
                </Stack>
            </>
        );
    }
}

import { getEventLogColumns, postTransluscnetTransformer } from "@lib/queries";
import {
    Space,
    Title,
    Text,
    Slider,
    Group,
    Button,
    MultiSelect,
} from "@mantine/core";
import { useMutation, useQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";

export const Route = createFileRoute(
    "/_layout/event-logs/$eventLogId/transformer/"
)({
    component: () => {
        const { eventLogId } = Route.useParams();
        return <TransformerComponent eventLogId={eventLogId} />;
    },
});

function TransformerComponent({ eventLogId }: { eventLogId: string }) {
    const navigate = useNavigate();
    const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
    const [threshold, setThreshold] = useState(0);

    const {
        data: columns,
        isLoading,
        isError,
        isSuccess,
    } = useQuery<string[]>({
        queryKey: ["event-logs", eventLogId, "transformer/columns"],
        queryFn: () => getEventLogColumns(eventLogId),
    });

    const columnMutation = useMutation({
        mutationFn: postTransluscnetTransformer,
    });

    if (isLoading) {
        return <div>Loading...</div>;
    }

    if (isError) {
        return <div>Error fetching data.</div>;
    }

    if (isSuccess)
        return (
            <div style={{ padding: "2rem" }}>
                <Title order={2}>Regression Configuration</Title>
                <Space h="xl" />
                <Title order={4}>Choose data columns</Title>
                <Space h="xs" />
                <MultiSelect
                    placeholder="Data Columns"
                    value={selectedColumns}
                    data={columns}
                    onChange={(value) => {
                        console.log("changed columns: ", value);
                        console.log("columns: ", columns);
                        const existingColumnSet = new Set(selectedColumns);

                        // Determine columns to add or remove
                        const columnsToAdd = value.filter(
                            (col) => !existingColumnSet.has(col)
                        );
                        const columnsToRemove = selectedColumns.filter(
                            (col) => !value.includes(col)
                        );
                        setSelectedColumns((prev) => [
                            ...prev.filter(
                                (col) => !columnsToRemove.includes(col)
                            ), // Remove columns
                            ...columnsToAdd,
                        ]);
                    }}
                    hidePickedOptions
                />

                <Space h="md" />
                <Title order={4}>Choose Threshold</Title>
                <Space h="xs" />
                <Text>Threshold: {threshold}%</Text>
                <Slider
                    min={0}
                    max={1}
                    step={0.01}
                    value={threshold}
                    onChange={setThreshold}
                />
                <Space h="md" />
                <Group justify="end">
                    <Button
                        onClick={() => {
                            columnMutation.mutate({
                                eventLogId,
                                columns: selectedColumns,
                                threshold,
                            });
                            navigate({
                                from: "/event-logs/$eventLogId/transformer",
                                to: "/event-logs/$eventLogId",
                            });
                        }}
                        variant="gradient"
                        gradient={{ from: "blue", to: "cyan", deg: 90 }}
                    >
                        Discover Translucent Log
                    </Button>
                </Group>
            </div>
        );
}

import {
    getEventLog,
    getTranslucentPetriNetColumns,
    postTranslucentPetriNetColumns,
} from "@lib/queries";
import {
    Button,
    Group,
    MultiSelect,
    Slider,
    Space,
    Stack,
    Switch,
    Text,
    Title,
} from "@mantine/core";
import { useMutation, useQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";

export const Route = createFileRoute(
    "/_layout/event-logs/$eventLogId/petri-net/"
)({
    component: () => {
        const { eventLogId } = Route.useParams();
        return <PetriNetComponent eventLogId={eventLogId} />;
    },
});

type ColumnType = "numerical" | "categorical";
export type ColumnDefinition = {
    column: string;
    type: ColumnType;
};

function PetriNetComponent({ eventLogId }: { eventLogId: string }) {
    const navigate = useNavigate();
    const [selectedColumns, setSelectedColumns] = useState<ColumnDefinition[]>(
        []
    );
    const [threshold, setThreshold] = useState(0);
    const {
        data: columns,
        isLoading,
        isError,
        isSuccess,
    } = useQuery<string[]>({
        queryKey: ["event-logs", eventLogId, "petri-net/columns"],
        queryFn: () => getTranslucentPetriNetColumns(eventLogId),
    });

    const columnMutation = useMutation({
        mutationFn: postTranslucentPetriNetColumns,
    });

    console.log("Selected columns:", selectedColumns);

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
                    value={selectedColumns.map((column) => column.column)}
                    data={columns}
                    onChange={(value) => {
                        console.log("changed columns: ", value);
                        console.log("columns: ", columns);
                        const existingColumnSet = new Set(
                            selectedColumns.map((col) => col.column)
                        );

                        // Determine columns to add or remove
                        const columnsToAdd = value.filter(
                            (col) => !existingColumnSet.has(col)
                        );
                        const columnsToRemove = selectedColumns.filter(
                            (col) => !value.includes(col.column)
                        );
                        setSelectedColumns((prev) => [
                            ...prev.filter(
                                (col) => !columnsToRemove.includes(col)
                            ), // Remove columns
                            ...columnsToAdd.map((col) => ({
                                column: col,
                                type: "categorical" as ColumnType,
                            })),
                        ]);
                    }}
                    hidePickedOptions
                />
                <Space h="md" />
                <Stack gap="md">
                    {selectedColumns.map((column) => (
                        <Group key={column.column} justify="space-between">
                            <Text>{column.column}</Text>
                            <Switch
                                label={column.type}
                                onChange={(event) => {
                                    const type = event.target.checked
                                        ? "numerical"
                                        : "categorical";
                                    setSelectedColumns((prev) => {
                                        return prev.map((prevColumn) => {
                                            if (
                                                prevColumn.column ===
                                                column.column
                                            ) {
                                                return {
                                                    column: prevColumn.column,
                                                    type,
                                                };
                                            }
                                            return prevColumn;
                                        });
                                    });
                                }}
                            />
                        </Group>
                    ))}
                </Stack>

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
                                from: "/event-logs/$eventLogId/petri-net",
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

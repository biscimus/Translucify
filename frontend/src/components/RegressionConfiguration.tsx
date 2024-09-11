import {
    Button,
    Group,
    MultiSelect,
    Slider,
    Space,
    Stack,
    Switch,
    Title,
    Text,
} from "@mantine/core";
import {
    ColumnDefinition,
    ColumnType,
} from "src/routes/_layout/event-logs/$eventLogId/petri-net";

export default function RegressionConfiguration({
    columns,
    selectedColumns,
    setSelectedColumns,
    threshold,
    setThreshold,
    translucifyFunction,
    buttonText = "Discover Translucent Log",
}: {
    columns: any[];
    selectedColumns: ColumnDefinition[];
    setSelectedColumns: React.Dispatch<
        React.SetStateAction<ColumnDefinition[]>
    >;
    threshold: number;
    setThreshold: any;
    translucifyFunction: any;
    buttonText?: string;
}) {
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
                        ...prev.filter((col) => !columnsToRemove.includes(col)), // Remove columns
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
                                            prevColumn.column === column.column
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
            <Text>Threshold: {Math.round(threshold * 100)}%</Text>
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
                    onClick={translucifyFunction}
                    variant="gradient"
                    gradient={{ from: "blue", to: "cyan", deg: 90 }}
                >
                    {buttonText}
                </Button>
            </Group>
        </div>
    );
}

import PrefixAutomaton from "@components/prefix-automaton/PrefixAutomaton";
import RegressionConfiguration from "@components/RegressionConfiguration";
import {
    getEventLogColumns,
    getTransluscentPrefixAutomaton,
    postTranslucentPrefixAutomaton,
} from "@lib/queries";
import { Space, Stepper, Title } from "@mantine/core";
import { useMutation, useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { ColumnDefinition } from "../petri-net";

export const Route = createFileRoute(
    "/_layout/event-logs/$eventLogId/prefix-automaton/"
)({
    component: () => {
        const { eventLogId } = Route.useParams();
        return <PrefixAutomatonComponent eventLogId={eventLogId} />;
    },
});

function PrefixAutomatonComponent({ eventLogId }: { eventLogId: string }) {
    // Stepper state
    const [active, setActive] = useState(0);
    const nextStep = () =>
        setActive((current) => (current < 2 ? current + 1 : current));

    const [selectedColumns, setSelectedColumns] = useState<ColumnDefinition[]>(
        []
    );
    const [threshold, setThreshold] = useState(0);

    const {
        data: paData,
        isLoading,
        isError,
        isSuccess,
    } = useQuery({
        queryKey: ["event-logs", eventLogId, "prefix-automaton"],
        queryFn: () => getTransluscentPrefixAutomaton(eventLogId),
    });

    const {
        data: columns,
        isLoading: isColumnsLoading,
        isError: isColumnsError,
        isSuccess: isColumnsSuccess,
    } = useQuery({
        queryKey: ["event-logs", eventLogId, "prefix-automaton/columns"],
        queryFn: () => getEventLogColumns(eventLogId),
    });

    const prefixAutomatonMutation = useMutation({
        mutationFn: postTranslucentPrefixAutomaton,
    });

    return (
        <div style={{ padding: "2rem" }}>
            <Title order={2}>Prefix Automaton</Title>
            <Space h="xl" />
            <Stepper active={active} onStepClick={setActive} size="sm">
                <Stepper.Step
                    label="First Step"
                    description="Select your Columns"
                    loading={isColumnsLoading}
                >
                    {isColumnsLoading && <div>Loading...</div>}
                    {isColumnsError && <div>Error fetching data</div>}
                    {isColumnsSuccess && (
                        <RegressionConfiguration
                            columns={columns}
                            selectedColumns={selectedColumns}
                            setSelectedColumns={setSelectedColumns}
                            threshold={threshold}
                            setThreshold={setThreshold}
                            translucifyFunction={() => {
                                nextStep();
                            }}
                            buttonText="Next"
                        />
                    )}
                </Stepper.Step>
                <Stepper.Step
                    label="Second Step"
                    description="Fine-tune your Prefix Automaton"
                    loading={isLoading}
                >
                    {isLoading && <div>Loading...</div>}
                    {isError && <div>Error fetching data</div>}
                    {isSuccess && (
                        <PrefixAutomaton
                            data={paData}
                            eventLogId={eventLogId}
                            prefixAutomatonMutation={prefixAutomatonMutation}
                            selectedColumns={selectedColumns}
                            threshold={threshold}
                        />
                    )}
                </Stepper.Step>
                {/* <Stepper.Completed>
                        <Stack>
                            Event Log ready to be translucified!
                            <Group justify="end">
                                <Button
                                    onClick={() => {
                                        setActive(0);
                                        close();
                                    }}
                                    color="red"
                                >
                                    Close
                                </Button>
                                <Link
                                    to="/event-logs/$eventLogId"
                                    params={{
                                        eventLogId: fileMutation.data?.id!,
                                    }}
                                >
                                    <Button>View Event Log</Button>
                                </Link>
                            </Group>
                        </Stack>
                    </Stepper.Completed> */}
            </Stepper>
        </div>
    );
}

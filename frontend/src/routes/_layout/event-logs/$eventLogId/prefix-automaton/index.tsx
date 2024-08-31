import PrefixAutomaton from "@components/prefix-automaton/PrefixAutomaton";
import { getTransluscentPrefixAutomaton } from "@lib/queries";
import { Space, Title } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute(
    "/_layout/event-logs/$eventLogId/prefix-automaton/"
)({
    component: () => {
        const { eventLogId } = Route.useParams();
        return <PrefixAutomatonComponent eventLogId={eventLogId} />;
    },
});

function PrefixAutomatonComponent({ eventLogId }: { eventLogId: string }) {
    const {
        data: paData,
        isLoading,
        isError,
        isSuccess,
    } = useQuery({
        queryKey: ["event-logs", eventLogId, "prefix-automaton"],
        queryFn: () => getTransluscentPrefixAutomaton(eventLogId),
    });

    return (
        <div style={{ padding: "2rem" }}>
            <Title order={2}>Prefix Automaton</Title>
            <Space h="xl" />
            {isLoading && <div>Loading...</div>}
            {isError && <div>Error fetching data</div>}
            {isSuccess && (
                <PrefixAutomaton data={paData} eventLogId={eventLogId} />
            )}
        </div>
    );
}

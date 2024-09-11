import RegressionConfiguration from "@components/RegressionConfiguration";
import { getEventLogColumns, postTranslucentPetriNet } from "@lib/queries";

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

export type ColumnType = "numerical" | "categorical";
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
        queryFn: () => getEventLogColumns(eventLogId),
    });

    const columnMutation = useMutation({
        mutationFn: postTranslucentPetriNet,
    });

    const translucifyFunction = () => {
        columnMutation.mutate({
            eventLogId,
            columns: selectedColumns,
            threshold,
        });
        navigate({
            from: "/event-logs/$eventLogId/petri-net",
            to: "/event-logs/$eventLogId",
        });
    };

    console.log("Selected columns:", selectedColumns);

    if (isLoading) {
        return <div>Loading...</div>;
    }

    if (isError) {
        return <div>Error fetching data.</div>;
    }

    if (isSuccess)
        return (
            <RegressionConfiguration
                columns={columns}
                selectedColumns={selectedColumns}
                setSelectedColumns={setSelectedColumns}
                threshold={threshold}
                setThreshold={setThreshold}
                translucifyFunction={translucifyFunction}
            />
        );
}
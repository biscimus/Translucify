import { Button } from "@mantine/core";
import { createFileRoute, Link } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
    component: () => (
        <>
            <div>Discover Enabled Activities</div>
            <Link to="/event-logs">
                <Button>Go to your logs</Button>
            </Link>
        </>
    ),
});

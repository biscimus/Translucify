import { Button, Card, Center, Stack, Title } from "@mantine/core";
import { createFileRoute, Link } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
    component: () => (
        <>
            <Center h={700}>
                <Card shadow="md" radius="md" p="xl">
                    <Stack align="center">
                        <Title order={4}>Discover Enabled Activities</Title>
                        <Link to="/event-logs">
                            <Button mt="sm">Go to your logs</Button>
                        </Link>
                    </Stack>
                </Card>
            </Center>
        </>
    ),
});

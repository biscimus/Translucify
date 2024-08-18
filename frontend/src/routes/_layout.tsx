import { getEventLogs } from "@lib/queries";
import { AppShell, Burger, Loader, NavLink, Title } from "@mantine/core";
import { IconTable } from "@tabler/icons-react";
import { useDisclosure } from "@mantine/hooks";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/_layout")({
    component: Demo,
});

function Demo() {
    const [opened, { toggle }] = useDisclosure();
    const { data, isSuccess, isLoading, isError } = useQuery({
        queryKey: ["event-logs"],
        queryFn: getEventLogs,
    });

    return (
        <AppShell
            header={{ height: 60 }}
            navbar={{
                width: 300,
                breakpoint: "sm",
                collapsed: { mobile: !opened },
            }}
            padding="md"
        >
            <AppShell.Header>
                <Burger
                    opened={opened}
                    onClick={toggle}
                    hiddenFrom="sm"
                    size="sm"
                />
                <Link
                    to="/event-logs"
                    style={{ color: "inherit", textDecoration: "inherit" }}
                >
                    <Title
                        style={{
                            color: "inherit",
                            padding: "1rem",
                        }}
                        order={3}
                    >
                        Translucify
                    </Title>
                </Link>
            </AppShell.Header>

            <AppShell.Navbar p="md">
                {isLoading ? (
                    <Loader color="blue" />
                ) : isError ? (
                    <div>Failed to fetch data.</div>
                ) : isSuccess ? (
                    <NavLink
                        href="#required-for-focus"
                        label="Event Logs"
                        childrenOffset={28}
                        defaultOpened
                        leftSection={<IconTable />}
                    >
                        {data.map((log) => (
                            <NavLink
                                key={log.id}
                                label={log.name}
                                href={`/event-logs/${log.id}`}
                            />
                        ))}
                    </NavLink>
                ) : null}
            </AppShell.Navbar>

            <AppShell.Main>
                <Outlet />
            </AppShell.Main>
        </AppShell>
    );
}

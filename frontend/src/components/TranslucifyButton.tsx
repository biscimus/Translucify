import { Button, Menu, rem, Text } from "@mantine/core";
import { IconMessageCircle, IconSettings, IconAi } from "@tabler/icons-react";
import { Link } from "@tanstack/react-router";

export default function TranslucifyButton() {
    function handlePetriNetClick() {}

    function handlePrefixAutomatonClick() {}

    function handleTransformerClick() {}

    return (
        <Menu shadow="md" width={200} withArrow>
            <Menu.Target>
                <Button
                    variant="gradient"
                    gradient={{ from: "blue", to: "cyan", deg: 90 }}
                >
                    Translucify!
                </Button>
            </Menu.Target>

            <Menu.Dropdown>
                <Menu.Label>Continue with a model</Menu.Label>
                <Link
                    from="/event-logs/$eventLogId"
                    to="/event-logs/$eventLogId/petri-net"
                    style={{ textDecoration: "inherit" }}
                >
                    <Menu.Item
                        leftSection={
                            <IconSettings
                                style={{ width: rem(14), height: rem(14) }}
                            />
                        }
                        onClick={handlePetriNetClick}
                    >
                        <div>
                            <Text>Petri Net</Text>
                            <Text size="xs" c="dimmed">
                                Classic option for process modeling
                            </Text>
                        </div>
                    </Menu.Item>
                </Link>

                <Link
                    from="/event-logs/$eventLogId"
                    to="/event-logs/$eventLogId/prefix-automaton"
                    style={{ textDecoration: "inherit" }}
                >
                    <Menu.Item
                        leftSection={
                            <IconMessageCircle
                                style={{ width: rem(14), height: rem(14) }}
                            />
                        }
                        onClick={handlePrefixAutomatonClick}
                    >
                        <div>
                            <Text>Prefix Automaton</Text>
                            <Text size="xs" c="dimmed">
                                Equipped with manually customizable states
                            </Text>
                        </div>
                    </Menu.Item>
                </Link>

                <Menu.Divider />

                <Menu.Label>Continue without a model</Menu.Label>
                <Link
                    from="/event-logs/$eventLogId"
                    to="/event-logs/$eventLogId/transformer"
                    style={{ textDecoration: "inherit" }}
                >
                    <Menu.Item
                        leftSection={
                            <IconAi
                                style={{ width: rem(14), height: rem(14) }}
                            />
                        }
                        onClick={handleTransformerClick}
                    >
                        <div>
                            <Text>Transformer</Text>
                            <Text size="xs" c="dimmed">
                                Try out the powerful Transformer model
                            </Text>
                        </div>
                    </Menu.Item>
                </Link>
            </Menu.Dropdown>
        </Menu>
    );
}

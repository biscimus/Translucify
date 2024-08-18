import { Button, Menu, rem, Text } from "@mantine/core";
import {
    IconArrowsLeftRight,
    IconMessageCircle,
    IconPhoto,
    IconSearch,
    IconSettings,
    IconTrash,
    IconAi,
} from "@tabler/icons-react";

export default function TranslucifyButton() {
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
                <Menu.Item
                    leftSection={
                        <IconSettings
                            style={{ width: rem(14), height: rem(14) }}
                        />
                    }
                >
                    <div>
                        <Text>Petri Net</Text>
                        <Text size="xs" c="dimmed">
                            Classic option for process modeling
                        </Text>
                    </div>
                </Menu.Item>
                <Menu.Item
                    leftSection={
                        <IconMessageCircle
                            style={{ width: rem(14), height: rem(14) }}
                        />
                    }
                >
                    <div>
                        <Text>Prefix Automaton</Text>
                        <Text size="xs" c="dimmed">
                            Let's see how the BA goes!
                        </Text>
                    </div>
                </Menu.Item>

                <Menu.Divider />

                <Menu.Label>Continue without a model</Menu.Label>
                <Menu.Item
                    leftSection={
                        <IconAi style={{ width: rem(14), height: rem(14) }} />
                    }
                >
                    <div>
                        <Text>Transformer</Text>
                        <Text size="xs" c="dimmed">
                            Try out the powerful Transformer model
                        </Text>
                    </div>
                </Menu.Item>
            </Menu.Dropdown>
        </Menu>
    );
}

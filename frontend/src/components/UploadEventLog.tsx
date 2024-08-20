import {
    Button,
    Modal,
    FileInput,
    TextInput,
    Flex,
    Stepper,
    Select,
    Stack,
    Group,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { patchColumns, postEventLog } from "@lib/queries";
import { Link } from "@tanstack/react-router";

export default function UploadEventLogButton({
    children,
}: {
    children: string;
}) {
    const queryClient = useQueryClient();

    // Modal state
    const [opened, { open, close }] = useDisclosure(false);

    // Stepper state
    const [active, setActive] = useState(0);
    const nextStep = () =>
        setActive((current) => (current < 2 ? current + 1 : current));

    // Step 1 states
    const [name, setName] = useState("");
    const [file, setFile] = useState<File | null>(null);

    const [columns, setColumns] = useState<string[]>([]);

    // Step 1 mutation
    const fileMutation = useMutation({
        mutationFn: postEventLog,
        onSuccess: (data) => {
            console.log("Success: ", data);
            setColumns(data.columns);
            nextStep();
        },
    });

    // Step 2 states

    const [caseId, setCaseId] = useState<string | null>("");
    const [activity, setActivity] = useState<string | null>("");
    const [timestamp, setTimestamp] = useState<string | null>("");

    // Step 2 mutation

    const columnMutation = useMutation({
        mutationFn: patchColumns,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["event-logs"] });
            nextStep();
        },
    });

    return (
        <>
            <Button onClick={open}>{children}</Button>
            <Modal opened={opened} onClose={close} title="Add an Event Log">
                <Stepper active={active} onStepClick={setActive} size="sm">
                    <Stepper.Step
                        label="First Step"
                        description="Upload your Event Log"
                    >
                        <Flex direction="column" gap="sm">
                            <TextInput
                                required
                                label="Event Log Name"
                                onChange={(e) => setName(e.currentTarget.value)}
                            />
                            <FileInput
                                required
                                onChange={(file) => setFile(file)}
                                label="Event Log Data"
                                description="We currently only accept CSV and XES files. The CSV file must be delimited with semicolons."
                            />
                            <Button
                                onClick={() => {
                                    fileMutation.mutate({
                                        name: name,
                                        type: file?.name.endsWith(".csv")
                                            ? "CSV"
                                            : "XES",
                                        value: file as File,
                                    });
                                }}
                            >
                                Upload
                            </Button>
                        </Flex>
                    </Stepper.Step>
                    <Stepper.Step
                        label="Second Step"
                        description="Select your Columns"
                    >
                        <Flex direction="column" gap="sm">
                            <Select
                                required
                                label="Case ID"
                                placeholder="Enter Case ID Column"
                                value={caseId}
                                onChange={setCaseId}
                                data={columns}
                            />
                            <Select
                                required
                                label="Activity Label"
                                placeholder="Enter Activity Column"
                                value={activity}
                                onChange={setActivity}
                                data={columns}
                            />
                            <Select
                                required
                                label="Timestamp"
                                placeholder="Enter Timestamp Column"
                                value={timestamp}
                                onChange={setTimestamp}
                                data={columns}
                            />
                            <Button
                                onClick={() => {
                                    columnMutation.mutate({
                                        eventLogId: fileMutation.data?.id!,
                                        columns: {
                                            caseId,
                                            activity,
                                            timestamp,
                                        } as {
                                            caseId: string;
                                            activity: string;
                                            timestamp: string;
                                        },
                                    });
                                }}
                            >
                                Submit
                            </Button>
                        </Flex>
                    </Stepper.Step>
                    <Stepper.Completed>
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
                    </Stepper.Completed>
                </Stepper>
            </Modal>
        </>
    );
}

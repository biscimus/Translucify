import { Button, Modal, FileInput, TextInput, Flex } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { postEventLog } from "@lib/queries";

export default function UploadEventLogButton({
    children,
}: {
    children: string;
}) {
    const [name, setName] = useState("");
    const [file, setFile] = useState<File | null>(null);
    const [opened, { open, close }] = useDisclosure(false);
    const queryClient = useQueryClient();

    const fileMutation = useMutation({
        mutationFn: postEventLog,
    });

    console.log("Name: ", name);
    console.log("File: ", file);

    // TODO: Implement uploadFile function
    const onSubmitEventLog = () => {
        console.log("submitting event log");

        // axios.post("/event-logs", formData);
        fileMutation.mutate({
            name: name,
            type: file?.name.endsWith(".csv") ? "CSV" : "XES",
            value: file as File,
        });

        queryClient.invalidateQueries({ queryKey: ["event-logs"] });
        close();
    };

    return (
        <>
            <Button onClick={open}>{children}</Button>
            <Modal opened={opened} onClose={close} title="Add an Event Log">
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
                    />
                    <Button onClick={onSubmitEventLog}>Upload</Button>
                </Flex>
                {/* <form action="POST" hx-trigger="submit">
                    <input type="text" name="username" />
                    <input type="password" name="password" />
                    <button type="submit">Submit</button>
                </form> */}
            </Modal>
        </>
    );
}

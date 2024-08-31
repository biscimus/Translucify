import { Handle, Position } from "@xyflow/react";
import { Box, Checkbox } from "@mantine/core";

export default function PANode({ data }: { data: any }) {
    const handleCheckboxChange = () => {
        // Uncheck and remove the state from the selectedStates array

        data.setSelectedStates((prev: any[]) => {
            if (prev.includes(data.id)) {
                return prev.filter((state) => state !== data.id);
            } else {
                return [...prev, data.id];
            }
        });
    };

    return (
        <div>
            <Handle type="target" position={Position.Left} />
            <Box bg="grey" p="sm" style={{ borderRadius: "1rem" }}>
                <Checkbox onChange={handleCheckboxChange} />
                <div>{data.label}</div>
            </Box>
            <Handle type="source" position={Position.Right} />
        </div>
    );
}

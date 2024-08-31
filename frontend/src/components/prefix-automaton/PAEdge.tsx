import { BaseEdge, getBezierPath, EdgeLabelRenderer } from "@xyflow/react";

export default function CustomEdge({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    label,
    markerEnd,
}: any) {
    const [edgePath, labelX, labelY] = getBezierPath({
        sourceX,
        sourceY,
        targetX,
        targetY,
    });

    console.log("Edge label: ", label);

    return (
        <>
            <BaseEdge
                id={id}
                path={edgePath}
                // labelShowBg={false}
                markerEnd={markerEnd}
            />
            <EdgeLabelRenderer>
                <div
                    style={{
                        position: "absolute",
                        transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
                        pointerEvents: "all",
                    }}
                >
                    {label}
                </div>
            </EdgeLabelRenderer>
        </>
    );
}

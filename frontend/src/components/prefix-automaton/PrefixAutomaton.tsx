import {
    ReactFlow,
    Background,
    Controls,
    useNodesState,
    useEdgesState,
    addEdge,
    MarkerType,
    Panel,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useMemo, useState } from "react";
import PANode from "./PANode";
import PAEdge from "./PAEdge";
import { Button, Group, Stack } from "@mantine/core";
import { useNavigate } from "@tanstack/react-router";
import { ColumnDefinition } from "src/routes/_layout/event-logs/$eventLogId/petri-net";

export default function PrefixAutomaton({
    data,
    eventLogId,
    prefixAutomatonMutation,
    selectedColumns,
    method,
    threshold,
}: {
    data: any;
    eventLogId: string;
    prefixAutomatonMutation: any;
    selectedColumns: ColumnDefinition[];
    method: string;
    threshold: number;
}) {
    const navigate = useNavigate();

    const [selectedStates, setSelectedStates] = useState<string[]>([]);
    console.log("Selected States: ", selectedStates);

    const initialStates = structuredClone(data.states);
    const initialTransitions = structuredClone(data.transitions);

    const initialNodes: any[] = [],
        initialEdges: any[] = [];

    const initialX = 0;
    const initialY = 0;

    const initialState = initialStates.splice(
        initialStates.findIndex((state: any) => state.name === "<>"),
        1
    )[0];

    // while (initialStates.length > 0) {
    const node = {
        id: initialState.id,
        type: "PANode",
        position: { x: initialX, y: initialY },
        data: {
            label: initialState.name,
            setSelectedStates: setSelectedStates,
            id: initialState.id,
        },
        sourcePosition: "right",
        targetPosition: "left",
    };
    initialNodes.push(node);

    // const numOfTransitions = initialState.outgoing.length;

    const addState = (
        prevState: any,
        transitionId: any,
        xPosition: number,
        yPosition: number
    ) => {
        // Get the transition object from the initialTransitions array
        const transition = initialTransitions.filter(
            (transition: any) => transition.id === transitionId
        )[0];

        // Get the state object from the initialStates array
        const currState = initialStates.filter(
            (state: any) => state.id === transition.to_state
        )[0];

        // Add the state node
        const node = {
            id: currState.id,
            type: "PANode",
            position: { x: xPosition, y: yPosition },
            data: {
                label: currState.name,
                setSelectedStates: setSelectedStates,
                id: currState.id,
            },
            sourcePosition: "right",
            targetPosition: "left",
        };
        initialNodes.push(node);

        // Add the edge
        const edge = {
            id: transition.id,
            source: prevState.id,
            target: currState.id,
            label: transition.name,
            type: "PAEdge",
            animated: true,
            markerEnd: {
                type: MarkerType.ArrowClosed,
                width: 15,
                height: 15,
            },
        };
        initialEdges.push(edge);

        currState.outgoing.forEach((transition: any, index: number) => {
            addState(
                currState,
                transition,
                xPosition + 200,
                yPosition + 100 * index
            );
        });
    };

    console.log("initial state outgoing", initialState.outgoing);

    initialState.outgoing.forEach((transitionId: string, index: number) => {
        addState(
            initialState,
            transitionId,
            initialX + 200,
            initialY + index * 100
        );
    });

    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    console.log("Nodes: ", nodes);
    console.log("Edges: ", edges);

    const edgeTypes = {
        PAEdge: PAEdge,
    };
    const onConnect = useCallback(
        (connection: any) => {
            const edge = { ...connection, type: PAEdge };
            setEdges((eds: any) => addEdge(edge, eds));
        },
        [setEdges]
    );
    const nodeTypes = useMemo(() => ({ PANode: PANode }), []);

    const handleMergeStates = () => {
        const selectedNodes = nodes.filter((node) =>
            selectedStates.includes(node.id)
        );
        console.log("Selected Nodes: ", selectedNodes);

        if (selectedNodes.length === 0) return;

        const newNodeId = selectedNodes.map((node) => node.id).join(", ");
        const newNodeXPosition =
            selectedNodes.reduce((p, c) => p + c.position.x, 0) /
            selectedNodes.length;
        const newNodeYPosition =
            selectedNodes.reduce((p, c) => p + c.position.y, 0) /
            selectedNodes.length;

        // Create a new node with the label as the concatenation of the selected nodes
        const newNode = {
            id: newNodeId,
            type: "PANode",
            position: { x: newNodeXPosition, y: newNodeYPosition },
            data: {
                label: selectedNodes.map((node) => node.data.label).join(", "),
                setSelectedStates: setSelectedStates,
                id: newNodeId,
            },
            sourcePosition: "right",
            targetPosition: "left",
        };

        // Remove the selected nodes from the nodes array
        setNodes((prevNodes: any[]) => {
            return prevNodes
                .filter((node) => !selectedStates.includes(node.id))
                .concat(newNode);
        });

        // Get all incoming & outgoing edges of the selected nodes
        const incomingEdges = edges.filter((edge) =>
            selectedStates.includes(edge.target)
        );
        const outgoingEdges = edges.filter((edge) =>
            selectedStates.includes(edge.source)
        );

        // Modify incoming & outgoing edges to point to the new node
        const modifiedIncomingEdges = incomingEdges.map((edge) => {
            return {
                ...edge,
                target: newNodeId,
            };
        });

        const modifiedOutgoingEdges = outgoingEdges.map((edge) => {
            return {
                ...edge,
                source: newNodeId,
            };
        });

        setEdges((prevEdges: any[]) => {
            return prevEdges
                .filter(
                    (edge) =>
                        !selectedStates.includes(edge.source) &&
                        !selectedStates.includes(edge.target)
                )
                .concat(modifiedIncomingEdges)
                .concat(modifiedOutgoingEdges);
        });

        setSelectedStates([]);
    };

    return (
        <Stack>
            {/* <pre>{JSON.stringify(data, null, 2)}</pre> */}
            <div
                style={{
                    border: "solid 0.5px white",
                    borderRadius: "5px",
                    width: "75vw",
                    height: "60vh",
                }}
            >
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    nodeTypes={nodeTypes}
                    edgeTypes={edgeTypes}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    elementsSelectable
                    fitView
                >
                    <Panel position="top-left">
                        <Button onClick={handleMergeStates}>
                            Merge States
                        </Button>
                    </Panel>
                    <Background variant="dots" />
                    <Controls />
                </ReactFlow>
            </div>
            <Group justify="end">
                <Button
                    fullWidth={false}
                    onClick={() => {
                        prefixAutomatonMutation.mutate({
                            eventLogId,
                            states: nodes.map((node) => {
                                return {
                                    id: node.id,
                                    name: node.data.label,
                                };
                            }),
                            transitions: edges.map((edge) => {
                                return {
                                    id: edge.id,
                                    name: edge.label,
                                    from_state: edge.source,
                                    to_state: edge.target,
                                };
                            }),
                            selectedColumns,
                            method,
                            threshold,
                        });
                        navigate({
                            from: "/event-logs/$eventLogId/prefix-automaton",
                            to: "/event-logs/$eventLogId",
                        });
                    }}
                    variant="gradient"
                    gradient={{ from: "blue", to: "cyan", deg: 90 }}
                >
                    Discover Translucent Log
                </Button>
            </Group>
        </Stack>
    );
}

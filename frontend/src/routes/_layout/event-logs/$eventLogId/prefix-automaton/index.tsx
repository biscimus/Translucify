import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_layout/event-logs/$eventLogId/prefix-automaton/')({
  component: () => <div>Hello /_layout/event-logs/$eventLogId/prefix-automaton/!</div>
})
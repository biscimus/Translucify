import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_layout/event-logs/$eventLogId/transformer/')({
  component: () => <div>Hello /_layout/event-logs/$eventLogId/transformer/!</div>
})
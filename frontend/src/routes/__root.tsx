import { createRootRouteWithContext, Outlet } from "@tanstack/react-router";
import React from "react";
import { MantineProvider } from "@mantine/core";
import "@mantine/core/styles.css";
import { QueryClient } from "@tanstack/react-query";

const TanStackRouterDevtools =
    process.env.NODE_ENV === "production"
        ? () => null // Render nothing in production
        : React.lazy(() =>
              // Lazy load in development
              import("@tanstack/router-devtools").then((res) => ({
                  default: res.TanStackRouterDevtools,
                  // For Embedded Mode
                  // default: res.TanStackRouterDevtoolsPanel
              }))
          );

interface MyRouterContext {
    queryClient: QueryClient;
}

export const Route = createRootRouteWithContext<MyRouterContext>()({
    component: () => (
        <>
            <MantineProvider defaultColorScheme="dark">
                <Outlet />
                <TanStackRouterDevtools />
            </MantineProvider>
        </>
    ),
});

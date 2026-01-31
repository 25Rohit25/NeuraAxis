import type { Preview } from "@storybook/react";
import React from "react";
import "../src/app/globals.css";
import { ToastProvider } from "../src/components/ui/Toast";
import { ThemeProvider } from "../src/providers/ThemeProvider";

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: "^on[A-Z].*" },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    backgrounds: {
      default: "light",
      values: [
        { name: "light", value: "#ffffff" },
        { name: "dark", value: "#0f172a" },
      ],
    },
    a11y: {
      config: {
        rules: [
          { id: "color-contrast", enabled: true },
          { id: "label", enabled: true },
        ],
      },
    },
  },
  decorators: [
    (Story, context) => {
      const isDark = context.globals.backgrounds?.value === "#0f172a";

      React.useEffect(() => {
        document.documentElement.classList.remove("light", "dark");
        document.documentElement.classList.add(isDark ? "dark" : "light");
      }, [isDark]);

      return (
        <ThemeProvider defaultTheme={isDark ? "dark" : "light"}>
          <ToastProvider>
            <div className="p-6">
              <Story />
            </div>
          </ToastProvider>
        </ThemeProvider>
      );
    },
  ],
  globalTypes: {
    theme: {
      description: "Global theme for components",
      defaultValue: "light",
      toolbar: {
        title: "Theme",
        icon: "circlehollow",
        items: ["light", "dark"],
        dynamicTitle: true,
      },
    },
  },
};

export default preview;

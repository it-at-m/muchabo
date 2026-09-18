import { fileURLToPath } from "node:url";

import { defineConfig, mergeConfig } from "vitest/config";

import viteConfig from "./vite.config.ts";

export default defineConfig(
  mergeConfig(
    viteConfig,
    defineConfig({
      test: {
        environment: "jsdom",
        passWithNoTests: true,
        root: fileURLToPath(new URL("./", import.meta.url)),
        server: {
          deps: {
            inline: ["vuetify"],
          },
        },
      },
    })
  )
);

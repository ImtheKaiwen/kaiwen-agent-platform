import { defineConfig } from "tsup";

export default defineConfig({
  entry: {
    index: "src/index.ts",
    "react/index": "src/react/index.ts",
  },
  format: ["esm"],
  dts: true,
  clean: true,
  external: ["react", "react/jsx-runtime"],
  noExternal: ["@kaiwen/agent-protocol"],
});

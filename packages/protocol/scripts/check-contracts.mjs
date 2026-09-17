import { readFile } from "node:fs/promises";

const files = [
  "schemas/event-envelope.schema.json",
  "schemas/artifact.schema.json",
  "schemas/client-action.schema.json",
];

for (const file of files) {
  const schema = JSON.parse(await readFile(new URL(`../${file}`, import.meta.url), "utf8"));
  if (schema.$schema !== "https://json-schema.org/draft/2020-12/schema") {
    throw new Error(`${file} must use JSON Schema Draft 2020-12`);
  }
  if (schema.type !== "object" || schema.additionalProperties !== false) {
    throw new Error(`${file} must be a closed object schema`);
  }
}

console.log(`Validated ${files.length} canonical schemas.`);


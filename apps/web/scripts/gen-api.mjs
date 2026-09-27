import { readFile, writeFile } from "node:fs/promises";
import openapiTS, { astToString } from "openapi-typescript";
import { schemas, responses } from "./response-schemas.mjs";

const root = new URL("../src/lib/api/", import.meta.url);
const document = JSON.parse(await readFile(new URL("openapi.json", root), "utf8"));
Object.assign(document.components.schemas, schemas);
for (const [operation, schema] of Object.entries(responses)) {
  const [method, path] = operation.split(" ");
  const route = document.paths[path]?.[method.toLowerCase()];
  if (!route) throw new Error(`Missing API operation: ${operation}`);
  for (const [status, response] of Object.entries(route.responses)) {
    if (status.startsWith("2")) response.content["application/json"].schema = schema;
  }
}
await writeFile(new URL("schema.d.ts", root), astToString(await openapiTS(document)));

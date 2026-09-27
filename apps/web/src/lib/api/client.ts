import createClient from "openapi-fetch";
import type { components, paths } from "./schema";

type ErrorBody = components["schemas"]["ApiErrorBody"]["error"];
// Middleware supplies required headers; callers still get generated path/body types.
type AutomaticHeaders<T> = T extends { parameters: infer P }
  ? Omit<T, "parameters"> & { parameters: P extends { header: infer H }
    ? Omit<P, "header"> & { header?: Partial<H> } : P } : T;
type ClientPaths = { [P in keyof paths]: { [M in keyof paths[P]]: AutomaticHeaders<paths[P][M]> } };
export class ApiError extends Error {
  constructor(public readonly status: number, public readonly code: string, message: string,
    public readonly details: ErrorBody["details"] = {}) {
    super(message);
    this.name = "ApiError";
  }
  get retryable() { return this.status === 0 || this.status >= 500; }
}

export function parseApiError(status: number, body: unknown): ApiError {
  if (body && typeof body === "object" && "error" in body) {
    const error = body.error;
    if (error && typeof error === "object" && "code" in error && "message" in error &&
      typeof error.code === "string" && typeof error.message === "string") {
      const details = "details" in error && error.details && typeof error.details === "object"
        ? error.details as Record<string, unknown> : {};
      return new ApiError(status, error.code, error.message, details);
    }
  }
  return new ApiError(status, status === 422 ? "validation_error" : "http_error",
    status === 401 ? "ログインの有効期限が切れました。" : "通信がうまくいきませんでした。もう一度お試しください。");
}

export const TOKEN_KEY = "tsuyulabo.guest-token";
type StorageAccess = () => Pick<Storage, "getItem" | "setItem"> | undefined;
const browserStorage: StorageAccess = () => {
  try { return typeof window === "undefined" ? undefined : window.localStorage; }
  catch { return undefined; }
};

export function createApi(options: { baseUrl?: string; fetch?: typeof fetch; storage?: StorageAccess; retries?: number } = {}) {
  const baseUrl = options.baseUrl ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const storage = options.storage ?? browserStorage;
  let token: string | undefined;
  let bootstrap: Promise<string> | undefined;
  let guestKey: string | undefined;

  async function transport(request: Request): Promise<Response> {
    for (let attempt = 0; ; attempt++) {
      try {
        const response = await (options.fetch ?? globalThis.fetch)(new Request(request.clone(), {
          signal: AbortSignal.any([request.signal, AbortSignal.timeout(12_000)]),
        }));
        if (response.status >= 500 && attempt < (options.retries ?? 1)) continue;
        if (!response.ok) {
          const body: unknown = await response.clone().json().catch(() => null);
          throw parseApiError(response.status, body);
        }
        return response;
      } catch (error) {
        if (error instanceof ApiError) throw error;
        if (request.signal.aborted) throw error;
        if (attempt < (options.retries ?? 1)) continue;
        throw new ApiError(0, "offline", "研究所につながりません。接続を確認して、もう一度お試しください。");
      }
    }
  }

  async function getToken(): Promise<string> {
    // No guest creation or shared identity while prerendering on the server.
    if (!options.storage && typeof window === "undefined") throw new ApiError(0, "client_only", "ブラウザーで開いてください。");
    if (token) return token;
    try { token = storage()?.getItem(TOKEN_KEY) || undefined; } catch { /* Memory fallback. */ }
    if (token) return token;
    if (!bootstrap) {
      guestKey ??= crypto.randomUUID();
      bootstrap = (async () => {
        const response = await transport(new Request(`${baseUrl.replace(/\/$/, "")}/v1/auth/guest`, {
          method: "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": guestKey! },
          body: JSON.stringify({ display_name: "研究員" }),
        }));
        const data: unknown = await response.json();
        if (!data || typeof data !== "object" || !("token" in data) || typeof data.token !== "string" || !data.token) {
          throw new ApiError(502, "invalid_response", "ログイン情報を読み取れませんでした。");
        }
        token = data.token;
        try { storage()?.setItem(TOKEN_KEY, token); } catch { /* Private mode can deny storage. */ }
        return token;
      })().finally(() => { bootstrap = undefined; });
    }
    return bootstrap;
  }

  const client = createClient<ClientPaths>({ baseUrl, fetch: transport });
  client.use({
    async onRequest({ request }) {
      request.headers.set("Authorization", `Bearer ${await getToken()}`);
      if (!["GET", "HEAD"].includes(request.method) && !request.headers.has("Idempotency-Key")) {
        request.headers.set("Idempotency-Key", crypto.randomUUID());
      }
      return request;
    },
  });
  return { client, getToken };
}

export function createAction<T>(run: (headers: Record<string, string>) => Promise<T>) {
  const key = crypto.randomUUID();
  return { key, run: () => run({ "Idempotency-Key": key }) };
}

export async function unwrap<T>(request: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T> {
  const result = await request;
  if (!result.response.ok) throw parseApiError(result.response.status, result.error);
  if (result.data === undefined) throw new ApiError(502, "invalid_response", "研究所からのデータを読み取れませんでした。");
  return result.data;
}

export const { client: api } = createApi();

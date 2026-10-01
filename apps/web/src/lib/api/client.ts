import createClient from "openapi-fetch";
import type { components, paths } from "./schema";

type ErrorBody = components["schemas"]["ApiErrorBody"]["error"];
// Middleware supplies required headers; callers still get generated path/body types.
type AutomaticHeaders<T> = T extends { parameters: infer P }
  ? Omit<T, "parameters"> & { parameters: P extends { header: infer H }
    ? Omit<P, "header"> & { header?: Partial<H> } : P } : T;
type ClientPaths = { [P in keyof paths]: { [M in keyof paths[P]]: AutomaticHeaders<paths[P][M]> } };
export class ApiError extends Error {
  readonly retryAt: number;
  constructor(public readonly status: number, public readonly code: string, message: string,
    public readonly details: ErrorBody["details"] = {}, public readonly retryAfter = 0) {
    super(code === "rate_limited" || code === "server_busy"
      ? "少し時間をおいてから、もう一度ためしてね。" : message);
    this.name = "ApiError";
    this.retryAt = Date.now() + retryAfter * 1000;
  }
  get overloaded() { return this.status === 429 || ["rate_limited", "server_busy"].includes(this.code); }
  get retryable() { return !this.overloaded && !this.retryAfter && (this.status === 0 || this.status >= 500); }
}

export function parseApiError(status: number, body: unknown, retryHeader: string | null = null): ApiError {
  const seconds = retryHeader === null ? 0 : /^\d+$/.test(retryHeader)
    ? Number(retryHeader) : Math.ceil((Date.parse(retryHeader) - Date.now()) / 1000);
  const headerWait = Number.isFinite(seconds) && seconds > 0 ? seconds : 0;
  if (body && typeof body === "object" && "error" in body) {
    const error = body.error;
    if (error && typeof error === "object" && "code" in error && "message" in error &&
      typeof error.code === "string" && typeof error.message === "string") {
      const details = "details" in error && error.details && typeof error.details === "object"
        ? error.details as Record<string, unknown> : {};
      const detailWait = typeof details.retry_after === "number" && Number.isFinite(details.retry_after)
        ? Math.max(0, Math.ceil(details.retry_after)) : 0;
      const defaultWait = ["rate_limited", "server_busy"].includes(error.code) ? 10 : status === 429 ? 60 : 0;
      return new ApiError(status, error.code, error.message, details, Math.max(headerWait, detailWait) || defaultWait);
    }
  }
  return new ApiError(status, status === 422 ? "validation_error" : "http_error",
    status === 401 ? "ログインの有効期限が切れました。" : "通信がうまくいきませんでした。もう一度お試しください。",
    {}, headerWait || (status === 429 ? 60 : 0));
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
  const cooldowns = new Map<string, ApiError>();

  async function transport(request: Request): Promise<Response> {
    const scope = `${request.method} ${new URL(request.url).pathname}`;
    for (const [key, error] of cooldowns) if (error.retryAt <= Date.now()) cooldowns.delete(key);
    const cooling = cooldowns.get(scope);
    if (cooling) throw cooling;
    for (let attempt = 0; ; attempt++) {
      try {
        const response = await (options.fetch ?? globalThis.fetch)(new Request(request.clone(), {
          signal: AbortSignal.any([request.signal, AbortSignal.timeout(12_000)]),
        }));
        if (!response.ok) {
          const body: unknown = await response.clone().json().catch(() => null);
          const error = parseApiError(response.status, body, response.headers.get("Retry-After"));
          if (error.retryAfter > 0) cooldowns.set(scope, error);
          if (response.status >= 500 && error.retryable && attempt < (options.retries ?? 1)) continue;
          throw error;
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
  if (!result.response.ok) throw parseApiError(result.response.status, result.error, result.response.headers.get("Retry-After"));
  if (result.data === undefined) throw new ApiError(502, "invalid_response", "研究所からのデータを読み取れませんでした。");
  return result.data;
}

export const { client: api } = createApi();

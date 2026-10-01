// Same-origin API proxy for the self-hosted backend (docs/selfhost.md).
// Browsers on the owner's tailnet resolve the API host to a private Tailscale address, and Chrome's
// Local Network Access blocks a public site from calling it; proxying through the web origin avoids
// both that and CORS. TSUYU_API_PROXY_TARGET is read at build time and never sent to the browser.
export type Rewrite = { source: string; destination: string };

export function apiRewrites(target: string | undefined): Rewrite[] {
  const origin = target?.trim().replace(/\/+$/, "");
  if (!origin) return [];
  const url = new URL(origin);
  if (url.protocol !== "https:" || url.pathname !== "/" || url.search || url.hash) {
    throw new Error("TSUYU_API_PROXY_TARGET must be an https origin without a path");
  }
  return [
    { source: "/v1/:path*", destination: `${origin}/v1/:path*` },
    { source: "/healthz", destination: `${origin}/healthz` },
  ];
}

/* The cache contains only the public offline shell, never API or account data. */
const CACHE = "tsuyu-offline-v1";
const OFFLINE = "/offline.html";
const DESTINATIONS = new Set(["/", "/care/meal", "/presentation", "/friends"]);

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.add(OFFLINE)));
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    for (const name of await caches.keys()) {
      if (name.startsWith("tsuyu-offline-") && name !== CACHE) await caches.delete(name);
    }
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET" || request.mode !== "navigate" ||
    new URL(request.url).origin !== self.location.origin) return;
  event.respondWith(fetch(request).catch(async () => {
    const cache = await caches.open(CACHE);
    return await cache.match(OFFLINE) || Response.error();
  }));
});

function destination(value) {
  return typeof value === "string" && DESTINATIONS.has(value) ? value : "/";
}

self.addEventListener("push", (event) => {
  let payload = {};
  try { payload = event.data?.json() || {}; } catch { /* Show a safe default for empty pushes. */ }
  event.waitUntil(self.registration.showNotification(
    typeof payload.title === "string" ? payload.title : "ツユラボからのお知らせ",
    {
      body: typeof payload.body === "string" ? payload.body : "研究室をのぞいてみよう。",
      icon: "/icon.svg",
      tag: typeof payload.tag === "string" ? payload.tag : "tsuyu",
      data: { url: destination(payload.url) },
    },
  ));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = new URL(destination(event.notification.data?.url), self.location.origin).href;
  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const client of windows) {
      if (new URL(client.url).origin === self.location.origin && "navigate" in client) {
        const navigated = await client.navigate(url);
        if (navigated) return navigated.focus();
      }
    }
    return self.clients.openWindow(url);
  })());
});

export function pushSupported(): boolean {
  return typeof window !== "undefined" && window.isSecureContext &&
    "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
}

export function applicationServerKey(value: string): Uint8Array<ArrayBuffer> {
  const raw = atob(value.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - value.length % 4) % 4));
  return Uint8Array.from(raw, (character) => character.charCodeAt(0));
}

export async function registerServiceWorker(): Promise<ServiceWorkerRegistration> {
  await navigator.serviceWorker.register("/sw.js", { scope: "/", updateViaCache: "none" });
  return navigator.serviceWorker.ready;
}

export async function enablePush(publicKey: string): Promise<PushSubscription> {
  // This must be the first await in the button handler, preserving user activation on Safari.
  const permission = await Notification.requestPermission();
  if (permission !== "granted") throw new Error("通知が許可されていません。ブラウザーの設定から変更できます。");
  const registration = await registerServiceWorker();
  return await registration.pushManager.getSubscription() || registration.pushManager.subscribe({
    userVisibleOnly: true, applicationServerKey: applicationServerKey(publicKey),
  });
}

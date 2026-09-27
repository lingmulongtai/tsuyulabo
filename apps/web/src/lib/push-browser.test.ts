import { afterEach, describe, expect, it, vi } from "vitest";
import { applicationServerKey, enablePush, pushSupported, registerServiceWorker } from "./push-browser";

afterEach(() => vi.unstubAllGlobals());

describe("browser push", () => {
  it("decodes base64url keys", () => {
    expect([...applicationServerKey("-_8")]).toEqual([251, 255]);
  });

  it("registers without asking permission", async () => {
    const requestPermission = vi.fn();
    const register = vi.fn().mockResolvedValue({});
    vi.stubGlobal("Notification", { requestPermission });
    vi.stubGlobal("navigator", { serviceWorker: { register, ready: Promise.resolve({}) } });
    await registerServiceWorker();
    expect(register).toHaveBeenCalledWith("/sw.js", { scope: "/", updateViaCache: "none" });
    expect(requestPermission).not.toHaveBeenCalled();
  });

  it("does not subscribe after denied permission", async () => {
    const register = vi.fn();
    vi.stubGlobal("Notification", { requestPermission: vi.fn().mockResolvedValue("denied") });
    vi.stubGlobal("navigator", { serviceWorker: { register } });
    await expect(enablePush("-_8")).rejects.toThrow("通知が許可されていません");
    expect(register).not.toHaveBeenCalled();
  });

  it("requests permission before asynchronous registration and reuses subscriptions", async () => {
    const subscription = { endpoint: "existing" };
    const requestPermission = vi.fn().mockResolvedValue("granted");
    const subscribe = vi.fn();
    const register = vi.fn().mockResolvedValue({});
    vi.stubGlobal("Notification", { requestPermission });
    vi.stubGlobal("navigator", { serviceWorker: { register, ready: Promise.resolve({
      pushManager: { getSubscription: vi.fn().mockResolvedValue(subscription), subscribe },
    }) } });
    expect(await enablePush("-_8")).toBe(subscription);
    expect(requestPermission.mock.invocationCallOrder[0]).toBeLessThan(register.mock.invocationCallOrder[0]);
    expect(subscribe).not.toHaveBeenCalled();
  });

  it("disables unsupported or insecure browsers", () => {
    vi.stubGlobal("window", { isSecureContext: false });
    expect(pushSupported()).toBe(false);
  });
});

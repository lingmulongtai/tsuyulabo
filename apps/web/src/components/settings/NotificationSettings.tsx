"use client";
import { useEffect, useState } from "react";
import { api, unwrap } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { enablePush, pushSupported, registerServiceWorker } from "@/lib/push-browser";
import { Button, Card } from "@/components/ui/primitives";

type Preferences = Required<components["schemas"]["PushPreferences"]>;
const DEFAULTS: Preferences = {
  meal_slots: ["morning", "noon", "night"], eclosion_night: true, friend_activity: true,
  quiet_start: "23:00", quiet_end: "07:00",
};
const SLOTS = [["morning", "朝のごはん（04:00）"], ["noon", "昼のごはん（12:00）"], ["night", "夜のごはん（18:00）"]] as const;

async function saveSubscription(subscription: PushSubscription) {
  const json = subscription.toJSON();
  if (!json.endpoint || !json.keys?.p256dh || !json.keys.auth) throw new Error("通知の登録情報を読み取れませんでした。");
  return unwrap(api.POST("/v1/push/subscribe", { body: {
    endpoint: json.endpoint, keys: { p256dh: json.keys.p256dh, auth: json.keys.auth },
    expirationTime: json.expirationTime,
  } }));
}

export function NotificationSettings() {
  const [preferences, setPreferences] = useState<Preferences>(DEFAULTS);
  const [publicKey, setPublicKey] = useState<string | null>(null);
  const [subscription, setSubscription] = useState<PushSubscription | null>(null);
  const [supported, setSupported] = useState(false);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const supported = pushSupported();
      const [prefs, key] = await Promise.all([
        unwrap(api.GET("/v1/push/preferences")), unwrap(api.GET("/v1/push/public-key")),
      ]);
      const registration = supported ? await registerServiceWorker() : null;
      const existing = await registration?.pushManager.getSubscription() ?? null;
      // Recover a subscription removed by a transient provider failure or database restore.
      if (existing && key.public_key && Notification.permission === "granted") await saveSubscription(existing);
      if (!cancelled) {
        setPreferences({ ...DEFAULTS, ...prefs }); setPublicKey(key.public_key);
        setSubscription(existing); setSupported(supported); setReady(true); setError("");
      }
    }
    void load().catch((cause: unknown) => {
      if (!cancelled) setError(cause instanceof Error ? cause.message : "設定を読み込めませんでした。");
    });
    return () => { cancelled = true; };
  }, [reload]);

  async function action(run: () => Promise<void>) {
    setBusy(true); setError(""); setMessage("");
    try { await run(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "通信を確認して、もう一度お試しください。"); }
    finally { setBusy(false); }
  }

  function enable() {
    if (!publicKey) return;
    void action(async () => {
      const created = await enablePush(publicKey);
      try { await saveSubscription(created); }
      catch (cause) { if (!subscription) await created.unsubscribe(); throw cause; }
      setSubscription(created); setMessage("この端末への通知を有効にしました。");
    });
  }

  function disable() {
    if (!subscription) return;
    void action(async () => {
      // Keep the endpoint available for retry if the API is offline.
      await unwrap(api.DELETE("/v1/push/subscribe", { body: { endpoint: subscription.endpoint } }));
      await subscription.unsubscribe(); setSubscription(null);
      setMessage("この端末への通知を停止しました。");
    });
  }

  return <Card className="space-y-5 p-5">
    <div><h2 className="font-kiwi text-xl">研究室からのお知らせ</h2>
      <p className="mt-2 text-sm text-muted">ごはんの時間や羽化の夜を、そっとお知らせします。</p></div>
    {!ready && !error && <p role="status">設定を読み込み中…</p>}
    {error && <p role="alert" className="text-sm text-eye">{error}</p>}
    {!ready && error && <Button tone="plain" onClick={() => setReload(value => value + 1)}>もう一度読み込む</Button>}
    {ready && <>
      {!supported && <p className="text-sm text-muted">このブラウザーでは通知を使えません。iPhone・iPadでは「ホーム画面に追加」したアプリから開いてね。</p>}
      {!publicKey && <p className="text-sm text-muted">通知サービスはただいま準備中です。</p>}
      <p className="text-sm font-bold">この端末の通知：{subscription ? "有効" : "停止中"}</p>
      <Button block tone={subscription ? "plain" : "leaf"} disabled={busy || (!subscription && (!supported || !publicKey))} onClick={subscription ? disable : enable}>
        {subscription ? "この端末の通知を止める" : "この端末で通知を受け取る"}
      </Button>
      <p className="text-xs text-muted">通知の許可は上のボタンを押したときに確認します。端末の通知設定もオンにしてね。</p>
      <form onSubmit={event => { event.preventDefault(); void action(async () => {
        const saved = await unwrap(api.PUT("/v1/push/preferences", { body: preferences }));
        setPreferences({ ...DEFAULTS, ...saved }); setMessage("お知らせの設定を保存しました。");
      }); }}>
        <fieldset disabled={busy} className="space-y-4">
          <legend className="mb-3 font-bold">受け取るお知らせ（すべての端末）</legend>
          {SLOTS.map(([slot, label]) => <label key={slot} className="flex items-center gap-3 text-sm">
            <input type="checkbox" className="h-5 w-5 accent-leaf" checked={preferences.meal_slots.includes(slot)} onChange={event => setPreferences({ ...preferences, meal_slots: event.target.checked ? [...preferences.meal_slots, slot] : preferences.meal_slots.filter(value => value !== slot) })} />{label}
          </label>)}
          {([["eclosion_night", "羽化の夜"], ["friend_activity", "フレンドの活動"]] as const).map(([key, label]) => <label key={key} className="flex items-center gap-3 text-sm">
            <input type="checkbox" className="h-5 w-5 accent-leaf" checked={preferences[key]} onChange={event => setPreferences({ ...preferences, [key]: event.target.checked })} />{label}
          </label>)}
          <div className="rounded-2xl bg-tint-leaf p-4">
            <p className="mb-3 text-sm font-bold">おやすみ時間（日本時間）</p>
            <div className="flex flex-wrap items-center gap-3">
              <label className="text-sm">開始<input required aria-label="おやすみ時間の開始" type="time" value={preferences.quiet_start} onChange={event => setPreferences({ ...preferences, quiet_start: event.target.value })} className="mt-1 block rounded-lg border border-line bg-surface p-2" /></label>
              <span aria-hidden>〜</span>
              <label className="text-sm">終了<input required aria-label="おやすみ時間の終了" type="time" value={preferences.quiet_end} onChange={event => setPreferences({ ...preferences, quiet_end: event.target.value })} className="mt-1 block rounded-lg border border-line bg-surface p-2" /></label>
            </div>
            <p className="mt-3 text-xs text-muted">この時間は通知を送りません。初期設定では朝04:00の通知もお休みします。同じ時刻にすると、おやすみ時間はなくなります。</p>
          </div>
          <Button type="submit" block tone="leaf">設定を保存する</Button>
        </fieldset>
      </form>
    </>}
    <p role="status" aria-live="polite" className="text-sm text-leaf">{busy ? "設定を更新中…" : message}</p>
  </Card>;
}

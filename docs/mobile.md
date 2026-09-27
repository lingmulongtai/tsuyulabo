# モバイル版（アルファ）

Android アプリは `apps/mobile/` の Capacitor 8 プロジェクトです。パッケージ ID は `app.tsuyulabo.alpha`、表示名は「ツユラボ α」です。WebView は既定で `https://tsuyulabo.vercel.app` を読み込みます。`TSUYU_APP_URL` 環境変数に HTTPS の URL を設定すると、`cap sync` 時に接続先を変更できます。これは APK に組み込まれる設定なので、変更後は APK を作り直してください。

`server.url` は Capacitor が主にライブリロード用に提供している機能です。このアルファ版では公開デモを表示するために使用しています。将来の本番配布では、Web アセットの同梱方式を見直します。接続エラー時は `apps/mobile/www/offline.html` が表示され、再試行ボタンは既定のデモサイトへ移動します。

## Android デバッグ APK

GitHub Actions の `Android alpha` を手動実行すると、Node 22 と JDK 17 を使って `npm ci`、`npx cap sync android`、`./gradlew assembleDebug` を実行し、APK をワークフローの artifact に保存します。CI の実行番号を Android の `versionCode` に、タグ名を `versionName` に使います。`v*-alpha*` タグでは、同じ APK を GitHub の prerelease に添付し、`docs/releases/<tag>.md` をリリースノートに使用します。タグに対応するノートを先に追加し、タグは別途作成してください。

ローカルに Android SDK がある場合の手順:

```sh
npm ci
cd apps/mobile
npx cap sync android
cd android
./gradlew assembleDebug
```

出力は `apps/mobile/android/app/build/outputs/apk/debug/app-debug.apk` です。デバッグ APK は Android のデバッグ鍵で署名されます。正式署名版への上書き更新はできない場合があります。

## 正式署名版を用意するとき

現時点では正式署名や配布の自動化は未実装です。所有者が鍵を作成し、安全な場所にバックアップしてから、次の手順で追加します。

1. Android SDK と JDK を用意し、`keytool -genkeypair -v -keystore tsuyulabo-release.jks -alias tsuyulabo -keyalg RSA -keysize 3072 -validity 10000` で鍵を作ります。鍵とパスワードはリポジトリに入れません。
2. GitHub Actions の Secrets に、鍵を Base64 化した `ANDROID_KEYSTORE_BASE64`、`ANDROID_KEYSTORE_PASSWORD`、`ANDROID_KEY_ALIAS`、`ANDROID_KEY_PASSWORD` を登録します。鍵の原本とパスワードは別の安全な場所にも保管します。
3. `apps/mobile/android/app/build.gradle` に release の `signingConfigs` を追加し、環境変数からパスワードとエイリアスを読みます。CI では秘密鍵を一時ファイルに復元してビルド後に削除します。シークレットがない実行では署名タスクを開始しないようにします。
4. 署名設定を検証したら `./gradlew assembleRelease` で APK、または `./gradlew bundleRelease` で Play Store 向け AAB を作成します。出力に `apksigner verify` を実行してから配布します。

鍵を失うと同じアプリ ID で更新できなくなるため、鍵のバックアップを保持してください。

## iOS の経路

iOS ビルドには macOS、Xcode、Apple Developer アカウントが必要です。Mac で依存関係をインストールして `npm install @capacitor/ios -w apps/mobile`、`cd apps/mobile && npx cap add ios && npx cap sync ios` を実行します。Xcode で Bundle ID と署名チームを設定し、実機で動作確認した後、Archive を App Store Connect にアップロードして TestFlight で配布します。現時点で iOS プロジェクトや CI ビルドはありません。

# RinPlugins

RinのFFXIV Dalamudプラグインをまとめて配布するリポジトリです。

## 導入

Dalamud設定の試験的機能から、Custom Plugin Repositoriesに次のURLを追加してください。

```text
https://raw.githubusercontent.com/Rin-0617/RinPlugins/main/pluginmaster.json
```

追加したあとは、プラグインインストーラーから各プラグインを導入できます。

## 収録プラグイン

| プラグイン | 内容 |
|---|---|
| [PartySieve](https://github.com/Rin-0617/PartySieve) | パーティ募集のスパム除去、高機能フィルター、募集主のDC表示 |
| [RaidFlow](https://github.com/Rin-0617/Raidflow) | 固定攻略向けのタイムラインメモ、軽減計画 |
| [BeastHelper](https://github.com/Rin-0617/BeastHelper) | ビーストマスターの仲間候補への移動補助 |

## 仕組み

1. 各プラグインのリポジトリで `v*` のタグをpushすると、そのリポジトリのGitHub Actionsがビルドし、GitHub Releaseにzipを置きます。
2. このリポジトリのGitHub Actionsが30分ごとに、`plugins.json` に並べたリポジトリの最新リリースを確認します。
3. zipの中のマニフェストから `pluginmaster.json` を作り直し、変更があればコミットします。

すぐに反映したいときは、Actionsの「Update pluginmaster」から手動で実行できます。

### プラグインを追加する

`plugins.json` にリポジトリを追加します。

```json
{
  "repo": "Rin-0617/NewPlugin",
  "overrides": {
    "Tags": ["tag1", "tag2"]
  }
}
```

`overrides` に書いた項目は、zipの中のマニフェストより優先されます。

### テスト版

GitHub Releaseで「Set as a pre-release」にしたリリースは、テスト版として配布されます。
Dalamudでテスト版を受け取る設定にしている人だけに届きます。

## 作者

Rin

## 開発の支援

```text
https://ofuse.me/rin0617
```

# Color Tetris (Python + venv)

`pygame` で作った、色付きブロックのテトリスです。

## 1. Python バージョン管理

- `.python-version` に `3.12` を指定しています。
- `direnv` は任意です。未導入でも手動 `venv` で動かせます。

## 2. セットアップ

`direnv` なし（推奨の最短手順）:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python tetris.py
```

`direnv` あり（任意）:

```bash
direnv allow
python -m pip install -r requirements.txt
python tetris.py
```

## 3. 操作

- `←` / `→`: 移動
- `↑`: 回転
- `↓`: ソフトドロップ
- `Space`: ハードドロップ
- `P`: 一時停止
- `R`: リスタート
- `Esc`: 終了

## 4. GitHub へ push

```bash
git init
git add .
git commit -m "Add color tetris with venv + direnv setup"
git branch -M main
git remote add origin git@github.com:<your-user>/<your-repo>.git
git push -u origin main
```

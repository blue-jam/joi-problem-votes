# joi-problem-votes

日本情報オリンピック（JOI）の印象に残っている問題の投票結果を集計・表示する静的サイト（Jekyll ベース）です。

## 概要

`votes/` ディレクトリに配置された投票データ（CSV）を Python スクリプトで JSON に変換・集計し、Jekyll で静的ページとしてレンダリングします。GitHub Pages でホストされることを想定しています。

## 必要な環境

- Ruby
- Bundler (`gem install bundler`)
- Python 3.x (投票データの集計スクリプト実行用)

## ローカルでのセットアップと実行方法

1. **依存関係のインストール**
   ```sh
   bundle install
   ```

2. **データの集計**
   投票データの CSV ファイル（例: `votes/2026-04.csv`）を基に、表示用の JSON データを生成します。
   ```sh
   python3 generate.py
   ```
   これにより、`_data/votes/` フォルダ内に集計済みの JSON ファイルが生成されます。

3. **ローカルサーバーの起動**
   ```sh
   bundle exec jekyll serve
   ```
   ブラウザで `http://localhost:4000/joi-problem-votes/` にアクセスしてサイトのプレビューを確認できます。

## ディレクトリ構成

- `_config.yml`: Jekyll のサイト設定ファイル
- `generate.py`: CSV から投票結果を集計し、JSON を生成するスクリプト
- `votes/`: 投票結果の生データ（CSV ファイル）を配置するディレクトリ
- `_data/votes/`: 生成された JSON ファイルが配置されるディレクトリ
- `index.md`: サイトのトップページ
- `pages/`: 各回の投票結果を表示する Markdown ページ
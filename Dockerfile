# Render のネイティブPythonランタイムが3.14に対応しているか確証が持てなかったため、
# uv公式イメージで直接Pythonバージョンを固定するDockerビルドに切り替えている。
# ローカルの .python-version / pyproject.toml と同じ 3.14 系を明示的に指定する。
FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

WORKDIR /app

# 依存関係だけ先にコピーしてキャッシュを効かせる
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Renderは PORT 環境変数でリッスンすべきポートを渡してくる（ローカル実行時は8000にフォールバック）
CMD ["sh", "-c", "uv run uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

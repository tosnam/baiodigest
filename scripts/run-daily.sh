#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/Users/seong-hyeuknam/Dev/baiodigest"
UV="/Users/seong-hyeuknam/.local/bin/uv"
LOG_DIR="$PROJECT_DIR/logs"

cd "$PROJECT_DIR"

echo "=== BioDigest daily run: $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG_DIR/daily.log"

# Ollama 실행 확인 — 미실행 시 백그라운드 시작
if ! curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "[INFO] Starting Ollama..." >> "$LOG_DIR/daily.log"
    /opt/homebrew/bin/ollama serve > "$LOG_DIR/ollama.log" 2>&1 &
    OLLAMA_PID=$!
    # 최대 30초 대기
    for i in $(seq 1 30); do
        sleep 1
        if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "[INFO] Ollama ready after ${i}s" >> "$LOG_DIR/daily.log"
            break
        fi
    done
fi

# 파이프라인 실행
echo "[INFO] Running pipeline..." >> "$LOG_DIR/daily.log"
"$UV" run python -m baiodigest.main >> "$LOG_DIR/daily.log" 2>&1

# git add + commit + push
echo "[INFO] Pushing to GitHub..." >> "$LOG_DIR/daily.log"
git -C "$PROJECT_DIR" add data/ docs/ >> "$LOG_DIR/daily.log" 2>&1

if git -C "$PROJECT_DIR" diff --cached --quiet; then
    echo "[INFO] No changes to commit." >> "$LOG_DIR/daily.log"
else
    TODAY=$(date '+%Y-%m-%d')
    git -C "$PROJECT_DIR" commit -m "digest: $TODAY" >> "$LOG_DIR/daily.log" 2>&1
    git -C "$PROJECT_DIR" push origin main >> "$LOG_DIR/daily.log" 2>&1
    echo "[INFO] Pushed successfully." >> "$LOG_DIR/daily.log"
fi

echo "=== Done: $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG_DIR/daily.log"

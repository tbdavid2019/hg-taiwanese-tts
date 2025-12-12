title: Taiwanese Tts
emoji: 👁
colorFrom: gray
colorTo: gray
sdk: gradio
sdk_version: 6.1.0
app_file: app.py
pinned: false
short_description: 台語TTS
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference


---
## 專案說明
這是一個台語文字轉語音介面，使用 Gradio 建立。介面會呼叫外部 TTS API（`https://learn-language.tokyo/taigiTTS/taigi-text-to-speech`），將使用者輸入的台語文字轉成語音並播放，同時保留最近 50 筆歷史紀錄（儲存在 `data/history.json`）。在 Hugging Face Spaces 可設定持久儲存以保存歷史。

## 快速開始
1) 安裝套件：
```
pip install -r requirements.txt
```
2) 啟動介面：
```
python3 app.py
```
開啟終端顯示的網址（預設 7860）操作。

## 使用方式
- 輸入台語文字並選擇模型（目前預設 `model6`），點擊「產生語音」。
- 轉換後可直接播放音檔；同時會顯示 API 回傳的狀態訊息、白話字（Tailo）與 IPA。
- 下方歷史區域可重播任一紀錄或重新載入最新紀錄。最多保留 50 筆，超出會自動覆蓋最舊項目。

## 注意事項
- 介面直接呼叫外部 API，若 API 502/429 等錯誤會在 UI 顯示友善訊息，不會造成程式崩潰。
- `data/history.json` 為本地紀錄檔，可視需要刪除或加入持久化設定。

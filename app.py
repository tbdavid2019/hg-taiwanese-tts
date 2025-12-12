import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Tuple

import gradio as gr
import requests

API_URL = "https://learn-language.tokyo/taigiTTS/taigi-text-to-speech"
API_HEADERS = {
    "content-type": "application/json",
    "origin": "https://learn-language.tokyo",
}

HISTORY_PATH = Path("data/history.json")
MAX_HISTORY = 50


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_history() -> List[Dict]:
    if HISTORY_PATH.exists():
        try:
            return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_history(entries: List[Dict]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def _format_preview(text: str, limit: int = 48) -> str:
    preview = " ".join(text.split())
    if len(preview) > limit:
        return preview[: limit - 3] + "..."
    return preview


def _history_options(entries: List[Dict]) -> List[str]:
    options = []
    for idx, entry in enumerate(entries):
        label = f"{idx}|{entry.get('time', '')} · {entry.get('model', '')} · {_format_preview(entry.get('text', ''))}"
        options.append(label)
    return options


def _history_table(entries: List[Dict]) -> List[Dict]:
    table = []
    for entry in entries:
        table.append(
            {
                "Time (UTC)": entry.get("time", ""),
                "Model": entry.get("model", ""),
                "Text": _format_preview(entry.get("text", "")),
                "Audio URL": entry.get("audio_url", ""),
            }
        )
    return table


def fetch_tts(text: str, model: str) -> Tuple[str, Dict]:
    payload = {"text": text, "model": model}
    try:
        response = requests.post(API_URL, json=payload, headers=API_HEADERS, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "N/A"
        detail = exc.response.text[:300] if exc.response is not None else str(exc)
        raise gr.Error(f"TTS API 呼叫失敗 (HTTP {status}): {detail}")
    except requests.RequestException as exc:
        raise gr.Error(f"TTS API 連線失敗：{exc}")
    except ValueError:
        raise gr.Error("TTS API 回傳非 JSON 內容。")

    audio_url = data.get("converted_audio_url") or data.get("audio_url")
    if not audio_url:
        raise gr.Error("TTS API 回傳內容缺少音檔網址 (audio_url)。")
    return audio_url, data


def handle_tts(text: str, model: str):
    text = text.strip()
    if not text:
        raise gr.Error("請輸入要轉成語音的文字。")

    audio_url, data = fetch_tts(text, model)

    new_entry = {
        "text": text,
        "model": model,
        "audio_url": audio_url,
        "message": data.get("message", ""),
        "tailuo": data.get("tailuo", ""),
        "ipa": data.get("ipa", ""),
        "time": _now_iso(),
    }

    history = _load_history()
    history = [new_entry] + history[: MAX_HISTORY - 1]
    _save_history(history)

    options = _history_options(history)
    table = _history_table(history)

    return (
        audio_url,
        data.get("message", "完成"),
        data.get("tailuo", ""),
        data.get("ipa", ""),
        gr.update(choices=options, value=options[0] if options else None),
        table,
    )


def load_history_item(selection: str):
    if not selection:
        return None, gr.update(), gr.update(), gr.update(), gr.update(value=None), _history_table(_load_history())

    idx_str = selection.split("|", 1)[0]
    try:
        idx = int(idx_str)
    except ValueError:
        return None, gr.update(), gr.update(), gr.update(), gr.update(value=None), _history_table(_load_history())

    history = _load_history()
    if idx < 0 or idx >= len(history):
        return None, gr.update(), gr.update(), gr.update(), gr.update(value=None), _history_table(history)

    entry = history[idx]
    options = _history_options(history)
    table = _history_table(history)

    return (
        entry.get("audio_url"),
        entry.get("message", ""),
        entry.get("tailuo", ""),
        entry.get("ipa", ""),
        gr.update(choices=options, value=selection),
        table,
    )


def refresh_history():
    history = _load_history()
    options = _history_options(history)
    table = _history_table(history)
    return gr.update(choices=options, value=options[0] if options else None), table


css = """
:root {
  --section-gap: 12px;
}
.history-table table {
  font-size: 14px;
}
"""

with gr.Blocks(title="台語 TTS") as demo:
    gr.Markdown(
        textwrap.dedent(
            """
            # 台語文字轉語音
            輸入要合成的文字，點擊「產生語音」。系統會呼叫外部 TTS API，並保留最近 50 筆紀錄方便重播。
            """
        ).strip()
    )

    with gr.Row():
        text_input = gr.Textbox(
            label="輸入文字",
            placeholder="輸入要轉成語音的句子，支援多行。",
            lines=4,
        )
    with gr.Row():
        model_input = gr.Dropdown(
            label="模型",
            choices=["model6"],
            value="model6",
        )
        submit_btn = gr.Button("產生語音", variant="primary")
    with gr.Row():
        audio_output = gr.Audio(label="語音播放", interactive=False, autoplay=True)
    with gr.Row():
        message_box = gr.Textbox(label="狀態", interactive=False)
        tailuo_box = gr.Textbox(label="白話字 / Tailo", interactive=False)
        ipa_box = gr.Textbox(label="IPA", interactive=False)

    gr.Markdown("### 歷史紀錄（最多 50 筆）")
    with gr.Row():
        history_selector = gr.Dropdown(
            label="選擇紀錄以重播或重新編輯",
            choices=_history_options(_load_history()),
            value=None,
        )
    refresh_btn = gr.Button("重新載入紀錄")
    history_table = gr.Dataframe(
        headers=["Time (UTC)", "Model", "Text", "Audio URL"],
        datatype=["str", "str", "str", "str"],
        value=_history_table(_load_history()),
        interactive=False,
        wrap=True,
        elem_classes=["history-table"],
    )

    submit_btn.click(
        fn=handle_tts,
        inputs=[text_input, model_input],
        outputs=[
            audio_output,
            message_box,
            tailuo_box,
            ipa_box,
            history_selector,
            history_table,
        ],
    )

    history_selector.change(
        fn=load_history_item,
        inputs=history_selector,
        outputs=[
            audio_output,
            message_box,
            tailuo_box,
            ipa_box,
            history_selector,
            history_table,
        ],
        queue=False,
    )

    refresh_btn.click(
        fn=refresh_history,
        inputs=None,
        outputs=[history_selector, history_table],
        queue=False,
    )

if __name__ == "__main__":
    demo.launch(css=css)

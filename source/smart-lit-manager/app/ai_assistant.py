"""Multi-model AI assistant with QThread async support for DeepSeek/OpenAI/Ollama."""
import json
import urllib.request
import urllib.error
import logging
from PyQt5.QtCore import QThread, pyqtSignal, QObject

log = logging.getLogger(__name__)

MODEL_PROVIDERS = {
    "DeepSeek-V3": {
        "base_url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-chat",
    },
    "DeepSeek-R1": {
        "base_url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-reasoner",
    },
    "OpenAI GPT-4o": {
        "base_url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o",
    },
    "OpenAI GPT-3.5": {
        "base_url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-3.5-turbo",
    },
    "Ollama (Local)": {
        "base_url": "http://localhost:11434/api/chat",
        "model": "llama3",
    },
}


class AIAssistant(QObject):
    """AI assistant that runs API calls in a background thread to avoid UI freezing."""

    # Signals for async communication
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self, api_key="", model_name="DeepSeek-V3", parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.model_name = model_name
        self.conversation_history = []
        self._thread = None
        self._worker = None

    def is_configured(self):
        return bool(self.api_key) or "ollama" in MODEL_PROVIDERS.get(self.model_name, {}).get("base_url", "")

    def set_model(self, model_name, api_key=""):
        self.model_name = model_name
        if api_key:
            self.api_key = api_key

    # ── Synchronous methods (for single-shot calls like summarize) ──

    def summarize_paper(self, title, abstract, fulltext=""):
        if not self.is_configured():
            return None
        text = f"Title: {title}\n"
        if abstract:
            text += f"Abstract: {abstract}\n"
        if fulltext:
            text += f"Content: {fulltext[:3000]}\n"
        prompt = (
            "You are a research assistant. Summarize the following paper "
            "structured into:\n"
            "[Background & Problem Statement]\n"
            "[Core Innovation & Methodology]\n"
            "[Experimental Setup & Key Results]\n"
            "[Limitations & Future Work]\n\n"
            f"{text}"
        )
        return self._call_api_sync(prompt)

    def extract_keywords(self, title, abstract):
        if not self.is_configured():
            return None
        text = f"Title: {title}\nAbstract: {abstract}\n"
        prompt = "Extract 5-8 key research keywords as comma-separated list.\n\n" + text
        return self._call_api_sync(prompt)

    def suggest_tags(self, title, abstract):
        if not self.is_configured():
            return None
        text = f"Title: {title}\nAbstract: {abstract[:2000]}\n"
        prompt = "Suggest 3-5 category tags as comma-separated list.\n\n" + text
        return self._call_api_sync(prompt)

    # ── Async chat (non-blocking, emits signals) ──

    def chat_async(self, user_message, library_context=None):
        """Send a chat message asynchronously. Results come via response_ready signal."""
        self.conversation_history.append({"role": "user", "content": user_message})
        self.status_changed.emit("Thinking...")

        system_prompt = (
            "You are an advanced academic research assistant within a literature management system. "
            "You have full knowledge of the user's paper library.\n"
            "When summarizing, structure into: [Background, Methodology, Evaluation, Limitations].\n"
            "Use LaTeX for formulas (e.g., $E=mc^2$). "
            "Respond in the same language as the user's input."
        )
        if library_context:
            system_prompt += "\n\nLibrary context:\n" + library_context

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history[-20:])

        # Run in thread
        self._thread = QThread()
        self._worker = ApiWorker(
            api_key=self.api_key,
            model_name=self.model_name,
            messages=messages,
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_worker_finished(self, result):
        if result and not result.startswith("[API Error"):
            self.conversation_history.append({"role": "assistant", "content": result})
            self.response_ready.emit(result)
            self.status_changed.emit("Ready")
        else:
            error_msg = result if result else "[API Error: No response]"
            self.error_occurred.emit(error_msg)
            self.status_changed.emit("Error")

    def clear_conversation(self):
        self.conversation_history = []

    # ── Internal sync API call ──

    def _call_api_sync(self, prompt=None, messages=None, max_tokens=2000):
        provider = MODEL_PROVIDERS.get(self.model_name, MODEL_PROVIDERS["DeepSeek-V3"])
        if messages is None:
            messages = [{"role": "user", "content": prompt}]
        return _do_api_call(provider, self.api_key, messages, max_tokens)


class ApiWorker(QObject):
    """Worker object that runs an API call in a background thread."""
    finished = pyqtSignal(str)

    def __init__(self, api_key, model_name, messages):
        super().__init__()
        self.api_key = api_key
        self.model_name = model_name
        self.messages = messages

    def run(self):
        provider = MODEL_PROVIDERS.get(self.model_name, MODEL_PROVIDERS["DeepSeek-V3"])
        result = _do_api_call(provider, self.api_key, self.messages, 2000)
        self.finished.emit(result)


def _do_api_call(provider, api_key, messages, max_tokens=2000):
    """Low-level synchronous API call shared by sync and async paths."""
    try:
        if "ollama" in provider["base_url"]:
            data = {"model": provider["model"], "messages": messages, "stream": False}
        else:
            data = {
                "model": provider["model"],
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.3,
            }
            # DeepSeek-R1 doesn't support temperature
            if "deepseek-reasoner" in provider["model"]:
                data.pop("temperature", None)

        payload = json.dumps(data).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        req = urllib.request.Request(
            provider["base_url"], data=payload, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if "ollama" in provider["base_url"]:
                return body.get("message", {}).get("content", "").strip()
            return body["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        log.error("API HTTP %d: %s", e.code, error_body)
        return f"[API Error {e.code}: {error_body[:200]}]"
    except Exception as e:
        log.error("API call failed: %s", e)
        return f"[API Error: {e}]"

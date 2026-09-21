import os
from typing import Any, List, Optional
from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from huggingface_hub import InferenceClient, HfApi

# Load environment variables from .env if present
load_dotenv(override=True)

def get_config_val(key: str, default: str = "") -> str:
    """Read configuration from Streamlit Cloud secrets first, then OS environment / .env."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    val = os.getenv(key)
    if val:
        return val
    return default

# Default settings (supports Streamlit Cloud secrets and local .env)
DEFAULT_HF_MODEL = get_config_val("HF_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B")
DEFAULT_OLLAMA_MODEL = get_config_val("OLLAMA_MODEL", "qwen3:4b")
OLLAMA_BASE_URL = get_config_val("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_PROVIDER = get_config_val("LLM_PROVIDER", "Hugging Face")

HF_POPULAR_FREE_MODELS = [
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
    "Qwen/Qwen2.5-7B-Instruct",
    "meta-llama/Llama-3.2-3B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "microsoft/Phi-3.5-mini-instruct",
]

class HFChatModel(BaseChatModel):
    model_id: str = DEFAULT_HF_MODEL
    token: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 2500

    @property
    def _llm_type(self) -> str:
        return "huggingface_inference"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        client = InferenceClient(model=self.model_id, token=self.token)
        hf_msgs = []
        for m in messages:
            role = "system" if m.type == "system" else ("user" if m.type == "human" else "assistant")
            hf_msgs.append({"role": role, "content": str(m.content)})
        
        try:
            resp = client.chat_completion(
                messages=hf_msgs,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            content = resp.choices[0].message.content or "{}"
        except Exception as e:
            # Fallback to text_generation if chat_completion encounters model provider differences
            raw_prompt = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in hf_msgs]) + "\n\nASSISTANT:"
            content = client.text_generation(raw_prompt, max_new_tokens=self.max_tokens, temperature=self.temperature)
        
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

def get_hf_token() -> Optional[str]:
    return get_config_val("HF_TOKEN") or get_config_val("HUGGINGFACEHUB_API_TOKEN") or None

def check_huggingface(model_name: str, token: Optional[str] = None) -> tuple[bool, str]:
    active_token = token or get_hf_token()
    if not active_token:
        return False, "Hugging Face requires a free API token. Set HF_TOKEN in Secrets or enter it in the sidebar."
    try:
        api = HfApi(token=active_token)
        user_info = api.whoami()
        username = user_info.get("name", "user")
        return True, f"Connected to Hugging Face ({username}) • {model_name}"
    except Exception as e:
        err = str(e)
        if "401" in err or "Invalid" in err:
            return False, "Invalid Hugging Face token. Please verify at huggingface.co/settings/tokens"
        return False, f"Hugging Face connection error: {err[:80]}"

def check_ollama(model_name: str = DEFAULT_OLLAMA_MODEL) -> tuple[bool, str]:
    try:
        import requests
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if r.ok:
            names = [m.get("name", "") for m in r.json().get("models", [])]
            if any(n == model_name or n == f"{model_name}:latest" or n.startswith(f"{model_name}:") for n in names):
                return True, f"Connected to Ollama: {model_name}"
            avail = ", ".join(names) if names else "None"
            return False, f"Ollama reachable, but '{model_name}' not found. (Available: {avail})"
        return False, f"Ollama returned HTTP {r.status_code}"
    except Exception as e:
        return False, f"Cannot reach Ollama at {OLLAMA_BASE_URL} (Ollama only works locally): {e}"

_CURRENT_LLM = None

def set_active_llm(llm):
    global _CURRENT_LLM
    _CURRENT_LLM = llm

def get_current_llm():
    global _CURRENT_LLM
    if _CURRENT_LLM is not None:
        return _CURRENT_LLM
    return get_llm()

def get_llm(provider: str = "Hugging Face", model_name: Optional[str] = None, token: Optional[str] = None):
    # Check environment variable or Streamlit secrets override
    env_provider = get_config_val("LLM_PROVIDER", provider)
    
    if env_provider == "Ollama":
        try:
            from langchain_ollama import ChatOllama
            m = model_name or get_config_val("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
            return ChatOllama(model=m, base_url=OLLAMA_BASE_URL, temperature=0.1, format="json")
        except Exception as e:
            raise RuntimeError(f"Ollama is only supported when running locally with an active Ollama daemon: {e}")
    else:
        # Default: Hugging Face
        m = model_name or get_config_val("HF_MODEL", DEFAULT_HF_MODEL)
        t = token or get_hf_token()
        return HFChatModel(model_id=m, token=t, temperature=0.1)

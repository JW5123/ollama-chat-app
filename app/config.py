BASE_URL = "http://127.0.0.1:11434/v1"
API_KEY = "ollama"
MODEL = "llama3.1:latest"

AVAILABLE_MODELS = [
    "llama3.1:8b",
    "llama3.2:3b",
    "llama3.1:latest",
    "codellama:latest"
]

DEFAULT_SYSTEM_PROMPT = (
    "你是專業的中文助理，請全程使用台灣繁體中文即zh-TW回覆，"
    "用詞與標點採台灣慣用法，除非明確要求其他語言或格式。"
)
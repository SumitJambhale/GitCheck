import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILENAME = ".gitcheckrc"

class Config:
    def __init__(self):
        self.config_data = self._load_config_file()
        self.threshold = float(self._get("THRESHOLD", 80.0))
        self.provider = self._get("AI_PROVIDER", "auto").lower()
        self.gemini_api_key = self._get("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
        self.openai_api_key = self._get("OPENAI_API_KEY", "")
        self.anthropic_api_key = self._get("ANTHROPIC_API_KEY", "")
        self.supabase_url = self._get("SUPABASE_URL", "")
        self.supabase_anon_key = self._get("SUPABASE_ANON_KEY", self._get("SUPABASE_KEY", ""))
        self.dashboard_url = self._get("GITCHECK_DASHBOARD_URL", "http://localhost:5173")

    def _load_config_file(self) -> Dict[str, Any]:
        paths = [
            Path.cwd() / CONFIG_FILENAME,
            Path.home() / CONFIG_FILENAME,
        ]
        for p in paths:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
        return {}

    def _get(self, key: str, default: Any = "") -> Any:
        # Check env first, then config file, then default
        val = os.getenv(key)
        if val is not None and val != "":
            return val
        return self.config_data.get(key, default)

    def resolve_provider(self) -> str:
        if self.provider != "auto":
            return self.provider
        if self.gemini_api_key:
            return "gemini"
        if self.openai_api_key:
            return "openai"
        if self.anthropic_api_key:
            return "anthropic"
        return "fallback"

    def save_local(self, key: str, value: Any):
        path = Path.cwd() / CONFIG_FILENAME
        data = self._load_config_file()
        data[key] = value
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

config = Config()

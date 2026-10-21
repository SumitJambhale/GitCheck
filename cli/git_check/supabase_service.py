import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from .config import config

LOCAL_STORE_FILE = ".gitcheck_history.json"

class SupabaseService:
    def __init__(self):
        self.url = config.supabase_url.rstrip("/")
        self.key = config.supabase_anon_key

    def is_configured(self) -> bool:
        return bool(self.url and self.key)

    def save_review(self, review_data: Dict[str, Any]) -> bool:
        """
        Saves commit review findings and summary to Supabase or local fallback store.
        """
        # Always store locally as fallback / instant cache
        self._save_to_local_file(review_data)

        if not self.is_configured():
            return False

        endpoint = f"{self.url}/rest/v1/git_check_reviews"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        payload = {
            "ticket_number": review_data.get("ticket_number", "UNKNOWN"),
            "branch_name": review_data.get("branch_name", ""),
            "commit_hash": review_data.get("commit_hash", ""),
            "author_name": review_data.get("author_name", ""),
            "author_email": review_data.get("author_email", ""),
            "summary": review_data.get("summary", ""),
            "detailed_analysis": review_data.get("detailed_analysis", {}),
            "agreed_with_changes": review_data.get("agreed_with_changes", True),
            "passed_verification": review_data.get("passed_verification", False),
            "status": review_data.get("status", "COMPLETED"),
            "tags": review_data.get("tags", [])
        }

        try:
            res = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            return res.status_code in (200, 201)
        except Exception:
            return False

    def fetch_ticket_history(self, ticket_number: str) -> List[Dict[str, Any]]:
        """
        Fetches previous commit contexts for a ticket so the developer understands
        the context when PRs are rejected or iterated on.
        """
        if self.is_configured():
            endpoint = f"{self.url}/rest/v1/git_check_reviews?ticket_number=eq.{ticket_number}&order=created_at.desc"
            headers = {
                "apikey": self.key,
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json"
            }
            try:
                res = requests.get(endpoint, headers=headers, timeout=10)
                if res.status_code == 200:
                    remote_records = res.json()
                    if remote_records:
                        return remote_records
            except Exception:
                pass

        # Fallback to local history
        local_records = self._load_local_file()
        matching = [r for r in local_records if r.get("ticket_number") == ticket_number]
        return sorted(matching, key=lambda x: x.get("created_at", ""), reverse=True)

    def _save_to_local_file(self, data: Dict[str, Any]):
        records = self._load_local_file()
        records.insert(0, data)
        try:
            with open(LOCAL_STORE_FILE, "w", encoding="utf-8") as f:
                json.dump(records[:100], f, indent=2)
        except Exception:
            pass

    def _load_local_file(self) -> List[Dict[str, Any]]:
        p = Path(LOCAL_STORE_FILE)
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

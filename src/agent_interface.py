import os
import re
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI

import config
from prompt_builder import PromptBuilder


class LLMBackend:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


@dataclass
class OpenAIBackend(LLMBackend):
    model: Optional[str] = None
    temperature: Optional[float] = None
    base_url: Optional[str] = None

    def __post_init__(self) -> None:
        load_dotenv()
        resolved_base_url = self.base_url
        if resolved_base_url is None:
            resolved_base_url = config.OPENAI_API_BASE
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=resolved_base_url if resolved_base_url else None,
        )
        if self.model is None:
            self.model = config.OPENAI_ENGINE
        if self.temperature is None:
            self.temperature = config.OPENAI_TEMPERATURE

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a Python strategy generator. "
                        "Output valid JSON only. "
                        "The JSON must contain exactly two keys: reasoning and code. "
                        "Do not use markdown. Do not use code fences."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "max_completion_tokens": 2000,
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        response = self.client.chat.completions.create(**payload)
        return response.choices[0].message.content


class MockBackend(LLMBackend):
    def generate(self, prompt: str) -> str:
        if "Output only the Python source code" in prompt:
            return (
                "def get_bid(day_context, my_status):\n"
                "    base = min(my_status['budget'], 10.0)\n"
                "    if my_status['hp'] <= 4:\n"
                "        return min(my_status['budget'], base + 5.0)\n"
                "    return base\n"
            )
        return "Focus on survival by bidding modestly and increasing bids when HP is low."


@dataclass
class GeminiBackend(LLMBackend):
    model: Optional[str] = None
    temperature: Optional[float] = None
    api_key: Optional[str] = None

    def __post_init__(self) -> None:
        load_dotenv()
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError(
                "Gemini backend requires google-generativeai. Install with: pip install google-generativeai"
            ) from exc

        resolved_api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not resolved_api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini backend")

        genai.configure(api_key=resolved_api_key)
        model_name = self.model or config.GEMINI_MODEL
        self.client = genai.GenerativeModel(model_name)

    def generate(self, prompt: str) -> str:
        # 🌟 核心修正點 1：強制 Gemini 使用 JSON 輸出模式，徹底去除 markdown fences
        generation_config = {
            "temperature": self.temperature or 0.6,
            "response_mime_type": "application/json"
        }
        response = self.client.generate_content(prompt, generation_config=generation_config)
        return response.text or ""


@dataclass
class OllamaBackend(LLMBackend):
    model: Optional[str] = None
    temperature: Optional[float] = None
    url: str = "http://localhost:11434/api/generate"

    def __post_init__(self) -> None:
        import requests
        self.requests = requests

        if self.model is None:
            self.model = "llama3.1:8b"

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        if self.temperature is not None:
            payload["options"] = {
                "temperature": self.temperature
            }

        response = self.requests.post(
            self.url,
            json=payload,
            timeout=300,
        )

        response.raise_for_status()
        data = response.json()
        return data.get("response", "")


@dataclass
class DeepSeekBackend(LLMBackend):
    model: Optional[str] = None
    temperature: Optional[float] = None
    base_url: str = "https://api.deepseek.com"

    def __post_init__(self) -> None:
        load_dotenv()
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=self.base_url,
        )

        if self.model:
            self.model = self.model.strip()
        else:
            self.model = "deepseek-v4-flash"

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a Python strategy generator. "
                        "Output valid JSON only. "
                        "The JSON must contain exactly two keys: reasoning and code. "
                        "The code must define def get_bid(day_context, my_status, opponents_status). "
                        "Do not use markdown. Do not use code fences."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "max_tokens": 2000,
            "extra_body": {
                "thinking": {
                    "type": "enabled"
                }
            },
        }

        if self.temperature is not None:
            payload["temperature"] = self.temperature

        response = self.client.chat.completions.create(**payload)
        return response.choices[0].message.content


def create_backend(
    name: str,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    base_url: Optional[str] = None,
) -> LLMBackend:
    if name == "mock":
        return MockBackend()
    if name == "openai":
        return OpenAIBackend(model=model, temperature=temperature, base_url=base_url)
    if name == "gemini":
        return GeminiBackend(model=model, temperature=temperature)
    if name == "ollama":
        return OllamaBackend(model=model, temperature=temperature)
    if name == "deepseek": 
        return DeepSeekBackend(model=model, temperature=temperature)
    raise ValueError(f"Unknown backend: {name}")


class AgentRunner:
    def __init__(
        self,
        backend: Optional[LLMBackend] = None,
        backend_map: Optional[Dict[str, LLMBackend]] = None,
        prompt_builder: Optional[PromptBuilder] = None,
    ) -> None:
        if backend is None and not backend_map:
            raise ValueError("AgentRunner requires a backend or backend_map")
        self.backend = backend
        self.backend_map = backend_map or {}
        self.prompt_builder = prompt_builder or PromptBuilder()

    def _select_backend(self, agent_id: str) -> LLMBackend:
        if agent_id in self.backend_map:
            return self.backend_map[agent_id]
        if self.backend is not None:
            return self.backend
        raise KeyError(f"No backend configured for agent_id={agent_id}")

    def _extract_json_field(
        self,
        response: str,
        field: str,
    ) -> str:

        pattern = (
            r'"'
            + re.escape(field)
            + r'"\s*:\s*"((?:\\.|[^"\\])*)'
        )

        match = re.search(
            pattern,
            response,
            re.DOTALL,
        )

        if not match:
            return ""

        raw_value = match.group(1)

        try:
            return json.loads(
                '"' + raw_value + '"'
            )
        except Exception:
            return raw_value.replace(
                "\\n",
                "\n"
            ).replace(
                '\\"',
                '"'
            )

    def _extract_strategy_code(
        self,
        response: str,
    ) -> str:

        code = self._extract_json_field(
            response,
            "code",
        )

        if code:
            return code

        all_blocks = re.findall(
            r"```python\s*(.*?)\s*```",
            response,
            re.DOTALL,
        )

        if not all_blocks:
            all_blocks = re.findall(
                r"```\s*(.*?)\s*```",
                response,
                re.DOTALL,
            )

        if all_blocks:
            return all_blocks[-1]

        match = re.search(
            r"(def\s+get_bid\(.*)",
            response,
            re.DOTALL,
        )

        if match:
            code = match.group(1)
            code = code.replace("\\n", "\n")
            code = code.replace('\\"', '"')
            return code

        return (
            "def get_bid(day_context, my_status, opponents_status):\n"
            "    return 15.0"
        )

    def generate_strategy(
        self,
        agent_profile: Dict[str, Any],
        game_state: Dict[str, Any],
        opponent_code: Dict[str, str],
        history: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str]:
        backend = self._select_backend(agent_profile.get("agent_id", ""))
        combined_prompt = self.prompt_builder.build_combined_prompt(
            agent_profile=agent_profile,
            game_state=game_state,
            opponent_code=opponent_code,
            history=history,
        )

        response = backend.generate(combined_prompt)

        # 🌟 核心修正點 2：在將字串餵給 json.loads 之前，自動切除所有可能存在的 ```json 外殼
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        parse_failed = False

        try:
            # 這裡改成解析清洗過後的 cleaned_response
            parsed = json.loads(cleaned_response)

            reasoning_cot = parsed.get(
                "reasoning",
                ""
            )

            strategy_code = parsed.get(
                "code",
                ""
            )

        except Exception:
            parse_failed = True

            reasoning_cot = self._extract_json_field(
                response,
                "reasoning",
            )

            strategy_code = self._extract_strategy_code(
                response
            )

        if parse_failed:
            print("\n[WARN] JSON parse failed.")
            print(
                "Agent:",
                agent_profile.get(
                    "agent_id",
                    "unknown"
                )
            )
            print("Raw response preview:")
            print(response[:1000])
            print()

        # ============================================================
        # 強化版程式碼提取邏輯
        # ============================================================
        all_blocks = re.findall(r"```python\s*(.*?)\s*```", strategy_code, re.DOTALL)
        if not all_blocks:
            all_blocks = re.findall(r"```\s*(.*?)\s*```", strategy_code, re.DOTALL)

        if all_blocks:
            strategy_code = all_blocks[-1]
        else:
            match = re.search(r"(def\s+get_bid\(.*?\):.*)", strategy_code, re.DOTALL)
            if match:
                strategy_code = match.group(1)
            else:
                strategy_code = "def get_bid(day_context, my_status, opponents_status): return 15.0"

        if "def get_bid" not in strategy_code:
            strategy_code = re.sub(
                r"def\s+\w+\s*\(",
                "def get_bid(",
                strategy_code,
            )

        return reasoning_cot, strategy_code.strip()
import os
import re
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI

import config
from prompt_builder import PromptBuilder
from strategy_validator import validate_strategy_code


class LLMBackend:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


@dataclass
class OpenAIBackend(LLMBackend):
    model: Optional[str] = None
    temperature: Optional[float] = None
    base_url: Optional[str] = None
    system_prompt: Optional[str] = None

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
                    "content": self.system_prompt or (
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
            "max_completion_tokens": 3500,
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
    system_prompt: Optional[str] = None

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
                    "content": self.system_prompt or (
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
            "max_tokens": 3500,
            "extra_body": {
                "thinking": {
                    "type": "enabled"
                }
            },
        }

        if config.DEEPSEEK_JSON_MODE:
            payload["response_format"] = {
                "type": "json_object"
            }

        if self.temperature is not None:
            payload["temperature"] = self.temperature

        response = self.client.chat.completions.create(**payload)
        return response.choices[0].message.content


@dataclass
class ClaudeBackend(LLMBackend):
    model: Optional[str] = None
    temperature: Optional[float] = None
    api_key: Optional[str] = None
    system_prompt: Optional[str] = None

    def __post_init__(self) -> None:
        load_dotenv()
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError(
                "Claude backend requires anthropic. Install with: pip install anthropic"
            ) from exc

        resolved_api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not resolved_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Claude backend")

        self.client = Anthropic(api_key=resolved_api_key)

        if self.model:
            self.model = self.model.strip()
        else:
            self.model = config.CLAUDE_MODEL

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "system": self.system_prompt or (
                "You are a Python strategy generator. "
                "Output valid JSON only. "
                "The JSON must contain exactly two keys: reasoning and code. "
                "The code must define def get_bid(day_context, my_status, opponents_status). "
                "Do not use markdown. Do not use code fences."
            ),
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "max_tokens": 3500,
        }

        response = self.client.messages.create(**payload)
        return "".join(
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        )


def create_backend(
    name: str,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    base_url: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> LLMBackend:
    if name == "mock":
        return MockBackend()
    if name == "openai":
        return OpenAIBackend(
            model=model,
            temperature=temperature,
            base_url=base_url,
            system_prompt=system_prompt,
        )
    if name == "gemini":
        return GeminiBackend(model=model, temperature=temperature)
    if name == "ollama":
        return OllamaBackend(model=model, temperature=temperature)
    if name == "deepseek": 
        return DeepSeekBackend(
            model=model,
            temperature=temperature,
            system_prompt=system_prompt,
        )
    if name == "claude":
        return ClaudeBackend(
            model=model,
            temperature=temperature,
            system_prompt=system_prompt,
        )
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
    ) -> Tuple[str, bool]:

        code = self._extract_json_field(
            response,
            "code",
        )

        if code:
            return code, False

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
            return all_blocks[-1], False

        match = re.search(
            r"(def\s+get_bid\(.*)",
            response,
            re.DOTALL,
        )

        if match:
            code = match.group(1)
            code = code.replace("\\n", "\n")
            code = code.replace('\\"', '"')
            return code, False

        return "", True

    def _parse_generation_response(
        self,
        response: str,
    ) -> Tuple[str, str, bool, bool]:
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        parse_failed = False
        code_extraction_failed = False

        try:
            parsed = json.loads(cleaned_response)

            reasoning_cot = parsed.get("reasoning", "")
            if not isinstance(reasoning_cot, str):
                reasoning_cot = str(reasoning_cot)

            strategy_code = parsed.get("code", "")
            if not isinstance(strategy_code, str):
                strategy_code = ""

            raw_code_extracted = int(
                bool(strategy_code.strip())
                and "def get_bid" in strategy_code
            )
            code_extraction_failed = (raw_code_extracted == 0)

        except Exception:
            parse_failed = True

            reasoning_cot = self._extract_json_field(
                response,
                "reasoning",
            )

            strategy_code, code_extraction_failed = self._extract_strategy_code(
                response
            )

        return reasoning_cot, strategy_code.strip(), parse_failed, code_extraction_failed

    def generate_strategy(
        self,
        agent_profile: Dict[str, Any],
        game_state: Dict[str, Any],
        opponent_code: Dict[str, str],
        self_previous_code: str = "",
        history: Optional[Dict[str, Any]] = None,
        opponent_info_mode: Optional[str] = None,
        show_opponent_code: Optional[bool] = None,
    ) -> Tuple[str, str, Dict[str, Any]]:
        backend = self._select_backend(agent_profile.get("agent_id", ""))
        combined_prompt = self.prompt_builder.build_combined_prompt(
            agent_profile=agent_profile,
            game_state=game_state,
            opponent_code=opponent_code,
            self_previous_code=self_previous_code,
            history=history,
            opponent_info_mode=opponent_info_mode,
            show_opponent_code=show_opponent_code,
        )

        response = backend.generate(combined_prompt)

        reasoning_cot, strategy_code, parse_failed, code_extraction_failed = (
            self._parse_generation_response(response)
        )

        raw_code_extracted = int(
            bool(strategy_code.strip())
            and "def get_bid" in strategy_code
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

        return (
            reasoning_cot,
            strategy_code.strip(),
            {
                "raw_json_valid": int(not parse_failed),
                "raw_code_extracted": raw_code_extracted,
                "code_extraction_failed": int(code_extraction_failed),
                "json_parse_failed": int(parse_failed),
                "default_code_used": 0,
                "generation_success": int((not parse_failed) and raw_code_extracted),
                "raw_response_preview": response[:4000],
                "_raw_response": response,
            },
        )

    def repair_json_output(
        self,
        agent_id: str,
        raw_response: str,
    ) -> Tuple[str, str, Dict[str, Any]]:
        backend = self._select_backend(agent_id)

        repair_prompt = (
            "You are repairing an invalid model response.\n"
            "Convert the raw response into exactly one valid JSON object.\n"
            "The JSON object must contain exactly two keys: reasoning and code.\n"
            "The code value must be a Python string defining:\n"
            "def get_bid(day_context, my_status, opponents_status):\n"
            "Do not use markdown.\n"
            "Do not use code fences.\n"
            "Do not add explanations outside JSON.\n\n"
            "Raw response:\n"
            f"{raw_response}"
        )

        repair_error = None
        try:
            repaired_response = backend.generate(repair_prompt)
            reasoning, strategy_code, parse_failed, _ = self._parse_generation_response(
                repaired_response
            )
            repaired_json_valid = int(not parse_failed)
            repaired_code_extracted = int(
                bool(strategy_code.strip())
                and "def get_bid" in strategy_code
            )
        except Exception as exc:
            reasoning = ""
            strategy_code = ""
            repaired_json_valid = 0
            repaired_code_extracted = 0
            repair_error = str(exc)

        repair_stats = {
            "json_repair_used": 1,
            "json_repair_success": int(repaired_json_valid and repaired_code_extracted),
            "json_repair_error": repair_error,
        }

        if repair_stats["json_repair_success"] == 0 and repair_error is None:
            repair_stats["json_repair_error"] = (
                "JSON repair output still failed schema/code extraction checks."
            )

        return reasoning, strategy_code, repair_stats

    def repair_strategy_code(
        self,
        agent_id: str,
        broken_code: str,
        validation_error: str,
    ) -> Tuple[str, str, Dict[str, Any]]:
        backend = self._select_backend(agent_id)

        repair_prompt = (
            "The previous strategy code failed validation.\n\n"
            "Validation error:\n"
            f"{validation_error}\n\n"
            "Broken code:\n"
            f"{broken_code}\n\n"
            "Please repair the code.\n\n"
            "Rules:\n"
            "1. Output valid JSON only.\n"
            "2. JSON must contain exactly two keys: reasoning and code.\n"
            "3. code must define exactly:\n"
            "   def get_bid(day_context, my_status, opponents_status):\n"
            "4. Do not use import/from.\n"
            "5. Do not use file/network access.\n"
            "6. Do not use eval/exec/open.\n"
            "7. Never return NaN or infinity.\n"
            "8. Always return a finite float or int.\n"
            "9. Never return a bid larger than my_status[\"budget\"].\n"
            "10. Be robust to missing opponent fields, e.g. use opp.get(\"last_bid\", 0).\n"
            "11. Available builtins only: min, max, abs, round, float, int, len, sum, any, all, isinstance, dict, list, tuple, range, sorted, enumerate.\n"
            "12. The math module is available as math, but imports are forbidden.\n"
            "13. Do not use bool, str, type, hasattr, set, zip, map, filter, reversed, globals, locals, vars, compile.\n"
            "14. Do not use dunder names or attributes containing double underscores.\n"
            "15. Do not use float('inf'), float('-inf'), NaN, or infinity checks that require unavailable helpers.\n"
            "16. If the broken code contains a forbidden name, remove every occurrence from the repaired code.\n"
            "17. The returned value must always be a finite float in [0.0, my_status[\"budget\"]]. If you apply any minimum bid or urgency floor, clamp to budget AFTER that floor.\n"
            "18. End with this safety pattern or an equivalent final clamp:\n"
            "    bid = max(0.0, bid)\n"
            "    bid = min(budget, bid)\n"
            "    return float(bid)\n"
            "19. Do not use markdown or code fences."
        )

        repair_error = None
        try:
            repaired_response = backend.generate(repair_prompt)
            reasoning, repaired_code, _, _ = self._parse_generation_response(
                repaired_response
            )
            validation = validate_strategy_code(repaired_code)
            repair_success = int(validation.admitted)
            if repair_success == 0:
                repair_error = validation.error_message or validation.error_type
        except Exception as exc:
            reasoning = ""
            repaired_code = ""
            repair_success = 0
            repair_error = str(exc)

        repair_stats = {
            "code_repair_used": 1,
            "code_repair_success": repair_success,
            "code_repair_error": repair_error,
        }

        return reasoning, repaired_code, repair_stats

    def generate_validated_strategy(
        self,
        agent_profile: Dict[str, Any],
        game_state: Dict[str, Any],
        opponent_code: Dict[str, str],
        self_previous_code: str = "",
        history: Optional[Dict[str, Any]] = None,
        opponent_info_mode: Optional[str] = None,
        show_opponent_code: Optional[bool] = None,
        evaluation_mode: str = "repair_assisted",
        max_json_repair_attempts: int = 1,
        max_code_repair_attempts: int = 1,
    ) -> Tuple[str, str, Dict[str, Any]]:
        reasoning_cot, strategy_code, generation_stats = self.generate_strategy(
            agent_profile=agent_profile,
            game_state=game_state,
            opponent_code=opponent_code,
            self_previous_code=self_previous_code,
            history=history,
            opponent_info_mode=opponent_info_mode,
            show_opponent_code=show_opponent_code,
        )

        one_shot_validation = validate_strategy_code(strategy_code)

        one_shot_json_valid = int(generation_stats.get("raw_json_valid", 0))
        one_shot_code_extracted = int(generation_stats.get("raw_code_extracted", 0))
        one_shot_compile_success = int(one_shot_validation.compile_success)
        one_shot_runtime_success = int(one_shot_validation.runtime_success)
        one_shot_strict_success = int(
            one_shot_json_valid
            and one_shot_code_extracted
            and one_shot_validation.admitted
        )

        candidate_reasoning = reasoning_cot
        candidate_code = strategy_code
        final_validation = one_shot_validation

        json_repair_used = 0
        json_repair_success = 0
        code_repair_used = 0
        code_repair_success = 0
        total_repair_attempts = 0
        json_repair_error = None
        code_repair_error = None

        if evaluation_mode == "repair_assisted":
            if one_shot_json_valid == 0:
                raw_response = str(generation_stats.get("_raw_response", ""))
                for _ in range(max(0, max_json_repair_attempts)):
                    total_repair_attempts += 1
                    json_repair_used = 1
                    repaired_reasoning, repaired_code, json_stats = self.repair_json_output(
                        agent_id=agent_profile.get("agent_id", ""),
                        raw_response=raw_response,
                    )
                    if int(json_stats.get("json_repair_success", 0)) == 1:
                        if repaired_reasoning:
                            candidate_reasoning = repaired_reasoning
                        candidate_code = repaired_code
                        json_repair_success = 1
                        break
                    json_repair_error = json_stats.get("json_repair_error")

            final_validation = validate_strategy_code(candidate_code)

            if not final_validation.admitted:
                for _ in range(max(0, max_code_repair_attempts)):
                    total_repair_attempts += 1
                    code_repair_used = 1
                    validation_error = (
                        f"{final_validation.error_type}: {final_validation.error_message}"
                    )
                    repaired_reasoning, repaired_code, code_stats = self.repair_strategy_code(
                        agent_id=agent_profile.get("agent_id", ""),
                        broken_code=candidate_code,
                        validation_error=validation_error,
                    )
                    if repaired_reasoning:
                        candidate_reasoning = repaired_reasoning
                    candidate_code = repaired_code
                    code_repair_error = code_stats.get("code_repair_error")

                    final_validation = validate_strategy_code(candidate_code)
                    if final_validation.admitted and int(code_stats.get("code_repair_success", 0)) == 1:
                        code_repair_success = 1
                        break

                    if int(code_stats.get("code_repair_success", 0)) == 1:
                        code_repair_success = 1

        if evaluation_mode == "one_shot":
            final_validation = one_shot_validation

        post_repair_strict_success = int(final_validation.admitted)
        final_admitted = int(final_validation.admitted)
        if evaluation_mode == "one_shot":
            post_repair_strict_success = one_shot_strict_success
            final_admitted = one_shot_strict_success

        strict_success_rate = (
            post_repair_strict_success
            if evaluation_mode == "repair_assisted"
            else one_shot_strict_success
        )

        final_stats: Dict[str, Any] = {
            "admitted": final_admitted,
            "one_shot_json_valid": one_shot_json_valid,
            "one_shot_code_extracted": one_shot_code_extracted,
            "one_shot_compile_success": one_shot_compile_success,
            "one_shot_runtime_success": one_shot_runtime_success,
            "one_shot_strict_success": one_shot_strict_success,
            "repair_used": int(json_repair_used or code_repair_used),
            "json_repair_used": int(json_repair_used),
            "json_repair_success": int(json_repair_success),
            "code_repair_used": int(code_repair_used),
            "code_repair_success": int(code_repair_success),
            "repair_attempts": total_repair_attempts,
            "post_repair_compile_success": int(final_validation.compile_success),
            "post_repair_runtime_success": int(final_validation.runtime_success),
            "post_repair_strict_success": post_repair_strict_success,
            "strict_success_rate": int(strict_success_rate),
            "final_error_type": final_validation.error_type,
            "final_error_message": final_validation.error_message,
            "one_shot_reasoning": reasoning_cot,
            "one_shot_code": strategy_code,
            "final_reasoning": candidate_reasoning,
            "final_code": candidate_code,
            "json_repair_error": json_repair_error,
            "code_repair_error": code_repair_error,
            "validation_test_results": final_validation.test_results,
            "json_parse_failed": int(generation_stats.get("json_parse_failed", 0)),
            "default_code_used": 0,
            "generation_success": int(generation_stats.get("generation_success", 0)),
            "raw_json_valid": int(generation_stats.get("raw_json_valid", 0)),
            "raw_code_extracted": int(generation_stats.get("raw_code_extracted", 0)),
            "code_extraction_failed": int(generation_stats.get("code_extraction_failed", 0)),
            "raw_response_preview": generation_stats.get("raw_response_preview", ""),
        }

        return candidate_reasoning, candidate_code, final_stats

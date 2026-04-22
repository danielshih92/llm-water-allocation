import os
import time

from openai import OpenAI  # 新版需要建立 Client 實例
from dotenv import load_dotenv
import config  # 假設你的 config.py 在同一個目錄


class PlayGround:
    def __init__(self) -> None:
        self.players = []
        self.game_setting = ""
        self.history = []  # Historical Records
        self.game_setting = []  # Game Setting

    def add_player(self, new_player):
        self.players.append(new_player)


class Player:
    def __init__(self, name, if_persona, persona):
        self.name = name
        self.if_persona = if_persona  # Persona Setting
        self.persona = persona
        self.llm = None
        self.player_status = {}  # Player Status
        self.history = []  # Memory Cache
        self.reasoning = None  # Reasoning Plugin
        self.other_components = None  # Other Components

    def append_message(self, role, content):
        self.history.append({"role": role, "content": content})

class LLM:
    def __init__(self, engine=None, temperature=None, sleep_time=None) -> None:
        load_dotenv()
        
        # 新版語法：初始化 Client，不再直接在 openai 模組上設定 api_key
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=config.OPENAI_API_BASE if config.OPENAI_API_BASE else None
            # 如果是 Azure 或是特定的 API Gateway 才需要 base_url
        )
        
        # 優先順序：傳入參數 > config.py 設定
        self.engine = engine or config.OPENAI_ENGINE
        self.temperature = temperature if temperature is not None else config.OPENAI_TEMPERATURE
        self.sleep_time = sleep_time if sleep_time is not None else config.OPENAI_SLEEP_TIME
    
    def call(self, message):
        status = 0
        RESPONSE = ""
        
        while status != 1:
            try:
                # 新版語法：client.chat.completions.create
                payload = {
                    "model": self.engine,
                    "messages": message,
                    "max_completion_tokens": 800,
                }
                if self.temperature is not None:
                    payload["temperature"] = self.temperature
                response = self.client.chat.completions.create(**payload)
                
                # 新版語法：回傳的是物件，不再是字典，改用屬性存取 (.content)
                RESPONSE = response.choices[0].message.content
                status = 1
                
                # 實驗時為了避免 Rate Limit，成功後可以稍微休息
                if self.sleep_time > 0:
                    time.sleep(self.sleep_time)
                    
            except Exception as e:
                print(f"API 發生錯誤: {e}")
                # 如果是 Rate Limit，建議休息久一點
                time.sleep(5)
                
        return RESPONSE
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # 模型配置 - LiteLLM 需要 provider/model 格式
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-3.5-turbo")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", None)

    # 组合成 LiteLLM 需要的格式
    LLM_MODEL = f"{LLM_PROVIDER}/{LLM_MODEL_NAME}"

    # 仿真配置
    SIMULATION_STEP = 0.5
    VESSEL_SPEED = 2.0

    # 地图配置
    MAP_RANGE = 200

    @classmethod
    def print_config(cls):
        """打印当前配置信息（调试用）"""
        print(f"🔧 当前模型配置：{cls.LLM_MODEL}")
        print(f"🔧 API Base: {cls.LLM_BASE_URL}")

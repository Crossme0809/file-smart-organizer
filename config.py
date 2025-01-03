import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Config:
    """用于加载和存储应用程序配置的类"""

    # 大模型配置
    API_KEY = os.getenv("API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash-thinking-exp-1219")
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))

    # 文件处理相关配置
    DEFAULT_BASE_DIR = os.getenv("DEFAULT_BASE_DIR", None)
    ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "True").lower() == "true"
    LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/app.log")

    # 应用程序配置
    APP_TITLE = os.getenv("APP_TITLE", "文件智能分类整理工具 v0.3")
    MIN_WINDOW_WIDTH = int(os.getenv("MIN_WINDOW_WIDTH", 800))
    MIN_WINDOW_HEIGHT = int(os.getenv("MIN_WINDOW_HEIGHT", 600))
# src/config.py
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 基础路径计算
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent
_DATA_DIR_ROOT = BASE_DIR / "data"

# 确保目录存在
os.makedirs(_DATA_DIR_ROOT / "logs", exist_ok=True)
os.makedirs(_DATA_DIR_ROOT / "screenshots", exist_ok=True)
os.makedirs(_DATA_DIR_ROOT / "userdata", exist_ok=True)

class Config:
    DATA_DIR = _DATA_DIR_ROOT
    USER_DATA_DIR = DATA_DIR / "userdata"
    LOG_PATH = DATA_DIR / "logs" / "epicmaster.log"
    FINGERPRINT_PATH = SRC_DIR / "fingerprints.json"
    
    EMAIL = os.getenv("EPIC_EMAIL")
    PASSWORD = os.getenv("EPIC_PASSWORD")
    
    # --- [修复 1] 严格的代理检查 ---
    # 只有当 PROXY_URL 存在且不为空字符串时才启用
    _proxy_env = os.getenv("PROXY_URL")
    PROXY = _proxy_env if _proxy_env and _proxy_env.strip() else None

    @staticmethod
    def load_fingerprint():
        if not Config.FINGERPRINT_PATH.exists():
            return {}
        with open(Config.FINGERPRINT_PATH, 'r') as f:
            return json.load(f)

config = Config()

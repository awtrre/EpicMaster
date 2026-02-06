# src/main.py
import sys
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
from apscheduler.schedulers.blocking import BlockingScheduler

# 路径修复
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

from src.config import config
from src.core.browser import StealthBrowser
from src.core.auth import EpicAuth
from src.core.claimer import EpicClaimer

# 全局变量
GLOBAL_BROWSER_MGR = None
scheduler = BlockingScheduler()

def ensure_browser_alive():
    """保活机制：如果浏览器崩溃了，重启它"""
    global GLOBAL_BROWSER_MGR
    try:
        if GLOBAL_BROWSER_MGR is None or not GLOBAL_BROWSER_MGR.page.check_page_alive():
            logger.warning("🚑 Browser is dead or not started. Launching new instance...")
            try:
                if GLOBAL_BROWSER_MGR: GLOBAL_BROWSER_MGR.page.quit()
            except: pass
            
            GLOBAL_BROWSER_MGR = StealthBrowser(config)
            GLOBAL_BROWSER_MGR.page = GLOBAL_BROWSER_MGR.start() 
            logger.success("✅ Browser launched/revived successfully.")
            return False # False = 新会话
        return True # True = 老会话
    except Exception as e:
        logger.error(f"⚠️ Browser Keep-Alive Check Failed: {e}")
        return False

def run_mission():
    global GLOBAL_BROWSER_MGR
    logger.info("🎬 Mission Start (Daemon Mode)...")
    
    try:
        # 1. 确保浏览器是活着的
        is_existing_session = ensure_browser_alive()
        
        # 2. 登录检查
        auth = EpicAuth(GLOBAL_BROWSER_MGR, config)
        
        if auth.login(is_new_session=not is_existing_session):
            
            # 3. 领取任务
            claimer = EpicClaimer(GLOBAL_BROWSER_MGR, config)
            # [修改] 获取领取结果
            all_clear = claimer.start_claiming()
            
            if all_clear:
                logger.success("💤 All missions finished cleanly. Parking browser.")
                GLOBAL_BROWSER_MGR.page.get("about:blank")
            else:
                logger.warning("🚨 Mission ended with UNRESOLVED SHIELDS.")
                logger.warning("✋ Browser LEFT OPEN on shield page for manual VNC intervention!")
            
        else:
            logger.error("❌ Login check failed. Waiting for manual intervention.")

    except Exception as e:
        logger.exception(f"💥 Mission Failure: {e}")
    
    finally:
        schedule_next_run()

def schedule_next_run():
    now = datetime.now()
    target_date = now + timedelta(days=1)
    random_hour = random.randint(10, 20)
    random_minute = random.randint(0, 59)
    next_run_time = target_date.replace(
        hour=random_hour, minute=random_minute, second=0, microsecond=0
    )
    logger.info(f"📅 Next run scheduled at: {next_run_time}")
    scheduler.add_job(run_mission, 'date', run_date=next_run_time)

if __name__ == "__main__":
    logger.add(config.LOG_PATH, rotation="1 week", encoding="utf-8")
    logger.info("🚀 EpicMaster Daemon Mode Started")

    ensure_browser_alive()
    
    start_time = datetime.now() + timedelta(seconds=5)
    scheduler.add_job(run_mission, 'date', run_date=start_time)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Shutting down daemon...")
        if GLOBAL_BROWSER_MGR:
            GLOBAL_BROWSER_MGR.page.quit()

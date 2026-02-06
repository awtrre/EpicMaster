# src/core/auth.py
import json
import time
from loguru import logger
from src.core.interaction import HumanActor
from src.core.anti_shield import ShieldBuster

class EpicAuth:
    def __init__(self, browser_mgr, config):
        self.browser = browser_mgr
        self.page = browser_mgr.page
        self.config = config
        self.actor = HumanActor(browser_mgr)
        self.buster = ShieldBuster(browser_mgr)

    def login(self, is_new_session=False):
        logger.info(f"☁️ Checking session (New Session: {is_new_session})...")

        if is_new_session:
            if self._inject_cookies_if_exist():
                logger.info("🍪 Cookies pre-injected.")

        # 0. 安全访问首页
        if "store.epicgames.com" not in self.page.url:
            self.page.get('https://store.epicgames.com/en-US/')
        
        # 统一的一套组合拳
        self.actor.wait_page_stable(3, 5)
        self.buster.check_and_solve()
        self.actor.wait_page_stable(2, 3)

        if self._is_logged_in():
            logger.success("✅ Already logged in.")
            self._save_cookies()
            return True

        if not is_new_session and self._inject_cookies_if_exist():
            self.page.refresh()
            self.actor.wait_page_stable(5, 8) # 给足时间加载 Session
            self.buster.check_and_solve()
            
            if self._is_logged_in():
                logger.success("✅ Session restored!")
                return True

        # 自动登录逻辑
        if self.config.EMAIL and self.config.PASSWORD:
            logger.info("🔑 Switching to Password Login...")
            self.page.get("https://www.epicgames.com/id/login")
            self.actor.wait_page_stable(3, 5)
            self.buster.check_and_solve()

            ele = self.page.ele('#email', timeout=10)
            if ele:
                ele.input(self.config.EMAIL)
                self.actor.wait_active(0.5, 1.0)
                pass_ele = self.page.ele('#password', timeout=5)
                if pass_ele:
                    pass_ele.input(self.config.PASSWORD)
                    self.actor.wait_active(0.5, 1.0)
                    submit_btn = self.page.ele('button[type="submit"]')
                    if submit_btn:
                        self.actor.hunt_and_click(submit_btn, "Login Submit")
                
                logger.info("⏳ Verifying password login...")
                for i in range(20):
                    # 每次循环都查盾
                    self.buster.check_and_solve()
                    self.actor.wait_page_stable(2, 3)
                    
                    curr_url = self.page.url
                    if "/account" in curr_url or "/id/" in curr_url:
                        logger.info("🔄 Landed on Account Page, redirecting to Store...")
                        self.page.get("https://store.epicgames.com/en-US/")
                        self.actor.wait_page_stable(5, 7)
                        continue

                    if self._is_logged_in():
                        logger.success("✅ Password login successful!")
                        self._save_cookies()
                        return True
        
        # 如果自动登录失败，进入手动模式
        return self._wait_for_manual_login()

    def _inject_cookies_if_exist(self):
        cookie_file = self.config.USER_DATA_DIR / "cookies.json"
        if not cookie_file.exists(): return False
        try:
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
            valid_cookies = [c for c in cookies if isinstance(c, dict) and 'name' in c]
            if valid_cookies:
                self.page.set.cookies(valid_cookies)
                return True
        except: pass
        return False

    def _wait_for_manual_login(self):
        """
        纯净的手动登录等待模式
        """
        logger.warning("🛑 Automatic login failed. Please login manually via VNC!")
        logger.warning("⚠️ SCRIPT IS PAUSED. I will strictly wait for you to finish.")
        
        # 1. 播放一个提示音（如果是在本地开发的话，Docker里听不到）
        # 2. 设置长等待，最多等 10 分钟
        max_wait_seconds = 600
        
        for i in range(0, max_wait_seconds, 5):
            # 每 5 秒钟只检查一次状态，绝不干扰页面
            if self._is_logged_in():
                logger.success(f"✅ Manual login detected! (Waited {i}s)")
                self._save_cookies()
                return True
            
            if i % 30 == 0: # 每30秒在日志里报个平安
                logger.info(f"⏳ Waiting for user input... ({i}/{max_wait_seconds}s)")
            
            time.sleep(5) 

        logger.error("❌ Manual login timeout.")
        return False

    def _is_logged_in(self):
        if "Just a moment" in self.page.title: return False
        try:
            # 1. 检查 EGS Navigation 标签 (最准)
            nav = self.page.ele('tag:egs-navigation', timeout=0.1)
            if nav and str(nav.attr('isloggedin')).lower() == 'true':
                return True
            
            # 2. 备用：检查 User 菜单链接
            if self.page.ele('css:a[href*="/account/personal"]', timeout=0.1):
                return True
        except: pass
        
        return False

    def _save_cookies(self):
        try:
            cookies = self.page.cookies()
            with open(self.config.USER_DATA_DIR / "cookies.json", 'w') as f:
                json.dump(cookies, f, indent=2)
        except: pass

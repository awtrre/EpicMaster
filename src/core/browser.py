# src/core/browser.py
import os
import shutil
import time
from pathlib import Path
from DrissionPage import ChromiumPage, ChromiumOptions
from loguru import logger

class StealthBrowser:
    def __init__(self, config_obj):
        self.page = None
        self.config = config_obj
        self.fingerprint_data = config_obj.load_fingerprint()
        
    def _force_clear_lock(self):
        """强制清理 Chromium 锁文件"""
        lock_file = self.config.USER_DATA_DIR / "SingletonLock"
        try:
            if lock_file.exists() or (lock_file.is_symlink() and not lock_file.exists()):
                lock_file.unlink(missing_ok=True)
                logger.warning(f"🔨 Force removed stale lock file: {lock_file}")
        except Exception as e:
            logger.error(f"⚠️ Failed to remove lock file: {e}")

    def start(self):
        self._force_clear_lock()

        co = ChromiumOptions()
        # 使用系统安装的 Chromium
        co.set_browser_path("/usr/bin/chromium")
        co.set_user_data_path(str(self.config.USER_DATA_DIR))
        
        # 调试与沙盒设置
        co.set_argument('--remote-debugging-address=0.0.0.0')
        co.set_argument('--remote-debugging-port=9222')
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-gpu')
        co.set_argument('--disable-dev-shm-usage') 
        co.set_argument('--disable-session-crashed-bubble')
        
        # --- [核心修复] 解决 Docker 下 Session 易丢失/过期问题 ---
        # 1. 禁用系统密钥环，强制使用基础存储（解决解密失败导致 Cookie 被丢弃）
        co.set_argument('--password-store=basic') 
        # 2. 强制使用默认 Profile，防止意外生成临时 Profile
        co.set_argument('--profile-directory=Default')
        
        co.headless(False)

        # --- 代理隔离逻辑 ---
        if self.config.PROXY:
            logger.info(f"🌐 Applying Custom Proxy: {self.config.PROXY}")
            co.set_proxy(self.config.PROXY)
        else:
            logger.info("🛡️ No Proxy configured. Forcing Direct Connection.")
            co.set_argument('--no-proxy-server')

        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"🚦 Starting Chromium (Attempt {attempt+1}/{max_retries})...")
                self.page = ChromiumPage(addr_or_opts=co)
                time.sleep(3)
                self._inject_stealth_scripts()
                logger.success("🚀 Browser started successfully!")
                return self.page
                
            except Exception as e:
                logger.warning(f"⚠️ Browser start failed on attempt {attempt+1}: {e}")
                try:
                    self.page.quit() 
                except: 
                    pass
                time.sleep(5)
                
                if attempt == max_retries - 1:
                    logger.critical("🔥 All browser launch attempts failed.")
                    raise e

    def _inject_stealth_scripts(self):
        fp = self.fingerprint_data
        if not fp: return
        try:
            self.page.run_cdp('Network.setUserAgentOverride', 
                userAgent=fp.get('userAgent'), 
                platform=fp.get('platform')
            )
        except: pass
            
        vendor = fp.get('vendor', 'Google Inc. (NVIDIA)')
        renderer = fp.get('renderer', 'ANGLE (NVIDIA)')
        script = f"""
        (function() {{
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{vendor}';
                if (parameter === 37446) return '{renderer}';
                return getParameter.apply(this, arguments);
            }};
        }})();
        """
        try:
            self.page.add_init_js(script)
        except: pass

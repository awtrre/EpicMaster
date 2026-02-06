# src/core/anti_shield.py
import time
import random
from loguru import logger
from src.core.interaction import HumanActor

class ShieldBuster:
    def __init__(self, browser_mgr):
        self.page = browser_mgr.page
        self.actor = HumanActor(browser_mgr)

    def check_and_solve(self):
        try:
            # 1. 初步检查：是否在盾页面？
            if "Just a moment" not in self.page.title and not self.page.ele('text:Verifying you are human', timeout=0.1):
                return False 

            logger.warning("🛡️ Cloudflare Shield Detected!")
            
            # --- [关键修改] 等待圈圈转完，iframe 出现 ---
            logger.info("⏳ Waiting for widget initialization (Spinning)...")
            if not self._wait_for_iframe_ready(timeout=15):
                logger.error("❌ Widget failed to load (Spinning timeout).")
                # 即使超时也尝试盲打，死马当活马医
            
            # 增加额外的缓冲，确保动画完全停止
            time.sleep(2) 

            # 策略 A: 精准 Tab & Enter (CDP)
            logger.info("⌨️ Strategy A: Precision Tab & Enter (CDP)...")
            
            # 点击页面空白处聚焦
            self._cdp_click(50, 300) 
            time.sleep(0.5)
            
            # 只有一次机会，动作要稳
            self._cdp_key('Tab')
            time.sleep(0.8) # 这里的等待很重要，让焦点框移动过去
            self._cdp_key('Enter')
            
            # 提交后，等待验证结果
            logger.info("⏳ Submitted challenge, waiting for reload...")
            self.actor.wait_active(5, 8)

            if self._is_shield_gone(): 
                logger.success("✨ Shield penetrated via Keyboard!")
                return True

            # 策略 B: 备用方案
            # ... (后续保持不变，作为兜底)
            
            # 再次检查
            if self._is_shield_gone():
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"⚠️ Anti-Shield Logic Error: {e}")
            return False

    def _wait_for_iframe_ready(self, timeout):
        """
        死循环等待，直到找到 Cloudflare 的 iframe
        这对应 '等待圈圈转完' 的过程
        """
        start = time.time()
        while time.time() - start < timeout:
            iframe = self._find_turnstile_iframe()
            if iframe:
                # 找到了！但还要确保它有尺寸（不是隐藏的）
                if iframe.rect.size != (0, 0):
                    logger.info("👁️ Turnstile Widget Visible!")
                    return True
            time.sleep(1)
        return False

    def _is_shield_gone(self):
        return "Just a moment" not in self.page.title

    def _find_turnstile_iframe(self):
        try:
            for iframe in self.page.eles('tag:iframe'):
                src = str(iframe.attr('src'))
                if "cloudflare" in src or "turnstile" in src:
                    return iframe
        except: pass
        return None

    def _cdp_click(self, x, y):
        try:
            self.page.run_cdp('Input.dispatchMouseEvent', type='mousePressed', x=x, y=y, button='left', clickCount=1)
            time.sleep(0.08)
            self.page.run_cdp('Input.dispatchMouseEvent', type='mouseReleased', x=x, y=y, button='left', clickCount=1)
        except: pass

    def _cdp_key(self, key_name):
        try:
            self.page.run_cdp('Input.dispatchKeyEvent', type='rawKeyDown', key=key_name)
            time.sleep(0.1)
            self.page.run_cdp('Input.dispatchKeyEvent', type='keyUp', key=key_name)
        except: pass

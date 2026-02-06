# src/core/interaction.py
import time
import random
import math
from loguru import logger
from DrissionPage.common import Actions

class HumanActor:
    def __init__(self, browser_mgr):
        self.page = browser_mgr.page
        self.ac = Actions(self.page)

    def wait_page_stable(self, min_seconds=3, max_seconds=6):
        """
        【新增】全能页面稳定等待
        1. 等待 document.readyState == complete
        2. 额外等待一段随机时间让动态脚本执行
        """
        logger.debug("⚓ Waiting for page stability...")
        
        # 1. 硬性等待：确保 DOM 已经就绪
        try:
            self.page.wait.doc_loaded(timeout=10)
        except:
            pass # 超时也不要崩，继续往下走

        # 2. 动态等待：让 JS 跑一会儿
        self.wait_active(min_seconds, max_seconds)
        
        # 3. 简单的鼠标晃动，告诉页面"我是活人"
        self._move_shiver()

    # ==========================
    # 基础动作单元 (保持不变)
    # ==========================

    def _move_shiver(self, duration=0.5):
        end_time = time.time() + duration
        while time.time() < end_time:
            x = random.randint(-3, 3)
            y = random.randint(-3, 3)
            self.ac.move(offset_x=x, offset_y=y, duration=0.1)
            time.sleep(random.uniform(0.05, 0.1))

    def _move_circle(self, duration=1.0):
        center_x, center_y = 0, 0 
        radius = random.randint(30, 80)
        steps = random.randint(10, 20)
        for i in range(steps):
            angle = 2 * math.pi * i / steps
            x = int(radius * math.cos(angle))
            y = int(radius * math.sin(angle))
            self.ac.move(offset_x=random.randint(-10, 10), offset_y=random.randint(-10, 10), duration=duration/steps)

    def _move_reading(self, duration=1.0):
        steps = int(duration / 0.2)
        for _ in range(steps):
            x = random.randint(10, 50) * random.choice([1, -1]) 
            y = random.randint(-5, 5) 
            self.ac.move(offset_x=x, offset_y=y, duration=0.2)

    def _move_park(self, duration=1.0):
        self.ac.move(offset_x=random.randint(100, 300), offset_y=random.randint(-50, 50), duration=0.5)
        remaining = duration - 0.5
        if remaining > 0: time.sleep(remaining)

    def _scroll_nervous(self, duration=1.0):
        self.page.scroll.down(random.randint(100, 300))
        time.sleep(duration * 0.3)
        if random.random() < 0.5:
            self.page.scroll.up(random.randint(20, 100))
        time.sleep(duration * 0.3)

    def wait_active(self, seconds_min, seconds_max=None):
        if seconds_max is None:
            total_time = seconds_min
        else:
            total_time = random.uniform(seconds_min, seconds_max)

        logger.debug(f"🎭 Acting idle for {total_time:.2f}s...")
        start_time = time.time()
        
        actions = [
            (self._move_shiver, 0.2), 
            (self._move_reading, 0.4), 
            (self._move_circle, 0.1), 
            (self._scroll_nervous, 0.3) 
        ]

        while (time.time() - start_time) < total_time:
            remaining = total_time - (time.time() - start_time)
            if remaining < 0.2: 
                time.sleep(remaining) 
                break

            action_func, weight = random.choices(actions, weights=[w for _, w in actions], k=1)[0]
            act_duration = min(random.uniform(0.5, 1.5), remaining)
            
            try:
                action_func(duration=act_duration)
            except Exception:
                pass

    def hunt_and_click(self, selector_or_ele, description="target", rage_mode=False):
        try:
            if isinstance(selector_or_ele, str):
                ele = self.page.ele(selector_or_ele)
            else:
                ele = selector_or_ele
            
            if not ele:
                logger.debug(f"👀 Hunting for {description}...")
                self._scroll_nervous() 
                if isinstance(selector_or_ele, str):
                    ele = self.page.ele(selector_or_ele)
            
            if not ele: return False

            self.page.scroll.to_see(ele)
            self.wait_active(0.5, 1.2)

            overshoot_x = random.randint(20, 50) * random.choice([-1, 1])
            overshoot_y = random.randint(20, 50) * random.choice([-1, 1])
            
            self.ac.move_to(ele, offset_x=overshoot_x, offset_y=overshoot_y, duration=random.uniform(0.2, 0.5))
            self.ac.move_to(ele, duration=random.uniform(0.3, 0.6))
            
            if rage_mode:
                clicks = random.randint(3, 5)
                for _ in range(clicks):
                    self.ac.click()
                    time.sleep(random.uniform(0.05, 0.1))
            else:
                self.ac.click()

            self.ac.move(offset_x=random.randint(20, 50), offset_y=random.randint(10, 30))
            return True

        except Exception as e:
            logger.error(f"⚠️ Action failed: {e}")
            return False

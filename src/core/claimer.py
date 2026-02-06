# src/core/claimer.py
import time
from loguru import logger
from src.core.interaction import HumanActor
from src.core.anti_shield import ShieldBuster

class EpicClaimer:
    def __init__(self, browser_mgr, config):
        self.page = browser_mgr.page
        self.config = config
        self.actor = HumanActor(browser_mgr)
        self.buster = ShieldBuster(browser_mgr)

    def start_claiming(self):
        logger.info("🎮 Starting Claim Process...")
        failed_games = [] # 失败重试队列

        try:
            url_free = "https://store.epicgames.com/en-US/free-games"
            self.page.get(url_free)
            
            # 1. 列表页查盾
            self.buster.check_and_solve()
            self.actor.wait_active(3, 5)

            # 2. 扫描游戏
            raw_urls = self._scan_games()
            unique_urls = list(set(raw_urls))
            logger.info(f"📋 Found {len(unique_urls)} unique games to process.")

            # === 第一轮领取 ===
            for url in unique_urls:
                # 尝试领取，如果返回 False (失败/超时)，加入重试队列
                if not self._process_single_game(url):
                    logger.warning(f"⚠️ Failed to claim {url}, adding to retry queue.")
                    failed_games.append(url)
                
                logger.info("🍵 Taking a tea break (10s)...")
                self.actor.wait_active(8, 12)

            # === 第二轮重试 (针对第一次失败的情况) ===
            if failed_games:
                logger.info(f"🔄 Retrying {len(failed_games)} failed games...")
                for url in failed_games:
                    logger.info(f"🔥 Retry attempt for: {url}")
                    # 如果重试依然失败
                    if not self._process_single_game(url):
                        logger.critical(f"🛑 Retry failed for {url}.")
                        logger.critical("✋ Stopping cleanup to preserve Shield Page for VNC.")
                        return False # 返回 False，告诉主程序不要跳转 about:blank

            return True # 全部成功或已处理完毕

        except Exception as e:
            logger.error(f"❌ Global Claim Error: {e}")
            raise e 

    def _scan_games(self):
        game_urls = []
        try:
            free_badges = self.page.eles('tag:span@@text():Free Now')
            for badge in free_badges:
                link = badge.parent('tag:a')
                if link:
                    url = link.attr('href')
                    if url: 
                        game_urls.append(url)
        except: 
            pass
        return game_urls

    def _process_single_game(self, url):
        """
        处理单个游戏领取逻辑
        Returns:
            True: 成功领取、已经在库中、或锁区无法领取（即处理完成）
            False: 遇到盾、超时、错误（需要重试）
        """
        full_url = f"https://store.epicgames.com{url}" if not url.startswith('http') else url
        logger.info(f"👉 Navigating: {full_url}")
        
        self.page.get(full_url)
        
        # 0. 初始查盾
        if self.buster.check_and_solve():
            self.actor.wait_active(3, 5)
        else:
            self.actor.wait_active(2, 4)

        # 年龄验证
        if self.page.ele('text:Continue', timeout=2):
            self.actor.hunt_and_click('text:Continue', "Age Gate")
            self.actor.wait_active(2, 3)

        logger.info("🔍 [Step 1] Scanning for 'Get' button...")

        # --- 第一步：点击 Get ---
        target_btn = None
        sidebar = self.page.ele('tag:aside', timeout=5)
        
        if sidebar:
            target_btn = sidebar.ele('tag:button@@data-testid=purchase-cta-button')
            if not target_btn:
                target_btn = sidebar.ele('tag:button@@text():Get')
        else:
            target_btn = self.page.ele('tag:button@@data-testid=purchase-cta-button')

        if not target_btn:
            if self.page.ele('text:In Library') or self.page.ele('text:Owned'):
                logger.success("✅ Game is already in Library/Owned.")
                return True # 视为成功
            logger.error("❌ 'Get' Button NOT found in Sidebar.")
            return False

        btn_text = target_btn.text.lower()
        logger.info(f"🔘 Button Found: [{btn_text}]")

        if 'get' in btn_text or 'free' in btn_text or 'purchase' in btn_text:
            logger.info("🖱️ [Step 1] Clicking 'Get'...")
            target_btn.click(by_js=True)
            
            logger.info("🛡️ Checking for shield after 'Get'...")
            self.actor.wait_active(2, 4)
            self.buster.check_and_solve()
            
            # 进入 Iframe 流程
            return self._handle_purchase_iframe()
        
        elif 'library' in btn_text or 'owned' in btn_text:
            logger.success("✅ Already in library.")
            return True
        
        elif 'unavailable' in btn_text:
            logger.warning("🚫 Unavailable in region (Main Page).")
            return True # 无法领取也是一种“完成”

        return False

    def _handle_purchase_iframe(self):
        logger.info("🛒 [Step 2] Waiting for Purchase Iframe (Active Waiting)...")
        
        # --- 忙等待循环：一边等 Iframe，一边演 ---
        iframe_ele = None
        start_time = time.time()
        max_wait = 20 # 最多等20秒
        
        while time.time() - start_time < max_wait:
            # 每次只查 0.5 秒
            iframe_ele = self.page.ele('css:iframe#webPurchaseContainer', timeout=0.5)
            if not iframe_ele:
                iframe_ele = self.page.ele('tag:iframe@@src:purchase', timeout=0.1)
            
            if iframe_ele:
                break # 找到了！
            
            # 没找到，演一下（假装在看页面加载，避免死板等待）
            self.actor.wait_active(0.5, 1.5) 
        
        if not iframe_ele:
            logger.warning("⚠️ Purchase Iframe timeout.")
            return False

        logger.info("✅ Iframe detected. Acting reading...")
        # 找到后不要马上操作，假装读取内容
        self.actor.wait_active(1.5, 3.0) 

        iframe = self.page.get_frame(iframe_ele)
        
        try:
            iframe.wait.ele('css:#purchase-app', timeout=10)
        except: pass

        # --- 锁区检测 ---
        logger.info("🚧 Checking for Region Lock...")
        self.actor.wait_active(0.5, 1.0) # 又是演
        
        blocked_msg = iframe.ele('css:.payment-blocked__msg', timeout=1)
        if not blocked_msg:
            blocked_msg = iframe.ele('xpath://h2[contains(text(),"This product is currently unavailable")]', timeout=1)

        if blocked_msg:
            err_text = blocked_msg.text
            logger.warning(f"🚫 REGION LOCKED: {err_text}")
            return True # 锁区也算处理完毕，不重试

        # --- 第二步：点击 Place Order ---
        place_btn = iframe.ele('css:button.payment-order-confirm__btn', timeout=5)
        if not place_btn:
            place_btn = iframe.ele('tag:button@@text():Place Order')

        if place_btn:
            logger.info("💳 Found 'Place Order', clicking...")
            self.actor.wait_active(1, 2)
            place_btn.click(by_js=True)
            
            # 等待 I Accept 弹窗
            logger.info("🎭 Acting nervous waiting for confirmation...")
            self.actor.wait_active(2, 4) 

            # 点击 Place Order 后也可能立刻弹盾
            self.buster.check_and_solve()
            
            # --- 第三步：点击 I Accept ---
            logger.info("📜 [Step 3] Hunting for 'I Accept'...")
            if iframe_ele.states.is_alive:
                
                # 1. 优先尝试：点击 Span 标签
                accept_ele = iframe.ele("xpath://span[normalize-space()='I Accept']", timeout=5)
                # 2. 备选尝试：点击 Button
                if not accept_ele:
                    accept_ele = iframe.ele("xpath://button[contains(@class, 'payment-confirm__btn')]", timeout=2)

                if accept_ele and accept_ele.states.is_displayed:
                    logger.info("🤝 Found 'I Accept' element, clicking...")
                    self.actor.wait_active(0.5, 1.0)
                    accept_ele.click(by_js=True)
                    
                    # --- [关键修改] 纯净等待模式 (1分钟) ---
                    # 策略：不主动查盾，只等 "Thanks"。没等到就是失败。
                    
                    logger.info("🤞 Waiting for 'Thanks' message (Max 120s acting)...")
                    
                    wait_start = time.time()
                    wait_timeout = 60 # 1分钟，给足时间
                    
                    while time.time() - wait_start < wait_timeout:
                        # 1. 检查成功标志 (包含用户指定的高精度 XPath)
                        if self._check_success(iframe):
                            logger.success("🎉 Purchase Confirmed! (Matched Success Element)")
                            return True
                            
                        # 2. 演戏 (随机等待 1~2秒，包含鼠标微动)
                        # 这里非常重要，保持 Session 活跃，同时模拟人类在等页面刷新
                        self.actor.wait_active(1.0, 2.0)
                    
                    # 3. 超时处理
                    logger.warning("⏳ Timeout: 'Thanks' message NOT found after 120s. Assuming Failure/Shield.")
                    return False # 返回 False -> 加入重试队列

                else:
                    logger.info("ℹ️ No 'I Accept' button found (Auto-accepted or not required).")
                    return True
            else:
                logger.warning("⚠️ Iframe detached, skipping Step 3.")
                return False
        else:
            logger.warning("❌ 'Place Order' button not found.")
            return False

    def _check_success(self, iframe):
        """检查是否有感谢购买的字样"""
        try:
            # 用户指定的高精度 XPath
            if iframe.ele("xpath://span[normalize-space()='Thanks for your order!']", timeout=0.1): 
                return True
                
            # 兼容旧版本检查
            if iframe.ele('text:Thank you', timeout=0.1): return True
            if iframe.ele('text:Email receipt', timeout=0.1): return True
            return False
        except: return False

    def _detect_post_click_shield(self, iframe):
        """
        保留此方法以备不时之需，但当前策略中不再主动调用。
        """
        try:
            if iframe.ele('tag:iframe@@src:hcaptcha', timeout=0.5): return True
            if iframe.ele('tag:iframe@@src:arkoselabs', timeout=0.5): return True
            if iframe.ele('css:#challenge-container', timeout=0.5): return True
            if iframe.ele('text:Please solve this puzzle', timeout=0.1): return True
            if self.page.ele('tag:iframe@@src:arkoselabs', timeout=0.5): return True
            return False
        except: return False

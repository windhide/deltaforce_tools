import threading
import time
import keyboard
import mouse

class AutoClicker:
    def __init__(self):
        # 控制左键点击线程
        self.clicking = threading.Event()
        self.click_thread = None
        self.click_lock = threading.Lock()  # 添加锁以防止竞态条件
        self._is_clicking_active = False # 新增标志，表示点击功能是否真正活跃

        # 控制 Alt+D 发送线程
        self.sending_alt_d = threading.Event()
        self.alt_d_thread = None
        self.alt_d_lock = threading.Lock()  # 添加锁以防止竞态条件
        self._is_alt_d_active = False # 新增标志，表示Alt+D功能是否真正活跃

        self.click_interval = 0.05  # 点击间隔秒

    # ===== 左键点击相关 =====
    def start_clicking(self):
        with self.click_lock:
            if self._is_clicking_active: # 检查新的活跃标志
                print("⚠️ 点击已在进行中，忽略重复启动请求")
                return
            
            self.clicking.set()
            self._is_clicking_active = True # 设置活跃标志
            
            # 确保线程不存在或已停止时才创建并启动新线程
            if self.click_thread is None or not self.click_thread.is_alive():
                self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
                self.click_thread.start()
                print("✅ 开始疯狂点击")
            else:
                print("⚠️ 点击线程已存在且活跃，无需重新启动")

    def stop_clicking(self):
        with self.click_lock:
            # 不再检查 self.clicking.is_set()，直接尝试清除并设置不活跃
            if not self._is_clicking_active: # 检查新的活跃标志
                print("⚠️ 点击未在进行中，忽略停止请求")
                return

            self.clicking.clear()
            self._is_clicking_active = False # 清除活跃标志
            print("✅ 停止疯狂点击")

    def click_loop(self):
        try:
            while self.clicking.is_set():
                mouse.click('left')
                time.sleep(self.click_interval)
        except Exception as e:
            print(f"❌ 点击循环中发生错误: {e}")
        finally:
            print("🔄 点击循环已结束")
            with self.click_lock:
                self._is_clicking_active = False # 确保循环结束时标志被清除

    # ===== Alt+D 发送相关 =====
    def start_alt_d(self):
        with self.alt_d_lock:
            if self._is_alt_d_active: # 检查新的活跃标志
                print("⚠️ Alt+D 发送已在进行中，忽略重复启动请求")
                return
            
            self.sending_alt_d.set()
            self._is_alt_d_active = True # 设置活跃标志
            
            # 确保线程不存在或已停止时才创建并启动新线程
            if self.alt_d_thread is None or not self.alt_d_thread.is_alive():
                self.alt_d_thread = threading.Thread(target=self.alt_d_loop, daemon=True)
                self.alt_d_thread.start()
                print("✅ 开始发送 Alt+D")
            else:
                print("⚠️ Alt+D 线程已存在且活跃，无需重新启动")

    def stop_alt_d(self):
        with self.alt_d_lock:
            # 不再检查 self.sending_alt_d.is_set()，直接尝试清除并设置不活跃
            if not self._is_alt_d_active: # 检查新的活跃标志
                print("⚠️ Alt+D 发送未在进行中，忽略停止请求")
                return

            self.sending_alt_d.clear()
            self._is_alt_d_active = False # 清除活跃标志
            print("✅ 停止发送 Alt+D")

    def alt_d_loop(self):
        try:
            while self.sending_alt_d.is_set():
                keyboard.press_and_release('alt+d')
                time.sleep(self.click_interval)
        except Exception as e:
            print(f"❌ Alt+D 循环中发生错误: {e}")
        finally:
            print("🔄 Alt+D 循环已结束")
            with self.alt_d_lock:
                self._is_alt_d_active = False # 确保循环结束时标志被清除


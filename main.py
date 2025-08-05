import customtkinter as ctk
import tkinter as tk
import threading
import time

import cv2
import keyboard
import mouse
import os
import datetime
import mss
import glob
import numpy as np

import MORSE_TOOLS

last_screenshot_path = None  # 全局变量，保存上一个截图路径

def stop_anticheat_service():
    os.system("sc stop AntiCheatExpert")

def screenshot_game():
    global last_screenshot_path
    if last_screenshot_path and os.path.exists(last_screenshot_path):
        os.remove(last_screenshot_path)
        print(f"已删除上一张截图：{last_screenshot_path}")

    with mss.mss() as sct:
        monitor = sct.monitors[1]  # 主屏幕
        screenshot = sct.grab(monitor)
        img = mss.tools.to_png(screenshot.rgb, screenshot.size)
        sct_img = sct.grab(monitor)
        img2 = np.array(sct_img)

        # 转换为灰度图（只保留亮度）
        gray = cv2.cvtColor(img2, cv2.COLOR_BGRA2GRAY)
        morse_codes, digits = MORSE_TOOLS.extract_three_groups_and_decode(gray, method="simple_cluster")
        print("\n最终结果：")
        print("摩斯码：", morse_codes)
        print("数字：", digits)

        filename = f"screenshot_delta_force_tools_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        with open(filename, "wb") as f:
            f.write(img)
        last_screenshot_path = filename
        print(f"截图保存为 {filename}")

class AutoClicker:
    def __init__(self):
        self.clicking = False
        self.thread = None
        self.click_interval = 0.05  # 初始点击间隔0.05秒

    def start_clicking(self):
        if self.clicking:
            return
        self.clicking = True
        self.thread = threading.Thread(target=self.click_loop, daemon=True)
        self.thread.start()
        print("开始疯狂点击")

    def stop_clicking(self):
        self.clicking = False
        print("停止疯狂点击")

    def click_loop(self):
        while self.clicking:
            mouse.click('left')
            print("点击一次")
            time.sleep(self.click_interval)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("三角洲行动辅助工具")
        self.geometry("480x320")
        self.resizable(False, False)

        self.screenshot_enabled = tk.BooleanVar(value=False)
        self.shortcut_key = 'right'

        self.autoclicker = AutoClicker()
        self.autoclicker_enabled = tk.BooleanVar(value=False)

        self.build_ui()
        self.register_shortcut(self.shortcut_key)

        threading.Thread(target=self.mouse_listener_thread, daemon=True).start()

    def build_ui(self):
        padding = {'padx': 10, 'pady': 5}

        status_frame = ctk.CTkFrame(self)
        status_frame.pack(fill='x', **padding)
        self.service_switch = ctk.CTkSwitch(status_frame, text="关闭游戏服务 (AntiCheatExpert)",
                                            command=self.toggle_service)
        self.service_switch.pack(side='left', padx=5)

        screenshot_frame = ctk.CTkFrame(self)
        screenshot_frame.pack(fill='x', **padding)

        self.screenshot_switch = ctk.CTkSwitch(screenshot_frame, text="", variable=self.screenshot_enabled)
        self.screenshot_switch.pack(side='left', padx=5)

        screenshot_label = ctk.CTkLabel(screenshot_frame, text="截图功能")
        screenshot_label.pack(side='left', padx=5)

        self.shortcut_label = ctk.CTkLabel(screenshot_frame, text=f"快捷键：{self.shortcut_key}")
        self.shortcut_label.pack(side='right', padx=5)

        shortcut_btn = ctk.CTkButton(screenshot_frame, text="修改快捷键", width=120, command=self.change_shortcut)
        shortcut_btn.pack(side='right', padx=5)

        # 自动点击开关
        self.autoclicker_switch = ctk.CTkSwitch(self,
                                                text="抢物品功能：按鼠标侧键（ButtonX，监听'x'）自动点击左键",
                                                variable=self.autoclicker_enabled,
                                                command=self.on_autoclicker_toggle)
        self.autoclicker_switch.pack(fill='x', **padding)

        # 滑动条调节点击速度
        slider_frame = ctk.CTkFrame(self)
        slider_frame.pack(fill='x', **padding)

        speed_label = ctk.CTkLabel(slider_frame, text="点击间隔（秒，数值越小点击越快）")
        speed_label.pack(anchor='w', padx=5)

        self.speed_slider = ctk.CTkSlider(slider_frame, from_=0.05, to=0.1, number_of_steps=50,
                                         command=self.on_speed_change)
        self.speed_slider.set(self.autoclicker.click_interval)
        self.speed_slider.pack(fill='x', padx=10)

        self.speed_value_label = ctk.CTkLabel(slider_frame, text=f"{self.autoclicker.click_interval:.3f} 秒")
        self.speed_value_label.pack(anchor='e', padx=10)

        # 初始禁用滑动条（自动点击默认关闭）
        self.speed_slider.configure(state='disabled')

        quit_btn = ctk.CTkButton(self, text="退出程序", command=self.quit)
        quit_btn.pack(pady=10)

    def on_autoclicker_toggle(self):
        enabled = self.autoclicker_enabled.get()
        if enabled:
            print("自动点击已开启")
            self.speed_slider.configure(state='normal')
        else:
            print("自动点击已关闭")
            self.speed_slider.configure(state='disabled')
            self.autoclicker.stop_clicking()

    def on_speed_change(self, value):
        interval = float(value)
        self.autoclicker.click_interval = interval
        self.speed_value_label.configure(text=f"{interval:.3f} 秒")
        print(f"点击间隔调整为 {interval:.3f} 秒")

    def toggle_service(self):
        if self.service_switch.get():
            threading.Thread(target=stop_anticheat_service, daemon=True).start()

    def register_shortcut(self, key):
        keyboard.unhook_all()
        keyboard.add_hotkey(key, lambda: self.on_screenshot_trigger())

    def change_shortcut(self):
        win = tk.Toplevel(self)
        win.title("按下新快捷键")
        ctk.CTkLabel(win, text="请按下新的快捷键...").pack(padx=10, pady=10)

        def on_key(e):
            self.shortcut_key = e.name
            self.shortcut_label.configure(text=f"快捷键：{self.shortcut_key}")
            self.register_shortcut(self.shortcut_key)
            keyboard.unhook_all()
            win.destroy()

        keyboard.hook(on_key)

    def on_screenshot_trigger(self):
        if self.screenshot_enabled.get():
            threading.Thread(target=screenshot_game, daemon=True).start()

    def mouse_listener_thread(self):
        def on_mouse_event(event):
            if hasattr(event, "event_type") and hasattr(event, "button"):
                # print(f"事件: {event.event_type}, 按键: {event.button}")
                if not self.autoclicker_enabled.get():
                    return
                if event.event_type == "down" and event.button == "x":
                    self.autoclicker.start_clicking()
                elif event.event_type == "up" and event.button == "x":
                    self.autoclicker.stop_clicking()

        mouse.hook(on_mouse_event)
        mouse.wait()

    def quit(self):
        self.cleanup_screenshots()
        self.destroy()

    def cleanup_screenshots(self):
        count = 0
        for file in glob.glob("screenshot_delta_force_tools_*.png"):
            try:
                os.remove(file)
                count += 1
            except Exception as e:
                print(f"无法删除 {file}：{e}")
        print(f"退出前共删除截图文件：{count} 张")

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()

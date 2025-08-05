import time

import customtkinter as ctk
import tkinter as tk
import threading
import keyboard
import mouse
import os
import MORSE_TOOLS
from AUTO_TOOLS import AutoClicker

last_screenshot_path = None  # 全局变量，保存上一个截图路径
def stop_anticheat_service():
    os.system("sc stop AntiCheatExpert")


def on_speed_change(self, value):
    interval = float(value) / 100.0  # 5 -> 0.05秒, 10 -> 0.10秒
    self.autoclicker.click_interval = interval
    self.speed_value_label.configure(text=f"{interval:.3f} 秒")
    print(f"点击间隔调整为 {interval:.3f} 秒")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.speed_value_label = None
        self.speed_slider = None
        self.autoclicker_switch = None
        self.alt_d_switch = None
        self.shortcut_label = None
        self.screenshot_switch = None
        self.service_switch = None
        self.title("三角洲行动辅助工具")
        self.geometry("480x280")
        self.resizable(False, False)

        self.screenshot_enabled = tk.BooleanVar(value=False)
        self.shortcut_key = 'right'

        self.autoclicker = AutoClicker()
        self.autoclicker_enabled = tk.BooleanVar(value=False)

        self.send_alt_d_enabled = tk.BooleanVar(value=False)
        self.sending_alt_d = False

        self.build_ui()
        self.register_shortcut(self.shortcut_key)

        threading.Thread(target=self.mouse_listener_thread, daemon=True).start()

    def build_ui(self):
        padding = {'padx': 10, 'pady': 5}

        status_frame = ctk.CTkFrame(self)
        status_frame.pack(fill='x', **padding)
        self.service_switch = ctk.CTkSwitch(status_frame, text="关闭ACE服务(AntiCheatExpert)",
                                            command=self.toggle_service)
        self.service_switch.pack(side='left', padx=5)

        screenshot_frame = ctk.CTkFrame(self)
        screenshot_frame.pack(fill='x', **padding)

        self.screenshot_switch = ctk.CTkSwitch(screenshot_frame, text="自动识别电脑密码输入", variable=self.screenshot_enabled)
        self.screenshot_switch.pack(side='left', padx=5)

        self.shortcut_label = ctk.CTkLabel(screenshot_frame, text=f"快捷键：{self.shortcut_key}")
        self.shortcut_label.pack(side='right', padx=5)

        shortcut_btn = ctk.CTkButton(screenshot_frame, text="修改快捷键", width=120, command=self.change_shortcut)
        shortcut_btn.pack(side='right', padx=5)

        # ALT+D 开关
        alt_d_frame = ctk.CTkFrame(self)
        alt_d_frame.pack(fill='x', **padding)

        self.alt_d_switch = ctk.CTkSwitch(
            alt_d_frame,
            text="丢东西👉长按鼠标上侧键不断发送 Alt + D",
            variable=self.send_alt_d_enabled
        )
        self.alt_d_switch.pack(side='left', padx=5)

        # 自动点击功能区域
        autoclicker_frame = ctk.CTkFrame(self)
        autoclicker_frame.pack(fill='x', **padding)

        self.autoclicker_switch = ctk.CTkSwitch(autoclicker_frame,
                                                text="抢物品👉按鼠标下侧键自动点击左键",
                                                variable=self.autoclicker_enabled,
                                                command=self.on_autoclicker_toggle,)
        self.autoclicker_switch.pack(side='left', padx=5)

        # 点击速度调节
        slider_frame = ctk.CTkFrame(self)
        slider_frame.pack(fill='x', **padding)

        speed_label = ctk.CTkLabel(slider_frame, text="间隔（秒，数值越小点击越快）")
        speed_label.pack(anchor='w', padx=5)

        self.speed_slider = ctk.CTkSlider(slider_frame, from_=0.05, to=0.1, number_of_steps=50,
                                          command=self.on_speed_change)
        self.speed_slider.set(int(self.autoclicker.click_interval * 100))
        self.speed_slider.pack(fill='x', padx=10)

        self.speed_value_label = ctk.CTkLabel(slider_frame, text=f"{self.autoclicker.click_interval:.3f} 秒")
        self.speed_value_label.pack(anchor='e', padx=10)

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
        # 移除旧的 hook
        if hasattr(self, '_keyboard_hook_id') and self._keyboard_hook_id:
            try:
                keyboard.unhook(self._keyboard_hook_id)
                print(f"[DEBUG] Successfully unhooked previous key: {key}")
            except Exception as e:
                print(f"[DEBUG] Error unhooking previous key: {e}")

        def handler(e):
            if e.event_type == 'down' and e.name == key:
                print(f"[DEBUG] Key '{key}' pressed, triggering screenshot")
                self.on_screenshot_trigger()

        try:
            self._keyboard_hook_id = keyboard.hook(handler)
            print(f"[DEBUG] Successfully registered hook for key: {key}")
        except Exception as e:
            print(f"[DEBUG] Error registering hook for key '{key}': {e}")

    def change_shortcut(self):
        win = tk.Toplevel(self)
        win.title("按下新快捷键")
        ctk.CTkLabel(win, text="请按下新的快捷键...").pack(padx=10, pady=10)

        def on_key(e):
            if e.event_type == 'down': # 只处理按键按下事件
                self.shortcut_key = e.name
                self.shortcut_label.configure(text=f"快捷键：{self.shortcut_key}")
                self.register_shortcut(self.shortcut_key)
                try:
                    keyboard.unhook(temp_hook_id)  # 正确卸载这个hook
                    print(f"[DEBUG] Successfully unhooked temporary hook")
                except Exception as e:
                    print(f"[DEBUG] Error unhooking temporary hook: {e}")
                win.destroy()

        try:
            temp_hook_id = keyboard.hook(on_key)
            print(f"[DEBUG] Temporary hook registered for shortcut change")
        except Exception as e:
            print(f"[DEBUG] Error registering temporary hook: {e}")

    def on_screenshot_trigger(self):
        if self.screenshot_enabled.get():
            print("[DEBUG] Screenshot trigger activated, starting thread")
            threading.Thread(target=MORSE_TOOLS.screenshot_game_and_sendCode, daemon=True).start()
        else:
            print("[DEBUG] Screenshot is disabled, ignoring trigger")

    def mouse_listener_thread(self):
        import time

        def on_mouse_event(event):
            try:
                # 先过滤无效事件（没有 event_type 或 button）
                if not (hasattr(event, 'event_type') and hasattr(event, 'button')):
                    return

                print(f"[DEBUG] Mouse event: {event.event_type} {event.button}")

                if event.event_type == 'down' and event.button == 'x':
                    if self.autoclicker_enabled.get():
                        print("[DEBUG] Mouse x button down, starting clicking")
                        self.autoclicker.start_clicking()

                elif event.event_type == 'up' and event.button == 'x':
                    # 只有在点击功能真正活跃时才尝试停止
                    if self.autoclicker._is_clicking_active:
                        print("[DEBUG] Mouse x button up, stopping clicking")
                        self.autoclicker.stop_clicking()
                    else:
                        print("[DEBUG] Mouse x button up, but clicking not active, ignoring")

                elif event.event_type == 'down' and event.button == 'x2':
                    if self.send_alt_d_enabled.get():
                        print("[DEBUG] Mouse x2 button down, starting alt+d")
                        self.autoclicker.start_alt_d()

                elif event.event_type == 'up' and event.button == 'x2':
                    # 只有在Alt+D功能真正活跃时才尝试停止
                    if self.autoclicker._is_alt_d_active:
                        print("[DEBUG] Mouse x2 button up, stopping alt+d")
                        self.autoclicker.stop_alt_d()
                    else:
                        print("[DEBUG] Mouse x2 button up, but alt+d not active, ignoring")

            except Exception as e:
                print(f"[DEBUG] Error in mouse event handler: {e}")

        try:
            print("[DEBUG] Starting mouse listener...")
            mouse.hook(on_mouse_event)
            mouse.wait()
        except Exception as e:
            print(f"[DEBUG] Error in mouse listener thread: {e}")


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()


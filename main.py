import base64
import sys
import time

import customtkinter as ctk
import tkinter as tk
import threading
import keyboard
import mouse # 雖然目前沒有直接使用mouse庫，但保留以防未來擴展
import os
import ctypes
import MORSE_TOOLS
from AUTO_TOOLS import AutoClicker
from logo import img

last_screenshot_path = None  # 全局变量，保存上一个截图路径

def stop_anticheat_service():
    try:
        # 尝试停止服务，如果不是管理员或服务不存在会抛出异常
        if ctypes.windll.shell32.IsUserAnAdmin():
            os.system("sc stop AntiCheatExpert")
            print("ACE服务已尝试停止。")
        else:
            print("非管理员权限，无法停止ACE服务。请以管理员身份运行程序。")
    except Exception as e:
        print(f"停止ACE服务时发生错误: {e}")


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
        
        base_title = "Delta行动小工具"
        if self.is_admin():
            self.title(f"{base_title} > admin")
        else:
            self.title(base_title)
        self.geometry("480x480")
        self.resizable(False, False)

        icon = open("icon.ico", "wb+")
        icon.write(base64.b64decode(img))
        icon.close()
        self.iconbitmap("icon.ico")
        os.remove("icon.ico")

        self.screenshot_enabled = tk.BooleanVar(value=False)
        # 恢復用戶原始的快捷鍵設置方式，並在UI上顯示
        self.shortcut_key = 'right' # 默認為右方向鍵

        self.autoclicker = AutoClicker()
        self.autoclicker_enabled = tk.BooleanVar(value=False)

        self.send_alt_d_enabled = tk.BooleanVar(value=False)
        self.sending_alt_d = False # 恢復原始的狀態變量

        self.show_debug_window_enabled = tk.BooleanVar(value=False)

        self.build_ui()

        # 啟動全局鍵盤監聽器
        threading.Thread(target=self.global_keyboard_listener, daemon=True).start()

    def build_ui(self):
        padding = {"padx": 10, "pady": 5}

        status_frame = ctk.CTkFrame(self)
        status_frame.pack(fill="x", **padding)
        self.service_switch = ctk.CTkSwitch(status_frame, text="关闭ACE服务(AntiCheatExpert)",
                                            command=self.toggle_service)
        self.service_switch.pack(side="left", padx=5)

        self.debug_switch = ctk.CTkSwitch(status_frame, text="调试模式", command=self.toggle_debug_mode)
        self.debug_switch.pack(side="right", padx=11)

        screenshot_frame = ctk.CTkFrame(self)
        screenshot_frame.pack(fill="x", **padding)

        self.screenshot_switch = ctk.CTkSwitch(screenshot_frame, text="自动识别电脑密码输入", variable=self.screenshot_enabled)
        self.screenshot_switch.pack(side="left", padx=5)

        # 顯示當前快捷鍵
        self.shortcut_label = ctk.CTkLabel(screenshot_frame, text=f"快捷键：{self.shortcut_key}")
        self.shortcut_label.pack(side="right", padx=5)

        shortcut_btn = ctk.CTkButton(screenshot_frame, text="修改快捷键", width=120, command=self.change_shortcut)
        shortcut_btn.pack(side="right", padx=5)

        # ALT+D 开关
        alt_d_frame = ctk.CTkFrame(self)
        alt_d_frame.pack(fill="x", **padding)

        self.alt_d_switch = ctk.CTkSwitch(
            alt_d_frame,
            text="丢东西👉长按 ` 键不断发送 Alt + D",
            variable=self.send_alt_d_enabled
        )
        self.alt_d_switch.pack(side="left", padx=5)

        # 自动点击功能区域
        autoclicker_frame = ctk.CTkFrame(self)
        autoclicker_frame.pack(fill="x", **padding)

        self.autoclicker_switch = ctk.CTkSwitch(autoclicker_frame,
                                                text="连点器👉长按F超过0.5秒就不停的按F",
                                                variable=self.autoclicker_enabled,
                                                command=self.on_autoclicker_toggle,)
        self.autoclicker_switch.pack(side="left", padx=5)

        # 点击速度调节
        self.slider_frame = ctk.CTkFrame(self)
        self.slider_frame.pack(fill="x", **padding)

        speed_label = ctk.CTkLabel(self.slider_frame, text="间隔（秒，数值越小点击越快）")
        speed_label.pack(anchor="w", padx=5)

        self.speed_slider = ctk.CTkSlider(self.slider_frame, from_=0.05, to=0.1, number_of_steps=50,
                                          command=self.on_speed_change)
        # 根據原始程式碼，這裡應該設置為 autoclicker.click_interval * 100
        self.speed_slider.set(self.autoclicker.click_interval * 100)
        self.speed_slider.pack(fill="x", padx=10)

        self.speed_value_label = ctk.CTkLabel(self.slider_frame, text=f"{self.autoclicker.click_interval:.3f} 秒")
        self.speed_value_label.pack(anchor="e", padx=10)

        self.speed_slider.configure(state="disabled")

        # 摩斯码识别区域配置
        self.morse_config_frame = ctk.CTkFrame(self)

        morse_label = ctk.CTkLabel(self.morse_config_frame, text="摩斯码识别区域配置：")
        morse_label.pack(anchor="w", padx=5)

        # 使用 grid 布局来对齐标签和输入框
        grid_frame = ctk.CTkFrame(self.morse_config_frame)
        grid_frame.pack(fill="x", padx=5, pady=5)

        self.morse_entries = {}
        config_fields = {
            "top": "上边界 (top)", "bottom": "下边界 (bottom)",
            "group_width": "区域宽度", "spacing": "区域间隔",
            "group1_x": "起始位置 (x)"
        }
        default_values = {"top": 510, "bottom": 570, "group_width": 200, "spacing": 65, "group1_x": 700}

        for i, (field, text) in enumerate(config_fields.items()):
            label = ctk.CTkLabel(grid_frame, text=text)
            label.grid(row=i, column=0, padx=5, pady=2, sticky="w")
            entry = ctk.CTkEntry(grid_frame, width=100)
            entry.insert(0, str(default_values[field]))
            entry.grid(row=i, column=1, padx=5, pady=2, sticky="w")
            self.morse_entries[field] = entry

        self.show_debug_window_switch = ctk.CTkSwitch(self.morse_config_frame, text="显示调试窗口", variable=self.show_debug_window_enabled)
        self.show_debug_window_switch.pack(anchor="w", padx=5, pady=5)

        quit_btn = ctk.CTkButton(self, text="退出程序", command=self.on_closing)
        quit_btn.pack(pady=10)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 默认隐藏配置区域
        self.toggle_debug_mode() # 初始化时调用一次以保证状态正确

    def on_closing(self):
        print("程序退出，卸载键盘钩子...")
        keyboard.unhook_all()
        self.destroy()

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def toggle_debug_mode(self):
        if self.debug_switch.get():
            # 将配置框显示在滑块框的下方
            self.morse_config_frame.pack(fill="x", padx=10, pady=5, after=self.slider_frame)
            self.geometry("480x540")  # 展开后的高度
        else:
            self.morse_config_frame.pack_forget()
            self.geometry("480x280")  # 收起后的高度

    def on_autoclicker_toggle(self):
        enabled = self.autoclicker_enabled.get()
        if enabled:
            print("自动点击已开启")
            self.speed_slider.configure(state="normal")
        else:
            print("自动点击已关闭")
            self.speed_slider.configure(state="disabled")

    def on_speed_change(self, value):
        # 這裡的value是slider的原始值，需要轉換為秒
        interval = float(value) / 100.0 # 根據原始程式碼，slider的值需要除以100
        self.autoclicker.click_interval = interval
        self.speed_value_label.configure(text=f"{interval:.3f} 秒")
        print(f"点击间隔调整为 {interval:.3f} 秒")

    def toggle_service(self):
        if self.service_switch.get():
            threading.Thread(target=stop_anticheat_service, daemon=True).start()

    def change_shortcut(self):
        win = ctk.CTkToplevel(self)
        win.title("设置新快捷键")
        win.geometry("300x100")
        win.transient(self)  # 保持在顶层
        win.grab_set()  # 模态窗口
        label = ctk.CTkLabel(win, text="请按下新的快捷键...")
        label.pack(padx=20, pady=10)

        def on_key_press(e):
            if e.event_type == 'down':
                # 排除修饰键和常用功能键
                if e.name not in ['alt', 'ctrl', 'shift', 'cmd', 'caps lock', 'tab', 'enter']:
                    self.shortcut_key = e.name
                    self.shortcut_label.configure(text=f"快捷键：{self.shortcut_key}")
                    print(f"[DEBUG] Shortcut key changed to: {self.shortcut_key}")
                    keyboard.unhook(on_key_press)
                    win.destroy()
                else:
                    label.configure(text=f"'{e.name}' 不能作为快捷键，请重试")

        keyboard.hook(on_key_press)
        self.wait_window(win)  # 等待窗口销毁


    def on_screenshot_trigger(self):
        if self.screenshot_enabled.get():
            try:
                # 从输入框获取配置，并转换为整数
                config = {key: int(entry.get()) for key, entry in self.morse_entries.items()}
                config['debug'] = self.show_debug_window_enabled.get()
                print(f"[DEBUG] Screenshot trigger activated with config: {config}")
                # 使用 lambda 来传递参数
                threading.Thread(target=lambda: MORSE_TOOLS.screenshot_game_and_sendCode(morse_config=config),
                                 daemon=True).start()
            except ValueError:
                print("❌ 错误: 摩斯码识别区域配置中包含了无效的非整数值。")
                # 可以在这里弹出一个错误提示框
                tk.messagebox.showerror("输入错误", "摩斯码识别区域配置中只能输入整数！")
            except Exception as e:
                print(f"❌ 触发截图时发生未知错误: {e}")
        else:
            print("[DEBUG] Screenshot is disabled, ignoring trigger")

    def global_keyboard_listener(self):
        f_key_press_time = None
        f_key_thread = None

        def f_press_handler():
            nonlocal f_key_press_time
            f_key_press_time = time.time()
            # 確保只有在按鍵被按住時才進入循環
            while keyboard.is_pressed('f'):
                if self.autoclicker_enabled.get() and time.time() - f_key_press_time > 0.5:
                    # 只有當autoclicker未啟動時才啟動，避免重複啟動線程
                    if not self.autoclicker._is_clicking_active:
                        self.autoclicker.start_clicking()
                time.sleep(0.01) # 短暫延遲，避免CPU佔用過高
            # 循環結束（意味著按鍵被鬆開），停止點擊
            if self.autoclicker._is_clicking_active:
                self.autoclicker.stop_clicking()

        def on_key(e):
            nonlocal f_key_press_time, f_key_thread
            
            # 摩斯密碼識別快捷鍵 (right)
            # 確保每次按下都觸發，並且只在按下時觸發
            if self.screenshot_enabled.get() and e.event_type == 'down' and e.name == self.shortcut_key:
                print(f"[DEBUG] Key '{self.shortcut_key}' pressed, triggering screenshot")
                # 使用 self.after 將 UI 更新和耗時操作放到主線程或新線程中
                # 這裡直接調用 on_screenshot_trigger，它內部會創建新線程處理耗時操作
                self.on_screenshot_trigger()

            # Alt+D 發送快捷鍵 (`)
            if self.send_alt_d_enabled.get() and e.name == '`':
                if e.event_type == 'down':
                    # 只有當autoclicker未啟動時才啟動，避免重複啟動線程
                    if not self.autoclicker._is_alt_d_active:
                        print("[DEBUG] ` key down, starting alt+d")
                        self.autoclicker.start_alt_d()
                elif e.event_type == 'up':
                    # 只有當autoclicker正在運行時才停止
                    if self.autoclicker._is_alt_d_active:
                        print("[DEBUG] ` key up, stopping alt+d")
                        self.autoclicker.stop_alt_d()
            
            # F 鍵連點器快捷鍵
            if self.autoclicker_enabled.get() and e.name == 'f':
                if e.event_type == 'down':
                    # 只有當f_key_thread不存在或已停止時才創建並啟動新線程
                    if f_key_thread is None or not f_key_thread.is_alive():
                        f_key_thread = threading.Thread(target=f_press_handler, daemon=True)
                        f_key_thread.start()

        keyboard.hook(on_key)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()



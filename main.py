import base64
import customtkinter as ctk
import tkinter as tk
import threading
import keyboard
import os
import ctypes
import MORSE_TOOLS
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

        self.shortcut_label = None
        self.screenshot_switch = None
        self.service_switch = None
        self.screenshot_frame = None
        base_title = "Delta行动小工具"
        if self.is_admin():
            self.title(f"{base_title} > admin")
        else:
            self.title(base_title)
        self.geometry("480x180")
        self.resizable(False, False)

        icon = open("icon.ico", "wb+")
        icon.write(base64.b64decode(img))
        icon.close()
        self.iconbitmap("icon.ico")
        os.remove("icon.ico")

        self.screenshot_enabled = tk.BooleanVar(value=False)
        # 恢復用戶原始的快捷鍵設置方式，並在UI上顯示
        self.shortcut_key = 'right' # 默認為右方向鍵

        self.show_debug_window_enabled = tk.BooleanVar(value=False)

        self.resolution_var = tk.StringVar(value=list(MORSE_TOOLS.resolution_config_map.keys())[0])

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

        self.resolution_option_menu = ctk.CTkOptionMenu(screenshot_frame, variable=self.resolution_var,
                                                       values=list(MORSE_TOOLS.resolution_config_map.keys()))
        self.resolution_option_menu.pack(side="left", padx=(5, 10))

        # 顯示當前快捷鍵
        self.shortcut_label = ctk.CTkLabel(screenshot_frame, text=f"快捷键：{self.shortcut_key}")
        self.shortcut_label.pack(side="right", padx=5)

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
            # 调试模式开启：显示手动配置，隐藏下拉框
            self.morse_config_frame.pack(fill="x", padx=10, pady=5, after=self.screenshot_frame)
            self.resolution_option_menu.pack_forget()
            self.geometry("480x380")  # 展开后的高度
        else:
            # 调试模式关闭：隐藏手动配置，显示下拉框
            self.morse_config_frame.pack_forget()
            self.resolution_option_menu.pack(side="left", padx=5)
            self.geometry("480x180")  # 收起后的高度

    def toggle_service(self):
        if self.service_switch.get():
            threading.Thread(target=stop_anticheat_service, daemon=True).start()

    def on_screenshot_trigger(self):
        if self.screenshot_enabled.get():
            config = {}
            try:
                # 根据调试模式决定配置来源
                if self.debug_switch.get():
                    # 调试模式：从输入框获取配置
                    config = {key: int(entry.get()) for key, entry in self.morse_entries.items()}
                    config['debug'] = self.show_debug_window_enabled.get()
                    print(f"[DEBUG] Screenshot trigger activated with manual config: {config}")
                else:
                    # 非调试模式：从下拉框获取预设配置
                    selected_resolution = self.resolution_var.get()
                    config = MORSE_TOOLS.resolution_config_map.get(selected_resolution, {}).copy()
                    config['debug'] = False # 非调试模式下，debug应为False
                    print(f"[DEBUG] Screenshot trigger activated with preset config '{selected_resolution}': {config}")

                if not config:
                    print("❌ 错误: 未找到有效配置。")
                    tk.messagebox.showerror("配置错误", "未找到所选分辨率的有效配置。")
                    return

                # 使用 lambda 来传递参数
                threading.Thread(target=lambda: MORSE_TOOLS.screenshot_game_and_sendCode(morse_config=config),
                                 daemon=True).start()
            except ValueError:
                print("❌ 错误: 摩斯码识别区域配置中包含了无效的非整数值。")
                tk.messagebox.showerror("输入错误", "摩斯码识别区域配置中只能输入整数！")
            except Exception as e:
                print(f"❌ 触发截图时发生未知错误: {e}")
        else:
            print("[DEBUG] Screenshot is disabled, ignoring trigger")

    def global_keyboard_listener(self):
        def on_key(e):
            # 摩斯密碼識別快捷鍵 (right)
            # 確保每次按下都觸發，並且只在按下時觸發
            if self.screenshot_enabled.get() and e.event_type == 'down' and e.name == self.shortcut_key:
                print(f"[DEBUG] Key '{self.shortcut_key}' pressed, triggering screenshot")
                # 使用 self.after 將 UI 更新和耗時操作放到主線程或新線程中
                # 這裡直接調用 on_screenshot_trigger，它內部會創建新線程處理耗時操作
                self.on_screenshot_trigger()

        keyboard.hook(on_key)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()



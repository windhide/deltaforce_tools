import base64
import customtkinter as ctk
import tkinter as tk
import threading
import keyboard
import mouse
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
        self.geometry("480x130")
        self.resizable(False, False)

        icon = open("icon.ico", "wb+")
        icon.write(base64.b64decode(img))
        icon.close()
        self.iconbitmap("icon.ico")
        os.remove("icon.ico")

        self.screenshot_enabled = tk.BooleanVar(value=False)
        # 恢复用户原始的快捷键设置方式，并在UI上显示
        # 鼠标按键映射：left=左键, right=右键, middle=中键, x=侧键1, x2=侧键2
        self.shortcut_key = 'middle' # 默认为鼠标中键（滚轮按下）

        self.show_debug_window_enabled = tk.BooleanVar(value=False)

        self.resolution_var = tk.StringVar(value=list(MORSE_TOOLS.resolution_config_map.keys())[0])

        self.build_ui()

        # 启动全局键盘监听器
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

        # 快捷键设置区域
        shortcut_frame = ctk.CTkFrame(screenshot_frame)
        shortcut_frame.pack(side="right", padx=5)
        
        # 显示当前快捷键
        self.shortcut_label = ctk.CTkLabel(shortcut_frame, text=f"快捷键：{self.shortcut_key}")
        self.shortcut_label.pack(side="left", padx=5)
        
        # 添加修改快捷键的按钮 - 增加宽度和高度确保显示正常
        self.change_shortcut_btn = ctk.CTkButton(shortcut_frame, text="修改", width=100, height=30,
                                         command=self.change_shortcut)
        self.change_shortcut_btn.pack(side="right", padx=5)

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
            self.geometry("550x380")  # 展开后的高度
        else:
            # 调试模式关闭：隐藏手动配置，显示下拉框
            self.morse_config_frame.pack_forget()
            self.resolution_option_menu.pack(side="left", padx=5)
            self.geometry("550x130")  # 收起后的高度

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

    def change_shortcut(self):
        # 创建一个新窗口用于设置快捷键
        shortcut_window = ctk.CTkToplevel(self)
        shortcut_window.title("设置快捷键")
        shortcut_window.geometry("400x210")  # 增加窗口大小
        shortcut_window.resizable(False, False)
        shortcut_window.grab_set()  # 使窗口成为模态窗口
        shortcut_window.focus_set()  # 确保窗口获得焦点
        
        # 创建说明标签
        instruction_label = ctk.CTkLabel(shortcut_window, 
                                       text="请按下您想要设置的按键（支持键盘和鼠标按键）")
        instruction_label.pack(pady=10)
        
        # 显示当前快捷键
        current_key_label = ctk.CTkLabel(shortcut_window, 
                                      text=f"当前快捷键：{self.shortcut_key}")
        current_key_label.pack(pady=5)
        
        # 创建一个标签用于显示按下的按键
        key_label = ctk.CTkLabel(shortcut_window, text="等待按键...")
        key_label.pack(pady=5)
        
        # 添加鼠标按钮选项
        mouse_frame = ctk.CTkFrame(shortcut_window)
        mouse_frame.pack(pady=10)
        
        mouse_label = ctk.CTkLabel(mouse_frame, text="或选择鼠标按钮:")
        mouse_label.pack(side="left", padx=5)
        
        def set_mouse_button(button):
            button_name = f"mouse_{button}"
            new_key[0] = button_name
            update_key_label(button_name)
            
        left_btn = ctk.CTkButton(mouse_frame, text="左键", width=60, 
                               command=lambda: set_mouse_button("left"))
        left_btn.pack(side="left", padx=2)
        
        right_btn = ctk.CTkButton(mouse_frame, text="右键", width=60, 
                                command=lambda: set_mouse_button("right"))
        right_btn.pack(side="left", padx=2)
        
        middle_btn = ctk.CTkButton(mouse_frame, text="中键", width=60, 
                                 command=lambda: set_mouse_button("middle"))
        middle_btn.pack(side="left", padx=2)
        
        # 创建确认和取消按钮
        button_frame = ctk.CTkFrame(shortcut_window)
        button_frame.pack(pady=1)
        
        # 确保按钮有足够的高度和宽度
        button_style = {"height": 25, "width": 80}
        
        # 用于存储新的快捷键
        new_key = [None]
        
        def on_key_press(e):
            try:
                # 获取按下的按键名称
                key_name = e.name
                # 记录按键
                new_key[0] = key_name
                print(f"[DEBUG] 检测到按键: {key_name}, 事件类型: {e.event_type}")
                # 使用after方法确保UI更新在主线程中进行
                shortcut_window.after(1, lambda: update_key_display(key_name))
                return False  # 不阻止事件继续传播
            except Exception as ex:
                print(f"[ERROR] 按键处理错误: {ex}")
                return False
            
        def update_key_display(key_name):
            try:
                if shortcut_window.winfo_exists():
                    key_label.configure(text=f"已选择：{key_name}")
            except Exception as e:
                print(f"[ERROR] 更新标签时出错: {e}")
                
        # 更新按键显示函数 - 用于鼠标按钮
        def update_key_label(key):
            update_key_display(key)
        
        def confirm():
            if new_key[0]:
                self.shortcut_key = new_key[0]
                self.shortcut_label.configure(text=f"快捷键：{self.shortcut_key}")
                print(f"[DEBUG] Shortcut key changed to: {self.shortcut_key}")
            shortcut_window.destroy()
        
        def cancel():
            shortcut_window.destroy()
        
        # 创建按钮
        confirm_btn = ctk.CTkButton(button_frame, text="确认", command=confirm, **button_style)
        confirm_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(button_frame, text="取消", command=cancel, **button_style)
        cancel_btn.pack(side="right", padx=10)
        
        # 设置按键监听
        listener = keyboard.hook(on_key_press)
        
        # 窗口关闭时取消监听
        def on_close():
            try:
                keyboard.unhook(listener)
            except Exception as e:
                print(f"[ERROR] 取消键盘钩子时出错: {e}")
            shortcut_window.destroy()
        
        shortcut_window.protocol("WM_DELETE_WINDOW", on_close)
    
    def global_keyboard_listener(self):
        def on_key(e):
            # 摩斯密码识别快捷键
            # 确保每次按下都触发，并且只在按下时触发
            try:
                # 检查是否是鼠标按键或键盘按键
                if self.screenshot_enabled.get() and e.event_type == 'down' and e.name == self.shortcut_key:
                    print(f"[DEBUG] Key '{self.shortcut_key}' pressed, triggering screenshot")
                    # 使用 self.after 将 UI 更新和耗时操作放到主线程或新线程中
                    # 这里直接调用 on_screenshot_trigger，它内部会创建新线程处理耗时操作
                    self.after(1, self.on_screenshot_trigger)
                    return False  # 不阻止事件继续传播
            except Exception as e:
                print(f"[ERROR] 处理按键事件时出错: {e}")
            return False  # 确保事件继续传播

        # 鼠标按钮事件处理函数
        def on_mouse_click(button):
            try:
                # 将鼠标按钮名称转换为字符串格式
                button_name = f"mouse_{button}"
                if self.screenshot_enabled.get() and button_name == self.shortcut_key:
                    print(f"[DEBUG] Mouse button '{button_name}' clicked, triggering screenshot")
                    self.after(1, self.on_screenshot_trigger)
            except Exception as e:
                print(f"[ERROR] 处理鼠标事件时出错: {e}")

        # 注册全局键盘事件监听
        keyboard.hook(on_key)
        
        # 注册鼠标事件监听
        mouse.on_click(lambda: on_mouse_click("left"))
        mouse.on_right_click(lambda: on_mouse_click("right"))
        mouse.on_middle_click(lambda: on_mouse_click("middle"))


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()



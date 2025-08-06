
<div align="center">

![:name](https://count.getloli.com/@deltaforce_tools?name=deltaforce_tools&theme=capoo-1&padding=6&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)

# ✨三角洲小助手✨

_✨ [deltaforce_tools]([https://github.com/AstrBotDevs/AstrBot](https://github.com/windhide/deltaforce_tools)) 三角洲小助手 ✨_  

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![GitHub](https://img.shields.io/badge/作者-WindHide-blue)](https://github.com/windhide)

</div>

# 🥹创建项目的原因🥹

一切的一切还要从好基友和我开同一个电脑，我速度开的没他快，从我嘴里掏走2个实验数据说起

# 🔨构建指令🔨
```shell
pyinstaller deltaforce_tools.spec --noconfirm
```

# 介绍

一个基于 Python 的辅助工具，集成键盘监听与图像识别功能，用于自动执行预设操作和解析摩斯密码输入。适用于各类自动化场景、个人研究或兴趣开发，不涉及任何游戏或软件的修改行为。

## ✨ 功能特性

### 1. 键盘监听与组合操作执行
- 使用 [`keyboard`](https://github.com/boppreh/keyboard) 库实现快捷键监听。
- 支持监听组合按键（如 `Alt+D`、`Ctrl+Shift+X`）触发自定义操作。
- 可执行一系列自动化行为（如模拟点击、持续输入、系统操作等）。
- 所有按键模拟均基于系统级事件，无需注入或与目标程序进行交互。

### 2. 摩斯密码图像识别与自动输入
- 截取屏幕或窗口指定区域图像。
- 对图像中的摩斯电码元素进行识别与解码（支持灰度、二值化处理等）。
- 解码结果通过键盘事件自动输入，无需人工干预。
- 支持动态识别与多次输入循环。

## 📁 项目结构
. <br>
├── main.py # 主程序入口 <br>
├── MORSE_TOOLS.py # 摩斯图像识别逻辑 <br>
├── AUTO_TOOLS.py # 键盘监听与操作模块 <br>
├── README.md # 项目说明 <br>
├── LICENSE # MIT 许可 <br>
└── requirements.txt # 所需依赖库


## 🧾 License

本项目采用 [MIT License](LICENSE)，你可以自由地使用、修改和分发代码，但需保留原始的许可声明。

## ⚠️ 使用声明

本工具完全基于操作系统提供的标准接口进行开发，**不涉及任何对第三方程序的内存、数据、图形等进行修改或干预的行为**，包括但不限于：
- 不注入 DLL / 不劫持进程
- 不读取或修改游戏/应用的内存
- 不使用任何绕过机制规避安全检测
- 不涉及封包分析或网络请求伪造

> 📌 本项目的初衷是进行图像处理、键盘控制等相关技术的实践与研究。请勿将其用于违反法律法规或侵犯他人权益的场景。

使用者应自行判断项目使用场景的合规性，并承担相关风险与责任。项目作者不承担任何因使用本工具所导致的直接或间接损失。

## 📦 安装与使用

### 安装依赖

确保使用 Python 3.10 或以上版本：

## 🙌 欢迎参与贡献
你可以通过以下方式参与改进本项目：

提交 Issue 反馈使用中的问题或建议

提交 PR 贡献新功能或代码优化

Fork 项目进行个性化定制

```bash
pip install -r requirements.txt

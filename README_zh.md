<div align="center">

# XLAT_NOVA

**鼠标 / 键盘延迟测量工具**

*(基于 [Finalmouse XLAT](https://github.com/teamfinalmouse/xlat) 的维护分支)*

[English](README.md) | [中文](README_zh.md)

</div>

## 简介

XLAT_NOVA 用于测量输入延迟——点击、移动、按键——也就是设备到主机之间的延迟。
它运行在 STM32F746G-DISCO 开发板上，通过硬件触发（GPIO 边沿）配合 USB 主机口
抓到的 HID 报文时间戳来计算延迟。

它是开源项目 Finalmouse XLAT（GPLv3）的一个维护分支。

## 特性

- 三种检测模式：**鼠标点击**、**鼠标移动**、**键盘按键**
- 切换模式时自动应用正确的检测配置（边沿 / 去抖 / 输入上下拉），无需手动调整
- 中英文界面，语言选择断电后保留（升级固件后默认恢复英文）
- 定制黑色主题 + 个人 logo
- macOS 与 Windows 10/11 一键刷机工具（内置 ST-LINK 驱动）

## 相对官方 XLAT 的改进与修复

与原版 Finalmouse XLAT 固件相比，本分支新增 / 修复了以下内容：

- **中英文双语界面**——语言选择写入内部 Flash，断电后保留；升级固件后自动
  恢复默认英文。
- **按模式自动应用检测配置**——原版固件切换模式后仍沿用之前的触发边沿
  （例如切到「移动」仍是点击模式的下降沿），不手动改就会测错；现在切换
  模式会自动设置正确的边沿 / 去抖 / 输入上下拉。
- **定制黑色主题** + 个人 logo。
- **macOS / Windows 一键刷机工具**，内置 ST-LINK 驱动；Windows 驱动卸载工具
  会彻底清理驱动（设备节点、驱动包、配置文件、注册表）。

## 所需硬件

- STM32F746G-DISCO（或带 USB 主机的兼容 STM32F7 开发板）
- 被测设备用 USB OTG 线 / 转接头
- ST-LINK mini-USB 线（板载 ST-Link，用于供电和刷机）

## 快速上手

### 1. 刷入固件

使用配套刷机工具：

- **macOS**：打开 `XLAT一键刷机.app`
- **Windows**：先运行 `1-Install-Driver.bat` 安装 ST-LINK 驱动，再运行 `2-Flash-XLAT.exe`

或手动刷入：

```sh
st-flash --connect-under-reset write build/release/xlat.bin 0x08000000
```

### 2. 触发输入接线

| 信号 | 接到 |
| --- | --- |
| 触发输入（D12） | CN7 第 5 脚 |
| GND | CN7 第 7 脚 |

自动触发输出用 D11（CN7 第 4 脚）或 D6，在设置页配置。

### 3. 开始测量

1. 把被测设备接到 USB 主机口，给板子上电。
2. 在主页进入 **设置 → 模式**，选择检测模式。
3. 移动 / 点击 / 按键，屏幕上就会显示延迟数值。
4. 按 **清除** 重置统计。

## 检测模式与自动配置

模式下拉框会自动应用对应的检测配置：

| 模式 | 边沿 | 去抖 | 上下拉 |
| --- | --- | --- | --- |
| 鼠标: 移动 | 上升沿 | 20ms | 上拉 |
| 鼠标: 点击 | 下降沿 | 50ms | 上拉 |
| 键盘: 按键 | 下降沿 | 50ms | 上拉 |

## 已知问题与排查

沿用官方 XLAT README 中标记的问题：

- **屏幕花屏 / 初始化异常**：官方原版固件的问题，本分支**已修复**——显示
  初始化稳定，不再需要重启 / 断电兜底。
- **设备无法识别**：如果鼠标 / 键盘未被识别，先刷最新固件（新设备支持会
  持续加入）。仍不行说明该设备需要描述符支持——请收集 USB VID:PID 和 HID
  报告描述符并反馈，以便加入支持。

## 从源码构建

```sh
# 需要 arm-none-eabi 工具链 + cmake + ninja
cmake -S . -B build -GNinja -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

## 许可证

GPLv3。本仓库是 [Finalmouse XLAT](https://github.com/teamfinalmouse/xlat)
（GPLv3）项目的**修改版**，详见 [COPYING](COPYING)。

本 fork 的改动见「相对官方 XLAT 的改进与修复」。第三方库（tinyusb、lvgl、
FreeRTOS 等）按各自许可证授权。

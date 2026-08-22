# 问题修复记录

> 记录时间：2026-08-17，话题：鼠标 Motion 延迟测试。

## 已修复：切到 Motion 模式时不会自动应用传感器的正常配置

**状态：已修复（2026-08-17）**

修复方式：在 `src/gfx_settings.c` 的 `mode_dropdown` 事件处理中新增 `apply_mode_defaults()`，
切换模式时自动应用对应配置（边沿 / 去抖 / 上下拉）并同步刷新界面下拉框。

**现象**

用户把检测模式从「鼠标: 点击」切到「鼠标: 移动」后，检测边沿仍然是点击模式用的「下降沿」。PAW3311 这类传感器的 MOTION 脚是「移动时输出高电平」，需要抓「上升沿」才能正确测到移动开始，所以切到 Motion 后必须手动再把边沿改成「上升沿」，否则测不出正常数据。

**期望行为**

切换到「鼠标: 移动」模式时，自动应用适合传感器测试的正常配置：

```
检测边沿 = 上升沿
去抖时间 = 20ms
输入上下拉 = 上拉
```

切回「鼠标: 点击」时，恢复点击模式的正常配置：

```
检测边沿 = 下降沿
去抖时间 = 50ms
输入上下拉 = 上拉
```

**根因**

`src/gfx_settings.c` 的 `mode_dropdown` 事件处理里，切换模式只调用了 `xlat_mode_set()` 和发送 `GFX_EVENT_MODE_CHANGED`，没有同步更新边沿 / 去抖 / 上下拉，所以边沿沿用之前（点击模式）的下降沿。

**修复方向**

在 `mode_dropdown` 的 `LV_EVENT_VALUE_CHANGED` 分支里，根据选中的模式自动设置并刷新：

- 边沿：`hw_config_input_trigger_set_edge()`
- 去抖：`xlat_gpio_irq_holdoff_us_set()`
- 上下拉：`hw_config_input_bias()`

并同步更新 `edge_dropdown`、`debounce_dropdown`、`bias_dropdown` 的显示选中项。

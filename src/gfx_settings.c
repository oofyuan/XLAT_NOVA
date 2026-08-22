/*
 * Copyright (c) 2023 Finalmouse, LLC
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

#include <stdio.h>
#include "gfx_settings.h"
#include "gfx_main.h"
#include "lvgl/lvgl.h"
#include "xlat.h"
#include "xlat_config.h"
#include "hardware_config.h"
#include "gfx_i18n.h"
#include "settings_store.h"

LV_IMG_DECLARE(bg_city);

// UI layout constants
#define LABEL_WIDTH 180
#define DROPDOWN_WIDTH 180

// Pointers to the widgets
lv_obj_t *settings_screen;
lv_obj_t *prev_screen = NULL;
lv_obj_t *edge_dropdown;
lv_obj_t *bias_dropdown;
lv_obj_t *debounce_dropdown;
lv_obj_t *trigger_dropdown;
lv_obj_t *mode_dropdown;
lv_obj_t *trigger_output_dropdown;
lv_obj_t *trigger_interval_dropdown;
lv_obj_t *language_dropdown;

// Auto-trigger interval options (ms), index-aligned with the dropdown
static const uint16_t interval_options[] = {100, 150, 200, 300, 400, 500,
                                            600, 700, 800, 900, 1000};

// Event handler for the back button
static void back_btn_event_handler(lv_event_t* e)
{
    lv_event_code_t code = lv_event_get_code(e);
    if (code == LV_EVENT_CLICKED) {
        if (prev_screen) {
            lv_scr_load(prev_screen);
            lv_obj_del(settings_screen);
        }
    }
}

static void reload_settings_page(void)
{
    lv_obj_t *parent = prev_screen;
    lv_obj_del(settings_screen);
    gfx_settings_create_page(parent);
}

static void reload_settings_async(void *user_data)
{
    (void)user_data;
    reload_settings_page();
}

static void apply_mode_defaults(enum xlat_mode mode)
{
    bool rising;
    input_bias_t bias;
    uint32_t debounce_us;

    if (mode == XLAT_MODE_MOUSE_MOTION) {
        /* Motion: MOTION pin asserts high on movement -> rising edge */
        rising = true;
        bias = INPUT_BIAS_PULLUP;
        debounce_us = 20 * 1000;
    } else {
        /* Click / Keyboard: switch closes to GND -> falling edge */
        rising = false;
        bias = INPUT_BIAS_PULLUP;
        debounce_us = 50 * 1000;
    }

    hw_config_input_trigger(rising, bias);
    xlat_gpio_irq_holdoff_us_set(debounce_us);

    if (edge_dropdown) {
        lv_dropdown_set_selected(edge_dropdown, rising ? 1 : 0);
    }
    if (debounce_dropdown) {
        uint16_t idx = 0;
        switch (debounce_us / 1000) {
            case 20: idx = 0; break;
            case 50: idx = 1; break;
            case 100: idx = 2; break;
            case 200: idx = 3; break;
            case 500: idx = 4; break;
            case 1000: idx = 5; break;
            default: idx = 0; break;
        }
        lv_dropdown_set_selected(debounce_dropdown, idx);
    }
    if (bias_dropdown) {
        uint16_t idx = 0;
        switch (bias) {
            case INPUT_BIAS_NOPULL: idx = 0; break;
            case INPUT_BIAS_PULLUP: idx = 1; break;
            case INPUT_BIAS_PULLDOWN: idx = 2; break;
            default: idx = 0; break;
        }
        lv_dropdown_set_selected(bias_dropdown, idx);
    }
}

static void event_handler(lv_event_t* e)
{
    lv_event_code_t code = lv_event_get_code(e);
    lv_obj_t* obj = lv_event_get_target(e);

    if (code == LV_EVENT_VALUE_CHANGED) {
        if (obj == edge_dropdown) {
            uint16_t sel = lv_dropdown_get_selected(obj);
            hw_config_input_trigger_set_edge(sel);
        } else if (obj == bias_dropdown) {
            uint16_t sel = lv_dropdown_get_selected(obj);
            uint32_t bias;
            switch (sel) {
                case 0: bias = INPUT_BIAS_NOPULL; break;
                case 1: bias = INPUT_BIAS_PULLUP; break;
                case 2: bias = INPUT_BIAS_PULLDOWN; break;
                default: bias = INPUT_BIAS_NOPULL; break;
            }
            hw_config_input_bias(bias);
        } else if (obj == debounce_dropdown) {
            uint16_t sel = lv_dropdown_get_selected(obj);
            uint32_t val = 100;
            switch (sel) {
                case 0: val = 20; break;
                case 1: val = 50; break;
                case 2: val = 100; break;
                case 3: val = 200; break;
                case 4: val = 500; break;
                case 5: val = 1000; break;
                default: break;
            }
            xlat_gpio_irq_holdoff_us_set(val * 1000);
        } else if (obj == trigger_dropdown) {
            uint16_t sel = lv_dropdown_get_selected(obj);
            xlat_auto_trigger_level_set(sel);
        } else if (obj == mode_dropdown) {
            uint16_t sel = lv_dropdown_get_selected(obj);
            if (sel == 0) {
                xlat_mode_set(XLAT_MODE_MOUSE_CLICK);
                apply_mode_defaults(XLAT_MODE_MOUSE_CLICK);
                gfx_event_send(GFX_EVENT_MODE_CHANGED, 0);
            } else if (sel == 1) {
                xlat_mode_set(XLAT_MODE_MOUSE_MOTION);
                apply_mode_defaults(XLAT_MODE_MOUSE_MOTION);
                gfx_event_send(GFX_EVENT_MODE_CHANGED, 0);
            } else if (sel == 2) {
                xlat_mode_set(XLAT_MODE_KEYBOARD);
                apply_mode_defaults(XLAT_MODE_KEYBOARD);
                gfx_event_send(GFX_EVENT_MODE_CHANGED, 0);
            }
        } else if (obj == trigger_interval_dropdown) {
            uint16_t sel = lv_dropdown_get_selected(obj);
            uint32_t interval = interval_options[sel];
            xlat_auto_trigger_interval_ms_set(interval);
        } else if (obj == trigger_output_dropdown) {
            uint16_t sel = lv_dropdown_get_selected(obj);
            uint8_t pin = (sel == 0) ? 6 : 11; // D6 or D11
            xlat_auto_trigger_output_set(pin);
        } else if (obj == language_dropdown) {
            uint16_t sel = lv_dropdown_get_selected(obj);
            gfx_lang_t lang = (sel == 0) ? GFX_LANG_EN : GFX_LANG_ZH;
            gfx_i18n_lang_set(lang);
            settings_store_save_language(lang);
            gfx_main_language_changed();
            lv_async_call(reload_settings_async, NULL);
        }
    }
}

void gfx_settings_create_page(lv_obj_t *previous_screen)
{
    prev_screen = previous_screen;
    settings_screen = lv_obj_create(NULL);
    lv_scr_load(settings_screen);

    // Draw background image
    lv_obj_t *bg = lv_img_create(settings_screen);
    lv_img_set_src(bg, &bg_city);
    lv_obj_align(bg, LV_ALIGN_TOP_LEFT, 0, 0);

    // Create a tabview
    lv_obj_t *tabview = lv_tabview_create(settings_screen, LV_DIR_TOP, 30);
    lv_obj_set_size(tabview, lv_disp_get_hor_res(NULL), lv_disp_get_ver_res(NULL) - 30);
    lv_obj_align(tabview, LV_ALIGN_TOP_MID, 0, 0);
    lv_obj_set_style_bg_opa(tabview, LV_OPA_TRANSP, 0);
    lv_obj_set_style_bg_opa(lv_tabview_get_content(tabview), LV_OPA_TRANSP, 0);

    // Create 4 tabs
    lv_obj_t *tab_mode = lv_tabview_add_tab(tabview, gfx_i18n_tr("Mode", "模式"));
    lv_obj_t *tab_detection = lv_tabview_add_tab(tabview, gfx_i18n_tr("Detection", "检测"));
    lv_obj_t *tab_trigger = lv_tabview_add_tab(tabview, gfx_i18n_tr("Trigger", "触发"));
    lv_obj_t *tab_language = lv_tabview_add_tab(tabview, "语言/Language");

    // Mode Tab Content
    // Add explanatory text for Mode tab first
    lv_obj_t *mode_info = lv_label_create(tab_mode);
    lv_label_set_text(mode_info, gfx_i18n_tr("Select detection mode.\n"
                                             "After changing mode, reconnect the USB device if needed.",
                                             "选择检测模式。\n"
                                             "更改模式后,可能需要重新插拔USB设备。"));
    lv_obj_set_style_text_align(mode_info, LV_TEXT_ALIGN_LEFT, 0);
    lv_obj_align(mode_info, LV_ALIGN_TOP_LEFT, 10, 10);

    // Then add the mode dropdown
    lv_obj_t *mode_label = lv_label_create(tab_mode);
    lv_label_set_text(mode_label, gfx_i18n_tr("Detection mode:", "检测模式:"));
    lv_obj_set_width(mode_label, LABEL_WIDTH);
    lv_obj_align_to(mode_label, mode_info, LV_ALIGN_OUT_BOTTOM_LEFT, 0, 30);

    mode_dropdown = lv_dropdown_create(tab_mode);
    lv_dropdown_set_options(mode_dropdown, gfx_i18n_tr("Mouse: Click\nMouse: Motion\nKeyboard: Key",
                                                        "鼠标: 点击\n鼠标: 移动\n键盘: 按键"));
    lv_obj_set_width(mode_dropdown, DROPDOWN_WIDTH);
    lv_obj_align_to(mode_dropdown, mode_label, LV_ALIGN_OUT_RIGHT_MID, 10, 0);
    lv_obj_add_event_cb(mode_dropdown, event_handler, LV_EVENT_VALUE_CHANGED, NULL);

    // Detection Tab Content
    // Add explanatory text for Detection tab first
    lv_obj_t *detection_info = lv_label_create(tab_detection);
    lv_label_set_text(detection_info, gfx_i18n_tr("Configure input signal detection.",
                                                  "配置输入信号检测。"));
    lv_obj_set_style_text_align(detection_info, LV_TEXT_ALIGN_LEFT, 0);
    lv_obj_align(detection_info, LV_ALIGN_TOP_LEFT, 10, 10);

    // Then add the detection settings
    lv_obj_t *edge_label = lv_label_create(tab_detection);
    lv_label_set_text(edge_label, gfx_i18n_tr("Edge:", "检测边沿:"));
    lv_obj_set_width(edge_label, LABEL_WIDTH);
    lv_obj_align_to(edge_label, detection_info, LV_ALIGN_OUT_BOTTOM_LEFT, 0, 30);

    edge_dropdown = lv_dropdown_create(tab_detection);
    lv_dropdown_set_options(edge_dropdown, gfx_i18n_tr("Falling\nRising", "下降沿\n上升沿"));
    lv_obj_set_width(edge_dropdown, DROPDOWN_WIDTH);
    lv_obj_align_to(edge_dropdown, edge_label, LV_ALIGN_OUT_RIGHT_MID, 10, 0);
    lv_obj_add_event_cb(edge_dropdown, event_handler, LV_EVENT_VALUE_CHANGED, NULL);

    lv_obj_t *debounce_label = lv_label_create(tab_detection);
    lv_label_set_text(debounce_label, gfx_i18n_tr("Debounce:", "去抖时间:"));
    lv_obj_set_width(debounce_label, LABEL_WIDTH);
    lv_obj_align_to(debounce_label, edge_label, LV_ALIGN_OUT_BOTTOM_LEFT, 0, 30);

    debounce_dropdown = lv_dropdown_create(tab_detection);
    lv_dropdown_set_options(debounce_dropdown, "20ms\n50ms\n100ms\n200ms\n500ms\n1000ms");
    lv_obj_set_width(debounce_dropdown, DROPDOWN_WIDTH);
    lv_obj_align_to(debounce_dropdown, debounce_label, LV_ALIGN_OUT_RIGHT_MID, 10, 0);
    lv_obj_add_event_cb(debounce_dropdown, event_handler, LV_EVENT_VALUE_CHANGED, NULL);

    lv_obj_t *bias_label = lv_label_create(tab_detection);
    lv_label_set_text(bias_label, gfx_i18n_tr("Input bias:", "输入上下拉:"));
    lv_obj_set_width(bias_label, LABEL_WIDTH);
    lv_obj_align_to(bias_label, debounce_label, LV_ALIGN_OUT_BOTTOM_LEFT, 0, 30);

    bias_dropdown = lv_dropdown_create(tab_detection);
    lv_dropdown_set_options(bias_dropdown, gfx_i18n_tr("None\nPull-up\nPull-down",
                                                        "无上下拉\n上拉\n下拉"));
    lv_obj_set_width(bias_dropdown, DROPDOWN_WIDTH);
    lv_obj_align_to(bias_dropdown, bias_label, LV_ALIGN_OUT_RIGHT_MID, 10, 0);
    lv_obj_add_event_cb(bias_dropdown, event_handler, LV_EVENT_VALUE_CHANGED, NULL);

    // Trigger Tab Content
    // Add explanatory text for Trigger tab first
    lv_obj_t *trigger_info = lv_label_create(tab_trigger);
    lv_label_set_text(trigger_info, gfx_i18n_tr("Configure auto-trigger behavior.",
                                                "配置自动触发行为。"));
    lv_obj_set_style_text_align(trigger_info, LV_TEXT_ALIGN_LEFT, 0);
    lv_obj_align(trigger_info, LV_ALIGN_TOP_LEFT, 10, 10);

    // Then add the trigger settings
    lv_obj_t *trigger_level_label = lv_label_create(tab_trigger);
    lv_label_set_text(trigger_level_label, gfx_i18n_tr("Auto-trigger level:",
                                                       "自动触发电平:"));
    lv_obj_set_width(trigger_level_label, LABEL_WIDTH);
    lv_obj_align_to(trigger_level_label, trigger_info, LV_ALIGN_OUT_BOTTOM_LEFT, 0, 30);

    trigger_dropdown = lv_dropdown_create(tab_trigger);
    lv_dropdown_set_options(trigger_dropdown, gfx_i18n_tr("Low\nHigh", "低电平\n高电平"));
    lv_obj_set_width(trigger_dropdown, DROPDOWN_WIDTH);
    lv_obj_align_to(trigger_dropdown, trigger_level_label, LV_ALIGN_OUT_RIGHT_MID, 10, 0);
    lv_obj_add_event_cb(trigger_dropdown, event_handler, LV_EVENT_VALUE_CHANGED, NULL);

    lv_obj_t *trigger_output_label = lv_label_create(tab_trigger);
    lv_label_set_text(trigger_output_label, gfx_i18n_tr("Auto-trigger output:",
                                                        "自动触发输出:"));
    lv_obj_set_width(trigger_output_label, LABEL_WIDTH);
    lv_obj_align_to(trigger_output_label, trigger_level_label, LV_ALIGN_OUT_BOTTOM_LEFT, 0, 30);

    trigger_output_dropdown = lv_dropdown_create(tab_trigger);
    lv_dropdown_set_options(trigger_output_dropdown, gfx_i18n_tr("D6 (Push-pull)\nD11 (Open-drain)",
                                                                 "D6 (推挽)\nD11 (开漏)"));
    lv_obj_set_width(trigger_output_dropdown, DROPDOWN_WIDTH);
    lv_obj_align_to(trigger_output_dropdown, trigger_output_label, LV_ALIGN_OUT_RIGHT_MID, 10, 0);
    lv_obj_add_event_cb(trigger_output_dropdown, event_handler, LV_EVENT_VALUE_CHANGED, NULL);

    // Add auto-trigger interval setting
    lv_obj_t *trigger_interval_label = lv_label_create(tab_trigger);
    lv_label_set_text(trigger_interval_label, gfx_i18n_tr("Auto-trigger interval:",
                                                          "自动触发间隔:"));
    lv_obj_set_width(trigger_interval_label, LABEL_WIDTH);
    lv_obj_align_to(trigger_interval_label, trigger_output_label, LV_ALIGN_OUT_BOTTOM_LEFT, 0, 30);

    trigger_interval_dropdown = lv_dropdown_create(tab_trigger);
    lv_dropdown_set_options(trigger_interval_dropdown, "100ms\n150ms\n200ms\n300ms\n400ms\n500ms\n600ms\n700ms\n800ms\n900ms\n1000ms");
    lv_obj_set_width(trigger_interval_dropdown, DROPDOWN_WIDTH);
    lv_obj_align_to(trigger_interval_dropdown, trigger_interval_label, LV_ALIGN_OUT_RIGHT_MID, 10, 0);
    lv_obj_add_event_cb(trigger_interval_dropdown, event_handler, LV_EVENT_VALUE_CHANGED, NULL);

    // Language Tab Content
    lv_obj_t *language_info = lv_label_create(tab_language);
    lv_label_set_text(language_info, gfx_i18n_tr("Select interface language.\n"
                                                 "The selection is saved and restored after reboot.",
                                                 "选择语言。选择后重启自动设置。"));
    lv_obj_set_style_text_align(language_info, LV_TEXT_ALIGN_LEFT, 0);
    lv_obj_align(language_info, LV_ALIGN_TOP_LEFT, 10, 10);

    lv_obj_t *language_label = lv_label_create(tab_language);
    lv_label_set_text(language_label, gfx_i18n_tr("Language:", "语言:"));
    lv_obj_set_width(language_label, LABEL_WIDTH);
    lv_obj_align_to(language_label, language_info, LV_ALIGN_OUT_BOTTOM_LEFT, 0, 30);

    language_dropdown = lv_dropdown_create(tab_language);
    lv_dropdown_set_options(language_dropdown, gfx_i18n_tr("English\n中文",
                                                            "English\n中文"));
    lv_obj_set_width(language_dropdown, DROPDOWN_WIDTH);
    lv_obj_align_to(language_dropdown, language_label, LV_ALIGN_OUT_RIGHT_MID, 10, 0);
    lv_obj_add_event_cb(language_dropdown, event_handler, LV_EVENT_VALUE_CHANGED, NULL);

    // Back button
    lv_obj_t *btn_back = lv_btn_create(settings_screen);
    lv_obj_set_size(btn_back, GFX_BTN_WIDTH, GFX_BTN_HEIGHT);
    lv_obj_align(btn_back, LV_ALIGN_BOTTOM_LEFT, 10, -5);
    lv_obj_add_event_cb(btn_back, back_btn_event_handler, LV_EVENT_CLICKED, NULL);
    lv_obj_t *back_label = lv_label_create(btn_back);
    lv_label_set_text(back_label, gfx_i18n_tr("Back", "返回"));
    lv_obj_center(back_label);

    // Version number label
    lv_obj_t *version_label = lv_label_create(settings_screen);
    char version_str[30];
    sprintf(version_str, "XLAT v%s", APP_VERSION_FULL);
    lv_label_set_text(version_label, version_str);
    lv_obj_align(version_label, LV_ALIGN_BOTTOM_RIGHT, -10, -10);

    // Set initial values
    lv_dropdown_set_selected(mode_dropdown, xlat_mode_get());
    lv_dropdown_set_selected(edge_dropdown, hw_config_input_trigger_is_rising_edge());
    lv_dropdown_set_selected(trigger_dropdown, xlat_auto_trigger_level_is_high());

    // Set debounce time
    uint32_t debounce_time = xlat_gpio_irq_holdoff_us_get() / 1000;
    uint16_t debounce_index = 0;
    switch (debounce_time) {
        case 20: debounce_index = 0; break;
        case 50: debounce_index = 1; break;
        case 100: debounce_index = 2; break;
        case 200: debounce_index = 3; break;
        case 500: debounce_index = 4; break;
        case 1000: debounce_index = 5; break;
        default: break;
    }
    lv_dropdown_set_selected(debounce_dropdown, debounce_index);

    // Set input bias
    uint32_t current_bias = hw_config_input_bias_get();
    uint16_t bias_index = 0;
    switch (current_bias) {
        case INPUT_BIAS_NOPULL: bias_index = 0; break;
        case INPUT_BIAS_PULLUP: bias_index = 1; break;
        case INPUT_BIAS_PULLDOWN: bias_index = 2; break;
        default: bias_index = 0; break;
    }
    lv_dropdown_set_selected(bias_dropdown, bias_index);

    // Set auto-trigger interval
    uint32_t current_interval = xlat_auto_trigger_interval_ms_get();
    uint16_t interval_index = 0;
    for (uint16_t i = 0; i < sizeof(interval_options) / sizeof(interval_options[0]); i++) {
        if (interval_options[i] == current_interval) {
            interval_index = i;
            break;
        }
    }
    lv_dropdown_set_selected(trigger_interval_dropdown, interval_index);

    // Set auto-trigger output
    uint16_t current_output = xlat_auto_trigger_output_get();
    uint16_t output_index = (current_output == 6) ? 0 : 1; // D6 or D11
    lv_dropdown_set_selected(trigger_output_dropdown, output_index);

    // Set current language
    lv_dropdown_set_selected(language_dropdown, (uint16_t)gfx_i18n_lang_get());
}

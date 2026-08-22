/*
 * XLAT 一键刷机 (Windows GUI launcher)
 * 检测设备 -> 确认 -> 进度窗口刷机 -> 结果提示
 */

#define UNICODE
#define _UNICODE

#include <windows.h>
#include <commctrl.h>
#include <shellapi.h>
#include <string.h>
#include <wchar.h>

static void msgbox(const wchar_t *title, const wchar_t *text, UINT flags)
{
    MessageBoxW(NULL, text, title, MB_OK | MB_SETFOREGROUND | flags);
}

static void app_dir(wchar_t *out, size_t out_len)
{
    GetModuleFileNameW(NULL, out, (DWORD)out_len);
    wchar_t *slash = wcsrchr(out, L'\\');
    if (slash) {
        *slash = 0;
    }
}

static void pump_messages(void)
{
    MSG m;
    while (PeekMessageW(&m, NULL, 0, 0, PM_REMOVE)) {
        TranslateMessage(&m);
        DispatchMessageW(&m);
    }
}

static void wait_for_process(HANDLE process, HWND hwnd)
{
    for (;;) {
        DWORD r = MsgWaitForMultipleObjects(1, &process, FALSE, 100, QS_ALLINPUT);
        if (r == WAIT_OBJECT_0) {
            break;
        }
        if (r == WAIT_OBJECT_0 + 1) {
            pump_messages();
        }
        if (hwnd && IsWindow(hwnd) == FALSE) {
            break;
        }
    }
}

static int run_capture(const wchar_t *cmdline, const wchar_t *log_path,
                       const wchar_t *workdir, HWND hwnd)
{
    SECURITY_ATTRIBUTES sa = { sizeof(sa), NULL, TRUE };
    HANDLE h_log = CreateFileW(log_path, GENERIC_WRITE, FILE_SHARE_READ,
                               &sa, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (h_log == INVALID_HANDLE_VALUE) {
        return -1;
    }

    STARTUPINFOW si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    ZeroMemory(&pi, sizeof(pi));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW | STARTF_USESTDHANDLES;
    si.wShowWindow = SW_HIDE;
    si.hStdOutput = h_log;
    si.hStdError = h_log;

    wchar_t cmd[4096];
    wcsncpy(cmd, cmdline, 4095);
    cmd[4095] = 0;

    BOOL ok = CreateProcessW(NULL, cmd, NULL, NULL, TRUE,
                             CREATE_NO_WINDOW, NULL, workdir, &si, &pi);
    CloseHandle(h_log);
    if (!ok) {
        return -1;
    }

    wait_for_process(pi.hProcess, hwnd);

    DWORD code = 1;
    GetExitCodeProcess(pi.hProcess, &code);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    return (int)code;
}

static int run_elevated_bat(const wchar_t *bat_path, HWND hwnd)
{
    wchar_t params[MAX_PATH * 2 + 16];
    _snwprintf(params, MAX_PATH * 2 + 16, L"/c \"%s\"", bat_path);

    SHELLEXECUTEINFOW sei;
    ZeroMemory(&sei, sizeof(sei));
    sei.cbSize = sizeof(sei);
    sei.fMask = SEE_MASK_NOCLOSEPROCESS;
    sei.lpVerb = L"runas";
    sei.lpFile = L"cmd.exe";
    sei.lpParameters = params;
    sei.nShow = SW_SHOWNORMAL;

    if (!ShellExecuteExW(&sei)) {
        return -1;
    }
    if (sei.hProcess == NULL) {
        return -1;
    }

    wait_for_process(sei.hProcess, hwnd);

    DWORD code = 1;
    GetExitCodeProcess(sei.hProcess, &code);
    CloseHandle(sei.hProcess);
    return (int)code;
}

static char *read_file_ansi(const wchar_t *path)
{
    HANDLE h = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ,
                           NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (h == INVALID_HANDLE_VALUE) {
        return NULL;
    }
    DWORD size = GetFileSize(h, NULL);
    char *buf = (char *)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, size + 2);
    if (buf) {
        DWORD read = 0;
        ReadFile(h, buf, size, &read, NULL);
        buf[read] = '\0';
    }
    CloseHandle(h);
    return buf;
}

static wchar_t *ansi_to_wide(const char *text)
{
    if (!text) {
        return NULL;
    }
    int len = MultiByteToWideChar(CP_ACP, 0, text, -1, NULL, 0);
    if (len <= 0) {
        return NULL;
    }
    wchar_t *wide = (wchar_t *)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY,
                                         (DWORD)len * sizeof(wchar_t));
    if (!wide) {
        return NULL;
    }
    MultiByteToWideChar(CP_ACP, 0, text, -1, wide, len);
    return wide;
}

static LRESULT CALLBACK prog_wnd_proc(HWND h, UINT m, WPARAM w, LPARAM l)
{
    if (m == WM_CLOSE) {
        return 0; /* 刷机进行中不允许关闭 */
    }
    return DefWindowProcW(h, m, w, l);
}

static HWND show_progress(HINSTANCE hinst, const wchar_t *title, const wchar_t *text)
{
    INITCOMMONCONTROLSEX icc = { sizeof(icc), ICC_PROGRESS_CLASS };
    InitCommonControlsEx(&icc);

    const wchar_t *cls = L"XLFlashProgressWnd";
    WNDCLASSW wc;
    ZeroMemory(&wc, sizeof(wc));
    wc.lpfnWndProc = prog_wnd_proc;
    wc.hInstance = hinst;
    wc.lpszClassName = cls;
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wc.hCursor = LoadCursorW(NULL, IDC_ARROW);
    RegisterClassW(&wc);

    int w = 380, h = 118;
    int x = (GetSystemMetrics(SM_CXSCREEN) - w) / 2;
    int y = (GetSystemMetrics(SM_CYSCREEN) - h) / 2;

    HWND hw = CreateWindowExW(0, cls, title,
                              WS_POPUP | WS_CAPTION | WS_SYSMENU,
                              x, y, w, h, NULL, NULL, hinst, NULL);
    CreateWindowExW(0, L"STATIC", text,
                    WS_CHILD | WS_VISIBLE, 20, 16, w - 40, 24, hw, NULL, hinst, NULL);
    HWND bar = CreateWindowExW(0, PROGRESS_CLASSW, NULL,
                               WS_CHILD | WS_VISIBLE | PBS_MARQUEE,
                               20, 52, w - 40, 20, hw, NULL, hinst, NULL);
    SendMessageW(bar, PBM_SETMARQUEE, TRUE, 30);
    ShowWindow(hw, SW_SHOW);
    UpdateWindow(hw);
    return hw;
}

static int probe_device(const wchar_t *stinfo, wchar_t *cmd, int cmd_len,
                        const wchar_t *log)
{
    _snwprintf(cmd, cmd_len, L"\"%s\" --probe", stinfo);
    run_capture(cmd, log, NULL, NULL);

    char *log_text = read_file_ansi(log);
    int detected = log_text && strstr(log_text, "Found 1 stlink programmers") != NULL;
    if (log_text) {
        HeapFree(GetProcessHeap(), 0, log_text);
    }
    return detected;
}

int WINAPI WinMain(HINSTANCE hInst, HINSTANCE hPrev, LPSTR lpCmd, int nShow)
{
    (void)hPrev; (void)lpCmd; (void)nShow;

    wchar_t dir[MAX_PATH];
    wchar_t stinfo[MAX_PATH * 2];
    wchar_t stflash[MAX_PATH * 2];
    wchar_t firmware[MAX_PATH * 2];
    wchar_t log[MAX_PATH * 2];
    wchar_t driverbat[MAX_PATH * 2];
    wchar_t cmd[4096];

    app_dir(dir, MAX_PATH);
    _snwprintf(stinfo, MAX_PATH * 2, L"%s\\_files\\tools\\st-info.exe", dir);
    _snwprintf(stflash, MAX_PATH * 2, L"%s\\_files\\tools\\st-flash.exe", dir);
    _snwprintf(firmware, MAX_PATH * 2, L"%s\\_files\\firmware\\xlat.bin", dir);
    _snwprintf(log, MAX_PATH * 2, L"%s\\_files\\flash.log", dir);
    _snwprintf(driverbat, MAX_PATH * 2, L"%s\\_files\\install_driver_silent.bat", dir);

    /* 1. 检测设备 */
    int detected = probe_device(stinfo, cmd, 4096, log);
    if (!detected) {
        int ans = MessageBoxW(NULL,
                              L"没有找到 XLAT / ST-Link。\n\n"
                              L"请先确认：\n"
                              L"1. 已用 mini-USB 线把板子连到电脑；\n"
                              L"2. 板子的电源指示灯已亮。\n\n"
                              L"是否现在自动安装 ST-LINK 官方驱动？\n"
                              L"（会弹出一次 Windows 管理员授权）",
                              L"未检测到设备",
                              MB_YESNO | MB_ICONQUESTION | MB_SETFOREGROUND);
        if (ans == IDYES) {
            HWND prog = show_progress(hInst,
                                      L"正在安装驱动",
                                      L"正在安装 ST-LINK 官方驱动，请允许管理员授权...");
            int drv_code = run_elevated_bat(driverbat, prog);
            DestroyWindow(prog);

            if (drv_code == 0) {
                detected = probe_device(stinfo, cmd, 4096, log);
            }
        }

        if (!detected) {
            char *raw = read_file_ansi(log);
            wchar_t *detail = ansi_to_wide(raw ? raw : "No st-info output.");
            wchar_t buf[2048];
            if (detail) {
                _snwprintf(buf, 2048,
                           L"驱动安装后仍未检测到设备。\n\n"
                           L"请重新插拔一次 mini-USB 线，再打开本程序。\n\n"
                           L"st-info 输出：\n%s",
                           detail);
                HeapFree(GetProcessHeap(), 0, detail);
            } else {
                wcsncpy(buf, L"驱动安装后仍未检测到设备。\n\n请重新插拔一次 mini-USB 线，再打开本程序。", 2047);
                buf[2047] = 0;
            }
            if (raw) {
                HeapFree(GetProcessHeap(), 0, raw);
            }
            msgbox(L"未检测到设备",
                   buf,
                   MB_ICONERROR);
            return 1;
        }
    }

    /* Ensure stlink chip database exists at the path expected by st-flash.exe */
    wchar_t program_files[MAX_PATH];
    wchar_t chip_db[MAX_PATH * 2];
    DWORD pf_len = GetEnvironmentVariableW(L"ProgramFiles(x86)", program_files, MAX_PATH);
    if (pf_len == 0 || pf_len >= MAX_PATH) {
        pf_len = GetEnvironmentVariableW(L"ProgramFiles", program_files, MAX_PATH);
    }
    if (pf_len > 0 && pf_len < MAX_PATH) {
        _snwprintf(chip_db, MAX_PATH * 2,
                   L"%s\\stlink\\config\\chips\\F74x_F75x.chip", program_files);
        if (GetFileAttributesW(chip_db) == INVALID_FILE_ATTRIBUTES) {
            HWND prep = show_progress(hInst,
                                      L"正在准备 ST-LINK 配置",
                                      L"正在补齐芯片配置文件，请允许管理员授权...");
            run_elevated_bat(driverbat, prep);
            DestroyWindow(prep);
        }
    }

    /* 2. 确认 */
    int ans = MessageBoxW(NULL,
                          L"已检测到设备。\n\n即将刷入 XLAT 固件（默认英文，可在设置中切换中文），预计约 15 秒。\n期间请勿断开 USB。是否继续？",
                          L"准备刷机",
                          MB_YESNO | MB_ICONQUESTION | MB_SETFOREGROUND);
    if (ans != IDYES) {
        return 0;
    }

    /* 3. 刷机(带进度窗口) */
    HWND prog = show_progress(hInst,
                              L"正在刷机",
                              L"正在擦除并写入固件，请勿断开 USB...");
    _snwprintf(cmd, 4096, L"\"%s\" --connect-under-reset write \"%s\" 0x08000000",
               stflash, firmware);
    int code = run_capture(cmd, log, dir, prog);
    DestroyWindow(prog);

    char *log_text = read_file_ansi(log);
    int ok = (code == 0) && log_text && strstr(log_text, "jolly good") != NULL;

    /* 4. 结果 */
    if (ok) {
        if (log_text) {
            HeapFree(GetProcessHeap(), 0, log_text);
        }
        msgbox(L"刷机成功",
               L"XLAT 固件已刷入并通过校验。\n\n"
               L"重新插拔一次电源，界面默认英文，可在设置中切换中文。",
               MB_ICONINFORMATION);
    } else {
        wchar_t *detail = ansi_to_wide(log_text ? log_text : "No st-flash output.");
        wchar_t buf[4096];
        if (detail) {
            _snwprintf(buf, 4096,
                       L"刷机过程中出错了。\n\n"
                       L"请重新插拔 USB 后再试一次。\n\n"
                       L"st-flash 输出：\n%s",
                       detail);
            HeapFree(GetProcessHeap(), 0, detail);
        } else {
            wcsncpy(buf, L"刷机过程中出错了。\n\n请重新插拔 USB 后再试一次。", 4095);
            buf[4095] = 0;
        }
        if (log_text) {
            HeapFree(GetProcessHeap(), 0, log_text);
        }
        msgbox(L"刷机失败",
               buf,
               MB_ICONERROR);
        return 1;
    }
    return 0;
}

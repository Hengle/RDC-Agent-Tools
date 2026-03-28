from __future__ import annotations

import ctypes
import threading
import time
from ctypes import wintypes
from typing import Callable, Optional


WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
PM_REMOVE = 0x0001
CW_USEDEFAULT = 0x80000000
WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_EX_CLIENTEDGE = 0x00000200
SW_SHOW = 5
IDC_ARROW = 32512
COLOR_WINDOW = 5


WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
    ]


_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32
_WNDPROC_REGISTRY: dict[int, "PreviewWindowHost"] = {}
_CLASS_LOCK = threading.Lock()
_CLASS_NAME = "RdxPreviewWindow"
_CLASS_READY = False


@WNDPROC
def _window_proc(hwnd: int, msg: int, wparam: int, lparam: int) -> int:
    host = _WNDPROC_REGISTRY.get(int(hwnd))
    if msg == WM_CLOSE:
        _user32.DestroyWindow(hwnd)
        return 0
    if msg == WM_DESTROY:
        if host is not None:
            host._destroyed.set()
        _user32.PostQuitMessage(0)
        return 0
    return _user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def _ensure_window_class() -> None:
    global _CLASS_READY
    with _CLASS_LOCK:
        if _CLASS_READY:
            return
        hinstance = _kernel32.GetModuleHandleW(None)
        window_class = WNDCLASSW()
        window_class.style = 0
        window_class.lpfnWndProc = _window_proc
        window_class.cbClsExtra = 0
        window_class.cbWndExtra = 0
        window_class.hInstance = hinstance
        window_class.hIcon = None
        window_class.hCursor = _user32.LoadCursorW(None, ctypes.c_void_p(IDC_ARROW))
        window_class.hbrBackground = wintypes.HBRUSH(COLOR_WINDOW + 1)
        window_class.lpszMenuName = None
        window_class.lpszClassName = _CLASS_NAME
        atom = _user32.RegisterClassW(ctypes.byref(window_class))
        if atom == 0:
            error = ctypes.GetLastError()
            # Class already exists.
            if error != 1410:
                raise OSError(f"RegisterClassW failed: {error}")
        _CLASS_READY = True


class PreviewWindowHost:
    def __init__(
        self,
        *,
        title: str,
        width: int = 1280,
        height: int = 720,
        on_closed: Optional[Callable[[bool], None]] = None,
    ) -> None:
        self.title = str(title or "RDX Preview")
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self.on_closed = on_closed
        self.hwnd: int = 0
        self._thread: Optional[threading.Thread] = None
        self._ready = threading.Event()
        self._destroyed = threading.Event()
        self._stop_requested = threading.Event()
        self._close_reason = "user"
        self._startup_error = ""

    def start(self, *, timeout_s: float = 5.0) -> int:
        if self._thread is not None and self._thread.is_alive() and self.hwnd:
            return int(self.hwnd)
        self._ready.clear()
        self._destroyed.clear()
        self._stop_requested.clear()
        self._close_reason = "user"
        self._startup_error = ""
        self._thread = threading.Thread(target=self._run, name="rdx-preview-window", daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=max(0.1, float(timeout_s))):
            raise TimeoutError("Preview window did not become ready")
        if self._startup_error:
            raise RuntimeError(self._startup_error)
        if not self.hwnd:
            raise RuntimeError("Preview window was not created")
        return int(self.hwnd)

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and bool(self.hwnd)

    def close(self, *, by_user: bool = False, timeout_s: float = 2.0) -> None:
        if by_user:
            self._close_reason = "user"
        else:
            self._close_reason = "runtime"
        self._stop_requested.set()
        hwnd = int(self.hwnd or 0)
        if hwnd:
            _user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        thread = self._thread
        if thread is not None:
            thread.join(timeout=max(0.1, float(timeout_s)))

    def set_title(self, title: str) -> None:
        self.title = str(title or self.title)
        hwnd = int(self.hwnd or 0)
        if hwnd:
            _user32.SetWindowTextW(hwnd, self.title)

    def _run(self) -> None:
        hwnd = 0
        try:
            _ensure_window_class()
            hinstance = _kernel32.GetModuleHandleW(None)
            hwnd = _user32.CreateWindowExW(
                WS_EX_CLIENTEDGE,
                _CLASS_NAME,
                self.title,
                WS_OVERLAPPEDWINDOW,
                CW_USEDEFAULT,
                CW_USEDEFAULT,
                self.width,
                self.height,
                None,
                None,
                hinstance,
                None,
            )
            if not hwnd:
                raise OSError(f"CreateWindowExW failed: {ctypes.GetLastError()}")
            self.hwnd = int(hwnd)
            _WNDPROC_REGISTRY[int(hwnd)] = self
            _user32.ShowWindow(hwnd, SW_SHOW)
            _user32.UpdateWindow(hwnd)
        except Exception as exc:  # noqa: BLE001
            self._startup_error = f"{exc.__class__.__name__}: {exc}"
            self._ready.set()
            return

        self._ready.set()
        msg = MSG()
        try:
            while True:
                while _user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                    _user32.TranslateMessage(ctypes.byref(msg))
                    _user32.DispatchMessageW(ctypes.byref(msg))
                    if msg.message == 0x0012:  # WM_QUIT
                        return
                if self._stop_requested.wait(0.02):
                    if int(self.hwnd or 0):
                        _user32.PostMessageW(int(self.hwnd), WM_CLOSE, 0, 0)
                if self._destroyed.is_set():
                    return
                time.sleep(0.02)
        finally:
            if hwnd:
                _WNDPROC_REGISTRY.pop(int(hwnd), None)
            closed_by_user = self._close_reason == "user"
            self.hwnd = 0
            if self.on_closed is not None:
                try:
                    self.on_closed(closed_by_user)
                except Exception:
                    pass

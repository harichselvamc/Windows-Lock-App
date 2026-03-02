import psutil
import ctypes
from ctypes import wintypes
from PySide6.QtCore import QObject, Signal

# Windows Constants
EVENT_SYSTEM_FOREGROUND = 0x0003
WINEVENT_OUTOFCONTEXT = 0x0000

# Function pointer type for the callback
WinEventProcType = ctypes.WINFUNCTYPE(
    None, 
    wintypes.HANDLE, 
    wintypes.DWORD, 
    wintypes.HWND, 
    wintypes.LONG, 
    wintypes.LONG, 
    wintypes.DWORD, 
    wintypes.DWORD
)

def get_process_info_from_hwnd(hwnd):
    try:
        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process = psutil.Process(pid.value)
        ppid = process.ppid()
        return process.name(), pid.value, ppid
    except Exception:
        return None, None, None

class ProcessMonitor(QObject):
    app_detected = Signal(str)

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.unlocked_pids = set()
        self.hook = None
        self.last_trapped_pid = None
        self.last_trapped_ppid = None
        
        # Keep references to avoid GC
        self._callback = WinEventProcType(self.callback)

    def start(self):
        # Listen for foreground window changes
        self.hook = ctypes.windll.user32.SetWinEventHook(
            EVENT_SYSTEM_FOREGROUND,
            EVENT_SYSTEM_FOREGROUND,
            0,
            self._callback,
            0,
            0,
            WINEVENT_OUTOFCONTEXT
        )

    def callback(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        if event == EVENT_SYSTEM_FOREGROUND:
            name, pid, ppid = get_process_info_from_hwnd(hwnd)
            protected_apps = self.config_manager.get_protected_apps()
            
            if name and name in protected_apps:
                # Check if PID or Parent PID is unlocked
                is_unlocked = (pid in self.unlocked_pids) or (ppid in self.unlocked_pids)
                
                if not is_unlocked:
                    self.last_trapped_pid = pid
                    self.last_trapped_ppid = ppid
                    self.app_detected.emit(name)
            
            # Maintenance: Clean up PIDs that are no longer running
            self._prune_pids()

    def _prune_pids(self):
        active_pids = set(psutil.pids())
        self.unlocked_pids &= active_pids

    def mark_unlocked(self):
        # Authorize the last trapped process tree
        if self.last_trapped_pid:
            self.unlocked_pids.add(self.last_trapped_pid)
        if self.last_trapped_ppid:
            self.unlocked_pids.add(self.last_trapped_ppid)
        
        self.last_trapped_pid = None
        self.last_trapped_ppid = None

    def stop(self):
        if self.hook:
            ctypes.windll.user32.UnhookWinEvent(self.hook)
            self.hook = None

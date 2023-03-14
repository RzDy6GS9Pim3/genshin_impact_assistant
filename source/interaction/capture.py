import threading
from source.util import *
from source.common import timer_module
import numpy as np
from source.common import static_lib


class Capture():
    def __init__(self):
        self.capture_cache = np.zeros_like((1080,1920,3), dtype="uint8")
        self.max_fps = 180
        self.fps_timer = timer_module.Timer(diff_start_time=1)
        self.capture_cache_lock = threading.Lock()
        self.capture_times = 0

    def _get_capture(self) -> np.ndarray:
        """
        需要根据不同设备实现该函数。
        """
    
    def _check_shape(self, img:np.ndarray):
        if img is None:
            return False
        if img.shape == [1080,1920,4] or img.shape == [768,1024,3]:
            return True
        else:
            return False
        

    def capture(self, is_next_img = False) -> np.ndarray:
        """
        is_next_img: 强制截取下一张图片
        """
        self._capture(is_next_img)
        self.capture_cache_lock.acquire()
        cp = self.capture_cache.copy()
        self.capture_cache_lock.release()
        return cp
    
    def _capture(self, is_next_img) -> None:
        if (self.fps_timer.get_diff_time() >= 1/self.max_fps) or is_next_img:
            # testt=time.time()
            self.fps_timer.reset()
            self.capture_cache_lock.acquire()
            self.capture_times+=1
            self.capture_cache = self._get_capture()
            while 1:
                self.capture_cache = self._get_capture()
                if not self._check_shape(self.capture_cache):
                    logger.warning(
                        t2t("Fail to get capture: ")+
                        f"shape: {self.capture_cache.shape},"+
                        t2t(" waiting 2 sec."))
                    time.sleep(2)
                else:
                    break
            self.capture_cache_lock.release()
            # print(time.time()-testt)
        else:
            pass
    
from ctypes.wintypes import RECT
import win32print, win32api

class WindowsCapture(Capture):
    """
    支持Windows10, Windows11的截图。
    """
    GetDC = ctypes.windll.user32.GetDC
    CreateCompatibleDC = ctypes.windll.gdi32.CreateCompatibleDC
    GetClientRect = ctypes.windll.user32.GetClientRect
    CreateCompatibleBitmap = ctypes.windll.gdi32.CreateCompatibleBitmap
    SelectObject = ctypes.windll.gdi32.SelectObject
    BitBlt = ctypes.windll.gdi32.BitBlt
    SRCCOPY = 0x00CC0020
    GetBitmapBits = ctypes.windll.gdi32.GetBitmapBits
    DeleteObject = ctypes.windll.gdi32.DeleteObject
    ReleaseDC = ctypes.windll.user32.ReleaseDC
    GetDeviceCaps = win32print.GetDeviceCaps
    

    def __init__(self):
        static_lib.HANDLE = static_lib.HANDLE
        super().__init__()
        self.max_fps = 30
        self.scale_factor = self._get_screen_scale_factor()
        
    def _check_shape(self, img:np.ndarray):
        if img.shape == (1080,1920,4):
            return True
        else:
            logger.info(t2t("research handle"))
            static_lib.search_handle()
            return False
    
    def _get_screen_scale_factor(self):
        monitor = win32api.EnumDisplayMonitors()[0][0]

        # Get a pointer to a DEVICE_SCALE_FACTOR value
        scale_factor = ctypes.c_int()

        # Call the GetScaleFactorForMonitor function with the monitor handle and scale factor pointer
        ctypes.windll.shcore.GetScaleFactorForMonitor(ctypes.c_int(monitor), ctypes.byref(scale_factor))

        # Print the scale factor value
        return float(scale_factor.value/100)
    
    def _get_capture(self):
        r = RECT()
        self.GetClientRect(static_lib.HANDLE, ctypes.byref(r))
        width, height = r.right, r.bottom
        # left, top, right, bottom = win32gui.GetWindowRect(static_lib.HANDLE)
        # 获取桌面缩放比例
        #desktop_dc = self.GetDC(0)
        #scale_x = self.GetDeviceCaps(desktop_dc, 88)
        #scale_y = self.GetDeviceCaps(desktop_dc, 90)

        # 计算实际截屏区域大小
        width = int(int(width)*self.scale_factor)
        height = int(int(height)*self.scale_factor)
        
        # 开始截图
        dc = self.GetDC(static_lib.HANDLE)
        cdc = self.CreateCompatibleDC(dc)
        bitmap = self.CreateCompatibleBitmap(dc, width, height)
        self.SelectObject(cdc, bitmap)
        self.BitBlt(cdc, 0, 0, width, height, dc, 0, 0, self.SRCCOPY)
        # 截图是BGRA排列，因此总元素个数需要乘以4
        total_bytes = width * height * 4
        buffer = bytearray(total_bytes)
        byte_array = ctypes.c_ubyte * total_bytes
        self.GetBitmapBits(bitmap, total_bytes, byte_array.from_buffer(buffer))
        self.DeleteObject(bitmap)
        self.DeleteObject(cdc)
        self.ReleaseDC(static_lib.HANDLE, dc)
        # 返回截图数据为numpy.ndarray
        ret = np.frombuffer(buffer, dtype=np.uint8).reshape(height, width, 4)
        return ret
    
class EmulatorCapture(Capture):
    def __init__(self):
        super().__init__()
    
    def _get_capture(self):
        pass
    
if __name__ == '__main__':
    wc = WindowsCapture()
    while 1:
        cv2.imshow("capture test", wc.capture())
        cv2.waitKey(10)
        # time.sleep(0.01)
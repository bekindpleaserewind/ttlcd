import time
import psutil

from PIL import Image

ROTATE_TOP = 0
ROTATE_LEFT = 90
ROTATE_BOTTOM = 180
ROTATE_RIGHT = 270

# Do not adjust image defaults unless you know what you are doing.
# You run the risk of bricking your device.
IMAGE_DEFAULT_RESOLUTION = (480, 128)
IMAGE_DEFAULT_DPI = (300, 300)

class ImagePostProcess:
    def __init__(self, image_path):
        self.image_path = image_path
    
    def process(self, orientation = ROTATE_TOP, quality = 80, optimize = False):
        image = Image.open(self.image_path)

        # We always make sure we have the correct image settings.
        # This is to avoid bricking the lcd (again).
        #   resolution of 480x128
        #   dpi of 300x300
        #   progressive should be disabled
        image = image.resize(size = IMAGE_DEFAULT_RESOLUTION)

        # Rotate the specified amount if provided
        if orientation > 0:
            image = image.rotate(orientation)

        image.save(self.image_path, "JPEG", quality = quality, optimize = optimize, dpi = IMAGE_DEFAULT_DPI, progressive = False)

class NetworkStatistics:
    def throughput(self, interval = 1):
        before = psutil.net_io_counters()
        time.sleep(interval)
        after = psutil.net_io_counters()

        recv_bps = round(after.bytes_recv - before.bytes_recv, 2)
        recv_kbps = round(recv_bps / 1024, 2)
        recv_mbps = round(recv_bps / 1024 / 1024, 2)

        sent_bps = round(after.bytes_sent - before.bytes_sent, 2)
        sent_kbps = round(sent_bps / 1024, 2)
        sent_mbps = round(sent_bps / 1024 / 1024, 2)

        return({
            'recv': {
                'bps': recv_bps,
                'kbps': recv_kbps,
                'mbps': recv_mbps,
            },
            'send': {
                'bps': sent_bps,
                'kbps': sent_kbps,
                'mbps': sent_mbps,
            }
        })

    def total(self):
        data = psutil.net_io_counters()

        recv_bps = round(data.bytes_recv, 2)
        recv_kbps = round(recv_bps / 1024, 2)
        recv_mbps = round(recv_bps / 1024 / 1024, 2)

        sent_bps = round(data.bytes_sent, 2)
        sent_kbps = round(sent_bps / 1024, 2)
        sent_mbps = round(sent_bps / 1024 / 1024, 2)

        return({
            'recv': {
                'bps': recv_bps,
                'kbps': recv_kbps,
                'mbps': recv_mbps,
            },
            'send': {
                'bps': sent_bps,
                'kbps': sent_kbps,
                'mbps': sent_mbps,
            }
        })

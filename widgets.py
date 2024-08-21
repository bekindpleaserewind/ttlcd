import os
import ast
import math
import time
import datetime
import psutil
import uptime
import kubernetes
import prometheus_api_client as prom

from PIL import Image, ImageDraw, ImageFont, ImageColor

import util

IMAGE_PATH = None

WIDGET_TYPE_TEXT = 10
WIDGET_TYPE_BAR = 20

ORIENTATION_VERTICAL = 10
ORIENTATION_HORIZONTAL = 20

CPU_LAST_POLL = 0
CPU_LAST_VALUE = 0

class Widget:
    def __init__(self, config, tmpdir, logger):
        self.config = config
        self.value = None
        self.node = None
        self.tmpdir = tmpdir
        self.logger = logger
        self.background_file = None
        self.x = 0
        self.y = 0
        self.font_file = None
        self.font_size = 14
        self.font_color = (255, 255, 255)
        self.line_length = 0
        self.line_space = 0
        self.bar_direction = None
        self.bar_width = 0
        self.bar_height = 0
        self.bar_scale = 10
        self.bar_fill_color = 'yellow'
        self.bar_outline_color = 'red'
        self.orientation = ORIENTATION_VERTICAL
        self.widget_type = 0
        self.prometheus_url = None
        self.prometheus_url_disable_ssl = True


    def tick(self):
        """ Override this function """
        pass

    def get(self):
        return(self.value)

    def set_image_path(self, path):
        global IMAGE_PATH
        IMAGE_PATH = path

    def set_background(self, background_file = None):
        if background_file is None:
            self.background_file = self.config.get('background')
        else:
            self.background_file = background_file

        if not os.path.exists(self.background_file):
            return(1)

        return(0)

    def set_font(self, font_file = None):
        if font_file is None:
            self.font_file = self.config.get('font_file', None)
        else:
            self.font_file = font_file

        if not os.path.exists(self.font_file):
            return(1)

        return(0)

    def set_font_size(self, font_size = None):
        if font_size is not None:
            self.font_size = font_size
        else:
            self.font_size = self.config.get('font_size')

    def set_font_color(self, font_color = None):
        if font_color is not None:
            self.font_color = font_color
            if type(self.font_color) == str:
                self.font_color = ImageColor.getcolor(self.font_color, "RGB")
                #self.font_color = ast.literal_eval(self.font_color)
        else:
            self.font_color = self.config.get('font_color')
            if type(self.font_color) == str:
                self.font_color = ImageColor.getcolor(self.font_color, "RGB")
                #self.font_color = ast.literal_eval(self.font_color)

    def set_line_length(self, line_length = None):
        if line_length is not None:
            self.line_length = line_length
        else:
            self.line_length = self.config.get('line_length')

    def set_line_space(self, line_space = None):
        if line_space is not None:
            self.line_space = line_space
        else:
            self.line_space = self.config.get('line_space')

    def set_x(self, x = None):
        if x is not None:
            self.x = x
        else:
            self.x = 0

    def set_y(self, y = None):
        if y is not None:
            self.y = y 
        else:
            self.y = 0

    def set_bar_width(self, bar_width = 60):
        self.bar_width = bar_width
    
    def set_bar_height(self, bar_height = 20):
        self.bar_height = bar_height
    
    def set_bar_scale(self, bar_scale = 20):
        self.bar_scale = bar_scale

    def set_bar_fill_color(self, bar_fill_color = 'yellow'):
        self.bar_fill_color = bar_fill_color
    
    def set_bar_outline_color(self, bar_outline_color = 'red'):
        self.bar_outline_color = bar_outline_color
    
    def set_type(self, widget_type):
        self.widget_type = widget_type

    def set_orientation(self, orientation):
        self.orientation = orientation

    def set_bar_direction(self, direction):
        self.bar_direction = direction

    def set_prometheus_url(self, url, ssl = False):
        self.prometheus_url = url

    def set_prometheus_url_disable_ssl(self, ssl = True):
        self.prometheus_url_disable_ssl = ssl

    def get_background(self):
        return(self.background_file)

    def get_image_path(self):
        global IMAGE_PATH
        return(IMAGE_PATH)

    def get_x(self):
        return(self.x)
    
    def get_y(self):
        return(self.y)

    def get_location(self):
        return((self.get_x(), self.get_y()))

    def get_font(self):
        return(self.font_file)

    def get_font_size(self):
        return(self.font_size)

    def get_font_color(self):
        return(self.font_color)
    
    def get_line_length(self):
        return(self.line_length)

    def get_line_space(self):
        return(self.line_space)

    def clear(self):
        global IMAGE_PATH
        if IMAGE_PATH is not None and os.path.exists(IMAGE_PATH):
            os.remove(IMAGE_PATH)
            IMAGE_PATH = None

    def draw(self):
        self.tick()

        if self.get_image_path() is None and self.get_background() is not None:
            image = Image.open(self.get_background())
            self.set_image_path(os.path.join(self.tmpdir.name, 'screen.jpg'))
        else:
            try:
                image = Image.open(self.get_image_path())
            except Exception as e:
                self.logger.error("failed to open image %s", str(e))
                return(False)

        draw = ImageDraw.Draw(image)

        if self.widget_type == WIDGET_TYPE_TEXT:
            f = ImageFont.truetype(self.get_font(), self.get_font_size())

            # Where to place us on the screen
            loc = self.get_location()

            if type(self.value) == list or type(self.value) == tuple:
                for value in self.value:
                    if self.line_length <= 0:
                        draw.text(loc, str(value), fill = self.get_font_color(), font = f)
                    else:
                        if len(str(value)) > self.line_length:
                            draw.text(loc, str(value)[0:self.line_length - 3] + "...", fill = self.get_font_color(), font = f)
                        else:
                            draw.text(loc, str(value), fill = self.get_font_color(), font = f)
                    loc = (loc[0], int(loc[1]) + int(self.get_font_size()) + int(self.line_space))
            else:
                if self.line_length <= 0:
                    draw.text(loc, str(self.value), fill = self.get_font_color(), font = f)
                else:
                    if len(str(self.value)) > self.line_length:
                        draw.text(loc, str(self.value)[0:self.line_length - 3] + "...", fill = self.get_font_color(), font = f)
                    else:
                        draw.text(loc, str(self.value)[0:self.line_length], fill = self.get_font_color(), font = f)
        elif self.widget_type == WIDGET_TYPE_BAR:
            # number of bars to display
            bar_step = 100 / self.bar_scale
            # index of current bar to display
            bar_index = 0

            start_xy = False
            stop_xy = False

            if self.value <= 0 or self.value < bar_step:
                value = 1
            else:
                value = math.floor(self.value / bar_step)

            if self.orientation == ORIENTATION_VERTICAL:
                if self.bar_direction == 'up':
                    start_xy = (self.x, self.y)
                elif self.bar_direction == 'down':
                    start_xy = (self.x, self.y)
                else:
                    self.logger.warning("invalid direction for orientation")
                    return(False)
            elif self.orientation == ORIENTATION_HORIZONTAL:
                if self.bar_direction == 'right':
                    start_xy = (self.x, self.y)
                elif self.bar_direction == 'left':
                    start_xy = (self.x - self.bar_height, self.y)
                else:
                    self.logger.warning("invalid direction for orientation")
                    return(False)
            else:
                self.logger.warning("invalid orientation specified")
                return(False)

            if self.orientation == ORIENTATION_VERTICAL:
                if self.bar_direction == 'up':
                    stop_xy = (start_xy[0] + self.bar_width, start_xy[1] + self.bar_height)
                elif self.bar_direction == 'down':
                    stop_xy = (start_xy[0] + self.bar_width, start_xy[1] + self.bar_height)
                else:
                    self.logger.warning("invalid direction for orientation")
                    return(False)
            elif self.orientation == ORIENTATION_HORIZONTAL:
                if self.bar_direction == 'right':
                    stop_xy = (self.x + self.bar_height, self.y + self.bar_width)
                elif self.bar_direction == 'left':
                    stop_xy = (self.x, self.y + self.bar_width)
                else:
                    self.logger.warning("invalid direction for orientation")
                    return(False)
            else:
                self.logger.warning("invalid orientation specified")
                return(False)

            while bar_index < value:
                draw.rectangle([start_xy, stop_xy], fill = self.bar_fill_color, outline = self.bar_outline_color)

                if self.orientation == ORIENTATION_VERTICAL:
                    if self.bar_direction == 'up':
                        start_xy = (start_xy[0], start_xy[1] - self.bar_height)
                        stop_xy = (self.x + self.bar_width, start_xy[1] + self.bar_height)
                    elif self.bar_direction == 'down':
                        start_xy = (start_xy[0], start_xy[1] + self.bar_height)
                        stop_xy = (self.x + self.bar_width, start_xy[1] + self.bar_height)
                    else:
                        self.logger.warning("invalid direction for orientation")
                        return(False)
                elif self.orientation == ORIENTATION_HORIZONTAL:
                    if self.bar_direction == 'right':
                        start_xy = (start_xy[0] + self.bar_height, self.y)
                        stop_xy = (stop_xy[0] + self.bar_height, self.y + self.bar_width)
                    elif self.bar_direction == 'left':
                        start_xy = (start_xy[0] - self.bar_height, self.y)
                        stop_xy = (stop_xy[0] - self.bar_height, self.y + self.bar_width)
                        self.logger.info("start_xy %s\tstop_xy %s", start_xy, stop_xy)
                    else:
                        self.logger.warning("invalid direction for orientation")
                        return(False)
                else:
                    self.logger.warning("invalid orientation specified")
                    return(False)

                bar_index = bar_index + 1

        image.save(self.get_image_path(), "JPEG", progressive = False, quality = 80, optimize = True)
    
    def get_tmpdir(self):
        return(self.tmpdir)

    def cleanup(self):
        if self.tmpdir is not None:
            self.tmpdir.cleanup()
    
    def setup(self):
        pass

    def shutdown(self):
        pass

class Text(Widget):
    def __init__(self, config, tmpdir, logger):
        super().__init__(config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('x'))
        self.set_y(self.config.get('y'))
        self.set_font(self.config.get('font_file'))
        self.set_font_size(self.config.get('font_size'))
        self.set_font_color(self.config.get('font_color'))

    def tick(self):
        self.value = self.config.get('string')

class Date(Widget):
    def __init__(self, config, tmpdir, logger):
        super().__init__(config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('date_x'))
        self.set_y(self.config.get('date_y'))
        self.set_font(self.config.get('date_font_file'))
        self.set_font_size(self.config.get('date_font_size'))
        self.set_font_color(self.config.get('date_font_color'))

    def tick(self):
        self.value = str(datetime.datetime.now()).split(" ")[0]

class Time(Widget):
    def __init__(self, config, tmpdir, logger):
        super().__init__(config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('time_x'))
        self.set_y(self.config.get('time_y'))
        self.set_font(self.config.get('time_font_file'))
        self.set_font_size(self.config.get('time_font_size'))
        self.set_font_color(self.config.get('time_font_color'))

    def tick(self):
        self.value = str(datetime.datetime.now()).split(" ")[1].split(".")[0]

class CpuUtilization(Widget):
    def __init__(self, config, tmpdir, logger):
        Widget.__init__(self, config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('cpu_utilization_x'))
        self.set_y(self.config.get('cpu_utilization_y'))
        self.set_font(self.config.get('cpu_utilization_font_file'))
        self.set_font_size(self.config.get('cpu_utilization_font_size'))
        self.set_font_color(self.config.get('cpu_utilization_font_color'))

    def tick(self):
        global CPU_LAST_POLL, CPU_LAST_VALUE

        now = time.time()

        if now - CPU_LAST_POLL >= 1:
            self.value = str(psutil.cpu_percent()).rjust(5, ' ')
            CPU_LAST_POLL = now
            CPU_LAST_VALUE = self.value
        else:
            self.value = str(CPU_LAST_VALUE).rjust(5, ' ')

class CpuUtilizationBar(Widget):
    def __init__(self, config, tmpdir, logger):
        super().__init__(config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_BAR)

        if self.config.get('cpu_utilization_bar_orientation', 'vertical') == 'vertical':
            self.set_orientation(ORIENTATION_VERTICAL)
        elif self.config.get('cpu_utilization_bar_orientation', 'horizontal') == 'horizontal':
            self.set_orientation(ORIENTATION_HORIZONTAL)

        self.set_background(background)

        if self.config.get('cpu_utilization_bar_orientation', 'vertical') == 'vertical':
            self.set_bar_direction(self.config.get('cpu_utilization_bar_direction', 'up'))
        elif self.config.get('cpu_utilization_bar_orientation', 'horizontal') == 'horizontal':
            self.set_bar_direction(self.config.get('cpu_utilization_bar_direction', 'right'))

        self.set_x(self.config.get('cpu_utilization_bar_x'))
        self.set_y(self.config.get('cpu_utilization_bar_y'))
        self.set_bar_width(self.config.get('cpu_utilization_bar_width'))
        self.set_bar_height(self.config.get('cpu_utilization_bar_height'))
        self.set_bar_scale(self.config.get('cpu_utilization_bar_scale'))
        self.set_bar_fill_color(self.config.get('cpu_utilization_bar_fill_color', 'yellow'))
        self.set_bar_outline_color(self.config.get('cpu_utilization_bar_outline_color', 'red'))

    def tick(self):
        global CPU_LAST_POLL, CPU_LAST_VALUE

        now = time.time()

        if now - CPU_LAST_POLL >= 1:
            self.value = psutil.cpu_percent()
            CPU_LAST_POLL = now
            CPU_LAST_VALUE = self.value
        else:
            self.value = CPU_LAST_VALUE

class RamAvailable(Widget):
    def __init__(self, config, tmpdir, logger):
        super().__init__(config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('ram_available_x'))
        self.set_y(self.config.get('ram_available_y'))
        self.set_font(self.config.get('ram_available_font_file'))
        self.set_font_size(self.config.get('ram_available_font_size'))
        self.set_font_color(self.config.get('ram_available_font_color'))

    def tick(self):
        mem = psutil.virtual_memory()
        self.value = "{}%".format(str(round(mem.available / mem.total * 100, 1)).rjust(3, ' '))

class RamUtilization(Widget):
    def __init__(self, config, tmpdir, logger):
        super().__init__(config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('ram_utilization_x'))
        self.set_y(self.config.get('ram_utilization_y'))
        self.set_font(self.config.get('ram_utilization_font_file'))
        self.set_font_size(self.config.get('ram_utilization_font_size'))
        self.set_font_color(self.config.get('ram_utilization_font_color'))

    def tick(self):
        mem = psutil.virtual_memory()
        self.value = "{}%".format(str(round(mem.used / mem.total * 100, 1)).rjust(3, ' '))

class RamUtilizationBar(Widget):
    def __init__(self, config, tmpdir, logger):
        super().__init__(config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_BAR)

        if self.config.get('ram_utilization_bar_orientation', 'vertical') == 'vertical':
            self.set_orientation(ORIENTATION_VERTICAL)
        elif self.config.get('ram_utilization_bar_orientation', 'horizontal') == 'horizontal':
            self.set_orientation(ORIENTATION_HORIZONTAL)

        self.set_background(background)

        if self.config.get('ram_utilization_bar_orientation', 'vertical') == 'vertical':
            self.set_bar_direction(self.config.get('ram_utilization_bar_direction', 'up'))
        elif self.config.get('ram_utilization_bar_orientation', 'horizontal') == 'horizontal':
            self.set_bar_direction(self.config.get('ram_utilization_bar_direction', 'right'))
        
        self.set_x(self.config.get('ram_utilization_bar_x'))
        self.set_y(self.config.get('ram_utilization_bar_y'))
        self.set_bar_width(self.config.get('ram_utilization_bar_width'))
        self.set_bar_height(self.config.get('ram_utilization_bar_height'))
        self.set_bar_scale(self.config.get('ram_utilization_bar_scale'))
        self.set_bar_fill_color(self.config.get('ram_utilization_bar_fill_color', 'yellow'))
        self.set_bar_outline_color(self.config.get('ram_utilization_bar_outline_color', 'red'))

    def tick(self):
        self.value = psutil.virtual_memory().percent

class LoadAverage(Widget):
    def __init__(self, config, tmpdir, logger):
        Widget.__init__(self, config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('loadavg_x'))
        self.set_y(self.config.get('loadavg_y'))
        self.set_font(self.config.get('loadavg_font_file'))
        self.set_font_size(self.config.get('loadavg_font_size'))
        self.set_font_color(self.config.get('loadavg_font_color'))

    def tick(self):
        self.value = psutil.getloadavg()
        self.value = str(round(self.value[0], 2)).rjust(5, ' ')

class IOWait(Widget):
    def __init__(self, config, tmpdir, logger):
        Widget.__init__(self, config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('iowait_x'))
        self.set_y(self.config.get('iowait_y'))
        self.set_font(self.config.get('iowait_font_file'))
        self.set_font_size(self.config.get('iowait_font_size'))
        self.set_font_color(self.config.get('iowait_font_color'))

    def tick(self):
        self.value = psutil.cpu_times().iowait
        self.value = str(round(self.value, 2)).rjust(5, ' ')

class NetworkThroughputSend(Widget):
    def __init__(self, config, tmpdir, logger):
        self.net_send = False
        Widget.__init__(self, config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('network_throughput_send_x'))
        self.set_y(self.config.get('network_throughput_send_y'))
        self.set_font(self.config.get('network_throughput_send_font_file'))
        self.set_font_size(self.config.get('network_throughput_send_font_size'))
        self.set_font_color(self.config.get('network_throughput_send_font_color'))

    def tick(self):
        if not self.net_send:
            self.net_send = util.NetworkStatistics(util.NETWORK_THROUGHPUT)
            self.net_send.start()

        tp = self.net_send.poll_throughput()
        if tp is not False:
            if tp['send']['bps'] < 1024:
                self.value = "{} B/s".format("%.2f" % tp['send']['kbps'],)
            elif tp['send']['bps'] >= 1024 and tp['send']['bps'] < 10000:
                self.value = "{} KB/s".format("%.2f" % tp['send']['kbps'],)
            else:
                self.value = "{} MB/s".format("%.2f" % tp['send']['mbps'],)
        else:
            self.value = "0 B/s"

    def shutdown(self):
        if self.net_send:
            self.net_send.shutdown()
        
class NetworkThroughputRecv(Widget):
    def __init__(self, config, tmpdir, logger):
        self.net_send = False
        Widget.__init__(self, config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('network_throughput_recv_x'))
        self.set_y(self.config.get('network_throughput_recv_y'))
        self.set_font(self.config.get('network_throughput_recv_font_file'))
        self.set_font_size(self.config.get('network_throughput_recv_font_size'))
        self.set_font_color(self.config.get('network_throughput_recv_font_color'))

    def tick(self):
        if not self.net_send:
            self.net_send = util.NetworkStatistics(util.NETWORK_THROUGHPUT)
            self.net_send.start()

        tp = self.net_send.poll_throughput()

        if tp is not False:
            if tp['recv']['bps'] < 1024:
                self.value = "{0} B/s".format("%.2f" % tp['recv']['kbps'],)
            elif tp['recv']['bps'] >= 1024 and tp['recv']['bps'] < 1024 * 1024:
                self.value = "{} KB/s".format("%.2f" % tp['recv']['kbps'],)
            else:
                self.value = "{} MB/s".format("%.2f" % tp['recv']['mbps'],)
        else:
            self.value = "0 B/s"
    
    def shutdown(self):
        if self.net_send:
            self.net_send.shutdown()

        
class NetworkThroughputRecvTotal(Widget):
    def __init__(self, config, tmpdir, logger):
        self.net_send = False
        Widget.__init__(self, config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('network_throughput_recv_total_x'))
        self.set_y(self.config.get('network_throughput_recv_total_y'))
        self.set_font(self.config.get('network_throughput_recv_total_font_file'))
        self.set_font_size(self.config.get('network_throughput_recv_total_font_size'))
        self.set_font_color(self.config.get('network_throughput_recv_total_font_color'))

    def tick(self):
        if not self.net_send:
            self.net_send = util.NetworkStatistics(util.NETWORK_TOTAL)
            self.net_send.start()

        tp = self.net_send.poll_total()

        if tp is not False:
            if tp['recv']['bps'] < 1024:
                self.value = "%.2f B/s" % (tp['recv']['kbps'],)
            elif tp['recv']['bps'] >= 1024 and tp['recv']['bps'] < 1024 * 1024:
                self.value = "%.2f KB/s" % (tp['recv']['kbps'],)
            else:
                self.value = "%.2f MB/s" % (tp['recv']['mbps'],)
        else:
            self.value = "0 B/s"

    def shutdown(self):
        if self.net_send:
            self.net_send.shutdown()

class NetworkThroughputSendTotal(Widget):
    def __init__(self, config, tmpdir, logger):
        self.net_send = False
        Widget.__init__(self, config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('network_throughput_send_total_x'))
        self.set_y(self.config.get('network_throughput_send_total_y'))
        self.set_font(self.config.get('network_throughput_send_total_font_file'))
        self.set_font_size(self.config.get('network_throughput_send_total_font_size'))
        self.set_font_color(self.config.get('network_throughput_send_total_font_color'))

    def tick(self):
        if not self.net_send:
            self.net_send = util.NetworkStatistics(util.NETWORK_TOTAL)
            self.net_send.start()

        tp = self.net_send.poll_total()

        if tp is not False:
            if tp['send']['bps'] < 1024:
                self.value = "%d B/s" % (tp['send']['kbps'],)
            elif tp['send']['bps'] >= 1024 and tp['send']['bps'] < 10000:
                self.value = "%d KB/s" % (tp['send']['kbps'],)
            else:
                self.value = "%d MB/s" % (tp['send']['mbps'],)
        else:
            self.value = "0 B/s"

    def shutdown(self):
        if self.net_send:
            self.net_send.shutdown()

class CpuFreq(Widget):
    def __init__(self, config, tmpdir, logger):
        Widget.__init__(self, config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('cpufreq_x'))
        self.set_y(self.config.get('cpufreq_y'))
        self.set_font(self.config.get('cpufreq_font_file'))
        self.set_font_size(self.config.get('cpufreq_font_size'))
        self.set_font_color(self.config.get('cpufreq_font_color'))

    def tick(self):
        self.value = psutil.cpu_freq().current
        self.value = "{} MHz".format(str(int(self.value)).rjust(5, ' '))

class Uptime(Widget):
    def __init__(self, config, tmpdir, logger):
        Widget.__init__(self, config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('uptime_x'))
        self.set_y(self.config.get('uptime_y'))
        self.set_font(self.config.get('uptime_font_file'))
        self.set_font_size(self.config.get('uptime_font_size'))
        self.set_font_color(self.config.get('uptime_font_color'))

    def tick(self):
        ut = uptime.uptime()
        if ut >= 86400:
            self.value = str("{} days".format(int(ut / 86400))).center(10, ' ')
        else:
            self.value = "0 days".center(10, ' ')

class KubernetesPodCount(Widget):
    def __init__(self, config, tmpdir, logger):
        Widget.__init__(self, config, tmpdir, logger)

    def setup(self, background):
        kubernetes.config.load_kube_config()
        self.client = kubernetes.client.CoreV1Api()
        self.network_client = kubernetes.client.NetworkingV1Api()

        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('kubernetes_pod_count_x'))
        self.set_y(self.config.get('kubernetes_pod_count_y'))
        self.set_font(self.config.get('kubernetes_pod_count_font_file'))
        self.set_font_size(self.config.get('kubernetes_pod_count_font_size'))
        self.set_font_color(self.config.get('kubernetes_pod_count_font_color'))

    def tick(self):
        r = self.client.list_pod_for_all_namespaces(watch=False)
        if len(r.items) < 10:
            self.value = " " + str(len(r.items)).center(3, ' ')
        else:
            self.value = str(len(r.items)).center(3, ' ')

class PrometheusNetworkThroughputRecv(Widget):
    def __init__(self, config, tmpdir, logger):
        self.net_send = False
        Widget.__init__(self, config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('prometheus_network_throughput_recv_x'))
        self.set_y(self.config.get('prometheus_network_throughput_recv_y'))
        self.set_font(self.config.get('prometheus_network_throughput_recv_font_file'))
        self.set_font_size(self.config.get('prometheus_network_throughput_recv_font_size'))
        self.set_font_color(self.config.get('prometheus_network_throughput_recv_font_color'))
        self.set_prometheus_url(self.config.get('prometheus_url'))
        self.set_prometheus_url_disable_ssl(self.config.get('prometheus_url_disable_ssl'))

        self.pclient = prom.PrometheusConnect(url = self.prometheus_url, disable_ssl=self.prometheus_url_disable_ssl)

    def tick(self):
        metrics = self.pclient.custom_query(query = 'irate(node_network_receive_bytes_total[1m])')
        if metrics:
            total = 0
            for m in metrics:
                total = total + float(m['value'][1])

            if total < 1024:
                self.value = "{} B/s".format("%.2f" % (total,))
            elif total >= 1024 and total < 1024 * 1024:
                self.value = "{} KB/s".format("%.2f" % (total / 1024,))
            else:
                self.value = "{} MB/s".format("%.2f" % (total / 1024 / 1024,))
        else:
            self.value = "0 B/s"
        
        self.logger.info(self.value)

class PrometheusNetworkThroughputSend(Widget):
    def __init__(self, config, tmpdir, logger):
        self.net_send = False
        Widget.__init__(self, config, tmpdir, logger)

    def setup(self, background):
        self.set_type(WIDGET_TYPE_TEXT)
        self.set_background(background)
        self.set_x(self.config.get('prometheus_network_throughput_send_x'))
        self.set_y(self.config.get('prometheus_network_throughput_send_y'))
        self.set_font(self.config.get('prometheus_network_throughput_send_font_file'))
        self.set_font_size(self.config.get('prometheus_network_throughput_send_font_size'))
        self.set_font_color(self.config.get('prometheus_network_throughput_send_font_color'))
        self.set_prometheus_url(self.config.get('prometheus_url'))
        self.set_prometheus_url_disable_ssl(self.config.get('prometheus_url_disable_ssl'))

        self.pclient = prom.PrometheusConnect(url = self.prometheus_url, disable_ssl=self.prometheus_url_disable_ssl)

    def tick(self):
        metrics = self.pclient.custom_query(query = 'irate(node_network_transmit_bytes_total[1m])')
        if metrics:
            total = 0
            for m in metrics:
                total = total + float(m['value'][1])

            if total < 1024:
                self.value = "{} B/s".format("%.2f" % (total,))
            elif total >= 1024 and total < 1024 * 1024:
                self.value = "{} KB/s".format("%.2f" % (total / 1024,))
            else:
                self.value = "{} MB/s".format("%.2f" % (total / 1024 / 1024,))
        else:
            self.value = "0 B/s"
        
        self.logger.info(self.value)
    
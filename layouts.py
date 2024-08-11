import os
import tempfile
from PIL import Image

import widgets
import util

class Overlay:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.tmpdir = tempfile.TemporaryDirectory()
        self.image_path = None

    def validate_config(self):
        """
        Override with config validation routines.
        Returns 0 on success, >0 on failure.
        """
        pass

    def set_background(self, background_file = None):
        if background_file is None:
            self.background_file = self.config.get('background')
        else:
            self.background_file = background_file

        if not os.path.exists(self.background_file):
            return(1)

        return(0)
    
    def get_background(self):
        return(self.background_file)

    def set_image_path(self, path):
        self.image_path = path
    
    def get_image_path(self):
        return(self.image_path)

class Kubernetes(Overlay):
    def __init__(self, config, logger):
        Overlay.__init__(self, config, logger)

    def validate_config(self):
        return(False)

    def setup(self):
        # Block execution if configuration is invalid
        if self.validate_config():
            return(True)

        # Use default background from configuration
        self.set_background()

        # Define where we store our screen jfif
        self.set_image_path(os.path.join(self.tmpdir.name, 'screen.jpg'))

        return(False)

    def display(self, orientation = 0, quality = 80, optimize = False):
        pass

class Node(Overlay):
    def __init__(self, config, logger):
        self.cpu_utilization = None
        self.text_widgets = []
        Overlay.__init__(self, config, logger)

    def validate_config(self):
        """
        Basic configuration validation
        """
        r = False
        
        # Validate required global variables exist
        for k in ['idVendor', 'idProduct', 'background', 'orientation', 'font_file', 'font_size', 'font_color', 'line_length', 'line_space']:
            if self.config.get(k) is None:
                self.logger.error("Missing configuration argument '%s'", k)
                r = True

        # Validate each widget argument when a widget is enabled
        if self.config.get('enable_date', False):
            for k in ['date_x', 'date_y']:
                if not self.config.get(k, False):
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        if self.config.get('enable_time', False):
            for k in ['time_x', 'time_y']:
                if not self.config.get(k, False):
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        if self.config.get('enable_cpu_utilization', False):
            for k in ['cpu_utilization_x', 'cpu_utilization_y']:
                if self.config.get(k) is None:
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        if self.config.get('enable_cpu_utilization_bar', False):
            for k in [
                'cpu_utilization_bar_x',
                'cpu_utilization_bar_y',
                'cpu_utilization_bar_orientation',
                'cpu_utilization_bar_direction',
                'cpu_utilization_bar_width',
                'cpu_utilization_bar_height',
                'cpu_utilization_bar_scale',
                'cpu_utilization_bar_fill_color',
                'cpu_utilization_bar_outline_color'
            ]:
                if self.config.get(k) is None:
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        if self.config.get('enable_ram_available', False):
            for k in ['ram_available_x', 'ram_available_y']:
                if self.config.get(k) is None:
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        if self.config.get('enable_ram_utilization', False):
            for k in ['ram_utilization_x', 'ram_utilization_y']:
                if self.config.get(k) is None:
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        if self.config.get('enable_ram_utilization_bar', False):
            for k in [
                'ram_utilization_bar_x',
                'ram_utilization_bar_y',
                'ram_utilization_bar_orientation',
                'ram_utilization_bar_direction',
                'ram_utilization_bar_width',
                'ram_utilization_bar_height',
                'ram_utilization_bar_scale',
                'ram_utilization_bar_fill_color',
                'ram_utilization_bar_outline_color'
            ]:
                if self.config.get(k) is None:
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        if self.config.get('enable_loadavg', False):
            for k in ['loadavg_x', 'loadavg_y', 'loadavg_line_space']:
                if self.config.get(k) is None:
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        if self.config.get('enable_network_throughput_send', False):
            for k in ['network_throughput_send_x', 'network_throughput_send_y']:
                if self.config.get(k) is None:
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        if self.config.get('enable_network_throughput_recv', False):
            for k in ['network_throughput_recv_x', 'network_throughput_recv_y']:
                if self.config.get(k) is None:
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        if self.config.get('enable_network_throughput_send_total', False):
            for k in ['network_throughput_send_total_x', 'network_throughput_send_total_y']:
                if self.config.get(k) is None:
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        if self.config.get('enable_network_throughput_recv_total', False):
            for k in ['network_throughput_recv_total_x', 'network_throughput_recv_total_y']:
                if self.config.get(k) is None:
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True

        # Specific tests
        if not os.path.exists(self.config.get('background')):
            self.logger.error("no such background file '%s'", self.config.get('background'))
            r = True

        return(r)

    def setup(self):
        # Block execution if configuration is invalid
        if self.validate_config():
            return(True)

        # Use default background from configuration
        self.set_background()

        # Define where we store our screen jfif
        self.set_image_path(os.path.join(self.tmpdir.name, 'screen.jpg'))

        if self.config.get('enable_date', False):
            self.date = widgets.Date(self.config, self.tmpdir, self.logger)
            self.date.setup(self.get_background())
        if self.config.get('enable_time', False):
            self.time = widgets.Time(self.config, self.tmpdir, self.logger)
            self.time.setup(self.get_background())
        if self.config.get('enable_cpu_utilization', False):
            self.cpu_utilization = widgets.CpuUtilization(self.config, self.tmpdir, self.logger)
            self.cpu_utilization.setup(self.get_background())
        if self.config.get('enable_cpu_utilization_bar', False):
            self.cpu_utilization_bar = widgets.CpuUtilizationBar(self.config, self.tmpdir, self.logger)
            self.cpu_utilization_bar.setup(self.get_background())
        if self.config.get('enable_ram_available', False):
            self.ram_available = widgets.RamAvailable(self.config, self.tmpdir, self.logger)
            self.ram_available.setup(self.get_background())
        if self.config.get('enable_ram_utilization', False):
            self.ram_utilization = widgets.RamUtilization(self.config, self.tmpdir, self.logger)
            self.ram_utilization.setup(self.get_background())
        if self.config.get('enable_ram_utilization_bar', False):
            self.ram_utilization_bar = widgets.RamUtilizationBar(self.config, self.tmpdir, self.logger)
            self.ram_utilization_bar.setup(self.get_background())
        if self.config.get('enable_loadavg', False):
            self.loadavg = widgets.LoadAverage(self.config, self.tmpdir, self.logger)
            self.loadavg.setup(self.get_background())
        if self.config.get('enable_network_throughput_send', False):
            self.network_throughput_send = widgets.NetworkThroughputSend(self.config, self.tmpdir, self.logger)
            self.network_throughput_send.setup(self.get_background())
        if self.config.get('enable_network_throughput_recv', False):
            self.network_throughput_recv = widgets.NetworkThroughputRecv(self.config, self.tmpdir, self.logger)
            self.network_throughput_recv.setup(self.get_background())
        if self.config.get('enable_network_throughput_send_total', False):
            self.network_throughput_send_total = widgets.NetworkThroughputSendTotal(self.config, self.tmpdir, self.logger)
            self.network_throughput_send_total.setup(self.get_background())
        if self.config.get('enable_network_throughput_recv_total', False):
            self.network_throughput_recv_total = widgets.NetworkThroughputRecvTotal(self.config, self.tmpdir, self.logger)
            self.network_throughput_recv_total.setup(self.get_background())
        if self.config.get('text', False):
            for text_config in self.config.get('text', []):
                if text_config.get('enabled', False):
                    text_widget = widgets.Text(text_config, self.tmpdir, self.logger)
                    text_widget.setup(self.get_background())
                    self.text_widgets.append(text_widget)

        # Success
        return(False)

    def display(self, orientation = 0, quality = 80, optimize = False):
        # Clear previous frame
        if self.config.get('enable_date', False):
            self.date.clear()
        if self.config.get('enable_time', False):
            self.time.clear()
        if self.config.get('enable_cpu_utilization', False):
            self.cpu_utilization.clear()
        if self.config.get('enable_cpu_utilization_bar', False):
            self.cpu_utilization_bar.clear()
        if self.config.get('enable_ram_available', False):
            self.ram_available.clear()
        if self.config.get('enable_ram_utilization', False):
            self.ram_utilization.clear()
        if self.config.get('enable"ram_utilization_bar', False):
            self.ram_utilization_bar.clear()
        if self.config.get('enable_loadavg', False):
            self.loadavg.clear()
        if self.config.get('enable_network_throughput_send', False):
            self.network_throughput_send.clear()
        if self.config.get('enable_network_throughput_recv', False):
            self.network_throughput_recv.clear()
        if self.config.get('enable_network_throughput_send_total', False):
            self.network_throughput_send_total.clear()
        if self.config.get('enable_network_throughput_recv_total', False):
            self.network_throughput_recv_total.clear()
        if self.config.get('text', False):
            for text_widget in self.text_widgets:
                text_widget.clear()
        
        # We retrieve a new temporary image path on first draw
        # It should be utilized in place of get_background in all
        # further Widgets rendered.
        if self.config.get('enable_date', False):
            self.date.draw()
        if self.config.get('enable_time', False):
            self.time.draw()
        if self.config.get('enable_cpu_utilization', False):
            self.cpu_utilization.draw()
        if self.config.get('enable_cpu_utilization_bar', False):
            self.cpu_utilization_bar.draw()
        if self.config.get('enable_ram_available', False):
            self.ram_available.draw()
        if self.config.get('enable_ram_utilization', False):
            self.ram_utilization.draw()
        if self.config.get('enable_ram_utilization_bar', False):
            self.ram_utilization_bar.draw()
        if self.config.get('enable_loadavg', False):
            self.loadavg.draw()
        if self.config.get('enable_network_throughput_send', False):
            self.network_throughput_send.draw()
        if self.config.get('enable_network_throughput_receive', False):
            self.network_throughput_receive.draw()
        if self.config.get('enable_network_throughput_send_total', False):
            self.network_throughput_send_total.draw()
        if self.config.get('enable_network_throughput_receive_total', False):
            self.network_throughput_receive_total.draw()
        if self.config.get('text', False):
            for text_widget in self.text_widgets:
                text_widget.draw()

        # Image post processing
        util.ImagePostProcess(self.image_path)
        util.process()

        return(self.image_path)
    
    def cleanup(self):
        # We only need to cleanup one of the widgets
        # to ensure the tmpdir has been removed.
        if self.config.get('enable_date', False):
            self.date.cleanup()
        elif self.config.get('enable_time', False):
            self.time.cleanup()
        elif self.config.get('enable_cpu_utilization', False):
            self.cpu_utilization.cleanup()
        elif self.config.get('enable_cpu_utilization_bar', False):
            self.cpu_utilization_bar.cleanup()
        elif self.config.get('enable_ram_available', False):
            self.ram_available.cleanup()
        elif self.config.get('enable_ram_utilization', False):
            self.ram_utilization.cleanup()
        elif self.config.get('enable_ram_utilization_bar', False):
            self.ram_utilization_bar.cleanup()
        elif self.config.get('enable_loadavg', False):
            self.loadavg.cleanup()
        elif self.config.get('enable_network_throughput_send', False):
            self.network_throughput_send.cleanup()
        elif self.config.get('enable_network_throughput_receive', False):
            self.network_throughput_receive.cleanup()
        elif self.config.get('enable_network_throughput_send_total', False):
            self.network_throughput_send_total.cleanup()
        elif self.config.get('enable_network_throughput_receive_total', False):
            self.network_throughput_receive_total.cleanup()
        elif self.config.get('text', False):
            for text_widget in self.text_widgets:
                text_widget.cleanup()
                break
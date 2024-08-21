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
        Returns False on success, True on failure.
        """
        r = False
        
        # Validate required global variables exist
        bg = self.config.get('background')
        if bg is not None:
            if not os.path.exists(bg):
                self.logger.error("no such background file '%s'", bg)
                r = True
        else:
            self.logger.error("you must specify a background file")
            r = True

        for k in ['idVendor', 'idProduct', 'background', 'orientation', 'font_file', 'font_size', 'font_color', 'line_length', 'line_space']:
            if self.config.get(k) is None:
                self.logger.error("Missing configuration argument '%s'", k)
                r = True
        
        return(r)

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

    def setup(self):
        # Block execution if configuration is invalid
        if self.validate_config():
            return(True)

        # Use default background from configuration
        self.set_background()

        # Define where we store our screen jfif
        self.set_image_path(os.path.join(self.tmpdir.name, 'screen.jpg'))

    def display(self, orientation = 0, quality = 80, optimize = False):
        # Image post processing keeps us safe
        pp = util.ImagePostProcess(self.image_path)
        pp.process()

        return(self.image_path)

    def cleanup(self):
        """
        Override me (required)!
        """
        pass

    def shutdown(self):
        """
        Override me (required)!
        """
        pass

class Kubernetes(Overlay):
    def __init__(self, config, logger):
        self.text_widgets = []
        Overlay.__init__(self, config, logger)

    def validate_config(self):
        """
        Basic configuration validation
        If missing config item, set r = True
        """
        if super().validate_config():
            self.logger.info("FAILED TO VALIDATE SUPER CONFIG")
            return(True)

        r = False

        # Validate Prometheus globals if any Prometheus option is enabled
        if self.config.get('enable_prometheus_network_throughput_recv', False) or self.config.get('enable_prometheus_network_throughput_send', False):
            if not self.config.get('prometheus_url', False):
                self.logger.error("Missing configuration argument 'prometheus_url'")
                r = True
            if not self.config.get('prometheus_url_disable_ssl', False):
                self.logger.error("Missing configuration argument 'prometheus_url_disable_ssl'")
                r = True

        # Validate each widget argument when a widget is enabled
        if self.config.get('enable_kubernetes_pod_count', False):
            for k in ['kubernetes_pod_count_x', 'kubernetes_pod_count_y']:
                if not self.config.get(k, False):
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        if self.config.get('enable_prometheus_network_throughput_recv', False):
            for k in ['prometheus_network_throughput_recv_x', 'prometheus_network_throughput_recv_y']:
                if not self.config.get(k, False):
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        if self.config.get('enable_prometheus_network_throughput_send', False):
            for k in ['prometheus_network_throughput_send_x', 'prometheus_network_throughput_send_y']:
                if not self.config.get(k, False):
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        
        return(r)

    def setup(self):
        super().setup()

        if self.validate_config():
            return(True)

        if self.config.get('enable_date', False):
            self.date = widgets.Date(self.config, self.tmpdir, self.logger)
            self.date.setup(self.get_background())
        if self.config.get('enable_time', False):
            self.time = widgets.Time(self.config, self.tmpdir, self.logger)
            self.time.setup(self.get_background())
        if self.config.get('enable_kubernetes_pod_count', False):
            self.pod_count = widgets.KubernetesPodCount(self.config, self.tmpdir, self.logger)
            self.pod_count.setup(self.get_background())
        if self.config.get('enable_prometheus_network_throughput_recv', False):
            self.prometheus_network_throughput_recv = widgets.PrometheusNetworkThroughputRecv(self.config, self.tmpdir, self.logger)
            self.prometheus_network_throughput_recv.setup(self.get_background())
        if self.config.get('enable_prometheus_network_throughput_send', False):
            self.prometheus_network_throughput_send = widgets.PrometheusNetworkThroughputSend(self.config, self.tmpdir, self.logger)
            self.prometheus_network_throughput_send.setup(self.get_background())
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
        if self.config.get('enable_kubernetes_pod_count', False):
            self.pod_count.clear()
        if self.config.get('enable_prometheus_network_throughput_recv', False):
            self.prometheus_network_throughput_recv.clear()
        if self.config.get('enable_prometheus_network_throughput_send', False):
            self.prometheus_network_throughput_send.clear()
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
        if self.config.get('enable_kubernetes_pod_count', False):
             self.pod_count.draw()
        if self.config.get('enable_prometheus_network_throughput_recv', False):
             self.prometheus_network_throughput_recv.draw()
        if self.config.get('enable_prometheus_network_throughput_send', False):
             self.prometheus_network_throughput_send.draw()
        if self.config.get('text', False):
            for text_widget in self.text_widgets:
                text_widget.draw()

        got = super().display(orientation = 0, quality = 80, optimize = False)
        return(self.image_path)

    def cleanup(self):
        # We only need to cleanup one of the widgets
        # to ensure the tmpdir has been removed.
        if self.config.get('enable_date', False):
            self.date.cleanup()
        elif self.config.get('enable_time', False):
            self.time.cleanup()
        elif self.config.get('enable_kubernetes_pod_count', False):
            self.pod_count.cleanup()
        elif self.config.get('enable_prometheus_network_throughput_recv', False):
            self.prometheus_network_throughput_recv.cleanup()
        elif self.config.get('enable_prometheus_network_throughput_send', False):
            self.prometheus_network_throughput_send.cleanup()
        elif self.config.get('text', False):
            for text_widget in self.text_widgets:
                text_widget.cleanup()
                break

    def shutdown(self):
        if self.config.get('enable_date', False):
            self.date.shutdown()
        if self.config.get('enable_time', False):
            self.time.shutdown()
        if self.config.get('enable_kubernetes_pod_count', False):
            self.pod_count.shutdown()
        if self.config.get('enable_prometheus_network_throughput_recv', False):
            self.prometheus_network_throughput_recv.shutdown()
        if self.config.get('enable_prometheus_network_throughput_send', False):
            self.prometheus_network_throughput_send.shutdown()
        if self.config.get('text', False):
            for text_widget in self.text_widgets:
                text_widget.shutdown()

class Node(Overlay):
    def __init__(self, config, logger):
        self.cpu_utilization = None
        self.text_widgets = []
        Overlay.__init__(self, config, logger)

    def validate_config(self):
        """
        Basic configuration validation
        If missing config item, set r = True
        """
        if Overlay.validate_config(self):
            return(True)

        r = False

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
            for k in ['loadavg_x', 'loadavg_y']:
                if self.config.get(k) is None:
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        if self.config.get('enable_iowait', False):
            for k in ['iowait_x', 'iowait_y']:
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
        if self.config.get('enable_cpufreq', False):
            for k in ['cpufreq_x', 'cpufreq_y']:
                if self.config.get(k) is None:
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True
        if self.config.get('enable_uptime', False):
            for k in ['uptime_x', 'uptime_y']:
                if self.config.get(k) is None:
                    self.logger.error("Missing configuration argument '%s'", k)
                    r = True

        return(r)

    def setup(self):
        super().setup()

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
        if self.config.get('enable_iowait', False):
            self.iowait = widgets.IOWait(self.config, self.tmpdir, self.logger)
            self.iowait.setup(self.get_background())
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
        if self.config.get('enable_cpufreq', False):
            self.cpufreq = widgets.CpuFreq(self.config, self.tmpdir, self.logger)
            self.cpufreq.setup(self.get_background())
        if self.config.get('enable_uptime', False):
            self.uptime = widgets.Uptime(self.config, self.tmpdir, self.logger)
            self.uptime.setup(self.get_background())

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
        if self.config.get('enable_iowait', False):
            self.iowait.clear()
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
        if self.config.get('enable_cpufreq', False):
            self.cpufreq.clear()
        if self.config.get('enable_uptime', False):
            self.uptime.clear()
 
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
        if self.config.get('enable_iowait', False):
            self.iowait.draw()
        if self.config.get('enable_network_throughput_send', False):
            self.network_throughput_send.draw()
        if self.config.get('enable_network_throughput_recv', False):
            self.network_throughput_recv.draw()
        if self.config.get('enable_network_throughput_send_total', False):
            self.network_throughput_send_total.draw()
        if self.config.get('enable_network_throughput_recv_total', False):
            self.network_throughput_recv_total.draw()
        if self.config.get('text', False):
            for text_widget in self.text_widgets:
                text_widget.draw()
        if self.config.get('enable_cpufreq', False):
            self.cpufreq.draw()
        if self.config.get('enable_uptime', False):
            self.uptime.draw()

        return(Overlay.display(self, orientation = 0, quality = 80, optimize = False))
    
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
        elif self.config.get('enable_iowait', False):
            self.iowait.cleanup()
        elif self.config.get('enable_network_throughput_send', False):
            self.network_throughput_send.cleanup()
        elif self.config.get('enable_network_throughput_recv', False):
            self.network_throughput_recv.cleanup()
        elif self.config.get('enable_network_throughput_send_total', False):
            self.network_throughput_send_total.cleanup()
        elif self.config.get('enable_network_throughput_recv_total', False):
            self.network_throughput_recv_total.cleanup()
        elif self.config.get('text', False):
            for text_widget in self.text_widgets:
                text_widget.cleanup()
                break
        elif self.config.get('enable_cpufreq', False):
            self.cpufreq.cleanup()
        elif self.config.get('enable_uptime', False):
            self.uptime.cleanup()

    def shutdown(self):
        if self.config.get('enable_date', False):
            self.date.shutdown()
        if self.config.get('enable_time', False):
            self.time.shutdown()
        if self.config.get('enable_cpu_utilization', False):
            self.cpu_utilization.shutdown()
        if self.config.get('enable_cpu_utilization_bar', False):
            self.cpu_utilization_bar.shutdown()
        if self.config.get('enable_ram_available', False):
            self.ram_available.shutdown()
        if self.config.get('enable_ram_utilization', False):
            self.ram_utilization.shutdown()
        if self.config.get('enable_ram_utilization_bar', False):
            self.ram_utilization_bar.shutdown()
        if self.config.get('enable_loadavg', False):
            self.loadavg.shutdown()
        if self.config.get('enable_iowait', False):
            self.iowait.shutdown()
        if self.config.get('enable_network_throughput_send', False):
            self.network_throughput_send.shutdown()
        if self.config.get('enable_network_throughput_recv', False):
            self.network_throughput_recv.shutdown()
        if self.config.get('enable_network_throughput_send_total', False):
            self.network_throughput_send_total.shutdown()
        if self.config.get('enable_network_throughput_recv_total', False):
            self.network_throughput_recv_total.shutdown()
        if self.config.get('text', False):
            for text_widget in self.text_widgets:
                text_widget.shutdown()
        if self.config.get('enable_cpufreq', False):
            self.cpufreq.shutdown()
        if self.config.get('enable_uptime', False):
            self.uptime.shutdown()

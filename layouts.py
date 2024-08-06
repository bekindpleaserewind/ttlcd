import os
import ast
import logging
import tempfile

import widgets

class Overlay:
    def __init__(self, config):
        self.config = config
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

class Node(Overlay):
    def __init__(self, config):
        self.cpu_utilization = None
        Overlay.__init__(self, config)

    def validate_config(self):
        """
        Basic configuration validation
        """
        r = 0

        # Validate required global variables exist
        for k in ['idVendor', 'idProduct', 'background', 'orientation', 'font_file', 'font_size', 'font_color', 'line_length', 'line_space']:
            if self.config.get(k) is None:
                logging.error("Missing configuration argument '%s'", k)
                r = 1

        # Validate each widget argument when a widget is enabled
        if self.config.get('enable_cpu_utilization') is not None:
            for k in ['cpu_utilization_x', 'cpu_utilization_y']:
                if self.config.get(k) is None:
                    logging.error("Missing configuration argument '%s'", k)
                    r = 1
        if self.config.get('enable_ram_utilization') is not None:
            for k in ['ram_utilization_x', 'ram_utilization_y']:
                if self.config.get(k) is None:
                    logging.error("Missing configuration argument '%s'", k)
                    r = 1
        if self.config.get('enable_loadavg') is not None:
            for k in ['loadavg_x', 'loadavg_y', 'loadavg_line_space']:
                if self.config.get(k) is None:
                    logging.error("Missing configuration argument '%s'", k)
                    r = 1

        return(r)

    def setup(self):
        # Block execution if configuration is invalid
        if self.validate_config():
            return(1)

        # Use default background from configuration
        self.set_background()

        # Define where we store our screen jfif
        self.set_image_path(os.path.join(self.tmpdir.name, 'screen.jpg'))

        if self.config.get('enable_cpu_utilization', False):
            self.cpu_utilization = widgets.CpuUtilization(self.config, self.tmpdir)
            self.cpu_utilization.setup(self.get_background())
        if self.config.get('enable_ram_utilization', False):
            self.ram_utilization = widgets.RamUtilization(self.config, self.tmpdir)
            self.ram_utilization.setup(self.get_background())
        if self.config.get('enable_loadavg', False):
            self.loadavg = widgets.LoadAverage(self.config, self.tmpdir)
            self.loadavg.setup(self.get_background())

        # Success
        return(0)

    def display(self):
        # Clear previous frame
        if self.config.get('enable_cpu_utilization', False):
            self.cpu_utilization.clear()
        if self.config.get('enable_ram_utilization', False):
            self.ram_utilization.clear()
        if self.config.get('enable_loadavg', False):
            self.loadavg.clear()
        
        # We retrieve a new temporary image path on first draw
        # It should be utilized in place of get_background in all
        # further Widgets rendered.
        if self.config.get('enable_cpu_utilization', False):
            self.cpu_utilization.draw()
        if self.config.get('enable_ram_utilization', False):
            self.ram_utilization.draw()
        if self.config.get('enable_loadavg', False):
            self.loadavg.draw()

        return(self.get_image_path())
    
    def cleanup(self):
        self.cpu_utilization.cleanup()


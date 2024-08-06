import os
import ast
import tempfile

import widgets

class Overlay:
    def __init__(self):
        self.tmpdir = tempfile.TemporaryDirectory()

    def set_background(self, image_file):
        if not os.path.exists(image_file):
            return(1)

        self.image_path = image_file
        return(0)
    
    def set_font(self, font_file):
        if not os.path.exists(font_file):
            return(1)

        self.font_file = font_file
        return(0)

    def set_font_size(self, font_size):
        self.font_size = font_size

    def set_font_color(self, font_color):
        self.font_color = font_color
        if type(self.font_color) == str:
            self.font_color = ast.literal_eval(self.font_color)

    def get_background(self):
        return(self.image_path)

    def get_font(self):
        return(self.font_file)

    def get_font_size(self):
        return(self.font_size)

    def get_font_color(self):
        return(self.font_color)

class Node(Overlay):
    def __init__(self):
        Overlay.__init__(self)
    
    def set_location_cpu_utilization(self, x, y):
        self.cpu_utilization_location = (x, y)
    
    def set_location_ram_utilization(self, x, y):
        self.ram_utilization_location = (x, y)

    def set_location_loadavg(self, x, y, line_length = 8):
        self.loadavg_location = (x, y)
        self.loadavg_line_length = line_length

    def setup(self, background, font, size, color_rgb):
        self.cpu_utilization = widgets.CpuUtilization(self.tmpdir)
        self.ram_utilization = widgets.RamUtilization(self.tmpdir)
        self.loadavg = widgets.LoadAverage(self.tmpdir)
        self.set_background(background)
        self.set_font(font)
        self.set_font_size(size)
        self.set_font_color(color_rgb)

    def display(self):
        # We retrieve a new temporary image path on first draw
        # It should be utilized in place of get_background in all
        # further Widgets rendered.
        image_path = self.cpu_utilization.draw(
            self.get_background(),
            self.cpu_utilization_location,
            self.get_font(),
            self.get_font_size(),
            self.get_font_color(),
        )

        self.ram_utilization.draw(
            image_path,
            self.ram_utilization_location,
            self.get_font(),
            self.get_font_size(),
            self.get_font_color(),
        )

        self.loadavg.draw(
            image_path,
            self.loadavg_location,
            self.get_font(),
            self.get_font_size(),
            self.get_font_color(),
            line_spacing = self.loadavg_line_length,
        )

        return(image_path)
    
    def cleanup(self):
        self.cpu_utilization.cleanup()


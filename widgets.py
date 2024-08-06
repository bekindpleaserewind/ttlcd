import os
import ast
import psutil

from PIL import Image, ImageDraw, ImageFont

IMAGE_PATH = None

class Widget:
    def __init__(self, config, tmpdir):
        self.config = config
        self.value = None
        self.node = None
        self.tmpdir = tmpdir
        self.background_file = None
        self.x = 0
        self.y = 0
        self.font_file = None
        self.font_size = 14
        self.font_color = (255, 255, 255)
        self.line_length = 0
        self.line_space = 0

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
            self.font_file = self.config.get('font_file')
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
                self.font_color = ast.literal_eval(self.font_color)
        else:
            self.font_color = self.config.get('font_color')
            if type(self.font_color) == str:
                self.font_color = ast.literal_eval(self.font_color)

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

        if self.get_image_path() is None:
            image = Image.open(self.get_background())
            self.set_image_path(os.path.join(self.tmpdir.name, 'screen.jpg'))
        else:
            image = Image.open(self.get_image_path())

        draw = ImageDraw.Draw(image)
        f = ImageFont.truetype(self.get_font(), self.get_font_size())

        # Where to place us on the screen
        loc = self.get_location()

        if type(self.value) == list or type(self.value) == tuple:
            for value in self.value:
                if self.line_length <= 0:
                    draw.text(loc, str(value), self.get_font_color(), font = f)
                else:
                    if len(str(value)) > self.line_length:
                        draw.text(loc, str(value)[0:self.line_length - 3] + "...", self.get_font_color(), font = f)
                    else:
                        draw.text(loc, str(value), self.get_font_color(), font = f)
                loc = (loc[0], int(loc[1]) + int(self.get_font_size()) + int(self.line_space))
        else:
            if self.line_length <= 0:
                draw.text(loc, str(self.value), self.get_font_color(), font = f)
            else:
                if len(str(self.value)) > self.line_length:
                    draw.text(loc, str(self.value)[0:self.line_length - 3] + "...", self.get_font_color(), font = f)
                else:
                    draw.text(loc, str(self.value)[0:self.line_length], self.get_font_color(), font = f)

        image.save(self.get_image_path(), "JPEG", progressive = False, quality = 80, optimize = True)
    
    def get_tmpdir(self):
        return(self.tmpdir)

    def cleanup(self):
        if self.tmpdir is not None:
            self.tmpdir.cleanup()
    
    def setup(self):
        pass

class CpuUtilization(Widget):
    def __init__(self, config, tmpdir):
        Widget.__init__(self, config, tmpdir)

    def setup(self, background):
        self.set_background(background)
        self.set_x(self.config.get('cpu_utilization_x'))
        self.set_y(self.config.get('cpu_utilization_y'))
        self.set_font(self.config.get('cpu_font_file'))
        self.set_font_size(self.config.get('cpu_font_size'))
        self.set_font_color(self.config.get('cpu_font_color'))

    def tick(self):
        self.value = psutil.cpu_percent()

class RamUtilization(Widget):
    def __init__(self, config, tmpdir):
        Widget.__init__(self, config, tmpdir)

    def setup(self, background):
        self.set_background(background)
        self.set_x(self.config.get('ram_utilization_x'))
        self.set_y(self.config.get('ram_utilization_y'))
        self.set_font(self.config.get('ram_font_file'))
        self.set_font_size(self.config.get('ram_font_size'))
        self.set_font_color(self.config.get('ram_font_color'))

    def tick(self):
        self.value = psutil.virtual_memory().percent

class LoadAverage(Widget):
    def __init__(self, config, tmpdir):
        Widget.__init__(self, config, tmpdir)

    def setup(self, background):
        self.set_background(background)
        self.set_x(self.config.get('loadavg_x'))
        self.set_y(self.config.get('loadavg_y'))
        self.set_font(self.config.get('loadavg_font_file'))
        self.set_font_size(self.config.get('loadavg_font_size'))
        self.set_font_color(self.config.get('loadavg_font_color'))
        self.set_line_length(self.config.get('loadavg_line_length'))
        self.set_line_space(self.config.get('loadavg_line_space'))

    def tick(self):
        self.value = psutil.getloadavg()
        self.value = (" 1 minute: %.2f" % self.value[0], " 5 minute: %.2f" % self.value[1], "15 minute: %.2f" % self.value[2])
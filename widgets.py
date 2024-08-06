import os
import psutil
import PIL

class Widget:
    def __init__(self, tmpdir):
        self.value = None
        self.tmpdir = tmpdir

    def tick(self):
        """ Define this function"""
        pass

    def get(self):
        return(self.value)

    def draw(self, background, loc, font_file, font_size, font_color, length = -1, line_spacing = 8):
        self.tick()

        image = PIL.Image.open(background)
        draw = PIL.ImageDraw.Draw(image)
        f = PIL.ImageFont.truetype(font_file, font_size)

        if type(self.value) == list or type(self.value) == tuple:
            for value in self.value:
                if length < 0:
                    draw.text(loc, str(value), font_color, font = f)
                else:
                    if len(str(value)) > length:
                        draw.text(loc, str(value)[0:length - 3] + "...", font_color, font = f)
                    else:
                        draw.text(loc, str(value), font_color, font = f)
                loc = (loc[0], int(loc[1]) + int(font_size) + int(line_spacing))     # 8 = padding
        else:
            if length < 0:
                draw.text(loc, str(self.value), font_color, font = f)
            else:
                if len(str(self.value)) > length:
                    draw.text(loc, str(self.value)[0:length - 3] + "...", font_color, font = f)
                else:
                    draw.text(loc, str(self.value)[0:length], font_color, font = f)

        bg = os.path.join(self.tmpdir.name, 'background.jpg')
        image.save(bg, "JPEG", progressive = False, quality = 80, optimize = True)
        
        return(bg)
    
    def get_tmpdir(self):
        return(self.tmpdir)

    def cleanup(self):
        if self.tmpdir is not None:
            self.tmpdir.cleanup()

class CpuUtilization(Widget):
    def __init__(self, tmpdir = None):
        Widget.__init__(self, tmpdir)

    def tick(self):
        self.value = psutil.cpu_percent()

class RamUtilization(Widget):
    def __init__(self, tmpdir = None):
        Widget.__init__(self, tmpdir)

    def tick(self):
        self.value = psutil.virtual_memory().percent

class LoadAverage(Widget):
    def __init__(self, tmpdir = None):
        Widget.__init__(self, tmpdir)

    def tick(self):
        self.value = psutil.getloadavg()
        self.value = (" 1 minute: %.2f" % self.value[0], " 5 minute: %.2f" % self.value[1], "15 minute: %.2f" % self.value[2])
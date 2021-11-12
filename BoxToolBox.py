#!/usr/bin/python

import os
#os.add_dll_directory("C:\\Qt\\6.2.0\\mingw81_64\\bin")
#os.add_dll_directory("D:\\shared\\BoxToolBox\\win\\target\\bin")
path = os.path.dirname(os.path.realpath(__file__))
os.environ["QT_PLUGIN_PATH"] = os.path.join(path, "qt_plugins")

import numpy as np, cv2 as cv; cv2=cv
import sys
import common
import normalize
import keyboard


main_win = 'main'

win_w = 1024
win_h = 768

class BoxToolBox:
    
    def overlay_image(self, img, img_overlay, x, y):
        # Image ranges
        y1, y2 = max(0, y), min(img.shape[0], y + img_overlay.shape[0])
        x1, x2 = max(0, x), min(img.shape[1], x + img_overlay.shape[1])

        # Overlay ranges
        y1o, y2o = max(0, -y), min(img_overlay.shape[0], img.shape[0] - y)
        x1o, x2o = max(0, -x), min(img_overlay.shape[1], img.shape[1] - x)

        # Exit if nothing to do
        if y1 >= y2 or x1 >= x2 or y1o >= y2o or x1o >= x2o:
            return

        # Blend overlay within the determined ranges
        img_crop = img[y1:y2, x1:x2]
        img_overlay_crop = img_overlay[y1o:y2o, x1o:x2o]
        
        #add aplha if missing
        if (img_overlay_crop.shape[2] == 3):
            img_overlay_crop = cv.cvtColor(img_overlay_crop, cv.COLOR_RGB2RGBA)
            
        img_crop[:] = img_overlay_crop

    
    def put_text(self, x, y, text) :  
        font = cv.FONT_HERSHEY_DUPLEX
        fsize = 1
        b_color = (0, 0, 0, 255)
        w_color = (255, 255, 255, 128)

        size, ret = cv.getTextSize(text, font, fsize, 1)

        cv.putText(self.main_image, text, (x, y + size[1]), font, fsize, w_color, 2)    
        cv.putText(self.main_image, text, (x, y + size[1]), font, fsize, b_color, 1)    
    
    def put_image(self, image_name, slot, x, y, w, h, 
                  final_proces, show_info, picked = False, show_crop = False):
        fname = os.path.join(self.path, slot, image_name)
        tmp = cv.imread(fname, cv.IMREAD_UNCHANGED)

        img_w = int(w * (self.scale + self.margin_w * self.scale))
        img_h = int(h * (self.scale + self.margin_h * self.scale))
        tmp = cv.resize(tmp, (img_w, img_h))

        if (final_proces == False or self.cfg[image_name]["crop"]) and not show_crop:
            if (img_w > self.dst_w):
                cx = int((img_w - self.dst_w) / 2)
                if (cx != 0):
                    tmp = tmp[:, cx: -cx]
                img_w = self.dst_w

            if (img_h > self.dst_h):
                cy = int((img_h - self.dst_h) / 2)
                if (cy != 0):
                    tmp = tmp[cy: -cy, :]
                img_h = self.dst_h

        x_offset = int((self.space + w / 2) + (self.space + w) * x - (img_w / 2))
        y_offset = int((self.space + h / 2) + (self.space + h) * y - (img_h / 2))

        self.overlay_image(self.main_image, tmp, x_offset, y_offset)

        if show_crop:
            x_offset = int((self.space + w / 2) + (self.space + w) * x - (self.dst_w / 2))
            y_offset = int((self.space + h / 2) + (self.space + h) * y - (self.dst_h / 2))        

        if picked:
            color = (0, 0, 255, 255)
            thick = 3
            cv.rectangle(self.main_image, (x_offset + self.space + thick, y_offset + self.space + thick), 
                 (x_offset + img_w - self.space - thick, y_offset + img_h - self.space - thick), color, thick)

        if show_info:
            h = 30
            nx = max(0, x_offset) + self.space * 1
            ny = max(0, y_offset) + self.space * 1
            self.put_text(nx, ny + h * 0, image_name)
            self.put_text(nx, ny + h * 1, "%u/%u" % (self.file_list.index(image_name) + 1, len(self.file_list)))
            self.put_text(nx, ny + h * 2, "crop" if self.cfg[image_name]["crop"] else "full")
 

    def __init__(self, path):
        self.path = path
        self.pick_index = None
        self.transparent_spacer = False
        self.show_info = False
        self.show_top = None
        self.mouse_x = None
        self.prev_fast = None
        
        self.file_list = common.read_dir(self.path)
        if len(self.file_list) == 0:
            common.show_message("Error", "No usable images found in directory '%s'" % self.path)
            return
        
        self.cfg = common.load_config(self.path)
        
        if self.cfg == {}:
            norm = normalize.Normalizator(self.path)
            norm.run()
        else:
            norm = normalize.Normalizator(self.path, True)
            norm.generate_all()            

        self.cfg = common.load_config(self.path)

        self.props = {}
        self.mouse_x = 0
        self.mouse_y = 0
        self.slot = None
        
        self.main_win = 'Grid layout'
        cv.namedWindow(self.main_win, cv.WINDOW_NORMAL)
        
        cv.resizeWindow(self.main_win, win_w, win_h)
        cv.setMouseCallback(self.main_win, self.on_mouse_event)     

        cv.createTrackbar("Space", "", 0, 200, self.on_space_track)
        cv.createTrackbar("Scale", "", 50, 200, self.on_scale_track)
        cv.setTrackbarMin("Scale", "", 25)
        cv.createTrackbar("Grid W", "", 1, 8, self.on_grid_w_track)
        cv.setTrackbarMin("Grid W", "", 1)
        cv.createTrackbar("Grid H", "", 1, 8, self.on_grid_h_track)
        cv.setTrackbarMin("Grid H", "", 1)

        cv.createButton("Render", lambda *args: self.redraw(False))
        cv.createButton("Output", lambda *args: self.redraw(False, ["process", []]))
        cv.createButton('Transparent spacer', self.on_transparent_check)
        cv.createButton('Show/Hide info', self.on_info_check)    
        cv.createButton('Quit', lambda *args:cv.destroyWindow(self.main_win))    
        
        cv.createButton('Slot 0', self.on_slot_change, 0, cv.QT_RADIOBOX | cv.QT_NEW_BUTTONBAR, 1)   
        for val in range(1,10):
            cv.createButton('Slot %u' %  val, self.on_slot_change, val, cv.QT_RADIOBOX, 0)    

        try:
            keyboard.press_and_release('ctrl+p')       
        except:
            cv.displayOverlay(self.main_win, "Press Ctrl+P to open controls", 2000);
       
    def check_cfg(self, key, default):
        if key not in self.props:
            self.props[key] = default        
        
    def set_slot(self, index):

        key = "slot_%02u" % index
        self.props = {}
        self.slot = index
        self.show_top = None
        
        if key in self.cfg:
            self.props = self.cfg[key]
        
        self.check_cfg("images", {})
        self.check_cfg("space", 20)
        self.check_cfg("scale", 140)
        self.check_cfg("grid_w", 3)
        self.check_cfg("grid_h", 3)
        self.check_cfg("transparent_spacer", 0)
        self.check_cfg("show_info", 0)
        
        cv.setTrackbarPos("Space", "", self.props["space"])
        cv.setTrackbarPos("Scale", "", self.props["scale"])
        cv.setTrackbarPos("Grid W", "", self.props["grid_w"])
        cv.setTrackbarPos("Grid H", "", self.props["grid_h"])
        
        self.redraw(True)

    def on_slot_change(self, val, p):
        if val == 1:
            self.set_slot(p)
        
    def save_slot(self):
        key = "slot_%02u" % self.slot
        self.cfg[key] = self.props
        common.store_config(self.cfg, self.path)
    
        
    def on_mouse_event(self, event, x, y, flags, param):
        if event == cv.EVENT_MOUSEMOVE:
            self.mouse_x = x
            self.mouse_y = y

        if event == cv.EVENT_LBUTTONUP:
            event = ["place", self.get_index(x, y)]
            self.redraw(True, event)

        if event == cv.EVENT_LBUTTONDOWN:
            event = ["pick", self.get_index(x, y)]
            self.redraw(True, event)


    def on_space_track(self, val): 
        self.props["space"] = val
        self.redraw(True, ["store", None])

    def on_scale_track(self, val): 
        self.props["scale"] = val
        self.redraw(True, ["store", None])

    def on_grid_w_track(self, val): 
        self.props["grid_w"] = val
        self.redraw(True, ["store", None])

    def on_grid_h_track(self, val): 
        self.props["grid_h"] = val
        self.redraw(True, ["store", None])

    def on_transparent_check(self, val, p):
        self.props["transparent_spacer"] = not self.props["transparent_spacer"]
        self.redraw(True, ["store", None])

    def on_info_check(self, val, p):
        self.props["show_info"] = not self.props["show_info"]
        self.redraw(True, ["store", None])

    def get_index(self, x, y):
        return "%u_%u" % (int(x / self.dst_w), int(y / self.dst_h))
        
    def redraw(self, fast, event = None):
        if self.slot == None:
            return
        
        cfg_change = False
        
        if fast != self.prev_fast:
            self.mouse_x = None
            self.prev_fast = fast 
        
        if fast:
            slot = "fast" 
            self.margin = int(self.cfg["box"]["margin"] * (self.cfg["box"]["prev_scale"] / 100.0))
            self.dst_w = int(self.cfg["box"]["width"] * (self.cfg["box"]["prev_scale"] / 100.0))
            self.dst_h = int(self.cfg["box"]["height"] * (self.cfg["box"]["prev_scale"] / 100.0))
            
            pb = None
            
        else:
            slot = "full"
            self.margin = self.cfg["box"]["margin"]
            self.dst_w = self.cfg["box"]["width"]
            self.dst_h = self.cfg["box"]["height"]
            
            pb = common.create_progressbar()   

        self.margin_w = (self.margin * 2) / self.dst_w
        self.margin_h = (self.margin * 2) / self.dst_h

        self.grid_w = self.props["grid_w"]
        self.grid_h = self.props["grid_h"]

        self.size_w = self.dst_w * self.grid_w
        self.size_h = self.dst_h * self.grid_h
        
        self.space = int(self.dst_w * (self.props["space"] / 500.0))
        self.scale = self.props["scale"] / 100.0

        self.main_image = np.zeros((self.size_h, self.size_w, 4), np.uint8)    
        cv.imshow(self.main_win, self.main_image)

        w = (self.size_w - (self.space * (self.grid_w + 1))) / self.grid_w
        h = (self.size_h - (self.space * (self.grid_h + 1))) / self.grid_h    

        #fill img list
        i = 0
        for y in range(self.grid_h):
            for x in range(self.grid_w):
                key = "%u_%u" % (x, y)
                if not key in self.props["images"]:
                    self.props["images"][key] = self.file_list[i % len(self.file_list)]
                    cfg_change = True
                i += 1

        final_process = False
        show_info_arr = []

        if event != None:
            t, p = event
            if t == "store":
                cfg_change = True
            
            if t == "change":
                key, d = p
                
                new_index = (self.file_list.index(self.props["images"][key]) + d + len(self.file_list)) % len(self.file_list)
                self.props["images"][key] = self.file_list[new_index]
                cfg_change = True
                show_info_arr.append(key)

            if t == "process":
                final_process = True
                show_top = None

                p_path = os.path.join(self.path, "slot_%u" % self.slot)
                common.clear_dir(p_path)
                if (not os.path.exists(p_path)):
                    os.mkdir(p_path)

            if t == "crop":
                file_name = self.props["images"][p]
                self.cfg[file_name]["crop"] = not self.cfg[file_name]["crop"] 
                cfg_change = True
                show_info_arr.append(p)

            if t == "pick":
                self.pick_index = p
                show_info_arr.append(self.pick_index)

            if t == "place":
                if self.pick_index != None:
                    if self.pick_index != p:
                        tmp = self.props["images"][self.pick_index]
                        self.props["images"][self.pick_index] = self.props["images"][p]
                        self.props["images"][p] = tmp
                        show_info_arr.append(p)
                        show_info_arr.append(self.pick_index)
                        cfg_change = True

                        
                    self.pick_index = None


            if t == "show":
                index, ex, ey = p
                if self.show_top == None:
                    self.show_top = [index, ex, ey]
                else:
                    if self.show_top[0] != index:
                        self.show_top = [index, ex, ey]
                    else:
                        self.show_top = None


        i = 0
        for y in range(self.grid_h):
            for x in range(self.grid_w):
                key = "%u_%u" % (x, y)

                if pb != None:
                    text = "[%u / %u] %s" % (i + 1, (self.grid_w * self.grid_w), self.props["images"][key])
                    prog = 100 * (i + 1) / (self.grid_w * self.grid_w)
                    common.update_progressbar(pb, "Rendering layers", text, prog)                  

                if final_process:
                    self.main_image = np.zeros((self.size_h, self.size_w, 4), np.uint8)    
                    
                picked = self.pick_index == key

                if fast:
                    if key in show_info_arr:
                        si = True
                    else:
                        si = self.props["show_info"]
                else:
                    si = False

                self.put_image(self.props["images"][key], slot, 
                          x, y, w, h, final_process, si, picked)

                if final_process:
                    fname = "%u_%u_%s.png" % (x + 1, y + 1, self.props["images"][key].split(".")[0])
                    cv.imwrite(os.path.join(p_path, fname), self.main_image)   

                i += 1


        if self.space > 0:
            if final_process:
                if pb != None:
                    common.update_progressbar(pb, "Rendering mask", "grid.png", 100)  
                    
                self.main_image = np.zeros((self.size_h, self.size_w, 4), np.uint8)   

            a_color = (255, 255, 255, 255)  

            for y in range(self.grid_h + 1):
                x1 = 0
                x2 = self.size_w
                y1 = int(y * (self.space + h))
                y2 = y1 + self.space

                cv.rectangle(self.main_image, (x1, y1), (x2, y2), a_color, 1 if self.props["transparent_spacer"] else -1)

            for x in range(self.grid_w + 1):
                y1 = 0
                y2 = self.size_h
                x1 = int(x * (self.space + w))
                x2 = x1 + self.space

                cv.rectangle(self.main_image, (x1, y1), (x2, y2), a_color, 1 if self.props["transparent_spacer"] else -1)    

            if final_process:
                fname = "grid.png"
                cv.imwrite(os.path.join(p_path, fname), self.main_image)   

        if self.show_top != None:
            key, x, y = self.show_top

            picked = self.pick_index == key       

            self.put_image(self.props["images"][key], slot, x, y, w, h, 
                      True, fast, picked, True)

            color = (0, 0, 255, 255)

            for y in range(self.grid_h + 1):
                x1 = 0
                x2 = self.size_w
                y1 = int(y * (self.space + h))
                y2 = y1 + self.space

                cv.rectangle(self.main_image, (x1, y1), (x2, y2), color, 1)

            for x in range(self.grid_w + 1):
                y1 = 0
                y2 = self.size_h
                x1 = int(x * (self.space + w))
                x2 = x1 + self.space

                cv.rectangle(self.main_image, (x1, y1), (x2, y2), color, 1)    

        if final_process:
            self.redraw(True)
        else:
            cv.imshow(self.main_win, self.main_image)
            
        if cfg_change:
            self.save_slot()
            
        if pb != None:
            common.close_progressbar(pb)


    def run(self):
        if len(self.file_list) == 0:
            return

        self.set_slot(0)

        while True:
            try:
                if cv.getWindowProperty(self.main_win, cv.WND_PROP_VISIBLE) == 0:
                    break
            except:
                break

            code = cv.waitKey(1)

            if self.mouse_x == None:
                continue

            if code == ord('s'):
                event = ["show", [self.get_index(self.mouse_x, self.mouse_y), 
                                  int(self.mouse_x / self.dst_w), 
                                  int(self.mouse_y / self.dst_h)]]
                self.redraw(True, event)                 

            if code == ord('c'):
                event = ["crop", self.get_index(self.mouse_x, self.mouse_y)]
                self.redraw(True, event)            

            if code == ord('n'):
                event = ["change", [self.get_index(self.mouse_x, self.mouse_y), -1]]
                self.redraw(True, event)     

            if code == ord('m'):
                event = ["change", [self.get_index(self.mouse_x, self.mouse_y), +1]]
                self.redraw(True, event)     
                
            if code == ord('e'):
                key = self.get_index(self.mouse_x, self.mouse_y)
                norm = normalize.Normalizator(self.path)
                norm.run(self.file_list.index(self.props["images"][key]))
                self.cfg = common.load_config(self.path)
                self.redraw(True)
        
        print("Quit")
       
if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = common.get_dir()    
    
    if len(path) > 0:
        box = BoxToolBox(path)
        box.run()

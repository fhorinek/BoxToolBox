#!/usr/bin/python

import numpy as np, cv2 as cv; cv2=cv
import os
import sys
import common

win_w = common.calibrate_win_w
win_h = common.calibrate_win_h


class Normalizator:

    def check_cfg(self, key, default):
        if key not in self.props:
            self.props[key] = default 

    def update_size(self):
        self.dst_w = self.props["width"]
        self.dst_h = self.props["height"]
        self.dst_margin = self.props["margin"]
        self.dst_size = (self.dst_w + self.dst_margin * 2, self.dst_h + self.dst_margin * 2)
        
        self.dst_pts = np.float32([[self.dst_margin, self.dst_margin], 
                                   [self.dst_w + self.dst_margin, self.dst_margin], 
                                   [self.dst_margin, self.dst_h + self.dst_margin], 
                                   [self.dst_w + self.dst_margin, self.dst_h + self.dst_margin]])        

    def __init__(self, path, silent = False):
        print("Base path is %s" % path)
        
        self.path = path
        self.changed = []

        self.file_list = common.read_dir(path)
        self.cfg = common.load_config(path)
        
        self.props = {}
        if "box" in self.cfg:
            self.props = dict(self.cfg["box"])
        
        self.check_cfg("width", 3000)
        self.check_cfg("height", 3000)
        self.check_cfg("margin", 500)
        self.check_cfg("prev_scale", 10)
 
        self.save_cfg_box()
        
        self.src_img = None
        if not silent:
            self.create_windows()

        self.update_size()
        
        self.src_image = None
        self.src_pts = None
      
    def on_width_track(self, val):
        self.props["width"] = val
        self.update_size()
        if not self.src_img is None:
            self.draw_transformed(self.src_img.copy())
      
    def on_height_track(self, val):
        self.props["height"] = val
        self.update_size()
        if not self.src_img is None:
            self.draw_transformed(self.src_img.copy())      
        
    def on_margin_track(self, val):
        self.props["margin"] = val
        self.update_size()
        if not self.src_img is None:
            self.draw_transformed(self.src_img.copy())        

    def on_prev_track(self, val):
        self.props["prev_scale"] = val
      
      
    def create_windows(self):
        self.src_win = 'Define box corners';
        cv.namedWindow(self.src_win, cv.WINDOW_NORMAL)
        self.dst_win = 'Transformation preview';
        cv.namedWindow(self.dst_win, cv.WINDOW_NORMAL)
        
        cv.setMouseCallback(self.src_win, self.on_mouse_event)

        cv.resizeWindow(self.src_win, win_w, win_h)
        cv.resizeWindow(self.dst_win, win_w, win_h)
        
        cv.createTrackbar("Width (px)", self.dst_win, self.props["width"], 5000, self.on_width_track)
        cv.setTrackbarMin("Width (px)", self.dst_win, 500)
        cv.createTrackbar("Height (px)", self.dst_win, self.props["height"], 5000, self.on_height_track)
        cv.setTrackbarMin("Height (px)", self.dst_win, 500)        
        cv.createTrackbar("Margin (px)", self.dst_win, self.props["margin"], 2500, self.on_margin_track)
        cv.setTrackbarMin("Margin (px)", self.dst_win, 100)        
        cv.createTrackbar("Preview scale (%)", self.dst_win, self.props["prev_scale"], 100, self.on_prev_track)
        cv.setTrackbarMin("Preview scale (%)", self.dst_win, 1)


      
    def note_change(self):
        if not self.image_name in self.changed:
            self.changed.append(self.image_name)        
    
    def get_prev_pts(self, index):
        i = index - 1
        while i >= 0:
            image_name = self.file_list[i]
            if image_name in self.cfg:
                if "points" in self.cfg[image_name]:
                    self.src_pts = np.float32(self.cfg[image_name]["points"])   
                    if self.parent != image_name:
                        self.note_change()
                        
                    self.parent = image_name
                    self.save_cfg()
                    return True
            i -= 1
        
        return False
        
    def load_now(self):
        self.loaded = True
        img_path = os.path.join(self.path, self.image_name)
        self.src_img = cv.imread(img_path, cv.IMREAD_UNCHANGED)
        print(self.src_img.shape)
        self.src_h = self.src_img.shape[0]
        self.src_w = self.src_img.shape[1]
            
        
    def load_image(self, index, silent = False):
        self.loaded = False
        self.image_index = index
        self.image_name = self.file_list[index]
        
        print("Loading %s" % self.file_list[index])
       
        self.parent = None
        self.src_pts = None
        self.crop = None
    
        if self.image_name in self.cfg:
            if "parent" in self.cfg[self.image_name]:
                self.parent = self.cfg[self.image_name]["parent"]
            
            if "points" in self.cfg[self.image_name]:
                self.src_pts = np.float32(self.cfg[self.image_name]["points"])
                
            if "crop" in self.cfg[self.image_name]:
                self.crop = self.cfg[self.image_name]["crop"]

        #load defaults
        if self.crop == None:
            self.crop = True
            
        if not isinstance(self.src_pts, np.ndarray):
            #try to find prew image with points
            if not self.get_prev_pts(index):
                if not self.loaded:
                    self.load_now()
                
                #set defaults
                self.src_pts = np.float32([[0, 0], 
                                           [self.src_w, 0], 
                                           [0, self.src_h - 1], 
                                           [self.src_w - 1, self.src_h - 1]])
                self.save_cfg()

        if not silent:
            self.load_now()
            
            img_copy = self.src_img.copy()
            self.draw_src_rect(img_copy)
            cv.imshow(self.src_win, img_copy) 
            self.draw_transformed(self.src_img.copy())

    def draw_helpers(self, image, x, y):
        color_r = (0, 0, 255)
    
        hor = np.int32([[0, y], [self.src_w, y]])
        ver = np.int32([[x, 0], [x, self.src_h]])
        cv.polylines(image, [hor], False, color_r, 4)
        cv.polylines(image, [ver], False, color_r, 4)
        
    def draw_src_rect(self, image):
        color_b = (255, 0, 140)
        
        cv.polylines(image, [np.int32(self.src_pts)], True, color_b, 8)
        rect = [np.int32([self.src_pts[0], 
                          self.src_pts[2], 
                          self.src_pts[3], 
                          self.src_pts[1]])]
        cv.polylines(image, rect, True, color_b, 8)

        for pt in self.src_pts:
            px, py = np.int32(pt)
            bs = 30
            cv.rectangle(image, (px-bs, py-bs), (px+bs,py+bs), color_b, 8)
     
    def put_text(self, x, y, text, image) :  
        font = cv.FONT_HERSHEY_SIMPLEX
        fsize = 10
        b_color = (0, 0, 0, 255)
        w_color = (255, 255, 255)

        size, ret = cv.getTextSize(text, font, fsize, 1)

        cv.putText(image, text, (x, y + size[1]), font, fsize, b_color, 15)    
        cv.putText(image, text, (x, y + size[1]), font, fsize, w_color, 10)        
    
    
    def draw_transformed(self, image):
        color_b = (255, 0, 140)
        
        matrix = cv.getPerspectiveTransform(self.src_pts, self.dst_pts)
        new = cv.warpPerspective(image, matrix, self.dst_size)
        cv.polylines(new, [np.int32(self.dst_pts)], True, color_b, 8)
        rect = [np.int32([self.dst_pts[0], self.dst_pts[2], self.dst_pts[3], self.dst_pts[1]])]
        cv.polylines(new, rect, True, color_b, 8)    

        line_w = 300
        self.put_text(100, line_w * 1, self.image_name, new)
        self.put_text(100, line_w * 2, "%u/%u" % (self.image_index + 1, len(self.file_list)), new)
        self.put_text(100, line_w * 3, "crop" if self.crop else "full", new)
        
        cv.imshow(self.dst_win, new)

    def on_mouse_event(self, event, x, y, flags, param):
        redraw = False
        transform = False

        if event == cv.EVENT_MOUSEMOVE:
            img_copy = self.src_img.copy()
            self.draw_helpers(img_copy, x, y)
            self.draw_src_rect(img_copy)
            cv.imshow(self.src_win, img_copy) 

        if event == cv.EVENT_MBUTTONUP:
            img_copy = self.src_img.copy()
            self.draw_helpers(img_copy, x, y)

            index = int(x / (self.src_w / 2)) + int(y / (self.src_h / 2)) * 2
            self.src_pts[index] = [x, y]

            self.draw_src_rect(img_copy)

            cv.imshow(self.src_win, img_copy) 
            self.draw_transformed(self.src_img.copy())
            
            self.parent = None
            self.note_change()
            self.save_cfg()


    def save_cfg(self):
        item = {}
        
        item["crop"] = self.crop
        if self.parent == None:
            item["points"] = self.src_pts.tolist()
        else:
            item["parent"] = self.parent
            
        self.cfg[self.image_name] = item
        
        common.store_config(self.cfg, self.path)
            
    def save_cfg_box(self):
        self.cfg["box"] = dict(self.props)
        
        common.store_config(self.cfg, self.path)            
            
    def resolution_changed(self):
        return self.cfg["box"]["width"] != self.props["width"] or self.cfg["box"]["height"] != self.props["height"] or self.cfg["box"]["margin"] != self.props["margin"]
        
    def resolution_prev_changed(self):
        return self.cfg["box"]["prev_scale"] != self.props["prev_scale"]
            
    def tgl_crop(self):
        self.crop = not self.crop
        self.save_cfg()

    def regenerate(self):
        full = os.path.join(self.path, "full")
        fast = os.path.join(self.path, "fast")
        
        if not os.path.exists(full):
            os.mkdir(full)
        if not os.path.exists(fast):
            os.mkdir(fast)    
            
        full = os.path.join(self.path, "full", self.image_name)
        fast = os.path.join(self.path, "fast", self.image_name)            
        
        fast_w = int(self.props["width"] * (self.props["prev_scale"] / 100.0))
        fast_h = int(self.props["height"] * (self.props["prev_scale"] / 100.0))
        
        change = False

        if self.resolution_changed():
#            print("Output resolution changed!")
            change = True        
            
        elif self.parent in self.changed:
#            print("Parent %s was changed!" % self.parent)
            change = True
        
        elif self.image_name in self.changed:
#            print("Transformation was changed!")
            change = True
        
        elif not os.path.exists(full) or not os.path.exists(fast):
#            print("Outputs does not exists!")
            change = True
        
        if change:
            print("Regenerating %s" % self.image_name)

            if not self.loaded:
                self.load_now()
            
            matrix = cv.getPerspectiveTransform(self.src_pts, self.dst_pts)
            print(self.src_img.shape)
            tmp = cv.warpPerspective(self.src_img, matrix, self.dst_size)
            print(tmp.shape)
            cv.imwrite(full, tmp)
            tmp = cv.resize(tmp, (fast_h, fast_w))
            cv.imwrite(fast, tmp)

        elif self.resolution_prev_changed():
            print("Just resizing preview for %s" % self.image_name)

            tmp = cv.imread(full)
            tmp = cv.resize(tmp, (fast_h, fast_w))
            cv.imwrite(fast, tmp)
        
        
    def generate_all(self, start = 0):
        pb = common.create_progressbar()
        self.image_index = start
        while self.image_index < len(self.file_list):
            text = "[%u / %u] %s" % (self.image_index + 1, len(self.file_list), self.file_list[self.image_index])
            prog = 100 * (self.image_index + 1) / len(self.file_list)
            common.update_progressbar(pb, "Procesing transformations", text, prog)
            self.load_image(self.image_index, True)
            self.regenerate()
            self.image_index += 1
            
        common.close_progressbar(pb)

        
    def run(self, index = 0):
        self.load_image(index)
        
        while True:
            try:
                if cv.getWindowProperty(self.src_win, cv.WND_PROP_VISIBLE) == 0:
                    break
                if cv.getWindowProperty(self.dst_win, cv.WND_PROP_VISIBLE) == 0:
                    break
            except:
                break
            
            code = cv.waitKey(1)

            if code == ord('c'):
                self.tgl_crop()
                self.draw_transformed(self.src_img.copy())
            
            if code == ord('n'):
                self.image_index = (self.image_index + len(self.file_list) - 1) % len(self.file_list)
                self.regenerate()
                self.load_image(self.image_index)            
            
            if code == ord('m'):
                self.image_index = (self.image_index + 1) % len(self.file_list)
                self.regenerate()
                self.load_image(self.image_index)

            if code == ord('q'):
                break    
                
        if self.resolution_changed() or self.resolution_prev_changed():
            self.generate_all()
        else:
            self.regenerate()
            self.generate_all(self.image_index + 1)
            
        self.save_cfg_box()   
            
        try:
            cv2.destroyWindow(self.src_win)
        except:
            print("%s allready closed" % self.src_win)
        try:
            cv2.destroyWindow(self.dst_win)
        except:
            print("%s allready closed" % self.dst_win)
        
if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = common.get_dir()
    
    norm = Normalizator(path)
    norm.run()


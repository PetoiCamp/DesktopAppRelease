#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
os.environ["PETOI_SHOW_GUI"] = "1"
from PetoiRobot import *

language = languageList['English']

BittleRWinSet = {
    "imageW": 360,       # The width of image
    "sliderW": 260,      # The width of the slider rail corresponding to joint numbers 0 to 3
    "rowJoint1": 2,      # The row number of the label with joint number 2 and 3
    "sliderLen": 260,    # The length of the slider rail corresponding to joint numbers 4 to 15
    "rowJoint2": 4       # The row number of the label with joint number 4 or 15 is located
}

RegularWinSet = {
    "imageW": 250,
    "sliderW": 200,
    "rowJoint1": 11,
    "sliderLen": 150,
    "rowJoint2": 2
}

BittleRMacSet = {
    "imageW": 300,       # The width of image
    "sliderW": 200,      # The width of the slider rail corresponding to joint numbers 0 to 3
    "rowJoint1": 2,      # The row number of the label with joint number 2 and 3
    "sliderLen": 200,    # The length of the slider rail corresponding to joint numbers 4 to 15
    "rowJoint2": 4       # The row number of the label with joint number 4 or 15 is located
}

RegularMacSet = {
    "imageW": 190,
    "sliderW": 140,
    "rowJoint1": 11,
    "sliderLen": 140,
    "rowJoint2": 2
}

# Chero-specific settings - compact 5-column layout
CheroWinSet = {
    "imageW": 250,       # Image width for Chero
    "sliderW": 150,      # Width for horizontal sliders (joints 0,1)
    "rowJoint1": 2,      # Row for horizontal sliders
    "sliderLen": 150,    # Length for vertical sliders (joints 2,3,4,5)
    "rowJoint2": 5       # Starting row for vertical sliders (moved down by 1 to make space for image)
}

CheroMacSet = {
    "imageW": 190,
    "sliderW": 120,
    "rowJoint1": 2,
    "sliderLen": 120,
    "rowJoint2": 5
}

parameterWinSet = {
    "Nybble": RegularWinSet,
    "Bittle": RegularWinSet,
    "BittleX+Arm": BittleRWinSet,
    "DoF16": RegularWinSet,
    "Chero": CheroWinSet,
    "Mini": CheroWinSet,
}

parameterMacSet = {
    "Nybble": RegularMacSet,
    "Bittle": RegularMacSet,
    "BittleX+Arm": BittleRMacSet,
    "DoF16": RegularMacSet,
    "Chero": CheroMacSet,
    "Mini": CheroMacSet,
}

frontJointIdx = [4, 5, 8, 9, 12, 13]

# BiBoard products use firmware strings like "B10_..."; wire diagrams are Model<digit>_Wire.jpeg (digit from version[1]).
# NyBoard products (Bittle, Nybble) always use Model_Wire.jpeg. From the Model menu, BiBoard trio uses digit 1 (same as boardVersion[1]=='1').
WIRE_BIBOARD_MODELS = frozenset({'BittleX', 'BittleX+Arm', 'NybbleQ'})

def txt(key):
    return language.get(key, textEN[key])
    
class Calibrator:
    def __init__(self,model,lan):
        self.calibratorReady = False
        global language
        language = lan
        smartConnectPorts()
        start = time.time()
        while config.model_ == '':
            if time.time() - start > 5:
                config.model_ = model
                config.version_ = "N_210101"
                print('Use the model set in the UI interface.')
            time.sleep(0.01)
        self.configName = config.model_
        self.boardVersion = config.version_
        # printH('boardVersion:', self.boardVersion)
        config.model_ = config.model_.replace(' ', '')
        if config.model_ == 'BittleX':
            self.model = 'Bittle'
        elif config.model_ == 'NybbleQ':
            self.model = 'Nybble'
        else:
            self.model = config.model_
        self.is6dof = self.model in ('Chero', 'Mini')

        self.winCalib = Tk()
        self.winCalib.title(txt('calibTitle'))
        self.winCalib.geometry('+200+100')
        self.winCalib.resizable(True, True)
        self._resize_job = None
        self._slider_resize_meta = []
        self._basis_size = None
        self._live_image_w = None
        self._last_center_img_sig = None
        self._current_posture_suffix = '_Ruler.jpeg'
        self.calibSliders = list()
        self._jointLabels = []
        self.autoCalibButton = None
        self.OSname = self.winCalib.call('tk', 'windowingsystem')
        if self.OSname == 'win32':
            self.winCalib.iconbitmap(resourcePath + 'Petoi.ico')
            self.calibButtonW = 8
        else:
            self.calibButtonW = 4
        self.createMenu()
        self._build_calibration_ui()
        time.sleep(3) # wait for the robot to reboot
        self.calibFun('c')
        self.winCalib.update()
        self.calibratorReady = True
        self.winCalib.protocol('WM_DELETE_WINDOW', self.closeCalib)
        self.winCalib.focus_force()    # force the main interface to get focus
        self.winCalib.mainloop()

    @staticmethod
    def _model_menu_key_equals(a, b):
        return (a or "").replace(" ", "") == (b or "").replace(" ", "")

    def _derive_ui_model(self):
        m = config.model_
        if m == "BittleX":
            self.model = "Bittle"
        elif m == "BittleX+Arm":
            self.model = "BittleX+Arm"
        elif m == "NybbleQ":
            self.model = "Nybble"
        elif m == "Chero":
            self.model = "Chero"
        elif m == "Mini":
            self.model = "Mini"
        else:
            self.model = m
        self.is6dof = self.model in ("Chero", "Mini")

    def _tear_down_calibration_ui(self):
        if self._resize_job is not None:
            try:
                self.winCalib.after_cancel(self._resize_job)
            except Exception:
                pass
            self._resize_job = None
        try:
            self.winCalib.unbind('<Configure>')
        except Exception:
            pass
        self._slider_resize_meta = []
        self._basis_size = None
        self._live_image_w = None
        self._last_center_img_sig = None
        for w in list(self.calibSliders):
            try:
                w.destroy()
            except Exception:
                pass
        self.calibSliders = []
        for w in list(self._jointLabels):
            try:
                w.destroy()
            except Exception:
                pass
        self._jointLabels = []
        if self.autoCalibButton is not None:
            try:
                self.autoCalibButton.destroy()
            except Exception:
                pass
            self.autoCalibButton = None
        for attr in ("imgWiring", "imgPosture"):
            w = getattr(self, attr, None)
            if w is not None:
                try:
                    w.destroy()
                except Exception:
                    pass
                setattr(self, attr, None)
        if getattr(self, "frameCalibMid", None) is not None:
            try:
                self.frameCalibMid.destroy()
            except Exception:
                pass
            self.frameCalibMid = None
        if getattr(self, "frameCalibButtons", None) is not None:
            try:
                self.frameCalibButtons.destroy()
            except Exception:
                pass
            self.frameCalibButtons = None

    def _adjust_window_geometry_for_model(self):
        self.winCalib.update_idletasks()
        rw = self.winCalib.winfo_reqwidth()
        rh = self.winCalib.winfo_reqheight()
        if self.model == "BittleX+Arm":
            rh += 3
        self.winCalib.geometry(f"{rw}x{rh}+200+100")
        self._basis_size = (rw, rh)

    def _configure_responsive_grid(self):
        """Center column grows with the window; only top content rows expand vertically (no huge grey footer)."""
        w = self.winCalib
        pad = 12
        img_floor = int(self.parameterSet['imageW']) + pad
        if self.is6dof:
            for c in range(5):
                w.grid_columnconfigure(c, weight=1, minsize=0)
            w.grid_columnconfigure(2, weight=3, minsize=max(180, img_floor))
        else:
            for c in range(7):
                w.grid_columnconfigure(c, weight=1, minsize=0)
            # Heavier center column so wiring/ruler JPEGs get more width when the window grows.
            w.grid_columnconfigure(3, weight=5, minsize=max(220, img_floor + 20))
        # Rows 0–1: top horizontal sliders. Rows 2–13: image stack (wiring / Calibrate row / posture).
        # Row 14: Walk/Save/Abort + bottom horizontal sliders (side columns).
        cal_mid = getattr(self, "_calib_mid_row", 7)
        for r in range(15):
            if r in (0, 1, 14, cal_mid):
                w.grid_rowconfigure(r, weight=0)
            elif 2 <= r <= 13:
                w.grid_rowconfigure(r, weight=1)
            else:
                w.grid_rowconfigure(r, weight=0)
        for r in range(15, 28):
            w.grid_rowconfigure(r, weight=0)

    def _apply_photo_contain(self, label, path, max_w, max_h):
        """Scale image to fit inside max_w x max_h without cropping or distortion."""
        max_w = max(40, int(max_w))
        max_h = max(40, int(max_h))
        img = Image.open(path)
        sw, sh = img.size
        if sw <= 0 or sh <= 0:
            return
        scale = min(max_w / sw, max_h / sh)
        nw = max(1, int(sw * scale))
        nh = max(1, int(sh * scale))
        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.LANCZOS
        img2 = img.resize((nw, nh), resample)
        photo = ImageTk.PhotoImage(img2)
        label.config(image=photo)
        label.image = photo

    def _apply_photo_fill(self, label, path, target_w, target_h):
        """Resize image to exactly target_w x target_h (may stretch) to fill the wiring diagram area."""
        target_w = max(40, int(target_w))
        target_h = max(40, int(target_h))
        img = Image.open(path)
        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.LANCZOS
        img2 = img.resize((target_w, target_h), resample)
        photo = ImageTk.PhotoImage(img2)
        label.config(image=photo)
        label.image = photo

    def _relayout_center_panel_images(self):
        """Resize wiring + posture in main-window image cells (rows 2–13); same target width for both bitmaps."""
        self.winCalib.update_idletasks()
        try:
            w1 = self.imgWiring.winfo_width()
            w2 = self.imgPosture.winfo_width()
            ih = self.imgWiring.winfo_height() + self.imgPosture.winfo_height()
        except Exception:
            return
        pad = 4 if self.is6dof else 2
        fw = max(40, max(w1, w2) - pad)
        fh = max(70, ih)
        if fw < 50 or fh < 70:
            return
        sig = (fw, fh)
        if self._last_center_img_sig is not None:
            pfw, pfh = self._last_center_img_sig
            if abs(pfw - fw) < 5 and abs(pfh - fh) < 5:
                return
        self._last_center_img_sig = sig
        gap = 4
        if self.is6dof:
            h_top = max(86, int(fh * 0.66))
        else:
            h_top = max(90, int(fh * 0.52))
        h_bot = max(82, fh - h_top - gap)
        try:
            if getattr(self, '_wire_image_path', None):
                if self.is6dof:
                    self._apply_photo_fill(self.imgWiring, self._wire_image_path, fw, h_top)
                else:
                    self._apply_photo_contain(self.imgWiring, self._wire_image_path, fw, h_top)
                self._wire_photo_ref = self.imgWiring.image
            suff = getattr(self, '_current_posture_suffix', '_Ruler.jpeg')
            self._apply_photo_contain(self.imgPosture, resourcePath + self.model + suff, fw, h_bot)
            self._posture_photo_ref = self.imgPosture.image
            self._live_image_w = fw
        except Exception:
            pass

    def _on_calib_configure(self, event):
        if event.widget != self.winCalib:
            return
        if self._resize_job is not None:
            try:
                self.winCalib.after_cancel(self._resize_job)
            except Exception:
                pass
        self._resize_job = self.winCalib.after(90, self._apply_calibration_resize)

    def _apply_calibration_resize(self):
        self._resize_job = None
        if not self.calibSliders or self._basis_size is None:
            return
        try:
            ww = self.winCalib.winfo_width()
            wh = self.winCalib.winfo_height()
        except Exception:
            return
        if ww < 80 or wh < 80:
            return
        bw, bh = self._basis_size
        sx = max(0.55, min(2.35, ww / max(bw, 1)))
        sy = max(0.55, min(2.35, wh / max(bh, 1)))
        for meta in self._slider_resize_meta:
            try:
                if meta['orient'] == HORIZONTAL:
                    nl = int(meta['base_len'] * sx)
                    nl = max(meta['min_len'], min(nl, 520))
                else:
                    nl = int(meta['base_len'] * sy)
                    nl = max(meta['min_len'], min(nl, 720))
                meta['widget'].config(length=nl)
            except Exception:
                pass
        self._relayout_center_panel_images()

    def _build_calibration_ui(self, model_from_menu=False):
        self.calibSliders = []
        self._jointLabels = []
        self.autoCalibButton = None
        self._slider_resize_meta = []
        self._current_posture_suffix = '_Ruler.jpeg'
        self._calib_center_col = 2 if self.is6dof else 3
        self.frameCalibMid = Frame(self.winCalib)
        self.calibButton = Button(self.frameCalibMid, text=txt('Calibrate'), fg = 'blue', width=self.calibButtonW,command=lambda cmd='c': self.calibFun(cmd))
        self.standButton = Button(self.frameCalibMid, text=txt('Stand Up'), fg = 'blue', width=self.calibButtonW, command=lambda cmd='balance': self.calibFun(cmd))
        self.restButton = Button(self.frameCalibMid, text=txt('Rest'),fg = 'blue', width=self.calibButtonW, command=lambda cmd='d': self.calibFun(cmd))
        self.frameCalibButtons = Frame(self.winCalib)
        self.walkButton = Button(self.frameCalibButtons, text=txt('Walk'),fg = 'blue', width=self.calibButtonW, command=lambda cmd='walk': self.calibFun(cmd))
        self.saveButton = Button(self.frameCalibButtons, text=txt('Save'),fg = 'blue', width=self.calibButtonW, command=lambda: send(goodPorts, ['s', 0]))
        self.abortButton = Button(self.frameCalibButtons, text=txt('Abort'),fg = 'blue', width=self.calibButtonW, command=lambda: send(goodPorts, ['a', 0]))
#        quitButton = Button(self.frameCalibButtons, text=txt('Quit'),fg = 'blue', width=self.calibButtonW, command=self.closeCalib)

        self.OSname = self.winCalib.call('tk', 'windowingsystem')
        print(self.OSname)
        if self.OSname == 'win32':
            self.parameterSet = parameterWinSet[self.model]
        else:
            self.parameterSet = parameterMacSet[self.model]

        if self.model == 'BittleX+Arm':
            scaleNames = BittleRScaleNames
        elif self.is6dof:
            # For Chero-like, use 6-DoF names
            scaleNames = DoF6ScaleNames
        else:
            # self.parameterSet = parameterSet['Regular']
            scaleNames = RegularScaleNames
        self._scaleNames = scaleNames

        # Use actual model name for images (Mini has its own copies)
        modelForImage = config.model_

        if "B" in self.boardVersion and config.model_ != 'DoF16':
            self.imgWiring = createImage(self.frameCalibButtons,
                                         resourcePath + modelForImage + self.boardVersion[1] + '_Wire.jpeg',
                                         self.parameterSet['imageW'])
        else:
            wire_path = wire_plain
        self._wire_image_path = wire_path
        cc = self._calib_center_col
        img_w = int(self.parameterSet['imageW'])
        # Image band: main grid rows 2 .. 13 (second-to-last row); row 14 is walk + bottom sliders.
        if self.is6dof:
            self._wiring_rowspan, self._posture_rowspan = 4, 7
        else:
            self._wiring_rowspan, self._posture_rowspan = 6, 5
        self._img_top_row = 2
        self._img_bottom_row = 13
        self._calib_mid_row = self._img_top_row + self._wiring_rowspan
        self._posture_start_row = self._calib_mid_row + 1
        assert self._posture_start_row + self._posture_rowspan - 1 == self._img_bottom_row

        self.imgWiring = createImage(self.winCalib, wire_path, img_w)
        self.imgWiring.grid(row=self._img_top_row, column=cc, rowspan=self._wiring_rowspan, sticky='nsew')
        self.imgWiring.configure(anchor='center')
        Hovertip(self.imgWiring, txt('tipImgWiring'))

        if config.model_ == 'NybbleQ':
            self.imgPosture = createImage(self.frameCalibButtons, resourcePath + config.model_  + '_Ruler.jpeg', self.parameterSet['imageW'])
        else:
            self.imgPosture = createImage(self.frameCalibButtons, resourcePath + self.model + '_Ruler.jpeg', self.parameterSet['imageW'])
        # Middle image between button rows
        self.imgPosture.grid(row=2, column=0, rowspan=3, columnspan=3, sticky='n')

        # For 6-DoF models, show 6 joints; otherwise 16
        if self.is6dof:
            self.numJoints = 6
        else:
            self.numJoints = 16

        for i in range(self.numJoints):
            if self.is6dof:
                # Chero layout: joints 0,1 horizontal, joints 2,3,4,5 vertical (like DoF16 joints 8,9,10,11)
                if i < 2:  # Joints 0, 1 - horizontal
                    tickDirection = 1
                    cSPAN = 2  # Each horizontal slider spans 2 columns
                    ROW = 0
                    rSPAN = 1
                    ORI = HORIZONTAL
                    LEN = self.parameterSet['sliderW']  # Use full slider width like SkillComposer
                    ALIGN = 'we'
                    
                    if i == 0:  # Head Pan
                        COL = 0  # Joint 0: columns 0-1 (leftmost)
                    else:  # Head Tilt  
                        COL = 3  # Joint 1: columns 3-4 (rightmost, skip column 2)
                else:  # Joints 2, 3, 4, 5 - vertical (like DoF16 joints 8,9,10,11)
                    tickDirection = -1
                    # Map Chero joints 2,3,4,5 to DoF16 layout positions 8,9,10,11
                    if i == 2:  # Joint 2 -> position like DoF16 joint 8 (left front)
                        leftQ = True
                        frontQ = True
                    elif i == 3:  # Joint 3 -> position like DoF16 joint 9 (right front)
                        leftQ = False
                        frontQ = True
                    elif i == 4:  # Joint 4 -> position like DoF16 joint 10 (right back)
                        leftQ = False
                        frontQ = False
                    else:  # Joint 5 -> position like DoF16 joint 11 (left back)
                        leftQ = True
                        frontQ = False
                    
                    LEN = self.parameterSet['sliderLen']
                    rSPAN = 3
                    cSPAN = 1
                    ROW = self.parameterSet['rowJoint2'] + (1 - frontQ) * (rSPAN + 2)
                    
                    # Use specific columns: joints 2,5 at column 0; joints 3,4 at column 4
                    if leftQ:
                        COL = 0  # Joints 2,5: column 0
                        ALIGN = 'sw'
                    else:
                        COL = 4  # Joints 3,4: column 4
                        ALIGN = 'se'
                    ORI = VERTICAL
            else:
                # Original logic for other models (16 joints)
                if i < 4:
                    tickDirection = 1
                    cSPAN = 3
                    if i < 2:
                        ROW = 0
                    else:
                        ROW = self.parameterSet['rowJoint1']

                    if 0 < i < 3:
                        COL = 4
                    else:
                        COL = 0
                    rSPAN = 1
                    ORI = HORIZONTAL
                    LEN = self.parameterSet['sliderW']
                    ALIGN = 'we'

                else:
                    tickDirection = -1
                    leftQ = (i - 1) % 4 > 1
                    frontQ = i % 4 < 2
                    upperQ = i / 4 < 3

                    rSPAN = 3
                    cSPAN = 1
                    ROW = self.parameterSet['rowJoint2'] + (1 - frontQ) * (rSPAN + 2)

                    if leftQ:
                        COL = 3 - i // 4
                        ALIGN = 'sw'
                    else:
                        COL = 3 + i // 4
                        ALIGN = 'se'
                    ORI = VERTICAL
                    LEN = self.parameterSet['sliderLen']
                    # ALIGN = 'sw'
            if i in NaJoints[self.model]:
                clr = 'light yellow'
                stt = DISABLED
            else:
                clr = 'yellow'
                stt = NORMAL
            
            # Set side labels
            if self.is6dof:
                # For 6-DoF models, joints 2,3,4,5 should have side labels corresponding to DoF16 joints 8,9,10,11
                if i in range(2, 6):  # Joints 2,3,4,5
                    # Map Chero joints 2,3,4,5 to DoF16 joints 8,9,10,11 labels
                    dof16_index = i + 6  # 2->8, 3->9, 4->10, 5->11
                    sideLabel = txt(sideNames[dof16_index % 8]) + '\n'
                else:
                    sideLabel = ''
            else:
                if i in range(8, 12):
                    sideLabel = txt(sideNames[i % 8]) + '\n'
                else:
                    sideLabel = ''
                    
            label = Label(self.winCalib,
                          text=sideLabel + '(' + str(i) + ')\n' + txt(scaleNames[i]))
            self._jointLabels.append(label)

            value = DoubleVar()
            if i in frontJointIdx:
                if self.model == 'BittleX+Arm':
                    LEN = LEN + 30
                sliderBar = Scale(self.winCalib, state=stt, fg='blue', bg=clr, variable=value, orient=ORI,
                                  borderwidth=2, relief='flat', width=8, from_=-25 * tickDirection,
                                  to=25 * tickDirection,
                                  length=LEN, tickinterval=10, resolution=1, repeatdelay=100, repeatinterval=100,
                                  command=lambda value, idx=i: self.setCalib(idx, value))
            else:
                sliderBar = Scale(self.winCalib, state=stt, fg='blue', bg=clr, variable=value, orient=ORI,
                                  borderwidth=2, relief='flat', width=8, from_=-25 * tickDirection, to=25 * tickDirection,
                                  length=LEN, tickinterval=10, resolution=1, repeatdelay=100, repeatinterval=100,
                                  command=lambda value, idx=i: self.setCalib(idx, value))
            self.calibSliders.append(sliderBar)
            self._slider_resize_meta.append({
                'widget': sliderBar,
                'orient': ORI,
                'base_len': LEN,
                'min_len': 48,
            })
            
            # Special layout handling for 6-DoF models
            if self.is6dof:
                if i < 2:  # Horizontal sliders (Head Pan/Tilt) - use cSPAN=2 like SkillComposer
                    label.grid(row=ROW, column=COL, columnspan=cSPAN, pady=2, sticky=sticky_label)
                else:  # Vertical sliders - use columnspan=1 to prevent overlap
                    label.grid(row=ROW, column=COL, columnspan=1, pady=2, sticky=sticky_label)
            elif i == 2 and scaleNames == BittleRScaleNames:
                self.autoCalibButton = Button(self.winCalib, text=txt('Auto'), fg='blue',
                                                width=self.calibButtonW, command=lambda cmd='c-2': self.calibFun(cmd))
                label.grid(row=ROW, column=COL, columnspan=2, pady=2, sticky='e')
                self.autoCalibButton.grid(row=ROW, column=COL + 2, pady=2, sticky='w')
            else:
                label.grid(row=ROW, column=COL, columnspan=cSPAN, pady=2, sticky=sticky_label)
            sliderBar.grid(row=ROW + 1, column=COL, rowspan=rSPAN, columnspan=cSPAN, sticky=sticky_scale)
        self._adjust_window_geometry_for_model()
        self._configure_responsive_grid()
        self.winCalib.update_idletasks()
        self._last_center_img_sig = None
        self._current_posture_suffix = '_Ruler.jpeg'
        self._relayout_center_panel_images()
        self.winCalib.bind('<Configure>', self._on_calib_configure)

        def _deferred_center_relayout():
            self._last_center_img_sig = None
            self._relayout_center_panel_images()

        self.winCalib.after(120, _deferred_center_relayout)
        bw, bh = self._basis_size
        img_min = max(200, int(self.parameterSet['imageW']) + 16)
        min_w = max(680, int(bw * 0.58), img_min + 340)
        self.winCalib.minsize(min_w, max(360, int(bh * 0.58)))
        self.winCalib.update_idletasks()
        rw2 = self.winCalib.winfo_reqwidth()
        rh2 = self.winCalib.winfo_reqheight()
        if rw2 > bw or rh2 > bh:
            self.winCalib.geometry(f"{rw2}x{rh2}+200+100")
            self._basis_size = (rw2, rh2)

    def createMenu(self):
        self.menubar = Menu(self.winCalib, background='#ff8000', foreground='black', activebackground='white',
                            activeforeground='black')
        file_menu = Menu(self.menubar, tearoff=0, background='#ffcc99', foreground='black')
        for m in modelOptions:
            file_menu.add_command(label=m, command=lambda model=m: self.changeModel(model))
        self.menubar.add_cascade(label=txt('Model'), menu=file_menu)

        lan_menu = Menu(self.menubar, tearoff=0)
        for l in languageList:
            lan_menu.add_command(label=languageList[l]['lanOption'], command=lambda lanChoice=l: self.changeLan(lanChoice))
        self.menubar.add_cascade(label=txt('lanMenu'), menu=lan_menu)

        help_menu = Menu(self.menubar, tearoff=0)
        help_menu.add_command(label=txt('About'), command=self.showAbout)
        self.menubar.add_cascade(label=txt('Help'), menu=help_menu)

        self.winCalib.config(menu=self.menubar)

    def changeModel(self, modelName):
        if not self.calibratorReady:
            return
        if self._model_menu_key_equals(modelName, self.configName):
            return
        self.calibratorReady = False
        self.configName = modelName
        config.model_ = modelName.replace(" ", "")
        self._derive_ui_model()
        self.saveConfig(defaultConfPath)
        self._tear_down_calibration_ui()
        self._build_calibration_ui(model_from_menu=True)
        try:
            self.calibFun("c")
        except Exception as e:
            logger.error("calibFun after model switch: %s", e)
        self.winCalib.update()
        self.calibratorReady = True

    def changeLan(self, l):
        global language
        if self.calibratorReady and txt('lan') != l:
            language = copy.deepcopy(languageList[l])
            self.defaultLan = l
            self.menubar.destroy()
            self.createMenu()
            self.winCalib.title(txt('calibTitle'))
            self.calibButton.config(text=txt('Calibrate'))
            self.standButton.config(text=txt('Stand Up'))
            self.restButton.config(text=txt('Rest'))
            self.walkButton.config(text=txt('Walk'))
            self.saveButton.config(text=txt('Save'))
            self.abortButton.config(text=txt('Abort'))
            if self.autoCalibButton is not None:
                self.autoCalibButton.config(text=txt('Auto'))
            self._refreshJointLabelTexts()
            Hovertip(self.imgWiring, txt('tipImgWiring'))
            Hovertip(self.imgPosture, txt('tipImgPosture'))
            self.saveConfig(defaultConfPath)

    def _refreshJointLabelTexts(self):
        for i, label in enumerate(self._jointLabels):
            if self.is6dof:
                if i in range(2, 6):
                    dof16_index = i + 6
                    side_label = txt(sideNames[dof16_index % 8]) + '\n'
                else:
                    side_label = ''
            else:
                if i in range(8, 12):
                    side_label = txt(sideNames[i % 8]) + '\n'
                else:
                    side_label = ''
            sn = self._scaleNames[i]
            label.config(text=side_label + '(' + str(i) + ')\n' + txt(sn))

    def showAbout(self):
        messagebox.showinfo(txt('titleVersion'), txt('msgVersion'))
        self.winCalib.focus_force()

    def saveConfig(self, filename):
        self.configuration = [self.defaultLan, self.configName, self.defaultPath, self.defaultSwVer, self.defaultBdVer,
                              self.defaultMode, self.configuration[6], self.configuration[7]]
        saveConfigToFile(self.configuration, filename)

    def _set_posture_image(self, filename_suffix):
        """Swap posture JPEG and rescale both center images to the current frame (same as window resize)."""
        self._current_posture_suffix = filename_suffix
        self._last_center_img_sig = None
        self._relayout_center_panel_images()

    def _calibration_offset_numbers(self, offsets_text):
        """Pick the substring of parsed numbers that correspond to calibration offsets (Chero is 6-DOF, format varies)."""
        numeric_matches = re.findall(r'-?\d+(?:\.\d+)?', offsets_text)
        if self.is6dof:
            n = len(numeric_matches)
            if n >= 32:
                return numeric_matches[16:22]
            if n >= 12:
                return numeric_matches[6:12]
            if n >= 6:
                return numeric_matches[:6]
            return numeric_matches
        return numeric_matches[self.numJoints:]

    def calibFun(self, cmd):
#        global ports
        if cmd == 'c' or cmd == 'c-2':
            self._set_posture_image('_Ruler.jpeg')
            if cmd == 'c-2':
                send(goodPorts, ['c', [-2], 0])
                time.sleep(1)
                result = send(goodPorts, ['c', 0])
            else:
                result = send(goodPorts, [cmd, 0])
            # print("result:", result)

            if result != -1:
                offsets = result[1]
                print("Raw result:", offsets)
                
                # Calibration dump: 16-DOF uses 16 pose-related numbers then 16 offsets; Chero may use 6+6 or 6 only.
                numeric_matches = self._calibration_offset_numbers(offsets)
                # print("numeric_matches:", numeric_matches)

                # Filter out values that are clearly not joint offsets
                # Joint offsets should be reasonable values (typically between -50 and 50)
                cleaned_offsets = []
                for match in numeric_matches:
                    try:
                        value = float(match)
                        # Only accept reasonable offset values
                        if -50 <= value <= 50:
                            cleaned_offsets.append(value)
                    except ValueError:
                        continue
                # print("cleaned_offsets:", cleaned_offsets)
                # If we don't have enough valid offsets, try alternative parsing
                if len(cleaned_offsets) < 6:  # Need at least 6 for Chero
                    # Try to find comma-separated values
                    if ',' in offsets:
                        parts = offsets.split(',')
                        for part in parts:
                            try:
                                value = float(part.strip())
                                if -50 <= value <= 50:
                                    cleaned_offsets.append(value)
                            except ValueError:
                                continue
                
                # Ensure we have at least 16 offsets for compatibility
                while len(cleaned_offsets) < 16:
                    cleaned_offsets.append(0.0)
                
                offsets = cleaned_offsets[:self.numJoints]
                # print("cleaned_offsets:", cleaned_offsets)
            else:
                offsets = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

            if cmd == 'c-2':
                print("offset2:", offsets[2])
                if int(offsets[2]) > 25:
                    messagebox.showwarning(title=txt('Warning'), message=txt('AutoCali failed'))
                else:
                    self.calibSliders[2].set(offsets[2])
            else:
                # For 6-DoF models, only set offsets for 6 joints; for others, set all 16
                if self.is6dof:
                    for i in range(min(6, len(self.calibSliders), len(offsets))):
                        self.calibSliders[i].set(offsets[i])
                else:
                    for i in range(min(16, len(self.calibSliders), len(offsets))):
                        self.calibSliders[i].set(offsets[i])
        elif cmd == 'd':
            self._set_posture_image('_Rest.jpeg')
            send(goodPorts, ['d', 0])
        elif cmd == 'balance':
            self._set_posture_image('_Stand.jpeg')
            send(goodPorts, ['kbalance', 0])
        elif cmd == 'walk':
            self._set_posture_image('_Walk.jpeg')
            send(goodPorts, ['kwkF', 0])

        self.imgPosture.grid(
            row=self._posture_start_row,
            column=self._calib_center_col,
            rowspan=self._posture_rowspan,
            sticky='nsew',
        )

        Hovertip(self.imgPosture, txt('tipImgPosture'))
        self.winCalib.update()

    def setCalib(self, idx, value):
        if not self.calibratorReady or idx in NaJoints[self.model]:
            return
        value = int(value)
        send(goodPorts, ['c', [idx, value], 0])

    def closeCalib(self):
        confirm = messagebox.askyesnocancel(title=None, message=txt('Do you want to save the offsets?'),
                                            default=messagebox.YES)
        if confirm is not None:
#            global ports
            if confirm:
                send(goodPorts, ['s', 0])
            else:
                send(goodPorts, ['a', 0])
            time.sleep(0.1)
            self.calibratorReady = False
            self.calibSliders.clear()
            self.winCalib.destroy()
            closeAllSerial(goodPorts)
            os._exit(0)
            
if __name__ == '__main__':
    # Do not reassign goodPorts: `from PetoiRobot import *` binds the same dict as ardSerial.goodPorts;
    # smartConnectPorts()/testPort populate that shared dict. If `goodPorts = {}` ran here, this module's
    # name would point at an empty dict and send(goodPorts, ...) would always see len==0 (no serial I/O).
    # goodPorts = {}
    try:
        #        time.sleep(2)
        #        if len(goodPorts)>0:
        #            t=threading.Thread(target=keepReadingSerial,args=(goodPorts,))
        #            t.start()
        model = "Bittle"
        Calibrator(model,language)
        closeAllSerial(goodPorts)
        os._exit(0)
    except Exception as e:
        logger.info("Exception")
        closeAllSerial(goodPorts)
        raise e


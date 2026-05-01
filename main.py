#Update date: 2025 10 27 
#Location: Shanghai
#Author: Federico 

import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
from PIL import Image, ImageTk
import math
import csv
import threading
import queue
import base64
from io import BytesIO

def hex_to_bgr(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (4, 2, 0))

class ContourInfo:
    def __init__(self, contour, contour_id, offset=(0, 0), scale=1.0):
        self.contour = (contour * scale).astype(np.int32) + offset
        self.id = contour_id
        self.deleted = False
      
        M = cv2.moments(self.contour)
        if M["m00"] > 0:
            self.cx = int(M["m10"] / M["m00"])
            self.cy = int(M["m01"] / M["m00"])
        else:
            brect = cv2.boundingRect(self.contour)
            self.cx = brect[0] + brect[2] // 2
            self.cy = brect[1] + brect[3] // 2
          
        self.color = '#00FF00'
        self.thickness = 2
        self.is_manual = False

class CircuitContourAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Contour Analyzer - Final Version")
        self.root.geometry("1400x900")

        style = ttk.Style(self.root)
        try:
            style.theme_use('clam')
            style.configure("Toolbutton", padding=0, relief="flat")
        except tk.TclError:
            print("Clam theme not available, using default.")
        self.selected_contour = None
        self.result_visible = tk.BooleanVar(value=True)

        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        # Create a PanedWindow to allow resizing between canvas and results
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.VERTICAL)
        #self.paned_window.pack(side="left", fill="both", expand=True)
        self.right_panel = ttk.Frame(self.main_frame)
        self.main_frame.columnconfigure(0, weight=10)
        self.main_frame.columnconfigure(1, weight=0)
        self.main_frame.rowconfigure(0, weight=1)
        self.paned_window.grid(row=0, column=0, sticky="nsew")
        self.right_panel.grid(row=0, column=1, sticky="ns", padx=10)

        # self.right_panel = ttk.Frame(self.main_frame, width=200)
        # self.right_panel.pack(side="right", fill="y", padx=10)
      


        # The canvas frame is the top pane
        self.canvas_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.canvas_frame, weight=3) # weight controls initial size ratio

        #self.canvas_frame.grid(row=0, column=0, sticky="nsew")
        self.canvas = tk.Canvas(self.canvas_frame, bg="#404040")
        self.canvas.pack(fill="both", expand=True)

        # self.result_frame = ttk.LabelFrame(self.left_panel, text="轮廓分析结果")
        # self.result_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        # self.result_text = tk.Text(self.result_frame, wrap="word", state="disabled", height=10)
        # self.result_text.pack(fill="both", expand=True)

        # --- Collapsible Result Frame ---
        self.result_container_ref = ttk.Frame(self.paned_window)
        result_container = self.result_container_ref # Keep using the local variable for subsequent lines
        #result_container.grid(row=1, column=0, sticky="nsew", pady=5)
        self.paned_window.add(result_container, weight=0) # weight controls initial size ratio
        result_container.columnconfigure(0, weight=1)
        # Title bar with toggle button
        title_bar = ttk.Frame(result_container)
        title_bar.grid(row=0, column=0, sticky="ew")

        self.toggle_button = ttk.Button(title_bar, text="▼ 轮廓分析结果", command=self.toggle_result_frame, style="Toolbutton")
        self.toggle_button.pack(side="left")

        # The actual frame that will be hidden/shown
        self.result_frame = ttk.Frame(result_container, padding="5")
        self.result_frame.grid(row=1, column=0, sticky="nsew")
        self.result_frame.columnconfigure(0, weight=1)
        self.result_frame.rowconfigure(0, weight=1)
        self.result_text = tk.Text(self.result_frame, wrap="word", state="disabled")
        self.result_text.grid(row=0, column=0, sticky="nsew")
        # --- End of Collapsible Result Frame ---


        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_image)
        self.canvas.bind("<MouseWheel>", self.mousewheel_zoom)

        # State variables for the new measurement function
        self.measure_mode = tk.BooleanVar(value=False)
        self.measure_points = []
        self.measurements_data = []
      
        # Create a Notebook to hold all control panels
        self.notebook = ttk.Notebook(self.right_panel)
        self.notebook.pack(fill="both", expand=True, pady=5)

        # Tab 1: Image Processing Settings (combines ROI, Control, Style)
        self.image_processing_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.image_processing_tab_frame, text="图像处理设置")
        self.setup_roi_widgets(self.image_processing_tab_frame)
        self.setup_control_widgets(self.image_processing_tab_frame)
        self.setup_style_widgets(self.image_processing_tab_frame)

        # Tab 2: Manual Edit and Measurement
        self.measurement_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.measurement_tab_frame, text="尺寸测量")
        self.setup_manual_edit_widgets(self.measurement_tab_frame)

        #self.setup_action_buttons()
      
        self.original_image = None
        self.image_tk = None
        self.contours_data = []
        self.scale_factor = 1.0
        self.current_scale = 1.0
        self.roi_rect = None
      
        self.image_offset_x, self.image_offset_y = 0, 0
        self.drag_start_x, self.drag_start_y = 0, 0

        self.calibrating = False
        self.cal_points = []

        # # State variables for the  measurement function
        # self.measure_mode = tk.BooleanVar(value=False)
        # self.measure_points = []
        # self.measurements_data = []

        self.drag_data = {"x": 0, "y": 0, "rect": None}
        self.drawing_points = []
        self.newly_added_contours = []

        # Threading and Queue for non-blocking processing
        self.processing_queue = queue.Queue()
        self.is_processing = False
        self.processing_thread = None
        self.after_id = None # For debouncing
      
        self.load_default_image()
        self.check_queue()
        # --- Version Info ---
        version_info_text = "Author: FedericoLi\nVersion: ECTV 2.3\nUpdate date: 20251027"
        version_label = ttk.Label(self.right_panel, text=version_info_text, justify=tk.LEFT, foreground="gray")
        version_label.pack(side="bottom", anchor="sw", pady=10, padx=10)


    def setup_roi_widgets(self, parent_frame):
        roi_frame = ttk.LabelFrame(parent_frame, text="识别区域与性能")
        roi_frame.pack(fill="x", pady=5)
      
        inner_frame = ttk.Frame(roi_frame) # Create an inner frame
        inner_frame.pack(fill="both", expand=True, padx=5, pady=5) # Pack the inner frame
        inner_frame.grid_columnconfigure(1, weight=1) # Configure grid for the inner frame

        ttk.Label(inner_frame, text="模式:").grid(row=0, column=0, padx=5, sticky="w")
        self.roi_mode_var = tk.StringVar(value="whole")
        ttk.Radiobutton(inner_frame, text="整张图", variable=self.roi_mode_var, value="whole", command=self.on_roi_mode_change).grid(row=1, column=0, sticky="w", padx=5)
        ttk.Radiobutton(inner_frame, text="自定义区域", variable=self.roi_mode_var, value="custom", command=self.on_roi_mode_change).grid(row=1, column=1, sticky="w", padx=5)
      
        self.select_roi_btn = ttk.Button(inner_frame, text="选择区域", command=self.enter_roi_selection_mode, state="disabled")
        self.select_roi_btn.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

        ttk.Label(inner_frame, text="ROI处理算法:").grid(row=3, column=0, padx=5, sticky="w")
        self.roi_algo_var = tk.StringVar(value="全局阈值")
        self.roi_algo_combo = ttk.Combobox(inner_frame, textvariable=self.roi_algo_var, values=["全局阈值", "自适应阈值", "GrabCut分割"], state="disabled")
        self.roi_algo_combo.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.roi_algo_combo.bind("<<ComboboxSelected>>", self.on_roi_mode_change)

        ttk.Label(inner_frame, text="图像缩放(性能):").grid(row=4, column=0, padx=5, sticky="w")
        self.binning_var = tk.StringVar(value="100% (原始尺寸)")
        self.binning_combo = ttk.Combobox(inner_frame, textvariable=self.binning_var, values=["100% (原始尺寸)", "50% (中等)", "25% (快速)"], state="readonly")
        self.binning_combo.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.binning_combo.bind("<<ComboboxSelected>>", self.on_roi_mode_change)

    def setup_control_widgets(self, parent_frame):
        control_panel = ttk.LabelFrame(parent_frame, text="轮廓检测参数")
        control_panel.pack(fill="x", pady=5)
      
        inner_frame = ttk.Frame(control_panel) # Create an inner frame
        inner_frame.pack(fill="both", expand=True, padx=5, pady=5) # Pack the inner frame
        inner_frame.grid_columnconfigure(1, weight=1) # Configure grid for the inner frame

        self.threshold_label = ttk.Label(inner_frame, text="二值化阈值:")
        self.threshold_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.threshold_var = tk.IntVar(value=127)
        self.threshold_scale = ttk.Scale(inner_frame, from_=0, to=255, variable=self.threshold_var, length=200)
        self.threshold_scale.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
      
        ttk.Label(inner_frame, text="去噪核大小:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.kernel_var = tk.IntVar(value=3)
        self.kernel_scale = ttk.Scale(inner_frame, from_=1, to=15, variable=self.kernel_var, length=200)
        self.kernel_scale.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        ttk.Label(inner_frame, text="轮廓模式:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.contour_mode = tk.StringVar(value="RETR_EXTERNAL")
        self.contour_mode_combo = ttk.Combobox(inner_frame, textvariable=self.contour_mode, values=["RETR_EXTERNAL", "RETR_TREE"], state="readonly")
        self.contour_mode_combo.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.contour_mode_combo.bind("<<ComboboxSelected>>", self.update_processing)

        self.realtime_render_var = tk.BooleanVar(value=False)
        self.realtime_render_check = ttk.Checkbutton(inner_frame, text="实时渲染", variable=self.realtime_render_var, command=self.toggle_realtime_render)
        self.realtime_render_check.grid(row=6, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        self.toggle_realtime_render() # Initialize slider binding based on default value

      

    def toggle_realtime_render(self):
        if self.realtime_render_var.get():
            self.threshold_scale.config(command=self.update_processing)
            self.kernel_scale.config(command=self.update_processing)
            self.threshold_scale.unbind("<ButtonRelease-1>")
            self.kernel_scale.unbind("<ButtonRelease-1>")
        else:
            self.threshold_scale.config(command=None)
            self.kernel_scale.config(command=None)
            self.threshold_scale.bind("<ButtonRelease-1>", self.update_processing)
            self.kernel_scale.bind("<ButtonRelease-1>", self.update_processing)

    def setup_style_widgets(self, parent_frame):
        style_panel = ttk.LabelFrame(parent_frame, text="轮廓与编号样式")
        style_panel.pack(fill="x", pady=5)
        ttk.Label(style_panel, text="轮廓颜色:").grid(row=0, column=0, padx=5, sticky="w")
        self.contour_color = '#00FF00'
        self.contour_color_btn = ttk.Button(style_panel, text="选择颜色", command=self.select_contour_color)
        self.contour_color_btn.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Label(style_panel, text="轮廓粗细:").grid(row=1, column=0, padx=5, sticky="w")
        self.contour_thickness = tk.IntVar(value=2)
        self.contour_thickness_scale = ttk.Scale(style_panel, from_=1, to=8, variable=self.contour_thickness, command=self.update_style, length=200)
        self.contour_thickness_scale.grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Label(style_panel, text="编号颜色:").grid(row=2, column=0, padx=5, sticky="w")
        self.id_color = '#FFFFFF'
        self.id_color_btn = ttk.Button(style_panel, text="选择颜色", command=self.select_id_color)
        self.id_color_btn.grid(row=2, column=1, sticky="ew", padx=5)
        self.show_id_var = tk.BooleanVar(value=True)
        self.show_id_check = ttk.Checkbutton(style_panel, text="显示编号", variable=self.show_id_var, command=self.update_display)
        self.show_id_check.grid(row=2, column=2, padx=5)
        ttk.Label(style_panel, text="字体大小:").grid(row=3, column=0, padx=5, sticky="w")
        self.font_size = tk.DoubleVar(value=0.7)
        self.font_size_scale = ttk.Scale(style_panel, from_=0.5, to=2.0, variable=self.font_size, command=self.update_display, length=200)
        self.font_size_scale.grid(row=3, column=1, sticky="ew", padx=5)

        # --- Action Buttons Panel ---
        action_frame = ttk.LabelFrame(parent_frame, text="文件操作")
        action_frame.pack(fill="x", pady=10, padx=5) # Added padx to align with other frames

        self.load_btn = ttk.Button(action_frame, text="加载图像", command=self.load_image)
        self.load_btn.pack(side="left", fill="x", expand=True, padx=2, pady=5)
        self.export_btn = ttk.Button(action_frame, text="导出结果", command=self.export_results)
        self.export_btn.pack(side="left", fill="x", expand=True, padx=2, pady=5)
        self.save_btn = ttk.Button(action_frame, text="保存图片", command=self.save_image)
        self.save_btn.pack(side="left", fill="x", expand=True, padx=2, pady=5)

    def setup_manual_edit_widgets(self, parent_frame):
        # Manual Edit controls
        manual_edit_frame = ttk.LabelFrame(parent_frame, text="手动编辑")
        manual_edit_frame.pack(fill="x", pady=5)

        self.edit_mode = tk.BooleanVar(value=False)
        self.edit_mode_check = ttk.Checkbutton(manual_edit_frame, text="编辑模式", variable=self.edit_mode, command=self.toggle_edit_mode)
        self.edit_mode_check.grid(row=0, column=0, padx=5, pady=5)
        self.select_mode = tk.BooleanVar(value=False)
        self.select_mode_check = ttk.Checkbutton(manual_edit_frame, text="框选删除", variable=self.select_mode, command=self.toggle_select_mode)
        self.select_mode_check.grid(row=0, column=1, padx=5, pady=5)
        self.draw_mode = tk.BooleanVar(value=False)
        self.draw_mode_check = ttk.Checkbutton(manual_edit_frame, text="手动绘制", variable=self.draw_mode, command=self.toggle_draw_mode)
        self.draw_mode_check.grid(row=0, column=2, padx=5, pady=5)
        self.contour_select_mode = tk.BooleanVar(value=False)
        self.contour_select_check = ttk.Checkbutton(manual_edit_frame, text="轮廓颜色", variable=self.contour_select_mode, command=self.toggle_contour_select_mode)
        self.contour_select_check.grid(row=0, column=3, padx=5, pady=5)


        ttk.Label(manual_edit_frame, text="绘制模式:").grid(row=2, column=0, padx=5, sticky="w")
        self.draw_shape_var = tk.StringVar(value="多点连线")
        self.draw_shape_combo = ttk.Combobox(manual_edit_frame, textvariable=self.draw_shape_var, values=["多点连线", "矩形", "圆形"], state="readonly")
        self.draw_shape_combo.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        self.draw_shape_combo.bind("<<ComboboxSelected>>", self.toggle_draw_mode)

        self.manual_draw_color = '#00FFFF'
        self.manual_draw_color_btn = ttk.Button(manual_edit_frame, text="绘制颜色", command=self.select_manual_draw_color)
        self.manual_draw_color_btn.grid(row=3, column=0, padx=5, pady=5)
        self.apply_btn = ttk.Button(manual_edit_frame, text="应用编辑", command=self.apply_edits, state="disabled")
        self.apply_btn.grid(row=3, column=1, columnspan=2, pady=5, sticky="ew", padx=5)

        # Measurement tools
        measurement_frame = ttk.LabelFrame(parent_frame, text="测量工具")
        measurement_frame.pack(fill="x", pady=5)

        self.calibrate_btn = ttk.Button(measurement_frame, text="校准比例", command=self.calibrate_scale)
        self.calibrate_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.measure_mode_check = ttk.Checkbutton(measurement_frame, text="测量距离", variable=self.measure_mode, command=self.toggle_measure_mode)
        self.measure_mode_check.grid(row=0, column=0, padx=5, pady=5)
        self.clear_measure_btn = ttk.Button(measurement_frame, text="清除测量", command=self.clear_measurements)
        self.clear_measure_btn.grid(row=0, column=1, padx=5, pady=5)


    # def setup_action_buttons(self):
    #     btn_frame = ttk.Frame(self.right_panel)
    #     btn_frame.pack(fill="x", pady=10)
    #     self.load_btn = ttk.Button(btn_frame, text="加载图像", command=self.load_image)
    #     self.load_btn.pack(side="left", fill="x", expand=True, padx=2)
    #     # self.calibrate_btn = ttk.Button(btn_frame, text="校准比例", command=self.calibrate_scale)
    #     # self.calibrate_btn.pack(side="left", fill="x", expand=True, padx=2)
    #     self.export_btn = ttk.Button(btn_frame, text="导出结果", command=self.export_results)
    #     self.export_btn.pack(side="left", fill="x", expand=True, padx=2)
    #     self.save_btn = ttk.Button(btn_frame, text="保存图片", command=self.save_image)
    #     self.save_btn.pack(side="left", fill="x", expand=True, padx=2)

    def set_ui_state(self, enabled):
        state = "normal" if enabled else "disabled"
      
        # Handle widgets within the notebook tabs
        if hasattr(self, 'notebook'):
            for tab_id in self.notebook.tabs():
                tab_frame = self.notebook.nametowidget(tab_id)
                for child_of_tab in tab_frame.winfo_children():
                    if isinstance(child_of_tab, ttk.LabelFrame): # e.g., roi_frame, control_panel, style_panel, manual_edit_frame, measurement_frame
                        for widget in child_of_tab.winfo_children():
                            if isinstance(widget, (ttk.Button, ttk.Scale, ttk.Combobox, ttk.Radiobutton, ttk.Checkbutton)):
                                widget.config(state=state)
      
        # Handle action buttons (load, calibrate, export, save)
        # Assuming setup_action_buttons creates self.load_btn, self.calibrate_btn, etc.
        if hasattr(self, 'load_btn'): 
            for btn in [self.export_btn, self.save_btn]:
                btn.config(state=state)
            self.load_btn.config(state="normal") # Always keep load button enabled

        if self.is_processing:
             self.result_text.config(state="normal")
             self.result_text.delete(1.0, tk.END)
             self.result_text.insert(tk.END, "处理中，请稍候...")
             self.result_text.config(state="disabled")

    def check_queue(self):
        try:
            result = self.processing_queue.get_nowait()
            self.contours_data = result
            self.is_processing = False
            self.set_ui_state(True)
            self.update_style()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)

    def start_processing_thread(self):
        if self.is_processing:
            return
        self.is_processing = True
        self.set_ui_state(False)
        self.processing_thread = threading.Thread(target=self.process_image_threaded, daemon=True)
        self.processing_thread.start()

    def create_progress_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("处理中")
        # Set the popup to be transient to the main window
        popup.transient(self.root)
        # Center the popup over the main window
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 100
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 50
        popup.geometry(f"200x100+{x}+{y}")
        popup.resizable(False, False)
        ttk.Label(popup, text="正在使用GrabCut算法处理...\n请稍候...", justify='center').pack(pady=20, expand=True)
        # Make it modal
        popup.grab_set()
        self.root.update_idletasks()
        return popup

    def process_image_threaded(self):
        # This runs in a background thread
        progress_popup = None
        try:
            # Create and show the popup only for GrabCut
            if self.roi_mode_var.get() == 'custom' and self.roi_algo_var.get() == "全局阈值":
                progress_popup = self.create_progress_popup()

            result = self.process_image()
            self.processing_queue.put(result)

        finally:
            # Destroy the popup if it was created
            if progress_popup:
                progress_popup.destroy()

    def on_roi_mode_change(self, event=None):
        is_custom = self.roi_mode_var.get() == "custom"
        algo = self.roi_algo_var.get()

        self.select_roi_btn.config(state="normal" if is_custom else "disabled")
        self.roi_algo_combo.config(state="readonly" if is_custom else "disabled")
      
        # Disable threshold controls if custom ROI and not global threshold
        self.threshold_label.config(state="disabled" if (is_custom and algo != "全局阈值") else "normal")
        self.threshold_scale.config(state="disabled" if (is_custom and algo != "全局阈值") else "normal")

        if not is_custom:
            self.roi_rect = None
      
        self.start_processing_thread()

    def enter_roi_selection_mode(self):
        self.unbind_all_edit_modes()
        self.canvas.config(cursor="tcross")
        self.canvas.bind("<ButtonPress-1>", self.start_roi_select)
        self.canvas.bind("<B1-Motion>", self.drag_roi_select)
        self.canvas.bind("<ButtonRelease-1>", self.end_roi_select)

    def start_roi_select(self, event):
        self.drag_data["x"], self.drag_data["y"] = event.x, event.y
        self.drag_data["rect"] = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="yellow", width=2, dash=(5, 5), tags="roi_rect")

    def drag_roi_select(self, event):
        if self.drag_data["rect"]:
            self.canvas.coords(self.drag_data["rect"], self.drag_data["x"], self.drag_data["y"], event.x, event.y)

    def end_roi_select(self, event):
        if not self.drag_data["rect"]: return
        x1, y1, x2, y2 = self.canvas.coords(self.drag_data["rect"])
        self.canvas.delete("roi_rect")
        self.drag_data["rect"] = None

        img_x1, img_y1 = self.canvas_to_image_coords(min(x1, x2), min(y1, y2))
        img_x2, img_y2 = self.canvas_to_image_coords(max(x1, x2), max(y1, y2))

        h, w, _ = self.original_image.shape
        img_x1 = max(0, img_x1)
        img_y1 = max(0, img_y1)
        img_x2 = min(w, img_x2)
        img_y2 = min(h, img_y2)

        self.roi_rect = (img_x1, img_y1, img_x2 - img_x1, img_y2 - img_y1)

        self.unbind_all_edit_modes()
        self.canvas.config(cursor="")
        self.start_processing_thread()

    def process_image(self):
        if self.original_image is None: return []
        try:
            binning_str = self.binning_var.get()
            scale_percent = int(binning_str.split('%')[0])
            binning_scale = scale_percent / 100.0

            process_image = self.original_image
            if binning_scale != 1.0:
                process_image = cv2.resize(self.original_image, (0,0), fx=binning_scale, fy=binning_scale, interpolation=cv2.INTER_AREA)

            target_image = process_image
            offset = (0, 0)
            is_custom_roi = self.roi_mode_var.get() == 'custom' and self.roi_rect
            algo = self.roi_algo_var.get()

            if is_custom_roi:
                x, y, w, h = self.roi_rect
                # Scale ROI rect to the binned image size
                rx, ry, rw, rh = [int(v * binning_scale) for v in (x, y, w, h)]
                if rw > 0 and rh > 0:
                    target_image = process_image[ry:ry+rh, rx:rx+rw]
                    offset = (x, y)
          
            binary = None
            if is_custom_roi and algo == "GrabCut分割":
                if target_image.shape[0] < 3 or target_image.shape[1] < 3: return []
                mask = np.zeros(target_image.shape[:2], np.uint8)
                bgdModel = np.zeros((1,65), np.float64)
                fgdModel = np.zeros((1,65), np.float64)
                rect = (1, 1, target_image.shape[1]-2, target_image.shape[0]-2)
                cv2.grabCut(target_image, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
                binary = np.where((mask==2)|(mask==0), 0, 1).astype('uint8')
            else:
                gray = cv2.cvtColor(target_image, cv2.COLOR_BGR2GRAY)
                if is_custom_roi and algo == "自适应阈值":
                    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
                else:
                    _, binary = cv2.threshold(gray, self.threshold_var.get(), 255, cv2.THRESH_BINARY_INV)

            if binary is None: return []

            kernel_size = self.kernel_var.get()
            if kernel_size > 0:
                kernel = np.ones((kernel_size, kernel_size), np.uint8)
                cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            else:
                cleaned = binary
            mode = cv2.RETR_EXTERNAL if self.contour_mode.get() == "RETR_EXTERNAL" else cv2.RETR_TREE
            contours, _ = cv2.findContours(cleaned, mode, cv2.CHAIN_APPROX_SIMPLE)
          
            contour_results = []
            contour_id = 1
            for cnt in contours:
                if cv2.contourArea(cnt) > 20:
                    contour_results.append(ContourInfo(cnt, contour_id, offset, 1/binning_scale))
                    contour_id += 1
            return contour_results
        except Exception as e:
            messagebox.showerror("处理错误", f"图像处理时出错: {e}")
            return []

    def update_display(self, event=None):
        if self.original_image is None: return
        try:
            display_img = self.original_image.copy()
            # --- Highlight Selected Contour ---
            if self.selected_contour:
                overlay = display_img.copy()
                # Fill the selected contour with solid yellow on the overlay
                cv2.fillPoly(overlay, [self.selected_contour.contour], (0, 255, 255)) # BGR for Yellow
                # Blend the overlay with the original image
                alpha = 0.4 # Transparency factor
                display_img = cv2.addWeighted(overlay, alpha, display_img, 1 - alpha, 0)
            # --- End of Highlight ---  

            if self.roi_mode_var.get() == 'custom' and self.roi_rect:
                x, y, w, h = self.roi_rect
                cv2.rectangle(display_img, (x, y), (x+w, y+h), (0, 255, 255), 2)

            id_text_color = hex_to_bgr(self.id_color)
            font_size = self.font_size.get()

            for cd in self.contours_data:
                if not cd.deleted:
                    contour_color_bgr = hex_to_bgr(cd.color)
                    cv2.drawContours(display_img, [cd.contour], -1, contour_color_bgr, cd.thickness)
                    if self.show_id_var.get():
                        text = str(cd.id)
                        pos = (cd.cx, cd.cy)
                        cv2.putText(display_img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, font_size, (0,0,0), 3, cv2.LINE_AA)
                        cv2.putText(display_img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, font_size, id_text_color, 2, cv2.LINE_AA)
          

            h, w, _ = display_img.shape
            scaled_w, scaled_h = int(w * self.current_scale), int(h * self.current_scale)
          
            if scaled_w > 0 and scaled_h > 0:
                resized_img = cv2.resize(display_img, (scaled_w, scaled_h))
                img_rgb = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb)
                self.image_tk = ImageTk.PhotoImage(image=img_pil)
                self.canvas.delete("all")
                self.canvas.create_image(self.image_offset_x, self.image_offset_y, anchor="nw", image=self.image_tk)
                # --- 开始绘制测量标记 ---
                # # 1. 绘制所有已完成的测量
                for measurement in self.measurements_data:
                    p1_img, p2_img = measurement['p1'], measurement['p2']

                    # 将存储的图像坐标转换为当前画布坐标
                    p1_canvas = self.image_to_canvas_coords(*p1_img)
                    p2_canvas = self.image_to_canvas_coords(*p2_img)

                    # 绘制带箭头的线
                    self.canvas.create_line(p1_canvas, p2_canvas, fill="cyan", width=2, arrow=tk.BOTH)

                    # 绘制距离文本
                    mid_x = (p1_canvas[0] + p2_canvas[0]) // 2
                    mid_y = (p1_canvas[1] + p2_canvas[1]) // 2
                    text = f"{measurement['distance_mm']:.2f} mm"

                    # 为文本添加一个深色背景以提高可读性
                    # 使用 's' (south) 锚点，让文本的底边中点位于指定坐标，这样文本就会在线的上方
                    text_id = self.canvas.create_text(mid_x, mid_y - 10, text=text, fill="white", font=("Arial", 10), anchor='s')
                    bbox = self.canvas.bbox(text_id)
                    if bbox:
                        self.canvas.create_rectangle(bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2,
                                                   fill="#404040", outline="", tags="text_bg")
                        self.canvas.tag_raise(text_id, "text_bg") # 确保文本在背景之上

                # 2. 如果正在进行一次新的测量，绘制它的第一个点 
                if len(self.measure_points) == 1:
                    p1_canvas = self.image_to_canvas_coords(*self.measure_points[0])
                    r = 3
                    self.canvas.create_oval(p1_canvas[0]-r, p1_canvas[1]-r, p1_canvas[0]+r, p1_canvas[1]+r,fill="cyan", outline="cyan")         
                # --- 结束绘制测量标记 ---


                self.update_results()
        except Exception as e:
            messagebox.showerror("显示错误", f"更新显示时发生错误: {e}")

    def select_contour_color(self):
        color_code = colorchooser.askcolor(title="选择轮廓颜色")
        if color_code and color_code[1]:
            self.contour_color = color_code[1]
            self.update_style()

    def select_id_color(self):
        color_code = colorchooser.askcolor(title="选择编号颜色")
        if color_code and color_code[1]:
            self.id_color = color_code[1]
            self.update_display()

    def select_manual_draw_color(self):
        color_code = colorchooser.askcolor(title="选择颜色")
        if not color_code and color_code[1]:
            return# User cancelled
        new_color_hex = color_code[1]
        if self.selected_contour:
            # If a contour is selected, change its color
            self.selected_contour.color = new_color_hex
            self.update_display() # Redraw to show the new color
        else:
            # Otherwise, update the default manual drawing color
            self.manual_draw_color = new_color_hex

    def canvas_to_image_coords(self, canvas_x, canvas_y):
        img_x = (canvas_x - self.image_offset_x) / self.current_scale
        img_y = (canvas_y - self.image_offset_y) / self.current_scale
        return int(img_x), int(img_y)

    def image_to_canvas_coords(self, img_x, img_y):
        canvas_x = img_x * self.current_scale + self.image_offset_x
        canvas_y = img_y * self.current_scale + self.image_offset_y
        return int(canvas_x), int(canvas_y)

    def load_default_image(self):
        img = np.zeros((600, 800, 3), dtype=np.uint8)
        cv2.rectangle(img, (20, 20), (780, 580), (100, 100, 0), -1)
        cv2.rectangle(img, (50, 50), (150, 180), (20, 20, 20), -1)
        cv2.rectangle(img, (200, 70), (300, 150), (20, 20, 20), -1)
        self.original_image = img
        self.reset_state()
        self.start_processing_thread()

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("图像文件", "*.jpg *.png *.bmp")])
        if not file_path: return
        try:
            img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is None: raise ValueError("无法加载图像文件")
            self.original_image = img
            self.reset_state()
            self.start_processing_thread()
        except Exception as e:
            messagebox.showerror("加载错误", f"加载图像失败: {e}")

    def reset_state(self):
        self.scale_factor = 1.0
        self.current_scale = 1.0
        self.image_offset_x, self.image_offset_y = 0, 0
        self.contours_data = []
        self.newly_added_contours = []
        self.drawing_points = []
        self.roi_rect = None
        if hasattr(self, 'roi_mode_var'):
            self.roi_mode_var.set("whole")
            self.on_roi_mode_change()

    def update_processing(self, event=None):
        if self.original_image is None: return

        if self.after_id:
            self.root.after_cancel(self.after_id)

        if self.realtime_render_var.get():
            # Realtime rendering: process immediately
            self.start_processing_thread()
        else:
            # Non-realtime: debounce processing
            self.after_id = self.root.after(300, self.start_processing_thread) # 300ms debounce

    def update_style(self, event=None):
        if self.original_image is None: return
        thickness = self.contour_thickness.get()
        for cd in self.contours_data:

            # Apply thickness to ALL contours
            cd.thickness = thickness
            # Only apply the main color to non-manual contours
            if not cd.is_manual:
                cd.color = self.contour_color
        self.update_display()

    def start_drag(self, event):
        print(">> 'start_drag' 被调用")
        if self.edit_mode.get() or self.is_processing: return
        self.drag_start_x = event.x - self.image_offset_x
        self.drag_start_y = event.y - self.image_offset_y
        self.canvas.config(cursor="fleur")

    def drag_image(self, event):
        if self.edit_mode.get() or self.is_processing: return
        self.image_offset_x = event.x - self.drag_start_x
        self.image_offset_y = event.y - self.drag_start_y
        self.update_display()

    def mousewheel_zoom(self, event):
        if self.is_processing: return
        factor = 1.1 if event.delta > 0 else 0.9
        canvas_x, canvas_y = event.x, event.y
        img_x, img_y = self.canvas_to_image_coords(canvas_x, canvas_y)
        self.current_scale = max(0.1, min(5.0, self.current_scale * factor))
        new_canvas_x, new_canvas_y = self.image_to_canvas_coords(img_x, img_y)
        self.image_offset_x += canvas_x - new_canvas_x
        self.image_offset_y += canvas_y - new_canvas_y
        self.update_display()

    def unbind_all_edit_modes(self):
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.unbind("<Button-3>")
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_image)

    def toggle_edit_mode(self):
        if self.edit_mode.get():
            self.unbind_all_edit_modes()
            self.canvas.config(cursor="cross")
        else:
            self.select_mode.set(False)
            self.draw_mode.set(False)
            self.unbind_all_edit_modes()
            self.canvas.config(cursor="")
            self.canvas.delete("temp_rect")

    def toggle_select_mode(self):
        if self.select_mode.get():
            self.edit_mode.set(True)
            self.draw_mode.set(False)
            self.measure_mode.set(False) 
            self.unbind_all_edit_modes()
            self.canvas.config(cursor="cross")
            self.canvas.bind("<ButtonPress-1>", self.start_select)
            self.canvas.bind("<B1-Motion>", self.drag_select)
            self.canvas.bind("<ButtonRelease-1>", self.end_select)
        else:
            self.toggle_edit_mode()

    def toggle_draw_mode(self, event=None):
        if self.draw_mode.get():
            self.edit_mode.set(True)
            self.select_mode.set(False)
            self.measure_mode.set(False) 
            self.unbind_all_edit_modes()
            self.canvas.config(cursor="plus")

            draw_shape = self.draw_shape_var.get()
            if draw_shape == "多点连线":
                self.canvas.bind("<ButtonPress-1>", self.start_drawing)
                self.canvas.bind("<Button-3>", self.finish_drawing)
            elif draw_shape == "矩形":
                self.canvas.bind("<ButtonPress-1>", self.start_rect_draw)
                self.canvas.bind("<B1-Motion>", self.drag_rect_draw)
                self.canvas.bind("<ButtonRelease-1>", self.end_rect_draw)
            elif draw_shape == "圆形":
                self.canvas.bind("<ButtonPress-1>", self.start_circle_draw)
                self.canvas.bind("<B1-Motion>", self.drag_circle_draw)
                self.canvas.bind("<ButtonRelease-1>", self.end_circle_draw)
        else:
            self.toggle_edit_mode()

    #Contour select mode used to change color of Contour
    def toggle_contour_select_mode(self):
        """Toggles the contour selection mode."""
        if self.contour_select_mode.get():
            self.edit_mode.set(True)
            self.select_mode.set(False)
            self.draw_mode.set(False)
            self.measure_mode.set(False)
            self.unbind_all_edit_modes()
            self.canvas.config(cursor="hand2")
            self.canvas.bind("<ButtonPress-1>", self.on_contour_click)
        else:
            # Exiting select mode
            self.selected_contour = None
            self.canvas.config(cursor="")
            self.unbind_all_edit_modes() # This will re-bind the default drag behavior
            self.update_display() # Redraw to remove any highlighting

    def on_contour_click(self, event):
        """Handles clicks on the canvas to select a contour."""
        if not self.contours_data:
            return
      
        img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
        clicked_point = (img_x, img_y)

        found_contour = None
        # Iterate in reverse order so we select the top-most contour if they overlap
        for cd in reversed(self.contours_data):
          
            if not cd.deleted:
                if cv2.pointPolygonTest(cd.contour, clicked_point, False) >= 0:
                    found_contour = cd
                    break # Stop after finding the first one (top-most)
        self.selected_contour = found_contour
        self.update_display()
          



    def start_select(self, event):
        self.drag_data["x"], self.drag_data["y"] = event.x, event.y
        self.drag_data["rect"] = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red", width=2, dash=(5, 5), tags="temp_rect")

    def drag_select(self, event):
        if self.drag_data["rect"]:
            self.canvas.coords(self.drag_data["rect"], self.drag_data["x"], self.drag_data["y"], event.x, event.y)

    def end_select(self, event):
        if not self.drag_data["rect"]: return
        x1, y1, x2, y2 = self.canvas.coords(self.drag_data["rect"])
        self.canvas.delete(self.drag_data["rect"])
        self.drag_data["rect"] = None
        img_x1, img_y1 = self.canvas_to_image_coords(min(x1, x2), min(y1, y2))
        img_x2, img_y2 = self.canvas_to_image_coords(max(x1, x2), max(y1, y2))
        # Delete contours within the selection box
        for cd in self.contours_data:
            if not cd.deleted and img_x1 < cd.cx < img_x2 and img_y1 < cd.cy < img_y2:
                cd.deleted = True
        #Delete measurements within the selection box
        #Iterate over a copy of the list to allow safe removal
        for measurement in self.measurements_data[:]:
            p1 = measurement['p1']
            p2 = measurement['p2']
            mid_x = (p1[0]+p2[0])/2
            mid_y = (p1[1]+p2[1])/2
            if img_x1 < mid_x < img_x2 and img_y1 < mid_y < img_y2:
                self.measurements_data.remove(measurement)
        self.apply_btn.config(state="normal")
        self.update_display()

    def start_rect_draw(self, event):
        self.drag_data["x"], self.drag_data["y"] = event.x, event.y
        self.drag_data["rect"] = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline=self.manual_draw_color, width=2, tags="temp_draw")

    def drag_rect_draw(self, event):
        if self.drag_data["rect"]:
            self.canvas.coords(self.drag_data["rect"], self.drag_data["x"], self.drag_data["y"], event.x, event.y)

    def end_rect_draw(self, event):
        if not self.drag_data["rect"]: return
        x1, y1, x2, y2 = self.canvas.coords(self.drag_data["rect"])
        self.canvas.delete(self.drag_data["rect"])
        self.drag_data["rect"] = None
        img_x1, img_y1 = self.canvas_to_image_coords(min(x1, x2), min(y1, y2))
        img_x2, img_y2 = self.canvas_to_image_coords(max(x1, x2), max(y1, y2))
      
        # Create a rectangular contour
        contour = np.array([[[img_x1, img_y1]], [[img_x2, img_y1]], [[img_x2, img_y2]], [[img_x1, img_y2]]], dtype=np.int32)
        self.newly_added_contours.append(contour)
        self.apply_btn.config(state="normal")
        self.apply_edits()

    def start_circle_draw(self, event):
        self.drag_data["x"], self.drag_data["y"] = event.x, event.y
        self.drag_data["oval"] = self.canvas.create_oval(event.x, event.y, event.x, event.y, outline=self.manual_draw_color, width=2, tags="temp_draw")

    def drag_circle_draw(self, event):
        if self.drag_data["oval"]:
            self.canvas.coords(self.drag_data["oval"], self.drag_data["x"], self.drag_data["y"], event.x, event.y)

    def end_circle_draw(self, event):
        if not self.drag_data["oval"]: return
        x1, y1, x2, y2 = self.canvas.coords(self.drag_data["oval"])
        self.canvas.delete(self.drag_data["oval"])
        self.drag_data["oval"] = None
      
        # Correct coordinate conversion
        img_x1, img_y1 = self.canvas_to_image_coords(min(x1, x2), min(y1, y2))
        img_x2, img_y2 = self.canvas_to_image_coords(max(x1, x2), max(y1, y2))

        center_x = (img_x1 + img_x2) / 2
        center_y = (img_y1 + img_y2) / 2
        radius_x = abs(img_x2 - img_x1) / 2
        radius_y = abs(img_y2 - img_y1) / 2
      
        # Generate points for a smoother elliptical contour
        num_segments = 360  # Increased for smoother circle
        points = []
        for i in range(num_segments):
            angle = 2 * math.pi * i / num_segments
            x = center_x + radius_x * math.cos(angle)
            y = center_y + radius_y * math.sin(angle)
            points.append([int(round(x)), int(round(y))])
      
        # Close the contour by adding the first point again
        points.append(points[0])
      
        contour = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
        self.newly_added_contours.append(contour)
        self.apply_btn.config(state="normal")
        self.apply_edits()

    def start_drawing(self, event):
        img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
        self.drawing_points.append((img_x, img_y))
        r = 3
        self.canvas.create_oval(event.x - r, event.y - r, event.x + r, event.y + r, fill=self.manual_draw_color, outline=self.manual_draw_color, tags="temp_draw")
        if len(self.drawing_points) > 1:
            prev_canvas_x, prev_canvas_y = self.image_to_canvas_coords(*self.drawing_points[-2])
            self.canvas.create_line(prev_canvas_x, prev_canvas_y, event.x, event.y, fill=self.manual_draw_color, width=2, tags="temp_draw")

    def finish_drawing(self, event):
        if len(self.drawing_points) >= 3:
            contour = np.array(self.drawing_points, dtype=np.int32).reshape((-1, 1, 2))
            self.newly_added_contours.append(contour)
            self.apply_btn.config(state="normal")
        self.drawing_points = []
        self.canvas.delete("temp_draw")
        self.apply_edits()

    def toggle_measure_mode(self):
        """Toggles the distance measurement mode."""
        if self.measure_mode.get():
            self.edit_mode.set(True)
            self.select_mode.set(False)
            self.draw_mode.set(False)
            self.contour_select_mode.set(False) # Ensure other modes are off

            self.unbind_all_edit_modes()
            self.canvas.config(cursor="crosshair")
            self.canvas.bind("<ButtonPress-1>", self.start_measure_drag)# Bind to the new start function
            #print(">> 'handle_measure_click' 已被绑定")
        else:
            # Exit measure mode
            self.canvas.delete("temp_measure_line") # Clean up any dangling temp lines
            self.measure_points = []
            self.unbind_all_edit_modes()
            self.update_display()

    def clear_measurements(self):
          """Clears all completed measurement data and redraws the canvas."""
          self.measurements_data = []
          self.measure_points = []
          self.update_display() 

    def start_measure_drag(self, event):
        """Starts the measurement drag operation."""
        # First point is captured on button press
        img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
        self.measure_points = [(img_x, img_y)]
        # Bind motion and release events
        self.canvas.bind("<B1-Motion>", self.drag_measure_line)
        self.canvas.bind("<ButtonRelease-1>", self.end_measure_drag)

    def drag_measure_line(self, event):
        """Drags a temporary line and shows real-time distance."""
        if not self.measure_points:
            return
        # Clean up previous temporary drawings
        self.canvas.delete("temp_measure_line")
        # Get current mouse position in canvas coordinates
        p1_canvas = self.image_to_canvas_coords(*self.measure_points[0])
        p2_canvas = (event.x, event.y)
        # Draw a dashed line
        self.canvas.create_line(p1_canvas, p2_canvas, fill="cyan", width=2,dash=(5, 5), tags="temp_measure_line")
        # Calculate and display real-time distance if calibrated
        if self.scale_factor != 1.0:
           p2_img = self.canvas_to_image_coords(event.x, event.y)
           pixel_dist = math.sqrt((p2_img[0] - self.measure_points[0][0])**2 + (p2_img[1] - self.measure_points[0][1])**2) 
           real_dist = pixel_dist * self.scale_factor
           text = f"{real_dist:.2f} mm"  
           text_id = self.canvas.create_text(event.x + 10, event.y - 10, text=text,fill="white", font=("Arial", 10), anchor='w',tags="temp_measure_line")
           bbox = self.canvas.bbox(text_id)
           if bbox:
               self.canvas.create_rectangle(bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2,fill="#404040", outline="", tags="temp_measure_line")
               self.canvas.tag_raise(text_id, "temp_measure_line")
  
    def end_measure_drag(self, event):
        """Finalizes the measurement on button release."""
        # Unbind events
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        # Clean up temporary drawings
        self.canvas.delete("temp_measure_line")
        # Check for calibration
        if self.scale_factor == 1.0:
            messagebox.showwarning("未校准", "请先使用'校准比例'功能。")
            self.measure_points = []
            return
        # Get the second point and finalize
        img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
        self.measure_points.append((img_x, img_y))

        if len(self.measure_points) == 2:
            p1_img, p2_img = self.measure_points[0], self.measure_points[1]
            pixel_dist = math.sqrt((p2_img[0] - p1_img[0])**2 + (p2_img[1] - p1_img[1])**2)
            real_dist = pixel_dist * self.scale_factor

            measurement_data = {
                'p1': p1_img,
                'p2': p2_img,
                'distance_mm': real_dist
            }
            self.measurements_data.append(measurement_data)
            # Reset for the next measurement and redraw
            self.measure_points = []
            self.update_display()




                                          



    def apply_edits(self):
        for new_contour in self.newly_added_contours:
            new_id = (max([cd.id for cd in self.contours_data], default=0)) + 1
            new_cd = ContourInfo(new_contour, new_id)
            new_cd.color = self.manual_draw_color
            new_cd.is_manual = True
            self.contours_data.append(new_cd)
        self.newly_added_contours = []
        self.apply_btn.config(state="disabled")
        self.update_display()

    def update_results(self):
        if not self.contours_data:
            self.result_text.config(state="normal")
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "未检测到任何轮廓")
            self.result_text.config(state="disabled")
            return
        try:
            self.result_text.config(state="normal")
            self.result_text.delete(1.0, tk.END)
            total_area = 0
            active_contours = [cd for cd in self.contours_data if not cd.deleted]

            # First, calculate the total area
            for cd in active_contours:
                pixel_area = cv2.contourArea(cd.contour)
                real_area = pixel_area * self.scale_factor**2
                total_area += real_area
                #self.result_text.insert(tk.END, f"轮廓{cd.id}: 像素面积={pixel_area:.1f}, 实际面积={real_area:.2f} mm²\n")

            # 1. Insert summary information first
            self.result_text.insert(tk.END, f"总计: {len(active_contours)}个轮廓, 总面积={total_area:.2f} mm²\n")
            self.result_text.insert(tk.END, f"比例因子: {self.scale_factor:.6f} mm/像素")
            self.result_text.insert(tk.END, f"\n{'='*40}\n")
            #self.result_text.config(state="disabled")
            # 2. Insert detailed information for each contour
            for cd in active_contours:

                pixel_area = cv2.contourArea(cd.contour)
                real_area = pixel_area * self.scale_factor**2
                self.result_text.insert(tk.END, f"轮廓{cd.id}: 像素面积={pixel_area:.1f}, 实际面积={real_area:.2f} mm²\n")
            self.result_text.config(state="disabled")

        except Exception as e:
            messagebox.showerror("结果错误", f"更新结果时发生错误: {e}")

    def calibrate_scale(self):
        if self.original_image is None:
            messagebox.showwarning("警告", "请先加载图像")
            return
      
        # Create a popup to choose calibration method
        popup = tk.Toplevel(self.root)
        popup.title("选择校准方式")
        popup.transient(self.root)

        # Center the popup
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
        popup.geometry(f"300x150+{x}+{y}")
        popup.resizable(False, False)
        popup_frame = ttk.Frame(popup, padding="10")
        popup_frame.pack(expand=True, fill="both")
        ttk.Label(popup_frame, text="请选择一种方式来设置比例尺：").pack(pady=5)
        def on_draw():
            popup.destroy()
            self.start_drawing_calibration()
        def on_manual():
            popup.destroy()
            self.prompt_for_manual_scale()

        draw_btn = ttk.Button(popup_frame, text="绘制校准", command=on_draw)
        draw_btn.pack(pady=5, fill='x')
        manual_btn = ttk.Button(popup_frame, text="手动输入比例尺", command=on_manual)
        manual_btn.pack(pady=5, fill='x')
        popup.grab_set()

    def start_drawing_calibration(self):
        """Initiates the process of calibrating by drawing on the canvas."""
        self.calibrating = True
        self.cal_points = []
        messagebox.showinfo ("校准说明","请在图像上店家两个参考点，并输入实际距离(mm).")
        self.unbind_all_edit_modes()
        self.canvas.bind("<Button-1>",self.image_click_calibrate)

    def prompt_for_manual_scale(self):
        """Prompts the user to manually enter the scale factor."""
        new_scale = simpledialog.askfloat(
            "手动输入比例尺",
            "请输入比例尺 (mm/像素):",
            parent=self.root,
            initialvalue=self.scale_factor
        )
        if new_scale and new_scale > 0:
            self.scale_factor = new_scale
            messagebox.showinfo("成功", f"比例尺已更新为: {self.scale_factor:.6f} mm/像素!")
            self.update_all_measurements()
  
    def update_all_measurements(self):
        """Recalculates all existing measurements based on the current scale factor."""
        for measurement in self.measurements_data:
            p1_img, p2_img = measurement['p1'], measurement['p2']
            pixel_dist = math.sqrt((p2_img[0] - p1_img[0])**2 + (p2_img[1] - p1_img[1])**2)
            measurement['distance_mm'] = pixel_dist * self.scale_factor
        self.update_results()
        self.update_display()

    def toggle_result_frame(self):
        """Shows or hides the result frame."""
        if self.result_visible.get():
            # --- COLLAPSE ---
            # Hide the inner result frame
            self.result_frame.grid_remove()
            # Update the button text
            self.toggle_button.config(text="▶ 轮廓分析结果")
            # Update the state
            self.result_visible.set(False)

            # Save the current sash position before collapsing
            self._last_sash_pos = self.paned_window.sashpos(0)
            # Move the sash to the bottom to hide the pane
            # getting the total height and move the sash almost all the way down
            self.paned_window.update_idletasks()
            height = self.paned_window.winfo_height()
            self.paned_window.sashpos(0, height - 40)

        else:
            # Show the inner result frame
            self.result_frame.grid()
            # Update the button text
            self.toggle_button.config(text="▼ 轮廓分析结果")
            # Update the state
            self.result_visible.set(True)

            # Restore the sash to its last known position, or a default

            if hasattr(self, '_last_sash_pos'):
                self.paned_window.sashpos(0, self._last_sash_pos)
            else:
                # If no last position, set to a default ratio (e.g., 70%)
                self.paned_window.update_idletasks()
                height = self.paned_window.winfo_height()
                self.paned_window.sashpos(0, int(height * 0.7))


    def image_click_calibrate(self, event):
        if not self.calibrating: return
        img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
        self.cal_points.append((img_x, img_y))
        canvas_x, canvas_y = self.image_to_canvas_coords(img_x, img_y)
        r = 2
        self.canvas.create_oval(canvas_x-r, canvas_y-r, canvas_x+r, canvas_y+r, outline="red", fill="red", tags="cal_marker")
        if len(self.cal_points) == 2:
            p1_canvas = self.image_to_canvas_coords(*self.cal_points[0])
            p2_canvas = self.image_to_canvas_coords(*self.cal_points[1])
            self.canvas.create_line(p1_canvas, p2_canvas, fill="red", width=2, tags="cal_marker")
            self.canvas.update_idletasks()
            pixel_distance = math.sqrt((self.cal_points[1][0] - self.cal_points[0][0])**2 + (self.cal_points[1][1] - self.cal_points[0][1])**2)
            actual_length = simpledialog.askfloat("实际长度", "请输入两点之间的实际长度(mm):", parent=self.root)
            if actual_length and actual_length > 0:
                self.scale_factor = actual_length / pixel_distance
                messagebox.showinfo("校准成功", f"比例因子已设置为: {self.scale_factor:.6f} mm/像素")
                self.update_all_measurements() # Use the new function to update everything
                #self.update_results()
            else:
                messagebox.showwarning("警告", "校准已取消或输入无效")
            self.calibrating = False
            self.cal_points = []
            self.unbind_all_edit_modes()
            self.canvas.delete("cal_marker")
            self.update_display()

    def export_results(self):
        active_contours = [cd for cd in self.contours_data if not cd.deleted]
        if not active_contours:
            messagebox.showwarning("无数据", "没有可导出的轮廓数据")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV文件", "*.csv")])
        if not file_path: return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["ContourID", "PixelArea", "RealArea(mm²)"])
                total_real = 0
                for cd in active_contours:
                    pixel_area = cv2.contourArea(cd.contour)
                    real_area = pixel_area * self.scale_factor**2
                    total_real += real_area
                    writer.writerow([cd.id, f"{pixel_area:.1f}", f"{real_area:.2f}"])
                writer.writerow([])
                writer.writerow(["TotalContours", len(active_contours)])
                writer.writerow(["TotalRealArea(mm²)", f"{total_real:.2f}"])
                writer.writerow(["ScaleFactor(mm/pixel)", f"{self.scale_factor:.6f}"])
            messagebox.showinfo("导出成功", f"结果已成功保存到:\n{file_path}")
        except Exception as e:
            messagebox.showerror("导出错误", f"无法保存文件:\n{e}")

    def save_image(self):
        if self.original_image is None: return
        display_img = self.original_image.copy()
        if self.roi_mode_var.get() == 'custom' and self.roi_rect:
            x, y, w, h = self.roi_rect
            cv2.rectangle(display_img, (x, y), (x+w, y+h), (0, 255, 255), 2)

        id_text_color = hex_to_bgr(self.id_color)
        font_size = self.font_size.get()
        for cd in self.contours_data:
            if not cd.deleted:
                contour_color_bgr = hex_to_bgr(cd.color)
                cv2.drawContours(display_img, [cd.contour], -1, contour_color_bgr, cd.thickness)
                if self.show_id_var.get():
                    cv2.putText(display_img, str(cd.id), (cd.cx, cd.cy), cv2.FONT_HERSHEY_SIMPLEX, font_size, (0,0,0), 3, cv2.LINE_AA)
                    cv2.putText(display_img, str(cd.id), (cd.cx, cd.cy), cv2.FONT_HERSHEY_SIMPLEX, font_size, id_text_color, 2, cv2.LINE_AA)
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG图像", "*.png"), ("JPEG图像", "*.jpg")])
        if not file_path: return
        try:
            cv2.imwrite(file_path, display_img)
            messagebox.showinfo("保存成功", f"图像已保存至:\n{file_path}")
        except Exception as e:
            messagebox.showerror("保存错误", f"保存失败: {e}")

ICON_BASE64 ="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"

def load_icon():
    icon_data = base64.b64decode(ICON_BASE64)
    image = Image.open(BytesIO(icon_data))
    return ImageTk.PhotoImage(image)


if __name__ == "__main__":
    root = tk.Tk()
    photo = load_icon()
    root.iconphoto(True, photo)
    app = CircuitContourAnalyzer(root)
    root.mainloop()
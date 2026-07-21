import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import xml.etree.ElementTree as ET
import threading
import os
import math
from slicerCore import sliceYInfill
import tqdm, svgelements
import subprocess

class DraggableRectCanvas(tk.Canvas):
    def __init__(self, parent, width=800, height=600):
        super().__init__(parent, width=width, height=height, bg='#f0f0f0', highlightthickness=1, highlightbackground='#cccccc')
        self.parent = parent
        
        self.canvas_width = width
        self.canvas_height = height
        
        # Boundary margin (minimum distance from edges)
        self.boundary_margin = 50
        
        # SVG properties (just dimensions)
        self.svg_width = 100
        self.svg_height = 100
        self.svg_path = None
        self.original_svg_width = 100
        self.original_svg_height = 100
        
        # Rectangle properties
        self.rect_x = 50
        self.rect_y = 50
        self.rect_width = 100
        self.rect_height = 100
        self.scale_factor = 1.0
        self.custom_scale = None  # If set, use custom scale instead of auto-fit
        
        # Dragging state
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.rect_start_x = 0
        self.rect_start_y = 0
        
        # Rectangle IDs
        self.rect_id = None
        self.info_text_id = None
        
        # Callback for position updates
        self.position_callback = None
        
        # Bind mouse events
        self.bind("<Button-1>", self.on_mouse_down)
        self.bind("<B1-Motion>", self.on_mouse_drag)
        self.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.bind("<Motion>", self.on_mouse_move)
        
        # Draw initial state
        self.draw_canvas()
    
    def set_position_callback(self, callback):
        self.position_callback = callback
    
    def get_svg_dimensions(self, svg_path):
        # efficiently get the svg's dimensions without parsing the ENTIRE file
        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()
            
            # get viewBox or width/height attributes
            viewBox = root.get('viewBox')
            if viewBox:
                # viewBox format is lik this: "min-x min-y width height"
                parts = viewBox.split()
                if len(parts) == 4:
                    width = float(parts[2])
                    height = float(parts[3])
                    return width, height
            
            # try width and height 
            width_str = root.get('width', '100')
            height_str = root.get('height', '100')
            
            # remove units (px, mm)
            width = float(''.join(c for c in width_str if c.isdigit() or c == '.'))
            height = float(''.join(c for c in height_str if c.isdigit() or c == '.'))
            
            return width, height
        except Exception as e:
            print(f"Error getting SVG dimensions: {e}")
            return 100, 100  # default if there is an error size
    
    def clamp_to_boundary(self, x, y, width, height):
        # clamp to edges    
        # Calculate valid range
        min_x = self.boundary_margin
        max_x = self.canvas_width - width - self.boundary_margin
        min_y = self.boundary_margin
        max_y = self.canvas_height - height - self.boundary_margin
        
        # Clamp
        x = max(min_x, min(x, max_x))
        y = max(min_y, min(y, max_y))
        
        return x, y
    
    def set_svg(self, svg_path, callback=None):
        # used to load the dimensions
        self.svg_path = svg_path
        
        # get SVG dimensions (fast method)
        self.original_svg_width, self.original_svg_height = self.get_svg_dimensions(svg_path)
        self.svg_width = self.original_svg_width
        self.svg_height = self.original_svg_height
        
        # auto fit to canvas
        self.auto_fit()
        
        if callback:
            callback(True)
    
    def auto_fit(self):
        #fit the svg to the size of the printbed
        self.custom_scale = None  # disable custom scale
        
        # available space with boundary margin
        available_width = self.canvas_width - 2 * self.boundary_margin
        available_height = self.canvas_height - 2 * self.boundary_margin
        
        scale_x = available_width / self.svg_width if self.svg_width > 0 else 1
        scale_y = available_height / self.svg_height if self.svg_height > 0 else 1
        self.scale_factor = min(scale_x, scale_y, 2.0)
        
        self.rect_width = self.svg_width * self.scale_factor
        self.rect_height = self.svg_height * self.scale_factor
        
        # center the rectangle within the boundary
        self.rect_x = (self.canvas_width - self.rect_width) / 2
        self.rect_y = (self.canvas_height - self.rect_height) / 2
        
        # clamp to boundary
        self.rect_x, self.rect_y = self.clamp_to_boundary(
            self.rect_x, self.rect_y, self.rect_width, self.rect_height
        )
        
        self.draw_canvas()
    
    #allow user to select a custom scale factor
    def set_custom_scale(self, scale):
        self.custom_scale = scale
        self.scale_factor = scale 
        self.rect_width = self.svg_width * self.scale_factor
        self.rect_height = self.svg_height * self.scale_factor

        # check if the scaled SVG fits within the boundary
        max_width = self.canvas_width - 2 * self.boundary_margin
        max_height = self.canvas_height - 2 * self.boundary_margin
        if self.rect_width > max_width or self.rect_height > max_height:
            # scale down to fit within boundary
            scale_x = max_width / self.rect_width if self.rect_width > max_width else 1
            scale_y = max_height / self.rect_height if self.rect_height > max_height else 1
            self.scale_factor *= min(scale_x, scale_y)
            self.rect_width = self.svg_width * self.scale_factor
            self.rect_height = self.svg_height * self.scale_factor
            messagebox.showwarning("Scale Adjusted", 
                f"Scale was reduced to {self.scale_factor:.2f}x to fit within the boundary margin.")
            
        # center the scaled SVG
        self.rect_x = (self.canvas_width - self.rect_width) / 2
        self.rect_y = (self.canvas_height - self.rect_height) / 2
        
        # clamp to boundary
        self.rect_x, self.rect_y = self.clamp_to_boundary(
            self.rect_x, self.rect_y, self.rect_width, self.rect_height
        )
        
        self.draw_canvas()

    def set_custom_size(self, width, height):
        #set custom width and height of the svg(pxiels)
        if width > 0 and height > 0:
            # check if the custom size fits within the boundary
            max_width = self.canvas_width - 2 * self.boundary_margin
            max_height = self.canvas_height - 2 * self.boundary_margin
            
            if width > max_width or height > max_height:
                # scale down to fit within boundary if it doesnt fit
                scale_x = max_width / width if width > max_width else 1
                scale_y = max_height / height if height > max_height else 1
                width *= min(scale_x, scale_y)
                height *= min(scale_x, scale_y)
                messagebox.showwarning("Size Adjusted", 
                    f"Size was reduced to {width:.0f}x{height:.0f} to fit within the boundary margin.")
            
            # calculate scale based on custom size
            scale_x = width / self.original_svg_width
            scale_y = height / self.original_svg_height
            self.scale_factor = min(scale_x, scale_y)
            
            self.rect_width = self.original_svg_width * self.scale_factor
            self.rect_height = self.original_svg_height * self.scale_factor
            
            # center the scaled SVG
            self.rect_x = (self.canvas_width - self.rect_width) / 2
            self.rect_y = (self.canvas_height - self.rect_height) / 2
            
            # clamp to boundary
            self.rect_x, self.rect_y = self.clamp_to_boundary(
                self.rect_x, self.rect_y, self.rect_width, self.rect_height
            )
            
            self.custom_scale = self.scale_factor
            self.draw_canvas()
    #draw boundary lines
    def draw_boundary(self):
        # draw boundary rectangle
        self.create_rectangle(
            self.boundary_margin, self.boundary_margin,
            self.canvas_width - self.boundary_margin, self.canvas_height - self.boundary_margin,
            outline='#ff0000', 
            dash=(5, 5),
            width=1,
            tags="boundary"
        )
        
        # add label for boundary
        self.create_text(
            self.boundary_margin + 10, self.boundary_margin + 10,
            text=f"Boundary ({self.boundary_margin}px margin)",
            fill='#ff0000',
            font=('Arial', 8),
            anchor='nw',
            tags="boundary"
        )
    
    def draw_canvas(self):
        self.delete("all")
        
        # draw grid
        for x in range(0, self.canvas_width, 20):
            self.create_line(x, 0, x, self.canvas_height, fill='#e0e0e0', dash=(2, 2))
        for y in range(0, self.canvas_height, 20):
            self.create_line(0, y, self.canvas_width, y, fill='#e0e0e0', dash=(2, 2))
        
        # draw boundary margin
        self.draw_boundary()
        
        # draw SVG placeholder rectangle with label
        self.rect_id = self.create_rectangle(
            self.rect_x, self.rect_y, 
            self.rect_x + self.rect_width, self.rect_y + self.rect_height,
            outline='#0066ff', 
            fill='#0066ff', 
            stipple='gray50',
            width=2
        )
        
        # draw "SVG" label in the center
        self.create_text(
            self.rect_x + self.rect_width/2, 
            self.rect_y + self.rect_height/2,
            text="Your image will be here",
            fill='#0066ff',
            font=('Arial', 16, 'bold')
        )
        
        # draw dimensions in the center
        self.create_text(
            self.rect_x + self.rect_width/2, 
            self.rect_y + self.rect_height/2 + 25,
            text=f"{self.rect_width:.0f} x {self.rect_height:.0f} px",
            fill='#666666',
            font=('Arial', 9)
        )
        
        # draw file name if loaded
        if self.svg_path:
            name = os.path.basename(self.svg_path)
            self.create_text(
                self.rect_x + self.rect_width/2, 
                self.rect_y + self.rect_height/2 + 45,
                text=name,
                fill='#666666',
                font=('Arial', 10)
            )
        
        # draw resize handles
        handle_size = 6
        for x, y in [(self.rect_x, self.rect_y), 
                     (self.rect_x + self.rect_width, self.rect_y),
                     (self.rect_x, self.rect_y + self.rect_height),
                     (self.rect_x + self.rect_width, self.rect_y + self.rect_height)]:
            self.create_rectangle(x - handle_size/2, y - handle_size/2,
                                 x + handle_size/2, y + handle_size/2,
                                 fill='#0066ff', outline='#ffffff')
        
        # draw info text
        scale_info = f"{self.scale_factor:.2f}x"
        if self.custom_scale:
            scale_info += " (custom)"
        
        self.info_text_id = self.create_text(
            10, 30, 
            anchor='nw',
            text=f"Position: ({self.rect_x:.0f}, {self.rect_y:.0f})\n"
                 f"Size: {self.rect_width:.0f}x{self.rect_height:.0f}\n"
                 f"Scale: {scale_info}\n"
                 f"Boundary: {self.boundary_margin}px margin",
            fill='#333333',
            font=('Arial', 10)
        )
        
        # updae=te position callback if it exists
        if self.position_callback is not None:
            self.position_callback(self.rect_x, self.rect_y, self.scale_factor)
    
    def on_mouse_down(self, event):
        x, y = event.x, event.y
        
        # check if clicked inside rectangle
        if (self.rect_x <= x <= self.rect_x + self.rect_width and
            self.rect_y <= y <= self.rect_y + self.rect_height):
            self.is_dragging = True
            self.drag_start_x = x
            self.drag_start_y = y
            self.rect_start_x = self.rect_x
            self.rect_start_y = self.rect_y
            self.config(cursor='fleur')
    
    def on_mouse_drag(self, event):
        if self.is_dragging:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            new_x = self.rect_start_x + dx
            new_y = self.rect_start_y + dy
            
            # clamp to boundary margin
            new_x, new_y = self.clamp_to_boundary(
                new_x, new_y, self.rect_width, self.rect_height
            )
            
            self.rect_x = new_x
            self.rect_y = new_y
            
            self.draw_canvas()
    
    def on_mouse_up(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.config(cursor='')
            self.draw_canvas()
    
    def on_mouse_move(self, event):
        x, y = event.x, event.y
        if (self.rect_x <= x <= self.rect_x + self.rect_width and
            self.rect_y <= y <= self.rect_y + self.rect_height):
            self.config(cursor='hand2')
        else:
            self.config(cursor='')
    
    def get_slice_parameters(self):
        return {
            'xOffset': self.rect_x,
            'yOffset': self.rect_y,
            'scaleFactor': self.scale_factor
        }

class SlicerApp:
    def __init__(self, root):
        self.root = root
        root.title("2D printer slicer")
        root.geometry("1100x850")
        
        # main container
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # control panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # file controls
        file_frame = ttk.LabelFrame(control_frame, text="File", padding="5")
        file_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        self.load_btn = ttk.Button(file_frame, text="Load SVG", command=self.load_svg)
        self.load_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.file_label = ttk.Label(file_frame, text="No file loaded")
        self.file_label.pack(side=tk.LEFT)
        
        # scale controls
        scale_frame = ttk.LabelFrame(control_frame, text="Scale", padding="5")
        scale_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        # auto-fit button
        self.auto_fit_btn = ttk.Button(scale_frame, text="Auto Fit", command=self.auto_fit_svg, state='disabled')
        self.auto_fit_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # custom scale
        ttk.Label(scale_frame, text="Scale:").pack(side=tk.LEFT, padx=(5, 2))
        self.scale_var = tk.StringVar(value="1.0")
        self.scale_entry = ttk.Entry(scale_frame, textvariable=self.scale_var, width=6)
        self.scale_entry.pack(side=tk.LEFT, padx=(0, 2))
        self.scale_entry.bind('<Return>', lambda e: self.apply_custom_scale())
        self.scale_entry.bind('<FocusOut>', lambda e: self.apply_custom_scale())
        
        self.apply_scale_btn = ttk.Button(scale_frame, text="Apply", command=self.apply_custom_scale, state='disabled')
        self.apply_scale_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # custom size
        ttk.Label(scale_frame, text="Size:").pack(side=tk.LEFT, padx=(10, 2))
        self.width_var = tk.StringVar(value="")
        self.width_entry = ttk.Entry(scale_frame, textvariable=self.width_var, width=6)
        self.width_entry.pack(side=tk.LEFT, padx=(0, 2))
        ttk.Label(scale_frame, text="x").pack(side=tk.LEFT, padx=(0, 2))
        self.height_var = tk.StringVar(value="")
        self.height_entry = ttk.Entry(scale_frame, textvariable=self.height_var, width=6)
        self.height_entry.pack(side=tk.LEFT, padx=(0, 2))
        self.height_entry.bind('<Return>', lambda e: self.apply_custom_size())
        self.height_entry.bind('<FocusOut>', lambda e: self.apply_custom_size())
        
        self.apply_size_btn = ttk.Button(scale_frame, text="Apply Size", command=self.apply_custom_size, state='disabled')
        self.apply_size_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # boundary info
        ttk.Label(scale_frame, text=f"Boundary: 50px margin").pack(side=tk.LEFT, padx=(10, 0))
        
        # speed controls
        speed_frame = ttk.LabelFrame(control_frame, text="Speed", padding="5")
        speed_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(speed_frame, text="Travel:").pack(side=tk.LEFT, padx=(5, 2))
        self.travel_speed_var = tk.StringVar(value="900")
        self.travel_speed_entry = ttk.Entry(speed_frame, textvariable=self.travel_speed_var, width=6)
        self.travel_speed_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(speed_frame, text="Draw:").pack(side=tk.LEFT, padx=(5, 2))
        self.draw_speed_var = tk.StringVar(value="300")
        self.draw_speed_entry = ttk.Entry(speed_frame, textvariable=self.draw_speed_var, width=6)
        self.draw_speed_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # slice controls
        slice_frame = ttk.LabelFrame(control_frame, text="Slice", padding="5")
        slice_frame.pack(side=tk.LEFT)
        
        self.slice_btn = ttk.Button(slice_frame, text="Slice SVG", command=self.slice_svg, state='disabled')
        self.slice_btn.pack(side=tk.LEFT)
        
        # canvas
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = DraggableRectCanvas(canvas_frame)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.set_position_callback(self.update_status)
        
        # status bar(istg if the app just shows "not responding" this is gonna be genuinely useess)
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(self.status_frame, text="Ready. Load an SVG file to begin.")
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.status_frame, variable=self.progress_var, 
                                           maximum=100, length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
        self.progress_bar.pack_forget()  # hide initially
        
        self.current_svg_path = None
        
        # update status periodically
        self.update_status(self.canvas.rect_x, self.canvas.rect_y, self.canvas.scale_factor)
    
    def load_svg(self):
        file_path = filedialog.askopenfilename(
            title="Select SVG File",
            filetypes=[("SVG Files", "*.svg"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.current_svg_path = file_path
            self.file_label.config(text=os.path.basename(file_path))
            self.load_btn.config(state='disabled')
            self.slice_btn.config(state='disabled')
            self.auto_fit_btn.config(state='disabled')
            self.apply_scale_btn.config(state='disabled')
            self.apply_size_btn.config(state='disabled')
            self.status_label.config(text=f"Loading: {os.path.basename(file_path)}...")
            
            # load SVG dimensions
            self.canvas.set_svg(file_path, self._svg_loaded)
    
    def _svg_loaded(self, success):
        #callback when it is loaded
        self.load_btn.config(state='normal')
        if success:
            self.slice_btn.config(state='normal')
            self.auto_fit_btn.config(state='normal')
            self.apply_scale_btn.config(state='normal')
            self.apply_size_btn.config(state='normal')
            self.scale_var.set(f"{self.canvas.scale_factor:.2f}")
            self.width_var.set(f"{self.canvas.rect_width:.0f}")
            self.height_var.set(f"{self.canvas.rect_height:.0f}")
            self.status_label.config(text=f"Loaded: {os.path.basename(self.current_svg_path)}")
        else:
            self.slice_btn.config(state='disabled')
            self.auto_fit_btn.config(state='disabled')
            self.apply_scale_btn.config(state='disabled')
            self.apply_size_btn.config(state='disabled')
            self.status_label.config(text="Failed to load SVG")
            messagebox.showerror("Error", "Failed to load SVG file.")
    
    def auto_fit_svg(self):
        #auto fit that svg
        if self.current_svg_path:
            self.canvas.auto_fit()
            self.scale_var.set(f"{self.canvas.scale_factor:.2f}")
            self.width_var.set(f"{self.canvas.rect_width:.0f}")
            self.height_var.set(f"{self.canvas.rect_height:.0f}")
            self.status_label.config(text="Auto-fitted to canvas")
    
    def apply_custom_scale(self):
        #scales your factor
        try:
            scale = float(self.scale_var.get())
            if scale > 0:
                self.canvas.set_custom_scale(scale)
                self.width_var.set(f"{self.canvas.rect_width:.0f}")
                self.height_var.set(f"{self.canvas.rect_height:.0f}")
                self.status_label.config(text=f"Applied scale: {scale:.2f}x")
            else:
                messagebox.showwarning("Invalid Scale", "Scale must be greater than 0.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for scale.")
    
    def apply_custom_size(self):
        # apply custom settings
        try:
            width = float(self.width_var.get())
            height = float(self.height_var.get())
            if width > 0 and height > 0:
                self.canvas.set_custom_size(width, height)
                self.scale_var.set(f"{self.canvas.scale_factor:.2f}")
                self.status_label.config(text=f"Applied size: {width:.0f}x{height:.0f} px")
            else:
                messagebox.showwarning("Invalid Size", "Width and height must be greater than 0.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for width and height.")
    
    def update_status(self, x, y, scale):
        self.status_label.config(
            text=f"Position: ({x:.0f}, {y:.0f}) | Scale: {scale:.2f}x"
        )
    
    def slice_svg(self):
        if not self.current_svg_path:
            messagebox.showerror("Error", "No SVG file loaded.")
            return
        
        params = self.canvas.get_slice_parameters()
        
        try:
            travel_speed = int(self.travel_speed_var.get())
            draw_speed = int(self.draw_speed_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Speed values must be integers.")
            return
        
        # confirm dialog
        if not messagebox.askyesno(
            "Confirm Slice, this may take a while",
            f"Slice SVG with:\n"
            f"X Offset: {params['xOffset']:.0f}px\n"
            f"Y Offset: {params['yOffset']:.0f}px\n"
            f"Scale: {params['scaleFactor']:.2f}x\n"
            f"Travel Speed: {travel_speed} px/sec\n"
            f"Draw Speed: {draw_speed} px/sec\n\n"
            f"Continue?"
        ):
            return
        
        # disable controls
        self.slice_btn.config(state='disabled')
        self.load_btn.config(state='disabled')
        self.auto_fit_btn.config(state='disabled')
        self.apply_scale_btn.config(state='disabled')
        self.apply_size_btn.config(state='disabled')
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
        self.progress_var.set(0)
        self.status_label.config(text="Slicing in progress...")
        
        # run slicing in a seperate thread to prevent gui from crashing
        thread = threading.Thread(
            target=self._run_slice,
            args=(self.current_svg_path, params, travel_speed, draw_speed)
        )
        thread.daemon = True
        thread.start()
    
    def _update_progress(self, current, total):
        #update progress
        progress = (current / total) * 100
        self.root.after(0, lambda: self.progress_var.set(progress))
    
    def _run_slice(self, svg_path, params, travel_speed=900, draw_speed=300):
        try:
            # run slice with progress callback
            success = sliceYInfill(
                svg_path,
                params['xOffset'],
                params['yOffset'],
                params['scaleFactor'],
                travel_speed,
                draw_speed,
                self._update_progress
            )
            
            # update UI on completion
            self.root.after(0, self._slicing_complete, success)
            
        except Exception as e:
            self.root.after(0, self._slicing_error, str(e))
    
    def _slicing_complete(self, success):
        self.progress_bar.pack_forget()
        self.slice_btn.config(state='normal')
        self.load_btn.config(state='normal')
        self.auto_fit_btn.config(state='normal')
        self.apply_scale_btn.config(state='normal')
        self.apply_size_btn.config(state='normal')
        
        if success:
            self.status_label.config(text="Slicing complete! Output saved to slicedExport.banana")
            messagebox.showinfo(
                "Slicing Complete",
                f"Slicing completed successfully!\n"
                f"Output saved to: slicedExport.banana"
            )
            subprocess.run(["explorer", "/select,", os.path.dirname(os.path.abspath(__file__))])
        else:
            self.status_label.config(text="Slicing failed")
            messagebox.showerror("Error", "Slicing failed.")
    
    def _slicing_error(self, error_msg):
        self.progress_bar.pack_forget()
        self.slice_btn.config(state='normal')
        self.load_btn.config(state='normal')
        self.auto_fit_btn.config(state='normal')
        self.apply_scale_btn.config(state='normal')
        self.apply_size_btn.config(state='normal')
        self.status_label.config(text=f"Error: {error_msg}")
        messagebox.showerror("Error", f"Error during slicing:\n{error_msg}")

def main():
    root = tk.Tk()
    app = SlicerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
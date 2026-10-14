import os
import threading
import tkinter as tk
from PIL import Image, ImageTk
import customtkinter as ctk


class NoteCard(ctk.CTkFrame):
    """A sleek, modern note card widget featuring glassmorphism accents, threaded AI, and responsive layout."""

    def __init__(self, master, initial_text="", title="Study Note", width=340, height=260):
        super().__init__(
            master,
            width=width,
            height=height,
            corner_radius=12,
            border_width=1,
            fg_color="#1e1e24",
            border_color="#334155",
        )

        self.title_text = title
        self.current_width = width   # Track current dimensions
        self.current_height = height
        self.original_height = height

        # Hover accent feedback
        self.bind("<Enter>", lambda e: self.configure(border_color="#3b82f6"))
        self.bind("<Leave>", lambda e: self.configure(border_color="#334155"))

        # --- 1. Header (Packed top) ---
        self.header = ctk.CTkFrame(self, height=36, corner_radius=0, fg_color="transparent")
        self.header.pack(fill="x", padx=8, pady=(8, 4), side="top")

        self.tag_label = ctk.CTkLabel(
            self.header,
            text="NOTE",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#60a5fa",
            fg_color="#1e293b",
            corner_radius=4,
            width=42,
            height=18,
        )
        self.tag_label.pack(side="left", padx=(4, 6))

        self.title_label = ctk.CTkLabel(
            self.header,
            text=self.title_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f1f5f9",
            anchor="w",
        )
        self.title_label.pack(side="left", padx=2, fill="x", expand=True)

        self.title_entry = ctk.CTkEntry(
            self.header,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=26,
            fg_color="#0f172a",
            border_color="#3b82f6",
            text_color="#f8fafc",
            corner_radius=6,
        )
        self.title_label.bind("<Double-Button-1>", self.enable_title_edit)
        self.title_entry.bind("<Return>", self.save_title_edit)
        self.title_entry.bind("<FocusOut>", self.save_title_edit)

        self.close_btn = ctk.CTkButton(
            self.header,
            text="✕",
            width=22,
            height=22,
            corner_radius=11,
            fg_color="transparent",
            hover_color="#ef4444",
            text_color="#94a3b8",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.destroy_card,
        )
        self.close_btn.pack(side="right", padx=2)

        # --- 2. Footer (Packed bottom FIRST with propagate(False)) ---
        self.footer = ctk.CTkFrame(self, fg_color="transparent", height=36)
        self.footer.pack(fill="x", padx=10, pady=(2, 8), side="bottom")
        self.footer.pack_propagate(False)

        self.resize_grip = ctk.CTkLabel(
            self.footer,
            text="◢",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#64748b",
            cursor="sizing",
        )
        self.resize_grip.pack(side="right", padx=2)
        self.resize_grip.bind("<Button-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.do_resize)
       

        self.copy_btn = ctk.CTkButton(
            self.footer,
            text="📋",
            width=28,
            height=26,
            corner_radius=6,
            fg_color="#0f172a",
            hover_color="#334155",
            text_color="#94a3b8",
            command=self.copy_to_clipboard,
        )
        self.copy_btn.pack(side="right", padx=4)

        self.ai_btn = ctk.CTkButton(
            self.footer,
            text="✨ AI",
            font=ctk.CTkFont(size=11, weight="bold"),
            width=65,
            height=26,
            corner_radius=6,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            text_color="white",
            command=self.trigger_ai_summary,
        )
        self.ai_btn.pack(side="left", padx=2)

        # --- 3. Text Input Area ---
        self.text_box = ctk.CTkTextbox(
            self,
            corner_radius=8,
            fg_color="#0f172a",
            text_color="#e2e8f0",
            border_width=1,
            border_color="#1e293b",
            font=ctk.CTkFont(family="Consolas" if os.name == "nt" else "Monaco", size=12),
        )
        self.text_box.pack(padx=10, pady=4, fill="both", expand=True, side="top")
        if initial_text:
            self.text_box.insert("1.0", initial_text)

    def enable_title_edit(self, event=None):
        self.title_label.pack_forget()
        self.title_entry.pack(side="left", padx=2, fill="x", expand=True)
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, self.title_text)
        self.title_entry.focus_set()
        self.title_entry.select_range(0, "end")

    def save_title_edit(self, event=None):
        new_text = self.title_entry.get().strip()
        if new_text:
            self.title_text = new_text
        self.title_label.configure(text=self.title_text)
        self.title_entry.pack_forget()
        self.title_label.pack(side="left", padx=2, fill="x", expand=True)
        try:
            app_root = self.winfo_toplevel()
            if hasattr(app_root, "update_minimap"):
                app_root.update_minimap()
        except Exception:
            pass

    def copy_to_clipboard(self):
        content = self.text_box.get("1.0", "end").strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)
            self.copy_btn.configure(text="✓")
            self.after(1200, lambda: self.copy_btn.configure(text="📋"))

    def start_resize(self, event):
        self.resize_start_x = event.x_root
        self.resize_start_y = event.y_root
        self.start_width = self.winfo_width()
        self.start_height = self.winfo_height()
        

    def do_resize(self, event):
        dx = event.x_root - self.resize_start_x
        dy = event.y_root - self.resize_start_y
        
        new_w = max(340, self.start_width + dx)
        new_h = max(220, self.start_height + dy)
        self.current_width = new_w   # Update tracked dimensions
        self.current_height = new_h
        self.original_height = new_h
        
        self.configure(width=new_w, height=new_h)
        self.update_canvas_window_size(new_w, new_h)

        # ---> Trigger save immediately during live dragging <---
        try:
            app_root = self.winfo_toplevel()
            if hasattr(app_root, "save_current_workspace_state"):
                app_root.save_current_workspace_state()
        except Exception:
            pass

    def update_canvas_window_size(self, w, h):
        canvas = self.master
        if isinstance(canvas, tk.Canvas):
            for item in canvas.find_all():
                if canvas.itemcget(item, "window") == str(self):
                    canvas.itemconfig(item, width=w, height=h)
                    break
        try:
            app_root = self.winfo_toplevel()
            if hasattr(app_root, "update_minimap"):
                app_root.update_minimap()
        except Exception:
            pass

    def destroy_card(self):
        master_canvas = self.master
        if isinstance(master_canvas, tk.Canvas):
            for item in master_canvas.find_all():
                if master_canvas.itemcget(item, "window") == str(self):
                    master_canvas.delete(item)
                    break
        try:
            app_root = self.winfo_toplevel()
            if hasattr(app_root, "update_minimap"):
                app_root.update_minimap()
            if hasattr(app_root, "save_current_workspace_state"):
                app_root.save_current_workspace_state()
        except Exception:
            pass
        self.destroy()

    def trigger_ai_summary(self):
        content = self.text_box.get("1.0", "end").strip()
        if not content:
            return

        self.ai_btn.configure(text="...", state="disabled")
        
        def run_ai():
            app_root = self.winfo_toplevel()
            summary_text = app_root.call_gemini(content) if hasattr(app_root, "call_gemini") else "AI Error"
            self.after(0, lambda: self.finish_ai_summary(summary_text))

        threading.Thread(target=run_ai, daemon=True).start()

    def finish_ai_summary(self, summary_text):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        self.ai_btn.configure(text="✨ AI", state="normal")
        canvas = self.master
        if isinstance(canvas, tk.Canvas):
            for item in canvas.find_all():
                if canvas.itemcget(item, "window") == str(self):
                    coords = canvas.coords(item)
                    if coords:
                        canvas_x = canvas.canvasx(coords[0])
                        canvas_y = canvas.canvasy(coords[1])
                        current_w = self.winfo_width()
                        try:
                            app_root = self.winfo_toplevel()
                            app_root.spawn_note_at(
                                canvas_x + current_w + 10, canvas_y, summary_text, f"Summary: {self.title_text}"
                            )
                        except Exception:
                            pass
                    break

    def set_detail_level(self, detailed=True):
        if detailed:
            if hasattr(self, "text_box") and self.text_box:
                self.text_box.pack(padx=12, pady=(0, 10), fill="both", expand=True, side="top")
            
            # Standard default dimensions for all note cards
            std_w, std_h = 340, 260
            self.current_width = std_w
            self.current_height = std_h
            #self.original_height = std_h
            
            self.configure(width=std_w, height=std_h)
            self.update_canvas_window_size(std_w, std_h)
        else:
            if self.winfo_height() > 100:
                self.original_height = self.winfo_height()
            if hasattr(self, "text_box") and self.text_box:
                self.text_box.pack_forget()
            
            compact_h = 75
            current_w = self.winfo_width()
            self.configure(height=compact_h)
            self.update_canvas_window_size(current_w, compact_h)


class FileNoteCard(ctk.CTkFrame):
    """A sleek card specialized for rendering attached image/PDF preview cards directly on the canvas workspace."""

    def __init__(self, master, file_path, width=360, height=360):
        super().__init__(
            master,
            width=width,
            height=height,
            corner_radius=12,
            border_width=1,
            fg_color="#1e1e24",
            border_color="#334155",
        )
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.is_pdf = self.file_name.lower().endswith(".pdf")
        self.current_width = width
        self.current_height = height
        self.original_height = height

        # Hover accent feedback
        self.bind("<Enter>", lambda e: self.configure(border_color="#3b82f6"))
        self.bind("<Leave>", lambda e: self.configure(border_color="#334155"))

        # --- 1. Header ---
        self.header = ctk.CTkFrame(self, height=36, corner_radius=0, fg_color="transparent")
        self.header.pack(fill="x", padx=8, pady=(8, 4), side="top")

        tag_bg = "#312e81" if self.is_pdf else "#064e3b"
        tag_color = "#a5b4fc" if self.is_pdf else "#6ee7b7"
        tag_label_text = "PDF" if self.is_pdf else "IMAGE"

        self.tag_label = ctk.CTkLabel(
            self.header,
            text=tag_label_text,
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=tag_color,
            fg_color=tag_bg,
            corner_radius=4,
            width=42,
            height=18,
        )
        self.tag_label.pack(side="left", padx=(4, 6))

        self.title_label = ctk.CTkLabel(
            self.header,
            text=self.file_name,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f1f5f9",
            anchor="w",
        )
        self.title_label.pack(side="left", padx=2, fill="x", expand=True)

        self.close_btn = ctk.CTkButton(
            self.header,
            text="✕",
            width=22,
            height=22,
            corner_radius=11,
            fg_color="transparent",
            hover_color="#ef4444",
            text_color="#94a3b8",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.destroy_card,
        )
        self.close_btn.pack(side="right", padx=2)

        # --- 2. Footer (Locked with pack_propagate so it NEVER gets covered) ---
        self.footer = ctk.CTkFrame(self, fg_color="transparent", height=36)
        self.footer.pack(fill="x", padx=10, pady=(2, 8), side="bottom")
        self.footer.pack_propagate(False)

        self.resize_grip = ctk.CTkLabel(
            self.footer,
            text="◢",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#64748b",
            cursor="sizing",
        )
        self.resize_grip.pack(side="right", padx=2)
        self.resize_grip.bind("<Button-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.do_resize)
        

        # --- 3. Content Area (Packed AFTER footer so it stays cleanly above it) ---
        if self.is_pdf:
            self.setup_pdf_preview()
        else:
            self.setup_image_display()

    

    def setup_image_display(self):
        self.content_frame = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=8)
        self.content_frame.pack(padx=10, pady=4, fill="both", expand=True, side="top")
        
        self.display_canvas = tk.Canvas(self.content_frame, bg="#0f172a", highlightthickness=0)
        self.display_canvas.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Bind to canvas configuration changes to auto-scale image on resize
        self.display_canvas.bind("<Configure>", self.on_canvas_configure)
        
        try:
            self.pil_image = Image.open(self.file_path)
            self.render_scaled_image()
        except Exception as e:
            ctk.CTkLabel(self.content_frame, text=f"Error loading image: {str(e)}", text_color="#f87171").pack(expand=True)

    def setup_pdf_preview(self):
        self.content_frame = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=8)
        self.content_frame.pack(padx=10, pady=4, fill="both", expand=True, side="top")

        ctk.CTkLabel(
            self.content_frame,
            text="📄 PDF DOCUMENT",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#a5b4fc",
        ).pack(pady=(35, 5))

        ctk.CTkLabel(
            self.content_frame,
            text=f"{self.file_name}",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
        ).pack(pady=2)

        ctk.CTkButton(
            self.content_frame,
            text="Open PDF Externally ↗",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#312e81",
            hover_color="#3730a3",
            text_color="#e0e7ff",
            height=28,
            corner_radius=6,
            command=self.open_pdf_external,
        ).pack(pady=(20, 20))

    def render_scaled_image(self):
        if not hasattr(self, "pil_image"):
            return
            
        canvas_w = self.display_canvas.winfo_width()
        canvas_h = self.display_canvas.winfo_height()
        
        # Fallbacks if canvas hasn't drawn yet
        if canvas_w < 10 or canvas_h < 10:
            return

        pil_w, pil_h = self.pil_image.size
        
        # Option A: Scale to fill entire canvas (may crop edges)
        # Option B: Scale to fit inside canvas preserving aspect ratio
        # Let's use aspect-fit so the full image remains visible:
        ratio = min(canvas_w / pil_w, canvas_h / pil_h)
        new_w = max(1, int(pil_w * ratio))
        new_h = max(1, int(pil_h * ratio))

        resized_img = self.pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_img)
        
        self.display_canvas.delete("all")
        # Center the image inside the canvas
        pos_x = (canvas_w - new_w) // 2
        pos_y = (canvas_h - new_h) // 2
        self.display_canvas.create_image(pos_x, pos_y, image=self.tk_image, anchor="nw")

    def on_canvas_configure(self, event):
        # Trigger redraw when the frame/canvas is resized
        self.render_scaled_image()

    def open_pdf_external(self):
        import subprocess, sys
        if sys.platform == "win32":
            os.startfile(self.file_path)
        elif sys.platform == "darwin":
            subprocess.call(["open", self.file_path])
        else:
            subprocess.call(["xdg-open", self.file_path])

    def start_resize(self, event):
        self.resize_start_x = event.x_root
        self.resize_start_y = event.y_root
        self.start_width = self.winfo_width()
        self.start_height = self.winfo_height()
        

    def do_resize(self, event):
        dx = event.x_root - self.resize_start_x
        dy = event.y_root - self.resize_start_y
        
        new_w = max(340, self.start_width + dx)
        new_h = max(200, self.start_height + dy)  # Minimum height floor
        self.current_width = new_w   # Update tracked dimensions
        self.current_height = new_h

        if new_h >= 200:
            self.original_height = new_h
            if hasattr(self, "content_frame") and self.content_frame:
                if not self.content_frame.winfo_ismapped():
                    # Pack without 'after=self.header' to respect bottom footer placement
                    self.content_frame.pack(padx=10, pady=4, fill="both", expand=True, side="top")
        else:
            if hasattr(self, "content_frame") and self.content_frame:
                self.content_frame.pack_forget()
        
        self.configure(width=new_w, height=new_h)
        self.update_canvas_window_size(new_w, new_h)

        # ---> Trigger save immediately during live dragging <---
        try:
            app_root = self.winfo_toplevel()
            if hasattr(app_root, "save_current_workspace_state"):
                app_root.save_current_workspace_state()
        except Exception:
            pass


    def update_canvas_window_size(self, w, h):
        canvas = self.master
        if isinstance(canvas, tk.Canvas):
            for item in canvas.find_all():
                if canvas.itemcget(item, "window") == str(self):
                    canvas.itemconfig(item, width=w, height=h)
                    break
        try:
            app_root = self.winfo_toplevel()
            if hasattr(app_root, "update_minimap"):
                app_root.update_minimap()
        except Exception:
            pass

    def destroy_card(self):
        master_canvas = self.master
        if isinstance(master_canvas, tk.Canvas):
            for item in master_canvas.find_all():
                if master_canvas.itemcget(item, "window") == str(self):
                    master_canvas.delete(item)
                    break
        
        try:
            app_root = self.winfo_toplevel()
            if hasattr(app_root, "update_minimap"):
                app_root.update_minimap()
            if hasattr(app_root, "save_current_workspace_state"):
                app_root.save_current_workspace_state()
        except Exception:
            pass
            
        self.destroy()

    def set_detail_level(self, detailed=True):
        if detailed:
            if hasattr(self, "content_frame") and self.content_frame:
                if not self.content_frame.winfo_ismapped():
                    self.content_frame.pack(padx=10, pady=4, fill="both", expand=True, side="top")
            
            # Standard default dimensions for all cards when zooming back in
            std_w, std_h = 360, 360
            self.current_width = std_w
            self.current_height = std_h
            #self.original_width = std_w
            #self.original_height = std_h
            
            self.configure(width=std_w, height=std_h)
            self.update_canvas_window_size(std_w, std_h)
        else:
            # Capture the current width first before any packing changes happen
            current_w = self.winfo_width()
            
            if self.winfo_height() > 100:
                self.original_height = self.winfo_height()
                
            if hasattr(self, "content_frame") and self.content_frame:
                self.content_frame.pack_forget()
            
            compact_h = 85
            # Keep current width as-is, only update height to compact view
            self.configure(width=current_w, height=compact_h)
            self.update_canvas_window_size(current_w, compact_h)
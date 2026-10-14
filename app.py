import os
import sys
import json
import tkinter as tk
from tkinter import filedialog
from dotenv import load_dotenv
from google import genai
from google.genai import types
import customtkinter as ctk

from cards import NoteCard, FileNoteCard

load_dotenv()

try:
    ai_client = genai.Client()
except Exception as e:
    ai_client = None
    print(
        "Warning: Gemini client failed to initialize. Check GEMINI_API_KEY env"
        " variable."
    )

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

STORAGE_FILE = "declutter_workspaces.json"


class WorkspaceDialog(ctk.CTkToplevel):
    """A sleek, custom modal dialog for creating or renaming workspaces."""

    def __init__(self, parent, title="New Workspace", initial_text=""):
        super().__init__(parent)
        self.title(title)
        self.geometry("380x200")
        self.resizable(False, False)
        self.configure(fg_color="#18181b")
        
        # Make modal foreground
        self.transient(parent)
        self.grab_set()

        self.result = None

        # Dialog Header
        self.label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#f8fafc",
        )
        self.label.pack(padx=20, pady=(20, 10), anchor="w")

        # Input Entry
        self.entry = ctk.CTkEntry(
            self,
            height=36,
            font=ctk.CTkFont(size=13),
            fg_color="#0f172a",
            border_color="#334155",
            text_color="#f8fafc",
            corner_radius=8,
        )
        self.entry.pack(padx=20, pady=(5, 15), fill="x")
        if initial_text:
            self.entry.insert(0, initial_text)
            self.entry.select_range(0, "end")
        self.entry.focus_set()
        self.entry.bind("<Return>", lambda e: self.on_submit())

        # Button Row
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=20, pady=(0, 20), fill="x")

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="#27272a",
            hover_color="#3f3f46",
            text_color="#cbd5e1",
            height=32,
            command=self.destroy,
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        submit_btn = ctk.CTkButton(
            btn_frame,
            text="Confirm",
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            text_color="#ffffff",
            height=32,
            command=self.on_submit,
        )
        submit_btn.pack(side="right")

    def on_submit(self):
        val = self.entry.get().strip()
        if val:
            self.result = val
            self.destroy()


class NotionCanvasApp(ctk.CTk):
    """Main application workspace featuring a sidebar, workspace management, local JSON storage"""

    def __init__(self):
        super().__init__()

        self.title("DeclutterMind - AI Canvas Workspace")
        self.geometry("1200x700")

        self.zoom_scale = 1.0
        self.workspaces = {}
        self.current_workspace = "Default Workspace"

        self._drag_data = {"x": 0, "y": 0, "item": None}
        
        
        self.load_storage()

        # --- Layout Grid ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Left Sidebar
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#18181b")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Sidebar Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="⚡ DeclutterMind",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f8fafc",
        )
        self.logo_label.pack(padx=20, pady=(25, 15), anchor="w")

        # New Workspace Button
        self.new_ws_btn = ctk.CTkButton(
            self.sidebar,
            text="+ New Workspace",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            height=36,
            corner_radius=8,
            command=self.prompt_new_workspace,
        )
        self.new_ws_btn.pack(padx=15, pady=(0, 15), fill="x")

        # Workspace List Header
        self.ws_header = ctk.CTkLabel(
            self.sidebar,
            text="WORKSPACES",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#64748b",
        )
        self.ws_header.pack(padx=20, pady=(5, 5), anchor="w")

        # Scrollable Frame for Workspace Items
        self.ws_scroll_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent", height=500)
        self.ws_scroll_frame.pack(padx=5, pady=0, fill="both", expand=True)

        # 2. Main Workspace Area
        self.main_content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew")

        # Top Control Bar
        self.toolbar = ctk.CTkFrame(self.main_content, height=50, corner_radius=0, fg_color="#1e1e24")
        self.toolbar.pack(fill="x", side="top")

        self.add_note_btn = ctk.CTkButton(
            self.toolbar,
            text="+ New Note",
            height=30,
            command=lambda: self.spawn_note_at(self.canvas.canvasx(100), self.canvas.canvasy(100), "", "New Note Block"),
        )
        self.add_note_btn.pack(side="left", padx=15, pady=10)

        self.add_file_btn = ctk.CTkButton(
            self.toolbar,
            text="📎 New File Card",
            fg_color="#334155",
            hover_color="#475569",
            height=30,
            command=self.spawn_file_card,
        )
        self.add_file_btn.pack(side="left", padx=5)

        self.info_label = ctk.CTkLabel(
            self.toolbar,
            text="Tip: Drag background to pan • Ctrl + Scroll to zoom",
            text_color="#94a3b8",
            font=ctk.CTkFont(size=11),
        )
        self.info_label.pack(side="left", padx=15)

        # Infinite Canvas Container
        self.workspace_frame = ctk.CTkFrame(self.main_content, corner_radius=0)
        self.workspace_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            self.workspace_frame,
            bg="#121215",
            highlightthickness=0,
            scrollregion=(-10000, -10000, 10000, 10000)
        )
        self.canvas.pack(fill="both", expand=True)

        # Screen-Locked Minimap HUD
        self.minimap = tk.Canvas(
            self.workspace_frame,
            width=220,
            height=150,
            bg="#0f172a",
            highlightthickness=1,
            highlightbackground="#334155",
            cursor="hand2"
        )
        self.minimap.place(relx=1.0, x=-235, y=15)

        # Bindings
        self.canvas.bind("<ButtonPress-1>", self.start_canvas_pan)
        self.canvas.bind("<B1-Motion>", self.do_canvas_pan)
        self.canvas.bind("<ButtonPress-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.do_pan)
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.do_pan)

        if sys.platform == "darwin":
            self.canvas.bind("<MouseWheel>", self.zoom_canvas_mac)
        else:
            self.canvas.bind("<MouseWheel>", self.zoom_canvas_pc)
            self.canvas.bind("<Button-4>", self.zoom_canvas_linux_up)
            self.canvas.bind("<Button-5>", self.zoom_canvas_linux_down)

        self.minimap.bind("<Button-1>", self.jump_to_minimap_location)


        self.refresh_sidebar()
        self.load_workspace(self.current_workspace)
        
       
        
    # --- Local Storage Handlers ---
    def load_storage(self):
        if os.path.exists(STORAGE_FILE):
            try:
                with open(STORAGE_FILE, "r") as f:
                    data = json.load(f)
                    self.workspaces = data.get("workspaces", {})
                    self.current_workspace = data.get("active_workspace", "Default Workspace")
            except Exception:
                pass
        
        if not self.workspaces:
            self.workspaces = {
                "Default Workspace": [
                    {
                        "type": "note",
                        "x": 100,
                        "y": 100,
                        "width": 700,
                        "height": 600,
                        "title": "💡 Welcome to DeclutterMind",
                        "content": "Workspaces are automatically saved locally. Drag the canvas to pan, and use Ctrl + Scroll to zoom in and out."
                    },
                    {
                        "type": "note",
                        "x": 880,
                        "y": 100,
                        "width": 700,
                        "height": 600,
                        "title": "✨ AI Summarization",
                        "content": "Type notes here and click the AI button in the footer to synthesize your thoughts instantly."
                    }
                ]
            }

    def save_storage(self):
        data = {
            "active_workspace": self.current_workspace,
            "workspaces": self.workspaces
        }
        try:
            with open(STORAGE_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving storage: {e}")

    def save_current_workspace_state(self):
        self.update_idletasks()
        cards_data = []
        print("--- Saving Workspace State ---")

        for item in self.canvas.find_all():
            tags = self.canvas.gettags(item)
            print(f"Canvas Item {item} tags: {tags}")
            if "draggable" in tags:
                coords = self.canvas.coords(item)
                win_widget = self.canvas.itemcget(item, "window")
                if win_widget and len(coords) >= 2:
                    try:
                        card_obj = self.nametowidget(win_widget)
                        w = card_obj.winfo_width()
                        h = card_obj.winfo_height()
                        print(f"Found card widget type: {type(card_obj)}")
           
                        if isinstance(card_obj, NoteCard):
                            cards_data.append({
                                "type": "note",
                                "x": coords[0], "y": coords[1],
                                "width": getattr(card_obj, "current_width", 340),
                                "height": getattr(card_obj, "current_height", 260),
                                "title": card_obj.title_text,
                                "content": card_obj.text_box.get("1.0", "end").strip()
                            })
                        elif isinstance(card_obj, FileNoteCard):
                            cards_data.append({
                                "type": "file",
                                "x": coords[0], "y": coords[1],
                                "width": getattr(card_obj, "current_width", 360),
                                "height": getattr(card_obj, "current_height", 360),
                                "file_path": card_obj.file_path
                            })
                            print(f"Successfully saved FileNoteCard: {card_obj.file_path}")
                    except Exception as e:
                        print(f"Error inspecting card: {e}")
                        
        self.workspaces[self.current_workspace] = cards_data
        self.save_storage()
        print(f"Saved {len(cards_data)} cards to storage.")

    # --- Workspace Navigation & Management ---
    def refresh_sidebar(self):
        for widget in self.ws_scroll_frame.winfo_children():
            widget.destroy()

        for ws_name in self.workspaces.keys():
            is_active = (ws_name == self.current_workspace)
            
            row_frame = ctk.CTkFrame(
                self.ws_scroll_frame,
                fg_color="#3b82f6" if is_active else "transparent",
                corner_radius=6,
                height=36
            )
            row_frame.pack(fill="x", pady=2)
            row_frame.pack_propagate(False)

            # Delete Button (Only shows if more than 1 workspace exists)
            if len(self.workspaces) > 1:
                delete_btn = ctk.CTkButton(
                    row_frame,
                    text="✕",
                    width=26,
                    height=26,
                    corner_radius=4,
                    fg_color="transparent",
                    hover_color="#ef4444",
                    text_color="#f87171" if is_active else "#94a3b8",
                    command=lambda name=ws_name: self.prompt_delete_workspace(name)
                )
                delete_btn.pack(side="right", padx=(0, 6))

            # Workspace Select Button (Takes remaining space)
            ws_btn = ctk.CTkButton(
                row_frame,
                text=ws_name,
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold" if is_active else "normal"),
                fg_color="transparent",
                hover_color="#2563eb" if is_active else "#27272a",
                text_color="#ffffff" if is_active else "#cbd5e1",
                height=32,
                command=lambda name=ws_name: self.switch_workspace(name)
            )
            ws_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

            # Double-click anywhere on the workspace tab to rename
            ws_btn.bind("<Double-Button-1>", lambda event, name=ws_name: self.prompt_rename_workspace(name))
            
    def switch_workspace(self, ws_name):
        if ws_name == self.current_workspace:
            return
        
        # Pause canvas rendering updates to prevent mid-load flickering
        self.canvas.config(state="disabled")
        
        self.save_current_workspace_state()
        self.current_workspace = ws_name
        self.save_storage()
        self.load_workspace(ws_name)
        self.refresh_sidebar()
        self.canvas.config(state="normal")

    def prompt_new_workspace(self):
        dialog = WorkspaceDialog(self, title="Create New Workspace")
        self.wait_window(dialog)
        if dialog.result:
            ws_name = dialog.result
            if ws_name not in self.workspaces:
                self.save_current_workspace_state()
                self.current_workspace = ws_name
                
                # Define default tutorial onboarding cards for every new workspace
                self.workspaces[ws_name] = [
                    {
                        "type": "note",
                        "x": 100,
                        "y": 100,
                        "width": 700,
                        "height": 600,
                        "title": "💡 Welcome to Your Workspace",
                        "content": "This is your infinite canvas workspace. You can drag cards around by their headers, resize them using the bottom-right corner grip, and edit titles with a double-click."
                    },
                    {
                        "type": "note",
                        "x": 880,
                        "y": 100,
                        "width": 700,
                        "height": 600,
                        "title": "✨ AI Summarization",
                        "content": "Type or paste your study notes here, then click the AI button in the footer to instantly generate a clean summary block spawned right beside your card."
                    }
                ]
                
                self.save_storage()
                self.load_workspace(ws_name)
                self.refresh_sidebar()

    def prompt_rename_workspace(self, old_name):
        dialog = WorkspaceDialog(self, title=f"Rename '{old_name}'", initial_text=old_name)
        self.wait_window(dialog)
        if dialog.result:
            new_name = dialog.result
            if new_name and new_name not in self.workspaces:
                self.workspaces[new_name] = self.workspaces.pop(old_name)
                if self.current_workspace == old_name:
                    self.current_workspace = new_name
                self.save_storage()
                self.refresh_sidebar()

    def prompt_delete_workspace(self, ws_name):
        if len(self.workspaces) <= 1:
            return
        
        # Simple confirmation before dropping workspace
        confirm_dialog = WorkspaceDialog(self, title=f"Delete '{ws_name}'? (Type name to confirm)")
        self.wait_window(confirm_dialog)
        if confirm_dialog.result == ws_name:
            del self.workspaces[ws_name]
            if self.current_workspace == ws_name:
                self.current_workspace = list(self.workspaces.keys())[0]
            self.save_storage()
            self.load_workspace(self.current_workspace)
            self.refresh_sidebar()

    def load_workspace(self, ws_name):
        
        # Disable redrawing updates temporarily
        self.update_idletasks()
        
        for item in self.canvas.find_all():
            win_widget = self.canvas.itemcget(item, "window")
            if win_widget:
                try:
                    self.nametowidget(win_widget).destroy()
                except Exception:
                    pass
            self.canvas.delete(item)

        cards_data = self.workspaces.get(ws_name, [])
        for data in cards_data:
            if data["type"] == "note":
                self.spawn_note_at(
                    data["x"], data["y"],
                    initial_text=data.get("content", ""),
                    title=data.get("title", "Study Note"),
                    width=data.get("width", 340),
                    height=data.get("height", 260)
                )
            elif data["type"] == "file":
                if os.path.exists(data.get("file_path", "")):
                    self.spawn_file_card_at(
                        data["x"], data["y"],
                        file_path=data["file_path"],
                        width=data.get("width", 360),
                        height=data.get("height", 360)
                    )
        
        # Force a single clean redraw frame at the end
        self.update_idletasks()
        self.update_minimap()
        

    # --- Canvas & Card Spawning ---
    def start_canvas_pan(self, event):
        if event.widget == self.canvas:
            self.canvas.scan_mark(event.x, event.y)
            self._is_panning = True
        else:
            self._is_panning = False

    def do_canvas_pan(self, event):
        if getattr(self, "_is_panning", False):
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            self.update_minimap()

    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.update_minimap()

    def zoom_canvas_pc(self, event):
        if event.state & 0x0004:
            factor = 1.1 if event.delta > 0 else 0.9
            self.apply_zoom(factor, event.x, event.y)
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def zoom_canvas_mac(self, event):
        factor = 1.05 if event.delta > 0 else 0.95
        self.apply_zoom(factor, event.x, event.y)

    def zoom_canvas_linux_up(self, event):
        self.apply_zoom(1.1, event.x, event.y)

    def zoom_canvas_linux_down(self, event):
        self.apply_zoom(0.9, event.x, event.y)

    def apply_zoom(self, factor, x, y):
        if self.zoom_scale * factor < 0.2 or self.zoom_scale * factor > 3.0:
            return
        
        old_scale = self.zoom_scale
        self.zoom_scale *= factor
        
        cx = self.canvas.canvasx(x)
        cy = self.canvas.canvasy(y)
        self.canvas.scale("all", cx, cy, factor, factor)
        
        # --- Level of Detail (LOD) Threshold Check ---
        # If zooming out past 0.7, hide card body text to show only headers (topics view)
        # If zooming back in above 0.7, restore full card details
        if old_scale >= 0.7 and self.zoom_scale < 0.7:
            self.toggle_cards_lod(detailed=False)
        elif old_scale < 0.7 and self.zoom_scale >= 0.7:
            self.toggle_cards_lod(detailed=True)

        bbox = self.canvas.bbox("all")
        if bbox:
            pad = 5000
            self.canvas.configure(scrollregion=(bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad))
        else:
            self.canvas.configure(scrollregion=(-20000, -20000, 20000, 20000))
            
        self.update_minimap()

    def toggle_cards_lod(self, detailed=True):
        for item in self.canvas.find_all():
            win_widget = self.canvas.itemcget(item, "window")
            if win_widget:
                try:
                    card_obj = self.nametowidget(win_widget)
                    if isinstance(card_obj, (NoteCard, FileNoteCard)):
                        card_obj.set_detail_level(detailed=detailed)
                except Exception:
                    pass

    def jump_to_minimap_location(self, event):
        map_w, map_h = 220, 150
        
        # Get current active scroll region bounds
        sr = self.canvas.cget("scrollregion")
        if sr:
            sr_coords = [float(val) for val in sr.split()]
            min_x, min_y, max_x, max_y = sr_coords
        else:
            min_x, min_y, max_x, max_y = -10000, -10000, 10000, 10000

        world_w = max_x - min_x
        world_h = max_y - min_y

        # Map click position relative to current scroll region
        clicked_world_x = min_x + (event.x / map_w) * world_w
        clicked_world_y = min_y + (event.y / map_h) * world_h

        v_width = self.canvas.winfo_width() / self.zoom_scale
        v_height = self.canvas.winfo_height() / self.zoom_scale
        
        target_world_x = clicked_world_x - (v_width / 2)
        target_world_y = clicked_world_y - (v_height / 2)

        fraction_x = (target_world_x - min_x) / world_w
        fraction_y = (target_world_y - min_y) / world_h

        self.canvas.xview_moveto(max(0.0, min(1.0, fraction_x)))
        self.canvas.yview_moveto(max(0.0, min(1.0, fraction_y)))
        self.update_minimap()

    def update_minimap(self):
        self.minimap.delete("all")
        map_w, map_h = 220, 150
        
        sr = self.canvas.cget("scrollregion")
        if sr:
            sr_coords = [float(val) for val in sr.split()]
            min_x, min_y, max_x, max_y = sr_coords
        else:
            min_x, min_y, max_x, max_y = -10000, -10000, 10000, 10000

        world_w = max_x - min_x
        world_h = max_y - min_y
        
        scale_x = map_w / world_w if world_w > 0 else 1
        scale_y = map_h / world_h if world_h > 0 else 1

        for item in self.canvas.find_all():
            tags = self.canvas.gettags(item)
            if "draggable" in tags:
                coords = self.canvas.coords(item)
                if len(coords) >= 2:
                    win_widget = self.canvas.itemcget(item, "window")
                    if win_widget:
                        try:
                            card_obj = self.nametowidget(win_widget)
                            cw = card_obj.winfo_width() / self.zoom_scale
                            ch = card_obj.winfo_height() / self.zoom_scale
                        except Exception:
                            cw, ch = 340, 260

                        cx = (coords[0] - min_x) * scale_x
                        cy = (coords[1] - min_y) * scale_y
                        self.minimap.create_rectangle(
                            cx, cy, cx + (cw * scale_x), cy + (ch * scale_y),
                            fill="#3b82f6", outline="#93c5fd", width=1
                        )

        x_view = self.canvas.canvasx(0)
        y_view = self.canvas.canvasy(0)
        v_width = self.canvas.winfo_width() / self.zoom_scale
        v_height = self.canvas.winfo_height() / self.zoom_scale

        vx = (x_view - min_x) * scale_x
        vy = (y_view - min_y) * scale_y
        vw = v_width * scale_x
        vh = v_height * scale_y

        self.minimap.create_rectangle(vx, vy, vx + vw, vy + vh, outline="#ef4444", width=2)

    def call_gemini(self, text):
        if not ai_client:
            return "Error: Client not initialized. Check your API key."
        
        try:
            response = ai_client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=(
                    "Summarize the following notes into clean, readable paragraphs. "
                    "Do NOT use any markdown symbols, asterisks, bullet points, or dashes. "
                    "Write it in plain, natural text:\n\n"
                    f"{text}"
                ),
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                return "AI Quota Exceeded for today. Please try again tomorrow or upgrade your API tier."
            return f"Generation Failed: {error_str}"

    def spawn_note_at(self, x, y, initial_text="", title="Study Note", width=550, height=760):
        card = NoteCard(self.canvas, initial_text=initial_text, title=title, width=width, height=height)
        card.current_width = width
        card.current_height = height
        
        window_item = self.canvas.create_window(x, y, window=card, anchor="nw", tags=("draggable",))
        
        # Force geometry propagation and update canvas window item sizing
        card.update_idletasks()
        card.configure(width=width, height=height)
        self.canvas.itemconfig(window_item, width=width, height=height)
        
        self.setup_card_dragging(card, window_item)
        self.update_minimap()
        self.save_current_workspace_state()
        return card

    def spawn_file_card_at(self, x, y, file_path, width=630, height=670):
        card = FileNoteCard(self.canvas, file_path=file_path, width=width, height=height)
        card.current_width = width
        card.current_height = height
        
        window_item = self.canvas.create_window(x, y, window=card, anchor="nw", tags=("draggable",))
        
        # Force geometry propagation and trigger image redraw if it's an image card
        card.update_idletasks()
        card.configure(width=width, height=height)
        self.canvas.itemconfig(window_item, width=width, height=height)
        if hasattr(card, "render_scaled_image"):
            card.render_scaled_image()
            
        self.setup_card_dragging(card, window_item)
        self.update_minimap()
        self.save_current_workspace_state()
        return card

    def setup_card_dragging(self, card, window_item):
        def start_header_drag(event):
            self._drag_data["x"] = event.x_root
            self._drag_data["y"] = event.y_root
            self._drag_data["item"] = window_item
            self.canvas.tag_raise(window_item)

        def motion_header_drag(event):
            dx = event.x_root - self._drag_data["x"]
            dy = event.y_root - self._drag_data["y"]
            self.canvas.move(window_item, dx, dy)
            self._drag_data["x"] = event.x_root
            self._drag_data["y"] = event.y_root
            self.update_minimap()

        def stop_header_drag(event):
            # CRITICAL: Save workspace state immediately when a card is dropped in its new position!
            self.save_current_workspace_state()

        # Bind header events
        card.header.bind("<Button-1>", start_header_drag)
        card.header.bind("<B1-Motion>", motion_header_drag)
        card.header.bind("<ButtonRelease-1>", stop_header_drag)
        
        card.title_label.bind("<Button-1>", start_header_drag)
        card.title_label.bind("<B1-Motion>", motion_header_drag)
        card.title_label.bind("<ButtonRelease-1>", stop_header_drag)

    def spawn_file_card(self):
        file_path = filedialog.askopenfilename(
            title="Create File Note from...",
            filetypes=[
                ("Supported Files", "*.png;*.jpg;*.jpeg;*.pdf"),
                ("Images", "*.png;*.jpg;*.jpeg"),
                ("PDF Documents", "*.pdf")
            ]
        )
        if file_path:
            v_width = self.canvas.winfo_width()
            v_height = self.canvas.winfo_height()
            world_x = self.canvas.canvasx(v_width / 2 - 180)
            world_y = self.canvas.canvasy(v_height / 2 - 180)
            self.spawn_file_card_at(world_x, world_y, file_path)

    def destroy(self):
        self.save_storage()
        super().destroy()


if __name__ == "__main__":
    app = NotionCanvasApp()
    app.mainloop()
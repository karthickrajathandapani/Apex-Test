import tkinter as tk
from tkinter import scrolledtext, font
import threading
import requests
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"


class OllamaChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Chat")
        self.root.geometry("750x620")
        self.root.resizable(True, True)
        self.root.configure(bg="#f0f2f5")

        self.colors = {
            "bg":           "#f0f2f5",
            "white":        "#ffffff",
            "user_bubble":  "#2563eb",
            "user_text":    "#ffffff",
            "bot_bubble":   "#e5e7eb",
            "bot_text":     "#111111",
            "header_bg":    "#ffffff",
            "header_border":"#e0e0e0",
            "input_bg":     "#fafafa",
            "input_border": "#dddddd",
            "send_btn":     "#2563eb",
            "send_hover":   "#1d4ed8",
            "status_on":    "#639922",
            "status_off":   "#E24B4A",
            "status_load":  "#EF9F27",
            "muted":        "#888888",
            "error_bg":     "#fff0f0",
            "error_text":   "#a32d2d",
        }

        self.build_ui()
        self.check_ollama_status()
        self.add_bot_message("Hello! I'm llama3 running locally via Ollama. How can I help you?")

    # ── UI Construction ─────────────────────────────────────────────────────

    def build_ui(self):
        self.build_header()
        self.build_messages_area()
        self.build_input_area()

    def build_header(self):
        header = tk.Frame(self.root, bg=self.colors["header_bg"],
                          relief="flat", bd=0)
        header.pack(fill="x", pady=(0, 0))

        inner = tk.Frame(header, bg=self.colors["header_bg"])
        inner.pack(fill="x", padx=16, pady=10)

        # Status dot (canvas circle)
        self.status_canvas = tk.Canvas(inner, width=12, height=12,
                                       bg=self.colors["header_bg"],
                                       highlightthickness=0)
        self.status_canvas.pack(side="left", padx=(0, 10))
        self.status_oval = self.status_canvas.create_oval(
            2, 2, 10, 10, fill=self.colors["status_off"], outline="")

        text_frame = tk.Frame(inner, bg=self.colors["header_bg"])
        text_frame.pack(side="left", fill="x", expand=True)

        tk.Label(text_frame, text="llama3",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.colors["header_bg"],
                 fg="#111").pack(anchor="w")

        tk.Label(text_frame, text="localhost:11434",
                 font=("Segoe UI", 10),
                 bg=self.colors["header_bg"],
                 fg=self.colors["muted"]).pack(anchor="w")

        clear_btn = tk.Button(inner, text="Clear chat",
                              font=("Segoe UI", 10),
                              bg=self.colors["white"],
                              fg=self.colors["muted"],
                              relief="solid", bd=1,
                              padx=10, pady=3,
                              cursor="hand2",
                              command=self.clear_chat)
        clear_btn.pack(side="right")

        # Separator line
        sep = tk.Frame(self.root, height=1, bg=self.colors["header_border"])
        sep.pack(fill="x")

    def build_messages_area(self):
        self.msg_frame_outer = tk.Frame(self.root, bg=self.colors["bg"])
        self.msg_frame_outer.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.msg_frame_outer,
                                bg=self.colors["bg"],
                                highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.msg_frame_outer,
                                      orient="vertical",
                                      command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.messages_inner = tk.Frame(self.canvas, bg=self.colors["bg"])
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.messages_inner, anchor="nw")

        self.messages_inner.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse scroll
        self.canvas.bind_all("<MouseWheel>",
            lambda e: self.canvas.yview_scroll(-1*(e.delta//120), "units"))

    def build_input_area(self):
        sep = tk.Frame(self.root, height=1, bg=self.colors["header_border"])
        sep.pack(fill="x")

        input_container = tk.Frame(self.root, bg=self.colors["white"], pady=10)
        input_container.pack(fill="x", side="bottom")

        inner = tk.Frame(input_container, bg=self.colors["white"])
        inner.pack(fill="x", padx=14)

        # Text input
        self.input_box = tk.Text(inner, height=2,
                                  font=("Segoe UI", 12),
                                  bg=self.colors["input_bg"],
                                  fg="#111",
                                  insertbackground="#111",
                                  relief="solid", bd=1,
                                  padx=10, pady=8,
                                  wrap="word")
        self.input_box.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.input_box.bind("<Return>", self.on_enter)
        self.input_box.bind("<Shift-Return>", lambda e: None)

        # Placeholder
        self._add_placeholder()

        # Send button
        self.send_btn = tk.Button(inner, text="Send ➤",
                                   font=("Segoe UI", 11, "bold"),
                                   bg=self.colors["send_btn"],
                                   fg="white",
                                   relief="flat",
                                   padx=16, pady=8,
                                   cursor="hand2",
                                   command=self.send_message)
        self.send_btn.pack(side="right")
        self.send_btn.bind("<Enter>",
            lambda e: self.send_btn.config(bg=self.colors["send_hover"]))
        self.send_btn.bind("<Leave>",
            lambda e: self.send_btn.config(bg=self.colors["send_btn"]))

        # Error label
        self.error_var = tk.StringVar()
        self.error_label = tk.Label(input_container,
                                     textvariable=self.error_var,
                                     font=("Segoe UI", 10),
                                     bg=self.colors["error_bg"],
                                     fg=self.colors["error_text"],
                                     pady=4)

    # ── Placeholder ─────────────────────────────────────────────────────────

    def _add_placeholder(self):
        self.placeholder = "Message llama3...  (Enter to send, Shift+Enter for newline)"
        self.input_box.insert("1.0", self.placeholder)
        self.input_box.config(fg="#bbb")
        self.input_box.bind("<FocusIn>", self._clear_placeholder)
        self.input_box.bind("<FocusOut>", self._restore_placeholder)

    def _clear_placeholder(self, event=None):
        if self.input_box.get("1.0", "end-1c") == self.placeholder:
            self.input_box.delete("1.0", "end")
            self.input_box.config(fg="#111")

    def _restore_placeholder(self, event=None):
        if not self.input_box.get("1.0", "end-1c").strip():
            self.input_box.insert("1.0", self.placeholder)
            self.input_box.config(fg="#bbb")

    # ── Message Rendering ────────────────────────────────────────────────────

    def add_user_message(self, text):
        self._add_bubble(text, role="user")

    def add_bot_message(self, text):
        self._add_bubble(text, role="bot")

    def _add_bubble(self, text, role="bot"):
        row = tk.Frame(self.messages_inner, bg=self.colors["bg"])
        row.pack(fill="x", padx=16, pady=6)

        is_user = role == "user"
        bubble_bg   = self.colors["user_bubble"] if is_user else self.colors["bot_bubble"]
        bubble_fg   = self.colors["user_text"]   if is_user else self.colors["bot_text"]
        anchor_side = "e" if is_user else "w"

        bubble_frame = tk.Frame(row, bg=self.colors["bg"])
        bubble_frame.pack(anchor=anchor_side)

        msg_label = tk.Label(bubble_frame,
                             text=text,
                             font=("Segoe UI", 12),
                             bg=bubble_bg,
                             fg=bubble_fg,
                             wraplength=460,
                             justify="left",
                             padx=14, pady=8)
        msg_label.pack(anchor=anchor_side)

        ts = tk.Label(bubble_frame,
                      text=datetime.now().strftime("%I:%M %p"),
                      font=("Segoe UI", 9),
                      bg=self.colors["bg"],
                      fg=self.colors["muted"])
        ts.pack(anchor=anchor_side, pady=(2, 0))

        self.root.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def show_typing(self):
        self.typing_row = tk.Frame(self.messages_inner, bg=self.colors["bg"])
        self.typing_row.pack(fill="x", padx=16, pady=6, anchor="w")
        self.typing_label = tk.Label(self.typing_row,
                                     text="● ● ●",
                                     font=("Segoe UI", 13),
                                     bg=self.colors["bot_bubble"],
                                     fg="#aaa",
                                     padx=14, pady=8)
        self.typing_label.pack(anchor="w")
        self._animate_typing(0)

    def _animate_typing(self, step):
        if not hasattr(self, 'typing_label') or \
           not self.typing_label.winfo_exists():
            return
        dots = ["● ○ ○", "○ ● ○", "○ ○ ●"]
        self.typing_label.config(text=dots[step % 3])
        self._typing_after = self.root.after(
            400, self._animate_typing, step + 1)

    def remove_typing(self):
        if hasattr(self, '_typing_after'):
            self.root.after_cancel(self._typing_after)
        if hasattr(self, 'typing_row') and self.typing_row.winfo_exists():
            self.typing_row.destroy()

    def show_error(self, msg):
        self.error_var.set("  " + msg)
        self.error_label.pack(fill="x", padx=14, pady=(0, 4))
        self.root.after(5000, self.hide_error)

    def hide_error(self):
        self.error_label.pack_forget()

    def clear_chat(self):
        for widget in self.messages_inner.winfo_children():
            widget.destroy()
        self.add_bot_message("Chat cleared. How can I help you?")

    # ── Send Logic ───────────────────────────────────────────────────────────

    def on_enter(self, event):
        if event.state & 0x1:   # Shift held → newline
            return
        self.send_message()
        return "break"

    def send_message(self):
        text = self.input_box.get("1.0", "end-1c").strip()
        if not text or text == self.placeholder:
            return

        self.input_box.delete("1.0", "end")
        self.input_box.config(fg="#111")
        self.send_btn.config(state="disabled")
        self.set_status("loading")

        self.add_user_message(text)
        self.show_typing()

        thread = threading.Thread(target=self._fetch_response,
                                  args=(text,), daemon=True)
        thread.start()

    def _fetch_response(self, prompt):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={"model": MODEL, "prompt": prompt, "stream": False},
                timeout=120
            )
            response.raise_for_status()
            reply = response.json().get("response", "No response received.")
            self.root.after(0, self._on_response_success, reply)
        except requests.exceptions.ConnectionError:
            self.root.after(0, self._on_response_error,
                "Could not connect to Ollama. Make sure it is running: ollama serve")
        except requests.exceptions.Timeout:
            self.root.after(0, self._on_response_error,
                "Request timed out. The model may be loading — try again.")
        except Exception as e:
            self.root.after(0, self._on_response_error, str(e))

    def _on_response_success(self, reply):
        self.remove_typing()
        self.add_bot_message(reply)
        self.set_status("online")
        self.send_btn.config(state="normal")
        self.input_box.focus_set()

    def _on_response_error(self, msg):
        self.remove_typing()
        self.add_bot_message("Connection failed. Is Ollama running?\nTry: ollama serve")
        self.show_error(msg)
        self.set_status("offline")
        self.send_btn.config(state="normal")

    # ── Status ───────────────────────────────────────────────────────────────

    def set_status(self, state):
        color_map = {
            "online":  self.colors["status_on"],
            "offline": self.colors["status_off"],
            "loading": self.colors["status_load"],
        }
        color = color_map.get(state, self.colors["status_off"])
        self.status_canvas.itemconfig(self.status_oval, fill=color)

    def check_ollama_status(self):
        def _check():
            try:
                r = requests.get("http://localhost:11434/api/tags", timeout=3)
                if r.ok:
                    self.root.after(0, self.set_status, "online")
            except Exception:
                pass
        threading.Thread(target=_check, daemon=True).start()

    # ── Canvas resize helpers ────────────────────────────────────────────────

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event=None):
        self.canvas.itemconfig(self.canvas_window, width=event.width)


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaChatApp(root)
    root.mainloop()
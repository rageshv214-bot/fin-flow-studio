#!/usr/bin/env python3
"""
FIN-FLOW // Student Budget & Expense Visualizer (Ultra-Premium Tkinter UI)
==========================================================================
Pure standard-library Python 3 (`tkinter`, `math`, `time`, `random`) — zero external dependencies.
Frontend-only, student-friendly personal finance & daily expense studio featuring:
  - 60-FPS custom Canvas rendering & cubic/spring easing animations
  - 3 hot-swappable dark neon themes (Midnight Emerald, Cyber Violet, Solaris Gold)
  - Animated radial budget gauges & morphing multi-segment spending donut ring
  - 14-day daily burn-rate spline chart with threshold line & glowing head marker
  - Interactive "+ Add Expense" modal, 1-click daily spend presets, & Ctrl+K Command Palette
  - What-If Monthly Allowance & Savings Simulator + floating toast notifications
"""

import tkinter as tk
import math
import time
import random


# ==============================================================================
# 1. COLOR PALETTES & THEME TOKENS
# ==============================================================================
THEMES = {
    "Midnight Emerald": {
        "bg_root": "#060A09",
        "bg_sidebar": "#0A110F",
        "bg_card": "#101B18",
        "bg_card_hover": "#152520",
        "bg_glass": "#192E28",
        "border": "#1F3830",
        "accent_primary": "#00FF87",
        "accent_secondary": "#00E5FF",
        "accent_tertiary": "#FFB703",
        "accent_pink": "#FF2A85",
        "success": "#00FF87",
        "warning": "#FFB703",
        "danger": "#FF3366",
        "text_primary": "#ECFDF5",
        "text_secondary": "#86B5A3",
        "text_muted": "#46695C",
    },
    "Cyber Violet": {
        "bg_root": "#08070E",
        "bg_sidebar": "#0D0B17",
        "bg_card": "#141124",
        "bg_card_hover": "#1C1833",
        "bg_glass": "#241E42",
        "border": "#2A244A",
        "accent_primary": "#B565FF",
        "accent_secondary": "#00F2FE",
        "accent_tertiary": "#FF2A85",
        "accent_pink": "#FF8E53",
        "success": "#00E676",
        "warning": "#FFD166",
        "danger": "#FF2A85",
        "text_primary": "#F5F3FF",
        "text_secondary": "#A59EC9",
        "text_muted": "#544D78",
    },
    "Solaris Gold": {
        "bg_root": "#0B0907",
        "bg_sidebar": "#120F0B",
        "bg_card": "#1C1712",
        "bg_card_hover": "#262018",
        "bg_glass": "#30281E",
        "border": "#3B3124",
        "accent_primary": "#FFB703",
        "accent_secondary": "#FB5607",
        "accent_tertiary": "#00F5D4",
        "accent_pink": "#FF006E",
        "success": "#06D6A0",
        "warning": "#FFB703",
        "danger": "#FF006E",
        "text_primary": "#FFFBEB",
        "text_secondary": "#C9B38C",
        "text_muted": "#6E5D44",
    },
}


# ==============================================================================
# 2. COLOR & GEOMETRY HELPERS
# ==============================================================================
def hex_to_rgb(hex_col: str):
    h = hex_col.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, int(rgb[0]))),
        max(0, min(255, int(rgb[1]))),
        max(0, min(255, int(rgb[2]))),
    )


def lerp_color(c1: str, c2: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex((r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t))


def draw_rounded_rect(canvas: tk.Canvas, x1, y1, x2, y2, r=14, **kwargs):
    r = min(r, max(1, (x2 - x1) / 2), max(1, (y2 - y1) / 2))
    points = [
        x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1,
        x2, y1, x2, y1 + r, x2, y1 + r, x2, y2 - r,
        x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2,
        x1 + r, y2, x1 + r, y2, x1, y2, x1, y2 - r,
        x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# ==============================================================================
# 3. CUSTOM ANIMATED WIDGETS
# ==============================================================================
class RippleButton(tk.Canvas):
    """Animated button with smooth hover glow and click ripple wave."""

    def __init__(
        self,
        parent,
        text="Action",
        icon="✦",
        command=None,
        width=155,
        height=38,
        theme=None,
        primary=True,
    ):
        self.theme = theme or THEMES["Midnight Emerald"]
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent["bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.text = text
        self.icon = icon
        self.command = command
        self.w = width
        self.h = height
        self.primary = primary

        self.hover_t = 0.0
        self.target_hover = 0.0
        self.ripples = []

        self.bind("<Enter>", lambda _: self._set_hover(1.0))
        self.bind("<Leave>", lambda _: self._set_hover(0.0))
        self.bind("<Button-1>", self._on_click)
        self._render()

    def set_theme(self, theme):
        self.theme = theme
        self.configure(bg=self.master["bg"])
        self._render()

    def _set_hover(self, target):
        self.target_hover = target
        self._animate()

    def _on_click(self, event):
        self.ripples.append([event.x, event.y, 2.0, 1.0])
        self._animate()
        if self.command:
            self.command()

    def _animate(self):
        needs_next = False
        if abs(self.hover_t - self.target_hover) > 0.02:
            self.hover_t += (self.target_hover - self.hover_t) * 0.25
            needs_next = True
        else:
            self.hover_t = self.target_hover

        alive = []
        for r in self.ripples:
            r[2] += 6.2
            r[3] -= 0.06
            if r[3] > 0:
                alive.append(r)
                needs_next = True
        self.ripples = alive

        self._render()
        if needs_next:
            self.after(16, self._animate)

    def _render(self):
        self.delete("all")
        t = self.theme
        if self.primary:
            base_bg = lerp_color(t["accent_secondary"], t["accent_primary"], 0.35 + 0.55 * self.hover_t)
            border_col = lerp_color(t["accent_primary"], "#FFFFFF", self.hover_t * 0.5)
            fg_col = "#060A09"
        else:
            base_bg = lerp_color(t["bg_card"], t["bg_glass"], self.hover_t)
            border_col = lerp_color(t["border"], t["accent_primary"], self.hover_t)
            fg_col = t["text_primary"]

        if self.hover_t > 0.05:
            glow_col = lerp_color(t["bg_card"], t["accent_primary"], self.hover_t * 0.45)
            draw_rounded_rect(self, 1, 1, self.w - 1, self.h - 1, r=12, fill="", outline=glow_col, width=2)

        draw_rounded_rect(self, 3, 3, self.w - 3, self.h - 3, r=10, fill=base_bg, outline=border_col, width=1.5)

        for rx, ry, rad, alpha in self.ripples:
            rip_col = lerp_color(base_bg, "#FFFFFF", alpha * 0.7)
            self.create_oval(rx - rad, ry - rad, rx + rad, ry + rad, outline=rip_col, width=2)

        label = f"{self.icon}  {self.text}" if self.icon else self.text
        self.create_text(self.w / 2, self.h / 2, text=label, fill=fg_col, font=("Helvetica", 10, "bold"))


class AnimatedToggle(tk.Canvas):
    """Physics-eased pill toggle switch."""

    def __init__(self, parent, initial=True, command=None, theme=None):
        self.theme = theme or THEMES["Midnight Emerald"]
        super().__init__(
            parent, width=50, height=26, bg=parent["bg"], highlightthickness=0, bd=0, cursor="hand2"
        )
        self.state = initial
        self.pos = 1.0 if initial else 0.0
        self.command = command
        self.bind("<Button-1>", self.toggle)
        self._render()

    def set_theme(self, theme):
        self.theme = theme
        self.configure(bg=self.master["bg"])
        self._render()

    def toggle(self, _=None):
        self.state = not self.state
        self._animate()
        if self.command:
            self.command(self.state)

    def _animate(self):
        target = 1.0 if self.state else 0.0
        if abs(self.pos - target) > 0.02:
            self.pos += (target - self.pos) * 0.28
            self._render()
            self.after(16, self._animate)
        else:
            self.pos = target
            self._render()

    def _render(self):
        self.delete("all")
        t = self.theme
        track_col = lerp_color(t["bg_root"], t["accent_primary"], self.pos * 0.85)
        border_col = lerp_color(t["border"], t["accent_primary"], self.pos)
        draw_rounded_rect(self, 2, 2, 48, 24, r=11, fill=track_col, outline=border_col, width=1.5)

        knob_x = 13 + self.pos * 24
        knob_col = lerp_color(t["text_secondary"], "#FFFFFF", self.pos)
        if self.pos > 0.2:
            halo = lerp_color(track_col, "#FFFFFF", 0.35 * self.pos)
            self.create_oval(knob_x - 10, 3, knob_x + 10, 23, fill=halo, outline="")
        self.create_oval(knob_x - 8, 5, knob_x + 8, 21, fill=knob_col, outline="")


# ==============================================================================
# 4. MAIN APPLICATION: FIN-FLOW STUDIO
# ==============================================================================
class FinFlowStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FIN-FLOW // Student Budget & Expense Visualizer")
        self.geometry("1340x840")
        self.minsize(1120, 720)

        self.theme_name = "Midnight Emerald"
        self.theme = THEMES[self.theme_name]
        self.configure(bg=self.theme["bg_root"])

        # Navigation & Loop State
        self.active_tab = "Overview"
        self.sidebar_indicator_y = 18.0
        self.target_indicator_y = 18.0
        self.nav_hover_idx = -1
        self.start_time = time.time()
        self.tick_count = 0

        # Student Finance Data Model (Frontend Interactive State)
        self.monthly_budget = 8000.0
        self.savings_goal = 2500.0
        self.auto_save_enabled = True
        self.weekend_alert = True

        self.categories = {
            "Food & Canteen": {"spent": 2150.0, "color_key": "accent_primary", "anim_angle": 0.0},
            "Travel & Bus": {"spent": 1180.0, "color_key": "accent_secondary", "anim_angle": 0.0},
            "Tech & Subs": {"spent": 790.0, "color_key": "accent_tertiary", "anim_angle": 0.0},
            "Gaming & Fun": {"spent": 620.0, "color_key": "accent_pink", "anim_angle": 0.0},
        }

        self.transactions = [
            {"title": "Campus Canteen Lunch", "cat": "Food & Canteen", "amt": 140.0, "time": "Today, 1:15 PM"},
            {"title": "Metro & Bus Pass", "cat": "Travel & Bus", "amt": 350.0, "time": "Today, 8:40 AM"},
            {"title": "Spotify + Cloud Storage", "cat": "Tech & Subs", "amt": 299.0, "time": "Yesterday"},
            {"title": "Cold Coffee & Snacks", "cat": "Food & Canteen", "amt": 95.0, "time": "Yesterday"},
            {"title": "Weekend Movie Ticket", "cat": "Gaming & Fun", "amt": 260.0, "time": "2 days ago"},
            {"title": "Dinner Mess Extra", "cat": "Food & Canteen", "amt": 180.0, "time": "3 days ago"},
        ]

        # 14-Day Daily Burn Rate (₹ per day)
        self.daily_spend = [210, 340, 180, 490, 260, 310, 540, 220, 195, 380, 420, 275, 310, 235]

        # Animated Gauge Values [current, target]
        self.anim_budget_pct = 0.0
        self.anim_remaining = 0.0
        self.anim_saved = 0.0

        # Ambient floating currency/orb particles
        self.particles = [
            {
                "x": random.uniform(40, 920),
                "y": random.uniform(40, 520),
                "vx": random.uniform(-0.45, 0.45),
                "vy": random.uniform(-0.45, 0.45),
                "r": random.uniform(2.0, 4.0),
                "phase": random.uniform(0, 6.28),
            }
            for _ in range(26)
        ]

        self.toasts = []
        self._build_layout()
        self._bind_shortcuts()

        self.after(180, lambda: self.spawn_toast("FIN-FLOW Student Budget Engine Ready!", "success"))
        self._animate_loop()

    # --------------------------------------------------------------------------
    # COMPUTED METRICS
    # --------------------------------------------------------------------------
    @property
    def total_spent(self) -> float:
        return sum(c["spent"] for c in self.categories.values())

    @property
    def remaining_budget(self) -> float:
        return max(0.0, self.monthly_budget - self.total_spent)

    @property
    def budget_pct(self) -> float:
        if self.monthly_budget <= 0:
            return 100.0
        return min(100.0, (self.total_spent / self.monthly_budget) * 100.0)

    @property
    def current_savings(self) -> float:
        base = max(0.0, self.monthly_budget - self.total_spent)
        return base * (0.45 if self.auto_save_enabled else 0.30)

    # --------------------------------------------------------------------------
    # LAYOUT CONSTRUCTION
    # --------------------------------------------------------------------------
    def _build_layout(self):
        t = self.theme

        # 1. Left Sidebar
        self.sidebar = tk.Frame(self, bg=t["bg_sidebar"], width=250)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.brand_canvas = tk.Canvas(
            self.sidebar, width=250, height=95, bg=t["bg_sidebar"], highlightthickness=0
        )
        self.brand_canvas.pack(fill="x")

        self.nav_items = [
            ("Overview", "◈", "Budget & Ring Analytics"),
            ("Transactions", "≡", "Daily Expense Ledger"),
            ("What-If Planner", "⚡", "Allowance Simulator"),
        ]
        self.nav_canvas = tk.Canvas(
            self.sidebar, width=250, height=195, bg=t["bg_sidebar"], highlightthickness=0, cursor="hand2"
        )
        self.nav_canvas.pack(fill="x", pady=(6, 0))
        self.nav_canvas.bind("<Motion>", self._on_nav_motion)
        self.nav_canvas.bind("<Leave>", lambda _: setattr(self, "nav_hover_idx", -1))
        self.nav_canvas.bind("<Button-1>", self._on_nav_click)

        # Quick Spend Presets Card in Sidebar
        self.preset_card = tk.Frame(self.sidebar, bg=t["bg_card"], padx=14, pady=12)
        self.preset_card.pack(fill="x", padx=16, pady=(6, 12))

        self.lbl_preset = tk.Label(
            self.preset_card,
            text="1-CLICK DAILY LOG",
            bg=t["bg_card"],
            fg=t["text_secondary"],
            font=("Helvetica", 8, "bold"),
        )
        self.lbl_preset.pack(anchor="w", pady=(0, 6))

        presets = [
            ("☕ Coffee & Snack  (₹60)", "Coffee & Snack", "Food & Canteen", 60),
            ("🍛 Campus Lunch  (₹130)", "Campus Lunch", "Food & Canteen", 130),
            ("🚌 Auto / Bus Ride  (₹45)", "Auto / Bus Ride", "Travel & Bus", 45),
            ("🎮 Game Top-Up  (₹190)", "In-Game Pass", "Gaming & Fun", 190),
        ]
        for label, title, cat, amt in presets:
            row = tk.Label(
                self.preset_card,
                text=label,
                bg=t["bg_glass"],
                fg=t["text_primary"],
                font=("Helvetica", 9, "bold"),
                anchor="w",
                padx=8,
                pady=5,
                cursor="hand2",
            )
            row.pack(fill="x", pady=3)
            row.bind("<Button-1>", lambda e, ti=title, ca=cat, am=amt: self.add_expense(ti, ca, am))

        # Theme Switcher Card in Sidebar
        self.theme_card = tk.Frame(self.sidebar, bg=t["bg_card"], padx=14, pady=10)
        self.theme_card.pack(fill="x", padx=16, pady=4)

        self.lbl_theme = tk.Label(
            self.theme_card,
            text="COLOR THEME",
            bg=t["bg_card"],
            fg=t["text_secondary"],
            font=("Helvetica", 8, "bold"),
        )
        self.lbl_theme.pack(anchor="w", pady=(0, 4))

        for th_name in THEMES:
            btn = tk.Label(
                self.theme_card,
                text=f"●  {th_name}",
                bg=t["bg_card"],
                fg=THEMES[th_name]["accent_primary"],
                font=("Helvetica", 9, "bold"),
                anchor="w",
                padx=4,
                pady=3,
                cursor="hand2",
            )
            btn.pack(fill="x")
            btn.bind("<Button-1>", lambda e, n=th_name: self.switch_theme(n))

        # Sidebar Footer Wallet Health Pulse
        self.footer_canvas = tk.Canvas(
            self.sidebar, width=250, height=105, bg=t["bg_sidebar"], highlightthickness=0
        )
        self.footer_canvas.pack(side="bottom", fill="x")

        # 2. Main Content Area
        self.main_area = tk.Frame(self, bg=t["bg_root"])
        self.main_area.pack(side="left", fill="both", expand=True)

        # Top Header Bar
        self.topbar = tk.Frame(self.main_area, bg=t["bg_root"], height=76)
        self.topbar.pack(fill="x", padx=26, pady=(16, 4))
        self.topbar.pack_propagate(False)

        self.title_frame = tk.Frame(self.topbar, bg=t["bg_root"])
        self.title_frame.pack(side="left", fill="y")

        self.lbl_page_title = tk.Label(
            self.title_frame,
            text="FIN-FLOW // STUDENT BUDGET OVERVIEW",
            bg=t["bg_root"],
            fg=t["text_primary"],
            font=("Helvetica", 16, "bold"),
        )
        self.lbl_page_title.pack(anchor="w", pady=(4, 2))

        self.lbl_page_sub = tk.Label(
            self.title_frame,
            text="",
            bg=t["bg_root"],
            fg=t["accent_primary"],
            font=("Courier", 10),
        )
        self.lbl_page_sub.pack(anchor="w")
        self._start_typewriter("MONTHLY ALLOWANCE: ₹8,000  •  PRESS [⌘K] COMMAND PALETTE  •  [⌘N] ADD EXPENSE")

        self.top_controls = tk.Frame(self.topbar, bg=t["bg_root"])
        self.top_controls.pack(side="right", fill="y")

        self.btn_cmd = RippleButton(
            self.top_controls,
            text="Commands [⌘K]",
            icon="⌕",
            width=150,
            height=38,
            theme=t,
            primary=False,
            command=self.toggle_command_palette,
        )
        self.btn_cmd.pack(side="left", padx=6, pady=12)

        self.btn_add = RippleButton(
            self.top_controls,
            text="+ Add Expense",
            icon="₹",
            width=155,
            height=38,
            theme=t,
            primary=True,
            command=self.open_add_expense_modal,
        )
        self.btn_add.pack(side="left", padx=6, pady=12)

        # Dynamic Workspace Canvas
        self.workspace = tk.Canvas(self.main_area, bg=t["bg_root"], highlightthickness=0, bd=0)
        self.workspace.pack(fill="both", expand=True, padx=26, pady=(4, 14))
        self.workspace.bind("<Button-1>", self._on_workspace_click)

        # Bottom Interactive Control Bar
        self.control_bar = tk.Frame(self.main_area, bg=t["bg_card"], height=58)
        self.control_bar.pack(fill="x", padx=26, pady=(0, 18))
        self.control_bar.pack_propagate(False)
        self._populate_control_bar()

    def _populate_control_bar(self):
        t = self.theme
        for w in self.control_bar.winfo_children():
            w.destroy()

        tk.Label(
            self.control_bar,
            text="💰 AUTO-SAVE BOOST",
            bg=t["bg_card"],
            fg=t["text_primary"],
            font=("Helvetica", 9, "bold"),
        ).pack(side="left", padx=(18, 8))

        self.toggle_autosave = AnimatedToggle(
            self.control_bar,
            initial=self.auto_save_enabled,
            theme=t,
            command=self._on_toggle_autosave,
        )
        self.toggle_autosave.pack(side="left", padx=(0, 22))

        tk.Label(
            self.control_bar,
            text="✦ AMBIENT ORBS",
            bg=t["bg_card"],
            fg=t["text_primary"],
            font=("Helvetica", 9, "bold"),
        ).pack(side="left", padx=(8, 8))

        self.toggle_orbs = AnimatedToggle(
            self.control_bar,
            initial=True,
            theme=t,
            command=lambda s: self.spawn_toast(f"Ambient Orbs {'Enabled' if s else 'Paused'}", "info"),
        )
        self.toggle_orbs.pack(side="left", padx=(0, 22))

        tk.Label(
            self.control_bar,
            text="MONTHLY BUDGET (₹):",
            bg=t["bg_card"],
            fg=t["text_secondary"],
            font=("Helvetica", 9, "bold"),
        ).pack(side="left", padx=(8, 6))

        self.budget_slider = tk.Scale(
            self.control_bar,
            from_=4000,
            to=20000,
            resolution=500,
            orient="horizontal",
            bg=t["bg_card"],
            fg=t["accent_primary"],
            troughcolor=t["bg_root"],
            highlightthickness=0,
            bd=0,
            length=160,
            showvalue=False,
            command=self._on_budget_slider,
        )
        self.budget_slider.set(self.monthly_budget)
        self.budget_slider.pack(side="left", padx=4)

        self.lbl_budget_val = tk.Label(
            self.control_bar,
            text=f"₹{int(self.monthly_budget):,}",
            bg=t["bg_card"],
            fg=t["accent_primary"],
            font=("Courier", 10, "bold"),
        )
        self.lbl_budget_val.pack(side="left", padx=6)

        RippleButton(
            self.control_bar,
            text="Reset Month",
            icon="↺",
            width=135,
            height=34,
            theme=t,
            primary=False,
            command=self.reset_month,
        ).pack(side="right", padx=14)

    # --------------------------------------------------------------------------
    # INTERACTIVE ACTIONS
    # --------------------------------------------------------------------------
    def _bind_shortcuts(self):
        self.bind("<Control-k>", lambda _: self.toggle_command_palette())
        self.bind("<Command-k>", lambda _: self.toggle_command_palette())
        self.bind("<Control-n>", lambda _: self.open_add_expense_modal())
        self.bind("<Command-n>", lambda _: self.open_add_expense_modal())
        self.bind("<Escape>", lambda _: self._close_modals())

    def _start_typewriter(self, full_text: str):
        self._typewriter_text = full_text
        self._typewriter_idx = 0
        self._step_typewriter()

    def _step_typewriter(self):
        if self._typewriter_idx <= len(self._typewriter_text):
            cur = self._typewriter_text[: self._typewriter_idx]
            cursor = "▋" if self._typewriter_idx < len(self._typewriter_text) else ""
            self.lbl_page_sub.configure(text=cur + cursor)
            self._typewriter_idx += 2
            self.after(24, self._step_typewriter)

    def _on_toggle_autosave(self, state: bool):
        self.auto_save_enabled = state
        self.spawn_toast(f"Auto-Save Boost {'Activated (45%)' if state else 'Standard (30%)'}", "success")

    def _on_budget_slider(self, val):
        self.monthly_budget = float(val)
        self.lbl_budget_val.configure(text=f"₹{int(self.monthly_budget):,}")

    def add_expense(self, title: str, category: str, amount: float):
        if amount <= 0:
            return
        self.categories[category]["spent"] += amount
        self.transactions.insert(
            0, {"title": title, "cat": category, "amt": amount, "time": "Just now"}
        )
        self.daily_spend[-1] += amount
        if self.budget_pct >= 85:
            self.spawn_toast(f"Added ₹{int(amount)} ({title}) — Budget at {self.budget_pct:.0f}%!", "warning")
        else:
            self.spawn_toast(f"Logged ₹{int(amount)} for {title}", "success")

    def reset_month(self):
        self.categories["Food & Canteen"]["spent"] = 1200.0
        self.categories["Travel & Bus"]["spent"] = 650.0
        self.categories["Tech & Subs"]["spent"] = 499.0
        self.categories["Gaming & Fun"]["spent"] = 300.0
        self.daily_spend = [180, 220, 150, 290, 210, 240, 310, 190, 160, 220, 250, 180, 210, 195]
        self.spawn_toast("Monthly Ledger Reset to Baseline", "info")

    def _on_nav_motion(self, event):
        idx = int(event.y // 58)
        self.nav_hover_idx = idx if 0 <= idx < len(self.nav_items) else -1

    def _on_nav_click(self, event):
        idx = int(event.y // 58)
        if 0 <= idx < len(self.nav_items):
            tab_name, _, subtitle = self.nav_items[idx]
            self.active_tab = tab_name
            self.target_indicator_y = idx * 58 + 18
            self.lbl_page_title.configure(text=f"FIN-FLOW // {tab_name.upper()} — {subtitle.upper()}")
            self._start_typewriter(
                f"ACTIVE VIEW: {tab_name.upper()}  •  SPENT: ₹{int(self.total_spent):,} / ₹{int(self.monthly_budget):,}"
            )

    def _on_workspace_click(self, event):
        # In What-If Planner view, allow clicking preset scenario cards
        if self.active_tab == "What-If Planner":
            w = max(860, self.workspace.winfo_width())
            if 20 < event.y < 140:
                if event.x < w / 3:
                    self.monthly_budget = 6000.0
                    self.budget_slider.set(6000)
                    self.spawn_toast("Applied Hostel Tight Budget (₹6,000/mo)", "info")
                elif event.x < (2 * w) / 3:
                    self.monthly_budget = 10000.0
                    self.budget_slider.set(10000)
                    self.spawn_toast("Applied Balanced Student Budget (₹10,000/mo)", "success")
                else:
                    self.monthly_budget = 15000.0
                    self.budget_slider.set(15000)
                    self.spawn_toast("Applied Internship / Pro Budget (₹15,000/mo)", "warning")

    def switch_theme(self, theme_name: str):
        self.theme_name = theme_name
        self.theme = THEMES[theme_name]
        t = self.theme

        self.configure(bg=t["bg_root"])
        self.sidebar.configure(bg=t["bg_sidebar"])
        self.brand_canvas.configure(bg=t["bg_sidebar"])
        self.nav_canvas.configure(bg=t["bg_sidebar"])
        self.footer_canvas.configure(bg=t["bg_sidebar"])

        self.preset_card.configure(bg=t["bg_card"])
        self.lbl_preset.configure(bg=t["bg_card"], fg=t["text_secondary"])
        for child in self.preset_card.winfo_children():
            if child != self.lbl_preset:
                child.configure(bg=t["bg_glass"], fg=t["text_primary"])

        self.theme_card.configure(bg=t["bg_card"])
        self.lbl_theme.configure(bg=t["bg_card"], fg=t["text_secondary"])
        for child in self.theme_card.winfo_children():
            if child != self.lbl_theme:
                child.configure(bg=t["bg_card"])

        self.main_area.configure(bg=t["bg_root"])
        self.topbar.configure(bg=t["bg_root"])
        self.title_frame.configure(bg=t["bg_root"])
        self.top_controls.configure(bg=t["bg_root"])
        self.lbl_page_title.configure(bg=t["bg_root"], fg=t["text_primary"])
        self.lbl_page_sub.configure(bg=t["bg_root"], fg=t["accent_primary"])
        self.workspace.configure(bg=t["bg_root"])
        self.control_bar.configure(bg=t["bg_card"])

        self.btn_cmd.set_theme(t)
        self.btn_add.set_theme(t)
        self._populate_control_bar()
        self.spawn_toast(f"Theme switched to {theme_name}", "success")

    # --------------------------------------------------------------------------
    # MODALS: ADD EXPENSE & COMMAND PALETTE
    # --------------------------------------------------------------------------
    def open_add_expense_modal(self):
        self._close_modals()
        t = self.theme
        self.modal_win = tk.Toplevel(self)
        self.modal_win.overrideredirect(True)
        self.modal_win.configure(bg=t["accent_primary"])

        mw, mh = 440, 340
        rx = self.winfo_rootx() + (self.winfo_width() - mw) // 2
        ry = self.winfo_rooty() + 130
        self.modal_win.geometry(f"{mw}x{mh}+{rx}+{ry}")

        box = tk.Frame(self.modal_win, bg=t["bg_card"], padx=22, pady=18)
        box.pack(fill="both", expand=True, padx=2, pady=2)

        hdr = tk.Frame(box, bg=t["bg_card"])
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="₹  LOG NEW EXPENSE", bg=t["bg_card"], fg=t["accent_primary"], font=("Helvetica", 11, "bold")
        ).pack(side="left")
        close_lbl = tk.Label(
            hdr, text="✕", bg=t["bg_card"], fg=t["text_secondary"], font=("Helvetica", 12, "bold"), cursor="hand2"
        )
        close_lbl.pack(side="right")
        close_lbl.bind("<Button-1>", lambda _: self._close_modals())

        tk.Label(box, text="ITEM / DESCRIPTION", bg=t["bg_card"], fg=t["text_secondary"], font=("Helvetica", 8, "bold")).pack(anchor="w", pady=(14, 4))
        ent_title = tk.Entry(box, bg=t["bg_root"], fg=t["text_primary"], insertbackground=t["accent_primary"], font=("Helvetica", 11), relief="flat", bd=8)
        ent_title.insert(0, "Evening Chai & Samosa")
        ent_title.pack(fill="x")
        ent_title.focus_set()

        tk.Label(box, text="AMOUNT (₹)", bg=t["bg_card"], fg=t["text_secondary"], font=("Helvetica", 8, "bold")).pack(anchor="w", pady=(12, 4))
        ent_amt = tk.Entry(box, bg=t["bg_root"], fg=t["accent_primary"], insertbackground=t["accent_primary"], font=("Courier", 12, "bold"), relief="flat", bd=8)
        ent_amt.insert(0, "80")
        ent_amt.pack(fill="x")

        tk.Label(box, text="CATEGORY", bg=t["bg_card"], fg=t["text_secondary"], font=("Helvetica", 8, "bold")).pack(anchor="w", pady=(12, 4))
        cat_var = tk.StringVar(value="Food & Canteen")
        cat_menu = tk.OptionMenu(box, cat_var, *self.categories.keys())
        cat_menu.configure(bg=t["bg_glass"], fg=t["text_primary"], highlightthickness=0, bd=0, font=("Helvetica", 10, "bold"))
        cat_menu.pack(fill="x", pady=(0, 14))

        def submit():
            try:
                amt = float(ent_amt.get().strip())
            except ValueError:
                amt = 0.0
            title = ent_title.get().strip() or "Daily Expense"
            self._close_modals()
            if amt > 0:
                self.add_expense(title, cat_var.get(), amt)
            else:
                self.spawn_toast("Enter a valid positive amount", "danger")

        RippleButton(box, text="Log Expense", icon="✓", width=180, height=38, theme=t, primary=True, command=submit).pack(pady=4)
        self.modal_win.bind("<Return>", lambda _: submit())
        self.modal_win.bind("<Escape>", lambda _: self._close_modals())

    def toggle_command_palette(self):
        if hasattr(self, "modal_win") and self.modal_win and self.modal_win.winfo_exists():
            self._close_modals()
            return

        t = self.theme
        self.modal_win = tk.Toplevel(self)
        self.modal_win.overrideredirect(True)
        self.modal_win.configure(bg=t["accent_primary"])

        pw, ph = 500, 310
        rx = self.winfo_rootx() + (self.winfo_width() - pw) // 2
        ry = self.winfo_rooty() + 115
        self.modal_win.geometry(f"{pw}x{ph}+{rx}+{ry}")

        inner = tk.Frame(self.modal_win, bg=t["bg_card"], padx=18, pady=16)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        hdr = tk.Frame(inner, bg=t["bg_card"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="⌕  FIN-FLOW COMMAND PALETTE", bg=t["bg_card"], fg=t["accent_primary"], font=("Helvetica", 10, "bold")).pack(side="left")
        tk.Label(hdr, text="[ESC]", bg=t["bg_card"], fg=t["text_secondary"], font=("Helvetica", 9)).pack(side="right")

        actions = [
            ("₹  Log Custom Expense [⌘N]", self.open_add_expense_modal),
            ("☕  Quick Log: ₹60 Coffee & Snack", lambda: self.add_expense("Coffee & Snack", "Food & Canteen", 60)),
            ("≡  View Daily Expense Ledger", lambda: self._switch_tab_idx(1)),
            ("⚡  Open What-If Allowance Planner", lambda: self._switch_tab_idx(2)),
            ("🎨  Theme: Midnight Emerald", lambda: self.switch_theme("Midnight Emerald")),
            ("🎨  Theme: Cyber Violet", lambda: self.switch_theme("Cyber Violet")),
            ("🎨  Theme: Solaris Gold", lambda: self.switch_theme("Solaris Gold")),
        ]

        for label, cb in actions:
            row = tk.Label(
                inner, text=label, bg=t["bg_card"], fg=t["text_primary"],
                font=("Helvetica", 10), anchor="w", padx=10, pady=7, cursor="hand2"
            )
            row.pack(fill="x", pady=1)
            row.bind("<Enter>", lambda e, r=row: r.configure(bg=t["bg_glass"], fg=t["accent_primary"]))
            row.bind("<Leave>", lambda e, r=row: r.configure(bg=t["bg_card"], fg=t["text_primary"]))
            row.bind("<Button-1>", lambda e, fn=cb: (self._close_modals(), fn()))

        self.modal_win.bind("<Escape>", lambda _: self._close_modals())

    def _switch_tab_idx(self, idx):
        fake_evt = type("Evt", (), {"y": idx * 58 + 20})()
        self._on_nav_click(fake_evt)

    def _close_modals(self):
        if hasattr(self, "modal_win") and self.modal_win and self.modal_win.winfo_exists():
            self.modal_win.destroy()

    # --------------------------------------------------------------------------
    # TOAST NOTIFICATIONS
    # --------------------------------------------------------------------------
    def spawn_toast(self, text: str, category="info"):
        color_map = {
            "success": self.theme["success"],
            "warning": self.theme["warning"],
            "danger": self.theme["danger"],
            "info": self.theme["accent_secondary"],
        }
        self.toasts.insert(0, {"text": text, "color": color_map.get(category, self.theme["accent_primary"]), "y": -48.0, "born": time.time()})
        if len(self.toasts) > 4:
            self.toasts.pop()

    # --------------------------------------------------------------------------
    # MASTER 60-FPS ANIMATION LOOP
    # --------------------------------------------------------------------------
    def _animate_loop(self):
        self.tick_count += 1
        elapsed = time.time() - self.start_time

        # Smooth metric easing
        self.anim_budget_pct += (self.budget_pct - self.anim_budget_pct) * 0.12
        self.anim_remaining += (self.remaining_budget - self.anim_remaining) * 0.12
        self.anim_saved += (self.current_savings - self.anim_saved) * 0.12

        total = max(1.0, self.total_spent)
        for cat in self.categories.values():
            target_ang = (cat["spent"] / total) * 360.0
            cat["anim_angle"] += (target_ang - cat["anim_angle"]) * 0.12

        self._render_brand_logo(elapsed)
        self._render_sidebar_nav()
        self._render_sidebar_footer(elapsed)
        self._render_workspace(elapsed)

        self.after(16, self._animate_loop)

    def _render_brand_logo(self, elapsed: float):
        c = self.brand_canvas
        c.delete("all")
        t = self.theme
        cx, cy = 42, 48

        for i, rad in enumerate((20, 13)):
            ang = elapsed * (90 if i == 0 else -135)
            col = t["accent_primary"] if i == 0 else t["accent_secondary"]
            c.create_arc(cx - rad, cy - rad, cx + rad, cy + rad, start=ang % 360, extent=235, style="arc", outline=col, width=2.5)

        core_r = 5 + 1.4 * math.sin(elapsed * 4)
        c.create_oval(cx - core_r, cy - core_r, cx + core_r, cy + core_r, fill=t["accent_primary"], outline="")
        c.create_text(78, 38, text="FIN-FLOW", anchor="w", fill=t["text_primary"], font=("Helvetica", 15, "bold"))
        c.create_text(78, 58, text="STUDENT BUDGET STUDIO", anchor="w", fill=t["accent_primary"], font=("Courier", 8, "bold"))
        c.create_line(18, 92, 232, 92, fill=t["border"], width=1)

    def _render_sidebar_nav(self):
        c = self.nav_canvas
        c.delete("all")
        t = self.theme

        self.sidebar_indicator_y += (self.target_indicator_y - self.sidebar_indicator_y) * 0.22
        pill_y = self.sidebar_indicator_y
        draw_rounded_rect(c, 14, pill_y - 10, 236, pill_y + 36, r=11, fill=t["bg_glass"], outline=t["border"], width=1)
        c.create_line(16, pill_y - 2, 16, pill_y + 28, fill=t["accent_primary"], width=4, capstyle="round")

        for idx, (name, icon, sub) in enumerate(self.nav_items):
            y = idx * 58 + 18
            is_active = name == self.active_tab
            is_hover = idx == self.nav_hover_idx
            if is_hover and not is_active:
                draw_rounded_rect(c, 14, y - 10, 236, y + 36, r=11, fill=t["bg_card_hover"], outline="")

            icon_col = t["accent_primary"] if (is_active or is_hover) else t["text_secondary"]
            text_col = t["text_primary"] if (is_active or is_hover) else t["text_secondary"]
            c.create_text(38, y + 12, text=icon, fill=icon_col, font=("Helvetica", 13))
            c.create_text(64, y + 5, text=name, anchor="w", fill=text_col, font=("Helvetica", 10, "bold"))
            c.create_text(64, y + 22, text=sub, anchor="w", fill=t["text_muted"], font=("Helvetica", 8))

    def _render_sidebar_footer(self, elapsed: float):
        c = self.footer_canvas
        c.delete("all")
        t = self.theme
        draw_rounded_rect(c, 16, 8, 234, 94, r=12, fill=t["bg_card"], outline=t["border"])

        status_col = t["danger"] if self.budget_pct >= 90 else (t["warning"] if self.budget_pct >= 75 else t["success"])
        status_txt = "CRITICAL SPEND" if self.budget_pct >= 90 else ("WATCH BUDGET" if self.budget_pct >= 75 else "WALLET HEALTHY")

        pulse_r = 5 + 2.8 * abs(math.sin(elapsed * 3.0))
        c.create_oval(34 - pulse_r, 30 - pulse_r, 34 + pulse_r, 30 + pulse_r, fill=lerp_color(t["bg_card"], status_col, 0.4), outline="")
        c.create_oval(30, 26, 38, 34, fill=status_col, outline="")
        c.create_text(48, 30, text=status_txt, anchor="w", fill=t["text_primary"], font=("Helvetica", 9, "bold"))

        c.create_text(30, 52, text=f"SAFE / DAY: ₹{int(self.remaining_budget / 15):,}", anchor="w", fill=t["text_secondary"], font=("Courier", 9, "bold"))

        # Animated mini spend bars
        for i in range(14):
            bh = 5 + 13 * abs(math.sin(elapsed * 3.2 + i * 0.5))
            bx = 30 + i * 13
            bar_col = lerp_color(t["accent_secondary"], t["accent_primary"], i / 14.0)
            c.create_line(bx, 82, bx, 82 - bh, fill=bar_col, width=3, capstyle="round")

    # --------------------------------------------------------------------------
    # WORKSPACE RENDERERS
    # --------------------------------------------------------------------------
    def _render_workspace(self, elapsed: float):
        c = self.workspace
        c.delete("all")
        w = max(860, c.winfo_width())
        h = max(530, c.winfo_height())

        if getattr(self, "toggle_orbs", None) and self.toggle_orbs.state:
            self._render_ambient_orbs(c, w, h, elapsed)

        if self.active_tab == "Overview":
            self._render_overview(c, w, h, elapsed)
        elif self.active_tab == "Transactions":
            self._render_transactions(c, w, h)
        else:
            self._render_planner(c, w, h, elapsed)

        self._render_toasts(c, w)

    def _render_ambient_orbs(self, c: tk.Canvas, w: int, h: int, elapsed: float):
        t = self.theme
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["x"] < 15 or p["x"] > w - 15:
                p["vx"] *= -1
            if p["y"] < 15 or p["y"] > h - 15:
                p["vy"] *= -1
            r = p["r"] + 0.7 * math.sin(elapsed * 2.5 + p["phase"])
            col = lerp_color(t["bg_root"], t["accent_primary"], 0.25)
            c.create_oval(p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r, fill=col, outline="")

    def _render_overview(self, c: tk.Canvas, w: int, h: int, elapsed: float):
        t = self.theme
        pad = 14
        top_h = 205
        card_w = (w - pad * 2) / 3

        # --- ROW 1: THREE ANIMATED RADIAL KPI CARDS ---
        kpis = [
            ("BUDGET UTILIZED", f"{self.anim_budget_pct:.1f}%", f"₹{int(self.total_spent):,} spent", self.anim_budget_pct, t["accent_primary"]),
            ("REMAINING SAFE SPEND", f"₹{int(self.anim_remaining):,}", f"of ₹{int(self.monthly_budget):,} limit", 100.0 - self.anim_budget_pct, t["accent_secondary"]),
            ("SAVINGS VAULT", f"₹{int(self.anim_saved):,}", f"Goal: ₹{int(self.savings_goal):,}", min(100.0, (self.anim_saved / self.savings_goal) * 100.0), t["accent_tertiary"]),
        ]

        for idx, (label, big_val, sub_val, pct, col) in enumerate(kpis):
            x1 = idx * (card_w + pad)
            y1 = 4
            x2 = x1 + card_w
            y2 = y1 + top_h
            draw_rounded_rect(c, x1, y1, x2, y2, r=16, fill=t["bg_card"], outline=t["border"], width=1.5)
            c.create_line(x1 + 22, y1 + 2, x2 - 22, y1 + 2, fill=col, width=2)
            c.create_text(x1 + 20, y1 + 24, text=label, anchor="w", fill=t["text_secondary"], font=("Helvetica", 9, "bold"))

            # Radial Arc
            cx, cy, rad = x1 + card_w * 0.30, y1 + 118, 52
            c.create_arc(cx - rad, cy - rad, cx + rad, cy + rad, start=225, extent=-270, style="arc", outline=t["bg_root"], width=10)
            c.create_arc(cx - rad, cy - rad, cx + rad, cy + rad, start=225, extent=-270 * (max(2.0, pct) / 100.0), style="arc", outline=col, width=10)
            c.create_text(cx, cy, text=f"{pct:.0f}%", fill=t["text_primary"], font=("Helvetica", 14, "bold"))

            rx = x1 + card_w * 0.57
            c.create_text(rx, y1 + 100, text=big_val, anchor="w", fill=t["text_primary"], font=("Helvetica", 18, "bold"))
            c.create_text(rx, y1 + 130, text=sub_val, anchor="w", fill=col, font=("Courier", 10, "bold"))

        # --- ROW 2: SPENDING DONUT + 14-DAY BURN-RATE SPLINE + SAVINGS GOALS ---
        r2_y1 = top_h + 18
        r2_y2 = h - 4
        col1_w = w * 0.34
        col2_w = w * 0.645

        # Left Card: Animated Category Spending Donut
        draw_rounded_rect(c, 0, r2_y1, col1_w, r2_y2, r=16, fill=t["bg_card"], outline=t["border"], width=1.5)
        c.create_text(20, r2_y1 + 26, text="SPENDING BREAKDOWN", anchor="w", fill=t["text_primary"], font=("Helvetica", 11, "bold"))

        dcx, dcy, drad = col1_w * 0.5, r2_y1 + 125, 68
        start_ang = 90.0
        for cname, cinfo in self.categories.items():
            ext = max(4.0, cinfo["anim_angle"])
            ccol = t[cinfo["color_key"]]
            c.create_arc(dcx - drad, dcy - drad, dcx + drad, dcy + drad, start=start_ang, extent=-ext + 3, style="arc", outline=ccol, width=18)
            start_ang -= ext

        c.create_text(dcx, dcy - 8, text=f"₹{int(self.total_spent):,}", fill=t["text_primary"], font=("Helvetica", 13, "bold"))
        c.create_text(dcx, dcy + 12, text="TOTAL SPENT", fill=t["text_secondary"], font=("Helvetica", 7, "bold"))

        # Category Legend
        ly = r2_y1 + 215
        for cname, cinfo in self.categories.items():
            ccol = t[cinfo["color_key"]]
            c.create_oval(22, ly - 5, 32, ly + 5, fill=ccol, outline="")
            c.create_text(40, ly, text=cname, anchor="w", fill=t["text_secondary"], font=("Helvetica", 9, "bold"))
            c.create_text(col1_w - 22, ly, text=f"₹{int(cinfo['spent']):,}", anchor="e", fill=t["text_primary"], font=("Courier", 9, "bold"))
            ly += 24

        # Right Card: 14-Day Daily Burn-Rate Spline Chart
        rx1 = w - col2_w
        draw_rounded_rect(c, rx1, r2_y1, w, r2_y2, r=16, fill=t["bg_card"], outline=t["border"], width=1.5)
        c.create_text(rx1 + 22, r2_y1 + 26, text="14-DAY DAILY BURN RATE (₹ / DAY)", anchor="w", fill=t["text_primary"], font=("Helvetica", 11, "bold"))
        c.create_text(w - 22, r2_y1 + 26, text="--- DAILY SAFE LIMIT (₹300)", anchor="e", fill=t["warning"], font=("Courier", 9, "bold"))

        gx1, gy1 = rx1 + 32, r2_y1 + 58
        gx2, gy2 = w - 26, r2_y2 - 34
        gw, gh = max(120, gx2 - gx1), max(90, gy2 - gy1)
        max_val = max(600.0, max(self.daily_spend) * 1.15)

        for i in range(4):
            gy = gy1 + (gh / 3) * i
            c.create_line(gx1, gy, gx2, gy, fill=t["border"], dash=(3, 5))

        # Safe daily limit dashed line (₹300)
        safe_y = gy2 - (300.0 / max_val) * gh
        c.create_line(gx1, safe_y, gx2, safe_y, fill=t["warning"], dash=(6, 4), width=1.5)

        pts = []
        n = len(self.daily_spend)
        for idx, val in enumerate(self.daily_spend):
            px = gx1 + (idx / (n - 1)) * gw
            py = gy2 - (val / max_val) * gh
            pts.extend([px, py])

        scan_col = lerp_color(t["bg_card"], t["accent_primary"], 0.20)
        for idx in range(0, len(pts), 2):
            c.create_line(pts[idx], pts[idx + 1], pts[idx], gy2, fill=scan_col, width=3)

        c.create_line(*pts, fill=t["accent_primary"], width=3, smooth=True)
        for idx in range(0, len(pts), 2):
            px, py = pts[idx], pts[idx + 1]
            c.create_oval(px - 3.5, py - 3.5, px + 3.5, py + 3.5, fill=t["accent_secondary"], outline=t["bg_card"])

        # Pulsing Today Marker
        lx, ly = pts[-2], pts[-1]
        pr = 6 + 3 * abs(math.sin(elapsed * 4))
        c.create_oval(lx - pr, ly - pr, lx + pr, ly + pr, outline=t["accent_primary"], width=1.5)
        c.create_oval(lx - 5, ly - 5, lx + 5, ly + 5, fill="#FFFFFF", outline=t["accent_primary"], width=2)
        c.create_text(lx, ly - 16, text=f"₹{int(self.daily_spend[-1])}", fill=t["accent_primary"], font=("Courier", 9, "bold"))

    def _render_transactions(self, c: tk.Canvas, w: int, h: int):
        t = self.theme
        draw_rounded_rect(c, 0, 4, w, h - 4, r=16, fill=t["bg_card"], outline=t["border"], width=1.5)
        c.create_text(26, 32, text="RECENT STUDENT EXPENSE LEDGER", anchor="w", fill=t["text_primary"], font=("Helvetica", 12, "bold"))
        c.create_text(w - 26, 32, text="CLICK '+ ADD EXPENSE' OR SIDEBAR PRESETS TO LOG LIVE", anchor="e", fill=t["accent_primary"], font=("Courier", 9, "bold"))
        c.create_line(24, 54, w - 24, 54, fill=t["border"])

        y = 74
        for idx, tx in enumerate(self.transactions[:8]):
            if y + 48 > h - 16:
                break
            cat_info = self.categories.get(tx["cat"], {"color_key": "accent_primary"})
            col = t[cat_info["color_key"]]
            draw_rounded_rect(c, 24, y, w - 24, y + 44, r=10, fill=t["bg_root"], outline=t["border"])
            c.create_oval(42, y + 17, 52, y + 27, fill=col, outline="")
            c.create_text(66, y + 22, text=tx["title"], anchor="w", fill=t["text_primary"], font=("Helvetica", 10, "bold"))
            c.create_text(w * 0.48, y + 22, text=tx["cat"], anchor="w", fill=col, font=("Helvetica", 9, "bold"))
            c.create_text(w * 0.72, y + 22, text=tx["time"], anchor="w", fill=t["text_secondary"], font=("Helvetica", 9))
            c.create_text(w - 42, y + 22, text=f"- ₹{int(tx['amt']):,}", anchor="e", fill=t["text_primary"], font=("Courier", 11, "bold"))
            y += 54

    def _render_planner(self, c: tk.Canvas, w: int, h: int, elapsed: float):
        t = self.theme
        pad = 14
        card_w = (w - pad * 2) / 3

        presets = [
            ("HOSTEL TIGHT MODE", "₹6,000 / month", "Max savings discipline", t["accent_secondary"]),
            ("BALANCED STUDENT", "₹10,000 / month", "Comfortable food & commute", t["accent_primary"]),
            ("INTERNSHIP PRO", "₹15,000 / month", "Tech gear + weekend trips", t["accent_tertiary"]),
        ]
        for idx, (title, amt, desc, col) in enumerate(presets):
            x1 = idx * (card_w + pad)
            x2 = x1 + card_w
            draw_rounded_rect(c, x1, 6, x2, 132, r=14, fill=t["bg_card"], outline=col, width=1.5)
            c.create_text(x1 + 20, 30, text=title, anchor="w", fill=col, font=("Helvetica", 10, "bold"))
            c.create_text(x1 + 20, 64, text=amt, anchor="w", fill=t["text_primary"], font=("Helvetica", 16, "bold"))
            c.create_text(x1 + 20, 96, text=f"{desc}  (Click to apply)", anchor="w", fill=t["text_secondary"], font=("Helvetica", 9))

        # Bottom Savings Goals Progress Bars with Shimmer
        draw_rounded_rect(c, 0, 152, w, h - 4, r=16, fill=t["bg_card"], outline=t["border"], width=1.5)
        c.create_text(26, 182, text="STUDENT SAVINGS GOALS & MILESTONES", anchor="w", fill=t["text_primary"], font=("Helvetica", 12, "bold"))

        goals = [
            ("Mac / Tech Upgrade Fund", min(1.0, self.anim_saved / 4000.0), t["accent_primary"], "₹4,000 Target"),
            ("Weekend Kerala / Pondy Trip", min(1.0, self.anim_saved / 2500.0), t["accent_secondary"], "₹2,500 Target"),
            ("Emergency Hostel Buffer", min(1.0, self.anim_saved / 1500.0), t["accent_tertiary"], "₹1,500 Target"),
        ]
        gy = 228
        bar_w = w - 60
        for gname, ratio, gcol, target_lbl in goals:
            c.create_text(28, gy, text=gname, anchor="w", fill=t["text_primary"], font=("Helvetica", 10, "bold"))
            c.create_text(w - 28, gy, text=f"{int(ratio * 100)}%  •  {target_lbl}", anchor="e", fill=gcol, font=("Courier", 10, "bold"))
            draw_rounded_rect(c, 28, gy + 16, 28 + bar_w, gy + 30, r=7, fill=t["bg_root"], outline="")
            fill_w = max(16, bar_w * ratio)
            draw_rounded_rect(c, 28, gy + 16, 28 + fill_w, gy + 30, r=7, fill=gcol, outline="")

            shimmer_x = (elapsed * 160) % fill_w
            if shimmer_x + 28 < fill_w:
                c.create_line(28 + shimmer_x, gy + 23, 28 + shimmer_x + 28, gy + 23, fill="#FFFFFF", width=3, capstyle="round")
            gy += 78

    def _render_toasts(self, c: tk.Canvas, w: int):
        t = self.theme
        now = time.time()
        alive = []
        for idx, toast in enumerate(self.toasts):
            if now - toast["born"] > 3.5:
                continue
            target_y = 14 + idx * 46
            toast["y"] += (target_y - toast["y"]) * 0.25
            tx1, ty1, tx2, ty2 = w - 375, toast["y"], w - 16, toast["y"] + 38
            draw_rounded_rect(c, tx1, ty1, tx2, ty2, r=10, fill=t["bg_glass"], outline=toast["color"], width=1.5)
            c.create_oval(tx1 + 14, ty1 + 14, tx1 + 24, ty1 + 24, fill=toast["color"], outline="")
            c.create_text(tx1 + 34, ty1 + 19, text=toast["text"], anchor="w", fill=t["text_primary"], font=("Helvetica", 9, "bold"))
            alive.append(toast)
        self.toasts = alive


if __name__ == "__main__":
    app = FinFlowStudio()
    app.mainloop()
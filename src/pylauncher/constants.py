"""Application-wide constants for colors, fonts, and dimensions."""

# ── Colors (Dark Mode – Neutral) ──
DEEP_PINK = "#FF1493"
DEEP_PINK_HOVER = "#E01280"

BG_DARK = "#1e1e1e"        # Main window background
BG_CARD = "#252526"         # Card/panel background
BG_INPUT = "#3c3c3c"        # Input fields, script rows
BG_SURFACE = "#2d2d2d"      # Tab content, elevated surfaces
BG_HOVER = "#454545"        # Hover states

TEXT_PRIMARY = "#e0e0e0"     # Primary text
TEXT_SECONDARY = "#858585"   # Secondary/muted text
TEXT_DIM = "#5a5a5a"         # Dim text, placeholders

BORDER_COLOR = "#3e3e3e"     # Borders
SCROLLBAR_COLOR = "#3e3e3e"

TRANSPARENT = "transparent"

# Feature colors
WARNING_COLOR = "#FFB347"           # Orange for invalid path warnings
HIGHLIGHT_COLOR = "#FFD700"         # Gold for search highlights
HIGHLIGHT_CURRENT_COLOR = "#FF8C00" # Darker gold for current match

# Legacy aliases used across UI files
WHITE = TEXT_PRIMARY
WHITE_SMOKE = BG_DARK
DARK_GRAY = TEXT_PRIMARY
MEDIUM_GRAY = TEXT_SECONDARY
LIGHT_GRAY = TEXT_SECONDARY
SILVER = TEXT_DIM
GAINSBORO = BG_HOVER

# ── Fonts ──
FONT_FAMILY = "Segoe UI"
FONT_TITLE_FAMILY = "Arial Rounded MT Bold"
FONT_SIZE_DEFAULT = 13
FONT_SIZE_TITLE = 24
FONT_SIZE_SMALL = 11
FONT_SIZE_LABEL = 12
FONT_MONO = "Consolas"
FONT_MONO_SIZE = 11

# ── Window Dimensions ──
MAIN_WINDOW_WIDTH = 1096
MAIN_WINDOW_HEIGHT = 668

SETTINGS_WINDOW_WIDTH = 600
SETTINGS_WINDOW_HEIGHT = 480

CLI_WINDOW_WIDTH = 650
CLI_WINDOW_HEIGHT = 520

SCHEDULE_DIALOG_WIDTH = 520
SCHEDULE_DIALOG_HEIGHT = 400

# ── Widget Dimensions ──
CARD_CORNER_RADIUS = 25
BUTTON_CORNER_RADIUS = 20
INPUT_CORNER_RADIUS = 5
ICON_SIZE = (24, 24)
TITLE_BAR_HEIGHT = 40
SCRIPT_ROW_HEIGHT = 50
ICON_BUTTON_SIZE = 32
IMPORT_BUTTON_WIDTH = 180
IMPORT_BUTTON_HEIGHT = 45

# ── Path Constants ──
SCRIPTS_DIR_NAME = "scripts"
ASSETS_DIR_NAME = "assets"
SETTINGS_FILE_NAME = "settings.ini"
SCRIPT_META_FILE_NAME = "me.ini"
STATE_FILE_NAME = "state.json"

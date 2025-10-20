"""
UI package
Exposes: render_chat_interface, apply_custom_styles
Version: 1.0.0
"""

# Streamlit imports for UI components
import streamlit as st

# Example UI configuration constants
UI_THEME = "banking-light"
UI_FONT = "Roboto"
UI_PRIMARY_COLOR = "#0055A4"

# Main UI components (to be implemented in separate modules)
from .components import render_chat_interface, apply_custom_styles

__version__ = "1.0.0"
__all__ = ["render_chat_interface", "apply_custom_styles", "UI_THEME", "UI_FONT", "UI_PRIMARY_COLOR"]

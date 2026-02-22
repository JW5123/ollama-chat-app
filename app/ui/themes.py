LIGHT_THEME = {
    "window_bg":            "#F5F5F0",
    "chat_bg":              "#F5F5F0",
    "chat_border":          "#E0DED8",
    "input_bg":             "#FFFFFF",
    "input_border":         "#D0CEC8",
    "input_focus":          "#A0A0A0",
    "text_color":           "#1A1A1A",

    "bubble_user_bg":       "#1A1A1A",
    "bubble_user_fg":       "#FFFFFF",
    "bubble_assistant_bg":  "#E8E8E4",
    "bubble_assistant_fg":  "#1A1A1A",

    "btn_send_bg":          "#1A1A1A",
    "btn_send_fg":          "#FFFFFF",
    "btn_send_hover":       "#333333",
    "btn_clear_bg":         "#EDECE8",
    "btn_clear_fg":         "#1A1A1A",
    "btn_clear_hover":      "#DDDBD5",
    "btn_file_bg":          "#EDECE8",
    "btn_file_fg":          "#1A1A1A",
    "btn_file_hover":       "#DDDBD5",
    "btn_theme_bg":         "#EDECE8",
    "btn_theme_fg":         "#1A1A1A",
    "file_label_fg":        "#555555",
    "divider":              "#E0DED8",
    "scrollbar":            "#CCCCCC",
}

DARK_THEME = {
    "window_bg":            "#1C1C1E",
    "chat_bg":              "#1C1C1E",
    "chat_border":          "#3A3A3C",
    "input_bg":             "#2C2C2E",
    "input_border":         "#3A3A3C",
    "input_focus":          "#636366",
    "text_color":           "#F0F0F0",

    "bubble_user_bg":       "#2563EB",
    "bubble_user_fg":       "#FFFFFF",
    "bubble_assistant_bg":  "#3A3A3C",
    "bubble_assistant_fg":  "#F0F0F0",

    "btn_send_bg":          "#F0F0F0",
    "btn_send_fg":          "#1C1C1E",
    "btn_send_hover":       "#CCCCCC",
    "btn_clear_bg":         "#3A3A3C",
    "btn_clear_fg":         "#F0F0F0",
    "btn_clear_hover":      "#48484A",
    "btn_file_bg":          "#3A3A3C",
    "btn_file_fg":          "#F0F0F0",
    "btn_file_hover":       "#48484A",
    "btn_theme_bg":         "#3A3A3C",
    "btn_theme_fg":         "#F0F0F0",
    "file_label_fg":        "#AAAAAA",
    "divider":              "#3A3A3C",
    "scrollbar":            "#48484A",
}


def get_theme(dark_mode: bool) -> dict:
    return DARK_THEME if dark_mode else LIGHT_THEME


def get_stylesheets(dark_mode: bool) -> dict:
    t = get_theme(dark_mode)

    return {
        "window": f"""
            QWidget {{
                background-color: {t['window_bg']};
                color: {t['text_color']};
            }}
        """,

        "input_edit": f"""
            QTextEdit {{
                background-color: {t['input_bg']};
                color: {t['text_color']};
                border: 1px solid {t['input_border']};
                border-radius: 12px;
                padding: 10px 14px;
            }}
            QTextEdit:focus {{
                border: 1px solid {t['input_focus']};
            }}
        """,

        "send_btn": f"""
            QPushButton {{
                background-color: {t['btn_send_bg']};
                color: {t['btn_send_fg']};
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {t['btn_send_hover']}; }}
            QPushButton:disabled {{ opacity: 0.4; }}
        """,

        "clear_btn": f"""
            QPushButton {{
                background-color: {t['btn_clear_bg']};
                color: {t['btn_clear_fg']};
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {t['btn_clear_hover']}; }}
        """,

        "file_btn": f"""
            QPushButton {{
                background-color: {t['btn_file_bg']};
                color: {t['btn_file_fg']};
                border: none;
                border-radius: 8px;
                font-size: 13px;
                padding: 0 12px;
            }}
            QPushButton:hover {{ background-color: {t['btn_file_hover']}; }}
        """,

        "theme_btn": f"""
            QPushButton {{
                background-color: {t['btn_theme_bg']};
                color: {t['btn_theme_fg']};
                border: none;
                border-radius: 8px;
                font-size: 12px;
                padding: 0 10px;
            }}
            QPushButton:hover {{ background-color: {t['btn_clear_hover']}; }}
        """,

        "title_label":  f"color: {t['text_color']};",
        "divider":      f"background-color: {t['divider']}; border: none;",
        "file_label":   f"color: {t['file_label_fg']};",
    }
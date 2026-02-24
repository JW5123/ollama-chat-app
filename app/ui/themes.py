LIGHT_THEME = {
    "window_bg":            "#F5F5F0",
    "chat_bg":              "#F5F5F0",
    "input_bg":             "#FFFFFF",
    "input_border":         "#D0CEC8",
    "input_focus":          "#A0A0A0",
    "text_color":           "#1A1A1A",
    "bubble_user_bg":       "#1A1A1A",
    "bubble_user_fg":       "#FFFFFF",
    "bubble_assistant_bg":  "#E8E8E4",
    "bubble_assistant_fg":  "#1A1A1A",
    "link_color":           "#2563EB",
    "code_block_bg":        "#1E1E1E",
    "code_block_fg":        "#D4D4D4",
    "code_header_bg":       "#2D2D2D",
    "code_lang_fg":         "#AAAAAA",
    "inline_code_bg":       "rgba(0,0,0,0.08)",
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
    # 側邊欄
    "sidebar_bg":           "#ECEAE4",
    "sidebar_item_bg":      "transparent",
    "sidebar_item_hover":   "#DDDBD5",
    "sidebar_item_active":  "#D0CEC8",
    "sidebar_title_fg":     "#1A1A1A",
    "sidebar_date_fg":      "#888888",
    "sidebar_new_bg":       "#1A1A1A",
    "sidebar_new_fg":       "#FFFFFF",
    "sidebar_new_hover":    "#333333",
    "sidebar_del_fg":       "#888888",
    "sidebar_del_hover":    "#CC3333",
}

DARK_THEME = {
    "window_bg":            "#1C1C1E",
    "chat_bg":              "#1C1C1E",
    "input_bg":             "#2C2C2E",
    "input_border":         "#3A3A3C",
    "input_focus":          "#636366",
    "text_color":           "#F0F0F0",
    "bubble_user_bg":       "#2563EB",
    "bubble_user_fg":       "#FFFFFF",
    "bubble_assistant_bg":  "#3A3A3C",
    "bubble_assistant_fg":  "#F0F0F0",
    "link_color":           "#60A5FA",
    "code_block_bg":        "#1E1E1E",
    "code_block_fg":        "#D4D4D4",
    "code_header_bg":       "#2D2D2D",
    "code_lang_fg":         "#AAAAAA",
    "inline_code_bg":       "rgba(255,255,255,0.1)",
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
    # 側邊欄
    "sidebar_bg":           "#141416",
    "sidebar_item_bg":      "transparent",
    "sidebar_item_hover":   "#2C2C2E",
    "sidebar_item_active":  "#3A3A3C",
    "sidebar_title_fg":     "#F0F0F0",
    "sidebar_date_fg":      "#636366",
    "sidebar_new_bg":       "#2563EB",
    "sidebar_new_fg":       "#FFFFFF",
    "sidebar_new_hover":    "#1D4ED8",
    "sidebar_del_fg":       "#636366",
    "sidebar_del_hover":    "#EF4444",
}


def get_theme(dark_mode: bool) -> dict:
    return DARK_THEME if dark_mode else LIGHT_THEME


def get_stylesheets(dark_mode: bool) -> dict:
    t = get_theme(dark_mode)
    return {
        "window":         f"QWidget {{ background-color: {t['window_bg']}; color: {t['text_color']}; }}",
        "chat_container": f"background-color: {t['chat_bg']};",
        "scrollbar": f"""
            QScrollBar:vertical {{ background: transparent; width: 6px; }}
            QScrollBar::handle:vertical {{ background: {t['scrollbar']}; border-radius: 3px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """,
        "input_edit": f"""
            QTextEdit {{
                background-color: {t['input_bg']};
                color: {t['text_color']};
                border: 1px solid {t['input_border']};
                border-radius: 12px;
                padding: 10px 14px;
            }}
            QTextEdit:focus {{ border: 1px solid {t['input_focus']}; }}
        """,
        "bubble_user": f"""
            QLabel {{
                background-color: {t['bubble_user_bg']};
                color: {t['bubble_user_fg']};
                border-radius: 18px 18px 4px 18px;
                padding: 10px 14px;
            }}
        """,
        "bubble_assistant": f"""
            QLabel {{
                background-color: {t['bubble_assistant_bg']};
                color: {t['bubble_assistant_fg']};
                border-radius: 18px 18px 18px 4px;
                padding: 10px 14px;
            }}
        """,
        "code_container": f"background-color: {t['code_block_bg']}; border-radius: 8px;",
        "code_header_bar": f"""
            QWidget {{
                background-color: {t['code_header_bg']};
                border-radius: 8px 8px 0px 0px;
            }}
        """,
        "code_lang_label": f"color: {t['code_lang_fg']}; background: transparent;",
        "code_copy_btn": f"""
            QPushButton {{
                background-color: transparent;
                color: {t['code_lang_fg']};
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 4px;
                padding: 0 8px;
            
            }}
            QPushButton:hover {{
                background-color: rgba(255,255,255,0.1);
                color: {t['code_block_fg']};
            }}
        """,
        "code_edit": f"""
            QPlainTextEdit {{
                background-color: {t['code_block_bg']};
                color: {t['code_block_fg']};
                border: none;
                border-radius: 0px 0px 8px 8px;
                padding: 10px 14px;
                selection-background-color: rgba(255,255,255,0.2);
            }}
        """,
        "send_btn": f"""
            QPushButton {{
                background-color: {t['btn_send_bg']}; color: {t['btn_send_fg']};
                border: none; border-radius: 8px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {t['btn_send_hover']}; }}
            QPushButton:disabled {{ opacity: 0.4; }}
        """,
        "clear_btn": f"""
            QPushButton {{
                background-color: {t['btn_clear_bg']}; color: {t['btn_clear_fg']};
                border: none; border-radius: 8px;
            }}
            QPushButton:hover {{ background-color: {t['btn_clear_hover']}; }}
        """,
        "file_btn": f"""
            QPushButton {{
                background-color: {t['btn_file_bg']}; color: {t['btn_file_fg']};
                border: none; border-radius: 8px; padding: 0 12px;
            }}
            QPushButton:hover {{ background-color: {t['btn_file_hover']}; }}
        """,
        "theme_btn": f"""
            QPushButton {{
                background-color: {t['btn_theme_bg']}; color: {t['btn_theme_fg']};
                border: none; border-radius: 8px; padding: 0 10px;
            }}
            QPushButton:hover {{ background-color: {t['btn_clear_hover']}; }}
        """,
        "model_combo": f"""
            QComboBox {{
                background-color: {t['btn_theme_bg']};
                color: {t['btn_theme_fg']};
                border: none;
                border-radius: 8px;
                padding: 0 10px;
            
                font-family: "Microsoft JhengHei";
            }}
            QComboBox:hover {{ background-color: {t['btn_clear_hover']}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {t['btn_theme_fg']};
                margin-right: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {t['input_bg']};
                color: {t['text_color']};
                border: 1px solid {t['input_border']};
                selection-background-color: {t['btn_theme_bg']};
                selection-color: {t['btn_theme_fg']};
                padding: 4px;
            
                font-family: "Microsoft JhengHei";
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                height: 28px;
                padding-left: 8px;
            }}
        """,
        "title_label":       f"color: {t['text_color']};",
        "divider":           f"background-color: {t['divider']}; border: none;",
        "file_label":        f"color: {t['file_label_fg']};",
        "link_color":        t['link_color'],
        "inline_code_style": (
            f"font-family:Consolas;"
            f"background:{t['inline_code_bg']};"
            f"border-radius:3px;padding:1px 4px;"
        ),
        # 側邊欄樣式
        "sidebar": f"""
            QWidget {{
                background-color: {t['sidebar_bg']};
                border: none;
            }}
        """,
        "sidebar_new_btn": f"""
            QPushButton {{
                background-color: {t['sidebar_new_bg']};
                color: {t['sidebar_new_fg']};
                border: none;
                border-radius: 0px;
            
                font-family: "Microsoft JhengHei";
                padding: 0 16px;
                text-align: left;
            }}
            QPushButton:hover {{ background-color: {t['sidebar_new_hover']}; }}
        """,
        "sidebar_scroll": "QScrollArea { background: transparent; border: none; }",
        "sidebar_item": f"""
            QWidget {{
                background-color: {t['sidebar_item_bg']};
                border-radius: 6px;
            }}
            QWidget:hover {{
                background-color: {t['sidebar_item_hover']};
            }}
        """,
        "sidebar_item_active": f"""
            QWidget {{
                background-color: {t['sidebar_item_active']};
                border-radius: 6px;
            }}
        """,
        "sidebar_item_title": f"color: {t['sidebar_title_fg']}; background: transparent;",
        "sidebar_item_date":  f"color: {t['sidebar_date_fg']}; background: transparent;",
        "sidebar_del_btn": f"""
            QPushButton {{
                background-color: transparent;
                color: {t['sidebar_del_fg']};
                border: none;
                border-radius: 4px;
            
                padding: 0;
            }}
            QPushButton:hover {{ color: {t['sidebar_del_hover']}; }}
        """,
    }
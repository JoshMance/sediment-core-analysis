"""Colour tokens for the Sedivis themes.

Tokens are substituted into dark.qss / light.qss by apply.py before the
stylesheet is applied.  Use @token_name in the QSS files.

Substitution replaces longer names first so e.g. @bg_hover_tint is never
partially clobbered by @bg_hover.
"""

DARK: dict[str, str] = {
    # Backgrounds
    "bg":              "#1e1e1e",  # base window / widget background
    "bg_panel":        "#252526",  # panels, toolbars, trees, header background
    "bg_raised":       "#2d2d2d",  # raised surface: tab pane, header sections, disabled button
    "bg_alt":          "#2a2a2a",  # alternating tree rows
    "bg_hover":        "#2a2a2a",  # generic hover, tab hover
    "bg_hover_tint":   "#2a3a4a",  # accent-tinted hover (tree items)
    "bg_button":       "#3c3c3c",  # default button fill
    "bg_button_hover": "#4a4a4a",  # button hover fill
    # Foregrounds
    "fg":              "#dcdcdc",  # primary text
    "fg_muted":        "#aaaaaa",  # secondary text: inactive tabs, header, captions
    "fg_disabled":     "#555555",  # disabled text
    # Borders
    "border":          "#555555",  # standard border
    "border_inner":    "#3a3a3a",  # subtle inner border
    "border_hover":    "#666666",  # border on hover / focus
    # Interactive
    "selection":       "#094771",  # selected row background
    "btn_hover":       "#3a3a3a",  # icon / tool button hover fill
    "scrollbar":       "#4a4a4a",  # scrollbar handle
    "scrollbar_hover": "#666666",  # scrollbar handle hover
    # Accent
    "accent":          "#0078d4",
    "on_accent":       "#ffffff",
}

LIGHT: dict[str, str] = {
    # Backgrounds
    "bg":              "#f3f3f3",
    "bg_panel":        "#ffffff",   # trees, tooltips
    "bg_raised":       "#eaeaea",   # tab selected, toolbar, header sections, disabled button
    "bg_alt":          "#f7f7f7",   # alternating tree rows (subtle stripe)
    "bg_hover":        "#e0e0e0",   # tab hover
    "bg_hover_tint":   "#e8f3fc",   # accent-tinted hover (tree items)
    "bg_button":       "#e1e1e1",
    "bg_button_hover": "#d0d0d0",
    # Foregrounds
    "fg":              "#1a1a1a",
    "fg_muted":        "#666666",
    "fg_disabled":     "#aaaaaa",
    # Borders
    "border":          "#cccccc",
    "border_inner":    "#dddddd",
    "border_hover":    "#aaaaaa",
    # Interactive
    "selection":       "#cce4f7",
    "btn_hover":       "#dce9f8",   # icon / tool button hover fill
    "scrollbar":       "#cccccc",
    "scrollbar_hover": "#aaaaaa",
    # Accent
    "accent":          "#0078d4",
    "on_accent":       "#ffffff",
}

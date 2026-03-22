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
    "accent":          "#8A4C57",
    "accent_hover":    "#7a3f4a",
    "on_accent":       "#ffffff",
}

LIGHT: dict[str, str] = {
    # Backgrounds
    "bg":              "#f0f0f0",   # window chrome / splitter areas
    "bg_panel":        "#ffffff",   # content panels, trees, editors
    "bg_raised":       "#efefef",   # toolbars, header sections, dock titles
    "bg_alt":          "#f5f8fc",   # alternating tree rows (very subtle blue tint)
    "bg_hover":        "#e3eef8",   # generic hover
    "bg_hover_tint":   "#e3eef8",   # tree item hover
    "bg_button":       "#f0f0f0",   # button fill
    "bg_button_hover": "#dce8f5",   # button hover (light blue tint)
    # Foregrounds
    "fg":              "#1a1a1a",
    "fg_muted":        "#555555",
    "fg_disabled":     "#b0b0b0",
    # Borders
    "border":          "#c0c0c0",   # standard panel/button border
    "border_inner":    "#d8d8d8",   # subtle inner dividers
    "border_hover":    "#8A4C57",   # focus / active border (brand colour)
    # Interactive
    "selection":       "#f0e0e3",   # selected row background (brand tint)
    "btn_hover":       "#f0e0e3",   # icon / tool button hover
    "scrollbar":       "#c0c0c0",
    "scrollbar_hover": "#909090",
    # Accent
    "accent":          "#8A4C57",   # brand colour
    "accent_hover":    "#7a3f4a",
    "on_accent":       "#ffffff",
}

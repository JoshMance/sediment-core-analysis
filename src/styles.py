"""
Application styling and themes
"""

RIBBON_STYLE = """
    QTabWidget::tab-bar {
        alignment: left;
    }
    QTabWidget::pane {
        border: 1px solid #ccc;
        background: white;
        top: -1px;
    }
    QTabBar {
        background: #7C444E;
    }
    QTabBar::tab {
        color: white;
        border-top-left-radius: 0px;
        border-top-right-radius: 0px;
        padding: 5px 24px;
        margin-top: 5px;
        margin-left: 5px;
        margin-right: 2px;
        font-size: 13px;
    }
    QTabBar::tab:selected {
        background: white;
        color: black;
        border-top-left-radius: 0px;
        border-top-right-radius: 0px;
        border-bottom: 1px solid white;
    }
    QTabBar::tab:hover:!selected {
        background: #8E5560;
        border-top-left-radius: 0px;
        border-top-right-radius: 0px;
    }
    QPushButton {
        background: #f8f8f8;
        color: #333;
        border: none;
        border-radius: 4px;
        padding: 10px 20px;
        min-width: 90px;
        font-size: 13px;
    }
    QPushButton:hover {
        background: #e5f1fb;
        border: 1px solid #0078d4;
    }
    QPushButton:pressed {
        background: #cce4f7;
        border: 1px solid #005a9e;
    }
"""

RIBBON_TAB_STYLE = "background: white;"

WORKSPACE_STYLE = "background: white;"

PLACEHOLDER_STYLE = "color: #999; font-size: 16px; border: none; background: transparent;"

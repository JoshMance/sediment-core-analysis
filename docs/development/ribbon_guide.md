# Ribbon Guide

The ribbon is a tabbed toolbar across the top of the window. It is split across two files:

| File                                    | Responsibility                                             |
| --------------------------------------- | ---------------------------------------------------------- |
| `src/ui/views/shell/ribbon/ribbon.py`   | Layout — tabs, groups, button labels, icon mapping         |
| `src/ui/presenters/ribbon_presenter.py` | Behaviour — wires button clicks to `AppController` methods |

## Structure

Tabs contain groups; groups contain buttons. Each button has a string label that is the shared key between the view and the presenter.

```
Ribbon (QTabWidget)
└── Tab  e.g. "Home"
    └── RibbonGroup  e.g. "File"
        └── RibbonButton  e.g. "Save"
```

Current tabs and their groups:

- **Home** — session management and asset loading. File (`New`, `Open`, `Save`), Import (`Load Image`, `Load Data`, `Load Map`), Edit (`Undo`, `Redo`)
- **Core** — core creation and preparation. Core (`Core Studio`)
- **Analysis** — discrete analysis actions on entities. Core (`Analyse`)
- **Map** — 3D simulation and spatial visualisation. _(no buttons yet)_
- **Export** — format and download results for use outside the software. _(no buttons yet)_

## Adding a button

1. **View** — in `ribbon.py`, add the label string to the relevant `_add_group(...)` call in `_build_tabs()`. To add an icon, add an entry to `_ICON_MAP` mapping the label to an icon filename in `src/ui/resources/icons/`.

2. **Presenter** — in `ribbon_presenter.py`, add a handler method and register it in the `_handlers` dict using the same label string as the key.

## Flow

```
User clicks button
  → Ribbon emits buttonClicked(label)
    → RibbonPresenter._on_button_clicked(label)
      → looks up label in _handlers dict
        → calls handler method
          → calls AppController
```

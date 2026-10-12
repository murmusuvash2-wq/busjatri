# design/

All of the website's design in one place: colours, flow, components, page shells.
Today this is 8 scattered CSS files in `css/`; this folder is the target.

| File | What | Change this to |
|---|---|---|
| `tokens.css` | colours, fonts, spacing, radii | whole-site colour |
| `layout.css` | header, footer, container, grid | layout / flow |
| `components.css` | cards, chips, buttons, tables, badges | components |
| `templates/` | page shells (route, stand, via, home, place) | page structure |

Build: `tokens + layout + components \u2192 css/style.css`

Rule: no design change ships without a before/after screenshot check.

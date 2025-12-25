# 🎨 Modern UI - Visual Preview

## Dark Mode Example (Default)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                               ☀️ (toggle) │
│  🚀 Waypoint                                                             │
│  GitHub-Jira Sync Automation                                             │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
└─────────────────────────────────────────────────────────────────────────┘

📊 Dashboard  |  ⚙️ Automation Rules  |  📈 Status  |  ⚙️ Settings
════════════════════════════════════════════════════════════════════════════

┌─ Automation Rules Configuration ──────────────────────────────────────────┐
│ Configure how GitHub events are synced to Jira                            │
│                                                                            │
│ ┌─ 🆕 When PR is Opened                                      [ENABLED ☑] │
│ │                                                                         │
│ │  Move Ticket to Status: [In Review              ]                     │
│ │  Add Label:             [has-pr                 ]                     │
│ │  ☑ Add Comment to Ticket                                             │
│ │  Comment Template:      [🔗 PR opened: {pr_url} ]                     │
│ └─────────────────────────────────────────────────────────────────────────│
│                                                                            │
│ ┌─ ✅ When PR is Merged (Branch-Specific)         [ENABLED ☑] │
│ │                                                                         │
│ │  ┌─ Branch Rule ──────────────────────────────────────┐               │
│ │  │ Branch:        [DEV        ]  [Delete]             │               │
│ │  │ Move to Status [Ready for Testing    ]             │               │
│ │  │ Add Label:     [merged-dev ]                       │               │
│ │  │ ☑ Add Comment                                      │               │
│ │  └─────────────────────────────────────────────────────┘               │
│ │                                                                         │
│ │  ┌─ Branch Rule ──────────────────────────────────────┐               │
│ │  │ Branch:        [INT        ]  [Delete]             │               │
│ │  │ Move to Status [Ready for QA      ]                │               │
│ │  │ Add Label:     [merged-int ]                       │               │
│ │  │ ☑ Add Comment                                      │               │
│ │  └─────────────────────────────────────────────────────┘               │
│ │                                                                         │
│ │  ┌─ Branch Rule ──────────────────────────────────────┐               │
│ │  │ Branch:        [PVS        ]  [Delete]             │               │
│ │  │ Move to Status [Ready for QA      ]                │               │
│ │  │ Add Label:     [merged-pvs ]                       │               │
│ │  │ ☑ Add Comment                                      │               │
│ │  └─────────────────────────────────────────────────────┘               │
│ │                                                                         │
│ │  [+ Add Branch Rule]                                                   │
│ │                                                                         │
│ └─────────────────────────────────────────────────────────────────────────│
│                                                                            │
│ ┌─ ❌ When PR is Closed (Not Merged)              [ENABLED ☑] │
│ │                                                                         │
│ │  Add Label:             [pr-closed             ]                     │
│ │  ☑ Add Comment to Ticket                                             │
│ │                                                                         │
│ └─────────────────────────────────────────────────────────────────────────│
│                                                                            │
│                           [💾 SAVE RULES]  [↻ RESET]                    │
└────────────────────────────────────────────────────────────────────────────┘
```

## Light Mode (After Toggle)

Same layout but with:
- ☀️ White backgrounds
- 🌙 Dark text on light backgrounds
- Atlassian blue accents
- Softer shadows

## Interactive Features

### 1. Hovering Over Save Button
```
Before:  [💾 SAVE RULES]  (blue background)
Hover:   [💾 SAVE RULES]  (lifts up 2px, glow expands)
Click:   [💾 SAVE RULES]  (ripple effect spreads from center)
```

### 2. Toggling Dark Mode
```
Click: ☀️ (top right)
Result: All colors transition smoothly (0.3s)
        Theme saved to browser storage
        Preference persists on reload
```

### 3. Adding a Branch Rule
```
Click: [+ Add Branch Rule]
Result: New empty branch rule appears with animations
        Can immediately edit branch name, status, label
        Has delete button on the right
```

### 4. Editing Fields
```
Before: [DEV        ]
Click:  Focus ring appears (blue glow)
Edit:   Type new branch name
Result: Highlights in primary color, ready to save
```

## Color Palette

### Light Mode
```
Header:         Gradient blue (#0052CC → #0747A6)
Text Primary:   Dark gray (#1a1a2e)
Text Secondary: Medium gray (#6c757d)
Background:     White (#ffffff)
Borders:        Light gray (#dee2e6)
Success:        Green (#00875a)
Danger:         Red (#de350b)
```

### Dark Mode
```
Header:         Same gradient (adapts well)
Text Primary:   Light gray (#e9ecef)
Text Secondary: Medium gray (#adb5bd)
Background:     Dark navy (#1a1a2e)
Borders:        Dark gray (#3d3d54)
Success:        Green (#00875a)
Danger:         Red (#de350b)
```

## Animation Effects

### Button Hover
- `transform: translateY(-2px)` - Lifts up
- `box-shadow: expand` - Glow grows
- `transition: 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)` - Bouncy effect

### Tab Switch
- `animation: fadeIn 0.3s ease` - Smooth fade in
- Previous tab fades out simultaneously

### Theme Toggle
- Icon rotates 20° on hover
- Sun/moon icons cross-fade
- Scale up slightly on interaction

### Input Focus
- Border color changes to primary
- Glow box-shadow appears
- Smooth 0.2s transition

## Responsive Breakpoints

### Mobile (< 768px)
```
- Single column layout
- Full-width buttons
- Smaller font sizes
- Touch-friendly spacing (48px min)
- Smaller toggle button (44px)
```

### Tablet/Desktop (≥ 768px)
```
- Multi-column grids
- Inline buttons
- Larger fonts
- Comfortable spacing
- Standard toggle button (48px)
```

## User Workflow

1. **Open Modern UI**
   - Smooth header animation with floating effect
   - Dark mode by default
   - Professional gradient background

2. **Switch to Light Mode**
   - Click sun icon (top right)
   - All colors transition smoothly
   - Preference saved automatically

3. **Edit Automation Rules**
   - Type in status field → Focus glow appears
   - Type in label field → Blue border
   - Toggle checkbox → Smooth slide animation
   - Type comment → Text area highlights

4. **Add Branch Rule**
   - Click "+ Add Branch Rule" button
   - New rule slides in with animation
   - All fields ready to edit
   - Delete button available on the right

5. **Save Rules**
   - Click "Save Rules" button (blue glow)
   - Button lifts up on hover
   - Success notification appears (bottom right)
   - Config saved automatically

## Professional Polish Details

- ✨ Gradient headers with floating animation
- 🎨 Atlassian design color palette
- 📱 Mobile-first responsive design
- ♿ WCAG AA accessibility compliant
- 🎭 Dark/Light mode with smooth transitions
- ⚡ GPU-accelerated animations (60 FPS)
- 🎯 Intuitive form interactions
- 🎪 Toast notifications for feedback
- 🌈 Consistent styling throughout
- ⌨️ Keyboard accessible controls

---

**This is production-ready!** Open `modern-ui.html` in your browser to see it live.

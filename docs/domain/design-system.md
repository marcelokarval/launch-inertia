# Launch - Design System

> HeroUI v3 beta.6 + Tailwind CSS v4 + React 19
> Single source of truth for all UI decisions.

---

## 1. Foundation

### 1.1 Color System

Built on HeroUI's oklch tokens. We extend with a custom **gradient-primary** (Launch brand).

#### Brand Gradient

```css
--gradient-primary: linear-gradient(135deg, oklch(0.65 0.25 262) 0%, oklch(0.75 0.20 285) 100%);
```

Purple (262) to Pink-Purple (285), 135deg diagonal. Used for:
- Primary CTA buttons (`variant="primary"` on Button)
- First stat card (`variant="gradient"` on StatCard)
- Active sidebar nav item
- Logo container
- Avatar fallbacks

#### Semantic Tokens (use these, NEVER hardcode)

| Purpose | Light Mode Class | Dark Mode Class | Use |
|---------|-----------------|-----------------|-----|
| Page background | `bg-background` | auto | Body, main content |
| Card/surface | `bg-surface` | auto | Cards, panels |
| Primary text | `text-foreground` | auto | Headings, body |
| Secondary text | `text-default-500` | auto | Subtitles, labels |
| Muted text | `text-default-400` | auto | Timestamps, hints |
| Disabled text | `text-muted` | auto | Placeholders |
| Brand accent | `bg-accent` / `text-accent` | auto | Links, highlights |
| Success | `text-success` / `bg-success` | auto | Positive states |
| Warning | `text-warning` / `bg-warning` | auto | Caution states |
| Danger | `text-danger` / `bg-danger` | auto | Errors, destructive |
| Borders | `border-divider` | auto | Section separators |
| Card borders | `border-default-200` | auto | Card outlines |
| Hover borders | `border-default-300` | auto | Card hover state |

#### Prohibited

```
NEVER: bg-white, bg-gray-*, text-gray-*, bg-slate-*, text-slate-*
ALWAYS: bg-surface, bg-background, text-foreground, text-default-*
```

### 1.2 Typography

- **Font**: System default (HeroUI default stack)
- **Scale**: Tailwind standard (`text-xs` through `text-3xl`)
- **Weights**: `font-medium` (labels), `font-semibold` (headings), `font-bold` (display)

| Element | Classes | Example |
|---------|---------|---------|
| Page title | `text-3xl font-bold text-foreground` | "Welcome back, Marcelo!" |
| Section heading | `text-lg font-semibold text-foreground` | "Quick Actions" |
| Card label | `text-sm text-default-500` | "Total Contacts" |
| Card value | `text-3xl font-bold text-foreground` | "2,847" |
| Body text | `text-sm text-default-600` | Navigation items |
| Caption/hint | `text-xs text-default-400` | Timestamps, versions |
| Nav section label | `text-xs font-semibold text-default-400 uppercase tracking-wider` | "PRINCIPAL" |

### 1.3 Spacing

| Context | Value | Usage |
|---------|-------|-------|
| Page padding | `p-6` | Main content area |
| Card padding | `p-6` | Card.Content internals |
| Section gap | `gap-6` | Between cards/sections |
| Inner gap | `gap-4` | Between items in a card |
| Compact gap | `gap-2` | Between icon + text |
| Stack spacing | `space-y-6` | Vertical page sections |

### 1.4 Border Radius

| Element | Class | Token |
|---------|-------|-------|
| Cards | `rounded-xl` | 12px |
| Buttons | `rounded-lg` | 8px |
| Inputs | `rounded-lg` | 8px (via `--field-radius`) |
| Avatars | `rounded-full` | 50% |
| Icon containers | `rounded-xl` | 12px |
| Badges/chips | `rounded-full` | pill |
| Logo container | `rounded-lg` | 8px |

### 1.5 Shadows

| Context | Class | When |
|---------|-------|------|
| Cards default | none (border only) | Static cards |
| Cards hover | `hover:shadow-md` | Enhanced variant |
| Gradient card | `shadow-lg shadow-purple-500/20` | Brand CTA |
| Header | none (backdrop-blur instead) | Top bar |
| Modals | `shadow-2xl` | Overlay content |

---

## 2. Component Hierarchy

```
Level 1: ui/          HeroUI wrappers (Button, Card, InputField, etc.)
Level 3: shared/      Cross-feature (DataGrid, Pagination, etc.)
Level 3: features/    Domain-specific (StatCard, ActivityFeed, etc.)
Level 4: layouts/     Shell components (DashboardLayout, AuthLayout)
Level 5: pages/       Route components (Dashboard/Index, Auth/Login)
```

### Import Rules

```
ui       -> @heroui/react, lucide-react (external only)
shared   -> ui
features -> ui, shared (NEVER other features)
layouts  -> ui, shared
pages    -> ALL levels
```

---

## 3. Component Catalog

### 3.1 Button (ui/Button.tsx)

HeroUI Button wrapper with loading state and project variants.

| Variant | Appearance | Use |
|---------|-----------|-----|
| `primary` | Purple gradient + white text + shadow | Primary CTA |
| `secondary` | `bg-default-100` + dark text | Secondary actions |
| `outline` | Border + transparent bg | Tertiary actions |
| `ghost` | No border/bg, text only | Inline actions |
| `danger` | Red bg + white text + shadow | Destructive |

| Size | Height | Use |
|------|--------|-----|
| `sm` | `h-9` | Inline, compact |
| `md` | `h-11` | Default |
| `lg` | `h-12` | Hero CTA |

```tsx
<Button variant="primary" size="lg" isLoading={submitting}>
  Save Changes
</Button>
```

### 3.2 Card (HeroUI direct)

Use HeroUI Card compound directly. No wrapper needed.

```tsx
<Card className="border border-default-200">
  <Card.Header className="pb-0 px-6 pt-6">
    <h2 className="text-lg font-semibold text-foreground">Title</h2>
  </Card.Header>
  <Card.Content className="p-6">
    {/* content */}
  </Card.Content>
  <Card.Footer className="px-6 pb-6">
    {/* actions */}
  </Card.Footer>
</Card>
```

#### Card Variants (via className)

| Variant | Classes | Use |
|---------|---------|-----|
| Default | `border border-default-200` | Standard cards |
| Enhanced | `border border-default-200 hover:shadow-md hover:border-default-300` | Interactive cards |
| Gradient | `bg-gradient-primary text-white border-transparent shadow-lg shadow-purple-500/20` | Brand highlight |
| CTA | `border border-accent/20 bg-accent/5` | Getting started, promo |
| Modal | `border-0 shadow-2xl` | Dialog content |

### 3.3 StatCard (page sub-component)

Co-located in Dashboard/Index.tsx. Not extracted to separate file.

```tsx
// Default variant
<StatCard title="Leads" value="2,847" icon={Users} trend={{ value: "+24%", positive: true }} />

// Gradient variant (first card only)
<StatCard title="Campaigns" value="12" icon={Target} variant="gradient" />
```

Anatomy:
- Icon in `p-3 rounded-xl bg-primary/10` (or `bg-white/20` for gradient)
- Value: `text-3xl font-bold`
- Optional trend: `ArrowUpRight` green icon + percentage

### 3.4 Avatar (HeroUI direct)

```tsx
<Avatar size="sm">
  <Avatar.Fallback className="bg-gradient-primary text-white text-xs font-medium">
    {initials}
  </Avatar.Fallback>
</Avatar>
```

### 3.5 Chip (HeroUI direct)

```tsx
<Chip size="sm" color="warning" variant="soft">Soon</Chip>
<Chip size="sm" color="accent" variant="soft">Pro</Chip>
```

Available colors: `default`, `accent`, `success`, `warning`, `danger`

### 3.6 Dropdown (HeroUI compound)

```tsx
<Dropdown>
  <Dropdown.Trigger>
    <button>...</button>
  </Dropdown.Trigger>
  <Dropdown.Popover placement="bottom end">
    <Dropdown.Menu>
      <Dropdown.Item id="action" onAction={handler}>Label</Dropdown.Item>
    </Dropdown.Menu>
  </Dropdown.Popover>
</Dropdown>
```

---

## 4. Layout Patterns

### 4.1 Dashboard Layout

```
+--------+--------------------------------------------+
| Sidebar | Header (h-16, backdrop-blur)              |
| w-64    |-------------------------------------------|
| (or     | Flash Messages                            |
|  w-16   |-------------------------------------------|
| when    | Main Content (p-6, overflow-auto)          |
| collapsed)|                                          |
+--------+--------------------------------------------+
```

- Sidebar: `bg-background border-r border-divider`
- Header: `bg-background/95 backdrop-blur border-b border-divider`
- Content: `bg-default-50` (slightly tinted background)
- Transition: `transition-all duration-300`
- Mobile: overlay with `bg-black/50` backdrop

### 4.2 Auth Layout

Split-panel:
- Left: `bg-gradient-primary` with features list + stats
- Right: White/dark form card
- Mobile: form first (order-1), features below

### 4.3 Page Grid Patterns

```tsx
// Stats: 4 columns
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

// Main content: 7-column split (4+3)
<div className="grid grid-cols-1 lg:grid-cols-7 gap-6">
  <div className="lg:col-span-4">{/* primary */}</div>
  <div className="lg:col-span-3">{/* secondary */}</div>
</div>

// Equal columns
<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
```

---

## 5. Sidebar Navigation

### Active State

```tsx
// Active: gradient background + white text + left bar
className="bg-gradient-primary text-white shadow-sm"
// + absolute left-0 h-6 w-1 rounded-r-full bg-white/80

// Inactive
className="text-default-600 hover:bg-default-100 hover:text-foreground"
```

### Section Labels

```tsx
<p className="px-3 mb-2 text-xs font-semibold text-default-400 uppercase tracking-wider">
  Principal
</p>
```

### Badges

```tsx
<Chip size="sm" color="warning" variant="soft" className="text-[10px] h-5">
  Soon
</Chip>
```

### Collapsed Mode

- Width: `w-16` (64px)
- Icons centered, labels hidden
- `title` attribute for tooltip
- Logo: icon only (no text)
- Footer: logout icon only

---

## 6. Interaction Patterns

### Hover Effects

| Element | Effect |
|---------|--------|
| Cards (enhanced) | `hover:shadow-md hover:border-default-300` |
| Nav items | `hover:bg-default-100 hover:text-foreground` |
| Quick action items | `hover:border-primary/40 hover:bg-primary/5` |
| Activity feed items | `hover:bg-default-100` |
| Buttons (ghost) | `hover:bg-default-100` |

### Transitions

```
All interactive: transition-all duration-200
Sidebar collapse: transition-all duration-300
Animations: animate-fade-in (0.3s), animate-slide-up (0.3s), animate-scale-in (0.2s)
```

### Loading States

- Buttons: `<Spinner size="sm" color="current" />` + optional `loadingText`
- Forms: `isSubmitting` disables all inputs
- Pages: Inertia progress bar (purple `#6366f1`)

---

## 7. Empty States

Centered layout:
```tsx
<div className="text-center py-8">
  <div className="mx-auto w-16 h-16 rounded-2xl bg-default-100 flex items-center justify-center mb-4">
    <Icon className="h-8 w-8 text-default-300" />
  </div>
  <p className="text-default-500 font-medium">Title</p>
  <p className="text-sm text-default-400 mt-1">Description</p>
</div>
```

---

## 8. Flash Messages

Semantic colors with soft backgrounds:

```tsx
// Success
"p-3 bg-success/10 text-success-700 dark:text-success-400 rounded-xl border border-success/20"

// Error
"p-3 bg-danger/10 text-danger-700 dark:text-danger-400 rounded-xl border border-danger/20"

// Warning
"p-3 bg-warning/10 text-warning-700 dark:text-warning-400 rounded-xl border border-warning/20"

// Info
"p-3 bg-primary/10 text-primary-700 dark:text-primary-400 rounded-xl border border-primary/20"
```

---

## 9. Form Patterns

### 9.1 Always use `useAppForm`

```tsx
const { data, setData, submit, isSubmitting } = useAppForm({
  initialData: { email: '', password: '' },
  url: '/auth/login/',
  method: 'post',
})
```

### 9.2 Field Layout

```tsx
<div className="space-y-2">
  <label className="text-sm font-medium text-default-700">Label</label>
  <div className="relative">
    <Icon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
    <input className="w-full pl-10 h-11 rounded-lg border ..." />
  </div>
  {error && <p className="text-sm text-danger">{error}</p>}
</div>
```

### 9.3 Error Display

- Field errors: inline below field
- Form errors (`__all__`): banner above submit button
- Verification needed: amber banner with action link

---

## 10. Dark Mode

- Toggle: `document.documentElement.classList.toggle('dark')`
- Storage: `localStorage('launch-theme')`
- All tokens auto-switch via HeroUI's `.dark` class
- Custom gradient stays the same (works in both modes)
- Backgrounds: `bg-background` (light: near-white, dark: near-black)
- Surfaces: `bg-surface` (light: white, dark: dark gray)
- **Test every component in both modes**

---

## 11. Responsive Breakpoints

| Breakpoint | Width | Layout Change |
|-----------|-------|---------------|
| Default | < 768px | Single column, sidebar overlay |
| `md` | >= 768px | 2-column grids |
| `lg` | >= 1024px | Sidebar visible, 4-column stats, 7-col grid |
| `xl` | >= 1280px | User name visible in header |

---

## 12. Icons

- Library: **Lucide React** (`lucide-react`)
- Standard sizes:
  - Nav items: `h-5 w-5`
  - Card icons: `h-6 w-6`
  - Header controls: `h-5 w-5`
  - Inline (small): `h-4 w-4`
  - Empty state: `h-8 w-8` or `h-12 w-12`
  - Hero CTA: `h-8 w-8`

---

## 13. File Organization

```
frontends/dashboard/src/
├── components/
│   ├── ui/               # Level 1 - HeroUI wrappers
│   │   ├── Button.tsx
│   │   ├── Card.tsx      # Re-export if needed
│   │   ├── InputField.tsx
│   │   ├── PasswordInput.tsx
│   │   ├── FormErrorBanner.tsx
│   │   ├── ThemeToggle.tsx
│   │   ├── LanguageSelector.tsx
│   │   └── index.ts      # Barrel exports
│   ├── shared/            # Level 3 - Cross-feature
│   │   └── (future)
│   └── features/          # Level 3 - Domain-specific
│       └── (future)
├── hooks/
│   ├── useAppForm.ts      # Form wrapper (forceFormData)
│   └── useTheme.ts        # Theme management
├── layouts/
│   ├── DashboardLayout.tsx # Main app shell
│   ├── AuthLayout.tsx      # Auth pages shell
│   └── OnboardingLayout.tsx
├── pages/                  # Level 5 - Route components
│   ├── Auth/
│   ├── Dashboard/
│   ├── Contacts/
│   ├── Settings/
│   └── ...
├── styles/
│   └── globals.css         # Tokens + overrides + animations
├── types/
│   ├── index.ts            # Single source of truth
│   └── inertia.d.ts        # Page props augmentation
└── lib/
    └── i18n.ts
```

---

*Last updated: 2026-02*

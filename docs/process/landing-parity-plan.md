# LANDING PARITY PLAN — Paridade Visual com Legado

## Diagnóstico

O frontend landing atual foi construído com visual genérico/corporate (indigo, fundo claro, cards brancos).
O legado tem identidade **dark, vermelha, agressiva de marketing direto**.

Funcionalidade será adaptada ao Inertia+Django (config-driven, não hardcoded por variante).
Mas o visual DEVE replicar fielmente o legado.

---

## Fase V1 — Design System (fundação visual)

### V1.1 — Reescrever globals.css para match legado

**Arquivo:** `frontends/landing/src/styles/globals.css`

| Token atual | Legado | Ação |
|-------------|--------|------|
| `--color-brand-primary: #6366f1` (indigo) | `#E50914` / `#FB061A` (vermelho) | Trocar para vermelho |
| `--color-brand-secondary: #8b5cf6` (violet) | `#D4AF37` (gold) | Trocar para gold |
| `--color-surface: #ffffff` | `bg-black` / `bg-gray-900` | Dark por padrão |
| `--color-surface-dark: #0f172a` (slate) | `#000000` / `#0C0E1F` | Preto puro |
| `--color-text-primary: #0f172a` | `#ffffff` | Branco |
| Font Inter | Geist Sans / Roboto | Avaliar troca ou manter Inter |

Adicionar tokens que faltam:
- `--color-brand-gradient: linear-gradient(to right, #0e036b, #fb061a)` (gradient do CTA)
- `--color-surface-glass: rgba(31, 41, 55, 0.5)` (cards glassmorphism)
- `--color-border-glass: rgba(55, 65, 81, 1)` (border-gray-700)
- `--color-success-neon: #00FF00` (verde WhatsApp legado)

Adicionar animações que faltam:
- `shimmer` com diagonal stripes (progress bar legado)
- `wobble` (badge GRÁTIS)
- `pulse-glow` (botão WhatsApp)

### V1.2 — Carregar font Geist (ou decidir manter Inter)

Legado usa Geist Sans do Google Fonts. Se manter Inter, documentar a decisão.

---

## Fase V2 — Legal Pages (terms, privacy)

### V2.1 — Reescrever LegalLayout.tsx

De: fundo claro, card branco, texto escuro
Para: match exato do legado:

```
Background: bg-gradient-to-br from-gray-900 via-gray-800 to-black
Container: max-w-4xl (não max-w-3xl)
Título: text-3xl md:text-4xl font-bold text-white text-center
Card: bg-gray-800/50 backdrop-blur-sm rounded-lg border border-gray-700
Botão voltar: bg-green-600 hover:bg-green-700 text-white rounded-full (pill)
Texto body: text-gray-300 (não gray-700)
Section headings: text-lg font-semibold text-white (não text-base gray-900)
Footer: bg-transparent, text-gray-400
```

### V2.2 — Atualizar Section.tsx

De: `text-base font-semibold text-gray-900`
Para: `text-lg font-semibold text-white mb-2`

### V2.3 — Atualizar warning box no Terms.tsx

De: `border-red-200 bg-red-50` + `text-red-700`
Para: `bg-red-900/20 border border-red-600/50 rounded-lg` + `text-red-400`

---

## Fase V3 — Support Page (Chatwoot embedded)

### V3.1 — Reescrever ChatwootWidget para embed real

O legado **move fisicamente** o `.woot-widget-holder` para dentro do container via DOM manipulation.
O atual apenas faz `$chatwoot.toggle('open')` que abre o popup floating.

Implementar a mesma abordagem do legado:
1. Após `chatwoot:ready`, encontrar `.woot-widget-holder` no DOM
2. `appendChild` para mover dentro do container ref
3. Forçar styles: `position: absolute, inset: 0, width/height: 100%`
4. Iframe filho: `border-radius: 0 0 16px 16px`
5. Auto-reopen logic com MutationObserver (max 3 tentativas)
6. Minimized overlay com botão de reabrir

### V3.2 — Atualizar Support/Index.tsx visual

De: header genérico com back arrow
Para: match legado:
- Background layers: `bg-gradient-to-br from-zinc-900 via-black to-zinc-900` + radial red gradient overlay
- Header: título com gradient `from-red-500 to-amber-500 bg-clip-text text-transparent`
- Mobile: chat em cima (60vh), FAQ embaixo (50vh)
- Desktop: FAQ esquerda, Chat direita (grid-cols-2)
- Full viewport height (h-screen overflow-hidden)

### V3.3 — ChatHeader dentro do widget

Adicionar header customizado:
- Avatar "AA" com gradient `from-red-500 to-red-700`
- Status dot (green/yellow/red) conforme estado
- Título + subtitle do config

---

## Fase V4 — Capture Pages

### V4.1 — Reescrever CaptureLayout.tsx

De: dark slate (#0f172a) com card branco centralizado
Para: match legado:
- Background: suporte a imagem full-screen (passada via campaign JSON)
- Body color: `#0C0E1F` (deep dark blue)
- Content: left-aligned (não centralizado), max-w-[570px], ml offset para desktop

### V4.2 — Atualizar CaptureForm estilo

- Headline highlights: vermelho (#FB061A) ao invés de indigo
- CTA button: gradient `from-[#0e036b] to-[#fb061a]` (padrão, configurável via JSON)
- Badge pills: estilo legado (não indigo/10)

### V4.3 — Suporte a background image

Campaign JSON precisa de campo `background_image` (URL ou path).
Layout renderiza `<img>` ou `background-image` com overlay dark.

### V4.4 — Footer com modals (não links)

Legado abre Terms/Privacy em modais no footer, não navega para outra página.
Criar `<LegalModal>` component que renderiza o conteúdo inline.

---

## Fase V5 — Thank-You Pages

### V5.1 — RedBanner component

Criar: `bg-red-600 text-white py-6 text-center animate-pulse font-bold`
Texto: "NÃO FECHE ESTA PÁGINA ANTES DE ENTRAR NO GRUPO VIP..."

### V5.2 — Progress bar estilo legado

De: green/indigo simples
Para: match legado:
- Cor: gradient red `#dc2626 -> #ef4444 -> #dc2626`
- Shimmer: translateX animation sobre o fill
- Diagonal stripes: `repeating-linear-gradient(45deg, ...)` animado
- Percentual DENTRO da barra (não acima)
- Target: 90% (não 66%)
- Width: 80% do container (w-4/5), left-aligned

### V5.3 — WhatsApp CTA estilo legado

De: green-500 simples com pulse
Para: match legado:
- Gradient: `from-green-600 to-green-500`
- Rounded-full (pill shape)
- Badge "GRÁTIS": `bg-red-500` (não yellow) com wobble animation
- Pulse ring: green-500
- Security text: lock icon + "100% Seguro e Gratuito"
- Social proof: `bg-gray-800/30 rounded-lg` card
- Auto-redirect countdown (configurável)

### V5.4 — UrgencyHeadline component

Texto vermelho "NÃO FECHE" + verde "GRUPO VIP" + yellow subtitle pulsando.

### V5.5 — CompactHeader (fixed top banner)

Banner vermelho fixo no topo: `fixed top-0 bg-red-600 text-white h-12`

### V5.6 — Variantes via campaign JSON

Suporte a múltiplos layouts de thank-you configuráveis:
- `standard`: RedBanner + SimpleHeadline + ProgressBar + WhatsApp + Footer
- `with_video`: Two-column com vídeo YouTube
- `urgency`: UrgencyHeadline + CountdownTimer grande + WhatsApp
- `compact`: CompactHeader + ProgressIndicator + WhatsApp

---

## Fase V6 — Checkout Pages

### V6.1 — Reescrever CheckoutLayout para dark theme

De: white background clean
Para: match legado:
- Background: image (configurável) + dark overlay
- Marquee header scrolling (product name)
- Two-column layout: form esquerda, vídeos/testimonials direita

### V6.2 — Plan selector component

- Botões Annual/Lifetime com cores distintas (blue/gold)
- Dropdown de parcelas
- Addon card com badge de desconto
- Order summary

### V6.3 — Checkout videos/testimonials

Component para embed YouTube em coluna lateral.

---

## Fase V7 — Componentes Globais

### V7.1 — WhatsApp floating button

Botão fixo bottom-right (como no legado):
- Variants: default (red #E50914), amber, green
- Modo: `whatsapp` (abre wa.me) ou `chatwoot` (abre chat)
- Ping animation
- Tooltip após 10s
- Preload Chatwoot SDK on hover

### V7.2 — Footer component com legal modals

Footer dark com:
- Links que abrem modals (Terms/Privacy)
- Copyright "Mestre das Casas Baratas no EUA" (ou configurável)
- Facebook disclaimer
- Estilo: `bg-black/50 backdrop-blur-sm border-t border-gray-800`

---

## Fase V8 — Páginas Faltantes (após V1-V7)

Estas precisam de trabalho mais extenso:

| Página | Complexidade | Prioridade |
|--------|-------------|-----------|
| AgrelliFllix (hub + 4 aulas) | Alta (Netflix UI) | Fase F.2 |
| recado-importante (sales page 22 seções) | Alta | Fase F.3 |
| lembrete-bf (Black Friday reminder) | Média | Quando tiver campanha BF |
| lista-de-espera (waitlist) | Baixa | Quando necessário |
| onboarding post-compra | Média | Após checkout funcionar E2E |
| suporte-launch (vídeo bg) | Baixa | Se necessário |
| Black Friday variants | Média | Sazonal |

---

## Ordem de Execução Recomendada

```
V1 (Design System)     → Fundação visual, impacta tudo
V2 (Legal Pages)       → Fix mais rápido, visible immediately
V3 (Support Embed)     → Chatwoot embed real
V4 (Capture Pages)     → Funil principal
V5 (Thank-You)         → Pós-conversão
V6 (Checkout)          → Pagamento
V7 (Globais)           → WhatsApp button, footer
V8 (Páginas extras)    → AgrelliFllix, sales page, etc.
```

Estimativa total: V1-V7 = ~5-7 dias de trabalho. V8 = +3-5 dias dependendo do escopo.

---

## Princípios

1. **Visual = legado** (dark, red, marketing agressivo)
2. **Funcional = Inertia+Django** (config-driven, server-side routing, campaign JSON)
3. **Não hardcodar variantes** — 1 template + N configurações
4. **Campaign JSON** é a fonte de verdade para: cores, textos, imagens, layout variant
5. **Frontend-landing-pages/ permanece como referência** até V8 concluída

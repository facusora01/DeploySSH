# Frontend — Guía de diseño y arquitectura

Este documento explica **cómo escribimos el frontend de Appointa**. No es una guía aspiracional: describe lo que ya está construido y cómo se construye lo que viene. Si una nueva sección de la app sigue estas reglas, va a quedar consistente con lo que ya hay. Si no las sigue, va a chocar.

> Antes de pelearte con una convención: si tu cambio mejora algo, hablalo con el equipo y **actualizamos este documento**. Las reglas existen para ayudar, no para joder.

---

## Tabla de contenidos

1. [Stack y tooling](#1-stack-y-tooling)
2. [Estructura de carpetas](#2-estructura-de-carpetas)
3. [Sistema de colores y tokens](#3-sistema-de-colores-y-tokens)
4. [El archivo `index.css` completo](#4-el-archivo-indexcss-completo)
5. [Convenciones de CSS](#5-convenciones-de-css)
6. [El archivo `auth.css` como referencia](#6-el-archivo-authcss-como-referencia)
7. [Componentes reusables](#7-componentes-reusables)
8. [Estado global con Context API](#8-estado-global-con-context-api)
9. [Cliente API](#9-cliente-api)
10. [Routing](#10-routing)
11. [Anatomía de una pantalla](#11-anatomía-de-una-pantalla)
12. [TypeScript](#12-typescript)
13. [Accesibilidad](#13-accesibilidad)
14. [Estilo de código](#14-estilo-de-código)
15. [Patrones reusables — tabla](#15-patrones-reusables--tabla)
16. [Qué hacer si tu caso no entra](#16-qué-hacer-si-tu-caso-no-entra)

---

## 1. Stack y tooling

- **React 19** con **TypeScript**. Todo el código es `.tsx` o `.ts`, **nada en `.jsx` o `.js`**.
- **Vite** como bundler y dev server.
- **react-router-dom** para routing.
- **Context API** de React para estado global. No usamos Redux, Zustand, ni ninguna otra librería de estado.
- **CSS plano con variables** para estilos. No usamos Tailwind, ni styled-components, ni CSS-in-JS, ni CSS Modules.
- **`fetch` nativo** envuelto en un cliente propio (`src/utils/api.ts`). No usamos axios.

### Por qué nada de Tailwind

Ya tenemos un sistema de tokens centralizado (variables CSS). Tailwind reemplaza eso por clases utility distribuidas en el JSX. Mezclar los dos enfoques duplica la fuente de verdad de los colores y rompe la consistencia visual.

Si querés cambiar el accent, hay **un solo lugar** donde hacerlo (`index.css`), no quinientos `text-blue-500` regados por el codebase.

### Por qué Context API y no Zustand/Redux

El estado global del proyecto hoy es chico: el usuario logueado y los tokens. Una librería externa es overkill. Context + `useState` da exactamente lo que necesitamos sin agregar dependencias ni convenciones extra.

Si en el futuro el estado se vuelve complejo (filtros compartidos, caché de queries, etc.), entonces sí evaluamos algo más sofisticado. Pero no antes.

---

## 2. Estructura de carpetas

```
frontend/src/
├── components/             Componentes reusables (≥2 pantallas)
│   ├── AuthCard.tsx
│   ├── TextField.tsx
│   ├── ProtectedRoute.tsx
│   └── AuthBackground.tsx
├── context/                Context providers + hooks
│   └── AuthContext.tsx
├── pages/                  Pantallas (rutas)
│   ├── Login.tsx
│   ├── Register.tsx
│   ├── Home.tsx
│   └── auth.css            CSS de la feature "auth"
├── types/                  Tipos TypeScript compartidos
│   └── auth.ts
├── utils/                  Helpers no-React
│   └── api.ts
├── App.tsx                 Definición de rutas
├── main.tsx                Entry point, providers
└── index.css               Variables globales + reset
```

### Reglas para decidir dónde va un archivo

- **¿Es una pantalla a la que se llega por una ruta?** → `pages/`
- **¿Es un pedazo de UI usado por ≥2 pantallas?** → `components/`
- **¿Es un pedazo de UI usado por una sola pantalla y tiene <50 líneas?** → inline en la pantalla
- **¿Maneja estado global o lógica transversal?** → `context/`
- **¿Es código sin React (utilidades, clientes HTTP)?** → `utils/`
- **¿Es un tipo TypeScript usado en ≥2 archivos?** → `types/`

### Cuando una feature crezca

Cuando una feature tenga muchas pantallas y componentes específicos (ej. dashboard con 5 sub-pantallas, varios componentes propios), está OK promoverla a su propia carpeta:

```
src/features/dashboard/
├── components/
├── pages/
├── dashboard.css
└── types.ts
```

Mientras la feature sea chica (≤3 archivos), no compliques: dejá los archivos en las carpetas globales.

---

## 3. Sistema de colores y tokens

**Toda decisión visual reusable vive en `src/index.css` como una variable CSS.** Esta es la regla más importante del documento.

### Por qué importa tanto

Cuando el accent vive en una sola variable, cambiar la identidad visual de toda la app es **una línea**. Cuando el accent está hardcodeado en 80 archivos, cambiarlo es un día de search-and-replace con bugs garantizados.

### La paleta actual

Estos son los 4 colores base de los que sale todo:

| Color | Hex | Uso |
|---|---|---|
| Beige claro | `#F5EFE6` | Fondo de página |
| Beige cálido | `#E8DFCA` | Bordes y divisores |
| Azul medio | `#6D94C5` | Accent principal: botones, links, focus |
| Azul claro | `#CBDCEB` | Accent suave: hover, fondos seleccionados |

Sobre esos 4 colores construimos el resto de los tokens (texto, error, hover, etc.) con grises neutros y derivados.

### Reglas duras para usar colores

1. **No hardcodear hex codes en ningún archivo CSS que no sea `index.css`.** Si necesitás un color que no existe como variable, **primero lo agregás como variable**, después lo usás.

   ❌ Mal:
   ```css
   .my-component { background: #6D94C5; }
   ```
   ✅ Bien:
   ```css
   .my-component { background: var(--accent); }
   ```

2. **No hardcodear colores en JSX inline-style** tampoco. Si tenés que usar un color en un `style={{}}`, leelo de la variable:
   ```tsx
   style={{ background: "var(--accent)" }}
   ```

3. **Forzamos modo claro** (`color-scheme: light` en `:root`). No hay tema oscuro hoy. Si en el futuro se agrega, será una decisión consciente de producto, no algo que aparezca solo por el `prefers-color-scheme` del SO.

4. **Tokens organizados por sección** dentro de `:root`, con comentarios de header (`/* === Auth tokens === */`). Cuando agregues una sección nueva (ej. tokens para dashboard), agregás otro bloque con su comentario.

5. **Nombres descriptivos pero cortos**. `--accent-hover`, no `--button-primary-color-on-hover-state`.

---

## 4. El archivo `index.css` completo

Acá está el archivo entero. Esto es la fuente de verdad. Léelo entero antes de tocar nada.

```css
:root {
  /* === Paleta base === */
  --bg: #F5EFE6;             /* fondo de página (beige claro) */
  --surface: #ffffff;         /* fondo de cards sobre la página */
  --border: #E8DFCA;          /* bordes y divisores (beige cálido) */
  --code-bg: #E8DFCA;

  --text: #5a6478;            /* texto secundario */
  --text-h: #2c3340;          /* texto principal / títulos */

  --accent: #6D94C5;          /* azul medio: botones, links, focus */
  --accent-bg: #CBDCEB;       /* azul claro: hover/seleccionado suave */
  --accent-border: #6D94C5;

  /* === Auth tokens === */
  --accent-fg: #ffffff;       /* texto sobre accent */
  --accent-hover: #5a80b0;    /* accent más oscuro para hover */
  --muted: #9aa3b2;           /* placeholders */
  --input-bg: #ffffff;
  --error: #c0392b;
  --error-bg: rgba(192, 57, 43, 0.08);
  --radius: 10px;

  --shadow:
    rgba(44, 51, 64, 0.08) 0 10px 15px -3px,
    rgba(44, 51, 64, 0.04) 0 4px 6px -2px;

  --sans: system-ui, 'Segoe UI', Roboto, sans-serif;
  --heading: system-ui, 'Segoe UI', Roboto, sans-serif;
  --mono: ui-monospace, Consolas, monospace;

  font: 18px/145% var(--sans);
  letter-spacing: 0.18px;
  color-scheme: light;
  color: var(--text);
  background: var(--bg);
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;

  @media (max-width: 1024px) {
    font-size: 16px;
  }
}

#root {
  min-height: 100svh;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--bg);
}

h1, h2 {
  font-family: var(--heading);
  font-weight: 500;
  color: var(--text-h);
}

h1 {
  font-size: 56px;
  letter-spacing: -1.68px;
  margin: 32px 0;
  @media (max-width: 1024px) {
    font-size: 36px;
    margin: 20px 0;
  }
}

h2 {
  font-size: 24px;
  line-height: 118%;
  letter-spacing: -0.24px;
  margin: 0 0 8px;
  @media (max-width: 1024px) {
    font-size: 20px;
  }
}

p { margin: 0; }

code, .counter {
  font-family: var(--mono);
  display: inline-flex;
  border-radius: 4px;
  color: var(--text-h);
}

code {
  font-size: 15px;
  line-height: 135%;
  padding: 4px 8px;
  background: var(--code-bg);
}
```

### Cuándo agregar una variable nueva

- Si vas a usar el mismo valor en **≥2 lugares**: variable.
- Si es un valor "semántico" (un color, un radius, un shadow): variable, aunque lo uses una vez.
- Si es un valor puntual sin significado (ej: un `padding: 13px` específico de un componente): inline, no variable.

---

## 5. Convenciones de CSS

### Un archivo CSS por feature, no por componente

No hacemos `Login.module.css`, `TextField.module.css`, etc. Hacemos **un solo archivo CSS por feature** (`auth.css`, próximamente `dashboard.css`, etc.). Ese archivo se importa una vez desde la pantalla principal y todas las clases de la feature viven ahí.

Razón: con CSS plano (sin Modules), el namespace es global. En vez de pelearlo con tooling, lo aceptamos y prefijamos todas las clases con el nombre de la feature.

### Naming: prefijo de feature en cada clase

Todas las clases de una feature empiezan con el nombre de la feature seguido de guion:

- `.auth-page` — layout root
- `.auth-card` — el cuadrado central
- `.auth-form-group`, `.auth-input`, `.auth-label`, `.auth-submit`
- `.auth-error`
- `.auth-role-selector`, `.auth-role-option`

### Modificadores con `.is-*`

Para variantes de estado de un componente, usamos `.is-*` (no BEM puro):

```css
.auth-role-option.is-active { ... }
.auth-submit.is-loading { ... }
```

### Layout con `gap`, no con margins entre hijos

Los espacios entre elementos se manejan con `gap` (flex/grid), no con `margin-bottom` en cada hijo:

```css
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
```

Esto evita el típico "el último elemento tiene un margen sobrante que rompe el padding del padre".

### Transitions cortas y específicas

```css
/* ✅ */
transition: border-color 0.15s ease, box-shadow 0.15s ease;

/* ❌ */
transition: all 0.3s;
```

Especificá qué propiedad transiciona — performa mejor y deja claro qué se anima.

### Responsive: un breakpoint, no cinco

Solo usamos `@media (max-width: 480px)` para mobile, y eventualmente `(max-width: 1024px)` cuando hace falta. Nada de tablets/desktops grandes como caso especial. Si una pantalla necesita más, lo discutimos primero.

---

## 6. El archivo `auth.css` como referencia

Este archivo demuestra todas las convenciones en acción. Si tenés dudas sobre cómo estructurar el CSS de una feature nueva, copialo de acá.

```css
/* ============================================
   AUTH STYLES
   Todos los colores vienen de index.css.
   No hardcodear hex acá: si necesitás un color
   nuevo, agregalo allá.
============================================ */

/* --- Layout --- */
.auth-page {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  width: 100%;
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
}

.auth-container {
  width: 100%;
  max-width: 440px;
  position: relative;
  z-index: 1;
}

.auth-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 40px 32px;
  box-shadow: var(--shadow);
  box-sizing: border-box;
}

/* --- Header --- */
.auth-header { text-align: center; margin-bottom: 32px; }

.auth-logo {
  display: inline-block;
  font-family: var(--heading);
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 2px;
  color: var(--accent);
  text-decoration: none;
  margin-bottom: 24px;
}

.auth-title {
  font-size: 26px;
  font-weight: 600;
  color: var(--text-h);
  margin: 0 0 8px;
  letter-spacing: -0.3px;
}

.auth-subtitle {
  font-size: 15px;
  color: var(--text);
  margin: 0;
}

/* --- Form --- */
.auth-form { display: flex; flex-direction: column; gap: 18px; }
.auth-form-group { display: flex; flex-direction: column; gap: 6px; }

.auth-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-h);
}

.auth-input {
  width: 100%;
  padding: 11px 14px;
  font-family: inherit;
  font-size: 15px;
  color: var(--text-h);
  background: var(--input-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.auth-input::placeholder { color: var(--muted); }

.auth-input:focus {
  border-color: var(--accent-border);
  box-shadow: 0 0 0 3px var(--accent-bg);
}

/* --- Role selector (segmented control) --- */
.auth-role-selector { display: flex; gap: 8px; margin-top: 4px; }

.auth-role-option {
  flex: 1;
  padding: 11px 12px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.15s ease;
}

.auth-role-option:hover {
  border-color: var(--accent-border);
  color: var(--text-h);
}

.auth-role-option.is-active {
  background: var(--accent-bg);
  border-color: var(--accent-border);
  color: var(--accent);
}

/* --- Error --- */
.auth-error {
  padding: 10px 12px;
  font-size: 13px;
  color: var(--error);
  background: var(--error-bg);
  border: 1px solid var(--error);
  border-radius: var(--radius);
}

/* --- Submit button --- */
.auth-submit {
  width: 100%;
  padding: 12px 16px;
  font-family: inherit;
  font-size: 15px;
  font-weight: 600;
  color: var(--accent-fg);
  background: var(--accent);
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  transition: background 0.15s ease;
  margin-top: 6px;
}

.auth-submit:hover:not(:disabled) { background: var(--accent-hover); }
.auth-submit:disabled { opacity: 0.6; cursor: not-allowed; }

/* --- Footer --- */
.auth-footer { margin-top: 28px; text-align: center; }
.auth-footer-text { font-size: 14px; color: var(--text); }

.auth-footer-link {
  color: var(--accent);
  font-weight: 500;
  text-decoration: none;
}

.auth-footer-link:hover { text-decoration: underline; }

/* --- Responsive --- */
@media (max-width: 480px) {
  .auth-card { padding: 28px 20px; }
  .auth-title { font-size: 22px; }
}
```

### Qué tomar de este archivo para otras features

- La estructura: layout → header → contenido principal → componentes auxiliares → estados (error, loading) → responsive.
- El uso exclusivo de variables CSS para colores.
- Los selectores planos (`.auth-input:focus`, no `.auth-input[data-focused="true"]`).
- Las transiciones específicas y cortas.

---

## 7. Componentes reusables

### Criterio para componentizar

**Regla del "rule of three" relajado**: si una estructura de UI aparece en **2 pantallas con código idéntico**, abstraela a componente. Si aparece una sola vez, dejala inline.

Ejemplos del proyecto:

- `<TextField>`: el grupo label + input aparece 8 veces entre Login y Register → componente.
- `<AuthCard>`: el layout page + container + card + header + footer aparece en Login y Register → componente.
- **Selector de rol** en Register: ~15 líneas, se usa en una sola pantalla → **inline**, no componente.

### 7.1 `TextField`

Un input con label asociado. Hereda de los props nativos de `<input>` para que admita `type`, `placeholder`, `autoComplete`, `required`, `value`, `onChange`, etc., sin re-tipar nada.

**Ruta:** `src/components/TextField.tsx`

```tsx
import type { InputHTMLAttributes } from "react"

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  id: string // requerido para el htmlFor del label
}

function TextField({ label, id, ...inputProps }: TextFieldProps) {
  return (
    <div className="auth-form-group">
      <label htmlFor={id} className="auth-label">{label}</label>
      <input id={id} className="auth-input" {...inputProps} />
    </div>
  )
}

export default TextField
```

**Cómo usarlo:**

```tsx
<TextField
  id="email"
  label="Correo electrónico"
  type="email"
  required
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  placeholder="tu@email.com"
  autoComplete="email"
/>
```

**Decisión clave**: extender `InputHTMLAttributes<HTMLInputElement>` significa que cualquier prop válido de un `<input>` HTML funciona. No tenemos que andar agregando `type?: string`, `placeholder?: string`, etc. uno por uno.

### 7.2 `AuthCard`

Layout reusable para las pantallas de auth. Incluye logo, título, subtítulo y footer con link. Lo único variable es el contenido del medio (el form).

**Ruta:** `src/components/AuthCard.tsx`

```tsx
import type { ReactNode } from "react"
import { Link } from "react-router-dom"
import AuthBackground from "./AuthBackground"

interface AuthCardProps {
  title: string
  subtitle: string
  children: ReactNode
  footerText: string
  footerLinkLabel: string
  footerLinkTo: string
}

function AuthCard({
  title,
  subtitle,
  children,
  footerText,
  footerLinkLabel,
  footerLinkTo,
}: AuthCardProps) {
  return (
    <div className="auth-page">
      <AuthBackground />
      <div className="auth-container">
        <section className="auth-card">
          <header className="auth-header">
            <Link to="/" className="auth-logo">APPOINTA</Link>
            <h1 className="auth-title">{title}</h1>
            <p className="auth-subtitle">{subtitle}</p>
          </header>

          {children}

          <footer className="auth-footer">
            <p className="auth-footer-text">
              {footerText}{" "}
              <Link to={footerLinkTo} className="auth-footer-link">
                {footerLinkLabel}
              </Link>
            </p>
          </footer>
        </section>
      </div>
    </div>
  )
}

export default AuthCard
```

**Cómo usarlo:** ver sección [11. Anatomía de una pantalla](#11-anatomía-de-una-pantalla).

### 7.3 `ProtectedRoute`

Wrapper para rutas que requieren autenticación. Si no hay usuario logueado, redirige a `/login`. Mientras hidrata el usuario desde localStorage, no renderiza nada (evita un flash de redirect indebido cuando el usuario refresca la página estando logueado).

**Ruta:** `src/components/ProtectedRoute.tsx`

```tsx
import { Navigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import type { ReactNode } from "react"

interface ProtectedRouteProps {
  children: ReactNode
}

function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading } = useAuth()

  if (loading) return null
  if (!user) return <Navigate to="/login" replace />

  return <>{children}</>
}

export default ProtectedRoute
```

**Cómo usarlo:** en `App.tsx`, ver sección [10. Routing](#10-routing).

### 7.4 `AuthBackground` (opcional / decorativo)

Renderiza un shader WebGL animado de fondo en las pantallas de auth. Es decorativo, no funcional. Se monta dentro de `AuthCard`.

Si en algún momento querés sacarlo:
1. Borrá la línea `<AuthBackground />` en `AuthCard.tsx`.
2. Borrá el archivo `src/components/AuthBackground.tsx`.

Está aislado a propósito. No se acopla a nada del resto del flow.

### Cómo escribir un componente nuevo

Plantilla mínima:

```tsx
import type { ReactNode } from "react"

interface MyComponentProps {
  title: string
  children: ReactNode
}

function MyComponent({ title, children }: MyComponentProps) {
  return (
    <div className="feature-component">
      <h2 className="feature-component-title">{title}</h2>
      {children}
    </div>
  )
}

export default MyComponent
```

Reglas:
- **Default export** (un componente por archivo).
- **Interface para props**, no `type`.
- **Sufijo `Props`** en el nombre de la interface.
- **Clase CSS prefijada por feature** (`feature-component`, no `MyComponent`).

---

## 8. Estado global con Context API

### El `AuthContext`

Mantiene el usuario logueado, los tokens, y expone las funciones para login, register y logout. Vive en `src/context/AuthContext.tsx`.

```tsx
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react"
import {
  api,
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  setOnAuthFailure,
} from "../utils/api"
import type {
  AuthResponse,
  LoginPayload,
  RegisterPayload,
  User,
} from "../types/auth"

const USER_KEY = "appointa_user"

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (payload: LoginPayload) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Al montar, recuperar el usuario de localStorage si existía
  useEffect(() => {
    const stored = localStorage.getItem(USER_KEY)
    if (stored) {
      try {
        setUser(JSON.parse(stored) as User)
      } catch {
        localStorage.removeItem(USER_KEY)
      }
    }
    setLoading(false)
  }, [])

  // Si el API client detecta sesión muerta (refresh falló), limpiamos el user
  useEffect(() => {
    setOnAuthFailure(() => {
      localStorage.removeItem(USER_KEY)
      setUser(null)
    })
  }, [])

  function persistSession(data: AuthResponse) {
    localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token)
    localStorage.setItem(USER_KEY, JSON.stringify(data.user))
    setUser(data.user)
  }

  async function login(payload: LoginPayload) {
    const data = await api.post<AuthResponse>("/api/v1/auth/login", payload)
    persistSession(data)
  }

  async function register(payload: RegisterPayload) {
    const data = await api.post<AuthResponse>("/api/v1/auth/register", payload)
    persistSession(data)
  }

  async function logout() {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    if (refreshToken) {
      try {
        await api.post("/api/v1/auth/logout", { refresh_token: refreshToken })
      } catch {
        // Si falla, igual hacemos logout local
      }
    }
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>")
  return ctx
}
```

### Cómo consumirlo

```tsx
import { useAuth } from "../context/AuthContext"

function MyComponent() {
  const { user, logout } = useAuth()
  return <button onClick={logout}>Hola, {user?.full_name}</button>
}
```

### Cómo crear un contexto nuevo

Si más adelante hace falta otro contexto (ej. `NotificationsContext`), seguí este patrón:

1. **Una interface para el value del contexto** (`NotificationsContextValue`).
2. **`createContext<Value | undefined>(undefined)`** — usar `undefined` como default, no un objeto falso.
3. **Componente `XxxProvider`** que envuelve a sus children.
4. **Hook custom `useXxx()`** que hace `useContext` y tira error si está fuera del provider.
5. **Provider montado en `main.tsx`**, no enterrado en componentes.

### Cuándo NO usar contexto

- Estado local de un componente → `useState`.
- Estado compartido entre 2-3 componentes hermanos → lifting state up.
- Solo cuando es **transversal a la app** entra al contexto.

---

## 9. Cliente API

### Ubicación y uso básico

`src/utils/api.ts` exporta el objeto `api` con métodos `get` y `post`. Toda llamada al back pasa por ahí. **No** usar `fetch` directo en ningún componente.

```ts
import { api, ApiError } from "../utils/api"

// Pública (sin auth)
const data = await api.post<AuthResponse>("/api/v1/auth/login", payload)

// Autenticada (manda Bearer token automáticamente)
const turnos = await api.get<Turno[]>("/api/v1/turnos", true)
```

El segundo argumento `auth: boolean` indica si la request lleva el token de autorización.

### Manejo de errores

Las requests fallidas tiran `ApiError` con `status` y `message`. El `message` viene parseado del backend (Problem Details RFC 7807).

```ts
try {
  await api.post("/api/v1/auth/login", payload)
} catch (err) {
  if (err instanceof ApiError) {
    if (err.status === 401) setError("Credenciales inválidas.")
    else if (err.status === 409) setError("Email ya registrado.")
    else setError(err.message)
  }
}
```

**Distinguí por status code en la UI**, no parses el mensaje del backend para tomar decisiones. El mensaje puede cambiar; el status code es el contrato.

### Refresh automático

Si una request autenticada devuelve 401, el cliente **refresca el token automáticamente** y reintenta la request original. Si el refresh también falla, limpia el localStorage y dispara el callback de auth failure → el `AuthContext` setea `user = null` → `ProtectedRoute` redirige a login. Todo transparente para el componente que llamó al endpoint.

Hay deduplicación: si varias requests vencen al mismo tiempo, **una sola** hace el refresh y las demás esperan a ese mismo refresh.

### Variables de entorno

El cliente lee `VITE_API_URL` del `.env` del frontend. Default: `http://localhost:8000`.

**Ruta:** `frontend/.env`
```env
VITE_API_URL=http://localhost:8000
```

Vite solo expone al cliente variables que arrancan con `VITE_`. No metas secrets ahí.

---

## 10. Routing

### Setup

`src/main.tsx` envuelve la app con `<BrowserRouter>` y `<AuthProvider>`:

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
```

### Definición de rutas

`src/App.tsx`:

```tsx
import { Routes, Route, Navigate } from "react-router-dom"
import Login from "./pages/Login"
import Register from "./pages/Register"
import Home from "./pages/Home"
import ProtectedRoute from "./components/ProtectedRoute"

function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Home />
          </ProtectedRoute>
        }
      />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
```

### Reglas

- **Rutas públicas (login, register, recovery)**: directo como `<Route element={<Login />} />`.
- **Rutas privadas**: envueltas con `<ProtectedRoute>`.
- **Catch-all (`path="*"`)**: siempre el último, redirige a `/`.
- **No** repetir la lógica de redirect dentro de las páginas. `ProtectedRoute` hace eso.

---

## 11. Anatomía de una pantalla

Así se ve una pantalla de auth típica (Login). Replicá esta estructura cuando hagas pantallas nuevas.

**Ruta:** `src/pages/Login.tsx`

```tsx
import { useEffect, useState, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { ApiError } from "../utils/api"
import AuthCard from "../components/AuthCard"
import TextField from "../components/TextField"
import "./auth.css"

function Login() {
  const navigate = useNavigate()
  const { user, login } = useAuth()

  // Estado local del form
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  // Redirect si ya está logueado
  useEffect(() => {
    if (user) navigate("/", { replace: true })
  }, [user, navigate])

  // Submit handler
  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      await login({ email, password })
      navigate("/", { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        setError(
          err.status === 401
            ? "Credenciales inválidas."
            : err.message,
        )
      } else {
        setError("Ocurrió un error inesperado.")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthCard
      title="Bienvenido de nuevo"
      subtitle="Ingresá a tu cuenta para continuar"
      footerText="¿No tenés cuenta?"
      footerLinkLabel="Registrate gratis"
      footerLinkTo="/register"
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        <TextField
          id="email"
          label="Correo electrónico"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
        />
        <TextField
          id="password"
          label="Contraseña"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
        />

        {error && <div className="auth-error" role="alert">{error}</div>}

        <button type="submit" disabled={loading} className="auth-submit">
          {loading ? "Ingresando..." : "Iniciar sesión"}
        </button>
      </form>
    </AuthCard>
  )
}

export default Login
```

### Estructura general de una pantalla

1. **Imports** ordenados: React → librerías externas → internos → CSS.
2. **Hooks** al principio: `useNavigate`, `useAuth`, `useState`, `useEffect`.
3. **Efectos** declarativos: redirect-si-ya-logueado, etc.
4. **Handlers** (`handleSubmit`, `handleChange`, etc.) como funciones nombradas, no inline.
5. **JSX al final**, usando los componentes reusables.

### Validación de inputs en el cliente

Validá en cliente **antes** de pegarle al back, para dar feedback inmediato. Ejemplos del Register:

```tsx
if (password !== confirm) {
  setError("Las contraseñas no coinciden.")
  return
}
if (password.length < 8) {
  setError("La contraseña debe tener al menos 8 caracteres.")
  return
}
```

El back **igual va a re-validar todo**. La validación del cliente es UX, no seguridad.

---

## 12. TypeScript

### Tipos compartidos en `src/types/`

Si un tipo lo usa más de un archivo, va a `types/`. Si lo usa solo un archivo, lo declarás en el mismo archivo.

Ejemplo: `src/types/auth.ts`

```ts
export type UserRole = "client" | "profesional"

export interface User {
  id: number
  email: string
  full_name: string
  role: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  role: UserRole
  full_name: string
  email: string
  phone: string
  password: string
  specialty?: string
}
```

### Interface vs type

- **`interface`** para props de componentes y shapes de objetos.
- **`type`** para uniones discriminadas, primitivos, intersecciones y mapeos.

```tsx
// ✅ interface
interface AuthCardProps {
  title: string
  children: ReactNode
}

// ✅ type
type UserRole = "client" | "profesional"
type Status = "idle" | "loading" | "success" | "error"
```

### Prohibido: `any`

Si no sabés cómo tipar algo, preguntá o usá `unknown` con narrowing. `any` desactiva el typechecker y derrota el propósito de usar TS.

### Importar tipos con `import type`

```ts
import type { User, AuthResponse } from "../types/auth"
```

Ayuda al bundler a tree-shakear y comunica intención.

### Tipar eventos

```tsx
import type { FormEvent, ChangeEvent } from "react"

function handleSubmit(e: FormEvent<HTMLFormElement>) { ... }
function handleChange(e: ChangeEvent<HTMLInputElement>) { ... }
```

---

## 13. Accesibilidad

### Mínimos no negociables

- **Todos los `<input>` tienen `<label htmlFor>`**. El componente `TextField` ya lo garantiza; usalo siempre.
- **Mensajes de error con `role="alert"`** para que lectores de pantalla los lean cuando aparecen:
  ```tsx
  <div className="auth-error" role="alert">{error}</div>
  ```
- **Estados que no son inputs nativos llevan `role` y `aria-*`**. Ejemplo del role selector:
  ```tsx
  <div role="radiogroup">
    <button
      role="radio"
      aria-checked={role === "client"}
      onClick={() => setRole("client")}
    >Como cliente</button>
  </div>
  ```
- **Elementos decorativos llevan `aria-hidden="true"`** (canvas del shader, iconos puramente decorativos).
- **Animaciones respetan `prefers-reduced-motion`**:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .my-animation { animation: none; }
  }
  ```
- **Inputs con `autoComplete` apropiado** (`email`, `current-password`, `new-password`, `tel`, `name`). Mejora UX y a veces es requerido para que los password managers funcionen.

### Contraste

Los colores de la paleta están elegidos para tener contraste suficiente texto/fondo. Si agregás un color nuevo, chequealo en [webaim.org/resources/contrastchecker](https://webaim.org/resources/contrastchecker/). Mínimo AA (4.5:1 para texto normal, 3:1 para texto grande).

---

## 14. Estilo de código

- **PascalCase** para componentes y tipos: `AuthCard`, `UserRole`, `LoginPayload`.
- **camelCase** para variables, funciones, props y métodos: `handleSubmit`, `fullName`, `onLogin`.
- **kebab-case** para clases CSS: `.auth-form-group`, `.is-active`.
- **SCREAMING_SNAKE_CASE** para constantes módulo-level: `const ACCESS_TOKEN_KEY = "..."`.
- **Comillas dobles** en JSX (`className="auth-card"`), consistente por archivo en JS/TS.
- **No `;` al final de cada línea** (estilo "ASI"). Sí cuando es ambiguo (líneas que arrancan con `(`, `[`).
- **Imports ordenados**: librerías externas → módulos internos → CSS al final.

```tsx
// ✅ Ejemplo de imports ordenados
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { api } from "../utils/api"
import AuthCard from "../components/AuthCard"
import "./auth.css"
```

### Handlers como funciones nombradas

```tsx
// ✅
async function handleSubmit(e: FormEvent) { ... }
<form onSubmit={handleSubmit}>

// ❌
<form onSubmit={async (e) => { ... }}>
```

Excepción: handlers de una sola línea (`onClick={() => setOpen(true)}`).

### Comentarios

Comentá el **por qué**, no el **qué**. El código ya dice qué hace.

```ts
// ✅ explica una decisión no-obvia
// Si varias requests vencen al mismo tiempo, hacemos una sola llamada
// de refresh y todas esperan ese mismo refresh.
let refreshInFlight: Promise<string> | null = null

// ❌ redundante
// Variable que guarda el refresh en vuelo
let refreshInFlight: Promise<string> | null = null
```

---

## 15. Patrones reusables — tabla

Antes de armar algo nuevo, fijate si ya está:

| Necesitás... | Usá... |
|---|---|
| Un input con label | `<TextField>` |
| Layout de pantalla de auth | `<AuthCard>` |
| Proteger una ruta | `<ProtectedRoute>` |
| Saber si hay usuario logueado | `useAuth().user` |
| Hacer login / register / logout | `useAuth().login()`, etc. |
| Llamar al backend | `api.get()` / `api.post()` |
| Tipos de usuario / auth | `import type { ... } from "../types/auth"` |
| Colores, radius, fonts | variables `--*` en `index.css` |
| Navegar programáticamente | `const navigate = useNavigate()` |
| Link declarativo | `<Link to="/ruta">` (react-router-dom) |
| Mostrar un error de form | `<div className="auth-error" role="alert">` |
| Botón principal de un form | `<button className="auth-submit">` |

---

## 16. Qué hacer si tu caso no entra

1. **Buscá si hay un patrón existente** que aplique con un ajuste menor. La mayoría de las veces, hay.
2. Si no, **preguntá antes de inventar**. La consistencia vale más que tu preferencia personal.
3. Si decidís agregar un patrón nuevo, **documentalo en este archivo**. Este documento se actualiza con el código, no aparte.

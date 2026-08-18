// Cliente HTTP único pra falar com a API Django (DRF). Sessão + CSRF, sem
// JWT — o cookie de sessão já autentica (credentials: 'include'), só falta
// mandar o token CSRF (lido do cookie `csrftoken`) em toda request que
// muda estado (POST/PUT/PATCH/DELETE), exigido pelo CsrfViewMiddleware.
//
// Em dev, front e back são "mesma origem" (Vite faz proxy de /api pro
// Django em :8000), então dá pra ler o cookie csrftoken direto via
// document.cookie. Em produção, front (Vercel) e back (Render) são
// domínios de verdade diferentes — JS de um domínio não consegue ler
// cookie setado pelo outro, então o token vem também no corpo da resposta
// de /auth/me/ (campo `csrfToken`, ver core/api_views.py::MeAPIView) e fica
// cacheado em memória aqui como fallback.

export const API_BASE = import.meta.env.VITE_API_URL || '/api'

let csrfTokenEmMemoria = null

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`))
  return match ? decodeURIComponent(match[2]) : null
}

const METODOS_SEM_CSRF = new Set(['GET', 'HEAD', 'OPTIONS'])

async function request(path, { method = 'GET', body } = {}) {
  const headers = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (!METODOS_SEM_CSRF.has(method)) {
    const csrftoken = getCookie('csrftoken') || csrfTokenEmMemoria
    if (csrftoken) headers['X-CSRFToken'] = csrftoken
  }

  const resp = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    credentials: 'include',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (resp.status === 204) return null

  const isJson = resp.headers.get('content-type')?.includes('application/json')
  const data = isJson ? await resp.json() : null

  if (data?.csrfToken) csrfTokenEmMemoria = data.csrfToken

  if (!resp.ok) {
    const erro = new Error(data?.detail || `Erro ${resp.status} em ${path}`)
    erro.status = resp.status
    erro.data = data
    throw erro
  }
  return data
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body }),
  put: (path, body) => request(path, { method: 'PUT', body }),
  patch: (path, body) => request(path, { method: 'PATCH', body }),
  delete: (path) => request(path, { method: 'DELETE' }),
}

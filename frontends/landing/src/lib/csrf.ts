/**
 * CSRF token utilities for landing page fetch() calls.
 *
 * Django sets the CSRF token in a cookie named "XSRF-TOKEN" (CSRF_COOKIE_HTTPONLY=False).
 * For Inertia requests, Axios reads this automatically. But for raw fetch() calls
 * (used by Stripe checkout JSON endpoints), we need to read it manually.
 */

/**
 * Read the XSRF-TOKEN cookie value.
 * Returns empty string if cookie is not found.
 */
export function getCsrfToken(): string {
  const name = 'XSRF-TOKEN';
  const cookies = document.cookie.split(';');

  for (const cookie of cookies) {
    const trimmed = cookie.trim();
    if (trimmed.startsWith(`${name}=`)) {
      return decodeURIComponent(trimmed.substring(name.length + 1));
    }
  }

  return '';
}

/**
 * Make a fetch() call with CSRF token included.
 * Convenience wrapper for POST requests to Django JSON endpoints.
 */
export async function csrfFetch(
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  const csrfToken = getCsrfToken();

  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');

  if (csrfToken) {
    headers.set('X-XSRF-TOKEN', csrfToken);
  }

  return fetch(url, {
    ...options,
    headers,
    credentials: 'same-origin',
  });
}

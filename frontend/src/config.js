function normalizeBaseUrl(url) {
  return url.trim().replace(/\/+$/, '');
}

const envUrl = import.meta.env.VITE_API_BASE_URL;

if (import.meta.env.PROD && !envUrl) {
  console.error(
    'VITE_API_BASE_URL is not configured. Set it in your Vercel project environment variables and redeploy.'
  );
}

// Local default uses 8001 to avoid common port-8000 conflicts with other dev servers.
export const API_BASE_URL = normalizeBaseUrl(
  envUrl || (import.meta.env.DEV ? 'http://localhost:8001' : '')
);

/** Join base URL and route path without double slashes or missing slashes. */
export function apiUrl(path) {
  const route = path.startsWith('/') ? path : `/${path}`;
  if (!API_BASE_URL) {
    return route;
  }
  return `${API_BASE_URL}${route}`;
}

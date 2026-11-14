function getApiBaseUrl() {
  const configuredUrl = import.meta.env.VITE_API_BASE_URL?.trim();
  if (configuredUrl) return configuredUrl.replace(/\/$/, '');
  if (import.meta.env.DEV) return 'http://localhost:8000';
  throw new Error('VITE_API_BASE_URL is not configured for this deployment.');
}

async function handleResponse(response) {
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();

  if (!response.ok) {
    const detail = payload?.detail;
    const message = typeof payload === 'string'
      ? payload
      : Array.isArray(detail)
        ? detail.map((issue) => issue.msg || 'Invalid input').join('; ')
        : detail || 'Request failed';
    throw new Error(message);
  }

  return payload;
}

export async function apiPost(path, body) {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return handleResponse(response);
}

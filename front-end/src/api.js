const API_BASE = "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    try {
      const data = await response.json();
      message = Object.entries(data)
        .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : typeof value === "string" ? value : JSON.stringify(value)}`)
        .join(" | ") || message;
    } catch {
      // Mantém a mensagem HTTP quando a resposta não é JSON.
    }
    throw new Error(message);
  }

  return response.status === 204 ? null : response.json();
}

function getCsrfCookie() {
  const entry = document.cookie.split("; ").find((item) => item.startsWith("csrftoken="));
  return entry ? decodeURIComponent(entry.slice("csrftoken=".length)) : "";
}

export const api = {
  dashboard: () => request("/dashboard/"),
  ocorrencias: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && String(value).trim() !== "") query.set(key, value);
    });
    return request(`/ocorrencias/${query.size ? `?${query.toString()}` : ""}`);
  },
  sessaoAdmin: () => request("/acesso-admin/session/"),
  csrfAdmin: () => request("/acesso-admin/csrf/"),
  entrarAdmin: async (username, password) => {
    await request("/acesso-admin/csrf/");
    return request("/acesso-admin/login/", {
      method: "POST", headers: { "X-CSRFToken": getCsrfCookie() },
      body: JSON.stringify({ username, password }),
    });
  },
  sairAdmin: () => request("/acesso-admin/logout/", {
    method: "POST", headers: { "X-CSRFToken": getCsrfCookie() },
    body: JSON.stringify({}),
  }),
  atualizarOcorrencia: (id, values) => request(`/acesso-admin/ocorrencias/${id}/`, {
    method: "PATCH", headers: { "X-CSRFToken": getCsrfCookie() },
    body: JSON.stringify(values),
  }),
  criarOcorrencia: (data) =>
    request("/ocorrencias/", { method: "POST", body: JSON.stringify(data) }),
};

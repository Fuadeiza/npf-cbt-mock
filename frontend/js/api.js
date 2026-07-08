// Thin wrapper over the backend HTTP API. Same-origin, so no base URL needed.

async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body.detail) detail = body.detail;
    } catch (_) {
      /* keep default */
    }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  listModes: () => request("/api/modes"),

  startAttempt: (candidateName, mode) =>
    request("/api/attempts", {
      method: "POST",
      body: JSON.stringify({ candidate_name: candidateName, mode }),
    }),

  submitAttempt: (attemptId, answers) =>
    request(`/api/attempts/${attemptId}/submit`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    }),
};

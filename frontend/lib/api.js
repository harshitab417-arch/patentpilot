const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

async function parseApiError(response) {
  const errorData = await response.json().catch(() => null);
  return errorData?.detail || `Request failed (${response.status})`;
}

export async function submitAnalysis(data) {
  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const message = await parseApiError(response);
    throw new Error(message);
  }

  return response.json();
}

export async function getJobStatus(jobId) {
  const response = await fetch(`${API_BASE}/api/job-status/${jobId}`, {
    cache: 'no-store',
  });

  if (!response.ok) {
    const message = await parseApiError(response);
    throw new Error(message);
  }

  return response.json();
}

export async function getAnalysis(id) {
  const response = await fetch(`${API_BASE}/api/analyses/${id}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Analysis not found');
    }
    const message = await parseApiError(response);
    throw new Error(message);
  }

  return response.json();
}

export async function listAnalyses() {
  const response = await fetch(`${API_BASE}/api/analyses`, { cache: 'no-store' });

  if (!response.ok) {
    const message = await parseApiError(response);
    throw new Error(message);
  }

  return response.json();
}

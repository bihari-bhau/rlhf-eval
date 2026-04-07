const base = import.meta.env.VITE_API_URL ?? ''

function apiReachableError(): Error {
  return new Error(
    'API unreachable. Start the FastAPI server on port 8000 (from the backend folder: `uvicorn app.main:app --reload`). PostgreSQL must be running and migrations applied (`alembic upgrade head`).'
  )
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  let r: Response
  try {
    r = await fetch(`${base}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers ?? {}),
      },
    })
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    if (
      msg.includes('Failed to fetch') ||
      msg.includes('NetworkError') ||
      msg.toLowerCase().includes('load failed')
    ) {
      throw apiReachableError()
    }
    throw e instanceof Error ? e : new Error(msg)
  }
  if (!r.ok) {
    const t = await r.text()
    throw new Error(t || r.statusText)
  }
  if (r.status === 204) return undefined as T
  return r.json() as Promise<T>
}

export const api = {
  health: () => req<{ status: string }>('/api/health'),
  listRepos: () => req<Repo[]>('/api/repos'),
  createRepo: (github_url: string) =>
    req<Repo>('/api/repos', { method: 'POST', body: JSON.stringify({ github_url }) }),
  getRepo: (id: string) => req<RepoDetail>(`/api/repos/${id}`),
  deleteRepo: (id: string) => req<void>(`/api/repos/${id}`, { method: 'DELETE' }),
  runEval: (id: string) => req<Evaluation>(`/api/evaluations/repos/${id}/run`, { method: 'POST' }),
  runEvalAsync: (id: string) => req<Evaluation>(`/api/evaluations/repos/${id}/run-async`, { method: 'POST' }),
  putOverride: (repoId: string, dim: string, human_score: number) =>
    req<HumanOverride>(`/api/repos/${repoId}/overrides/${dim}`, {
      method: 'PUT',
      body: JSON.stringify({ human_score }),
    }),
  putStars: (repoId: string, stars: number) =>
    req<StarRating>(`/api/repos/${repoId}/stars`, { method: 'PUT', body: JSON.stringify({ stars }) }),
  addComment: (repoId: string, body: string) =>
    req<Comment>(`/api/repos/${repoId}/comments`, { method: 'POST', body: JSON.stringify({ body }) }),
  listComparisons: () => req<Comparison[]>('/api/comparisons'),
  createComparison: (body: {
    repo_a_id: string
    repo_b_id: string
    preferred_repo_id?: string | null
    notes?: string | null
  }) => req<Comparison>('/api/comparisons', { method: 'POST', body: JSON.stringify(body) }),
  exportJsonl: async () => {
    let r: Response
    try {
      r = await fetch(`${base}/api/export/jsonl`)
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
        throw apiReachableError()
      }
      throw e instanceof Error ? e : new Error(msg)
    }
    if (!r.ok) throw new Error(await r.text())
    return r.blob()
  },
}

export interface Repo {
  id: string
  github_url: string
  full_name: string
  local_path: string | null
  created_at: string
}

export interface DimensionScore {
  dimension_code: string
  automated_score: number
  detail: string | null
}

export interface Evaluation {
  id: string
  repo_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  error_message: string | null
  created_at: string
  completed_at: string | null
  dimension_scores: DimensionScore[]
}

export interface HumanOverride {
  id: string
  repo_id: string
  dimension_code: string
  human_score: number
  updated_at: string
}

export interface StarRating {
  id: string
  repo_id: string
  stars: number
  updated_at: string
}

export interface Comment {
  id: string
  repo_id: string
  body: string
  created_at: string
}

export interface RepoDetail extends Repo {
  latest_evaluation: Evaluation | null
  overrides: HumanOverride[]
  star_rating: StarRating | null
  comments: Comment[]
}

export interface Comparison {
  id: string
  repo_a_id: string
  repo_b_id: string
  preferred_repo_id: string | null
  notes: string | null
  created_at: string
}

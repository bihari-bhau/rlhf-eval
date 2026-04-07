import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Repo } from '../api'

export function RepoList() {
  const [repos, setRepos] = useState<Repo[]>([])
  const [url, setUrl] = useState('')
  const [err, setErr] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    setErr(null)
    try {
      setRepos(await api.listRepos())
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load repos')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function addRepo(e: React.FormEvent) {
    e.preventDefault()
    setErr(null)
    try {
      await api.createRepo(url)
      setUrl('')
      await load()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to add repo')
    }
  }

  if (loading) {
    return <p className="text-slate-500">Loading…</p>
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-white mb-2">Repositories</h1>
        <p className="text-slate-400 text-sm max-w-xl">
          Add a GitHub URL to clone and score against nine datasheet dimensions (D1–D9). Run automated checks,
          then override scores, rate, and comment for RLHF export.
        </p>
      </div>

      <form onSubmit={addRepo} className="flex flex-col sm:flex-row gap-2 max-w-2xl">
        <input
          type="url"
          required
          placeholder="https://github.com/owner/repo"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="flex-1 rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
        />
        <button
          type="submit"
          className="rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium px-4 py-2"
        >
          Add repo
        </button>
      </form>

      {err && <p className="text-red-400 text-sm">{err}</p>}

      <ul className="divide-y divide-slate-800 rounded-xl border border-slate-800 overflow-hidden">
        {repos.length === 0 && (
          <li className="px-4 py-8 text-center text-slate-500 text-sm">No repos yet.</li>
        )}
        {repos.map((r) => (
          <li key={r.id}>
            <Link
              to={`/repos/${r.id}`}
              className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-slate-900/50 transition-colors"
            >
              <span className="font-mono text-sm text-violet-200">{r.full_name}</span>
              <span className="text-xs text-slate-500 truncate max-w-[50%]">{r.github_url}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Comparison, type Repo } from '../api'

export function Compare() {
  const [repos, setRepos] = useState<Repo[]>([])
  const [comparisons, setComparisons] = useState<Comparison[]>([])
  const [a, setA] = useState('')
  const [b, setB] = useState('')
  const [pref, setPref] = useState<'A' | 'B' | ''>('')
  const [notes, setNotes] = useState('')
  const [err, setErr] = useState<string | null>(null)

  async function load() {
    setErr(null)
    try {
      const [r, c] = await Promise.all([api.listRepos(), api.listComparisons()])
      setRepos(r)
      setComparisons(c)
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Load failed')
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!a || !b || a === b) {
      setErr('Pick two different repos')
      return
    }
    setErr(null)
    try {
      let preferred_repo_id: string | null = null
      if (pref === 'A') preferred_repo_id = a
      if (pref === 'B') preferred_repo_id = b
      await api.createComparison({
        repo_a_id: a,
        repo_b_id: b,
        preferred_repo_id,
        notes: notes.trim() || null,
      })
      setNotes('')
      setPref('')
      await load()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Save failed')
    }
  }

  function nameFor(id: string) {
    return repos.find((r) => r.id === id)?.full_name ?? id.slice(0, 8)
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-white mb-2">Compare A vs B</h1>
        <p className="text-slate-400 text-sm max-w-xl">
          Record pairwise preferences for RLHF. Exported JSONL includes <code className="text-violet-300">record_type: pairwise_comparison</code>{' '}
          rows alongside per-repo evaluations.
        </p>
      </div>

      <form onSubmit={submit} className="space-y-4 max-w-xl">
        <div className="grid sm:grid-cols-2 gap-4">
          <label className="block text-sm">
            <span className="text-slate-400">Repo A</span>
            <select
              value={a}
              onChange={(e) => setA(e.target.value)}
              className="mt-1 w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-white"
            >
              <option value="">Select…</option>
              {repos.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.full_name}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="text-slate-400">Repo B</span>
            <select
              value={b}
              onChange={(e) => setB(e.target.value)}
              className="mt-1 w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-white"
            >
              <option value="">Select…</option>
              {repos.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.full_name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <fieldset className="text-sm">
          <legend className="text-slate-400 mb-2">Preference (optional)</legend>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="radio" name="pref" checked={pref === 'A'} onChange={() => setPref('A')} />
              <span>Prefer A</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="radio" name="pref" checked={pref === 'B'} onChange={() => setPref('B')} />
              <span>Prefer B</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="radio" name="pref" checked={pref === ''} onChange={() => setPref('')} />
              <span>No preference</span>
            </label>
          </div>
        </fieldset>
        <label className="block text-sm">
          <span className="text-slate-400">Notes</span>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={2}
            className="mt-1 w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-white"
          />
        </label>
        {err && <p className="text-red-400 text-sm">{err}</p>}
        <button
          type="submit"
          className="rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium px-4 py-2"
        >
          Save comparison
        </button>
      </form>

      <section>
        <h2 className="text-lg font-medium text-white mb-3">History</h2>
        <ul className="space-y-2">
          {comparisons.length === 0 && <li className="text-slate-500 text-sm">No comparisons yet.</li>}
          {comparisons.map((c) => (
            <li
              key={c.id}
              className="rounded-lg border border-slate-800 bg-slate-900/40 px-3 py-2 text-sm flex flex-wrap items-baseline gap-x-3 gap-y-1"
            >
              <Link to={`/repos/${c.repo_a_id}`} className="font-mono text-violet-300 hover:underline">
                {nameFor(c.repo_a_id)}
              </Link>
              <span className="text-slate-500">vs</span>
              <Link to={`/repos/${c.repo_b_id}`} className="font-mono text-violet-300 hover:underline">
                {nameFor(c.repo_b_id)}
              </Link>
              {c.preferred_repo_id && (
                <span className="text-emerald-400">
                  → preferred: {c.preferred_repo_id === c.repo_a_id ? 'A' : 'B'}
                </span>
              )}
              {c.notes && <span className="text-slate-400 w-full">{c.notes}</span>}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

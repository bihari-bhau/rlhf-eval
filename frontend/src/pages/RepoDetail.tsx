import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type RepoDetail } from '../api'
import { DIMENSIONS } from '../dimensions'

export function RepoDetail() {
  const { id } = useParams<{ id: string }>()
  const [data, setData] = useState<RepoDetail | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [comment, setComment] = useState('')
  const [overrideDrafts, setOverrideDrafts] = useState<Record<string, string>>({})

  const load = useCallback(async () => {
    if (!id) return
    setErr(null)
    try {
      const d = await api.getRepo(id)
      setData(d)
      const drafts: Record<string, string> = {}
      for (const o of d.overrides) {
        drafts[o.dimension_code] = String(o.human_score)
      }
      setOverrideDrafts(drafts)
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Load failed')
    }
  }, [id])

  useEffect(() => {
    load()
  }, [load])

  async function runEval() {
    if (!id) return
    setBusy(true)
    setErr(null)
    try {
      await api.runEval(id)
      await load()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Evaluation failed')
    } finally {
      setBusy(false)
    }
  }

  async function saveOverride(dim: string) {
    if (!id) return
    const raw = overrideDrafts[dim]
    const v = parseFloat(raw)
    if (Number.isNaN(v) || v < 0 || v > 1) {
      setErr('Overrides must be numbers between 0 and 1')
      return
    }
    setBusy(true)
    setErr(null)
    try {
      await api.putOverride(id, dim, v)
      await load()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setBusy(false)
    }
  }

  async function saveStars(stars: number) {
    if (!id) return
    setBusy(true)
    setErr(null)
    try {
      await api.putStars(id, stars)
      await load()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Stars failed')
    } finally {
      setBusy(false)
    }
  }

  async function submitComment(e: React.FormEvent) {
    e.preventDefault()
    if (!id || !comment.trim()) return
    setBusy(true)
    setErr(null)
    try {
      await api.addComment(id, comment.trim())
      setComment('')
      await load()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Comment failed')
    } finally {
      setBusy(false)
    }
  }

  if (!id) return null
  if (!data) {
    return <p className="text-slate-500">{err ?? 'Loading…'}</p>
  }

  const ev = data.latest_evaluation
  const scores = new Map((ev?.dimension_scores ?? []).map((s) => [s.dimension_code, s]))
  const overrideByDim = new Map(data.overrides.map((o) => [o.dimension_code, o.human_score]))

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <Link to="/" className="text-sm text-slate-500 hover:text-violet-300">
            ← Repos
          </Link>
          <h1 className="text-2xl font-semibold text-white mt-2 font-mono">{data.full_name}</h1>
          <a
            href={data.github_url}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-violet-400 hover:underline break-all"
          >
            {data.github_url}
          </a>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={runEval}
          className="shrink-0 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-medium px-4 py-2"
        >
          {busy ? 'Working…' : 'Run automated evaluation'}
        </button>
      </div>

      {err && <p className="text-red-400 text-sm">{err}</p>}

      {ev && (
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-3 text-sm">
          <span className="text-slate-400">Latest run: </span>
          <span
            className={
              ev.status === 'completed'
                ? 'text-emerald-400'
                : ev.status === 'failed'
                  ? 'text-red-400'
                  : 'text-amber-400'
            }
          >
            {ev.status}
          </span>
          {ev.error_message && <p className="text-red-300 mt-2 whitespace-pre-wrap">{ev.error_message}</p>}
        </div>
      )}

      <section>
        <h2 className="text-lg font-medium text-white mb-4">Dimensions (0–1)</h2>
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-900/80 text-left text-slate-400">
                <th className="px-3 py-2">Dim</th>
                <th className="px-3 py-2">Label</th>
                <th className="px-3 py-2">Auto</th>
                <th className="px-3 py-2">Human override</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {DIMENSIONS.map(({ code, label, hint }) => {
                const s = scores.get(code)
                const auto = s?.automated_score
                return (
                  <tr key={code} className="hover:bg-slate-900/30">
                    <td className="px-3 py-2 font-mono text-violet-300">{code}</td>
                    <td className="px-3 py-2">
                      <div className="text-white">{label}</div>
                      <div className="text-xs text-slate-500">{hint}</div>
                      {s?.detail && (
                        <pre className="text-xs text-slate-600 mt-1 max-w-md truncate" title={s.detail}>
                          {s.detail}
                        </pre>
                      )}
                    </td>
                    <td className="px-3 py-2 font-mono text-slate-300">
                      {auto !== undefined ? auto.toFixed(3) : '—'}
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        step="0.01"
                        min={0}
                        max={1}
                        placeholder="0–1"
                        value={overrideDrafts[code] ?? ''}
                        onChange={(e) => setOverrideDrafts((d) => ({ ...d, [code]: e.target.value }))}
                        className="w-24 rounded bg-slate-950 border border-slate-700 px-2 py-1 font-mono text-xs"
                      />
                      {overrideByDim.has(code) && (
                        <span className="ml-2 text-xs text-emerald-500">saved</span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => saveOverride(code)}
                        className="text-xs text-violet-400 hover:text-violet-300"
                      >
                        Save
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-medium text-white mb-2">Star rating (1–5)</h2>
        <div className="flex gap-2">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              disabled={busy}
              onClick={() => saveStars(n)}
              className={`rounded-lg px-3 py-2 text-sm font-medium border ${
                data.star_rating?.stars === n
                  ? 'bg-amber-500/20 border-amber-500 text-amber-200'
                  : 'border-slate-700 text-slate-400 hover:border-slate-500'
              }`}
            >
              {n}★
            </button>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-medium text-white mb-2">Comments</h2>
        <form onSubmit={submitComment} className="flex flex-col gap-2 max-w-xl">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
            placeholder="Notes for RLHF dataset…"
            className="rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-white placeholder:text-slate-600"
          />
          <button
            type="submit"
            disabled={busy || !comment.trim()}
            className="self-start rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm px-4 py-2 disabled:opacity-50"
          >
            Add comment
          </button>
        </form>
        <ul className="mt-4 space-y-3">
          {data.comments.map((c) => (
            <li key={c.id} className="rounded-lg border border-slate-800 bg-slate-900/30 px-3 py-2 text-sm">
              <p className="text-slate-200 whitespace-pre-wrap">{c.body}</p>
              <p className="text-xs text-slate-500 mt-1">{new Date(c.created_at).toLocaleString()}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

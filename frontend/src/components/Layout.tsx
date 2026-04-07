import { useCallback, useEffect, useState } from 'react'
import { Link, Outlet } from 'react-router-dom'
import { api } from '../api'

export function Layout() {
  const [apiDown, setApiDown] = useState<boolean | null>(null)

  const ping = useCallback(() => {
    setApiDown(null)
    api
      .health()
      .then(() => setApiDown(false))
      .catch(() => setApiDown(true))
  }, [])

  useEffect(() => {
    ping()
  }, [ping])

  return (
    <div className="min-h-screen flex flex-col">
      {apiDown === true && (
        <div className="bg-amber-950/90 border-b border-amber-800 text-amber-100 text-sm px-4 py-3">
          <p className="max-w-5xl mx-auto">
            <strong className="text-amber-50">Backend not reachable.</strong> The UI needs the API on{' '}
            <code className="text-amber-200">http://127.0.0.1:8000</code>. From <code className="text-amber-200">backend/</code>, run{' '}
            <code className="text-amber-200">uvicorn app.main:app --reload</code> after Postgres is up and{' '}
            <code className="text-amber-200">alembic upgrade head</code> has been run.{' '}
            <button type="button" onClick={ping} className="underline text-amber-50 hover:text-white ml-1">
              Check again
            </button>
          </p>
        </div>
      )}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <Link to="/" className="font-semibold text-violet-300 hover:text-violet-200">
            RLHF Repo Eval
          </Link>
          <nav className="flex gap-4 text-sm">
            <Link to="/" className="text-slate-400 hover:text-white">
              Repos
            </Link>
            <Link to="/compare" className="text-slate-400 hover:text-white">
              Compare A vs B
            </Link>
            <a
              href="/api/export/jsonl"
              download="rlhf_export.jsonl"
              className="text-slate-400 hover:text-white"
              onClick={async (e) => {
                e.preventDefault()
                const blob = await api.exportJsonl()
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = 'rlhf_export.jsonl'
                a.click()
                URL.revokeObjectURL(url)
              }}
            >
              Export JSONL
            </a>
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}

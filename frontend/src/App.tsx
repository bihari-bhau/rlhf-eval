import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Compare } from './pages/Compare'
import { RepoDetail } from './pages/RepoDetail'
import { RepoList } from './pages/RepoList'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<RepoList />} />
          <Route path="/repos/:id" element={<RepoDetail />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

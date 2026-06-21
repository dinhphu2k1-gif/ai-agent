import { useState, useRef } from 'react'
import type { FormEvent } from 'react'
import './index.css'

const API_BASE = 'http://localhost:8000'

interface UserInfo {
  id: string
  username: string
  full_name: string | null
  branch_code: string | null
  role: string | null
}

interface StreamEvent {
  type: string
  data: Record<string, unknown>
}

// ─── Preset Users (in case API is down) ──────────────────

const PRESET_USERS: UserInfo[] = [
  { id: '1', username: 'teller_hn', full_name: 'Nguyễn Thị Hoa (GDV)', branch_code: 'HN', role: 'Giao dịch viên' },
  { id: '2', username: 'manager_hcm', full_name: 'Trần Quốc Bảo (GĐ)', branch_code: 'HCM', role: 'Giám đốc chi nhánh' },
  { id: '3', username: 'auditor', full_name: 'Lê Minh Tuấn (KTV)', branch_code: null, role: 'Kiểm toán viên' },
]

const ROLE_ICONS: Record<string, string> = {
  'teller_hn': '👤',
  'manager_hcm': '👔',
  'auditor': '🔍',
}

// ─── App ─────────────────────────────────────────────────

export default function App() {
  const [users] = useState<UserInfo[]>(PRESET_USERS)
  const [activeUser, setActiveUser] = useState<string>('teller_hn')
  const [question, setQuestion] = useState('')
  const [events, setEvents] = useState<StreamEvent[]>([])
  const [loading, setLoading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!question.trim() || loading) return

    setEvents([])
    setLoading(true)

    try {
      const resp = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim(), user_id: activeUser }),
      })

      if (!resp.ok) {
        setEvents([{ type: 'error', data: { message: `HTTP ${resp.status}` } }])
        setLoading(false)
        return
      }

      const reader = resp.body?.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let currentEventType = ''

      if (!reader) return

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        // console.log("Received chunk:", buffer)
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEventType = line.slice(7).trim()
            // console.log("Parsed event type:", currentEventType)
          } else if (line.startsWith('data: ') && currentEventType) {
            try {
              const eventType = currentEventType
              const data = JSON.parse(line.slice(6))
              // console.log("Parsed data:", data)
              setEvents(prev => [...prev, { type: eventType, data }])
            } catch (err) { 
              console.error('Failed to parse SSE data:', line.slice(6), err)
            }
            currentEventType = ''
          }
        }
      }
    } catch (err) {
      setEvents([{ type: 'error', data: { message: `Không thể kết nối tới backend: ${err}` } }])
    } finally {
      setLoading(false)
    }
  }

  const currentUser = users.find(u => u.username === activeUser)

  return (
    <>
      {/* Header */}
      <header className="header">
        <div className="header__title">
          <div className="header__icon">🛡️</div>
          <div className="header__text">
            <h1>AI Governance Demo</h1>
            <p>SeABank — Phân quyền dữ liệu cho AI Agent</p>
          </div>
        </div>

        <div className="user-switcher">
          {users.map(u => (
            <button
              key={u.username}
              className={`user-btn ${activeUser === u.username ? 'user-btn--active' : ''}`}
              onClick={() => { setActiveUser(u.username); setEvents([]) }}
            >
              <span style={{ fontSize: '20px' }}>{ROLE_ICONS[u.username] || '👤'}</span>
              <span className="user-btn__name">{u.full_name}</span>
              <span className="user-btn__role">{u.role}</span>
              <span className="user-btn__branch">{u.branch_code ? `Chi nhánh: ${u.branch_code}` : 'Toàn hệ thống'}</span>
            </button>
          ))}
        </div>
      </header>

      {/* Main */}
      <main className="main">
        {/* Chat Input */}
        <form className="chat-input" onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            type="text"
            placeholder={`Hỏi AI với tư cách ${currentUser?.full_name || activeUser}...`}
            value={question}
            onChange={e => setQuestion(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? '⏳ Đang xử lý...' : '🚀 Gửi'}
          </button>
        </form>

        {/* Events */}
        <div className="events">
          {events.map((ev, i) => (
            <EventCard key={i} event={ev} />
          ))}
        </div>
      </main>
    </>
  )
}

// ─── Event Card Component ────────────────────────────────

function EventCard({ event }: { event: StreamEvent }) {
  const { type, data } = event

  if (type === 'thinking') {
    return (
      <div className="event-card event-card--thinking">
        <div className="event-label event-label--thinking">💭 Đang suy luận</div>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>{data.message as string}</p>
      </div>
    )
  }

  if (type === 'sql') {
    return (
      <div className="event-card event-card--sql">
        <div className="event-label event-label--sql">📝 SQL đã sinh</div>
        <div className="sql-block">{data.sql as string}</div>
      </div>
    )
  }

  if (type === 'policy') {
    const filters = (data.row_filters_applied as string[]) || []
    const masks = (data.masked_columns as string[]) || []
    const denied = (data.denied_columns as string[]) || []

    return (
      <div className="event-card event-card--policy">
        <div className="event-label event-label--policy">🔒 Chính sách áp dụng</div>
        <div className="policy">
          <span className={`badge badge--${data.decision === 'ALLOW' ? 'allow' : 'filter'}`}>
            {data.decision as string}
          </span>
          {filters.map((f, i) => (
            <span key={i} className="badge badge--filter">🔵 Row Filter: {f}</span>
          ))}
          {masks.map((m, i) => (
            <span key={i} className="badge badge--mask">🟡 Mask: {m}</span>
          ))}
          {denied.map((d, i) => (
            <span key={i} className="badge badge--deny">🔴 Denied: {d}</span>
          ))}
        </div>
      </div>
    )
  }

  if (type === 'result') {
    const columns = (data.columns as string[]) || []
    const rows = (data.rows as Record<string, unknown>[]) || []
    const rewrittenSql = data.rewritten_sql as string

    return (
      <div className="event-card event-card--result">
        <div className="event-label event-label--result">✅ Kết quả ({data.row_count as number} dòng)</div>

        {rewrittenSql && (
          <div style={{ marginBottom: 12 }}>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>SQL sau khi rewrite:</span>
            <div className="sql-block" style={{ fontSize: 12, marginTop: 4 }}>{rewrittenSql}</div>
          </div>
        )}

        <div className="result-table-wrap">
          <table className="result-table">
            <thead>
              <tr>
                {columns.map(col => (
                  <th key={col}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, ri) => (
                <tr key={ri}>
                  {columns.map(col => {
                    const val = row[col]
                    const isMasked = typeof val === 'string' && (val.includes('***') || /^[a-f0-9]{12}$/.test(val))
                    return (
                      <td key={col} className={isMasked ? 'cell--masked' : ''}>
                        {val === null ? '—' : String(val)}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  if (type === 'error' || type === 'denied') {
    return (
      <div className={`event-card event-card--${type}`}>
        <div className={`event-label event-label--${type}`}>
          {type === 'denied' ? '🚫 Truy cập bị từ chối' : '❌ Lỗi'}
        </div>
        <p style={{ color: 'var(--accent-red)', fontSize: 14 }}>{data.message as string}</p>
      </div>
    )
  }

  return null
}

function events_get_masks(_event: StreamEvent): string[] {
  // This is a helper that would extract mask info from policy events
  // For now, we detect masked cells by their content pattern
  return []
}

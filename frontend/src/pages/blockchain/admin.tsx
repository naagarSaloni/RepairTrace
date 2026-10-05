import { FormEvent, useEffect, useMemo, useState } from 'react'
import { BadgeCheck, Gavel, Store, XCircle } from 'lucide-react'
import { disputesApi, vendorApi } from '../../api/blockchain'
import { adminApi } from '../../api/services'
import { errorMessage } from '../../api/client'
import type { Technician } from '../../types'
import type { Dispute, Vendor } from '../../types/blockchain'
import { Button, Card, Empty, ErrorBox, SectionTitle, Stat } from '../../components/ui'
import { Pill, fmtDate } from '../../components/blockchain/Widgets'
import { disputeTone } from './customer'

/* ============================================================
   DISPUTES  ·  /admin/disputes
   GET /api/disputes/all   and   PATCH /api/disputes/{id}/resolve
   ============================================================ */
export function AdminDisputes() {
  const [disputes, setDisputes] = useState<Dispute[]>([])
  const [filter, setFilter] = useState<'ALL' | 'OPEN' | 'RESOLVED'>('OPEN')
  const [responses, setResponses] = useState<Record<number, string>>({})
  const [busy, setBusy] = useState<number | null>(null)
  const [error, setError] = useState('')

  const load = () => disputesApi.all().then(r => setDisputes(r.data)).catch(e => setError(errorMessage(e)))
  useEffect(() => { load() }, [])
  const shown = disputes.filter(d => filter === 'ALL' || d.status === filter)
  const resolve = async (id: number) => {
    setBusy(id); setError('')
    try { await disputesApi.resolve(id, (responses[id] || '').trim()); await load() } catch (e) { setError(errorMessage(e)) } finally { setBusy(null) }
  }

  return <>
    <SectionTitle eyebrow="ADMIN" title="Repair disputes" description="Review customer disputes and record a resolution." />
    {error && <ErrorBox message={error} onRetry={load} />}
    <div className="stats-grid">
      <Stat icon={Gavel} label="Total" value={disputes.length} />
      <Stat icon={Gavel} label="Open" value={disputes.filter(d => d.status === 'OPEN').length} />
      <Stat icon={BadgeCheck} label="Resolved" value={disputes.filter(d => d.status === 'RESOLVED').length} />
    </div>
    <Card>
      <div className="card-heading"><div><span className="eyebrow">QUEUE</span><h2>Disputes</h2></div>
        <div className="bc-actions">{(['OPEN', 'RESOLVED', 'ALL'] as const).map(f => <Button key={f} variant={filter === f ? 'primary' : 'ghost'} onClick={() => setFilter(f)}>{f[0] + f.slice(1).toLowerCase()}</Button>)}</div>
      </div>
      {shown.length ? <div className="stack">{shown.map(d => <div className="bc-repair" style={{ marginTop: 0 }} key={d.id}><div className="bc-body">
        <div className="row-between"><b>Dispute #{d.id} · Repair #{d.repair_id}</b><Pill tone={disputeTone(d.status)}>{d.status}</Pill></div>
        <div><b>{d.reason}</b>{d.description && <p className="muted" style={{ margin: '4px 0 0' }}>{d.description}</p>}</div>
        <span className="muted">Raised by user #{d.raised_by} · {fmtDate(d.created_at)}</span>
        {d.status === 'RESOLVED'
          ? <div className="bc-note"><b>Response.</b> {d.admin_response}<br /><span className="muted">Resolved by user #{d.resolved_by} · {fmtDate(d.resolved_at)}</span></div>
          : <div className="form-grid compact">
              <label className="full-span">Administrator's response<textarea value={responses[d.id] || ''} onChange={e => setResponses({ ...responses, [d.id]: e.target.value })} placeholder="Explain the outcome to the customer…" /></label>
              <div className="form-actions full-span"><Button loading={busy === d.id} disabled={!(responses[d.id] || '').trim()} onClick={() => resolve(d.id)}><BadgeCheck size={16} /> Resolve dispute</Button></div>
            </div>}
      </div></div>)}</div> : <Empty title="No disputes here" description="Nothing matches this filter." />}
    </Card>
  </>
}

/* ============================================================
   VENDORS  ·  /admin/vendors
   POST/GET /api/admin/vendors   PATCH /api/admin/vendors/{id}/verify | reject
   ============================================================ */
const vendorTone = (s: string) => (s === 'VERIFIED' ? 'good' : s === 'REJECTED' ? 'bad' : 'warn') as 'good' | 'bad' | 'warn'
const blank = { user_id: '', business_name: '', phone: '', address: '', specialization: '' }

export function AdminVendors() {
  const [vendors, setVendors] = useState<Vendor[]>([])
  const [techs, setTechs] = useState<Technician[]>([])
  const [form, setForm] = useState(blank)
  const [busy, setBusy] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const load = () => Promise.all([vendorApi.list(), adminApi.technicians()]).then(([v, t]) => { setVendors(v.data); setTechs(t.data) }).catch(e => setError(errorMessage(e)))
  useEffect(() => { load() }, [])
  // a technician can only have one vendor profile
  const available = useMemo(() => techs.filter(t => !vendors.some(v => v.user_id === t.id)), [techs, vendors])

  const create = async (e: FormEvent) => {
    e.preventDefault(); setBusy('create'); setError(''); setMessage('')
    try {
      await vendorApi.create({ user_id: Number(form.user_id), business_name: form.business_name.trim(), phone: form.phone.trim(), address: form.address.trim(), specialization: form.specialization.trim() })
      setMessage('Vendor profile created and waiting for verification.'); setForm(blank); await load()
    } catch (err) { setError(errorMessage(err)) } finally { setBusy('') }
  }
  const act = async (id: number, kind: 'verify' | 'reject') => {
    setBusy(`${kind}${id}`); setError(''); setMessage('')
    try { await (kind === 'verify' ? vendorApi.verify(id) : vendorApi.reject(id)); await load() } catch (e) { setError(errorMessage(e)) } finally { setBusy('') }
  }

  return <>
    <SectionTitle eyebrow="ADMIN" title="Repair vendors" description="Register technicians as repair vendors and verify their business details." />
    {error && <ErrorBox message={error} onRetry={load} />}
    <div className="admin-grid">
      <Card>
        <div className="card-heading"><div><span className="eyebrow">DIRECTORY</span><h2>{vendors.length} vendor{vendors.length === 1 ? '' : 's'}</h2></div></div>
        {vendors.length ? <div className="stack">{vendors.map(v => <div className="bc-repair" style={{ marginTop: 0 }} key={v.id}><div className="bc-body">
          <div className="row-between"><div><b>{v.business_name}</b><span className="muted" style={{ display: 'block' }}>{v.name} · {v.email}</span></div><Pill tone={vendorTone(v.verification_status)}>{v.verification_status}</Pill></div>
          <div className="verify-grid" style={{ marginTop: 0 }}>
            <div><small>Specialization</small><b>{v.specialization || '—'}</b></div>
            <div><small>Phone</small><b>{v.phone || '—'}</b></div>
            <div><small>Address</small><b>{v.address || '—'}</b></div>
            <div><small>Verified at</small><b>{fmtDate(v.verified_at)}</b></div>
          </div>
          <div className="bc-actions">
            <Button loading={busy === `verify${v.id}`} disabled={v.verification_status === 'VERIFIED'} onClick={() => act(v.id, 'verify')}><BadgeCheck size={15} /> Verify</Button>
            <Button variant="danger" loading={busy === `reject${v.id}`} disabled={v.verification_status === 'REJECTED'} onClick={() => act(v.id, 'reject')}><XCircle size={15} /> Reject</Button>
          </div>
        </div></div>)}</div> : <Empty title="No vendors yet" description="Create a vendor profile for a technician." />}
      </Card>

      <Card>
        <span className="eyebrow">NEW VENDOR</span><h2>Register a vendor</h2>
        {message && <div className="form-success" style={{ margin: '10px 0' }}>{message}</div>}
        <form className="form-grid" onSubmit={create}>
          <label className="full-span">Technician
            <select required value={form.user_id} onChange={e => setForm({ ...form, user_id: e.target.value })}>
              <option value="">Select technician</option>
              {available.map(t => <option key={t.id} value={t.id}>{t.name} · {t.email}</option>)}
            </select>
          </label>
          <label className="full-span">Business name<input required value={form.business_name} onChange={e => setForm({ ...form, business_name: e.target.value })} /></label>
          <label>Phone<input value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} /></label>
          <label>Specialization<input value={form.specialization} onChange={e => setForm({ ...form, specialization: e.target.value })} placeholder="e.g. Mobile phones" /></label>
          <label className="full-span">Address<input value={form.address} onChange={e => setForm({ ...form, address: e.target.value })} /></label>
          <div className="form-actions full-span"><Button type="submit" loading={busy === 'create'} disabled={!available.length}><Store size={16} /> Create vendor</Button></div>
        </form>
        {!available.length && techs.length > 0 && <p className="tiny-note">Every technician already has a vendor profile.</p>}
      </Card>
    </div>
  </>
}

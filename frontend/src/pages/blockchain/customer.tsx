import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeftRight, Gauge, MessageSquareWarning, ShieldCheck, Sparkles } from 'lucide-react'
import { disputesApi, ownershipApi, riskApi } from '../../api/blockchain'
import { productsApi, repairsApi } from '../../api/services'
import { errorMessage } from '../../api/client'
import type { Product, Repair } from '../../types'
import type { AiRiskResult, Dispute, OwnershipHistory, RiskResult } from '../../types/blockchain'
import { Button, Card, Empty, ErrorBox, SectionTitle } from '../../components/ui'
import { FlagList, Hash, Pill, RiskPill, TrustMeter, fmtDate } from '../../components/blockchain/Widgets'

/* ============================================================
   PRODUCT TRUST  ·  /customer/trust
   GET /api/risk/products/{uid}   and   GET /api/ai-risk/products/{uid}
   ============================================================ */
export function ProductTrust() {
  const [products, setProducts] = useState<Product[]>([])
  const [uid, setUid] = useState('')
  const [risk, setRisk] = useState<RiskResult | null>(null)
  const [ai, setAi] = useState<AiRiskResult | null>(null)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')

  useEffect(() => { productsApi.list().then(r => setProducts(r.data)).catch(e => setError(errorMessage(e))) }, [])
  const pick = (value: string) => { setUid(value); setRisk(null); setAi(null); setError('') }
  const run = async (name: 'risk' | 'ai') => {
    if (!uid) return
    setBusy(name); setError('')
    try { if (name === 'risk') setRisk((await riskApi.analyze(uid)).data); else setAi((await riskApi.analyzeAi(uid)).data) }
    catch (e) { setError(errorMessage(e)) } finally { setBusy('') }
  }
  const shown = ai || risk

  return <>
    <SectionTitle eyebrow="TRUST" title="Product trust score" description="See how trustworthy your product's repair history looks to a future buyer." />
    {error && <ErrorBox message={error} />}
    <Card>
      <div className="bc-select-row">
        <select value={uid} onChange={e => pick(e.target.value)}>
          <option value="">Select one of your products</option>
          {products.map(p => <option key={p.id} value={p.product_uid}>{p.product_name} · {p.product_uid}</option>)}
        </select>
        <Button loading={busy === 'risk'} disabled={!uid} onClick={() => run('risk')}><Gauge size={16} /> Trust score</Button>
        <Button variant="secondary" loading={busy === 'ai'} disabled={!uid} onClick={() => run('ai')}><Sparkles size={16} /> Detailed analysis</Button>
      </div>
      {!products.length && !error && <Empty title="No products yet" description="Register a product to see its trust score." />}
      {shown && <>
        <div className="bc-head">
          <TrustMeter score={shown.trust_score} level={shown.risk_level} />
          <div className="grow">
            <span className="eyebrow">{shown.product_uid}</span>
            <h2>{shown.product_name}</h2>
            <RiskPill level={shown.risk_level} /> <span className="muted">&nbsp;{shown.total_repairs} repair{shown.total_repairs === 1 ? '' : 's'} recorded</span>
          </div>
          <Link className="btn btn-secondary" to={`/passport/${shown.product_uid}`}><ShieldCheck size={16} /> Public passport</Link>
        </div>
        <FlagList flags={shown.risk_flags} emptyText="No risk indicators. This product's repair history looks clean." />
      </>}
      {ai && <div style={{ marginTop: 18, display: 'grid', gap: 10 }}>
        <div className="bc-note"><b>Assessment.</b> {ai.assessment}</div>
        <div className="bc-note"><b>Recommendation.</b> {ai.recommendation}</div>
        <p className="tiny-note">{ai.analysis_type}. The score is calculated from rules applied to your repair records (repair count, cancelled repairs, missing diagnosis, documents and more).</p>
      </div>}
    </Card>
  </>
}

/* ============================================================
   OWNERSHIP  ·  /customer/ownership
   POST /api/ownership/transfer   and   GET /api/ownership/{uid}/history
   ============================================================ */
export function OwnershipTransferPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [uid, setUid] = useState('')
  const [history, setHistory] = useState<OwnershipHistory | null>(null)
  const [email, setEmail] = useState('')
  const [reason, setReason] = useState('')
  const [confirm, setConfirm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const loadProducts = () => productsApi.list().then(r => setProducts(r.data)).catch(e => setError(errorMessage(e)))
  useEffect(() => { loadProducts() }, [])
  useEffect(() => {
    setHistory(null)
    if (uid) ownershipApi.history(uid).then(r => setHistory(r.data)).catch(e => setError(errorMessage(e)))
  }, [uid])

  const submit = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true); setError(''); setMessage('')
    try {
      const r = await ownershipApi.transfer(uid, email.trim(), reason.trim())
      setMessage(`${r.data.product_uid} was transferred to ${r.data.new_owner_name} (${r.data.new_owner_email}). It no longer appears in your products.`)
      setUid(''); setEmail(''); setReason(''); setConfirm(false); await loadProducts()
    } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) }
  }

  return <>
    <SectionTitle eyebrow="OWNERSHIP" title="Transfer ownership" description="Hand a product, with its full repair history, to a new customer account." />
    {message && <div className="form-success" style={{ marginBottom: 16 }}>{message}</div>}
    {error && <ErrorBox message={error} />}
    <div className="admin-grid">
      <Card>
        <span className="eyebrow">NEW TRANSFER</span><h2>Transfer a product</h2>
        <form className="form-grid" onSubmit={submit}>
          <label className="full-span">Product
            <select required value={uid} onChange={e => { setUid(e.target.value); setMessage('') }}>
              <option value="">Select product</option>
              {products.map(p => <option key={p.id} value={p.product_uid}>{p.product_name} · {p.product_uid}</option>)}
            </select>
          </label>
          <label className="full-span">New owner's email<input required type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="buyer@example.com" /></label>
          <label className="full-span">Reason (optional)<input maxLength={255} value={reason} onChange={e => setReason(e.target.value)} placeholder="e.g. Sold to a friend" /></label>
          <label className="full-span" style={{ display: 'flex', gap: 8, alignItems: 'center', fontWeight: 600 }}>
            <input type="checkbox" checked={confirm} onChange={e => setConfirm(e.target.checked)} style={{ width: 'auto' }} />
            I understand I will lose access to this product after the transfer.
          </label>
          <div className="form-actions full-span"><Button type="submit" loading={busy} disabled={!confirm || !uid}><ArrowLeftRight size={16} /> Transfer ownership</Button></div>
        </form>
        <p className="tiny-note">The new owner must already have a RepairTrace customer account.</p>
      </Card>

      <Card>
        <span className="eyebrow">HISTORY</span><h2>Ownership timeline</h2>
        {!uid && <p className="muted">Select a product to see who has owned it.</p>}
        {uid && history && (history.ownership_transfers.length ? <div className="timeline">{history.ownership_transfers.map(t => <div className="timeline-item" key={t.id}>
          <div className="timeline-dot"></div>
          <div className="timeline-body">
            <div className="timeline-head"><b>{t.previous_owner.name || 'Unknown'} → {t.new_owner.name || 'Unknown'}</b><span>{fmtDate(t.transferred_at)}</span></div>
            <p>{t.transfer_reason || 'No reason given.'}</p>
            <Hash label="Blockchain transaction" value={t.blockchain_tx_hash} />
          </div>
        </div>)}</div> : <p className="muted">This product has not been transferred. You are the original owner.</p>)}
      </Card>
    </div>
  </>
}

/* ============================================================
   DISPUTES  ·  /customer/disputes
   POST /api/disputes/repairs/{repair_id}   and   GET /api/disputes/my
   ============================================================ */
export const disputeTone = (s: string) => (s === 'RESOLVED' ? 'good' : 'warn') as 'good' | 'warn'

export function CustomerDisputes() {
  const [repairs, setRepairs] = useState<Repair[]>([])
  const [disputes, setDisputes] = useState<Dispute[]>([])
  const [repairId, setRepairId] = useState('')
  const [reason, setReason] = useState('')
  const [description, setDescription] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const load = () => Promise.all([repairsApi.listMine(), disputesApi.mine()])
    .then(([r, d]) => { setRepairs(r.data); setDisputes(d.data) }).catch(e => setError(errorMessage(e)))
  useEffect(() => { load() }, [])
  // disputes store the numeric repair id, so map it back to the REP-… code
  const codeById = useMemo(() => new Map(repairs.map(r => [r.id, r.repair_id])), [repairs])

  const submit = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true); setError(''); setMessage('')
    try {
      await disputesApi.create(repairId, reason.trim(), description.trim())
      setMessage('Dispute submitted. An administrator will review it.')
      setRepairId(''); setReason(''); setDescription(''); await load()
    } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) }
  }

  return <>
    <SectionTitle eyebrow="DISPUTES" title="Repair disputes" description="Raise a concern about a repair and track the administrator's response." />
    {message && <div className="form-success" style={{ marginBottom: 16 }}>{message}</div>}
    {error && <ErrorBox message={error} />}
    <div className="admin-grid">
      <Card>
        <div className="card-heading"><div><span className="eyebrow">YOUR DISPUTES</span><h2>{disputes.length} raised</h2></div></div>
        {disputes.length ? <div className="stack">{disputes.map(d => <div key={d.id} className="bc-repair" style={{ marginTop: 0 }}><div className="bc-body">
          <div className="row-between"><b>{codeById.get(d.repair_id) || `Repair #${d.repair_id}`}</b><Pill tone={disputeTone(d.status)}>{d.status}</Pill></div>
          <div><b>{d.reason}</b>{d.description && <p className="muted" style={{ margin: '4px 0 0' }}>{d.description}</p>}</div>
          <span className="muted">Raised {fmtDate(d.created_at)}</span>
          {d.admin_response && <div className="bc-note"><b>Administrator's response.</b> {d.admin_response}<br /><span className="muted">Resolved {fmtDate(d.resolved_at)}</span></div>}
        </div></div>)}</div> : <Empty title="No disputes" description="Disputes you raise will appear here." />}
      </Card>

      <Card>
        <span className="eyebrow">NEW DISPUTE</span><h2>Raise a dispute</h2>
        <form className="form-grid" onSubmit={submit}>
          <label className="full-span">Repair
            <select required value={repairId} onChange={e => setRepairId(e.target.value)}>
              <option value="">Select repair</option>
              {repairs.map(r => <option key={r.id} value={r.repair_id}>{r.repair_id} · {r.status.replaceAll('_', ' ')}</option>)}
            </select>
          </label>
          <label className="full-span">Reason<input required maxLength={255} value={reason} onChange={e => setReason(e.target.value)} placeholder="e.g. Problem returned after repair" /></label>
          <label className="full-span">Details (optional)<textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Describe what went wrong…" /></label>
          <div className="form-actions full-span"><Button type="submit" loading={busy}><MessageSquareWarning size={16} /> Submit dispute</Button></div>
        </form>
        <p className="tiny-note">Only one open dispute is allowed per repair. Only the product owner can raise a dispute.</p>
      </Card>
    </div>
  </>
}

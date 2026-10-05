import { FormEvent, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { FileText, FileSearch, Link2, PackageCheck, Search, ShieldCheck, Wrench } from 'lucide-react'
import { passportApi } from '../../api/blockchain'
import { assetUrl, errorMessage } from '../../api/client'
import type { DocumentVerification, PassportRepair, ProductPassport } from '../../types/blockchain'
import { Badge, Button, Card, ErrorBox, Timeline } from '../../components/ui'
import { Check, FlagList, Hash, RiskPill, TrustMeter, VerifyPill, fmtDate } from '../../components/blockchain/Widgets'

function DocRow({ doc }: { doc: PassportRepair['documents'][number] }) {
  const [result, setResult] = useState<DocumentVerification | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const check = async () => { setBusy(true); setError(''); try { setResult((await passportApi.verifyDocument(doc.id)).data) } catch (e) { setError(errorMessage(e)) } finally { setBusy(false) } }
  return <div className="bc-doc">
    <FileText size={18} />
    <div className="grow">
      <a href={assetUrl(doc.file_url)} target="_blank" rel="noreferrer"><b>{doc.file_name}</b></a>
      <span>{doc.document_type.replaceAll('_', ' ')}{doc.description ? ` · ${doc.description}` : ''} · {fmtDate(doc.uploaded_at)}</span>
      <Hash label="SHA-256 stored at upload" value={doc.file_hash} />
      {result && <div style={{ marginTop: 8 }}><Check ok={result.verified} label={result.verified ? 'File unchanged' : 'File changed or missing'} /><p className="tiny-note">{result.message}</p></div>}
      {error && <p className="form-error">{error}</p>}
    </div>
    <Button variant="secondary" loading={busy} onClick={check}><FileSearch size={14} /> Verify file</Button>
  </div>
}

function RepairBlock({ repair }: { repair: PassportRepair }) {
  return <details className="bc-repair">
    <summary>
      <div className="row-icon"><Wrench size={17} /></div>
      <div className="grow"><b>{repair.repair_id}</b><span>{repair.issue_description}</span></div>
      <VerifyPill status={repair.verification_status} />
      <Badge status={repair.status} />
    </summary>
    <div className="bc-body">
      <div className="verify-grid" style={{ marginTop: 0 }}>
        <div><small>Diagnosis</small><b>{repair.diagnosis || '—'}</b></div>
        <div><small>Last updated</small><b>{fmtDate(repair.updated_at || repair.created_at)}</b></div>
      </div>
      <div>
        <h4>INTEGRITY PROOF</h4>
        <div className="bc-actions" style={{ marginBottom: 10 }}>
          <Check ok={repair.hash_verified} label={repair.hash_verified ? 'SHA-256 matches' : 'SHA-256 not confirmed'} />
          <Check ok={repair.blockchain_verified} label={repair.blockchain_verified ? 'Found on blockchain' : 'Not on blockchain'} />
        </div>
        <Hash label="Record hash (SHA-256)" value={repair.record_hash} />
        <div style={{ height: 8 }} />
        <Hash label="Blockchain transaction" value={repair.blockchain_tx_hash} />
        {!repair.record_hash && <p className="muted">A record hash is created when the technician completes the repair.</p>}
      </div>
      <div>
        <h4>COMPONENT HISTORY</h4>
        {repair.components.length ? <div className="part-list">{repair.components.map((c, i) => <div className="part-row" key={i}><div><b>{c.part_name}</b><span>{c.old_part_serial || '—'} → {c.new_part_serial || '—'}</span></div><span>{c.warranty_months} mo warranty</span></div>)}</div> : <p className="muted">No components were replaced.</p>}
      </div>
      <div>
        <h4>DOCUMENTS</h4>
        {repair.documents.length ? repair.documents.map(d => <DocRow key={d.id} doc={d} />) : <p className="muted">No documents attached.</p>}
      </div>
      <div>
        <h4>STATUS HISTORY</h4>
        {repair.status_history.length ? <Timeline history={repair.status_history} /> : <p className="muted">No history recorded.</p>}
      </div>
    </div>
  </details>
}

export default function PublicPassport() {
  const params = useParams()
  const [uid, setUid] = useState(params.productUid || '')
  const [data, setData] = useState<ProductPassport | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const load = async (value: string) => {
    if (!value.trim()) return
    setBusy(true); setError(''); setData(null)
    try { setData((await passportApi.get(value.trim())).data) } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) }
  }
  useEffect(() => { if (params.productUid) load(params.productUid) }, [params.productUid])
  const submit = (e: FormEvent) => { e.preventDefault(); load(uid) }
  const s = data?.summary

  return <div className="public-verify"><div className="verify-wrap">
    <div className="verify-brand"><div className="brand-mark"><ShieldCheck /></div><div><b>RepairTrace</b><span>Digital product passport</span></div></div>
    <div className="verify-intro">
      <span className="eyebrow">SCAN · VERIFY · TRUST</span>
      <h1>Product repair passport</h1>
      <p>Enter the product ID from the QR label to see its complete repair history, verified with SHA-256 hashes and the blockchain record.</p>
    </div>
    <Card><form className="verify-form" onSubmit={submit}>
      <input value={uid} onChange={e => setUid(e.target.value)} placeholder="e.g. PRD-7F3A91B22C" />
      <Button type="submit" loading={busy}><Search size={17} /> View passport</Button>
    </form></Card>
    {error && <ErrorBox message={error} />}

    {data && s && <>
      <Card className="verification-result">
        <div className="bc-head">
          <TrustMeter score={s.trust_score} level={s.risk_level} />
          <div className="grow">
            <span className="eyebrow">{data.passport.product_uid}</span>
            <h2>{data.passport.product_name}</h2>
            <p className="muted">{[data.passport.brand, data.passport.model].filter(Boolean).join(' · ') || 'Registered product'}{data.passport.serial_number ? ` · S/N ${data.passport.serial_number}` : ''}</p>
            <RiskPill level={s.risk_level} />
          </div>
          <Link className="btn btn-secondary" to={`/buyer-report/${data.passport.product_uid}`}><PackageCheck size={16} /> Buyer report</Link>
        </div>
        <div className="bc-counts">
          <div><b>{s.total_repairs}</b><small>Total repairs</small></div>
          <div><b>{s.completed_repairs}</b><small>Completed</small></div>
          <div><b>{s.hash_verified_repairs}</b><small>Hash verified</small></div>
          <div><b>{s.blockchain_verified_repairs}</b><small>On blockchain</small></div>
        </div>
        <FlagList flags={s.risk_flags} emptyText="No risk indicators detected in this product's repair history." />
        <div className="verification-message"><Link2 size={20} /><span>{data.message}</span></div>
      </Card>

      <Card>
        <div className="card-heading"><div><span className="eyebrow">REPAIR HISTORY</span><h2>{data.repair_history.length ? `${data.repair_history.length} recorded repair${data.repair_history.length > 1 ? 's' : ''}` : 'No repairs recorded'}</h2></div></div>
        {data.repair_history.length ? data.repair_history.map(r => <RepairBlock key={r.repair_id} repair={r} />) : <p className="muted">This product has no repair records yet.</p>}
      </Card>
    </>}
  </div></div>
}

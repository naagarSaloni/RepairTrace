import { FormEvent, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, FileSearch, FileText, Plus, ScanSearch, Upload, Wrench } from 'lucide-react'
import { evidenceApi, passportApi } from '../../api/blockchain'
import { technicianApi } from '../../api/services'
import { assetUrl, errorMessage } from '../../api/client'
import type { Part, Repair } from '../../types'
import type { AddPartResult, DocumentVerification, EvidenceDocument, UploadResult } from '../../types/blockchain'
import { Badge, Button, Card, Empty, ErrorBox, SectionTitle } from '../../components/ui'
import { Check, FlagList, Hash, Pill, fmtDate } from '../../components/blockchain/Widgets'

/* ============================================================
   EVIDENCE CHECK LIST  ·  /technician/evidence
   ============================================================ */
export function TechnicianEvidenceList() {
  const [repairs, setRepairs] = useState<Repair[]>([])
  const [error, setError] = useState('')
  useEffect(() => { technicianApi.repairs().then(r => setRepairs(r.data)).catch(e => setError(errorMessage(e))) }, [])
  return <>
    <SectionTitle eyebrow="TECHNICIAN" title="Evidence & fraud check" description="Upload supporting documents and record parts. Every file is fingerprinted and checked against the product and components." />
    {error && <ErrorBox message={error} />}
    <div className="repair-list">{repairs.map(r => <Link className="repair-card card" key={r.id} to={`/technician/evidence/${r.repair_id}`}>
      <div className="repair-card-icon"><ScanSearch size={21} /></div>
      <div className="repair-card-main"><div className="row-between"><b>{r.repair_id}</b><Badge status={r.status} /></div><p>{r.issue_description}</p><span className="muted">Product #{r.product_id}</span></div>
    </Link>)}</div>
    {!repairs.length && !error && <Card><Empty title="No assigned repairs" /></Card>}
  </>
}

/* ============================================================
   EVIDENCE CHECK  ·  /technician/evidence/:repairId
   POST /documents (returns file_hash + content_validation)
   POST /parts     (returns fraud_detected + fraud_flags)
   GET  /api/public/documents/{id}/verify
   ============================================================ */
const UPLOAD_STATES = ['DIAGNOSING', 'IN_REPAIR', 'PART_REPLACED', 'COMPLETED']
const PART_STATES = ['IN_REPAIR', 'PART_REPLACED']

export function TechnicianEvidence() {
  const { repairId } = useParams()
  const [repair, setRepair] = useState<Repair | null>(null)
  const [docs, setDocs] = useState<EvidenceDocument[]>([])
  const [parts, setParts] = useState<Part[]>([])
  const [docType, setDocType] = useState('REPAIR_REPORT')
  const [file, setFile] = useState<File | null>(null)
  const [desc, setDesc] = useState('')
  const [part, setPart] = useState({ part_name: '', old_part_serial: '', new_part_serial: '', warranty_months: '0' })
  const [upload, setUpload] = useState<UploadResult | null>(null)
  const [partResult, setPartResult] = useState<AddPartResult | null>(null)
  const [checks, setChecks] = useState<Record<number, DocumentVerification>>({})
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')

  const load = async () => {
    if (!repairId) return
    try {
      const r = await technicianApi.repairs()
      const found = r.data.find(x => x.repair_id === repairId)
      if (!found) throw new Error('Repair not found or not assigned to you')
      setRepair(found)
      const [d, p] = await Promise.all([evidenceApi.documents(repairId), technicianApi.parts(repairId)])
      setDocs(d.data); setParts(p.data)
    } catch (e) { setError(errorMessage(e)) }
  }
  useEffect(() => { load() }, [repairId])

  const send = async (e: FormEvent) => {
    e.preventDefault(); if (!file || !repairId) return
    setBusy('upload'); setError(''); setUpload(null)
    try { setUpload((await evidenceApi.upload(repairId, file, docType, desc)).data); setFile(null); setDesc(''); await load() }
    catch (err) { setError(errorMessage(err)) } finally { setBusy('') }
  }
  const addPart = async (e: FormEvent) => {
    e.preventDefault(); if (!repairId) return
    setBusy('part'); setError(''); setPartResult(null)
    try {
      setPartResult((await evidenceApi.addPart(repairId, { ...part, warranty_months: Number(part.warranty_months) })).data)
      setPart({ part_name: '', old_part_serial: '', new_part_serial: '', warranty_months: '0' }); await load()
    } catch (err) { setError(errorMessage(err)) } finally { setBusy('') }
  }
  const verify = async (id: number) => {
    setBusy(`v${id}`)
    try { const r = await passportApi.verifyDocument(id); setChecks(c => ({ ...c, [id]: r.data })) } catch (e) { setError(errorMessage(e)) } finally { setBusy('') }
  }

  if (error && !repair) return <ErrorBox message={error} />
  if (!repair) return <div className="loading-page">Loading evidence workspace…</div>
  const canUpload = UPLOAD_STATES.includes(repair.status)
  const canPart = PART_STATES.includes(repair.status)

  return <>
    <Link className="back-link" to="/technician/evidence"><ArrowLeft size={16} /> Back to repairs</Link>
    <SectionTitle eyebrow="EVIDENCE CHECK" title={repair.repair_id} description={repair.issue_description} action={<Badge status={repair.status} />} />
    {error && <ErrorBox message={error} />}
    <div className="detail-grid">
      <div className="stack">
        <Card>
          <div className="card-heading"><div><span className="eyebrow">DOCUMENTS</span><h2>Upload & validate</h2></div></div>
          {canUpload ? <form onSubmit={send} className="upload-form">
            <select value={docType} onChange={e => setDocType(e.target.value)}>
              {['REPAIR_REPORT', 'INVOICE', 'WARRANTY', 'BEFORE_PHOTO', 'AFTER_PHOTO', 'OTHER'].map(t => <option key={t}>{t}</option>)}
            </select>
            <input type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" onChange={e => setFile(e.target.files?.[0] || null)} />
            <input placeholder="Description (optional)" value={desc} onChange={e => setDesc(e.target.value)} />
            <Button type="submit" loading={busy === 'upload'} disabled={!file}><Upload size={16} /> Upload & check</Button>
          </form> : <div className="bc-note">Documents can be uploaded once diagnosis has started. Current status: {repair.status.replaceAll('_', ' ')}.</div>}

          {upload && <div style={{ marginTop: 16, display: 'grid', gap: 10 }}>
            <div className="bc-actions"><b>{upload.file_name}</b>
              <Pill tone={upload.content_validation.fraud_detected ? (upload.content_validation.severity === 'HIGH' ? 'bad' : 'warn') : 'good'}>
                {upload.content_validation.fraud_detected ? `FLAGGED · ${upload.content_validation.severity}` : 'NO ISSUES FOUND'}
              </Pill></div>
            <Hash label="SHA-256 of uploaded file" value={upload.file_hash} />
            <p className="muted">{upload.content_validation.performed ? `Text extracted from the document (${upload.content_validation.text_length} characters) and compared with the product and recorded parts.` : 'No readable text could be extracted, so content checks were limited.'}</p>
            <FlagList flags={upload.content_validation.fraud_flags} emptyText="Document content matches the registered product." />
          </div>}
        </Card>

        <Card>
          <div className="card-heading"><div><span className="eyebrow">UPLOADED FILES</span><h2>{docs.length} document{docs.length === 1 ? '' : 's'}</h2></div></div>
          {docs.length ? docs.map(d => <div className="bc-doc" key={d.id}>
            <FileText size={18} />
            <div className="grow">
              <a href={assetUrl(d.file_url)} target="_blank" rel="noreferrer"><b>{d.file_name}</b></a>
              <span>{d.document_type.replaceAll('_', ' ')} · {fmtDate(d.created_at)}</span>
              <Hash label="SHA-256" value={d.file_hash} />
              {checks[d.id] && <div style={{ marginTop: 8 }}><Check ok={checks[d.id].verified} label={checks[d.id].verified ? 'File unchanged' : 'File changed or missing'} /></div>}
            </div>
            <Button variant="secondary" loading={busy === `v${d.id}`} onClick={() => verify(d.id)}><FileSearch size={14} /> Verify</Button>
          </div>) : <p className="muted">No documents uploaded yet.</p>}
        </Card>
      </div>

      <div className="stack">
        <Card>
          <div className="card-heading"><div><span className="eyebrow">PARTS</span><h2>Record a component</h2></div></div>
          {parts.length > 0 && <div className="part-list" style={{ marginBottom: 14 }}>{parts.map(p => <div className="part-row" key={p.id}><div><b>{p.part_name}</b><span>{p.old_part_serial || '—'} → {p.new_part_serial || '—'}</span></div><span>{p.warranty_months} mo</span></div>)}</div>}
          {canPart ? <form className="form-grid compact" onSubmit={addPart}>
            <label className="full-span">Part name<input required value={part.part_name} onChange={e => setPart({ ...part, part_name: e.target.value })} /></label>
            <label>Old serial<input value={part.old_part_serial} onChange={e => setPart({ ...part, old_part_serial: e.target.value })} /></label>
            <label>New serial<input value={part.new_part_serial} onChange={e => setPart({ ...part, new_part_serial: e.target.value })} /></label>
            <label>Warranty months<input type="number" min="0" value={part.warranty_months} onChange={e => setPart({ ...part, warranty_months: e.target.value })} /></label>
            <div className="form-actions full-span"><Button type="submit" loading={busy === 'part'}><Plus size={16} /> Add & check part</Button></div>
          </form> : <div className="bc-note">Parts can be recorded while the repair is in progress.</div>}
          {partResult && <div style={{ marginTop: 14 }}>
            <Pill tone={partResult.fraud_detected ? 'bad' : 'good'}>{partResult.fraud_detected ? 'COMPONENT FLAGGED' : 'COMPONENT OK'}</Pill>
            <FlagList flags={partResult.fraud_flags} emptyText={`${partResult.part_name} was recorded with no mismatches.`} />
          </div>}
        </Card>
        <Card>
          <span className="eyebrow">HOW IT WORKS</span><h2>Automatic checks</h2>
          <p className="muted" style={{ lineHeight: 1.6 }}>Each uploaded file is fingerprinted with SHA-256 so later edits can be detected. Its text is read and compared with the registered product brand and the components you recorded. Mismatches are flagged here and count against the product's trust score.</p>
          <p className="tiny-note"><Wrench size={11} /> Completing the repair also writes its record hash to the blockchain.</p>
        </Card>
      </div>
    </div>
  </>
}

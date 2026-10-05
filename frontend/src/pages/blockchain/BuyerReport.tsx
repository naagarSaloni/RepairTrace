import { FormEvent, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { CheckCircle2, AlertTriangle, ClipboardCheck, Search, ShieldCheck } from 'lucide-react'
import { passportApi } from '../../api/blockchain'
import { errorMessage } from '../../api/client'
import type { BuyerReport as Report } from '../../types/blockchain'
import { Badge, Button, Card, ErrorBox } from '../../components/ui'
import { Check, FlagList, Hash, RiskPill, TrustMeter } from '../../components/blockchain/Widgets'

export default function BuyerReport() {
  const params = useParams()
  const [uid, setUid] = useState(params.productUid || '')
  const [data, setData] = useState<Report | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const load = async (value: string) => {
    if (!value.trim()) return
    setBusy(true); setError(''); setData(null)
    try { setData((await passportApi.buyerReport(value.trim())).data) } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) }
  }
  useEffect(() => { if (params.productUid) load(params.productUid) }, [params.productUid])
  const submit = (e: FormEvent) => { e.preventDefault(); load(uid) }
  const good = (data?.trust.trust_score ?? 0) >= 80

  return <div className="public-verify"><div className="verify-wrap">
    <div className="verify-brand"><div className="brand-mark"><ShieldCheck /></div><div><b>RepairTrace</b><span>Buyer verification</span></div></div>
    <div className="verify-intro">
      <span className="eyebrow">BUYING SECOND-HAND?</span>
      <h1>Buyer verification report</h1>
      <p>Check a product's repair history, trust score and blockchain proof before you buy it.</p>
    </div>
    <Card><form className="verify-form" onSubmit={submit}>
      <input value={uid} onChange={e => setUid(e.target.value)} placeholder="e.g. PRD-7F3A91B22C" />
      <Button type="submit" loading={busy}><Search size={17} /> Generate report</Button>
    </form></Card>
    {error && <ErrorBox message={error} />}

    {data && <>
      <Card className="verification-result">
        <div className="bc-head">
          <TrustMeter score={data.trust.trust_score} level={data.trust.risk_level} />
          <div className="grow">
            <span className="eyebrow">{data.report_type.toUpperCase()}</span>
            <h2>{data.product.product_name}</h2>
            <p className="muted">{[data.product.brand, data.product.model].filter(Boolean).join(' · ')}{data.product.serial_number ? ` · S/N ${data.product.serial_number}` : ''}</p>
            <RiskPill level={data.trust.risk_level} />
          </div>
          <Link className="btn btn-secondary" to={`/passport/${data.product.product_uid}`}>Full passport</Link>
        </div>
        <div className={`bc-reco ${good ? 'good' : 'warn'}`} style={{ marginTop: 18 }}>{good ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}<span>{data.buyer_recommendation}</span></div>
        <div className="bc-counts">
          <div><b>{data.repair_summary.total_repairs}</b><small>Total repairs</small></div>
          <div><b>{data.repair_summary.completed_repairs}</b><small>Completed</small></div>
          <div><b>{data.repair_summary.hash_verified_repairs}</b><small>Hash verified</small></div>
          <div><b>{data.repair_summary.blockchain_verified_repairs}</b><small>On blockchain</small></div>
        </div>
        <FlagList flags={data.trust.risk_flags} />
      </Card>

      <Card>
        <div className="card-heading"><div><span className="eyebrow">REPAIR RECORDS</span><h2>Verification per repair</h2></div><ClipboardCheck size={20} /></div>
        {data.repairs.length ? <div className="bc-scroll"><table className="bc-table">
          <thead><tr><th>REPAIR</th><th>ISSUE / DIAGNOSIS</th><th>STATUS</th><th>PROOF</th></tr></thead>
          <tbody>{data.repairs.map(r => <tr key={r.repair_id}>
            <td><b>{r.repair_id}</b></td>
            <td>{r.issue_description}<br /><span className="muted">{r.diagnosis || 'No diagnosis recorded'}</span></td>
            <td><Badge status={r.status} /></td>
            <td><div className="bc-actions"><Check ok={r.hash_verified} label="SHA-256" /><Check ok={r.blockchain_verified} label="Blockchain" /></div>
              {r.record_hash && <div style={{ marginTop: 8 }}><Hash label="Record hash" value={r.record_hash} /></div>}
              {r.blockchain_tx_hash && <div style={{ marginTop: 8 }}><Hash label="Transaction" value={r.blockchain_tx_hash} /></div>}</td>
          </tr>)}</tbody></table></div> : <p className="muted">No repairs have been recorded for this product.</p>}
      </Card>
    </>}
  </div></div>
}

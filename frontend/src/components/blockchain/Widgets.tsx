import { AlertTriangle, CheckCircle2, ShieldAlert, ShieldCheck, ShieldX, XCircle } from 'lucide-react'
import type { ReactNode } from 'react'
import type { FraudFlag, RiskLevel, VerificationStatus } from '../../types/blockchain'
import '../../styles/blockchain.css'

type Tone = 'good' | 'warn' | 'bad' | 'neutral'

export const Pill = ({ tone, children }: { tone: Tone; children: ReactNode }) => <span className={`bc-pill ${tone}`}>{children}</span>

export function TrustMeter({ score, level }: { score: number; level: RiskLevel }) {
  const cls = level === 'LOW' ? '' : level === 'MEDIUM' ? 'medium' : 'high'
  return <div className={`bc-meter ${cls}`} style={{ ['--v' as any]: Math.max(0, Math.min(100, score)) }}><div><span><b>{Math.round(score)}</b><small>TRUST</small></span></div></div>
}

export const RiskPill = ({ level }: { level: RiskLevel }) =>
  <Pill tone={level === 'LOW' ? 'good' : level === 'MEDIUM' ? 'warn' : 'bad'}>{level} RISK</Pill>

export function VerifyPill({ status }: { status: VerificationStatus }) {
  if (status === 'BLOCKCHAIN_VERIFIED') return <Pill tone="good"><ShieldCheck size={12} /> BLOCKCHAIN VERIFIED</Pill>
  if (status === 'HASH_VERIFIED') return <Pill tone="neutral"><ShieldCheck size={12} /> HASH VERIFIED</Pill>
  if (status === 'VERIFICATION_FAILED') return <Pill tone="bad"><ShieldX size={12} /> VERIFICATION FAILED</Pill>
  return <Pill tone="warn"><ShieldAlert size={12} /> NOT VERIFIED YET</Pill>
}

export const Check = ({ ok, label }: { ok: boolean; label: string }) =>
  <Pill tone={ok ? 'good' : 'warn'}>{ok ? <CheckCircle2 size={12} /> : <XCircle size={12} />} {label}</Pill>

// Accepts plain strings (risk flags) or {type, severity, message} objects (fraud flags)
export function FlagList({ flags, emptyText = 'No risk indicators detected.' }: { flags: (string | FraudFlag)[]; emptyText?: string }) {
  if (!flags?.length) return <ul className="bc-flags clear"><li><CheckCircle2 size={16} />{emptyText}</li></ul>
  return <ul className="bc-flags">{flags.map((f, i) => typeof f === 'string'
    ? <li key={i}><AlertTriangle size={16} />{f}</li>
    : <li key={i} className={f.severity === 'HIGH' ? 'high' : ''}><AlertTriangle size={16} /><div>{f.type.replaceAll('_', ' ')} · {f.severity}<span>{f.message}</span></div></li>)}</ul>
}

export const Hash = ({ label, value }: { label: string; value?: string | null }) =>
  value ? <div className="bc-kv"><small>{label}</small><code className="bc-hash">{value}</code></div> : null

export const fmtDate = (d?: string | null) => d ? new Date(d).toLocaleString() : '—'

import { Link } from 'react-router-dom'
import { ArrowRight, Laptop } from 'lucide-react'
import type { Repair } from '../types'
import { Badge, Card } from './ui'
export default function RepairCard({repair}:{repair:Repair}){return <Card className="repair-card"><div className="repair-card-icon"><Laptop size={21}/></div><div className="repair-card-main"><div className="row-between"><div><b>{repair.repair_id}</b><span className="muted">Product #{repair.product_id}</span></div><Badge status={repair.status}/></div><p>{repair.issue_description}</p><div className="repair-meta"><span>{repair.created_at?new Date(repair.created_at).toLocaleDateString():'Recently'}</span>{repair.technician_id&&<span>Technician assigned</span>}</div></div><Link className="icon-link" to={`/customer/repairs/${repair.repair_id}`}><ArrowRight size={18}/></Link></Card>}

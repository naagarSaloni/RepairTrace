import { api } from './client'
import type {
  AddPartResult, AiRiskResult, BuyerReport, Dispute, DocumentVerification, EvidenceDocument,
  OwnershipHistory, ProductPassport, RiskResult, TransferResult, UploadResult, Vendor
} from '../types/blockchain'

const e = encodeURIComponent

// Public (no login)
export const passportApi = {
  get: (uid: string) => api.get<ProductPassport>(`/api/public/products/${e(uid)}`),
  risk: (uid: string) => api.get<RiskResult>(`/api/public/products/${e(uid)}/risk`),
  verifyDocument: (id: number) => api.get<DocumentVerification>(`/api/public/documents/${id}/verify`),
  buyerReport: (uid: string) => api.get<BuyerReport>(`/api/buyer/products/${e(uid)}/report`)
}

// Customer / owner
export const riskApi = {
  analyze: (uid: string) => api.get<RiskResult>(`/api/risk/products/${e(uid)}`),
  analyzeAi: (uid: string) => api.get<AiRiskResult>(`/api/ai-risk/products/${e(uid)}`)
}
export const ownershipApi = {
  // the backend reads these as query parameters, not a JSON body
  transfer: (product_uid: string, new_owner_email: string, transfer_reason?: string) =>
    api.post<TransferResult>('/api/ownership/transfer', null, { params: { product_uid, new_owner_email, ...(transfer_reason ? { transfer_reason } : {}) } }),
  history: (uid: string) => api.get<OwnershipHistory>(`/api/ownership/${e(uid)}/history`)
}
export const disputesApi = {
  create: (repairId: string, reason: string, description?: string) =>
    api.post(`/api/disputes/repairs/${e(repairId)}`, null, { params: { reason, ...(description ? { description } : {}) } }),
  mine: () => api.get<Dispute[]>('/api/disputes/my'),
  all: () => api.get<Dispute[]>('/api/disputes/all'),
  resolve: (id: number, admin_response: string) => api.patch(`/api/disputes/${id}/resolve`, null, { params: { admin_response } })
}

// Admin
export const vendorApi = {
  list: () => api.get<Vendor[]>('/api/admin/vendors'),
  create: (d: { user_id: number; business_name: string; phone?: string; address?: string; specialization?: string }) =>
    api.post('/api/admin/vendors', null, { params: Object.fromEntries(Object.entries(d).filter(([, v]) => v !== undefined && v !== '')) }),
  verify: (id: number) => api.patch(`/api/admin/vendors/${id}/verify`),
  reject: (id: number) => api.patch(`/api/admin/vendors/${id}/reject`)
}

// Technician (same endpoints as before, typed to expose the new fraud-check and file-hash fields)
export const evidenceApi = {
  documents: (repairId: string) => api.get<EvidenceDocument[]>(`/api/technician/repairs/${e(repairId)}/documents`),
  upload: (repairId: string, file: File, document_type: string, description: string) => {
    const form = new FormData(); form.append('document_type', document_type); form.append('file', file); if (description) form.append('description', description)
    return api.post<UploadResult>(`/api/technician/repairs/${e(repairId)}/documents`, form)
  },
  addPart: (repairId: string, d: { part_name: string; old_part_serial?: string; new_part_serial?: string; warranty_months: number }) => {
    const form = new FormData(); Object.entries(d).forEach(([k, v]) => form.append(k, String(v ?? ''))); return api.post<AddPartResult>(`/api/technician/repairs/${e(repairId)}/parts`, form)
  }
}

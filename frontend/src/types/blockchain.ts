// Types for the blockchain / trust add-on backend (disputes, ownership, risk, vendors, passport, buyer report)

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH'
export type VerificationStatus = 'BLOCKCHAIN_VERIFIED' | 'HASH_VERIFIED' | 'VERIFICATION_FAILED' | 'NOT_VERIFIED'
export type FraudFlag = { type: string; severity: 'LOW' | 'MEDIUM' | 'HIGH'; message: string }

/* ---------- Public product passport: GET /api/public/products/{uid} ---------- */
export type PassportComponent = { part_name: string; old_part_serial?: string | null; new_part_serial?: string | null; warranty_months: number; replaced_at?: string | null }
export type PassportDocument = { id: number; document_type: string; file_name: string; file_url: string; file_hash?: string | null; description?: string | null; uploaded_at?: string | null }
export type PassportHistory = { id?: number; status: string; description?: string | null; created_at?: string | null; blockchain_tx_hash?: string | null }
export type PassportRepair = {
  repair_id: string; issue_description: string; diagnosis?: string | null; status: string
  created_at?: string | null; updated_at?: string | null
  record_hash?: string | null; hash_verified: boolean
  blockchain_tx_hash?: string | null; blockchain_verified: boolean
  verification_status: VerificationStatus
  components: PassportComponent[]; documents: PassportDocument[]; status_history: PassportHistory[]
}
export type ProductPassport = {
  verified: boolean
  passport: { product_uid: string; product_name: string; brand?: string | null; model?: string | null; serial_number?: string | null }
  summary: { total_repairs: number; completed_repairs: number; hash_verified_repairs: number; blockchain_verified_repairs: number; cancelled_repairs: number; trust_score: number; risk_level: RiskLevel; risk_flags: string[] }
  repair_history: PassportRepair[]
  message: string
}

/* ---------- Document integrity: GET /api/public/documents/{id}/verify ---------- */
export type DocumentVerification = { verified: boolean; document_id: number; file_name: string; stored_hash: string | null; current_hash: string | null; message: string }

/* ---------- Buyer report: GET /api/buyer/products/{uid}/report ---------- */
export type BuyerReport = {
  verified: boolean; report_type: string
  product: ProductPassport['passport']
  trust: { trust_score: number; risk_level: RiskLevel; risk_flags: string[] }
  repair_summary: { total_repairs: number; completed_repairs: number; hash_verified_repairs: number; blockchain_verified_repairs: number }
  repairs: { repair_id: string; issue_description: string; diagnosis?: string | null; status: string; record_hash?: string | null; hash_verified: boolean; blockchain_tx_hash?: string | null; blockchain_verified: boolean }[]
  buyer_recommendation: string
}

/* ---------- Risk: GET /api/risk/products/{uid}  and  /api/ai-risk/products/{uid} ---------- */
export type RiskResult = { product_uid: string; product_name: string; trust_score: number; risk_level: RiskLevel; risk_flags: string[]; total_repairs: number }
export type AiRiskResult = RiskResult & { analysis_type: string; assessment: string; recommendation: string }

/* ---------- Ownership ---------- */
export type OwnerRef = { id: number | null; name: string | null; email: string | null }
export type OwnershipTransfer = { id: number; previous_owner: OwnerRef; new_owner: OwnerRef; transfer_reason?: string | null; blockchain_tx_hash?: string | null; transferred_at: string }
export type OwnershipHistory = { product_uid: string; current_owner_id: number; ownership_transfers: OwnershipTransfer[] }
export type TransferResult = { message: string; product_uid: string; previous_owner_id: number; new_owner_id: number; new_owner_name: string; new_owner_email: string; transfer_reason?: string | null; transferred_at: string }

/* ---------- Disputes ---------- */
export type Dispute = { id: number; repair_id: number; raised_by?: number; reason: string; description?: string | null; status: 'OPEN' | 'RESOLVED' | string; admin_response?: string | null; created_at: string; resolved_at?: string | null; resolved_by?: number | null }

/* ---------- Vendors (admin) ---------- */
export type Vendor = { id: number; user_id: number; name?: string | null; email?: string | null; business_name: string; phone?: string | null; address?: string | null; specialization?: string | null; verification_status: 'PENDING' | 'VERIFIED' | 'REJECTED' | string; verified_at?: string | null; created_at?: string }

/* ---------- Technician evidence (documents + parts with fraud checks) ---------- */
export type ContentValidation = { performed: boolean; text_length: number; fraud_detected: boolean; severity: 'LOW' | 'MEDIUM' | 'HIGH'; fraud_flags: FraudFlag[] }
export type UploadResult = { message: string; document_id: number; document_type: string; file_name: string; file_url: string; file_hash: string; content_validation: ContentValidation }
export type AddPartResult = { message: string; part_id: number; part_name: string; new_part_serial?: string | null; fraud_detected: boolean; fraud_flags: FraudFlag[] }
export type EvidenceDocument = { id: number; repair_id: number; document_type: string; file_name: string; file_url: string; file_hash?: string | null; description?: string | null; uploaded_by: number; created_at?: string }

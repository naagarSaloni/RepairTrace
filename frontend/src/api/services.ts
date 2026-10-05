import { api } from './client'
import type { Document, History, Part, Product, PublicProduct, Repair, Technician, TokenResponse } from '../types'

export const authApi = {
  login: (email:string,password:string) => api.post<TokenResponse>('/api/auth/login',{email,password}),
  register: (name:string,email:string,password:string) => api.post<TokenResponse>('/api/auth/register',{name,email,password,role:'CUSTOMER'})
}
export const productsApi = {
  list: () => api.get<Product[]>('/api/products/my-products'),
  get: (uid:string) => api.get<Product>(`/api/products/${encodeURIComponent(uid)}`),
  create: (data:Partial<Product>) => api.post<Product>('/api/products/',data)
}
export const repairsApi = {
  create: (data:{product_id:number;issue_description:string}) => api.post<Repair>('/api/repairs/',data),
  listMine: () => api.get<Repair[]>('/api/repairs/my-repairs'),
  get: (id:string) => api.get<Repair>(`/api/repairs/${encodeURIComponent(id)}`),
  history: (id:string) => api.get<History[]>(`/api/repairs/${encodeURIComponent(id)}/history`),
  verifyHash: (id:string) => api.get(`/api/repairs/${encodeURIComponent(id)}/verify-hash`),
  verify: (id:string) => api.post(`/api/repairs/${encodeURIComponent(id)}/verify`),
  returnRepair: (id:string) => api.post(`/api/repairs/${encodeURIComponent(id)}/return`)
}
export const technicianApi = {
  repairs: () => api.get<Repair[]>('/api/technician/repairs'),
  startDiagnosis: (id:string) => api.post(`/api/technician/repairs/${encodeURIComponent(id)}/start-diagnosis`),
  diagnosis: (id:string, diagnosis:string) => { const form=new FormData(); form.append('diagnosis',diagnosis); return api.put(`/api/technician/repairs/${encodeURIComponent(id)}/diagnosis`,form) },
  startRepair: (id:string) => api.post(`/api/technician/repairs/${encodeURIComponent(id)}/start-repair`),
  addPart: (id:string,data:{part_name:string;old_part_serial?:string;new_part_serial?:string;warranty_months:number}) => { const form=new FormData(); Object.entries(data).forEach(([k,v])=>form.append(k,String(v ?? ''))); return api.post(`/api/technician/repairs/${encodeURIComponent(id)}/parts`,form) },
  parts: (id:string) => api.get<Part[]>(`/api/technician/repairs/${encodeURIComponent(id)}/parts`),
  markPartReplaced: (id:string) => api.post(`/api/technician/repairs/${encodeURIComponent(id)}/part-replaced`),
  uploadDocument: (id:string,file:File,document_type:string,description:string) => { const form=new FormData(); form.append('document_type',document_type); form.append('file',file); if(description) form.append('description',description); return api.post(`/api/technician/repairs/${encodeURIComponent(id)}/documents`,form) },
  documents: (id:string) => api.get<Document[]>(`/api/technician/repairs/${encodeURIComponent(id)}/documents`),
  complete: (id:string) => api.post(`/api/technician/repairs/${encodeURIComponent(id)}/complete`)
}
export const adminApi = {
  technicians: () => api.get<Technician[]>('/api/admin/technicians'),
  assign: (repairId:string,technicianId:number) => api.post(`/api/admin/repairs/${encodeURIComponent(repairId)}/assign/${technicianId}`)
}
export const publicApi = { verify: (uid:string) => api.get<PublicProduct>(`/api/public/products/${encodeURIComponent(uid)}`) }

export const systemApi = { root: () => api.get('/'), health: () => api.get('/health') }

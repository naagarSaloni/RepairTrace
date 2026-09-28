import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { authApi } from '../api/services'
import type { Role, UserSession } from '../types'

const Ctx = createContext<any>(null)
const parseToken = (token:string): Partial<UserSession> => { try { const p=JSON.parse(atob(token.split('.')[1].replace(/-/g,'+').replace(/_/g,'/'))); return {role:p.role,email:p.email}} catch { return {} } }
export function AuthProvider({children}:{children:ReactNode}) {
  const [session,setSession]=useState<UserSession|null>(()=>{const raw=localStorage.getItem('repairtrace_session'); return raw?JSON.parse(raw):null})
  const save=(token:string)=>{ const p=parseToken(token); const s={token,role:p.role as Role,email:p.email||''}; localStorage.setItem('repairtrace_token',token); localStorage.setItem('repairtrace_session',JSON.stringify(s)); setSession(s) }
  const login=async(email:string,password:string)=>{const {data}=await authApi.login(email,password); save(data.access_token); return data}
  const register=async(name:string,email:string,password:string)=>{const {data}=await authApi.register(name,email,password); save(data.access_token); return data}
  const logout=()=>{localStorage.removeItem('repairtrace_token');localStorage.removeItem('repairtrace_session');setSession(null)}
  useEffect(()=>{const fn=()=>logout(); window.addEventListener('repairtrace:logout',fn); return()=>window.removeEventListener('repairtrace:logout',fn)},[])
  const value=useMemo(()=>({session,isAuthenticated:!!session,login,register,logout}),[session])
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
export const useAuth=()=>useContext(Ctx)

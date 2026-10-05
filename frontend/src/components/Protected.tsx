import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import type { Role } from '../types'
export default function Protected({roles}:{roles?:Role[]}){const {session}=useAuth();if(!session)return <Navigate to="/login" replace/>;if(roles&&!roles.includes(session.role))return <Navigate to={`/${session.role.toLowerCase()}/dashboard`} replace/>;return <Outlet/>}

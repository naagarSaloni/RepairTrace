import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Protected from './components/Protected'
import { Login, Register } from './pages/Auth'
import Landing from './pages/Landing'
import PublicVerify from './pages/PublicVerify'
import { CustomerDashboard, Products, NewProduct, ProductDetails, NewRepair, Repairs, RepairDetails } from './pages/customer'
import { TechnicianDashboard, TechnicianRepairs, TechnicianRepair, AdminDashboard, AdminTechnicians } from './pages/staff'
import { useAuth } from './context/AuthContext'
function Home(){const {session}=useAuth();return session?<Navigate to={`/${session.role.toLowerCase()}/dashboard`} replace/>:<Landing/>}
export default function App(){return <BrowserRouter><Routes><Route path="/" element={<Home/>}/><Route path="/login" element={<Login/>}/><Route path="/register" element={<Register/>}/><Route path="/verify" element={<PublicVerify/>}/><Route element={<Layout/>}><Route element={<Protected roles={['CUSTOMER']}/> }><Route path="/customer/dashboard" element={<CustomerDashboard/>}/><Route path="/customer/products" element={<Products/>}/><Route path="/customer/products/new" element={<NewProduct/>}/><Route path="/customer/products/:productUid" element={<ProductDetails/>}/><Route path="/customer/repairs" element={<Repairs/>}/><Route path="/customer/repairs/new" element={<NewRepair/>}/><Route path="/customer/repairs/:repairId" element={<RepairDetails/>}/></Route><Route element={<Protected roles={['TECHNICIAN']}/> }><Route path="/technician/dashboard" element={<TechnicianDashboard/>}/><Route path="/technician/repairs" element={<TechnicianRepairs/>}/><Route path="/technician/repairs/:repairId" element={<TechnicianRepair/>}/></Route><Route element={<Protected roles={['ADMIN']}/> }><Route path="/admin/dashboard" element={<AdminDashboard/>}/><Route path="/admin/technicians" element={<AdminTechnicians/>}/></Route></Route><Route path="*" element={<Navigate to="/" replace/>}/></Routes></BrowserRouter>}

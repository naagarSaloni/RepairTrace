/*
 * Route + navigation definitions for the blockchain add-on pages.
 * Nothing in the existing frontend imports this file yet. See INTEGRATION.md for the few lines
 * that connect it to App.tsx and Layout.tsx.
 */
import { Route } from 'react-router-dom'
import { ArrowLeftRight, BadgeCheck, Gauge, Gavel, ScanSearch, Store } from 'lucide-react'
import PublicPassport from '../pages/blockchain/PublicPassport'
import BuyerReport from '../pages/blockchain/BuyerReport'
import { CustomerDisputes, OwnershipTransferPage, ProductTrust } from '../pages/blockchain/customer'
import { AdminDisputes, AdminVendors } from '../pages/blockchain/admin'
import { TechnicianEvidence, TechnicianEvidenceList } from '../pages/blockchain/technician'

/* Public routes: place directly inside <Routes>, next to /verify */
export const blockchainPublicRoutes = (
  <>
    <Route path="/passport" element={<PublicPassport />} />
    <Route path="/passport/:productUid" element={<PublicPassport />} />
    <Route path="/buyer-report" element={<BuyerReport />} />
    <Route path="/buyer-report/:productUid" element={<BuyerReport />} />
  </>
)

/* Role routes: place inside the matching <Route element={<Protected roles={[...]}/>}> block */
export const blockchainCustomerRoutes = (
  <>
    <Route path="/customer/trust" element={<ProductTrust />} />
    <Route path="/customer/ownership" element={<OwnershipTransferPage />} />
    <Route path="/customer/disputes" element={<CustomerDisputes />} />
  </>
)
export const blockchainTechnicianRoutes = (
  <>
    <Route path="/technician/evidence" element={<TechnicianEvidenceList />} />
    <Route path="/technician/evidence/:repairId" element={<TechnicianEvidence />} />
  </>
)
export const blockchainAdminRoutes = (
  <>
    <Route path="/admin/disputes" element={<AdminDisputes />} />
    <Route path="/admin/vendors" element={<AdminVendors />} />
  </>
)

/* Sidebar links in the same [path, label, Icon] shape that Layout.tsx uses */
export const blockchainNavLinks: Record<'CUSTOMER' | 'TECHNICIAN' | 'ADMIN', [string, string, any][]> = {
  CUSTOMER: [['/customer/trust', 'Trust Score', Gauge], ['/customer/ownership', 'Ownership', ArrowLeftRight], ['/customer/disputes', 'Disputes', Gavel], ['/passport', 'Product Passport', BadgeCheck]],
  TECHNICIAN: [['/technician/evidence', 'Evidence Check', ScanSearch]],
  ADMIN: [['/admin/disputes', 'Disputes', Gavel], ['/admin/vendors', 'Vendors', Store]]
}

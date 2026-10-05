# RepairTrace Frontend

A demo-ready React + Vite frontend for the RepairTrace FastAPI backend.

## What is included

- Light, responsive SaaS-style UI
- Customer, Technician and Admin dashboards
- Login and customer registration
- Product registration + QR image
- Repair creation + repair timeline
- Customer record-hash verification
- Customer completion verification and return flow
- Technician diagnosis, parts, documents and completion workflow
- Admin technician listing and repair assignment
- Public product verification
- API/root/health connectivity check in the admin dashboard
- Loading, empty and error states

## Run locally

### 1. Start the backend

From the backend directory:

```bash
uvicorn app.main:app --reload
```

The frontend assumes the backend is available at `http://127.0.0.1:8000` during development.

### 2. Install frontend dependencies

```bash
npm install
```

### 3. Start frontend

```bash
npm run dev
```

Open the Vite URL shown in the terminal (normally `http://localhost:5173`).

The Vite dev proxy forwards `/api`, `/uploads` and `/health` to the FastAPI server, so local development does not require a CORS change.

## Environment

Copy `.env.example` to `.env`.

For local development, leave `VITE_API_URL` blank. For a deployed backend, set it to the FastAPI origin, for example:

```env
VITE_API_URL=https://api.example.com
```

## Demo flow

1. Sign in with an existing Customer, Technician or Admin account.
2. Customer: register a product.
3. Customer: create a repair request.
4. Admin: assign the repair ID to a technician.
5. Technician: start diagnosis, save diagnosis, start repair, add a part, mark it replaced, upload a document and complete the repair.
6. Customer: open the repair timeline, verify the SHA-256 record, verify completion and confirm return.
7. Open `/verify` to test public product registration verification.

## Blockchain note

The current backend exposes record hashing and fields reserved for blockchain transaction hashes, but it does not currently submit live smart-contract transactions. This frontend therefore labels the current feature as **record integrity / SHA-256 verification** and does not fabricate blockchain confirmations.

A later phase can add Solidity + an Ethereum-compatible test network + ethers.js/web3.py + MetaMask without redesigning the core screens.

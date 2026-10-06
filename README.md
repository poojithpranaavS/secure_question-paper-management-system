#Video Demonstration
https://drive.google.com/drive/folders/1iyuRQpCdx1FIeROXhQNk8BGOa-At1e5J?usp=sharing

# Secure Cloud-Based Question Paper Management System

## 1. Project Description

The **Secure Cloud-Based Question Paper Management System** is a secure web application for managing government competitive-exam question papers with confidentiality, integrity, controlled access, approval workflows, scheduled release, secure downloads, and auditability.

The system provides role-based access control (RBAC), JWT authentication, multi-factor authentication support, encrypted question-paper storage, SHA-256 integrity verification, approval/rejection workflows, controlled release scheduling, secure downloads, and a tamper-evident audit log using hash chaining.

### Key Features

- JWT-based user authentication
- Role-Based Access Control (RBAC)
- Exam Authority and Question Setter roles
- PBKDF2-HMAC-SHA256 password hashing
- Multi-Factor Authentication (MFA)
- Secure question-paper upload
- PDF validation and file-size restrictions
- SHA-256 file integrity hashing
- AES-256-GCM encrypted storage
- Approval and rejection workflow
- Prevention of self-approval
- Controlled and scheduled release
- Authenticated secure downloads
- Audit logging
- Tamper-evident audit hash chain
- Audit-chain verification
- Cloud deployment using Render

---

## 2. Technologies and Tools Used

### Backend

- Python
- FastAPI
- SQLAlchemy
- SQLite for local development
- python-jose for JWT authentication
- Cryptography for AES-256-GCM encryption
- python-dotenv for environment variables
- Uvicorn

### Frontend

- React
- Vite
- JavaScript
- Axios
- CSS

### Security Technologies

- JWT bearer-token authentication
- PBKDF2-HMAC-SHA256 password hashing with 600,000 iterations
- Role-Based Access Control
- Multi-Factor Authentication
- AES-256-GCM encryption
- SHA-256 file hashing
- Audit hash chaining
- Approval and self-approval controls
- Controlled release scheduling

### Development and Deployment

- Git
- GitHub
- Render
- VS Code
- Postman

---

## 3. System Architecture

    +-----------------------------+
    |        React Frontend       |
    |        Vite + JavaScript    |
    +--------------+--------------+
                   |
              HTTPS / REST
                   |
                   v
    +-----------------------------+
    |       FastAPI Backend       |
    |                             |
    | Authentication / RBAC       |
    | Question Paper Management   |
    | Approval / Rejection        |
    | Controlled Release          |
    | Secure Downloads            |
    | Audit & Verification        |
    +--------------+--------------+
                   |
        +----------+----------+
        |                     |
        v                     v
    +-----------------+   +---------------------+
    |    Database     |   |   Secure Storage    |
    | SQLite /        |   | AES-256-GCM Files   |
    | SQLAlchemy      |   |                     |
    +-----------------+   +---------------------+

---

## 4. Project Structure

    secure_question_paper_system/
    ├── backend/
    │   ├── app/
    │   │   ├── database/
    │   │   │   ├── __init__.py
    │   │   │   └── connection.py
    │   │   ├── models/
    │   │   │   ├── __init__.py
    │   │   │   ├── user.py
    │   │   │   ├── question_paper.py
    │   │   │   └── audit_log.py
    │   │   ├── routes/
    │   │   │   ├── __init__.py
    │   │   │   ├── auth.py
    │   │   │   ├── question_papers.py
    │   │   │   ├── approvals.py
    │   │   │   ├── audit.py
    │   │   │   ├── downloads.py
    │   │   │   └── release.py
    │   │   ├── security/
    │   │   │   ├── __init__.py
    │   │   │   ├── authentication.py
    │   │   │   ├── authorization.py
    │   │   │   ├── encryption.py
    │   │   │   └── mfa.py
    │   │   ├── services/
    │   │   │   ├── __init__.py
    │   │   │   └── audit.py
    │   │   └── main.py
    │   ├── secure_storage/
    │   ├── .env
    │   ├── create_authority.py
    │   ├── migrate_audit_hashes.py
    │   ├── migrate_mfa.py
    │   ├── migrate_rejection.py
    │   ├── reset_setter.py
    │   ├── requirements.txt
    │   └── question_paper_system.db
    └── frontend/
        ├── public/
        ├── src/
        │   ├── assets/
        │   ├── components/
        │   ├── context/
        │   ├── pages/
        │   │   ├── Dashboard.jsx
        │   │   └── Login.jsx
        │   ├── services/
        │   │   └── api.js
        │   ├── App.jsx
        │   ├── index.css
        │   └── main.jsx
        ├── package.json
        └── ...

### Module Purpose

| Module | Purpose |
|---|---|
| `database/connection.py` | Database engine and session configuration |
| `models/user.py` | User and role model |
| `models/question_paper.py` | Question-paper metadata and lifecycle state |
| `models/audit_log.py` | Audit-log model |
| `routes/auth.py` | Authentication endpoints |
| `routes/question_papers.py` | Question-paper upload and management |
| `routes/approvals.py` | Approval and rejection workflow |
| `routes/audit.py` | Audit-log retrieval and hash-chain verification |
| `routes/downloads.py` | Authenticated secure downloads |
| `routes/release.py` | Controlled and scheduled release |
| `security/authentication.py` | Password hashing and verification |
| `security/authorization.py` | JWT authentication and RBAC |
| `security/encryption.py` | Question-paper encryption/decryption |
| `security/mfa.py` | MFA functionality |
| `services/audit.py` | Audit logging and hash-chain operations |
| `main.py` | FastAPI initialization, CORS and router registration |
| `frontend/pages/Login.jsx` | Login interface |
| `frontend/pages/Dashboard.jsx` | Role-based management dashboard |
| `frontend/services/api.js` | Frontend API communication |
| `frontend/index.css` | Application styling and responsive layout |

---

## 5. Installation and Setup

### Prerequisites

- Python 3.10 or later
- Node.js and npm
- Git

### Clone the Repository

    git clone https://github.com/poojithpranaavS/secure_question-paper-management-system.git
    cd secure-question-paper-management-system

### Backend Setup

    cd backend
    python -m venv .venv

### Windows

    .venv\Scripts\activate

### Linux/macOS

    source .venv/bin/activate

### Install Dependencies

    pip install -r requirements.txt

Configure the required environment variables in `backend/.env`:

    DATABASE_URL=sqlite:///./question_paper_system.db
    JWT_SECRET_KEY=your-secret-key
    QUESTION_PAPER_ENCRYPTION_KEY=your-encryption-key
    MFA_ENCRYPTION_KEY=your-mfa-encryption-key
    AUTHORITY_EMAIL=authority@exam.gov
    AUTHORITY_PASSWORD=your-authority-password

**Do not commit real production secrets to GitHub.**

### Run the Backend

    uvicorn app.main:app --reload

Backend:

    http://127.0.0.1:8000

### Frontend Setup

Open another terminal:

    cd frontend
    npm install
    npm run dev

Frontend:

    http://localhost:5173

---

## 6. Application Screenshots

### 6.1 Secure Login

The deployed system provides a dedicated authentication interface for authorized users.

<img width="1903" height="1046" alt="image" src="https://github.com/user-attachments/assets/baa1f7ad-b5f9-404e-9936-8e993355fb73" />


---

### 6.2 Approval Control Center

The Exam Authority receives a role-specific approval interface for managing the question-paper approval queue.

<img width="1406" height="734" alt="image" src="https://github.com/user-attachments/assets/750a4339-971c-4994-b253-7d659122bf59" />



---

## 7. Application Workflow

### Question Paper Upload

1. A Question Setter logs in.
2. JWT authentication verifies the session.
3. RBAC checks the user's role.
4. The uploaded file is validated as a PDF.
5. File size and PDF magic bytes are checked.
6. A SHA-256 hash is generated.
7. The PDF is encrypted using AES-256-GCM.
8. The encrypted file is stored securely.
9. The paper receives `PENDING_APPROVAL` status.
10. An audit entry is created.

### Approval Workflow

    Question Setter
          |
          v
    Upload Question Paper
          |
          v
    PENDING_APPROVAL
          |
          v
    Exam Authority Review
          |
          +--------------+
          |              |
          v              v
       APPROVED       REJECTED
          |
          v
    Controlled Release

The system prevents the creator of a question paper from approving the same paper.

### Controlled Release

An approved question paper can be scheduled for release. It becomes available according to the configured release time.

### Secure Download

Authenticated and authorized users can access the secure download endpoint. The encrypted stored file is decrypted by the backend before delivery.

### Audit and Transparency

Important actions are recorded in the audit log. Each audit entry incorporates the previous entry's hash, creating a hash chain that can be verified to detect unauthorized modification of the audit history.

---

## 8. Sample Input and Output

### Login Input

    {
      "email": "authority@exam.gov",
      "password": "********"
    }

### Login Output

    {
      "access_token": "<JWT_TOKEN>",
      "token_type": "bearer"
    }

### Question Paper Input

    Title: Data Structures Model Question Paper
    Examination: Government Competitive Examination
    Subject: Computer Science
    File: data_structures_question_paper.pdf

### Upload Result

    {
      "id": 5,
      "status": "PENDING_APPROVAL",
      "message": "Question paper uploaded successfully."
    }

### Approval Result

    {
      "message": "Question paper approved successfully."
    }

### Health Check

Request:

    GET /health

Response:

    {
      "status": "healthy",
      "service": "backend"
    }

---

## 9. Cloud Deployment

The application is deployed using Render.

### Backend

https://secure-question-paper-management-system.onrender.com

### Frontend

https://secure-question-paper-frontend.onrender.com

### Backend Configuration

    Root Directory: backend
    Build Command: pip install -r requirements.txt
    Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT

### Frontend Configuration

    Root Directory: frontend
    Build Command: npm install; npm run build
    Publish Directory: dist

---

## 10. Testing Performed

The following workflows were tested during development and deployment:

- User authentication
- Role-based authorization
- Question-paper upload
- PDF validation
- Question-paper encryption
- Approval workflow
- Controlled release
- Secure download
- Audit logging
- Audit hash-chain verification
- MFA functionality
- Rejection workflow
- Cloud deployment
- Live cloud authentication
- Live dashboard access

---

## 11. Project Outcome

The completed system provides a secure lifecycle for examination question papers from submission through approval, controlled release, secure access, and auditing.

The security architecture combines authentication, RBAC, MFA, encryption, integrity verification, controlled release, and tamper-evident audit logging to protect sensitive examination content.

---

## 12. Repository

GitHub:

https://github.com/poojithpranaavS/secure_question-paper-management-system

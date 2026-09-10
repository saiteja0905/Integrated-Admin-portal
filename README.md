# Sanyuth (Shidhaan) - Modern Blue-Collar Marketplace 🚀

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

Sanyuth is an AI-ready, highly scalable dual-sided marketplace designed to formalize the fragmented blue-collar workforce sector in India. It securely connects Customers (individuals and businesses) with skilled Workers (electricians, daily wage laborers, etc.) through transparent digital workflows.

## 💡 The Problem & Our Solution
* **The Problem:** The current process of hiring blue-collar labor lacks trust, transparent pricing, and standardized payments. Discovering skilled talent quickly is a chaotic, offline process.
* **Our Solution:** A scalable, decoupled platform that supports both **fixed-rate daily labor** and **complex contractual bidding**. We introduce verified trust through integrated customer ratings, privacy via masked communication, and digital payments—all governed by a dedicated Enterprise Admin Portal.

## ✨ Key Features
* 🔄 **Dual Job System:** Support for immediate, direct-application daily jobs, and competitive bidding on contractual tasks.
* 🛡️ **Built-in Enterprise Admin:** A secure internal dashboard for operators to handle KYC, track analytics, issue "strikes", and resolve user disputes.
* 💬 **Secure Interaction:** Masked in-app chat systems to protect user privacy before an engagement begins.
* 💳 **Dynamic Checkouts:** Sandboxed support for digital payments (Razorpay) alongside Cash-on-Delivery (COD).
* 🗺️ **Job Attachments & Location:** Users can upload image attachments directly to jobs, providing visual context.

## 🏗️ Technical Architecture
Sanyuth is a production-ready application featuring a containerized deployment architecture, a decoupled UI, and a high-performance event-driven backend.

* **Frontend:** React 18 Single Page Application using Tailwind CSS and Shadcn UI for a responsive, clean, metric-driven interface.
* **Backend:** FastAPI (Python) executing asynchronous endpoints, using JWT authentication and strict BSON schema enforcement. 
* **Database:** MongoDB Atlas (motor async driver) utilizing UUID standards.
* **Infrastructure:** Fully Dockerized configurations with a tailored `fly.toml` for Edge deployment.

## 🔐 Demo Test Credentials
To allow judges to evaluate the platform's moderation capabilities, the Enterprise Admin Portal is configured with default demo credentials. Once the database relies on its initial seed data, you can log in directly:
* **Portal URL:** `/admin-login`
* **Email:** `admin@shidhaan.com`
* **Password:** `admin123`

## 📚 Official Documentation
Dive into the platform's technical core and operational guides:

- 📖 **[Comprehensive Technical Product Documentation](docs/SANYUTH_TECHNICAL_PRODUCT_DOCUMENTATION.md)** - *START HERE: Full PRD and Tech Spec*
- 🚀 **[Quick Start Guide](QUICK_START.md)** - Run the app locally via Docker in minutes.
- 🧑‍🤝‍🧑 **[User Personas & Flows](USER_FLOWS.md)** - Breakdown of Customer, Worker, and Admin interfaces.
- 🔌 **[API Documentation](API_DOCS.md)** - RESTful API definitions.
- 🐳 **[Docker Setup](DOCKER_SETUP.md)** / 🌐 **[Production Deployment](DEPLOYMENT.md)**

---
*Developed for scalability, trust, and formalizing the future of work.*
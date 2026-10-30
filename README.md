# NeuroBridge 🧠 - Real-Time Psychological Assessment Using AI

> **BSCS Final Year Project | Mirpur University of Science and Technology (MUST) | Session 2022-2026**
> Version 1.0

### Executive Summary
NeuroBridge is a secure, cross-platform mental health oversight program designed to solve critical gaps in mental health services: lengthy waiting times, weak communication, and fragmented patient files.

Patients can fill out structured clinical questionnaires and request appointments, while AI sorts through the answers and summarizes the results into a concise report for the doctor. This highlights key symptoms and provides necessary context before consultation.

Built with Flutter (Dart) for frontend and Firebase (Firestore, Auth, Cloud Functions, FCM) for secure, scalable backend with role-based access: Patient, Clinician, Admin.

### Problem Statement
In Pakistan, patients face long distances to specialists, weeks of waiting, poor doctor-patient communication, and disorganized records leading to delayed treatment.

### Key Features

**For Patients:**
- 🔍 Searchable Doctor Directory with ratings
- 📅 Smart Appointment Scheduling (book, reschedule, cancel)
- 📝 AI-Powered Clinical Questionnaires
- 💬 Secure Real-Time Chat
- 📁 Encrypted Medical Records
- 🔔 Real-time Notifications via FCM

**For Clinicians:**
- ✅ Accept/Reject Appointment Requests
- 📊 AI-Generated Patient Summary Report
- 👤 Centralized Patient Records View

**For Admin:**
- 👥 User & Payment Management
- 🛡️ System Security Control

### System Architecture
**Three-Tier:** 
1. Presentation Layer: Patient App, Doctor App, Admin Console (Flutter)
2. Business Logic: Cloud Functions, Appointment Service, AI Triage
3. Data Layer: Firestore DB, Firebase Auth, Encrypted Storage

Security: TLS, Firebase Security Rules, Role-Based Access, Encrypted Health Data.

### Tech Stack
- Frontend: Flutter, Dart
- Backend: Firebase Firestore, Auth, Cloud Functions, Cloud Messaging
- Methodology: Agile Scrum, UML Diagrams
- Documentation: SRS, SDD, Traceability Matrix

### Team Members
- Abdull Raffy (FA22-CSE-099)
- Adeel Aslam Anjum (FA22-CSE-063)
- Anjum Imtiaz (FA22-CSE-047)
- Muhammad Uzair (FA22-CSE-073)

Supervisor: Dr. Firdos Kanwal

### How to Run
```bash
flutter pub get
flutter run

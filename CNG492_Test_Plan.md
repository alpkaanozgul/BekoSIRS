# Software Test Documentation: Test Plan
for
**BekoSIRS (Beko Smart Inventory and Recommendation System)**

Prepared by `[Author Name / Team Name]`  
`[University Name]`  
`[Department Name]`  
Supervised by `[Supervisor Name]`  
`[Date Created]`  

---

## Contents
1. Introduction
2. Test items
3. Features to be tested
4. Features not to be tested
5. Approach
   5.1 Unit Testing
   5.2 Integration Testing
   5.3 System Testing
   5.4 Performance Testing
   5.5 User Testing
6. Item pass/fail criteria
7. Schedule
   7.1 Milestones and Tasks
   7.2 Gantt Chart
8. References

---

## 1. Introduction

This Test Plan outlines the testing strategy, items, and approach for the **BekoSIRS (Beko Smart Inventory and Recommendation System)** software product. BekoSIRS is a comprehensive architectural platform composed of four main pillars:
1. A **Django REST API Backend** providing endpoints for inventory, users, sales, and analytics.
2. A **Machine Learning (ML) Engine** that calculates hybrid recommendations consisting of Neural Collaborative Filtering (NCF), Content-Based filtering, and popularity-based fallback.
3. A **React Web Panel Dashboard** for managers to track KPIs, approve reviews, assign service requests, and monitor stock.
4. A **React Native Mobile Application** for customers to browse Beko products, get recommendations, manage their wishlist, authenticate via biometrics, and schedule maintenance service.

The purpose of this test plan is to ensure that all core functionalities (including user authentication, recommendation algorithms, CRUD operations for inventory, and service request assignments) operate securely and bug-free before production deployment.

---

## 2. Test items

A test item is a software item which is an object of testing. The primary test items for the BekoSIRS product include:

| Test Item | Description / Role |
| :--- | :--- |
| **Backend API Server (`BekoSIRS_api`)** | The Django REST Framework application. It acts as the central data controller and handles JWT authentication, product catalog storage, service queue logic, and manager queries. |
| **ML Recommendation Engine** | The scikit-learn/pandas based Python module integrated in the backend. It dynamically generates daily customized product suggestions for every user. |
| **Web Dashboard Application (`BekoSIRS_Web`)** | The React/Vite-based frontend panel used by administrative staff to monitor metrics, handle database CRUD operations, and oversee the service lifecycle. |
| **Mobile Customer Application (`BekoSIRS_Frontend`)** | The cross-platform React Native/Expo application utilized by final customers to log in (including face biometric setup), view catalogs, interact with recommendations, and issue service requests. |
| **Database Schemas** | The foundational SQL models connecting `CustomUser`, `Product`, `ServiceRequest`, and `Wishlist` ensuring strict foreign key constraints and fast data retrieval. |

---

## 3. Features to be tested

For the test items identified above, the following targeted software features will be evaluated:

**Authentication and Security:**
- JWT token generation, refresh, and blacklist functionality.
- Biometric (Face/Touch ID) authentication integration in the Mobile App.
- Role-based Access Control (RBAC) ensuring customers cannot access manager APIs.

**Product and Inventory Management (Web & API):**
- Product and Category standard CRUD (Create, Read, Update, Delete).
- Stock monitoring calculations.

**Recommendation Algorithms (ML Engine):**
- NCF data feeding and training process.
- Cosine similarity matching mechanism (Content-Based routing).
- Verification of fallback metrics (Popularity-Based suggestions).

**Customer Interactions (Mobile & API):**
- Wishlist operations (adding/removing items, push notifications upon change).
- Service Request flow (creating requests, uploading status attachments).
- User Profile updates.

**Management Dashboard Tasks (Web):**
- Analytics visualization logic (Sales KPIs, User Activity graphs).
- Review moderation system (Submit, Approve, Reject).

---

## 4. Features not to be tested

- **Third-Party Payment Gateways:** Since payment simulation is handled externally and out of project scope for this version, the physical transaction mechanism will not be tested.
- **Internal Device Hardware APIs Frameworks:** Internal workings of Apple Face ID / Android BiometricPrompt are presumed reliable; we will only test our Expo module's ability to trigger and receive statuses from them.
- **Low-level Library Functions:** Code heavily utilizing generic `React`, `Django`, or `scikit-learn` algorithms will only be tested in terms of its application to our specific models, rather than re-testing the foundational third-party framework code itself.

---

## 5. Approach

The testing methodology ensures that all modules initially pass tests individually (Unit), in a combined state (Integration), and as an entire stack (System). Test data consisting of mock Beko products, dummy user accounts, and mock historical sales data will be injected into the test database.

### 5.1 Unit Testing
- **What will be tested:** Backend Django Models and individual Views (using a simulated SQLite in-memory test database). ML model unit isolation. React individual UI components rendering logic.
- **Activities & Tools:** Execute standard assertions checking logic pathways handling exceptions.  
  _Tools:_ `pytest`, `pytest-django` for Python/Django. `Jest` and `React Testing Library` for React and React Native components.

### 5.2 Integration Testing
- **What will be tested:** API Endpoints interoperability with the Mobile App and Web Panel. Verifying that the data payloads sent by React components are accurately received, validated, and processed by Django serializers.
- **Activities & Tools:** Using API mocking and intercepted HTTP responses. Checking error logs and responses (HTTP 200, 400, 401, 403, 404).  
  _Tools:_ `Postman`, `Axios` mock adapters, `pytest` APIClient.

### 5.3 System Testing
- **What will be tested:** The fully containerized system (Backend + Web + Mobile + Database). End-to-end purchasing simulating a user from login -> browsing -> wishlist -> recommendations -> reporting.
- **Activities & Tools:** System will be launched using `start-all.sh` layout. Automated scripts will navigate the browser.  
  _Tools:_ `Cypress` or `Selenium` for Web App E2E. `Detox` for Mobile E2E.

### 5.4 Performance Testing
- **What will be tested:** API Response times under heavy load. The ML Engine's ability to reconstruct matrices without memory leaks. Database indexing optimization preventing N+1 logic.
- **Activities & Tools:** Simulating 500+ concurrent user login attempts and fetching the heavy `recommendations/` endpoints simultaneously.  
  _Tools:_ `Locust` (for load testing Python APIs) and `JMeter`.

### 5.5 User Testing
- **What will be tested:** Ergonomic UI / UX flow for both the end customer (Mobile) and the Store Manager (Web Panel).
- **Activities & Tools:** Providing the Expo Go mobile client to a sample group of 5-10 users. Collecting feedback on app navigation, recommendation relevance, and ease of scheduling a maintenance service.  
  _Tools:_ `Google Forms` (for feedback collection), direct interview methodologies.

---

## 6. Item pass/fail criteria

The application will be green-lit for production if the following quantitative criteria are met during the testing phases:

- **Unit Test Level:** 
  - Code coverage tool (`pytest-cov`, `Jest`) indicates at least **80% Code Coverage**.
  - All automated Unit and Integration tests are successfully completed without fatal errors (100% pass rate).
- **Security Check Level:** 
  - 100% block rate on all unauthorized access tests (e.g., trying to access Dashboard APIs with a Customer Token).
- **Performance/System Plan Level:** 
  - Recommendation API responds in **under 1000ms** for 95% of requests under standard load. _Justification: Since ML computation can be heavy, response times up to 1s are considered acceptable per user experience studies, preventing interface timeouts._
  - Main catalogue viewing APIs must respond in **under 300ms**.
- **User Test Level:**
  - Overall user satisfaction rating must be above 4/5 based on collected User Testing forms. No UI bugs preventing core actions (e.g., checkout or authentication block).

---

## 7. Schedule

### 7.1 Milestones and Tasks

This schedule organizes the testing into 4 major sprints (weeks):

| Task ID | Task Description | Dependencies | Duration | Responsible |
| :--- | :--- | :--- | :--- | :--- |
| T1 | Setup Testing Framework (pytest/Jest) & Mock DB | None | 1 Week | Test Engineer 1 |
| T2 | Conduct Unit Tests for Backend Models & APIs | T1 | 1 Week | Backend Developer |
| T3 | Conduct UI Component Tests for Web & Mobile | T1 | 1 Week | Frontend Developer |
| T4 | Perform Integration Testing (API + Frontend) | T2, T3 | 1 Week | QA Engineer |
| T5 | Execute ML Engine Performance Verification | T2 | 0.5 Weeks | ML Engineer |
| T6 | Perform System Load Testing (Locust) | T4 | 0.5 Weeks | QA Engineer |
| T7 | Final E2E Automated Tests (Cypress) | T4 | 1 Week | Test Engineer 1 |
| T8 | User Acceptance Testing (UAT) | T7 | 1 Week | QA Engineer / Users |
| T9 | Test Result Analysis & Bug Fix Allocation | T8 | 0.5 Weeks | Project Manager |

### 7.2 Gantt Chart

```mermaid
gantt
    title BekoSIRS Testing Schedule
    dateFormat  YYYY-MM-DD
    section Setup & Unit Tests
    T1: Setup Test Frameworks      :done,    des1, 2026-04-01, 7d
    T2: Backend Unit Tests         :active,  des2, 2026-04-08, 7d
    T3: Frontend Unit Tests        :active,  des3, 2026-04-08, 7d
    section Integration
    T4: Integrational API Flow Tests :         des4, after des2, 7d
    T5: ML Execution Verification  :         des5, after des2, 4d
    section System & UAT
    T6: Locust Performance Testing :         des6, after des4, 4d
    T7: E2E Automation (Cypress)   :         des7, after des4, 7d
    T8: User Acceptance Testing    :         des8, after des7, 7d
    T9: Review & Bug Fix Phase     :         des9, after des8, 4d
```

---

## 8. References

- IEEE. (1998). *IEEE Standard for Software Test Documentation* (IEEE Std 829-1998). IEEE Computer Society.
- Django Software Foundation. (2024). *Testing Django applications*. https://docs.djangoproject.com/en/stable/topics/testing/
- React Native Contributors. (2024). *Testing with Jest*. https://reactnative.dev/docs/testing-overview
- BekoSIRS Team. (2026). *BekoSIRS - Comprehensive Project Analysis Report* (`ANALYSIS_REPORT.md` inside GitHub repository core).

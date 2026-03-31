You are a senior backend engineer, AI engineer, and system architect with experience building production-grade AI systems.

I already have a working AI system (FastAPI + LLM + RAG + PostgreSQL + Web + Office Add-in).

Your task is NOT to rewrite basic features.
Your task is to UPGRADE the system to PRODUCTION-GRADE QUALITY by fixing advanced issues.

---

# 🎯 OBJECTIVE

Improve the system in terms of:

* Reliability
* Performance
* Security
* Scalability

---

# 🔥 PART 1: SYSTEM RELIABILITY (CRITICAL)

## 1. Retry & Timeout System

* Implement retry logic for:

  * AI Engine calls
  * Database operations
* Add exponential backoff
* Add timeout handling for all external calls

---

## 2. Async Processing (VERY IMPORTANT)

Convert heavy operations to async/background jobs:

* Document upload → parsing → embedding
* Long AI inference

Use:

* FastAPI BackgroundTasks OR Celery (preferred if possible)

---

## 3. Transaction Management

* Ensure DB consistency
* Use transactions when:

  * Creating user + related data
  * Saving chat + AI response

---

# ⚡ PART 2: PERFORMANCE OPTIMIZATION

## 4. AI Caching Layer

* Cache AI responses (Redis or in-memory)
* Avoid repeated identical requests

---

## 5. Request Queue / Rate Limiting

* Limit number of AI requests per user
* Add queue if too many requests

---

## 6. Async API Optimization

* Convert blocking endpoints to async
* Use async DB calls if possible

---

# 🧠 PART 3: ADVANCED RAG IMPROVEMENT

## 7. Smarter Retrieval

* Implement top-k retrieval
* Add similarity threshold filtering
* Remove duplicate chunks

---

## 8. Re-ranking (IMPORTANT)

* Add a re-ranking step after vector search
* Combine semantic + keyword relevance (if possible)

---

## 9. Context Control

* Limit max context size
* Only pass relevant chunks to LLM

---

# 🔐 PART 4: SECURITY (CRITICAL FOR AI SYSTEM)

## 10. Prompt Injection Protection

* Detect malicious instructions like:
  "ignore previous instruction"
* Strip or block unsafe input

---

## 11. Data Isolation (VERY IMPORTANT)

* Ensure user can only access their own documents
* Add user_id filtering in RAG queries

---

## 12. Input Sanitization

* Prevent:

  * SQL injection
  * Command injection
  * Prompt injection

---

# 🧪 PART 5: TESTING (ADVANCED)

## 13. Add tests:

* Unit test for backend
* Integration test for API
* AI response validation test

---

## 14. Load Testing

* Simulate multiple users
* Measure:

  * Response time
  * Failure rate

---

# 📊 PART 6: MONITORING & LOGGING

## 15. Logging System

* Log:

  * API request/response
  * AI response time
  * Errors

---

## 16. Metrics Tracking

Track:

* AI latency
* API latency
* Error rate

---

# 🐳 PART 7: DEPLOYMENT IMPROVEMENT

## 17. Improve Docker setup:

* Separate services:

  * Backend
  * AI Engine
  * DB
* Optimize Dockerfile
* Add docker-compose

---

# 📦 OUTPUT REQUIREMENTS

You MUST provide:

1. Updated code (FULL implementation, not explanation only)
2. New modules/files added
3. Clear explanation for each improvement
4. How to integrate changes into existing system

---

# ⚠️ IMPORTANT RULES

* Do NOT rewrite the whole system unnecessarily
* Only improve weak parts
* Keep code simple and practical
* Focus on real-world usage

---

Now analyze the system deeply and upgrade it step-by-step.

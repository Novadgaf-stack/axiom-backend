# AGENT_WORKFLOW.md — Agentic Engineering Lifecycle

## 1. Overview

Superteam Agentic Engineering Grant requires a clear demonstration of AI-driven software development workflows alongside a structured agent runtime layer.

---

## 2. Engineering Workflow Cycle

```
1. Human Objective
   "Extend Nexus-7 with an isolated Solana Devnet Agent Layer"
   ↓
2. Repository Analysis & Architectural Mapping
   (Automated inspection of app/engine.py, risk.py, strategy.py)
   ↓
3. Planning & Specification (NO Code Edits Phase)
   (Creation of APPLICATION.md, PROJECT_SPEC.md, SECURITY_MODEL.md)
   ↓
4. Modular Implementation
   (Building solana_agent/ policy gate, simulator, and signer)
   ↓
5. Automated Testing Suite
   (pytest execution across unit, integration, and policy tests)
   ↓
6. Failure Diagnosis & Verification
   (Inspecting logs, traceback resolution, fixing lints/imports)
   ↓
7. Human Review & Feedback Loop
   (User review of proposed changes and approval)
   ↓
8. Git Version Control & Deployment
   (Git add, commit, push to GitHub repo; deployment to Render)
   ↓
9. Live Devnet Verification
   (Verifying RPC simulation logs & Solana Explorer Devnet tx signatures)
```

---

## 3. Runtime Agent Decision Engine

At runtime, the Solana Agent Layer operates as a structured agentic decision pipeline rather than a simple LLM text generator:

```
Input Market Telemetry & Signal
             ↓
    [Gemini AI Advisory]
             ↓ (Raw JSON decision & confidence score)
    [Policy & Safety Gate] (Hard code deterministic checks)
             ↓ (PASS)
    [Solana RPC Simulator] (pre-flight simulateTransaction)
             ↓ (SUCCESS)
    [Isolated Signer] (Keypair signing)
             ↓
  [Devnet Broadcast] → Signature Logged to SQLite & JSON
```

{\rtf1\ansi\ansicpg1252\cocoartf2759
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 # System Architecture Document: Multi-Agent Job Hunting Orchestrator\
\
**Codename: JobPilot**\
**Version:** 1.0\
**Audience:** Backend, ML/AI, Data, Frontend, Platform, and Security Engineers\
\
---\
\
## Table of Contents\
\
1. [Executive Summary](#1-executive-summary)\
2. [Design Principles](#2-design-principles)\
3. [High-Level Architecture Overview](#3-high-level-architecture-overview)\
4. [Agent Definitions & Responsibilities](#4-agent-definitions--responsibilities)\
5. [Manager Orchestration Layer](#5-manager-orchestration-layer)\
6. [Data Models & Schema Design](#6-data-models--schema-design)\
7. [End-to-End Data Flow](#7-end-to-end-data-flow)\
8. [Job Discovery & Source Acquisition Strategy](#8-job-discovery--source-acquisition-strategy)\
9. [Resume Parsing & Preference Analysis Engine](#9-resume-parsing--preference-analysis-engine)\
10. [Outreach & Networking Pipeline](#10-outreach--networking-pipeline)\
11. [Anti-Scraping Resilience & Source Policy Enforcement](#11-anti-scraping-resilience--source-policy-enforcement)\
12. [Security, Privacy & Safety](#12-security-privacy--safety)\
13. [Technology Stack](#13-technology-stack)\
14. [Deployment Architecture](#14-deployment-architecture)\
15. [Observability, Testing & Quality Assurance](#15-observability-testing--quality-assurance)\
16. [Extensibility & Plugin Architecture](#16-extensibility--plugin-architecture)\
17. [Cost Estimation & Optimization](#17-cost-estimation--optimization)\
18. [Development Phases & Milestones](#18-development-phases--milestones)\
19. [Open Considerations & Known Blind Spots](#19-open-considerations--known-blind-spots)\
20. [Appendix](#20-appendix)\
\
---\
\
## 1. Executive Summary\
\
JobPilot is an autonomous, manager-led multi-agent orchestration system that automates the end-to-end job hunting lifecycle. A user uploads a resume PDF, specifies target roles, companies, and tech stack preferences. The system then autonomously discovers matching jobs, ranks them against the user's profile, identifies networking targets, and prepares outreach artifacts\'97all coordinated by a central Manager Agent that delegates tasks to specialized worker agents running atop a durable workflow engine.\
\
The system is designed as a **policy-aware acquisition platform**\'97not a scraping bypass engine. Every platform integration is governed by a formal Source Capability Registry that enforces compliant access modes, falling back gracefully through official APIs, licensed data vendors, email alert ingestion, employer career pages, and manual link input before considering any browser automation. Outreach outputs are always **drafts requiring human approval**; fully automatic job application submission is explicitly out of scope.\
\
**Core outputs per search campaign:**\
1. A ranked list of matching jobs with explainable scores\
2. Canonical application links (preferring employer ATS pages)\
3. Prioritized contacts per target job: Hiring Managers \uc0\u8594  Recruiters/HR \u8594  Potential Peers\
4. Personalized outreach message drafts\
5. A continuously improving preference profile\
\
---\
\
## 2. Design Principles\
\
| Principle | Rationale |\
|---|---|\
| **Manager-Led Orchestration** | A single Manager Agent owns the execution plan. It decomposes user intent into a task DAG, assigns agents, and re-plans on failure. This prevents chaotic agent-to-agent chatter. |\
| **LLMs Reason; Services Execute** | Agents decide *what* to do. Deterministic services and tools perform *the actual work*. This separation keeps behavior predictable and auditable. |\
| **Policy-Aware Source Access** | Every source connector checks a policy registry before making requests. Official/licensed access comes first; browser automation is allowlisted and gated. The architecture respects platform Terms of Service. |\
| **Durable Workflows, Ephemeral Agents** | Long-running campaigns, retries, and approval waits live in a durable workflow engine (Temporal). Worker agents are stateless and spun up on demand. |\
| **On-Demand Execution** | Agents don't run continuously. The Manager spins them up when needed and deallocates after completion, keeping costs proportional to usage. |\
| **Human-in-the-Loop at Risk Boundaries** | The system generates "ready-to-apply" packages\'97never auto-submits applications or sends messages without explicit user approval. This protects against ATS blacklisting. |\
| **Explainability** | Every match score and outreach recommendation includes a human-readable reasoning trace stored alongside the result. |\
| **Source Redundancy** | Every job platform has \uc0\u8805 2 retrieval strategies. If one fails, the next is attempted automatically before falling back to manual input. |\
| **Idempotent Tasks** | Every agent task can be safely retried. State is persisted before and after each step. |\
| **Canonicalize to Employer ATS** | Job boards are discovery channels; the canonical record should reference the employer's own career page/ATS URL for better deduplication, freshness, and application success. |\
| **Privacy-First** | User resume data is encrypted at rest, never shared beyond what's necessary for LLM processing, and deletable on demand. |\
\
---\
\
## 3. High-Level Architecture Overview\
\
```\
\uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
\uc0\u9474                           USER INTERFACE LAYER                             \u9474 \
\uc0\u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9474 \
\uc0\u9474   \u9474  Resume Upload \u9474   \u9474  Role/Company  \u9474   \u9474  Manual Link   \u9474   \u9474  Dashboard  \u9474  \u9474 \
\uc0\u9474   \u9474    (PDF)       \u9474   \u9474   Config Panel \u9474   \u9474    Input       \u9474   \u9474  & Reports  \u9474  \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9650 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9474 \
\uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
          \uc0\u9660                   \u9660                   \u9660                  \u9474 \
\uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
\uc0\u9474                    API GATEWAY / AUTH / CAMPAIGN SERVICE                    \u9474 \
\uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
                                \uc0\u9660 \
\uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
\uc0\u9474                       DURABLE WORKFLOW ENGINE (Temporal)                    \u9474 \
\uc0\u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9474 \
\uc0\u9474   \u9474                      \u55356 \u57263  MANAGER AGENT (Orchestrator)                  \u9474   \u9474 \
\uc0\u9474   \u9474   \'95 Receives user intent & parsed inputs                             \u9474   \u9474 \
\uc0\u9474   \u9474   \'95 Builds execution plan (DAG of tasks)                             \u9474   \u9474 \
\uc0\u9474   \u9474   \'95 Delegates to worker agents (as Temporal activities)              \u9474   \u9474 \
\uc0\u9474   \u9474   \'95 Monitors progress, handles failures, re-plans                    \u9474   \u9474 \
\uc0\u9474   \u9474   \'95 Waits on approval gates                                          \u9474   \u9474 \
\uc0\u9474   \u9474   \'95 Aggregates results and delivers final output                     \u9474   \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9474 \
\uc0\u9474      \u9660          \u9660           \u9660           \u9660           \u9660           \u9660               \u9474 \
\uc0\u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9474 \
\uc0\u9474   \u9474 Resume \u9474  \u9474  Job   \u9474  \u9474 Prefer.  \u9474  \u9474 Outreach \u9474  \u9474 Research \u9474  \u9474 QA/Critic \u9474   \u9474 \
\uc0\u9474   \u9474 Parser \u9474  \u9474 Scout  \u9474  \u9474 Analyst  \u9474  \u9474 Finder   \u9474  \u9474  Agent   \u9474  \u9474   Agent   \u9474   \u9474 \
\uc0\u9474   \u9474 Agent  \u9474  \u9474 Agent  \u9474  \u9474  Agent   \u9474  \u9474  Agent   \u9474  \u9474          \u9474  \u9474           \u9474   \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9474 \
\uc0\u9474       \u9474          \u9474           \u9474            \u9474            \u9474            \u9474           \u9474 \
\uc0\u9474   \u9484 \u9472 \u9472 \u9472 \u9524 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9524 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9524 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9524 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9524 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9524 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9474 \
\uc0\u9474   \u9474               SOURCE POLICY ENGINE / CAPABILITY REGISTRY            \u9474   \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9474 \
\uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
                                    \uc0\u9474 \
\uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9660 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
\uc0\u9474                        INFRASTRUCTURE / TOOLING LAYER                      \u9474 \
\uc0\u9474                                                                            \u9474 \
\uc0\u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9474 \
\uc0\u9474   \u9474  Vector    \u9474  \u9474  Source     \u9474  \u9474  Browser    \u9474  \u9474  LLM     \u9474  \u9474  Alert      \u9474  \u9474 \
\uc0\u9474   \u9474  Store     \u9474  \u9474  Adapters   \u9474  \u9474  Worker Pool\u9474  \u9474  Gateway \u9474  \u9474  Ingestion  \u9474  \u9474 \
\uc0\u9474   \u9474  (Qdrant)  \u9474  \u9474  (per-plat) \u9474  \u9474 (Playwright)\u9474  \u9474 (LiteLLM)\u9474  \u9474  (Email)    \u9474  \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9474 \
\uc0\u9474                                                                            \u9474 \
\uc0\u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9474 \
\uc0\u9474   \u9474  Postgres  \u9474  \u9474  Redis      \u9474  \u9474  Object     \u9474  \u9474  Skill   \u9474  \u9474  Logging &  \u9474  \u9474 \
\uc0\u9474   \u9474  (Primary  \u9474  \u9474  (Cache +   \u9474  \u9474  Store (S3/ \u9474  \u9474  Taxonomy\u9474  \u9474 Observability\u9474  \u9474 \
\uc0\u9474   \u9474   DB)      \u9474  \u9474   Rate Lim) \u9474  \u9474   MinIO)    \u9474  \u9474  Service \u9474  \u9474 (OTel+Jaeger)\u9474  \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9474 \
\uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
```\
\
---\
\
## 4. Agent Definitions & Responsibilities\
\
### 4.1 Agent Architecture Pattern (Agent Shell)\
\
Every agent follows a uniform structural contract. This custom agent shell is inspired by CrewAI's role-based pattern but runs as a stateless activity within the Temporal durable workflow engine\'97giving the benefits of structured agent contracts with crash-proof execution and built-in retry/timeout support.\
\
```\
\uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
\uc0\u9474                  AGENT SHELL                  \u9474 \
\uc0\u9474                                              \u9474 \
\uc0\u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9474 \
\uc0\u9474   \u9474    Persona    \u9474   \u9474     Tools/Functions    \u9474   \u9474 \
\uc0\u9474   \u9474    (System    \u9474   \u9474     Available to       \u9474   \u9474 \
\uc0\u9474   \u9474     Prompt)   \u9474   \u9474     This Agent         \u9474   \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9474 \
\uc0\u9474                                              \u9474 \
\uc0\u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9474 \
\uc0\u9474   \u9474   Input       \u9474   \u9474   Output Schema       \u9474   \u9474 \
\uc0\u9474   \u9474   Schema      \u9474   \u9474   (Pydantic / JSON)   \u9474   \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9474 \
\uc0\u9474                                              \u9474 \
\uc0\u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9474 \
\uc0\u9474   \u9474   Memory      \u9474   \u9474   Callback Hooks      \u9474   \u9474 \
\uc0\u9474   \u9474   (Short +    \u9474   \u9474   (on_start, on_end,  \u9474   \u9474 \
\uc0\u9474   \u9474    Long-term) \u9474   \u9474    on_error)          \u9474   \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9474 \
\uc0\u9474                                              \u9474 \
\uc0\u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488    \u9474 \
\uc0\u9474   \u9474   Execution Loop:                      \u9474    \u9474 \
\uc0\u9474   \u9474   1. Receive task from Manager         \u9474    \u9474 \
\uc0\u9474   \u9474   2. Reason about approach             \u9474    \u9474 \
\uc0\u9474   \u9474   3. Select & invoke tools             \u9474    \u9474 \
\uc0\u9474   \u9474   4. Validate output against schema    \u9474    \u9474 \
\uc0\u9474   \u9474   5. Return result + reasoning trace   \u9474    \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496    \u9474 \
\uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
```\
\
### 4.2 Agent Roster\
\
---\
\
#### Agent 0: **Manager Agent** (Orchestrator)\
\
```\
Role:        Chief Orchestrator\
Goal:        Decompose user request into an execution plan, delegate to\
             worker agents, monitor execution, handle failures, wait on\
             approval gates, aggregate final results.\
Autonomy:    FULL \'97 makes all delegation and re-planning decisions.\
LLM:         GPT-4o / Claude Sonnet (needs strong reasoning)\
Execution:   Runs as the primary Temporal workflow definition.\
```\
\
**Detailed Responsibilities:**\
\
1. **Intake Processing** \'97 Receive parsed user inputs (resume data, roles, companies, tech stack). Validate completeness; if gaps exist, generate clarification prompts.\
\
2. **Plan Generation** \'97 Build a Directed Acyclic Graph (DAG) of tasks:\
\
```\
Phase 1 (Parallel):\
  \uc0\u9500 \u9472 \u9472  Task: Parse Resume             \u8594  Resume Parser Agent\
  \uc0\u9492 \u9472 \u9472  Task: Validate Inputs          \u8594  Manager (self)\
\
Phase 2 (Parallel, after Phase 1):\
  \uc0\u9500 \u9472 \u9472  Task: Scout Naukri             \u8594  Job Scout Agent (instance 1)\
  \uc0\u9500 \u9472 \u9472  Task: Scout Indeed             \u8594  Job Scout Agent (instance 2)\
  \uc0\u9500 \u9472 \u9472  Task: Scout LinkedIn           \u8594  Job Scout Agent (instance 3)\
  \uc0\u9500 \u9472 \u9472  Task: Scout IIMJobs            \u8594  Job Scout Agent (instance 4)\
  \uc0\u9500 \u9472 \u9472  Task: Ingest Alert Emails      \u8594  Alert Ingestion Service\
  \uc0\u9492 \u9472 \u9472  Task: Research Companies       \u8594  Research Agent\
\
Phase 3 (After Phase 2):\
  \uc0\u9500 \u9472 \u9472  Task: Deduplicate & Normalize  \u8594  Manager (self) + Canonicalization\
  \uc0\u9492 \u9472 \u9472  Task: QA Check (Extractions)   \u8594  QA/Critic Agent\
\
Phase 4 (After Phase 3):\
  \uc0\u9492 \u9472 \u9472  Task: Rank & Filter Jobs       \u8594  Preference Analyst Agent\
\
Phase 5 (After Phase 4):\
  \uc0\u9500 \u9472 \u9472  Task: Find Contacts            \u8594  Outreach Finder Agent\
  \uc0\u9492 \u9472 \u9472  Task: QA Check (Rankings)      \u8594  QA/Critic Agent\
\
Phase 6 (After Phase 5):\
  \uc0\u9492 \u9472 \u9472  Task: Compile & Deliver Report \u8594  Manager (self)\
```\
\
3. **Execution Monitoring** \'97 Track task status. If a scout fails on one platform, do NOT block others. If a scout times out (>120s), mark source as degraded and proceed.\
\
4. **Re-Planning** \'97 If all scraping sources fail for a platform, escalate to manual input. If resume parsing fails, ask for manual profile entry. If match quality is low (<3 results above threshold), relax filters and re-run.\
\
5. **Approval Gates** \'97 Pause workflow and await user approval for: top-N job shortlist, contact list, outreach drafts, and any suspicious-posting reviews.\
\
6. **Aggregation** \'97 Combine all agent outputs into a unified ranked report with reasoning traces.\
\
**Manager Agent State Machine:**\
\
```\
                    \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
                    \uc0\u9474    IDLE   \u9474 \
                    \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
                         \uc0\u9474  (user triggers campaign)\
                         \uc0\u9660 \
                    \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
                    \uc0\u9474  PLANNING \u9474 \
                    \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
                         \uc0\u9474  (DAG generated)\
                         \uc0\u9660 \
                    \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
            \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472  \u9474   EXECUTING   \u9474  \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
            \uc0\u9474       \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496       \u9474 \
            \uc0\u9474  (task fails)    (all tasks  \u9474 \
            \uc0\u9660                   complete)  \u9660 \
     \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488           \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
     \uc0\u9474  RE-PLANNING \u9474           \u9474  AWAITING_APPROVAL \u9474 \
     \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496           \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
            \uc0\u9474                           \u9474  (user approves)\
            \uc0\u9474  (new plan ready)         \u9660 \
            \uc0\u9492 \u9472 \u9472 \u9658  EXECUTING      \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
                                \uc0\u9474  AGGREGATING  \u9474 \
                                \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
                                       \uc0\u9474  (report built)\
                                       \uc0\u9660 \
                                \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
                                \uc0\u9474  COMPLETE \u9474 \
                                \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
```\
\
---\
\
#### Agent 1: **Resume Parser Agent**\
\
```\
Role:        Extract structured profile data from uploaded resume PDF\
Goal:        Produce a canonical user profile that all other agents reference\
LLM:         GPT-4o-mini (sufficient for extraction tasks)\
Tools:       pdf_text_extractor, pdf_vision_extractor, schema_validator,\
             skill_normalizer\
```\
\
**Input:**\
```json\
\{\
  "resume_file_path": "s3://bucket/resumes/user123.pdf",\
  "user_overrides": \{\
    "additional_skills": ["Kubernetes", "Terraform"],\
    "preferred_titles": ["Senior Backend Engineer", "Staff Engineer"],\
    "years_experience_override": null\
  \}\
\}\
```\
\
**Processing Steps:**\
1. Extract raw text from PDF using PyMuPDF/pdfplumber\
2. If text extraction yields <100 chars (scanned PDF), fall back to vision-based extraction via GPT-4o multimodal\
3. Send extracted text to LLM with structured extraction prompt\
4. Normalize skills via synonym dictionary + LLM fallback (e.g., "React.js" \uc0\u8594  "React", "k8s" \u8594  "Kubernetes", "Amazon Web Services" \u8594  "AWS")\
5. Merge `user_overrides` on top (overrides win)\
6. Compute embeddings for full profile summary, skill clusters, and work experience blocks\
7. Store embeddings in vector store with metadata tags\
8. Present extracted profile for optional human correction (especially for ambiguous fields)\
\
**Output Schema (`CandidateProfile`):**\
```json\
\{\
  "candidate_profile": \{\
    "name": "string",\
    "email": "string",\
    "phone": "string",\
    "location": \{\
      "city": "string",\
      "state": "string",\
      "country": "string",\
      "open_to_remote": true,\
      "open_to_relocation": true\
    \},\
    "summary": "string (LLM-generated 3-line summary)",\
    "total_years_experience": 7.5,\
    "current_title": "Senior Software Engineer",\
    "current_company": "Acme Corp",\
    "education": [\
      \{\
        "degree": "B.Tech Computer Science",\
        "institution": "IIT Delhi",\
        "year": 2017,\
        "gpa": "8.6/10"\
      \}\
    ],\
    "skills": \{\
      "languages": ["Python", "Go", "TypeScript"],\
      "frameworks": ["FastAPI", "React", "Django"],\
      "databases": ["PostgreSQL", "Redis", "MongoDB"],\
      "cloud": ["AWS", "GCP"],\
      "devops": ["Docker", "Kubernetes", "Terraform"],\
      "domains": ["Distributed Systems", "ML Infrastructure"],\
      "soft_skills": ["Technical Leadership", "System Design"]\
    \},\
    "experience": [\
      \{\
        "company": "Acme Corp",\
        "title": "Senior Software Engineer",\
        "duration": "2021 - Present",\
        "duration_months": 36,\
        "highlights": [\
          "Led migration of monolith to microservices serving 2M RPM",\
          "Designed event-driven architecture using Kafka"\
        ],\
        "tech_used": ["Python", "Kafka", "PostgreSQL", "AWS"]\
      \}\
    ],\
    "certifications": ["AWS Solutions Architect Associate"],\
    "notable_projects": [],\
    "embedding_ids": \{\
      "full_profile": "emb_001",\
      "skills_cluster": ["emb_002", "emb_003"],\
      "experience_summary": "emb_005"\
    \}\
  \},\
  "parsing_metadata": \{\
    "extraction_method": "text_primary",\
    "confidence_score": 0.92,\
    "fields_missing": ["phone"],\
    "warnings": ["Could not determine exact graduation GPA"]\
  \}\
\}\
```\
\
---\
\
#### Agent 2: **Job Scout Agent** (Multiple Instances)\
\
```\
Role:        Discover job listings from a specific platform\
Goal:        Return raw job listings matching search criteria\
LLM:         GPT-4o-mini (for query construction + result cleaning)\
Tools:       api_client, web_scraper, headless_browser, alert_ingestion,\
             manual_input_listener\
Instances:   1 per platform (Naukri, Indeed, LinkedIn, IIMJobs, + extensible)\
Policy:      MUST check Source Capability Registry before each request.\
```\
\
**Input:**\
```json\
\{\
  "platform": "naukri",\
  "search_params": \{\
    "titles": ["Senior Backend Engineer", "Staff Engineer", "Platform Engineer"],\
    "companies": ["Google", "Flipkart", "Razorpay", "Atlassian"],\
    "tech_keywords": ["Python", "Kubernetes", "Distributed Systems"],\
    "location": "Bangalore",\
    "remote_ok": true,\
    "experience_range": \{"min": 5, "max": 10\},\
    "posted_within_days": 14,\
    "salary_range": \{"min": 3000000, "currency": "INR"\}\
  \},\
  "max_results": 50,\
  "retrieval_strategy_preference": "auto"\
\}\
```\
\
**Retrieval Strategy Cascade (per platform):**\
\
```\
\uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
\uc0\u9474               RETRIEVAL STRATEGY CASCADE                           \u9474 \
\uc0\u9474                                                                   \u9474 \
\uc0\u9474   For each platform, attempt strategies in order:                 \u9474 \
\uc0\u9474                                                                   \u9474 \
\uc0\u9474   Strategy 1: OFFICIAL API                                        \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472  LinkedIn \u8594  LinkedIn Job Search API (partner access)        \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472  Indeed  \u8594  Indeed Publisher API (approved partners)          \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472  Naukri  \u8594  No official public API (skip)                    \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472  IIMJobs \u8594  No official API (skip)                           \u9474 \
\uc0\u9474        \u8595  if unavailable or rate-limited                           \u9474 \
\uc0\u9474                                                                   \u9474 \
\uc0\u9474   Strategy 2: LICENSED THIRD-PARTY DATA VENDORS                   \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472  RapidAPI job search endpoints                               \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472  SerpAPI (Google Jobs results)                               \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472  Apify pre-built actors                                      \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472  JobDataAPI / JSearch                                        \u9474 \
\uc0\u9474        \u8595  if unavailable or insufficient results                   \u9474 \
\uc0\u9474                                                                   \u9474 \
\uc0\u9474   Strategy 3: ALERT / EMAIL INGESTION                             \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472  Parse user's job alert emails from the platform             \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472  Extract job links from notification feeds                   \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472  Feed into canonicalization pipeline                         \u9474 \
\uc0\u9474        \u8595  if not configured or insufficient                        \u9474 \
\uc0\u9474                                                                   \u9474 \
\uc0\u9474   Strategy 4: CANONICAL EMPLOYER ATS / CAREER PAGES               \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472  Fetch directly from employer career pages                   \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472  Lever, Greenhouse, Workday career sites                     \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472  Allowlisted browser automation (employer pages only)        \u9474 \
\uc0\u9474        \u8595  if insufficient                                          \u9474 \
\uc0\u9474                                                                   \u9474 \
\uc0\u9474   Strategy 5: MANUAL INPUT FALLBACK                               \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472  Prompt user: "Paste job URLs or upload a CSV/screenshot"   \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472  Accept: URL list, CSV paste, screenshot                     \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472  Parse pasted content using LLM extraction                   \u9474 \
\uc0\u9474                                                                   \u9474 \
\uc0\u9474   POLICY CONSTRAINT: Before any request, the adapter              \u9474 \
\uc0\u9474   MUST check the Source Capability Registry.                      \u9474 \
\uc0\u9474   On login wall, CAPTCHA, or bot challenge \u8594  STOP and             \u9474 \
\uc0\u9474   create a human review task instead of attempting bypass.         \u9474 \
\uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
```\
\
**Platform-Specific Strategy Table:**\
\
| Platform | Strategy 1 (Official API) | Strategy 2 (Licensed Vendor) | Strategy 3 (Alerts) | Strategy 4 (ATS/Career) | Strategy 5 (Manual) |\
|---|---|---|---|---|---|\
| **LinkedIn** | LinkedIn API (partner access) or RapidAPI wrapper | SerpAPI, Apify LinkedIn actor | LinkedIn job alert emails | Employer career page | Paste URLs |\
| **Naukri** | N/A | SerpAPI (`site:naukri.com`), Apify actor | Naukri email/push alerts | Employer career page | Paste URLs |\
| **Indeed** | Indeed Publisher API (approved) | RapidAPI Indeed endpoints, SerpAPI | Indeed email alerts | Employer career page | Paste URLs |\
| **IIMJobs** | N/A | SerpAPI (`site:iimjobs.com`) | IIMJobs app notifications | Employer career page | Paste URLs |\
\
**Output Schema per Job:**\
```json\
\{\
  "raw_jobs": [\
    \{\
      "job_id": "scout_naukri_12345",\
      "source_platform": "naukri",\
      "retrieval_strategy_used": "third_party_api",\
      "title": "Senior Backend Engineer",\
      "company": "Razorpay",\
      "location": "Bangalore, India",\
      "remote_type": "hybrid",\
      "description_raw": "...(full JD text)...",\
      "description_structured": \{\
        "responsibilities": ["..."],\
        "requirements": \{\
          "must_have": ["Python", "3+ years", "REST APIs"],\
          "nice_to_have": ["Kafka", "Kubernetes"]\
        \},\
        "benefits": ["..."],\
        "experience_range": "5-8 years"\
      \},\
      "salary_info": \{\
        "disclosed": false,\
        "range": null,\
        "estimated_range": "\uc0\u8377 30L - \u8377 50L (Glassdoor estimate)"\
      \},\
      "posted_date": "2025-01-10",\
      "application_url": "https://naukri.com/apply/12345",\
      "canonical_employer_url": "https://razorpay.com/careers/12345",\
      "apply_method": "external_redirect",\
      "recruiter_name_on_posting": "Rahul Verma",\
      "scraped_at": "2025-01-15T14:30:00Z",\
      "risk_flags": [],\
      "embedding_id": "emb_job_001"\
    \}\
  ],\
  "scout_metadata": \{\
    "platform": "naukri",\
    "strategy_attempts": [\
      \{"strategy": "third_party_api", "status": "success", "results": 23\}\
    ],\
    "total_results": 23,\
    "execution_time_seconds": 12.4\
  \}\
\}\
```\
\
---\
\
#### Agent 3: **Research Agent**\
\
```\
Role:        Gather enrichment data about target companies\
Goal:        Provide context for better matching and outreach personalization\
LLM:         GPT-4o-mini\
Tools:       web_search, company_db_lookup, glassdoor_scraper,\
             crunchbase_api, linkedin_company_page (public data)\
```\
\
**Output Schema:**\
```json\
\{\
  "company_profiles": \{\
    "Razorpay": \{\
      "domain": "fintech",\
      "stage": "Late Stage / Series F",\
      "headcount": "3000+",\
      "tech_stack_known": ["Go", "Python", "Kubernetes", "AWS", "Kafka"],\
      "engineering_blog_url": "https://engineering.razorpay.com",\
      "glassdoor_rating": 4.1,\
      "recent_news": [\
        "Razorpay launches tokenization platform (Jan 2025)"\
      ],\
      "culture_signals": ["Fast-paced", "High ownership", "Engineering-driven"],\
      "hiring_velocity": "HIGH (30+ engineering roles open)",\
      "linkedin_company_url": "https://linkedin.com/company/razorpay"\
    \}\
  \}\
\}\
```\
\
---\
\
#### Agent 4: **Preference Analyst Agent**\
\
```\
Role:        Score and rank jobs against the candidate profile\
Goal:        Produce a ranked shortlist with explainable, deterministic scores\
LLM:         GPT-4o (needs nuanced reasoning for matching)\
Tools:       vector_similarity_search, scoring_engine, embedding_comparator,\
             tech_adjacency_graph\
```\
\
Full detail in [Section 9](#9-resume-parsing--preference-analysis-engine).\
\
---\
\
#### Agent 5: **Outreach Finder Agent**\
\
```\
Role:        Identify key people at target companies for networking\
Goal:        Build a prioritized contact list with outreach context\
LLM:         GPT-4o (for composing personalized outreach angles)\
Tools:       linkedin_people_search (approved/manual), email_finder,\
             company_org_mapper\
```\
\
Full detail in [Section 10](#10-outreach--networking-pipeline).\
\
---\
\
#### Agent 6: **QA / Critic Agent**\
\
```\
Role:        Verify extraction completeness and check for hallucination risk\
Goal:        Catch errors before they propagate through the pipeline\
LLM:         GPT-4o-mini (pattern matching + verification)\
Tools:       schema_validator, hallucination_detector, completeness_checker\
```\
\
**Responsibilities:**\
- Validates that extracted job fields are complete and internally consistent\
- Cross-checks LLM-generated match reasoning against the actual score breakdown for contradictions\
- Flags jobs where JD extraction confidence is low\
- Detects hallucinated skills or experience claims in the parsed resume\
- Runs after major pipeline stages: post-extraction, post-ranking, post-outreach-draft\
\
**Conflict Resolution Protocol:** When multiple signals produce contradictory results (e.g., semantic match says "strong fit" but hard skill overlap says "weak"), the QA Agent flags the conflict and the final score is computed using a **weighted arbitration rule**: hard skill overlap is treated as a floor constraint\'97if the candidate is missing >50% of must-have skills, the final tier cannot exceed "GOOD MATCH" regardless of semantic similarity. This prevents semantic embedding similarity from masking genuine skill gaps.\
\
---\
\
#### Agent 7: **Feedback Learning Agent**\
\
```\
Role:        Update scoring weights and preferences based on user behavior\
Goal:        Continuously improve match quality over time\
LLM:         GPT-4o-mini (for interpreting patterns)\
Trigger:     User actions (save/dismiss jobs, apply, interview outcomes)\
```\
\
**Consumes:**\
- Saved vs. dismissed jobs\
- Applied vs. ignored recommendations\
- Interview outcomes (if reported)\
- Recruiter response rates\
- Manual edits to outreach drafts\
- Accepted/rejected contacts\
\
**Outputs:**\
- Updated scoring weight vector per user\
- Updated source confidence scores\
- Updated people-ranking weights\
- Updated message style preferences\
\
---\
\
## 5. Manager Orchestration Layer\
\
### 5.1 Why Temporal (Not Celery or Agent-Framework-Only)\
\
The orchestration requirements\'97long-running campaigns that span hours or days, retries with exponential backoff, human approval gates that may block for hours, crash recovery, and complex DAG dependencies\'97demand a **durable workflow engine**. Celery + Redis provides a task queue but lacks native support for workflow durability, long-running approval waits, and complex DAG management. Similarly, relying solely on the agent framework (CrewAI or LangGraph) for orchestration conflates LLM reasoning with infrastructure concerns and provides no crash recovery.\
\
**Temporal** provides crash-proof workflow execution that automatically resumes after failures, native support for long-running activities, timer-based waits for approvals, and visibility tooling for debugging workflow state. The Manager Agent runs as a Temporal Workflow; each worker agent runs as a Temporal Activity.\
\
### 5.2 Task DAG Engine\
\
```\
                    \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
                    \uc0\u9474    USER INPUT       \u9474 \
                    \uc0\u9474    (resume, roles,  \u9474 \
                    \uc0\u9474     companies, tech) \u9474 \
                    \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
                             \uc0\u9474 \
                    \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9660 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
                    \uc0\u9474   PARSE_RESUME      \u9474 \
                    \uc0\u9474   Agent: ResumeParser\u9474 \
                    \uc0\u9474   Depends: none     \u9474 \
                    \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
                             \uc0\u9474 \
              \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
              \uc0\u9474               \u9474                   \u9474                 \u9474 \
    \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9660 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9660 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9660 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488     \u9474 \
    \uc0\u9474  SCOUT_LINKEDIN \u9474  \u9474  SCOUT_NAUKRI  \u9474  \u9474  SCOUT_INDEED  \u9474  ...\u9474 \
    \uc0\u9474  Agent: Scout   \u9474  \u9474  Agent: Scout  \u9474  \u9474  Agent: Scout  \u9474     \u9474 \
    \uc0\u9474  Depends:       \u9474  \u9474  Depends:      \u9474  \u9474  Depends:      \u9474     \u9474 \
    \uc0\u9474   PARSE_RESUME  \u9474  \u9474   PARSE_RESUME \u9474  \u9474   PARSE_RESUME \u9474     \u9474 \
    \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496     \u9474 \
             \uc0\u9474                  \u9474                  \u9474              \u9474 \
             \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496                  \u9474      \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9660 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
                      \uc0\u9474      \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496      \u9474  INGEST_ALERTS    \u9474 \
                      \uc0\u9474      \u9474                           \u9474  (Email Parser)   \u9474 \
                      \uc0\u9474      \u9474                           \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
              \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9660 \u9472 \u9472 \u9472 \u9472 \u9472 \u9660 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488     \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9474 \
              \uc0\u9474   DEDUPLICATE &       \u9474     \u9474  RESEARCH_COMPANIES\u9474  \u9474 \
              \uc0\u9474   CANONICALIZE        \u9474 \u9668 \u9472 \u9472 \u9472 \u9496  Agent: Research   \u9474  \u9474 \
              \uc0\u9474   Agent: Manager      \u9474     \u9474  Depends:          \u9474  \u9474 \
              \uc0\u9474   (self-executed)     \u9474     \u9474    PARSE_RESUME    \u9474  \u9474 \
              \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496     \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
                      \uc0\u9474                             \u9474 \
                      \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
                                 \uc0\u9474 \
                      \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9660 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
                      \uc0\u9474    QA CHECK              \u9474 \
                      \uc0\u9474    Agent: QA/Critic      \u9474 \
                      \uc0\u9474    (verify extractions)  \u9474 \
                      \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
                                 \uc0\u9474 \
                      \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9660 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
                      \uc0\u9474    RANK_AND_FILTER       \u9474 \
                      \uc0\u9474    Agent: PrefAnalyst    \u9474 \
                      \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
                                 \uc0\u9474 \
                      \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9660 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
                      \uc0\u9474  APPROVAL GATE (User)    \u9474 \
                      \uc0\u9474  Review top-N shortlist  \u9474 \
                      \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
                                 \uc0\u9474 \
                      \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9660 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
                      \uc0\u9474    FIND_OUTREACH_TARGETS \u9474 \
                      \uc0\u9474    Agent: OutreachFinder \u9474 \
                      \uc0\u9474    (only top N jobs)     \u9474 \
                      \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
                                 \uc0\u9474 \
                      \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9660 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
                      \uc0\u9474    QA CHECK              \u9474 \
                      \uc0\u9474    (verify contacts/msgs)\u9474 \
                      \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
                                 \uc0\u9474 \
                      \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9660 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
                      \uc0\u9474    COMPILE_REPORT        \u9474 \
                      \uc0\u9474    Agent: Manager (self) \u9474 \
                      \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
                                 \uc0\u9474 \
                      \uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9660 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
                      \uc0\u9474    DELIVER TO USER       \u9474 \
                      \uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
```\
\
### 5.3 Task Data Structure\
\
```python\
@dataclass\
class Task:\
    task_id: str                          # Unique identifier\
    task_type: TaskType                   # Enum: PARSE, SCOUT, RESEARCH, RANK, OUTREACH, etc.\
    assigned_agent: str                   # Agent identifier\
    dependencies: List[str]              # task_ids that must complete first\
    input_payload: dict                   # Serialized input for the agent\
    status: TaskStatus                    # PENDING | QUEUED | RUNNING | SUCCESS | FAILED | TIMEOUT\
    priority: int                         # 1 (highest) to 5 (lowest)\
    retry_count: int                      # Current retry attempt\
    max_retries: int                      # Default 3\
    timeout_seconds: int                  # Default 120\
    result: Optional[dict]               # Agent output on success\
    error: Optional[str]                 # Error message on failure\
    reasoning_trace: Optional[str]       # Agent's explanation of approach\
    idempotency_key: str                 # For safe retries\
    created_at: datetime\
    started_at: Optional[datetime]\
    completed_at: Optional[datetime]\
    cost_tokens_used: Optional[int]      # LLM token consumption tracking\
```\
\
### 5.4 Execution Engine\
\
```python\
class ManagerOrchestrator:\
    """\
    Runs as a Temporal Workflow. Each agent task is a Temporal Activity.\
    """\
\
    def execute_plan(self, dag: TaskDAG, shared_context: SharedContext):\
        while not dag.all_terminal():\
            ready_tasks = dag.get_ready_tasks()\
\
            # Launch ready tasks in parallel as Temporal activities\
            futures = \{\}\
            for task in ready_tasks:\
                task.status = TaskStatus.QUEUED\
                future = workflow.execute_activity(\
                    agent=self.get_agent(task.assigned_agent),\
                    task=task,\
                    context=shared_context,\
                    start_to_close_timeout=timedelta(seconds=task.timeout_seconds),\
                    retry_policy=RetryPolicy(\
                        maximum_attempts=task.max_retries,\
                        backoff_coefficient=2.0\
                    )\
                )\
                futures[task.task_id] = future\
\
            for task_id, future in as_completed(futures):\
                task = dag.get_task(task_id)\
                try:\
                    result = await future\
                    task.status = TaskStatus.SUCCESS\
                    task.result = result\
                    shared_context.update(task_id, result)\
                except ActivityError as e:\
                    task.status = TaskStatus.FAILED\
                    task.error = str(e)\
                    self.handle_failure(dag, task, shared_context)\
\
    def handle_failure(self, dag, failed_task, context):\
        if failed_task.task_type == TaskType.SCOUT:\
            # One platform failing doesn't block others\
            context.mark_source_degraded(failed_task.input_payload['platform'])\
\
            if context.all_scouts_failed():\
                # Escalate to manual input \'97 workflow waits for user signal\
                manual_result = await workflow.wait_for_signal("manual_job_input")\
                # ... inject manual jobs into pipeline\
\
        elif failed_task.task_type == TaskType.PARSE:\
            # Critical path \'97 request manual profile entry\
            raise UnrecoverableError(\
                "Resume parsing failed. Please fill in your profile manually."\
            )\
\
        elif failed_task.task_type == TaskType.RANK:\
            # Re-run with relaxed parameters\
            relaxed_input = \{**failed_task.input_payload, "min_score_threshold": 0.3\}\
            dag.inject_retry(failed_task, new_input=relaxed_input)\
```\
\
### 5.5 Shared Context Store\
\
```python\
class SharedContext:\
    """\
    Thread-safe context store. All agents can read from it.\
    Only the Manager writes (after receiving agent results).\
    Persisted as part of the Temporal workflow state.\
    """\
\
    def __init__(self, run_id: str):\
        self.run_id = run_id\
        self.candidate_profile = None       # Set after resume parsing\
        self.user_preferences = None        # Set from user inputs\
        self.raw_jobs = \{\}                  # platform -> [jobs]\
        self.canonical_jobs = []            # After dedup + canonicalization\
        self.company_profiles = \{\}          # company_name -> profile\
        self.ranked_jobs = []               # After preference analysis\
        self.outreach_targets = []          # After outreach finding\
        self.degraded_sources = set()       # Platforms that failed\
        self.execution_log = []             # Ordered log of all events\
        self.approval_decisions = \{\}        # User approval gate results\
\
    def get_search_params(self) -> dict:\
        return \{\
            "titles": self.user_preferences.target_roles,\
            "companies": self.user_preferences.target_companies,\
            "tech_keywords": (self.candidate_profile.skills.languages\
                            + self.candidate_profile.skills.frameworks),\
            "location": self.candidate_profile.location.city,\
            "experience_range": \{\
                "min": self.candidate_profile.total_years_experience - 2,\
                "max": self.candidate_profile.total_years_experience + 3\
            \}\
        \}\
```\
\
---\
\
## 6. Data Models & Schema Design\
\
### 6.1 Database Schema (PostgreSQL)\
\
```sql\
-- Core entities\
\
CREATE TABLE users (\
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),\
    email           VARCHAR(255) UNIQUE NOT NULL,\
    name            VARCHAR(255),\
    created_at      TIMESTAMPTZ DEFAULT NOW(),\
    updated_at      TIMESTAMPTZ DEFAULT NOW()\
);\
\
CREATE TABLE resumes (\
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),\
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,\
    file_path       VARCHAR(500) NOT NULL,\
    parsed_profile  JSONB,\
    parsing_status  VARCHAR(20) DEFAULT 'pending',\
    embedding_ids   JSONB,\
    uploaded_at     TIMESTAMPTZ DEFAULT NOW(),\
    parsed_at       TIMESTAMPTZ\
);\
\
CREATE TABLE candidate_preferences (\
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),\
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,\
    target_roles    JSONB NOT NULL,\
    target_companies JSONB,\
    tech_stack      JSONB,\
    locations       JSONB,\
    work_modes      JSONB,\
    seniority_preference VARCHAR(50),\
    salary_preference JSONB,\
    company_excludes JSONB,\
    scoring_weights JSONB,              -- User-customizable score weights\
    updated_at      TIMESTAMPTZ DEFAULT NOW()\
);\
\
CREATE TABLE search_campaigns (\
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),\
    user_id         UUID REFERENCES users(id),\
    resume_id       UUID REFERENCES resumes(id),\
    preferences_id  UUID REFERENCES candidate_preferences(id),\
    status          VARCHAR(20) DEFAULT 'pending',\
    task_dag        JSONB,\
    execution_log   JSONB,\
    final_report    JSONB,\
    total_tokens    INTEGER DEFAULT 0,\
    total_cost_usd  DECIMAL(10,4) DEFAULT 0,\
    temporal_workflow_id VARCHAR(255),\
    started_at      TIMESTAMPTZ,\
    completed_at    TIMESTAMPTZ,\
    created_at      TIMESTAMPTZ DEFAULT NOW()\
);\
\
-- Source policy enforcement\
CREATE TABLE source_policies (\
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),\
    source_name     VARCHAR(50) UNIQUE NOT NULL,\
    allowed_modes   JSONB NOT NULL,      -- ["official_api","licensed_vendor","alerts"]\
    blocked_modes   JSONB,               -- ["stealth_scraping","captcha_bypass"]\
    requires_user_auth BOOLEAN DEFAULT false,\
    rate_limit_policy JSONB,             -- \{"max_rpm": 20, "burst": 5\}\
    confidence_weight DECIMAL(3,2) DEFAULT 1.0,\
    allowed_actions JSONB,               -- ["discover","fetch_jd","resolve_apply_link"]\
    disallowed_actions JSONB,            -- ["auto_apply","auto_message"]\
    updated_at      TIMESTAMPTZ DEFAULT NOW()\
);\
\
-- Raw and canonical job storage\
CREATE TABLE raw_job_artifacts (\
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),\
    campaign_id     UUID REFERENCES search_campaigns(id),\
    source_platform VARCHAR(50) NOT NULL,\
    external_id     VARCHAR(255),\
    raw_content     TEXT,\
    retrieval_strategy VARCHAR(50),\
    scraped_at      TIMESTAMPTZ,\
    created_at      TIMESTAMPTZ DEFAULT NOW()\
);\
\
CREATE TABLE canonical_jobs (\
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),\
    campaign_id     UUID REFERENCES search_campaigns(id),\
    title_normalized VARCHAR(500),\
    company_id      UUID REFERENCES companies(id),\
    location_normalized VARCHAR(255),\
    remote_type     VARCHAR(50),\
    employment_type VARCHAR(50),\
    description_raw TEXT,\
    description_structured JSONB,\
    salary_info     JSONB,\
    application_url_board VARCHAR(1000),\
    application_url_employer VARCHAR(1000),  -- Canonical ATS URL\
    apply_channel   VARCHAR(50),\
    posted_date     DATE,\
    embedding_id    VARCHAR(100),\
    confidence_score DECIMAL(3,2),\
    risk_flags      JSONB,\
    content_hash    VARCHAR(64),\
    source_refs     JSONB,                   -- [\{platform, external_id, url\}]\
    staleness_checked_at TIMESTAMPTZ,\
    UNIQUE(campaign_id, content_hash)\
);\
\
CREATE TABLE job_matches (\
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),\
    campaign_id     UUID REFERENCES search_campaigns(id),\
    job_id          UUID REFERENCES canonical_jobs(id),\
    match_score     DECIMAL(4,3) NOT NULL,\
    match_tier      VARCHAR(20),\
    score_breakdown JSONB NOT NULL,\
    reasoning_trace TEXT,\
    gaps_identified JSONB,\
    conflict_flags  JSONB,                   -- Signal contradiction warnings\
    recommended_action VARCHAR(50),\
    rank_position   INTEGER,\
    created_at      TIMESTAMPTZ DEFAULT NOW()\
);\
\
CREATE TABLE companies (\
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),\
    name            VARCHAR(255) UNIQUE,\
    domain          VARCHAR(100),\
    stage           VARCHAR(100),\
    headcount       VARCHAR(50),\
    tech_stack      JSONB,\
    glassdoor_rating DECIMAL(2,1),\
    culture_signals JSONB,\
    enrichment_data JSONB,\
    last_updated    TIMESTAMPTZ DEFAULT NOW()\
);\
\
CREATE TABLE outreach_contacts (\
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),\
    campaign_id     UUID REFERENCES search_campaigns(id),\
    job_id          UUID REFERENCES canonical_jobs(id),\
    name            VARCHAR(255),\
    title           VARCHAR(500),\
    company_id      UUID REFERENCES companies(id),\
    linkedin_url    VARCHAR(1000),\
    contact_type    VARCHAR(50),           -- HIRING_MANAGER | RECRUITER | PEER | ALUMNI\
    priority        VARCHAR(20),\
    connection_degree INTEGER,\
    mutual_connections INTEGER,\
    shared_background JSONB,\
    outreach_angle  TEXT,\
    message_draft   TEXT,\
    identity_confidence DECIMAL(3,2),\
    created_at      TIMESTAMPTZ DEFAULT NOW()\
);\
\
CREATE TABLE approval_tasks (\
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),\
    campaign_id     UUID REFERENCES search_campaigns(id),\
    approval_type   VARCHAR(50),            -- SHORTLIST | CONTACTS | DRAFTS | RISK_REVIEW\
    payload         JSONB,\
    status          VARCHAR(20) DEFAULT 'pending',\
    decided_at      TIMESTAMPTZ,\
    decision_notes  TEXT\
);\
\
CREATE TABLE user_actions (\
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),\
    user_id         UUID REFERENCES users(id),\
    campaign_id     UUID REFERENCES search_campaigns(id),\
    job_id          UUID REFERENCES canonical_jobs(id),\
    action_type     VARCHAR(50),            -- SAVED | DISMISSED | APPLIED | INTERVIEWED | OFFERED\
    metadata        JSONB,\
    created_at      TIMESTAMPTZ DEFAULT NOW()\
);\
\
CREATE TABLE audit_logs (\
    id              BIGSERIAL PRIMARY KEY,\
    campaign_id     UUID,\
    agent           VARCHAR(100),\
    action          VARCHAR(255),\
    details         JSONB,\
    created_at      TIMESTAMPTZ DEFAULT NOW()\
);\
\
-- Indexes\
CREATE INDEX idx_canonical_jobs_campaign ON canonical_jobs(campaign_id);\
CREATE INDEX idx_canonical_jobs_company ON canonical_jobs(company_id);\
CREATE INDEX idx_canonical_jobs_hash ON canonical_jobs(content_hash);\
CREATE INDEX idx_matches_campaign_score ON job_matches(campaign_id, match_score DESC);\
CREATE INDEX idx_contacts_campaign_job ON outreach_contacts(campaign_id, job_id);\
CREATE INDEX idx_user_actions_user ON user_actions(user_id, action_type);\
```\
\
### 6.2 Vector Store Schema (Qdrant)\
\
```\
Collection: "candidate_profiles"\
  - Vector dim: 1536 (OpenAI text-embedding-3-small) or 768 (local)\
  - Payload: \{ user_id, embedding_type: "full_profile"|"skills"|"experience" \}\
\
Collection: "job_descriptions"\
  - Vector dim: 1536\
  - Payload: \{ job_id, campaign_id, company, title, platform \}\
\
Similarity search usage:\
  - Query: candidate_profile embedding\
  - Against: job_descriptions collection\
  - Metric: Cosine similarity\
  - Used by: Preference Analyst Agent for semantic matching\
```\
\
### 6.3 Optional Graph Projection\
\
For complex contact discovery scenarios where the same person appears across multiple companies/roles or where referral chains matter, consider an optional graph projection:\
\
```\
(Person) --[WORKS_AT]--> (Company)\
(Person) --[POSTED]--> (Job)\
(Company) --[HAS_OPENING]--> (Job)\
(Person) --[MANAGES_TEAM]--> (Team)\
(Job) --[BELONGS_TO]--> (Team)\
(Candidate) --[ALUMNI_OF]--> (Institution)\
(Person) --[ALUMNI_OF]--> (Institution)\
```\
\
This can be implemented as a materialized view in PostgreSQL or a lightweight graph database (e.g., Neo4j) if contact discovery complexity warrants it.\
\
---\
\
## 7. End-to-End Data Flow\
\
### Flow A: Campaign Creation & Parsing\
\
1. User uploads resume PDF, enters roles, companies, tech stack, locations, and optional manual job links.\
2. Campaign Service validates inputs, stores files in object store, creates `SearchCampaign`.\
3. Manager Agent launches Resume Parser Agent as a Temporal activity.\
4. Candidate profile is extracted, skills normalized, and embeddings generated.\
5. User reviews/edits extracted profile before discovery begins (optional approval gate).\
\
### Flow B: Discovery\
\
1. Query Planner expands role/title synonyms and stack terms using the Skill Taxonomy Service.\
2. Source Strategy checks the **Source Capability Registry** for each platform's allowed modes.\
3. Manager spawns parallel Discovery/Scout Agents\'97one per platform.\
4. Each adapter runs its strategy cascade within allowed modes:\
   - Official API \uc0\u8594  Licensed vendor \u8594  Alert email ingestion \u8594  Employer ATS \u8594  Manual fallback.\
5. **Alert Ingestion Service** independently parses configured job alert emails, extracting links.\
6. Raw jobs are stored as immutable `raw_job_artifacts`.\
7. Failures create retry events or human review tasks (never attempted CAPTCHA bypass).\
\
### Flow C: Canonicalization, Deduplication & Matching\
\
1. **Canonicalization Agent** normalizes titles, companies, locations, skills.\
2. **Deduplication** merges cross-platform duplicates using content hashing + fuzzy matching + embedding similarity.\
3. **Canonical employer ATS/apply links** are resolved where possible\'97treating the board URL as secondary and the employer career page as primary.\
4. **Job Risk Detector** flags suspicious postings (see Section 12).\
5. **QA/Critic Agent** verifies extraction completeness and consistency.\
6. **Match Engine** computes multi-signal scores + explanations.\
7. **Conflict Resolution** runs if signals disagree (see Agent 6 above).\
8. Top jobs move to shortlist \uc0\u8594  **Approval Gate** for user review.\
\
### Flow D: Outreach & Networking\
\
1. Company Research Agent gathers context for top-N approved jobs.\
2. People Finder Agent ranks contacts: Recruiter on posting \uc0\u8594  Hiring Manager \u8594  Peer.\
3. Outreach Draft Agent creates channel-specific drafts (LinkedIn note, email, referral request).\
4. **Approval Gate** before any outreach is sent\'97drafts are copy/paste or user-approved send.\
5. Daily send caps enforced; bulk outreach disabled by default.\
\
### Flow E: Feedback Loop\
\
1. User saves/dismisses jobs, edits messages, marks contacts as useful/not, reports outcomes.\
2. System records all actions in `user_actions`.\
3. Feedback Learning Agent periodically updates scoring weights and preferences.\
\
---\
\
## 8. Job Discovery & Source Acquisition Strategy\
\
### 8.1 Source Capability Registry\
\
The Source Capability Registry is a **database-backed policy enforcement layer** that every adapter must check before making any request. This is the central mechanism that keeps the system compliant and sustainable.\
\
```python\
@dataclass\
class SourcePolicy:\
    source_name: str\
    allowed_modes: List[str]          # ["official_api", "licensed_vendor", "alerts",\
                                      #  "employer_ats", "manual_input", "browser_allowlisted"]\
    blocked_modes: List[str]          # ["captcha_bypass", "stealth_scraping", "auto_apply"]\
    requires_user_auth: bool\
    requires_human_review_on_challenge: bool\
    rate_limit_policy: dict           # \{"max_rpm": 20, "burst": 5\}\
    data_retention_policy: str\
    confidence_weight: float          # How much to trust results from this source\
    allowed_actions: List[str]        # ["discover", "fetch_jd", "resolve_apply_link"]\
    disallowed_actions: List[str]     # ["auto_apply", "auto_message"]\
```\
\
### 8.2 Platform-Specific Compliance Position\
\
**LinkedIn:** Use approved partner/API integrations where available, user-created job alerts as a first-class discovery channel, manual LinkedIn job URLs, and user-provided exports. Do **not** design for generic LinkedIn scraping, auto-messaging, or background browser automation on LinkedIn pages. LinkedIn's terms explicitly prohibit third-party software that scrapes or automates site activity.\
\
**Indeed:** Use official partner APIs if approved, user job alerts, manual job URLs, and canonical employer ATS URLs. Do **not** use generic bots/scrapers or automated application submission unless contractually permitted.\
\
**Naukri:** Use user search + alert ingestion, manual link input, licensed/approved access if obtained. Naukri's terms state they use technological measures against robots/scraping and forbid circumvention.\
\
**IIMJobs:** Use manual links, public listing fetches where policy permits, user-assisted discovery. IIMJobs' terms prohibit duplication/distribution and block robots.\
\
### 8.3 Alert Email Ingestion as a First-Class Channel\
\
This is one of the most practical and stable discovery approaches. All four target platforms support user-facing job alerts:\
\
- LinkedIn job alert emails\
- Indeed email job alerts\
- Naukri email/push alerts\
- IIMJobs app notifications\
\
Build an **Email/Notification Ingestion Service** that:\
1. Connects to the user's email via OAuth (Gmail, Outlook)\
2. Filters for job alert emails by sender/subject patterns\
3. Extracts job links using pattern matching + LLM fallback\
4. Feeds links into the canonicalization pipeline\
5. Can also accept forwarded alert emails or CSV pastes\
\
This channel is often more stable than direct board access and operates entirely within platform-supported flows.\
\
### 8.4 Canonical Employer ATS Resolution\
\
Treat job boards as **discovery channels**, not the final source of truth. Whenever possible, resolve the board listing to the employer's own career page or ATS system:\
\
- LinkedIn job postings often include an `applyUrl` pointing to the employer's ATS\
- Naukri postings reference "Apply on Company Website" links\
- Indeed aggregates jobs from company career sites\
\
The data model stores:\
- `application_url_board` \'97 the board listing URL\
- `application_url_employer` \'97 the canonical employer career/ATS URL\
- `source_refs[]` \'97 all platforms where this job appeared\
- `apply_channel` \'97 where the user should actually apply\
\
This improves deduplication, freshness detection, and application success rate.\
\
### 8.5 Platform Adapter Interface\
\
```python\
from abc import ABC, abstractmethod\
from typing import List, Optional\
from enum import Enum\
\
class RetrievalStrategy(Enum):\
    OFFICIAL_API = "official_api"\
    LICENSED_VENDOR = "licensed_vendor"\
    ALERT_INGESTION = "alert_ingestion"\
    EMPLOYER_ATS = "employer_ats"\
    MANUAL_INPUT = "manual_input"\
    BROWSER_ALLOWLISTED = "browser_allowlisted"\
\
class PlatformAdapter(ABC):\
    """\
    Base class for all job platform integrations.\
    Each platform implements this with platform-specific logic.\
    """\
\
    def __init__(self, config: dict, source_policy: SourcePolicy,\
                 proxy_pool, rate_limiter, session_manager):\
        self.config = config\
        self.source_policy = source_policy\
        self.proxy_pool = proxy_pool\
        self.rate_limiter = rate_limiter\
        self.session_manager = session_manager\
        self.strategies = self._configure_strategies()\
\
    def _configure_strategies(self) -> List[RetrievalStrategy]:\
        """Return ordered strategies filtered by source policy."""\
        all_strategies = self._preferred_strategy_order()\
        return [s for s in all_strategies\
                if s.value in self.source_policy.allowed_modes]\
\
    @abstractmethod\
    def _preferred_strategy_order(self) -> List[RetrievalStrategy]:\
        pass\
\
    @abstractmethod\
    def _execute_strategy(self, strategy: RetrievalStrategy,\
                          params: dict) -> StrategyResult:\
        pass\
\
    def search(self, params: dict) -> StrategyResult:\
        """Execute strategy cascade. Try each in order until one succeeds."""\
        all_results = []\
        for strategy in self.strategies:\
            # Policy check before every request\
            if not self._policy_allows(strategy, "discover"):\
                continue\
\
            result = self._execute_strategy(strategy, params)\
\
            if result.status == "success":\
                return result\
            elif result.status == "partial":\
                all_results.extend(result.results)\
                continue\
            elif result.status == "challenge_detected":\
                # STOP \'97 create human review task\
                self._create_human_task(strategy, result)\
                continue\
            else:\
                logger.warning(f"\{self.__class__.__name__\}: "\
                              f"\{strategy\} failed: \{result.error\}")\
                continue\
\
        if all_results:\
            return StrategyResult(status="partial", results=all_results)\
\
        return StrategyResult(\
            strategy=RetrievalStrategy.MANUAL_INPUT,\
            status="failed",\
            results=[],\
            error="All retrieval strategies exhausted"\
        )\
```\
\
### 8.6 Browser Automation Safe Envelope\
\
Browser automation via Playwright is used **only** for:\
- Employer career pages and external ATS systems (Lever, Greenhouse, Workday)\
- Manual replay of user-provided links\
- Structured capture on allowlisted domains\
\
**Never** used to defeat platform controls on restricted job boards.\
\
Design constraints:\
- Isolated Playwright containers with separate browser node pool\
- Domain-level concurrency controls\
- Proxy layer for reliability/geo-routing only\
- Screenshot + DOM snapshot on errors for debugging\
- **Automatic stop on any challenge page** (login wall, CAPTCHA, bot detection)\
- Human review task created on challenge \'97 no bypass attempts\
- Secure vault for session cookie injection when the user explicitly provides credentials, keeping them isolated from agent logic\
\
### 8.7 Job Deduplication Strategy\
\
```\
Step 1: Exact Hash Match\
  hash = SHA256(normalize(title) + normalize(company) + normalize(location))\
  If hash matches \uc0\u8594  definite duplicate \u8594  keep the one with richer data\
\
Step 2: Fuzzy Match (for near-duplicates)\
  - title_similarity = fuzzy_ratio(title_a, title_b)        threshold: >85%\
  - company_similarity = fuzzy_ratio(company_a, company_b)  threshold: >90%\
  - description_similarity = cosine_sim(embed_a, embed_b)   threshold: >0.92\
  If all three pass \uc0\u8594  likely duplicate \u8594  merge, prefer employer ATS link\
\
Step 3: Cross-Platform ID / URL Matching\
  Canonical employer URL deduplication across board listings.\
\
Output:\
  Canonical job record with:\
  - List of all source platforms where it appeared\
  - Best application URL selected (prefer employer ATS)\
  - Source provenance chain\
```\
\
---\
\
## 9. Resume Parsing & Preference Analysis Engine\
\
### 9.1 Resume Parsing Pipeline\
\
```\
Stage 1: RAW TEXT EXTRACTION\
  \uc0\u9500 \u9472 \u9472  PyMuPDF / pdfplumber \u8594  text extraction\
  \uc0\u9500 \u9472 \u9472  Quality check: >100 chars? \u8594  proceed\
  \uc0\u9492 \u9472 \u9472  <100 chars (scanned PDF) \u8594  GPT-4o Vision multimodal extraction\
\
Stage 2: LLM STRUCTURED EXTRACTION\
  \uc0\u9500 \u9472 \u9472  System prompt extracts into CandidateProfile schema\
  \uc0\u9500 \u9472 \u9472  Structured JSON output with all fields\
  \uc0\u9492 \u9472 \u9472  JSON schema validation + sanity checks\
\
Stage 3: SKILL NORMALIZATION (via Skill Taxonomy Service)\
  \uc0\u9500 \u9472 \u9472  Raw: "React.js, ReactJS, react" \u8594  Normalized: "React"\
  \uc0\u9500 \u9472 \u9472  Raw: "Amazon Web Services"      \u8594  Normalized: "AWS"\
  \uc0\u9500 \u9472 \u9472  Raw: "k8s"                      \u8594  Normalized: "Kubernetes"\
  \uc0\u9492 \u9472 \u9472  Uses maintained synonym dictionary + LLM fallback\
\
Stage 4: EMBEDDING GENERATION\
  \uc0\u9500 \u9472 \u9472  Full profile summary text \u8594  1 embedding\
  \uc0\u9500 \u9472 \u9472  Skills concatenated text \u8594  1 embedding\
  \uc0\u9492 \u9472 \u9472  Each work experience block \u8594  N embeddings\
  \uc0\u8594  Stored in Qdrant with metadata\
\
Stage 5: HUMAN CORRECTION (Optional)\
  \uc0\u9492 \u9472 \u9472  Review UI for ambiguous fields before discovery starts\
```\
\
### 9.2 Preference Matching \'97 Multi-Signal Scoring Algorithm\
\
```\
\uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
\uc0\u9474                 MATCH SCORING ALGORITHM                           \u9474 \
\uc0\u9474                                                                  \u9474 \
\uc0\u9474   Final Score = \u931  (weight_i \'d7 signal_i)                          \u9474 \
\uc0\u9474                                                                  \u9474 \
\uc0\u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9516 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9474 \
\uc0\u9474   \u9474  Signal                   \u9474  Weight \u9474  Method                  \u9474  \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9508  \u9474 \
\uc0\u9474   \u9474  Skills Match             \u9474   0.30  \u9474  Jaccard + Semantic +    \u9474  \u9474 \
\uc0\u9474   \u9474                           \u9474         \u9474  Tech Adjacency Graph    \u9474  \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9508  \u9474 \
\uc0\u9474   \u9474  Title Alignment          \u9474   0.15  \u9474  Embedding cosine sim    \u9474  \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9508  \u9474 \
\uc0\u9474   \u9474  Experience Level Fit     \u9474   0.15  \u9474  Range overlap + decay   \u9474  \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9508  \u9474 \
\uc0\u9474   \u9474  Semantic JD-Resume Sim   \u9474   0.15  \u9474  Full embedding cosine   \u9474  \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9508  \u9474 \
\uc0\u9474   \u9474  Company Preference       \u9474   0.10  \u9474  Exact + domain match    \u9474  \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9508  \u9474 \
\uc0\u9474   \u9474  Location/Remote Fit      \u9474   0.05  \u9474  Rule-based              \u9474  \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9508  \u9474 \
\uc0\u9474   \u9474  Recency of Posting       \u9474   0.05  \u9474  Exponential decay       \u9474  \u9474 \
\uc0\u9474   \u9500 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9508  \u9474 \
\uc0\u9474   \u9474  Source Confidence         \u9474   0.05  \u9474  From Source Policy      \u9474  \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9524 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9524 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9474 \
\uc0\u9474                                                                  \u9474 \
\uc0\u9474   Users can customize weights via preferences:                    \u9474 \
\uc0\u9474   \{                                                               \u9474 \
\uc0\u9474     "skills_match": 0.40,   // "I care most about skill fit"     \u9474 \
\uc0\u9474     "company_preference": 0.20,                                   \u9474 \
\uc0\u9474     "location_fit": 0.02,   // "I'm flexible on location"        \u9474 \
\uc0\u9474   \}                                                               \u9474 \
\uc0\u9474                                                                  \u9474 \
\uc0\u9474   Score Tiers:                                                    \u9474 \
\uc0\u9474   \u8805  0.80  \u8594   \u55357 \u57314  STRONG MATCH   (auto-shortlist)                 \u9474 \
\uc0\u9474   0.60-0.79 \u8594  \u55357 \u57313  GOOD MATCH    (recommend review)               \u9474 \
\uc0\u9474   0.40-0.59 \u8594  \u55357 \u57312  PARTIAL MATCH (stretch role)                   \u9474 \
\uc0\u9474   < 0.40    \u8594  \u55357 \u56628  WEAK MATCH    (exclude by default)             \u9474 \
\uc0\u9474                                                                  \u9474 \
\uc0\u9474   CONFLICT ARBITRATION RULE:                                      \u9474 \
\uc0\u9474   If semantic similarity > 0.80 but hard skill overlap < 0.50,   \u9474 \
\uc0\u9474   final tier is capped at GOOD MATCH and the QA Agent flags      \u9474 \
\uc0\u9474   the conflict for user awareness.                                \u9474 \
\uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
```\
\
### 9.3 Tech Adjacency Graph\
\
A key innovation for fuzzy skill matching that goes beyond exact keyword overlap:\
\
```json\
\{\
  "equivalences": \{\
    "react": ["react.js", "reactjs"],\
    "vue": ["vue.js", "vuejs"],\
    "node": ["node.js", "nodejs"],\
    "postgres": ["postgresql", "psql"],\
    "k8s": ["kubernetes"],\
    "aws": ["amazon web services"]\
  \},\
  "adjacencies": \{\
    "react":       \{"vue": 0.7, "angular": 0.6, "svelte": 0.5\},\
    "python":      \{"go": 0.5, "ruby": 0.4, "java": 0.3\},\
    "postgresql":  \{"mysql": 0.8, "mariadb": 0.85, "cockroachdb": 0.7\},\
    "kubernetes":  \{"docker": 0.8, "nomad": 0.6, "ecs": 0.5\},\
    "kafka":       \{"rabbitmq": 0.6, "pulsar": 0.7, "kinesis": 0.5\},\
    "fastapi":     \{"flask": 0.8, "django": 0.6, "express": 0.4\},\
    "terraform":   \{"pulumi": 0.8, "cloudformation": 0.6, "ansible": 0.4\}\
  \}\
\}\
```\
\
When computing skill overlap, candidate skills are expanded using equivalences (exact match) and adjacencies (weighted partial credit). This means a candidate with Docker experience gets partial credit toward a Kubernetes requirement, rather than a binary miss.\
\
### 9.4 Skills Match Detail\
\
```python\
def _score_skills(self, candidate, job) -> dict:\
    candidate_skills = set(s.lower() for s in candidate.all_skills())\
    must_have = set(s.lower() for s in job.requirements.must_have)\
    nice_to_have = set(s.lower() for s in job.requirements.nice_to_have)\
\
    # Expand candidate skills with equivalences and adjacencies\
    expanded_candidate = set()\
    for skill in candidate_skills:\
        expanded_candidate.add(skill)\
        expanded_candidate.update(self.skill_graph.get_equivalents(skill))\
\
    # Hard match\
    must_have_matched = expanded_candidate & must_have\
    nice_matched = expanded_candidate & nice_to_have\
    hard_score = len(must_have_matched) / max(len(must_have), 1)\
\
    # Adjacency credit for unmatched must-haves\
    adjacency_bonus = 0\
    unmatched = must_have - expanded_candidate\
    for skill in unmatched:\
        best_adj = max(\
            (self.skill_graph.adjacency_score(skill, cs)\
             for cs in candidate_skills), default=0\
        )\
        adjacency_bonus += best_adj\
    adjacency_score = adjacency_bonus / max(len(must_have), 1)\
\
    nice_bonus = 0.1 * (len(nice_matched) / max(len(nice_to_have), 1))\
\
    # Semantic match via embeddings\
    semantic_score = self.vector_store.similarity(\
        candidate.embedding_ids['skills_cluster'],\
        job.embedding_id\
    )\
\
    combined = (0.4 * hard_score +\
                0.2 * adjacency_score +\
                0.25 * semantic_score +\
                0.15 * nice_bonus)\
\
    return \{\
        'score': min(combined, 1.0),\
        'detail': f"\{len(must_have_matched)\}/\{len(must_have)\} must-have matched, "\
                  f"adjacency credit for \{len(unmatched)\} gaps, "\
                  f"semantic=\{semantic_score:.2f\}"\
    \}\
```\
\
### 9.5 Gap Identification\
\
```python\
def _identify_gaps(self, candidate, job) -> List[str]:\
    gaps = []\
    candidate_skills = set(s.lower() for s in candidate.all_skills())\
\
    for skill in job.requirements.must_have:\
        if skill.lower() not in candidate_skills:\
            adjacent = self.skill_graph.get_adjacent(skill.lower())\
            overlap = candidate_skills & adjacent\
            if overlap:\
                gaps.append(\
                    f"JD requires \{skill\}; candidate has related: "\
                    f"\{', '.join(overlap)\} (transferable)"\
                )\
            else:\
                gaps.append(\
                    f"JD requires \{skill\}; not found in candidate profile"\
                )\
    return gaps\
```\
\
### 9.6 Match Output Schema\
\
```json\
\{\
  "ranked_jobs": [\
    \{\
      "rank": 1,\
      "job_id": "canonical_12345",\
      "title": "Senior Backend Engineer",\
      "company": "Razorpay",\
      "match_score": 0.87,\
      "match_tier": "STRONG_MATCH",\
      "score_breakdown": \{\
        "skills_match": \{"score": 0.91, "detail": "8/9 must-have matched"\},\
        "experience_fit": \{"score": 0.85, "detail": "7.5 YoE in 5-10 range"\},\
        "title_alignment": \{"score": 0.88, "detail": "High semantic similarity"\},\
        "semantic_sim": \{"score": 0.84, "detail": "JD-resume embedding cosine"\},\
        "company_preference": \{"score": 1.0, "detail": "Exact company match"\},\
        "location_fit": \{"score": 0.80, "detail": "Hybrid in preferred city"\},\
        "recency": \{"score": 0.95, "detail": "Posted 5 days ago"\},\
        "source_confidence": \{"score": 0.90, "detail": "Via licensed API"\}\
      \},\
      "reasoning_trace": "This role at Razorpay is a strong match because...",\
      "gaps_identified": ["JD mentions Go; candidate has limited Go (Python\uc0\u8594 Go adjacency: 0.5)"],\
      "conflict_flags": [],\
      "application_url_employer": "https://razorpay.com/careers/12345",\
      "application_url_board": "https://naukri.com/apply/12345",\
      "recommended_action": "APPLY_NOW",\
      "why_this_job": "Strong Python/K8s overlap, exact company match, active hiring.",\
      "risk_flags": []\
    \}\
  ],\
  "summary_stats": \{\
    "total_evaluated": 92,\
    "strong_matches": 8,\
    "good_matches": 15,\
    "partial_matches": 23,\
    "excluded": 46\
  \}\
\}\
```\
\
---\
\
## 10. Outreach & Networking Pipeline\
\
### 10.1 Contact Discovery Strategy\
\
For each shortlisted company+role combination:\
\
```\
1. RECRUITER ON THE POSTING (Priority: \uc0\u11088 \u11088 \u11088  HIGHEST)\
   \uc0\u9500 \u9472 \u9472  Extract recruiter name from JD metadata\
   \uc0\u9500 \u9472 \u9472  Cross-reference with LinkedIn profile\
   \uc0\u9492 \u9472 \u9472  Highest confidence: person is directly tied to this role\
\
2. HIRING MANAGER (Priority: \uc0\u11088 \u11088 \u11088  HIGH)\
   \uc0\u9500 \u9472 \u9472  Search: "(Engineering Manager OR Director) AND \{company\}"\
   \uc0\u9500 \u9472 \u9472  Filter by department alignment with the job\
   \uc0\u9492 \u9472 \u9472  Heuristic: team/function keywords in title match JD department\
\
3. HR / TALENT ACQUISITION (Priority: \uc0\u11088 \u11088 \u11088  HIGH)\
   \uc0\u9500 \u9472 \u9472  Search: "(Recruiter OR Talent Acquisition) AND \{company\}"\
   \uc0\u9500 \u9472 \u9472  Prefer those who posted/shared the specific job listing\
   \uc0\u9492 \u9472 \u9472  Cross-ref: check if JD mentions recruiter email\
\
4. POTENTIAL PEERS / TEAM MEMBERS (Priority: \uc0\u11088 \u11088  MEDIUM)\
   \uc0\u9500 \u9472 \u9472  Search: "\{similar_title\} AND \{company\}"\
   \uc0\u9500 \u9472 \u9472  Purpose: informational outreach\
   \uc0\u9492 \u9472 \u9472  Check for shared connections or alumni overlap\
\
5. ALUMNI CONNECTIONS (Priority: \uc0\u11088 \u11088  MEDIUM)\
   \uc0\u9500 \u9472 \u9472  Search: "\{user's university\} AND \{company\}"\
   \uc0\u9492 \u9472 \u9472  Warm intro potential\
```\
\
**Important compliance note on LinkedIn people search:** This should be limited to approved APIs/partner integrations, manual user-provided links, user-provided exports (e.g., LinkedIn CSV export), or Google Custom Search API targeting `site:linkedin.com/in`. Do not design for generic LinkedIn profile scraping. When identity confidence is low, create a human review task rather than guessing.\
\
### 10.2 Contact Ranking Features\
\
- Role proximity to the opening\
- Org/department proximity\
- Title relevance\
- Location overlap\
- Tech stack overlap\
- Whether person appears directly tied to the posting\
- Confidence of identity match\
- Recency/activity signals\
\
### 10.3 Outreach Output Types\
\
| Draft Type | Channel | Purpose |\
|---|---|---|\
| Connection request note | LinkedIn (1 line) | Initial contact |\
| Recruiter intro | LinkedIn/Email (4-6 lines) | Reference specific role |\
| Peer referral request | LinkedIn/Email | "What's it like working on..." |\
| Cover letter variant | Application portal | Tailored to JD |\
| Follow-up email | Email | After application submitted |\
\
### 10.4 Outreach Contact Output Schema\
\
```json\
\{\
  "outreach_targets": [\
    \{\
      "for_job_id": "canonical_12345",\
      "company": "Razorpay",\
      "contacts": [\
        \{\
          "name": "Priya Sharma",\
          "title": "Engineering Manager - Payments Platform",\
          "linkedin_url": "https://linkedin.com/in/priyasharma",\
          "contact_type": "HIRING_MANAGER",\
          "priority": "HIGH",\
          "connection_degree": 2,\
          "mutual_connections": 3,\
          "shared_background": ["IIT Delhi alumni"],\
          "identity_confidence": 0.85,\
          "suggested_outreach_angle": "Fellow IIT Delhi alum with deep Python + distributed systems experience.",\
          "message_drafts": \{\
            "linkedin_connection_note": "Hi Priya, fellow IIT Delhi alum here...",\
            "recruiter_intro": "Hi Priya, I noticed you lead the Payments Platform team..."\
          \}\
        \}\
      ]\
    \}\
  ]\
\}\
```\
\
### 10.5 Outreach Approval Rules\
\
- **LinkedIn drafts:** Manual copy/send only \'97 user copies message and sends themselves.\
- **Email drafts:** Optionally send via user's connected mailbox (OAuth) after explicit approval.\
- **Bulk outreach:** Disabled by default.\
- **Daily send caps:** Enforced (configurable, e.g., 10 LinkedIn notes/day).\
- **Approval gate:** Every outreach batch requires user review before any action.\
\
---\
\
## 11. Anti-Scraping Resilience & Source Policy Enforcement\
\
### 11.1 Design Philosophy\
\
This system is designed as a **policy-aware acquisition platform**, not a "bypass anti-scraping" engine. The architecture treats source compliance as a first-class engineering concern rather than an afterthought. Anti-detection measures are employed only on allowlisted employer career pages/ATS systems, never to defeat controls on major job boards.\
\
### 11.2 Resilience Matrix (for Allowlisted Sources)\
\
| Threat | Mitigation | Fallback |\
|---|---|---|\
| IP-based rate limiting | Rotating residential proxies (BrightData/SmartProxy), India-geo targeted | Switch proxy provider; reduce rate |\
| Browser fingerprinting | Random viewport, User-Agent rotation, timezone matching (employer ATS pages only) | New browser context per request |\
| CAPTCHA / Login wall | **STOP** \'97 create human review task | User-assisted browsing or manual link input |\
| Rate limiting (429) | Redis token bucket per domain; respect `Retry-After` headers | Adaptive backoff: halve rate for 10 min |\
| Dynamic rendering (SPA) | `wait_until='networkidle'`, scroll triggers, MutationObserver | Intercept XHR/API calls directly |\
| Layout changes | LLM-based extraction (describe page, extract data) rather than rigid CSS selectors | Alert + manual selector fix |\
| Complete source failure | Strategy cascade exhaustion | Manual input fallback with user notification |\
\
### 11.3 Rate Limiter Configuration\
\
Redis-backed token bucket per platform/domain:\
\
```\
Platform/Domain     \uc0\u9474  Max RPM \u9474  Burst \u9474  On 429/Challenge\
\uc0\u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9532 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
SerpAPI             \uc0\u9474     30   \u9474   10   \u9474  Halve for 10 min\
RapidAPI (LinkedIn) \uc0\u9474     10   \u9474    3   \u9474  Halve for 10 min\
Apify (Naukri)      \uc0\u9474     20   \u9474    5   \u9474  Halve for 10 min\
Employer ATS pages  \uc0\u9474     15   \u9474    5   \u9474  Halve + rotate proxy\
```\
\
### 11.4 Scheduling Consideration\
\
For discovery runs that span multiple platforms, consider **daily batch scheduling** rather than pure on-demand real-time queries for platforms with strict rate limits. This reduces detection risk and smooths resource usage. The user triggers a campaign; the system completes it within a defined window (e.g., 1\'964 hours) rather than attempting everything in a 30-second burst.\
\
---\
\
## 12. Security, Privacy & Safety\
\
### 12.1 Data Protection\
\
```\
DATA AT REST\
  \'95 Resume PDFs: AES-256 encrypted in object store\
  \'95 Database: PostgreSQL TDE (Transparent Data Encryption)\
  \'95 PII fields (email, phone): Application-level encryption with per-user keys\
  \'95 Vector embeddings: Not reversible to source text (safe unencrypted)\
  \'95 Short-lived signed URLs for file access\
\
DATA IN TRANSIT\
  \'95 All internal service communication: mTLS\
  \'95 External API calls: TLS 1.3\
  \'95 WebSocket connections: WSS\
\
LLM DATA HANDLING\
  \'95 Resume text sent to LLM only for parsing & matching\
  \'95 LLM provider: ensure data is not used for training (Enterprise tier)\
  \'95 Option for local LLM (Ollama + Llama 3) for maximum privacy\
\
ACCESS CONTROL\
  \'95 User authentication: JWT tokens (Auth0 or Supabase Auth)\
  \'95 Each user accesses only their own campaigns, resumes, results\
  \'95 Tenant isolation enforced at the query level\
  \'95 Admin access: separate role, audit-logged\
\
DATA RETENTION\
  \'95 Resume PDFs: deleted after 90 days or on user request\
  \'95 Parsed profiles: retained while account active\
  \'95 Search results: retained for 30 days, then archived\
  \'95 User can trigger full data deletion (GDPR-style)\
\
API KEY MANAGEMENT\
  \'95 All API keys: HashiCorp Vault or K8s Secrets (encrypted)\
  \'95 Rotated every 90 days\
  \'95 Never logged, never in environment variables in plain text\
  \'95 Source credentials stored in secure vault with tool-token access\
    (never exposed in agent prompts)\
```\
\
### 12.2 Prompt Injection Defense\
\
All fetched JDs, career pages, and scraped content must be treated as **untrusted input**:\
\
- Sanitize HTML and strip scripts before LLM processing\
- Block tool-calling directives embedded in page text\
- Use structured extraction prompts that constrain LLM output to the expected schema\
- Never allow source content to alter policy, credentials, or system instructions\
- Log any detected injection attempts in audit logs\
\
### 12.3 Job Risk / Fraud Detection\
\
A `JobRiskDetector` component flags suspicious postings:\
\
| Risk Signal | Flag |\
|---|---|\
| Job requests money/fees | \uc0\u55357 \u56628  SCAM_LIKELY |\
| Requests sensitive docs early (identity, banking) | \uc0\u55357 \u56628  HIGH_RISK |\
| Off-platform chat pressure ("message me on Telegram") | \uc0\u55357 \u57313  SUSPICIOUS |\
| Suspicious/disposable domain for career page | \uc0\u55357 \u57313  SUSPICIOUS |\
| Generic email patterns (gmail/yahoo for "enterprise" company) | \uc0\u55357 \u57313  SUSPICIOUS |\
| Company cannot be verified in any public database | \uc0\u55357 \u57313  SUSPICIOUS |\
| Salary too good to be true for seniority level | \uc0\u55357 \u57313  SUSPICIOUS |\
\
Flagged jobs are routed to a human review approval task before appearing in the shortlist. This aligns with safety guidance from platforms like Naukri, which explicitly warn users about paying for jobs/interviews or sharing sensitive information early.\
\
### 12.4 Human Review Gates (Mandatory)\
\
- Source policy says "manual only" for a specific action\
- CAPTCHA / login wall / bot challenge detected\
- Person identity confidence is below threshold\
- Outreach is about to be sent\
- Job risk score is elevated\
- Agent reasoning quality check fails (QA Agent flags)\
\
---\
\
## 13. Technology Stack\
\
| Layer | Technology | Rationale |\
|---|---|---|\
| **Language** | Python 3.12+ | Ecosystem strength for ML/AI/scraping |\
| **Agent Framework** | Custom Agent Shell (inspired by CrewAI) | Structured contracts without framework lock-in |\
| **Workflow Engine** | **Temporal** | Crash-proof durable execution, approval waits, retries |\
| **LLM Provider** | Primary: OpenAI (GPT-4o, GPT-4o-mini); Fallback: Anthropic Claude Sonnet | |\
| **LLM Router** | LiteLLM | Unified API across providers |\
| **Embeddings** | OpenAI text-embedding-3-small (1536d) or local sentence-transformers | |\
| **Vector Store** | Qdrant (self-hosted or cloud) | |\
| **Primary Database** | PostgreSQL 16 with JSONB | |\
| **Cache / Rate Limiter** | Redis 7 | Session state, rate limiting, hot lookups |\
| **Web Scraping** | Playwright (async, Chromium) + httpx + BeautifulSoup4 | |\
| **PDF Processing** | PyMuPDF (fitz) + pdfplumber | |\
| **Proxy Service** | BrightData Residential Proxies (primary); SmartProxy (secondary) | |\
| **Third-Party APIs** | SerpAPI, RapidAPI, Apify | |\
| **API Framework** | FastAPI | Backend API for UI |\
| **Frontend** | Next.js 14 / React | Dashboard + review UI |\
| **Object Storage** | MinIO (self-hosted) or AWS S3 | Resume PDFs, reports |\
| **Secrets** | HashiCorp Vault / K8s Secrets | |\
| **Observability** | OpenTelemetry \uc0\u8594  Jaeger (traces); Prometheus + Grafana (metrics); Loki (logs) | |\
| **Data Validation** | Pydantic v2 | Enforces structured schemas between agents |\
| **Deployment** | Docker Compose (dev); Kubernetes (production) | |\
| **CI/CD** | GitHub Actions \uc0\u8594  Docker \u8594  K8s deploy | |\
\
---\
\
## 14. Deployment Architecture\
\
```\
\uc0\u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488 \
\uc0\u9474                     KUBERNETES CLUSTER                             \u9474 \
\uc0\u9474                                                                   \u9474 \
\uc0\u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488     \u9474 \
\uc0\u9474   \u9474   NAMESPACE: jobpilot                                     \u9474     \u9474 \
\uc0\u9474   \u9474                                                          \u9474     \u9474 \
\uc0\u9474   \u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474  api-server   \u9474   \u9474  web-frontend \u9474   \u9474  temporal-     \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474  (FastAPI)    \u9474   \u9474  (Next.js)    \u9474   \u9474  worker       \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474  Replicas: 2  \u9474   \u9474  Replicas: 2  \u9474   \u9474  (agent exec) \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474  CPU: 500m    \u9474   \u9474  CPU: 250m    \u9474   \u9474  Replicas: 4  \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474  RAM: 512Mi   \u9474   \u9474  RAM: 256Mi   \u9474   \u9474  CPU: 1000m   \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474               \u9474   \u9474               \u9474   \u9474  RAM: 2Gi     \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9474     \u9474 \
\uc0\u9474   \u9474                                                          \u9474     \u9474 \
\uc0\u9474   \u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474  playwright-  \u9474   \u9474  temporal-    \u9474   \u9474  alert-       \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474  pool         \u9474   \u9474  server       \u9474   \u9474  ingestion    \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474  (headless    \u9474   \u9474  + history    \u9474   \u9474  service      \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474   browsers)   \u9474   \u9474  Replicas: 1  \u9474   \u9474  Replicas: 1  \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474  Replicas: 3  \u9474   \u9474               \u9474   \u9474               \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474  CPU: 1000m   \u9474   \u9474               \u9474   \u9474               \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474  RAM: 2Gi     \u9474   \u9474               \u9474   \u9474               \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9474     \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496     \u9474 \
\uc0\u9474                                                                   \u9474 \
\uc0\u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488     \u9474 \
\uc0\u9474   \u9474   STATEFUL SERVICES                                       \u9474     \u9474 \
\uc0\u9474   \u9474                                                          \u9474     \u9474 \
\uc0\u9474   \u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474  PostgreSQL   \u9474   \u9474  Redis        \u9474   \u9474  Qdrant       \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474  (Primary DB  \u9474   \u9474  (Cache +     \u9474   \u9474  (Vector      \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474   + Temporal) \u9474   \u9474   Rate Limit) \u9474   \u9474   Store)      \u9474   \u9474     \u9474 \
\uc0\u9474   \u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496   \u9474     \u9474 \
\uc0\u9474   \u9474                                                          \u9474     \u9474 \
\uc0\u9474   \u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488                                        \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474  MinIO        \u9474                                        \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474  (Object Store\u9474                                        \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474   for PDFs)   \u9474                                        \u9474     \u9474 \
\uc0\u9474   \u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496                                        \u9474     \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496     \u9474 \
\uc0\u9474                                                                   \u9474 \
\uc0\u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488     \u9474 \
\uc0\u9474   \u9474   OBSERVABILITY                                           \u9474     \u9474 \
\uc0\u9474   \u9474   \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488  \u9484 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9488    \u9474     \u9474 \
\uc0\u9474   \u9474   \u9474 Jaeger  \u9474  \u9474 Prometheus\u9474  \u9474 Grafana\u9474  \u9474 Loki (logs)    \u9474    \u9474     \u9474 \
\uc0\u9474   \u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496  \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496    \u9474     \u9474 \
\uc0\u9474   \u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496     \u9474 \
\uc0\u9492 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9496 \
\
SEPARATE NODE POOLS:\
  \'95 General pool: API, frontend, Temporal workers\
  \'95 Browser pool: Playwright containers (isolated, seccomp-restricted)\
  \'95 Stateful pool: PostgreSQL, Redis, Qdrant, MinIO\
```\
\
---\
\
## 15. Observability, Testing & Quality Assurance\
\
### 15.1 Observability\
\
Instrument the entire stack with **OpenTelemetry** for standardized traces, metrics, and logs:\
\
**Key Metrics:**\
- Workflow latency (end-to-end campaign time)\
- Agent latency per agent type\
- Source success rate per platform per strategy\
- Parse completeness score\
- Deduplication rate\
- Match precision proxies (user acceptance rate)\
- Approval conversion rate\
- Outreach response rates (if tracked)\
- LLM token consumption and cost per campaign\
- CAPTCHA / challenge encounter rate\
- Error rates by service\
\
**Alerting:**\
- Source success rate drops below 70% for any platform\
- LLM API error rate exceeds 5%\
- Campaign completion time exceeds SLA\
- Anomalous cost spike per campaign\
\
### 15.2 Testing Strategy\
\
This is a critical area that requires deliberate investment:\
\
**Unit Tests:**\
- Scoring algorithm correctness: test each signal computation in isolation\
- Skill normalization and Tech Adjacency Graph lookups\
- Deduplication logic: hash-based and fuzzy match correctness\
- Resume parser: test against a corpus of diverse resume formats\
- Rate limiter behavior under load\
\
**Integration Tests:**\
- Per-platform adapter: use recorded HTTP responses (VCR/cassette pattern) to verify adapter behavior without hitting real APIs\
- End-to-end pipeline: feed a known resume + known set of jobs \uc0\u8594  verify scored output\
- Temporal workflow: verify DAG execution, retry behavior, approval gate pausing\
\
**Scraping Stability Tests:**\
- **Canary runs:** Weekly automated health checks against all platforms using the strategy cascade. Track success rate over time.\
- **Layout change detection:** Compare current page DOM structure against stored snapshots; alert when structure diverges beyond threshold.\
- **Selector regression:** Maintain a test suite of saved HTML pages from each platform; run extraction logic against them in CI to detect breakage before production.\
\
**Scoring Validation:**\
- Maintain a labeled ground-truth dataset: ~100 resume-JD pairs with human-assigned match tiers\
- Run scoring engine against this dataset in CI; alert if accuracy drops below threshold\
- Track precision/recall of each match tier against user accept/dismiss behavior over time\
\
**Agent Behavioral Testing:**\
- For each agent, maintain a set of "golden" input-output pairs\
- Verify that agent reasoning traces are internally consistent\
- Test that QA/Critic Agent correctly detects inserted hallucinations\
\
### 15.3 LLM Quality Monitoring\
\
- Track hallucination rate in production: compare LLM-extracted skills against literal text in resume/JD\
- Monitor scoring explanation quality: periodic human review of sampled reasoning traces\
- Detect reasoning quality degradation: if user override rate increases, trigger alert\
- A/B test LLM model changes against historical accuracy baselines\
\
---\
\
## 16. Extensibility & Plugin Architecture\
\
### 16.1 New Job Platforms\
\
To add a new platform (e.g., Glassdoor, AngelList):\
\
```python\
class GlassdoorAdapter(PlatformAdapter):\
    def _preferred_strategy_order(self):\
        return [\
            RetrievalStrategy.LICENSED_VENDOR,\
            RetrievalStrategy.ALERT_INGESTION,\
            RetrievalStrategy.EMPLOYER_ATS,\
            RetrievalStrategy.MANUAL_INPUT\
        ]\
    def _execute_strategy(self, strategy, params):\
        ...\
```\
\
Register in Source Capability Registry:\
```sql\
INSERT INTO source_policies (source_name, allowed_modes, ...)\
VALUES ('glassdoor', '["licensed_vendor","alerts","employer_ats","manual_input"]', ...);\
```\
\
The Manager Agent auto-discovers registered platforms and creates Scout tasks for each enabled one.\
\
### 16.2 New Agents\
\
Future agents that can be added following the same Agent Shell pattern:\
\
- **Cover Letter Agent:** Generate tailored cover letters per JD\
- **Interview Prep Agent:** Research company + role for prep questions\
- **Salary Research Agent:** Benchmark compensation data\
- **Application Tracker Agent:** Monitor application statuses over time\
- **Follow-Up Agent:** Schedule and draft follow-up messages\
- **Resume Tailor Agent:** Adjust resume emphasis per JD\
\
Register with the Manager's agent registry; no changes to core orchestration needed.\
\
### 16.3 Scoring Model Customization\
\
Users can adjust scoring weights via preferences. Advanced: plug in a custom scoring function or ML model that learns from user feedback (which jobs they applied to vs. skipped).\
\
---\
\
## 17. Cost Estimation & Optimization\
\
### Per-Search-Campaign Estimated Costs (50 jobs evaluated):\
\
| Component | Token/API Usage | Est. Cost |\
|---|---|---|\
| Resume Parsing (GPT-4o) | ~3K tokens | $0.02 |\
| Resume Embeddings | ~2K tokens | $0.001 |\
| Job Scouting (SerpAPI) | 8-12 API calls | $0.10-0.15 |\
| JD Parsing (GPT-4o-mini \'d7 50 jobs) | ~50K tokens | $0.15 |\
| Job Embeddings | ~25K tokens | $0.01 |\
| Preference Analysis (GPT-4o for reasoning) | ~20K tokens | $0.10 |\
| Company Research | ~10K tokens | $0.05 |\
| Outreach Finding + Drafting | ~15K tokens | $0.08 |\
| QA/Critic Agent | ~5K tokens | $0.03 |\
| Manager Agent overhead | ~5K tokens | $0.03 |\
| Proxy costs | ~50 requests | $0.10-0.25 |\
| **TOTAL PER CAMPAIGN** | **~135K tokens** | **~$0.70-0.90** |\
\
### Optimization Strategies\
\
- Use GPT-4o-mini for extraction tasks; GPT-4o only for reasoning/matching\
- Cache company profiles (don't re-research the same company across campaigns)\
- Cache job embeddings (same JD across campaigns \uc0\u8594  reuse embedding)\
- Batch embedding requests (50 texts in one API call)\
- Use local embedding model (sentence-transformers) to eliminate embedding API costs\
- Deduplicate early in the pipeline to reduce downstream LLM processing\
- Share computed results across users targeting the same company/role (with privacy boundaries)\
\
---\
\
## 18. Development Phases & Milestones\
\
### Phase 1: Core Matching MVP (Weeks 1-5)\
\
- [ ] Set up project structure, Docker Compose dev environment\
- [ ] Implement Agent Shell base class\
- [ ] Set up Temporal server and basic workflow\
- [ ] Implement Resume Parser Agent (PDF \uc0\u8594  structured profile)\
- [ ] Set up PostgreSQL schema + Qdrant + Redis\
- [ ] Implement manual link input as first discovery channel\
- [ ] Implement canonical job parsing and normalization\
- [ ] Implement deduplication engine\
- [ ] Build Preference Analyst Agent with multi-signal scoring\
- [ ] Build Tech Adjacency Graph (v1: manual dictionary)\
- [ ] Basic FastAPI endpoints: upload resume, start campaign, view results\
- [ ] Unit tests for scoring algorithm and skill normalization\
- [ ] Build Streamlit or basic React shortlist UI\
\
### Phase 2: Discovery Expansion (Weeks 6-9)\
\
- [ ] Implement Source Capability Registry and policy enforcement\
- [ ] Build PlatformAdapter base class\
- [ ] Build alert email ingestion service (Gmail/Outlook OAuth)\
- [ ] Build NaukriAdapter (SerpAPI + Apify strategies)\
- [ ] Build IndeedAdapter (partner API + SerpAPI)\
- [ ] Build LinkedInAdapter (RapidAPI + alerts + manual)\
- [ ] Build IIMJobsAdapter (SerpAPI + manual)\
- [ ] Implement canonical employer ATS URL resolution\
- [ ] Implement Research Agent (company enrichment)\
- [ ] Implement proxy pool + rate limiter\
- [ ] Integration tests: end-to-end discovery pipeline\
- [ ] Scoring validation against labeled ground-truth dataset\
\
### Phase 3: Networking & Outreach MVP (Weeks 10-12)\
\
- [ ] Implement Outreach Finder Agent\
- [ ] Contact prioritization logic (Recruiter \uc0\u8594  HM \u8594  Peer)\
- [ ] Message draft generation with personalization\
- [ ] Implement QA/Critic Agent\
- [ ] Implement Job Risk Detector\
- [ ] Build approval workflow (shortlist, contacts, drafts)\
- [ ] Build Feedback Learning Agent (logging; weight updates in Phase 4)\
- [ ] Email send via Gmail/Outlook after approval\
\
### Phase 4: Production Hardening (Weeks 13-16)\
\
- [ ] Build Next.js dashboard (campaign config, results, contacts, approvals)\
- [ ] WebSocket real-time progress updates\
- [ ] Report export (PDF, CSV)\
- [ ] Error handling UX (manual input fallback flows)\
- [ ] Security audit (encryption, access control, prompt injection)\
- [ ] Feedback learning: implement weight update logic\
- [ ] Observability setup (tracing, metrics, alerts, dashboards)\
- [ ] Browser worker pool: allowlisted employer ATS automation\
- [ ] Load testing (concurrent campaigns)\
- [ ] Anti-scraping resilience testing + canary runs\
- [ ] Kubernetes deployment manifests / Helm chart\
- [ ] CI/CD pipeline\
- [ ] Documentation (API docs, runbook)\
- [ ] Production deployment\
\
---\
\
## 19. Open Considerations & Known Blind Spots\
\
The following areas require further design work or explicit engineering decisions:\
\
### 19.1 LinkedIn People Search Authentication\
All contact discovery recommendations involve LinkedIn people search, but no clear compliant programmatic path exists for unapproved developers. **Current recommendation:** limit to Google Custom Search (`site:linkedin.com/in`), user-provided LinkedIn URLs, user-provided CSV exports, and recruiter names extracted from JD metadata. Evaluate LinkedIn Marketing or Sales Navigator APIs for partner access if budget allows.\
\
### 19.2 Stale / Expired Job Handling\
Jobs get filled, postings get taken down. The system should:\
- Track `posted_date` and apply a recency decay in scoring\
- Periodically re-check canonical employer ATS URLs for 404/closed status\
- Flag jobs older than 30 days as potentially stale\
- Allow users to report jobs as filled/expired to improve data quality\
\
### 19.3 Multi-Tenant Architecture\
For a multi-user deployment:\
- Enforce tenant isolation at the database query level (row-level security)\
- Separate Temporal task queues per tenant or by priority tier\
- Implement per-tenant cost controls and campaign rate limits\
- Share cached company profiles and skill taxonomy across tenants\
- Isolate resume/PII storage per tenant\
\
### 19.4 Internationalization\
The v1 architecture assumes India-focused search (INR salaries, Indian cities, English-language JDs). Expanding to other markets requires:\
- Multi-language resume parsing (Hindi, etc.)\
- Locale-specific skill taxonomy and title normalization\
- Additional platform adapters (e.g., Glassdoor, AngelList, Wellfound)\
- Currency normalization for salary comparison\
- Country-specific resume convention handling\
\
### 19.5 LLM Hallucination Monitoring in Production\
Beyond the QA/Critic Agent's per-run checks, invest in:\
- Tracking the rate at which users manually correct extracted profile fields\
- A/B testing LLM versions against scoring accuracy baselines\
- Sampling and human-reviewing a percentage of reasoning traces weekly\
- Alerting when user override rate increases significantly\
\
### 19.6 Signal Conflict Resolution\
When semantic similarity and hard skill overlap disagree, the current design caps the match tier. However, edge cases exist (e.g., a very senior architect matches semantically but their title doesn't align with the JD's title). Consider building a conflict resolution log that surfaces these cases to the user with explicit "here's why the signals disagree" explanations.\
\
### 19.7 Accessibility & Mobile Experience\
The dashboard should meet WCAG 2.1 AA standards. Consider a mobile-first design for the review/approval flows, as users may review job shortlists and approve outreach from their phone. Push notifications for campaign completion and approval requests would enhance the mobile experience.\
\
### 19.8 Key Build Decisions to Lock Early\
\
1. **Will LinkedIn support be manual/approved-only?** \uc0\u8594  Recommend yes, unless a real partner path is secured.\
2. **Will the product stop at draft generation or send emails too?** \uc0\u8594  Recommend send email only with explicit user approval; never auto-send LinkedIn messages.\
3. **Do you want employer ATS pages as primary apply targets?** \uc0\u8594  Recommend yes.\
4. **India-focused first, or global?** \uc0\u8594  Affects taxonomy, location normalization, and source selection.\
5. **Feedback learning from outcomes in v1 or v2?** \uc0\u8594  Start with logged feedback in v1; weight updates in Phase 4.\
6. **Self-hosted vs. managed Temporal?** \uc0\u8594  Temporal Cloud reduces ops burden but adds cost.\
\
---\
\
## 20. Appendix\
\
### A. Manager Agent System Prompt (Reference)\
\
```\
You are the Manager Agent for JobPilot, a job search orchestration system.\
\
YOUR RESPONSIBILITIES:\
1. Analyze the user's profile and search preferences\
2. Decompose the search into a task DAG\
3. Delegate tasks to specialized worker agents (as Temporal activities)\
4. Monitor execution and handle failures gracefully\
5. Wait on approval gates when required\
6. Aggregate results into a comprehensive, actionable report\
\
PLANNING RULES:\
- Always parse the resume FIRST before any scouting\
- Launch all scouts in PARALLEL (they are independent)\
- Company research can run in parallel with scouting\
- Preference analysis requires BOTH scout results AND research\
- QA/Critic Agent must verify extractions before scoring\
- Outreach finding only operates on the top N user-approved jobs\
- If a scout fails after retries, continue with others; never block the pipeline\
- If fewer than 3 strong matches, re-run analysis with relaxed thresholds\
- NEVER bypass source policy constraints\
\
COMMUNICATION:\
- Be concise in task descriptions\
- Include all necessary context in each task payload\
- Log every decision with reasoning for auditability\
\
Available agents: ResumeParser, JobScout, ResearchAgent, PreferenceAnalyst,\
OutreachFinder, QACritic, FeedbackLearner.\
\
Current user request: \{user_request_json\}\
Current execution state: \{execution_state_json\}\
\
What is your next action?\
```\
\
### B. Tech Adjacency Graph (Full Sample)\
\
```json\
\{\
  "equivalences": \{\
    "react": ["react.js", "reactjs"],\
    "vue": ["vue.js", "vuejs"],\
    "node": ["node.js", "nodejs"],\
    "postgres": ["postgresql", "psql"],\
    "k8s": ["kubernetes"],\
    "aws": ["amazon web services"],\
    "gcp": ["google cloud platform", "google cloud"],\
    "js": ["javascript"],\
    "ts": ["typescript"]\
  \},\
  "adjacencies": \{\
    "react":       \{"vue": 0.7, "angular": 0.6, "svelte": 0.5\},\
    "python":      \{"go": 0.5, "ruby": 0.4, "java": 0.3\},\
    "postgresql":  \{"mysql": 0.8, "mariadb": 0.85, "cockroachdb": 0.7\},\
    "kubernetes":  \{"docker": 0.8, "nomad": 0.6, "ecs": 0.5\},\
    "kafka":       \{"rabbitmq": 0.6, "pulsar": 0.7, "kinesis": 0.5\},\
    "fastapi":     \{"flask": 0.8, "django": 0.6, "express": 0.4\},\
    "terraform":   \{"pulumi": 0.8, "cloudformation": 0.6, "ansible": 0.4\},\
    "redis":       \{"memcached": 0.7, "dragonfly": 0.9\},\
    "aws":         \{"gcp": 0.7, "azure": 0.7\}\
  \}\
\}\
```\
\
### C. API Contract Suggestions\
\
```\
POST /campaigns\
  Create a search campaign.\
  Body: \{ resume_file_id, roles[], target_companies[], tech_stack[],\
          locations[], work_modes[], manual_job_links[] \}\
\
POST /campaigns/\{id\}/manual-links\
  Ingest pasted URLs or CSV.\
\
GET /campaigns/\{id\}/status\
  Campaign status + progress.\
\
GET /campaigns/\{id\}/jobs\
  Ranked job shortlist.\
\
GET /campaigns/\{id\}/contacts\
  Prioritized people by company/job.\
\
POST /approvals/\{id\}\
  Approve or reject draft, contact list, or campaign step.\
\
POST /feedback\
  Store user interaction outcomes.\
```\
\
### D. Project Folder Structure\
\
```\
jobpilot/\
\uc0\u9500 \u9472 \u9472  README.md\
\uc0\u9500 \u9472 \u9472  docker-compose.yml\
\uc0\u9500 \u9472 \u9472  pyproject.toml\
\uc0\u9500 \u9472 \u9472  alembic/                          # DB migrations\
\uc0\u9474    \u9492 \u9472 \u9472  versions/\
\uc0\u9500 \u9472 \u9472  src/\
\uc0\u9474    \u9500 \u9472 \u9472  __init__.py\
\uc0\u9474    \u9500 \u9472 \u9472  main.py                       # FastAPI app entry\
\uc0\u9474    \u9500 \u9472 \u9472  config/\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  settings.py               # Pydantic Settings\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  platforms.yaml            # Platform adapter configs\
\uc0\u9474    \u9474    \u9492 \u9472 \u9472  scoring_weights.yaml     # Default scoring weights\
\uc0\u9474    \u9500 \u9472 \u9472  api/\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  routes/\
\uc0\u9474    \u9474    \u9474    \u9500 \u9472 \u9472  campaigns.py\
\uc0\u9474    \u9474    \u9474    \u9500 \u9472 \u9472  resume.py\
\uc0\u9474    \u9474    \u9474    \u9500 \u9472 \u9472  results.py\
\uc0\u9474    \u9474    \u9474    \u9500 \u9472 \u9472  approvals.py\
\uc0\u9474    \u9474    \u9474    \u9492 \u9472 \u9472  feedback.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  schemas/                  # Pydantic request/response models\
\uc0\u9474    \u9474    \u9492 \u9472 \u9472  websocket.py\
\uc0\u9474    \u9500 \u9472 \u9472  agents/\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  base.py                   # AgentShell base class\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  manager.py               # ManagerAgent (Temporal Workflow)\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  resume_parser.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  job_scout.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  research.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  preference_analyst.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  outreach_finder.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  qa_critic.py\
\uc0\u9474    \u9474    \u9492 \u9472 \u9472  feedback_learner.py\
\uc0\u9474    \u9500 \u9472 \u9472  orchestration/\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  workflows.py              # Temporal Workflow definitions\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  activities.py             # Temporal Activity wrappers\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  dag.py                    # TaskDAG implementation\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  shared_context.py\
\uc0\u9474    \u9474    \u9492 \u9472 \u9472  planner.py\
\uc0\u9474    \u9500 \u9472 \u9472  platforms/\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  base_adapter.py           # PlatformAdapter ABC\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  source_policy.py          # Source Capability Registry\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  naukri.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  indeed.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  linkedin.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  iimjobs.py\
\uc0\u9474    \u9474    \u9492 \u9472 \u9472  alert_ingestion.py        # Email alert parser\
\uc0\u9474    \u9500 \u9472 \u9472  scraping/\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  proxy_pool.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  rate_limiter.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  session_manager.py\
\uc0\u9474    \u9474    \u9492 \u9472 \u9472  browser_pool.py\
\uc0\u9474    \u9500 \u9472 \u9472  scoring/\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  engine.py                 # Multi-signal scoring\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  skill_graph.py            # Tech Adjacency Graph\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  embeddings.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  normalizer.py\
\uc0\u9474    \u9474    \u9492 \u9472 \u9472  risk_detector.py          # Job fraud/scam detection\
\uc0\u9474    \u9500 \u9472 \u9472  tools/\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  pdf_extractor.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  web_search.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  linkedin_search.py\
\uc0\u9474    \u9474    \u9492 \u9472 \u9472  email_finder.py\
\uc0\u9474    \u9500 \u9472 \u9472  models/\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  database.py               # SQLAlchemy models\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  schemas.py                # Shared Pydantic models\
\uc0\u9474    \u9474    \u9492 \u9472 \u9472  enums.py\
\uc0\u9474    \u9500 \u9472 \u9472  services/\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  llm_gateway.py            # LiteLLM wrapper\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  vector_store.py           # Qdrant client\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  storage.py                # MinIO/S3 wrapper\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  notifications.py\
\uc0\u9474    \u9474    \u9492 \u9472 \u9472  approval_service.py\
\uc0\u9474    \u9492 \u9472 \u9472  utils/\
\uc0\u9474        \u9500 \u9472 \u9472  deduplication.py\
\uc0\u9474        \u9500 \u9472 \u9472  canonicalization.py\
\uc0\u9474        \u9500 \u9472 \u9472  hashing.py\
\uc0\u9474        \u9492 \u9472 \u9472  logging.py\
\uc0\u9500 \u9472 \u9472  tests/\
\uc0\u9474    \u9500 \u9472 \u9472  unit/\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  test_scoring_engine.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  test_skill_graph.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  test_deduplication.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  test_resume_parser.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  test_risk_detector.py\
\uc0\u9474    \u9474    \u9492 \u9472 \u9472  test_qa_critic.py\
\uc0\u9474    \u9500 \u9472 \u9472  integration/\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  test_naukri_adapter.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  test_end_to_end.py\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  test_temporal_workflow.py\
\uc0\u9474    \u9474    \u9492 \u9472 \u9472  test_alert_ingestion.py\
\uc0\u9474    \u9500 \u9472 \u9472  scoring_validation/\
\uc0\u9474    \u9474    \u9500 \u9472 \u9472  ground_truth_dataset.json\
\uc0\u9474    \u9474    \u9492 \u9472 \u9472  test_scoring_accuracy.py\
\uc0\u9474    \u9492 \u9472 \u9472  fixtures/\
\uc0\u9474        \u9500 \u9472 \u9472  sample_resume.pdf\
\uc0\u9474        \u9500 \u9472 \u9472  sample_jds.json\
\uc0\u9474        \u9500 \u9472 \u9472  saved_html/               # For adapter regression tests\
\uc0\u9474        \u9492 \u9472 \u9472  expected_matches.json\
\uc0\u9500 \u9472 \u9472  frontend/                         # Next.js app\
\uc0\u9474    \u9500 \u9472 \u9472  app/\
\uc0\u9474    \u9500 \u9472 \u9472  components/\
\uc0\u9474    \u9492 \u9472 \u9472  package.json\
\uc0\u9492 \u9472 \u9472  k8s/                              # Kubernetes manifests\
    \uc0\u9500 \u9472 \u9472  namespace.yaml\
    \uc0\u9500 \u9472 \u9472  deployments/\
    \uc0\u9500 \u9472 \u9472  services/\
    \uc0\u9500 \u9472 \u9472  configmaps/\
    \uc0\u9492 \u9472 \u9472  secrets/\
```\
\
---\
\
This document provides all the architectural decisions, data contracts, agent specifications, policy constraints, and implementation details necessary for an engineering team to begin building JobPilot. Each section is independently actionable\'97an engineer can pick up the Platform Adapter specification and start building the Naukri integration without needing decisions from the Scoring Engine team, and vice versa. The Manager Agent's DAG-based orchestration atop Temporal ensures that adding new agents or platforms requires no changes to the core execution infrastructure.}
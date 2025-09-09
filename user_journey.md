# Detailed User Journey and Interactions

This document outlines the process of curriculum generation, validation, and enrichment using a modular AI agent architecture.

---

## 1. Workflow Overview

1. **Educator Uploads Syllabus**  
   - Input can be a syllabus document, free‑form text, or voice input.

2. **Orchestration Agent (OA)**  
   - Parses the request.  
   - Routes it to the **Curriculum Validator Agent (CV)**.

3. **Curriculum Validator Agent (CV)**  
   - Uses GenAI to validate the curriculum.  
   - Identifies missing or incomplete elements (e.g., *Ethics* in Week 3, *RAG Fundamentals* in Week 6).  
   - Produces a **Curriculum Gap Matrix**.

4. **QC (Quick Curriculum Approval)**  
   - Educator reviews and approves the validated curriculum via an online interface.

5. **Quiz Creator Agent (QC)**  
   - Generates quizzes for new or updated topics.  
   - Adjusts question style (e.g., fewer math-heavy questions).

6. **Feedback Evaluator Agent (FA)**  
   - Rebalances quiz difficulty based on educator feedback.  
   - Flags modules needing attention (e.g., Ethics, RAG).

7. **Content Enricher Agent (CE)**  
   - Suggests enrichment materials:  
     - 2 case studies  
     - 1 hands‑on lab for Ethics and RAG modules.

8. **Memory Agent (MA)**  
   - Stores educator preferences, past feedback, and curriculum gaps.  
   - Optimizes workflow for future semesters.

---

## 2. Outputs

- **Curriculum Gap Matrix** (Excel/CSV)  
- **PDF Blocks** (finalized curriculum content)  
- **CSV Quiz Banks**  
- **HTML Expandable Modules** (enrichment content)

---

## 3. Agent Roles Summary

| Agent | Primary Function | Inputs | Outputs |
|-------|------------------|--------|---------|
| **Orchestration Agent (OA)** | Coordinates workflow across all agents, ensures sequence and integration. | Educator’s input (syllabus, free‑form text, or voice) | Routed tasks to agents; combined final outputs. |
| **Curriculum Validator Agent (CV)** | Validates curriculum, identifies gaps/overlaps/missing AI concepts. | Curriculum documents, syllabus, or uploaded text | Curriculum gap matrix (Excel/CSV). |
| **Quiz Creator Agent (QC)** | Designs quizzes aligned with curriculum and objectives. | Validated curriculum, educator preferences | Quizzes (PowerPoint slide blocks or interactive modules). |
| **Content Enricher Agent (CE)** | Suggests additional reading, case studies, and enrichment resources. | Curriculum content, reference databases | Expandable modules with resources and activities. |
| **Feedback Evaluator Agent (FA)** | Refines quizzes/content based on feedback and engagement. | Educator review, learner engagement signals | Iterative improvements to quizzes and enrichment. |
| **Memory Agent (MA)** | Stores past inputs, preferences, and usage for personalization. | Historical interactions, prior reviews | Personalized suggestions, continuity across reviews. |

---

## 4. Process Flow (High-Level)

Educator Upload → OA → CV → Curriculum Gap Matrix → QC Approval → Quiz Creator → FA → CE → Final Outputs


---

## 5. Key Notes

- **Feedback Loop:** FA ensures continuous improvement of quizzes and content.  
- **Personalization:** MA ensures educator-specific preferences are remembered for future iterations.  
- **Integration:** OA ensures all agents work in sequence without manual intervention.
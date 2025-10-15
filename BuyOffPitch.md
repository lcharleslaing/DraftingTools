# Engineering Drafting Dashboard

### Unified Tool for Project, Configuration, and Print Package Management

## Overview

The **Engineering Drafting Dashboard** is designed to simplify and unify our entire drafting and design documentation workflow.
It brings together **project tracking**, **product configuration**, and **print-package management** into a single, easy-to-use desktop app built for real-world production environments.

This tool helps our team **save time**, **reduce errors**, and **stay consistent** across every job—from the first redline to final release.

---

## Core Purpose

Our drafting and design process currently touches multiple systems, folders, and manual checklists.
The goal of this app is to bring those scattered steps into **one organized workspace** that:

* Tracks every job and its workflow stages.
* Centralizes heater, tank, and pump configuration data.
* Manages print packages and drawing sets.
* Automates documentation, review, and release workflows.
* Provides a direct bridge to D365 and Inventor systems.
* Ensures the entire team operates from the same live data.

---

## Key Features

### 🔹 1. Dashboard

* A **central home screen** showing live job counts, active configurations, and print packages.
* One-click access to Projects, Product Configurations, and Print Packages.
* Clean visual layout, responsive for large displays.
* Quick view of which tasks are in progress and who’s assigned.

### 🔹 2. Project Manager

* Tracks every job from **initial redline** to **release to Dee**.
* Shows completion dates, due dates, and designer/engineer assignments.
* Automatic duration calculations and progress tracking.
* Built-in shortcuts to open job folders, customer directories, and key documents.
* Ensures no job gets lost in email threads or shared drives.

### 🔹 3. Product Configurations

* Stores configuration details for heaters, tanks, and pumps.
* Dropdowns and data fields for all key specs — parameters, fittings, drawing numbers.
* Autosaves changes immediately so data isn’t lost.
* Links configurations directly to project numbers for full traceability.
* Prepares configuration data for **Inventor integration** (see enhancement below).

### 🔹 4. Print Package Management

* Searches and organizes drawings by job.
* Allows batch printing, PDF conversion, and printer selection.
* Imports/exports full print-package sets for re-use.
* Detects paper sizes and selects the correct printer automatically.
* Greatly reduces time spent assembling and printing drawing sets.

### 🔹 5. Admin Controls (App Order Manager)

* Controls which modules appear on the dashboard and in what order.
* Exports/imports setup in JSON format for quick backup or sharing.
* Automatically performs data backups on exit.

---

## Benefits for the Team

| Area                 | Before                                    | After                                     |
| -------------------- | ----------------------------------------- | ----------------------------------------- |
| **Project Tracking** | Excel sheets, folders, and manual updates | Centralized interface with live status    |
| **Redline Workflow** | Hard to tell who has what and what’s done | Clear progress tracking per stage         |
| **Data Entry**       | Repetitive typing and version mismatches  | Unified forms, shared database            |
| **Print Packages**   | Manual file hunting and printing          | Auto-assembled sets with printer profiles |
| **Backup/Recovery**  | Risk of lost data                         | Automatic backups and JSON exports        |

---

## Benefits for Management

* **Visibility:** See project status, workload distribution, and bottlenecks at a glance.
* **Accountability:** Each job and stage is timestamped and assigned.
* **Efficiency:** Saves hours per job in coordination and document prep.
* **Standardization:** Everyone works from the same data, forms, and naming rules.
* **Scalability:** Future-ready for cloud sync, reporting, and role-based access.

---

## New Enhancements (Phase 2+)

### 🔸 1. D365 Bill of Material Interface

* A dedicated **BOM interface** directly aligned with the D365 upload process.
* Engineers and drafters can review, edit, and validate BOM data before submission.
* The app will:

  * Pull live part and assembly data from our shared database.
  * Allow grouping, quantity edits, and unit conversions.
  * Automatically format and export BOM files to match D365 import templates.
  * Track upload history by project for audit and traceability.
* **Goal:** Eliminate manual Excel-based uploads, reduce entry errors, and speed up the “BOM Entry” workflow stage.

### 🔸 2. Inventor Integration for Heater, Tank, and Pump Configurations

* Each configuration form (Heater/Tank/Pump) will tie directly into **Autodesk Inventor** using iLogic automation.
* The app will:

  * Pass configuration parameters into Inventor templates.
  * Automatically generate new models or drawings based on selected specs.
  * Save versions and maintain a version history (with user, date, and configuration snapshot).
  * Sync configuration data back into the database for future reuse or comparison.
* **Goal:** Provide a true **Configure-to-Design** workflow — where engineering rules and CAD outputs are managed from one interface.

---

## Technical Summary (Plain English)

* Desktop app built using **modern web technology (Next.js + Electron)**.
* Runs entirely on Windows PCs with **no internet requirement**.
* Uses a **local database (SQLite)** for reliability and speed.
* Automatically creates **backups and JSON exports** for recovery.
* Fully compatible with future integration to:

  * Microsoft **D365** (via file or API).
  * Autodesk **Inventor** (via iLogic or COM automation).

---

## Phase-Based Rollout Plan

### **Phase 1 – Core Platform & Daily Use Tools**

**Goal:** Deliver immediate efficiency for drafting and engineering teams.

* Deploy Dashboard, Project Manager, Product Configurations, Print Package Manager, and Admin Controls.
* All data stored in a single SQLite database with auto-backup.
* Standardize job tracking and print-package workflows.
* Result: Fully functional internal tool that centralizes operations and replaces scattered spreadsheets.

**Timeline:** ~8–10 weeks
**Outcome:** Visible daily productivity boost; immediate time savings and consistency.

---

### **Phase 2 – D365 Bill of Material Integration**

**Goal:** Streamline and validate all BOM uploads from engineering and drafting.

* Add the D365 BOM interface to the Dashboard.
* Create direct export to D365 import templates (matching current Excel formats).
* Add revision tracking, validation checks, and upload logs.
* Result: Accurate, audit-ready BOM entries with reduced manual effort.

**Timeline:** ~6–8 weeks after Phase 1
**Outcome:** Seamless D365 integration; eliminates rework and data-entry risk.

---

### **Phase 3 – Inventor iLogic Integration**

**Goal:** Bridge configuration data directly with Autodesk Inventor models.

* Connect heater, tank, and pump configuration modules to Inventor via iLogic.
* Automate model generation based on database-driven specs.
* Add version control and design history to configuration records.
* Enable engineers to instantly open or regenerate models from within the Dashboard.
* Result: Fully unified design environment — “Configure once, design automatically.”

**Timeline:** ~8–10 weeks after Phase 2
**Outcome:** Dramatic reduction in manual CAD work and configuration errors; sets foundation for digital-twin workflows.

---

## Future Expansion Possibilities

* **Automated report exports** (CSV/PDF summaries of projects and BOMs).
* **Centralized printer profiles** per user/site.
* **Cloud sync and team collaboration** between engineering and drafting workstations.
* **Performance dashboards** showing job throughput and workload analytics.
* **Authentication and role-based permissions** for engineering, drafting, and admin roles.

---

## Summary

The **Engineering Drafting Dashboard** is more than a productivity tool — it’s the next step toward a **fully integrated engineering ecosystem**.

By unifying D365 and Inventor processes into the same workspace, this project will dramatically reduce duplicate work, increase accuracy, and provide management with complete visibility into every job and configuration.

It sets a foundation for automation, traceability, and smart manufacturing — built on the real workflows our team uses every day.
## **MedVision Frontend Design Specification** 

## **Version 1.0 (MVP)** 

## **AI-Powered Clinical Decision Support System (CDSS)** 

## **Document Information** 

|Item|Details|
|---|---|
|Product|MedVision|
|Version|1.0 (MVP)|
|Document Type|Frontend Design & Workfow Specifcation|
|Audience|Product Designers, UI/UX Designers, Frontend Engineers, Clinical Stakeholders|
|Prepared By|Senior Product Design Team|
|Last Updated|June 2026|



## **1. Product Vision** 

## **What is MedVision?** 

MedVision is an AI-powered Clinical Decision Support System (CDSS) designed to assist healthcare professionals in synthesizing complex patient data into evidence-backed clinical insights. 

The platform ingests multiple modalities of patient information—including laboratory reports, radiology images, and clinical notes—and transforms them into explainable intelligence that supports physician decision-making. 

MedVision does not replace clinicians. 

It enhances clinical efficiency by reducing cognitive burden and surfacing relevant findings with supporting evidence. 

## **2. Design Philosophy** 

## **Core Principle** 

The interface should mirror how physicians naturally work. 

1 

## The product must **not resemble a business analytics dashboard.** 

Instead, it should follow the clinical reasoning journey. 

## **Physician Workflow** 

```
Patient Data Collection
        ↓
AI Processing
        ↓
Clinical Summary Review
        ↓
Evidence Verification
        ↓
Image Validation
        ↓
Clinical Decision
```

## **3. Design Goals** 

The interface should optimize for: 

## **Speed** 

Allow physicians to understand a case within seconds. 

## **Trust** 

Every AI finding must provide supporting evidence. 

## **Explainability** 

Users should understand why conclusions were generated. 

## **Minimal Cognitive Load** 

Present only relevant information. 

## **Safety** 

Support—not replace—clinical judgment. 

2 

## **4. User Roles** 

## **4.1 Physician** 

Primary user. 

Responsibilities: 

- Upload patient cases 

- Review AI-generated findings 

- Verify supporting evidence 

- Examine imaging outputs 

- Make final clinical decisions 

## **4.2 Radiologist** 

Responsibilities: 

- Review imaging interpretations 

- Validate Grad-CAM outputs 

- Compare AI predictions against visual findings 

## **4.3 Administrator** 

Responsibilities: 

- Monitor platform usage 

- Manage user access 

- Audit system activity 

## **5. Information Architecture** 

```
Login
 │
 ▼
Dashboard
 │
 ├── Upload New Case
 │
 ├── Search Patient
 │
 └── Recent Cases
          │
```

3 

```
          ▼
    Patient Case Page
          │
          ├── AI Summary
          ├── Evidence
          └── Imaging
```

## **6. Authentication Experience** 

## **Objective** 

Provide a fast and secure entry point. 

## **Components** 

## **Login Form** 

Fields: 

- Email Address 

- Password 

Actions: 

- Sign In 

- Forgot Password 

Optional: 

- Single Sign-On (Hospital Integration) 

## **Post Login** 

Users are redirected to: 

```
Dashboard
```

based on their role permissions. 

4 

## **7. Dashboard** 

## **Purpose** 

Provide a concise overview of current activity without overwhelming users. 

## **Dashboard Layout** 

```
-------------------------------------------------
Top Navigation
-------------------------------------------------
Statistics Cards
Recent Cases
Quick Actions
-------------------------------------------------
```

## **7.1 Statistics Cards** 

Display high-level operational metrics. 

## **Card 1** 

Total Patients 

Example: 

**==> picture [440 x 34] intentionally omitted <==**

**----- Start of picture text -----**<br>
1,248<br>**----- End of picture text -----**<br>


## **Card 2** 

Cases Processed Today 

Example: 

**==> picture [440 x 34] intentionally omitted <==**

**----- Start of picture text -----**<br>
36<br>**----- End of picture text -----**<br>


5 

## **Card 3** 

Pending Reviews 

Example: 

```
12
```

## **Card 4** 

Critical Alerts 

Example: 

```
5
```

## **Design Guidelines** 

- Minimal visual noise 

- Soft shadows 

- Large typography 

- High contrast 

- Avoid decorative charts 

## **7.2 Recent Cases** 

Purpose: 

Allow rapid access to ongoing patient reviews. 

## **Table Structure** 

|Patient|Status|Risk|
|---|---|---|
|Ravi Patel|Completed|Moderate|
|Priya Shah|Review Pending|High|
|Amit Joshi|Completed|Low|



6 

## **Risk Indicators** 

## **Critical** 

Red 

## **Moderate** 

Amber 

## **Low** 

Green 

## **7.3 Quick Actions** 

Primary CTA section. 

Actions: 

- Upload New Case 

- Search Patient 

- View Recent Cases 

## **8. Upload Case Experience** 

## **Purpose** 

Collect all patient-related information into a unified workflow. 

## **Workflow** 

```
Upload Files
```

```
      ↓
AI Processing
```

```
      ↓
OCR
      ↓
Medical NLP
      ↓
Imaging Analysis
      ↓
```

```
Multimodal Correlation
```

7 

```
      ↓
Clinical Summary Generation
      ↓
Case Ready
```

## **Upload Screen Layout** 

```
Patient Details
Upload Reports
Upload Imaging
Processing Status
Submit
```

## **8.1 Patient Information** 

Fields: 

- Patient Name 

- Patient ID 

- Age 

- Gender 

Optional: 

- Clinical Notes 

## **8.2 Report Upload** 

Supported Formats: 

## **Documents** 

- PDF 

- PNG 

- JPEG 

Capabilities: 

- Drag-and-drop upload 

8 

- Multiple file upload 

- Preview uploaded files 

## **8.3 Imaging Upload** 

Supported Formats 

## **Chest Imaging** 

- DICOM • JPEG • PNG 

Capabilities 

- Drag-and-drop upload • Thumbnail preview 

- File validation 

## **8.4 AI Processing Status** 

Purpose 

Build confidence during processing. 

## **Live Progress States** 

✓ `OCR Complete` 

- ✓ `Biomarker Extraction Complete` 

- ✓ `Medical NLP Complete` 

- ✓ `Imaging Analysis Complete` 

- ✓ `Multimodal Correlation Complete` 

✓ `Clinical Summary Generated` 

## **Design Guidelines** 

- Animated progress timeline 

9 

- Avoid spinners without context 

- Always communicate current step 

## **9. Patient Case Page** 

## **Purpose** 

This is the core experience of MedVision. 

All clinical intelligence for one patient is centralized here. 

## **Layout Structure** 

```
Patient Header
```

```
Tabs
 ├── AI Summary
 ├── Evidence
 └── Imaging
Tab Content
```

## **10. Patient Header** 

Purpose: 

Provide essential patient context. 

## **Display Information** 

Patient Name 

Patient ID 

Age 

Gender 

Last Updated 

10 

Risk Level 

## **Example** 

```
Patient: Ravi Patel
ID: P-10234
Age: 54
Gender: Male
Risk: Moderate
Last Updated:
08 June 2026
```

## **Risk Badge Styling** 

## **Critical** 

Filled Red 

## **Moderate** 

Filled Amber 

## **Low** 

Filled Green 

## **11. Tab 1 — AI Clinical Summary** 

## **Purpose** 

Deliver the final synthesized interpretation. 

This is the first tab physicians encounter. 

11 

## **Layout** 

```
Key Findings
```

```
Confidence Scores
Risk Factors
Recommendations
```

## **11.1 Findings** 

Example: 

```
Possible Pneumonia
```

## **11.2 Confidence** 

Example: 

```
92%
```

Displayed as: 

- Circular indicator 

- Confidence badge 

## **11.3 Risk Factors** 

Examples: 

- Elevated WBC 

- Persistent Cough 

- Right Lung Opacity 

12 

## **11.4 Recommendations** 

Examples: 

```
Further clinical evaluation advised.
```

```
Recommend correlation with
patient symptoms and
additional diagnostics.
```

## **Design Objectives** 

Physicians should understand: 

- What was found 

- How certain the system is 

- What factors contributed 

- Suggested next actions 

within 10–15 seconds. 

## **12. Tab 2 — Evidence Panel** 

## **Purpose** 

Enable explainability. 

Answer the question: 

Why did the AI conclude this? 

## **Evidence Layout** 

```
Finding
    ↓
Evidence Sources
    ↓
Source References
```

13 

## **Example** 

## **Finding** 

Possible Pneumonia 

## **Supporting Evidence** 

Chest X-ray 

```
Right lower lung opacity
```

Blood Report 

```
Elevated WBC
```

Clinical Notes 

```
Persistent cough
```

## **Source References** 

- Blood_Report.pdf 

- Chest_Xray.jpg 

- Clinical_Notes.txt 

## **Design Principles** 

Every AI insight must be traceable. 

No black-box conclusions. 

Transparency builds trust. 

## **13. Tab 3 — Imaging Viewer** 

## **Purpose** 

Enable visual validation of AI findings. 

14 

## **Layout** 

```
Image Viewer
Heatmap Controls
Predictions Panel
```

## **13.1 Original Image Viewer** 

Capabilities: 

- View uploaded image 

- DICOM support 

- High-resolution rendering 

## **13.2 Navigation Tools** 

Features: 

- Zoom 

- Pan 

- Reset View 

## **13.3 Heatmap Overlay** 

Purpose 

Display Grad-CAM visual explanations. 

Controls: 

- Toggle Overlay 

- Adjust Transparency 

## **13.4 Disease Predictions** 

Example 

15 

|Disease|Probability|
|---|---|
|Pneumonia|92%|
|Pleural Efusion|18%|
|Cardiomegaly|10%|



## **Design Objectives** 

Allow clinicians to verify: 

- Image quality • AI attention regions • Prediction confidence 

before accepting conclusions. 

## **14. Patient Search** 

## **Purpose** 

Rapid retrieval of patient records. 

## **Search Criteria** 

Users can search using: 

- Patient ID • Patient Name 

## **Search Results** 

Display: 

- Patient Name • Age • Last Visit • Risk Status 

16 

## **Design Guidelines** 

- Instant search feedback 

- Keyboard accessible 

- Highlight matched results 

## **15. Report Viewer** 

## **Purpose** 

Allow physicians to inspect original reports. 

## **Features** 

PDF Preview 

OCR Extracted Text 

Biomarker Extraction 

## **Example** 

## **Hemoglobin** 

```
10.8 g/dL
```

Status: 

```
Low
```

## **Biomarker Display Pattern** 

```
Biomarker
```

```
Value
Reference Status
```

17 

## **16. Alerts System** 

## **Purpose** 

Surface clinically important findings. 

## **Alert Categories** 

## **Critical** 

Examples: 

- High Pneumonia Risk 

- Severe Biomarker Deviations 

Color: 

Red 

## **Moderate** 

Examples: 

- Elevated WBC 

Color: 

Orange 

## **Normal** 

Examples: 

- No concerning findings 

Color: 

Green 

18 

## **Alert Principles** 

Alerts should: 

- Be actionable 

- Avoid alarm fatigue 

- Prioritize severity 

## **17. Visual Design Guidelines** 

## **Design Language** 

Clinical 

Calm 

Professional 

Human-centered 

## **Recommended Palette** 

Primary: 

Deep Medical Blue 

Secondary: 

Slate Gray 

Success: 

Green 

Warning: 

Amber 

Critical: 

Red 

Background: 

19 

Soft White 

## **Typography** 

Primary: 

Inter 

Fallback: 

System Sans 

## **Principles** 

- Large readable text 

- Adequate spacing 

- Strong hierarchy 

- Minimal decoration 

## **18. Accessibility Requirements** 

The system shall comply with: 

WCAG 2.1 AA standards. 

Requirements: 

- Keyboard navigation 

- Screen reader compatibility 

- High contrast support 

- Focus indicators 

- Scalable typography 

## **19. MVP Scope (Version 1.0)** 

Included Features: 

## **Dashboard** 

- Statistics 

- Recent Cases 

20 

• Quick Actions 

## **Upload Case Page** 

- Report Upload 

- Imaging Upload 

- AI Processing Status 

## **Patient Case Page** 

**AI Summary** 

**Evidence Panel** 

**Imaging Viewer** 

## **20. MedVision Intelligence Pipeline** 

The MVP should visually demonstrate the complete AI workflow. 

```
OCR
 ↓
Medical NLP
 ↓
Imaging AI
 ↓
Multimodal Correlation
 ↓
RAG Retrieval
 ↓
Gemini Clinical Reasoning
 ↓
Explainable Clinical Intelligence
```

## **21. Success Metrics** 

The design should enable physicians to: 

- Review a case in under 2 minutes. 

- Understand AI conclusions within 15 seconds. 

- Verify evidence without switching contexts. 

- Access imaging explanations seamlessly. 

21 

- Maintain trust through explainability. 

## **22. Future Enhancements (Post-MVP)** 

Potential Version 2.0 features: 

- Longitudinal Timeline 

- Physician Feedback Loop 

- Collaborative Review 

- Multi-specialty Workflows 

- EHR Integration 

- Voice Dictation 

- Audit Trails 

- Mobile Companion Experience 

- Personalized Clinical Recommendations 

## **Closing Statement** 

MedVision is designed to augment clinical expertise through transparent, explainable, and multimodal AI. 

The user experience should always reinforce one principle: 

## **"AI provides intelligence. Physicians provide judgment."** 

22 


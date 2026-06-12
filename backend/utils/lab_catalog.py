"""Standard adult blood panel catalog — reference ranges, aliases, precautions."""

from __future__ import annotations

from typing import Any

# Clinical reference intervals (adult, approximate — correlate with local lab ranges).
LAB_CATALOG: dict[str, dict[str, Any]] = {
    # --- Complete Blood Count (CBC) ---
    "Hemoglobin": {
        "category": "CBC",
        "low": 12.0,
        "high": 16.0,
        "unit": "g/dL",
        "aliases": ["hemoglobin", "hgb", "hb", "haemoglobin"],
        "precautions": {
            "LOW": "Possible anemia. Eat iron-rich foods (leafy greens, legumes, lean meat). Avoid strenuous exertion until reviewed. Physician may order iron/B12 studies.",
            "HIGH": "Possible dehydration or polycythemia. Maintain hydration; avoid smoking. Repeat test and seek physician review.",
        },
    },
    "RBC": {
        "category": "CBC",
        "low": 4.2,
        "high": 5.8,
        "unit": "10^6/uL",
        "aliases": ["rbc", "red blood cell", "red blood cells", "erythrocyte"],
        "precautions": {
            "LOW": "Low red cell count — correlate with hemoglobin. Rest, nutrition support, physician follow-up for anemia workup.",
            "HIGH": "Elevated RBC — review hydration, oxygen exposure, and medications with your physician.",
        },
    },
    "WBC": {
        "category": "CBC",
        "low": 4.5,
        "high": 11.0,
        "unit": "10^3/uL",
        "aliases": ["wbc", "white blood cell", "leukocyte", "total leucocyte"],
        "precautions": {
            "LOW": "Low immunity risk (leukopenia). Avoid sick contacts, practice hand hygiene, report fever immediately to a doctor.",
            "HIGH": "May indicate infection, inflammation, or stress. Monitor fever; seek care if worsening. Do not self-medicate antibiotics.",
        },
    },
    "Platelets": {
        "category": "CBC",
        "low": 150.0,
        "high": 400.0,
        "unit": "10^3/uL",
        "aliases": ["platelet", "platelets", "plt", "thrombocyte"],
        "precautions": {
            "LOW": "Bleeding risk if severely low. Avoid NSAIDs/aspirin unless prescribed. Report bruising, gum bleeding, or petechiae urgently.",
            "HIGH": "Elevated platelets — reduce smoking/alcohol; physician may evaluate for inflammation or clotting risk.",
        },
    },
    "Hematocrit": {
        "category": "CBC",
        "low": 36.0,
        "high": 46.0,
        "unit": "%",
        "aliases": ["hematocrit", "hct", "pcv", "packed cell volume"],
        "precautions": {
            "LOW": "Supports anemia evaluation. Increase fluids and iron intake as guided; follow up with CBC.",
            "HIGH": "May reflect dehydration or polycythemia. Hydrate well and repeat test.",
        },
    },
    "MCV": {
        "category": "CBC",
        "low": 80.0,
        "high": 100.0,
        "unit": "fL",
        "aliases": ["mcv", "mean corpuscular volume"],
        "precautions": {
            "LOW": "Microcytic pattern — often iron deficiency. Iron-rich diet; physician may check ferritin.",
            "HIGH": "Macrocytic pattern — B12/folate deficiency possible. Balanced diet; avoid excess alcohol.",
        },
    },
    "MCH": {
        "category": "CBC",
        "low": 27.0,
        "high": 33.0,
        "unit": "pg",
        "aliases": ["mch", "mean corpuscular hemoglobin"],
        "precautions": {
            "LOW": "Often seen with iron deficiency. Nutritional review recommended.",
            "HIGH": "May accompany macrocytic anemias. Physician correlation advised.",
        },
    },
    "MCHC": {
        "category": "CBC",
        "low": 32.0,
        "high": 36.0,
        "unit": "g/dL",
        "aliases": ["mchc"],
        "precautions": {
            "LOW": "May indicate hypochromic red cells. Iron studies may be warranted.",
            "HIGH": "Uncommon; repeat test and physician review.",
        },
    },
    "RDW": {
        "category": "CBC",
        "low": 11.5,
        "high": 14.5,
        "unit": "%",
        "aliases": ["rdw", "red cell distribution width"],
        "precautions": {
            "LOW": "Usually not clinically significant alone.",
            "HIGH": "Suggests mixed or early nutritional anemias. Further CBC and iron/B12 workup may help.",
        },
    },
    "Neutrophils": {
        "category": "Differential",
        "low": 40.0,
        "high": 70.0,
        "unit": "%",
        "aliases": ["neutrophil", "neutrophils", "polymorphs", "neut"],
        "precautions": {
            "LOW": "Increased infection risk. Avoid crowds when ill; seek care for fever.",
            "HIGH": "Often bacterial infection or stress. Monitor symptoms; medical review if persistent.",
        },
    },
    "Lymphocytes": {
        "category": "Differential",
        "low": 20.0,
        "high": 40.0,
        "unit": "%",
        "aliases": ["lymphocyte", "lymphocytes", "lymph"],
        "precautions": {
            "LOW": "May follow steroids or acute infection. Support rest and immunity.",
            "HIGH": "May follow viral illness. Rest, fluids; physician review if prolonged.",
        },
    },
    # --- Metabolic / Renal ---
    "Glucose": {
        "category": "Metabolic",
        "low": 70.0,
        "high": 100.0,
        "unit": "mg/dL",
        "aliases": ["glucose", "fasting glucose", "blood sugar", "fbs", "fasting blood sugar", "rbs"],
        "precautions": {
            "LOW": "Hypoglycemia risk. Take fast-acting sugar if symptomatic; eat regular meals; do not skip breakfast.",
            "HIGH": "Hyperglycemia risk. Reduce refined sugar, exercise regularly, consider HbA1c; physician diabetes screening.",
        },
    },
    "HbA1c": {
        "category": "Metabolic",
        "low": 4.0,
        "high": 5.6,
        "unit": "%",
        "aliases": ["hba1c", "hb a1c", "glycated hemoglobin", "a1c"],
        "precautions": {
            "LOW": "Uncommon; avoid hypoglycemia if on diabetes meds.",
            "HIGH": "Indicates poor long-term glucose control. Low-glycemic diet, daily activity, diabetes care plan with physician.",
        },
    },
    "Urea": {
        "category": "Renal",
        "low": 15.0,
        "high": 40.0,
        "unit": "mg/dL",
        "aliases": ["urea", "blood urea", "bun"],
        "precautions": {
            "LOW": "Often nutritional/liver related. Balanced protein intake.",
            "HIGH": "Kidney strain or dehydration possible. Hydrate; limit high-protein load; renal function review.",
        },
    },
    "Creatinine": {
        "category": "Renal",
        "low": 0.7,
        "high": 1.3,
        "unit": "mg/dL",
        "aliases": ["creatinine", "serum creatinine", "s creatinine"],
        "precautions": {
            "LOW": "Usually benign; low muscle mass can lower values.",
            "HIGH": "Kidney function concern. Hydrate, avoid nephrotoxic drugs/NSAIDs; urgent review if rising.",
        },
    },
    "Uric Acid": {
        "category": "Metabolic",
        "low": 3.5,
        "high": 7.2,
        "unit": "mg/dL",
        "aliases": ["uric acid", "urate"],
        "precautions": {
            "LOW": "Rarely clinically significant.",
            "HIGH": "Gout/kidney stone risk. Limit red meat, alcohol, fructose drinks; stay hydrated.",
        },
    },
    "Sodium": {
        "category": "Electrolytes",
        "low": 136.0,
        "high": 145.0,
        "unit": "mEq/L",
        "aliases": ["sodium", "na", "serum sodium"],
        "precautions": {
            "LOW": "Hyponatremia risk. Avoid excess water; seek care if confusion or seizures.",
            "HIGH": "Dehydration possible. Increase fluids unless fluid-restricted; medical review.",
        },
    },
    "Potassium": {
        "category": "Electrolytes",
        "low": 3.5,
        "high": 5.0,
        "unit": "mEq/L",
        "aliases": ["potassium", "k", "serum potassium"],
        "precautions": {
            "LOW": "Muscle weakness risk. Eat potassium-rich foods (banana, spinach) as advised.",
            "HIGH": "Cardiac risk if severe. Avoid potassium supplements/salt substitutes; urgent review.",
        },
    },
    "Chloride": {
        "category": "Electrolytes",
        "low": 98.0,
        "high": 106.0,
        "unit": "mEq/L",
        "aliases": ["chloride", "cl"],
        "precautions": {
            "LOW": "Often with vomiting/alkalosis. Hydration and physician review.",
            "HIGH": "May reflect dehydration or acidosis. Hydrate and repeat.",
        },
    },
    # --- Liver ---
    "ALT": {
        "category": "Liver",
        "low": 7.0,
        "high": 56.0,
        "unit": "U/L",
        "aliases": ["alt", "sgpt", "alanine aminotransferase"],
        "precautions": {
            "LOW": "Usually normal.",
            "HIGH": "Liver cell injury signal. Avoid alcohol, hepatotoxic drugs; hepatitis and medication review.",
        },
    },
    "AST": {
        "category": "Liver",
        "low": 10.0,
        "high": 40.0,
        "unit": "U/L",
        "aliases": ["ast", "sgot", "aspartate aminotransferase"],
        "precautions": {
            "LOW": "Usually normal.",
            "HIGH": "Liver or muscle injury. Avoid alcohol/strenuous exercise before repeat; physician review.",
        },
    },
    "ALP": {
        "category": "Liver",
        "low": 44.0,
        "high": 147.0,
        "unit": "U/L",
        "aliases": ["alp", "alkaline phosphatase", "alk phos"],
        "precautions": {
            "LOW": "Uncommon significance.",
            "HIGH": "Bile duct or bone turnover. Avoid alcohol; imaging/labs per physician.",
        },
    },
    "Bilirubin": {
        "category": "Liver",
        "low": 0.1,
        "high": 1.2,
        "unit": "mg/dL",
        "aliases": ["bilirubin", "total bilirubin", "serum bilirubin"],
        "precautions": {
            "LOW": "Normal.",
            "HIGH": "Jaundice risk. Avoid alcohol; urgent review if yellow eyes/skin or dark urine.",
        },
    },
    "Albumin": {
        "category": "Liver",
        "low": 3.5,
        "high": 5.0,
        "unit": "g/dL",
        "aliases": ["albumin", "serum albumin"],
        "precautions": {
            "LOW": "Malnutrition or liver/kidney loss. Adequate protein intake; physician evaluation.",
            "HIGH": "Usually dehydration. Hydrate and repeat.",
        },
    },
    # --- Lipids ---
    "Cholesterol": {
        "category": "Lipid",
        "low": 0.0,
        "high": 200.0,
        "unit": "mg/dL",
        "high_only": True,
        "aliases": ["cholesterol", "total cholesterol", "serum cholesterol"],
        "precautions": {
            "HIGH": "Cardiovascular risk. Reduce saturated fat, increase fiber, exercise 150 min/week; consider statin discussion with physician.",
        },
    },
    "HDL": {
        "category": "Lipid",
        "low": 40.0,
        "high": 999.0,
        "unit": "mg/dL",
        "low_only": True,
        "aliases": ["hdl", "hdl cholesterol"],
        "precautions": {
            "LOW": "Lower heart protection. Aerobic exercise, quit smoking, healthy fats (nuts, fish).",
        },
    },
    "LDL": {
        "category": "Lipid",
        "low": 0.0,
        "high": 130.0,
        "unit": "mg/dL",
        "high_only": True,
        "aliases": ["ldl", "ldl cholesterol"],
        "precautions": {
            "HIGH": "Atherosclerosis risk. Low saturated fat diet, weight management, lipid-lowering therapy per physician.",
        },
    },
    "Triglycerides": {
        "category": "Lipid",
        "low": 0.0,
        "high": 150.0,
        "unit": "mg/dL",
        "high_only": True,
        "aliases": ["triglycerides", "triglyceride", "tg", "serum triglycerides"],
        "precautions": {
            "HIGH": "Pancreatitis risk if very high. Cut sugar/alcohol, lose weight, repeat fasting lipid panel.",
        },
    },
    # --- Thyroid / Vitamins / Inflammation ---
    "TSH": {
        "category": "Thyroid",
        "low": 0.4,
        "high": 4.0,
        "unit": "mIU/L",
        "aliases": ["tsh", "thyroid stimulating hormone"],
        "precautions": {
            "LOW": "Hyperthyroid pattern possible. Palpitations/weight loss — thyroid review.",
            "HIGH": "Hypothyroid pattern possible. Fatigue/cold intolerance — thyroid hormone review.",
        },
    },
    "Vitamin D": {
        "category": "Vitamins",
        "low": 30.0,
        "high": 100.0,
        "unit": "ng/mL",
        "aliases": ["vitamin d", "vit d", "25-oh vitamin d", "25 hydroxy vitamin d"],
        "precautions": {
            "LOW": "Bone health risk. Safe sun exposure, vitamin D foods/supplements per physician.",
            "HIGH": "Reduce supplements; toxicity rare but needs physician review.",
        },
    },
    "Vitamin B12": {
        "category": "Vitamins",
        "low": 200.0,
        "high": 900.0,
        "unit": "pg/mL",
        "aliases": ["vitamin b12", "b12", "cobalamin"],
        "precautions": {
            "LOW": "Neuropathy/macrocytic anemia risk. B12-rich foods or supplements; absorption workup.",
            "HIGH": "Usually supplement related; adjust dose with physician.",
        },
    },
    "Iron": {
        "category": "Iron Studies",
        "low": 60.0,
        "high": 170.0,
        "unit": "µg/dL",
        "aliases": ["serum iron", "iron"],
        "precautions": {
            "LOW": "Iron deficiency pattern. Iron-rich diet; do not take iron without physician advice.",
            "HIGH": "Hemochromatosis or supplementation. Avoid extra iron; physician review.",
        },
    },
    "Ferritin": {
        "category": "Iron Studies",
        "low": 12.0,
        "high": 300.0,
        "unit": "ng/mL",
        "aliases": ["ferritin", "serum ferritin"],
        "precautions": {
            "LOW": "Iron stores depleted. Nutritional iron and cause of loss evaluation.",
            "HIGH": "Inflammation or iron overload. Physician correlation required.",
        },
    },
    "ESR": {
        "category": "Inflammation",
        "low": 0.0,
        "high": 20.0,
        "unit": "mm/hr",
        "aliases": ["esr", "erythrocyte sedimentation rate"],
        "precautions": {
            "HIGH": "Non-specific inflammation. Investigate infection/autoimmune causes with physician.",
        },
    },
    "CRP": {
        "category": "Inflammation",
        "low": 0.0,
        "high": 3.0,
        "unit": "mg/L",
        "aliases": ["crp", "c reactive protein", "c-reactive protein"],
        "precautions": {
            "HIGH": "Active inflammation/infection. Rest, treat underlying cause; seek care if febrile.",
        },
    },
}

# Core tests expected on a typical blood report for coverage scoring.
CORE_PANEL: list[str] = [
    "Hemoglobin",
    "RBC",
    "WBC",
    "Platelets",
    "Hematocrit",
    "Glucose",
    "Urea",
    "Creatinine",
]

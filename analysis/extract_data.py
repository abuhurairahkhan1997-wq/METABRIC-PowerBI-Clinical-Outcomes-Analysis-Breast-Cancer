"""Extract the patient-level fact table from the Power BI file into data/fact_clinical_outcomes.csv."""
from pathlib import Path
from pbixray import PBIXRay
root = Path(__file__).resolve().parents[1]
m = PBIXRay(str(root / "powerbi" / "METABRIC_Clinical_PowerBI_Analysis.pbix"))
fact = m.get_table("Fact_Clinical_Outcomes")
out = root / "data" / "fact_clinical_outcomes.csv"
fact.to_csv(out, index=False)
print(f"Wrote {len(fact):,} rows to {out}")

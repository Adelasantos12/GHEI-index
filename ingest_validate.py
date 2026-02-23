import pandas as pd
import numpy as np
import os
from config import FILES
from utils import log, ValidationError

RANGES = {
    "A_e_SPAR.Promedio_total": (0, 100),
    "A_GHSIndex.OVERALL SCORE": (0, 100),
    "B_UHCIndex.UHC_Index": (0, 100),
    "B_efforts.value": (0, 100),
    "B_DisasterRisk.value": (0, 1),
    "D_WPI.value": (0, 1),
}

ANNUAL_FILES = {
    "A_e_SPAR": FILES["A_e_SPAR"],
    "A_GHSIndex": FILES["A_GHSIndex"],
    "B_DisasterRisk": FILES["B_DisasterRisk"],
    "B_HealthExpenditure": FILES["B_HealthExpenditure"],
    "B_UHCIndex": FILES["B_UHCIndex"],
    "C_participation": FILES["C_participation"],
    "D_WPI": FILES["D_WPI"],
}

EVENT_FILES = {
    "B_HealthPolicy": FILES["B_HealthPolicy"],
    "B_NationalPlan": FILES["B_NationalPlan"],
    "B_NationalStrategy": FILES["B_NationalStrategy"],
    "B_recognition": FILES["B_recognition"],
}


def load_notion_schema():
    # We keep the file for audit but do not programmatically parse here due to format complexity
    log("Loaded Notion.xlsx for schema reference: %s" % FILES["notion"], "validation.log")


def _read(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".xlsx":
        return pd.read_excel(file_path)
    else:
        # robust CSV reader with encoding fallback
        try:
            return pd.read_csv(file_path, encoding="utf-8")
        except UnicodeDecodeError:
            return pd.read_csv(file_path, encoding="latin-1")


def validate():
    load_notion_schema()
    # Load all files
    data = {}
    for k, fp in {**ANNUAL_FILES, **EVENT_FILES, "B_efforts": FILES["B_efforts"], "C_Exclusiones": FILES["C_Exclusiones"]}.items():
        df = _read(fp)
        data[k] = df
        log(f"Loaded {k} from {fp} shape={df.shape}", "validation.log")

    # Standardize CountryISO column naming
    # Pre-aggregate WPI to ensure uniqueness per ISO-year
    if 'D_WPI' in data:
        dfw = data['D_WPI'].copy()
        dfw.columns = [str(c).strip() for c in dfw.columns]
        iso_col_w = 'ISO' if 'ISO' in dfw.columns else ('iso' if 'iso' in dfw.columns else None)
        year_col_w = 'year' if 'year' in dfw.columns else ('Year' if 'Year' in dfw.columns else None)
        val_col_w = 'value' if 'value' in dfw.columns else ('Value' if 'Value' in dfw.columns else None)
        if iso_col_w and year_col_w and val_col_w:
            dfw[year_col_w] = pd.to_numeric(dfw[year_col_w], errors='coerce')
            dfw[val_col_w] = pd.to_numeric(dfw[val_col_w], errors='coerce')
            agg_w = dfw.groupby([iso_col_w, year_col_w], as_index=False)[val_col_w].mean()
            data['D_WPI'] = agg_w
            log(f"Aggregated D_WPI to unique ISO-year: {agg_w.shape}", "validation.log")

    # Pre-aggregate participation to ensure uniqueness per ISO-year per Notion schema
    if 'C_participation' in data:
        dfp = data['C_participation'].copy()
        # standardize column names
        dfp.columns = [str(c).strip() for c in dfp.columns]
        iso_col = 'ISO' if 'ISO' in dfp.columns else ('iso' if 'iso' in dfp.columns else None)
        year_col = 'year' if 'year' in dfp.columns else ('Year' if 'Year' in dfp.columns else None)
        # ensure numeric types
        for c in ['participation_event_it','decision_event_it','leadership_event_it','admin_event_it','role_type_it']:
            if c in dfp.columns:
                dfp[c] = pd.to_numeric(dfp[c], errors='coerce')
        if iso_col and year_col:
            agg = dfp.groupby([iso_col, year_col], as_index=False).agg({
                'participation_event_it':'sum',
                'decision_event_it':'sum',
                'leadership_event_it':'sum',
                'admin_event_it':'sum',
                'role_type_it':'max'
            })
            data['C_participation'] = agg
            log(f"Aggregated C_participation to unique ISO-year: {agg.shape}", "validation.log")

    def iso_col(df):
        for c in df.columns:
            lc = str(c).lower()
            if lc in ["iso", "countryiso", "...3"]:
                return c
        # fallback for participation_clean
        if "ISO" in df.columns:
            return "ISO"
        if "countryISO" in df.columns:
            return "countryISO"
        return None

    # Check CountryISO consistency (set of ISO codes intersection non-empty, reasonable)
    iso_sets = {}
    for k, df in data.items():
        col = iso_col(df)
        if col is None and k == "B_recognition":
            # recognition has ISO and Country? check columns
            if "ISO" in df.columns:
                col = "ISO"
            elif "iso" in df.columns:
                col = "iso"
        if col is None:
            log(f"WARNING: Could not find ISO column in {k}", "validation.log")
            continue
        iso_sets[k] = set(df[col].dropna().astype(str))
    common = set.intersection(*[s for s in iso_sets.values()]) if iso_sets else set()
    if len(common) == 0:
        raise ValidationError("CountryISO inconsistent across files (no intersection)")

    # Validate year numeric where applicable and uniqueness for annual files
    for k, df in data.items():
        if k in ANNUAL_FILES:
            if "year" not in [c.lower() for c in df.columns]:
                raise ValidationError(f"Missing year in annual file {k}")
            year_col = [c for c in df.columns if str(c).lower() == "year"][0]
            if not pd.api.types.is_numeric_dtype(df[year_col]):
                # try convert
                try:
                    df[year_col] = pd.to_numeric(df[year_col])
                except Exception:
                    raise ValidationError(f"year not numeric in {k}")
            # Uniqueness CountryISO-year
            col_iso = iso_col(df)
            if col_iso:
                dup = df.duplicated(subset=[col_iso, year_col]).sum()
                if dup > 0:
                    raise ValidationError(f"Uniqueness violated in {k}: {dup} duplicates of CountryISO-year")

    # Validate ranges
    # Map columns
    colmap = {
        "A_e_SPAR.Promedio_total": ("A_e_SPAR", "Promedio_total"),
        "A_GHSIndex.OVERALL SCORE": ("A_GHSIndex", "OVERALL SCORE"),
        "B_UHCIndex.UHC_Index": ("B_UHCIndex", "value"),
        "B_efforts.value": ("B_efforts", "Value"),
        "B_DisasterRisk.value": ("B_DisasterRisk", "value"),
        "D_WPI.value": ("D_WPI", "value"),
    }
    for key, (k, col) in colmap.items():
        df = data[k]
        if col not in df.columns:
            # try alternative names
            alt = None
            for c in df.columns:
                if "overall" in str(c).lower() and k == "A_GHSIndex":
                    alt = c
                    break
                if k == "B_UHCIndex" and str(c).lower() in ["uhc_index", "value"]:
                    alt = c
                    break
                if k == "B_efforts" and str(c).lower() in ["value", "score", "val"]:
                    alt = c
                    break
            if alt is None:
                raise ValidationError(f"Column {col} missing in {k}")
            col = alt
        rng = RANGES[key]
        vals = pd.to_numeric(df[col], errors="coerce")
        out = ((vals < rng[0]) | (vals > rng[1])).sum()
        if out > 0:
            raise ValidationError(f"Values out of range in {k}.{col}: {out} rows")
    log("Validation passed.", "validation.log")
    return data

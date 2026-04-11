#!/usr/bin/env python3
"""
Database Migration: Insert EEE canonical overlay into governance.db

Standalone script for Stage 9.9 — can be run independently.

Usage:
    python -m src.eee_overlay.db_migrate \
        --db benchmark_repository/governance.db \
        --canonical path/to/canonicalised_v1.json
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone


EEE_OVERLAY_DDL = """
CREATE TABLE IF NOT EXISTS eee_canonical_overlay (
    case_id TEXT PRIMARY KEY,
    eee_case_id TEXT NOT NULL,
    canonical_version TEXT NOT NULL,
    triangulated_confidence REAL,
    confidence_band TEXT,
    evidence_grade TEXT NOT NULL,
    triangulation_integrity TEXT NOT NULL,
    deployment_risk_class TEXT NOT NULL,
    phenomena_json TEXT,
    audit_flags_json TEXT,
    eee_feature_overlay_json TEXT,
    governance_mapping_json TEXT,
    input_hash TEXT,
    parent_hash TEXT,
    run_timestamp TEXT,
    inserted_at TEXT,
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
);
"""


def create_overlay_table(conn):
    """Create the eee_canonical_overlay table if it doesn't exist."""
    conn.execute(EEE_OVERLAY_DDL)
    conn.commit()


def insert_canonical_overlay(conn, canonical_data):
    """Insert all canonical cases into the overlay table."""
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0

    for case in canonical_data["cases"]:
        conn.execute(
            "INSERT OR REPLACE INTO eee_canonical_overlay VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                case["case_id"],
                case["eee_case_id"],
                case["canonical_version"],
                case["triangulated_confidence"],
                case["confidence_band"],
                case["evidence_grade"],
                case["triangulation_integrity"],
                case["deployment_risk_class"],
                json.dumps(case["phenomena"]),
                json.dumps(case["audit_flags"]),
                json.dumps(case["eee_feature_overlay"]),
                json.dumps(case["governance_mapping"]),
                case["evidence_provenance"]["input_hash"],
                case["evidence_provenance"]["parent_hash"],
                case["evidence_provenance"]["run_timestamp"],
                now,
            ),
        )
        inserted += 1

    conn.commit()
    return inserted


def verify_integrity(conn):
    """Verify FK integrity and blocked case constraints."""
    # FK check
    orphans = conn.execute("""
        SELECT o.case_id FROM eee_canonical_overlay o
        LEFT JOIN cases c ON o.case_id = c.case_id
        WHERE c.case_id IS NULL
    """).fetchall()

    if orphans:
        print(f"FAIL: Foreign key violations: {[r[0] for r in orphans]}", file=sys.stderr)
        return False

    # Blocked case check
    for blocked in ["acclarent_trudi_navigation_reuters2026", "sonio_detect_prenatal_labeling_reuters2026"]:
        row = conn.execute(
            "SELECT deployment_risk_class, evidence_grade, eee_feature_overlay_json FROM eee_canonical_overlay WHERE case_id=?",
            (blocked,),
        ).fetchone()
        if not row:
            print(f"FAIL: Missing blocked case {blocked}", file=sys.stderr)
            return False
        if row[0] != "BLOCKED" or row[1] != "INSUFFICIENT":
            print(f"FAIL: Blocked case {blocked} has wrong state: {row[0]}/{row[1]}", file=sys.stderr)
            return False
        overlay = json.loads(row[2])
        if len(overlay) > 0:
            print(f"FAIL: Blocked case {blocked} has non-empty overlay", file=sys.stderr)
            return False

    total = conn.execute("SELECT COUNT(*) FROM eee_canonical_overlay").fetchone()[0]
    print(f"Verification passed: {total} rows, 0 orphans, blocked cases correct")
    return True


def main():
    parser = argparse.ArgumentParser(description="Insert EEE overlay into governance.db")
    parser.add_argument("--db", required=True, help="Path to governance.db")
    parser.add_argument("--canonical", required=True, help="Path to canonicalised_dataset_v1.json")
    args = parser.parse_args()

    with open(args.canonical) as f:
        canonical = json.load(f)

    conn = sqlite3.connect(args.db)

    create_overlay_table(conn)
    inserted = insert_canonical_overlay(conn, canonical)
    print(f"Inserted {inserted} cases into eee_canonical_overlay")

    ok = verify_integrity(conn)
    conn.close()

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

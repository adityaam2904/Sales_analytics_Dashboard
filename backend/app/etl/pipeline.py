import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.etl.cleaners import clean_dataframe
from app.etl.loader import load_dataframe, save_rejected_records

# ─────────────────────────────────────────────
# LOGGING HELPER
# ─────────────────────────────────────────────

def log(db: Session, run_id: int, level: str, message: str):
    """Write a log line to etl_logs table."""
    db.execute(text("""
        INSERT INTO etl_logs (run_id, level, message)
        VALUES (:run_id, :level, :message)
    """), {"run_id": run_id, "level": level, "message": message})
    db.commit()
    print(f"[{level}] {message}")


# ─────────────────────────────────────────────
# CREATE ETL RUN
# ─────────────────────────────────────────────

def create_run(db: Session, mode: str = "incremental") -> int:
    """Create a new ETL run record and return its run_id."""
    result = db.execute(text("""
        INSERT INTO etl_runs (mode, status)
        VALUES (:mode, 'running')
        RETURNING run_id
    """), {"mode": mode})
    db.commit()
    return result.fetchone().run_id


# ─────────────────────────────────────────────
# FINISH ETL RUN
# ─────────────────────────────────────────────

def finish_run(db: Session, run_id: int, totals: dict, status: str):
    """Update the ETL run with final counts and status."""
    db.execute(text("""
        UPDATE etl_runs
        SET status          = :status,
            finished_at     = now(),
            files_processed = :files_processed,
            rows_read       = :rows_read,
            rows_inserted   = :rows_inserted,
            rows_updated    = :rows_updated,
            rows_unchanged  = :rows_unchanged,
            rows_rejected   = :rows_rejected
        WHERE run_id = :run_id
    """), {
        "run_id":          run_id,
        "status":          status,
        "files_processed": totals.get("files_processed", 0),
        "rows_read":       totals.get("rows_read", 0),
        "rows_inserted":   totals.get("rows_inserted", 0),
        "rows_updated":    totals.get("rows_updated", 0),
        "rows_unchanged":  totals.get("rows_unchanged", 0),
        "rows_rejected":   totals.get("rows_rejected", 0),
    })
    db.commit()


# ─────────────────────────────────────────────
# UPDATE UPLOADED FILE STATUS
# ─────────────────────────────────────────────

def update_file_status(db: Session, file_id: int, run_id: int,
                       status: str, counts: dict, error: str = None):
    """Update the uploaded_files record after processing."""
    db.execute(text("""
        UPDATE uploaded_files
        SET status        = :status,
            processed_at  = now(),
            last_run_id   = :run_id,
            rows_read     = :rows_read,
            rows_inserted = :rows_inserted,
            rows_updated  = :rows_updated,
            rows_unchanged= :rows_unchanged,
            rows_rejected = :rows_rejected,
            error_message = :error_message
        WHERE file_id = :file_id
    """), {
        "file_id":       file_id,
        "run_id":        run_id,
        "status":        status,
        "rows_read":     counts.get("rows_read", 0),
        "rows_inserted": counts.get("inserted", 0),
        "rows_updated":  counts.get("updated", 0),
        "rows_unchanged":counts.get("unchanged", 0),
        "rows_rejected": counts.get("rejected", 0),
        "error_message": error
    })
    db.commit()


# ─────────────────────────────────────────────
# PROCESS ONE FILE
# ─────────────────────────────────────────────

def process_file(db: Session, run_id: int, file_record) -> dict:
    """
    Process a single uploaded file through the full ETL pipeline:
    1. Read CSV
    2. Clean and validate with Pandas
    3. Save rejected rows
    4. Load clean rows into PostgreSQL
    """
    file_id   = file_record.file_id
    entity    = file_record.entity
    file_path = file_record.stored_path

    log(db, run_id, "INFO", f"Starting processing: {file_record.original_name} ({entity})")

    # ── Step 1: Read CSV ─────────────────────
    try:
        df = pd.read_csv(file_path)
        rows_read = len(df)
        log(db, run_id, "INFO", f"Read {rows_read} rows from {file_record.original_name}")
    except Exception as e:
        error_msg = f"Failed to read CSV: {str(e)}"
        log(db, run_id, "ERROR", error_msg)
        update_file_status(db, file_id, run_id, "failed", {}, error=error_msg)
        return {"rows_read": 0, "inserted": 0, "updated": 0,
                "unchanged": 0, "rejected": 0, "status": "failed"}

    # ── Step 2: Clean and Validate ───────────
    try:
        clean_df, rejected_rows = clean_dataframe(entity, df)
        rows_rejected = len(rejected_rows)
        rows_clean    = len(clean_df)

        log(db, run_id, "INFO",
            f"Validation complete: {rows_clean} clean, {rows_rejected} rejected")

        if rows_rejected > 0:
            log(db, run_id, "WARNING",
                f"{rows_rejected} rows rejected in {entity}")

    except Exception as e:
        error_msg = f"Cleaning failed: {str(e)}"
        log(db, run_id, "ERROR", error_msg)
        update_file_status(db, file_id, run_id, "failed", {}, error=error_msg)
        return {"rows_read": rows_read, "inserted": 0, "updated": 0,
                "unchanged": 0, "rejected": 0, "status": "failed"}

    # ── Step 3: Save Rejected Rows ───────────
    if rejected_rows:
        try:
            save_rejected_records(rejected_rows, entity, run_id, file_id, db)
            log(db, run_id, "INFO", f"Saved {rows_rejected} rejected records")
        except Exception as e:
            log(db, run_id, "WARNING", f"Could not save rejected records: {str(e)}")

    # ── Step 4: Load Clean Data ──────────────
    counts = {"rows_read": rows_read, "rejected": rows_rejected}

    if clean_df.empty:
        log(db, run_id, "WARNING", f"No clean rows to load for {entity}")
        update_file_status(db, file_id, run_id, "processed", counts)
        counts.update({"inserted": 0, "updated": 0, "unchanged": 0})
        return counts

    try:
        result = load_dataframe(entity, clean_df, db)
        counts.update(result)

        # Handle skipped orders (orphan foreign keys)
        skipped = result.get("skipped", [])
        if skipped:
            for s in skipped:
                log(db, run_id, "WARNING", f"Skipped order: {s['reason']}")
                # Also save skipped orders as rejected records
                save_rejected_records(
                    [{"row_number": 0, "reason": s["reason"], "raw_data": s["row"]}],
                    entity, run_id, file_id, db
                )
            counts["rejected"] += len(skipped)

        log(db, run_id, "INFO",
            f"Loaded {entity}: inserted={result.get('inserted',0)}, "
            f"updated={result.get('updated',0)}, "
            f"unchanged={result.get('unchanged',0)}")

        update_file_status(db, file_id, run_id, "processed", counts)
        counts["status"] = "processed"

    except Exception as e:
        error_msg = f"Loading failed: {str(e)}"
        log(db, run_id, "ERROR", error_msg)
        update_file_status(db, file_id, run_id, "failed", counts, error=error_msg)
        counts["status"] = "failed"

    return counts


# ─────────────────────────────────────────────
# MAIN PIPELINE ORCHESTRATOR
# ─────────────────────────────────────────────

def run_pipeline(db: Session, mode: str = "incremental") -> dict:
    """
    Main ETL pipeline entry point.
    - Creates a new run record
    - Finds all uploaded (unprocessed) files
    - Processes each file in correct order: customers → products → orders
    - Updates run summary with final counts
    """

    # ── Create ETL Run ───────────────────────
    run_id = create_run(db, mode)
    log(db, run_id, "INFO", f"ETL pipeline started | mode={mode} | run_id={run_id}")

    # ── Fetch Pending Files ──────────────────
    # Process in order: customers first, then products, then orders
    # This ensures foreign keys exist before orders are loaded
    pending_files = db.execute(text("""
        SELECT file_id, entity, original_name, stored_path
        FROM uploaded_files
        WHERE status = 'uploaded'
        ORDER BY
            CASE entity
                WHEN 'customers' THEN 1
                WHEN 'products'  THEN 2
                WHEN 'orders'    THEN 3
            END,
            uploaded_at ASC
    """)).fetchall()

    if not pending_files:
        log(db, run_id, "WARNING", "No pending files found to process")
        finish_run(db, run_id, {}, "success")
        return {
            "run_id": run_id,
            "status": "success",
            "message": "No pending files to process"
        }

    log(db, run_id, "INFO", f"Found {len(pending_files)} file(s) to process")

    # ── Process Each File ────────────────────
    totals = {
        "files_processed": 0,
        "rows_read":       0,
        "rows_inserted":   0,
        "rows_updated":    0,
        "rows_unchanged":  0,
        "rows_rejected":   0
    }

    all_statuses = []

    for file_record in pending_files:
        result = process_file(db, run_id, file_record)

        totals["files_processed"] += 1
        totals["rows_read"]       += result.get("rows_read", 0)
        totals["rows_inserted"]   += result.get("inserted", 0)
        totals["rows_updated"]    += result.get("updated", 0)
        totals["rows_unchanged"]  += result.get("unchanged", 0)
        totals["rows_rejected"]   += result.get("rejected", 0)
        all_statuses.append(result.get("status", "failed"))

    # ── Determine Final Status ───────────────
    if all(s == "processed" for s in all_statuses):
        final_status = "success"
    elif all(s == "failed" for s in all_statuses):
        final_status = "failed"
    else:
        final_status = "partial"

    # ── Finish Run ───────────────────────────
    finish_run(db, run_id, totals, final_status)
    log(db, run_id, "INFO",
        f"ETL pipeline finished | status={final_status} | "
        f"inserted={totals['rows_inserted']} | "
        f"updated={totals['rows_updated']} | "
        f"rejected={totals['rows_rejected']}")

    return {
        "run_id":          run_id,
        "status":          final_status,
        "files_processed": totals["files_processed"],
        "rows_read":       totals["rows_read"],
        "rows_inserted":   totals["rows_inserted"],
        "rows_updated":    totals["rows_updated"],
        "rows_unchanged":  totals["rows_unchanged"],
        "rows_rejected":   totals["rows_rejected"]
    }
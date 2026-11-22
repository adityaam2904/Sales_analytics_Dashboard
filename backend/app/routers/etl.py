from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.etl.pipeline import run_pipeline

router = APIRouter(prefix="/etl", tags=["ETL"])


# ─────────────────────────────────────────────
# TRIGGER ETL PIPELINE
# ─────────────────────────────────────────────
 
@router.post("/run")
def trigger_etl(
    mode: str = "incremental",
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Trigger the ETL pipeline.
    mode: 'incremental' (default) or 'full_reload'
    """
    if mode not in ("incremental", "full_reload"):
        raise HTTPException(
            status_code=400,
            detail="mode must be 'incremental' or 'full_reload'"
        )

    # Check if a run is already in progress
    active_run = db.execute(text("""
        SELECT run_id FROM etl_runs
        WHERE status = 'running'
        LIMIT 1
    """)).fetchone()

    if active_run:
        raise HTTPException(
            status_code=409,
            detail=f"ETL run #{active_run.run_id} is already in progress. Wait for it to finish."
        )

    # If full_reload, reset all uploaded files back to 'uploaded'
    if mode == "full_reload":
        db.execute(text("""
            UPDATE uploaded_files
            SET status = 'uploaded'
            WHERE status IN  ('processed','failed')
        """))
        db.commit()

    # Run the pipeline
    result = run_pipeline(db, mode=mode)

    return {
        "message":         "✅ ETL pipeline completed",
        "run_id":          result["run_id"],
        "status":          result["status"],
        "files_processed": result["files_processed"],
        "rows_read":       result["rows_read"],
        "rows_inserted":   result["rows_inserted"],
        "rows_updated":    result["rows_updated"],
        "rows_unchanged":  result["rows_unchanged"],
        "rows_rejected":   result["rows_rejected"]
    }


# ─────────────────────────────────────────────
# GET ALL ETL RUNS
# ─────────────────────────────────────────────

@router.get("/runs")
def get_etl_runs(limit: int = 20, db: Session = Depends(get_db)):
    """Get list of all ETL runs with their summary."""
    runs = db.execute(text("""
        SELECT
            run_id,
            mode,
            status,
            started_at,
            finished_at,
            files_processed,
            rows_read,
            rows_inserted,
            rows_updated,
            rows_unchanged,
            rows_rejected,
            EXTRACT(EPOCH FROM (finished_at - started_at))::INT AS duration_seconds
        FROM etl_runs
        ORDER BY started_at DESC
        LIMIT :limit
    """), {"limit": limit}).fetchall()

    return [dict(row._mapping) for row in runs]


# ─────────────────────────────────────────────
# GET SINGLE RUN DETAILS
# ─────────────────────────────────────────────

@router.get("/runs/{run_id}")
def get_run_detail(run_id: int, db: Session = Depends(get_db)):
    """Get full details of a specific ETL run."""
    run = db.execute(text("""
        SELECT
            run_id, mode, status,
            started_at, finished_at,
            files_processed, rows_read,
            rows_inserted, rows_updated,
            rows_unchanged, rows_rejected,
            EXTRACT(EPOCH FROM (finished_at - started_at))::INT AS duration_seconds
        FROM etl_runs
        WHERE run_id = :run_id
    """), {"run_id": run_id}).fetchone()

    if not run:
        raise HTTPException(status_code=404, detail=f"Run #{run_id} not found")

    return dict(run._mapping)


# ─────────────────────────────────────────────
# GET LOGS FOR A RUN
# ─────────────────────────────────────────────

@router.get("/runs/{run_id}/logs")
def get_run_logs(run_id: int, db: Session = Depends(get_db)):
    """Get all log lines for a specific ETL run."""
    # Verify run exists
    run = db.execute(text(
        "SELECT run_id FROM etl_runs WHERE run_id = :run_id"
    ), {"run_id": run_id}).fetchone()

    if not run:
        raise HTTPException(status_code=404, detail=f"Run #{run_id} not found")

    logs = db.execute(text("""
        SELECT log_id, level, message, created_at
        FROM etl_logs
        WHERE run_id = :run_id
        ORDER BY created_at ASC
    """), {"run_id": run_id}).fetchall()

    return [dict(row._mapping) for row in logs]


# ─────────────────────────────────────────────
# GET REJECTED RECORDS
# ─────────────────────────────────────────────

@router.get("/rejected")
def get_rejected_records(
    run_id: int = None,
    entity: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get rejected records.
    Optionally filter by run_id and/or entity.
    """
    filters = []
    params  = {"limit": limit}

    if run_id:
        filters.append("run_id = :run_id")
        params["run_id"] = run_id

    if entity:
        if entity not in ("customers", "products", "orders"):
            raise HTTPException(status_code=400, detail="Invalid entity")
        filters.append("entity = :entity")
        params["entity"] = entity

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""

    records = db.execute(text(f"""
        SELECT
            reject_id, run_id, upload_id, entity,
            row_number, reason, raw_data, created_at
        FROM rejected_records
        {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit
    """), params).fetchall()

    return [dict(row._mapping) for row in records]


# ─────────────────────────────────────────────
# GET LATEST RUN STATUS (for dashboard polling)
# ─────────────────────────────────────────────

@router.get("/status")
def get_latest_status(db: Session = Depends(get_db)):
    """Get the status of the most recent ETL run."""
    run = db.execute(text("""
        SELECT
            run_id, mode, status,
            started_at, finished_at,
            rows_inserted, rows_rejected
        FROM etl_runs
        ORDER BY started_at DESC
        LIMIT 1
    """)).fetchone()

    if not run:
        return {"message": "No ETL runs yet"}

    return dict(run._mapping)
"""Full library export/import as .zip archive (library.db + PDF attachments)."""
import os
import zipfile
import json
import logging
from datetime import datetime

log = logging.getLogger(__name__)


def export_full_zip(output_path, db_path, pdf_dir=None, metadata=None):
    """Export entire library state as a .zip archive.
    
    Args:
        output_path: Path for the output .zip file.
        db_path: Path to the current library.db.
        pdf_dir: Optional directory containing PDF files to include.
        metadata: Optional dict with extra info (e.g., export date, version).
    
    Returns:
        int: Number of files archived, or 0 on failure.
    """
    count = 0
    try:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add manifest
            manifest = {
                "export_date": datetime.now().isoformat(),
                "version": "1.0",
                "type": "IntelliPaper Full Backup",
            }
            if metadata:
                manifest.update(metadata)
            zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
            count += 1

            # Add database
            if os.path.isfile(db_path):
                zf.write(db_path, "library.db")
                count += 1
                log.info("Added library.db to archive")

            # Add WAL / SHM if they exist
            for ext in ("-wal", "-shm"):
                extra = db_path + ext
                if os.path.isfile(extra):
                    zf.write(extra, os.path.basename(extra))
                    count += 1

            # Add PDF files
            if pdf_dir and os.path.isdir(pdf_dir):
                pdf_count = 0
                for root, dirs, files in os.walk(pdf_dir):
                    for fname in files:
                        if fname.lower().endswith(".pdf"):
                            fpath = os.path.join(root, fname)
                            arcname = os.path.join("pdfs", fname)
                            zf.write(fpath, arcname)
                            pdf_count += 1
                            count += 1
                log.info("Added %d PDF files to archive", pdf_count)

            # Add embeddings cache if exists
            cache_dir = os.path.join(os.path.dirname(db_path), "cache")
            if os.path.isdir(cache_dir):
                for fname in os.listdir(cache_dir):
                    fpath = os.path.join(cache_dir, fname)
                    if os.path.isfile(fpath):
                        zf.write(fpath, os.path.join("cache", fname))
                        count += 1

        log.info("Full backup created: %s (%d files)", output_path, count)
        return count
    except Exception as e:
        log.error("Failed to create full backup: %s", e)
        return 0


def import_full_zip(zip_path, extract_dir):
    """Restore full library state from a .zip archive.
    
    Args:
        zip_path: Path to the .zip archive.
        extract_dir: Directory to extract files into.
    
    Returns:
        dict: Summary with keys: success (bool), files (int), db_path (str), pdf_dir (str).
    """
    result = {"success": False, "files": 0, "db_path": "", "pdf_dir": ""}
    try:
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
            file_list = zf.namelist()
            result["files"] = len(file_list)

            # Locate extracted database
            db_candidates = [f for f in file_list if f.endswith(".db")]
            if db_candidates:
                result["db_path"] = os.path.join(extract_dir, db_candidates[0])

            # Locate extracted PDFs
            pdf_dir = os.path.join(extract_dir, "pdfs")
            if os.path.isdir(pdf_dir):
                result["pdf_dir"] = pdf_dir

        result["success"] = True
        log.info("Full restore extracted %d files to %s", result["files"], extract_dir)
        return result
    except Exception as e:
        log.error("Failed to restore from backup: %s", e)
        result["error"] = str(e)
        return result

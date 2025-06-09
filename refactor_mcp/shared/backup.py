"""Backup and restore functionality for safe refactoring operations."""

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .logging import get_logger

logger = get_logger(__name__)


class BackupManager:
    """Manages file backups for safe refactoring operations."""

    def __init__(self, backup_dir: Optional[str] = None):
        """Initialize backup manager.

        Args:
            backup_dir: Directory for backups. If None, uses temp directory.
        """
        if backup_dir:
            self.backup_root = Path(backup_dir)
        else:
            self.backup_root = Path(tempfile.gettempdir()) / "refactor-mcp-backups"

        self.backup_root.mkdir(parents=True, exist_ok=True)
        self._active_backups: Dict[str, Path] = {}
        logger.debug(f"Backup manager initialized: {self.backup_root}")

    def create_backup(self, operation_id: str, files: List[str]) -> Path:
        """Create backup for a set of files.

        Args:
            operation_id: Unique identifier for the operation
            files: List of file paths to backup

        Returns:
            Path to backup directory

        Raises:
            OSError: If backup creation fails
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{operation_id}_{timestamp}"
        backup_dir = self.backup_root / backup_name

        try:
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Create manifest
            manifest = {
                "operation_id": operation_id,
                "timestamp": timestamp,
                "files": [],
                "project_root": None,
            }

            # Determine common project root
            if files:
                project_root = self._find_common_root(files)
                manifest["project_root"] = str(project_root)

                # Copy files preserving directory structure
                for file_path in files:
                    source = Path(file_path)
                    if not source.exists():
                        logger.warning(f"File not found for backup: {file_path}")
                        continue

                    # Calculate relative path from project root
                    try:
                        rel_path = source.relative_to(project_root)
                    except ValueError:
                        # File outside project root, use absolute structure
                        rel_path = Path(str(source).lstrip("/"))

                    target = backup_dir / "files" / rel_path
                    target.parent.mkdir(parents=True, exist_ok=True)

                    shutil.copy2(source, target)
                    manifest["files"].append(
                        {
                            "original_path": str(source),
                            "backup_path": str(rel_path),
                            "size": source.stat().st_size,
                            "mtime": source.stat().st_mtime,
                        }
                    )

                    logger.debug(f"Backed up: {source} -> {target}")

            # Save manifest
            manifest_path = backup_dir / "manifest.json"
            with manifest_path.open("w") as f:
                json.dump(manifest, f, indent=2)

            self._active_backups[operation_id] = backup_dir
            logger.info(f"Created backup for operation {operation_id}: {backup_dir}")

            return backup_dir

        except Exception as e:
            logger.error(f"Failed to create backup for {operation_id}: {e}")
            # Clean up partial backup
            if backup_dir.exists():
                shutil.rmtree(backup_dir, ignore_errors=True)
            raise

    def restore_backup(self, operation_id: str) -> bool:
        """Restore files from backup.

        Args:
            operation_id: Operation identifier to restore

        Returns:
            True if restore successful, False otherwise
        """
        backup_dir = self._active_backups.get(operation_id)
        if not backup_dir or not backup_dir.exists():
            # Try to find backup by scanning directory
            backup_dir = self._find_backup_by_operation_id(operation_id)
            if not backup_dir:
                logger.error(f"No backup found for operation: {operation_id}")
                return False

        try:
            manifest_path = backup_dir / "manifest.json"
            if not manifest_path.exists():
                logger.error(f"Backup manifest not found: {manifest_path}")
                return False

            with manifest_path.open() as f:
                manifest = json.load(f)

            files_restored = 0

            for file_info in manifest["files"]:
                original_path = Path(file_info["original_path"])
                backup_rel_path = file_info["backup_path"]
                backup_file = backup_dir / "files" / backup_rel_path

                if not backup_file.exists():
                    logger.warning(f"Backup file not found: {backup_file}")
                    continue

                # Ensure target directory exists
                original_path.parent.mkdir(parents=True, exist_ok=True)

                # Restore file
                shutil.copy2(backup_file, original_path)
                files_restored += 1
                logger.debug(f"Restored: {backup_file} -> {original_path}")

            logger.info(f"Restored {files_restored} files for operation {operation_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore backup for {operation_id}: {e}")
            return False

    def cleanup_backup(self, operation_id: str) -> bool:
        """Remove backup after successful operation.

        Args:
            operation_id: Operation identifier to clean up

        Returns:
            True if cleanup successful, False otherwise
        """
        backup_dir = self._active_backups.get(operation_id)
        if backup_dir and backup_dir.exists():
            try:
                shutil.rmtree(backup_dir)
                del self._active_backups[operation_id]
                logger.info(f"Cleaned up backup for operation {operation_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to cleanup backup for {operation_id}: {e}")
                return False

        logger.warning(f"No active backup found for operation {operation_id}")
        return False

    def list_backups(self) -> List[Dict[str, any]]:
        """List all available backups.

        Returns:
            List of backup information dictionaries
        """
        backups = []

        if not self.backup_root.exists():
            return backups

        for backup_dir in self.backup_root.iterdir():
            if not backup_dir.is_dir():
                continue

            manifest_path = backup_dir / "manifest.json"
            if not manifest_path.exists():
                continue

            try:
                with manifest_path.open() as f:
                    manifest = json.load(f)

                backups.append(
                    {
                        "operation_id": manifest["operation_id"],
                        "timestamp": manifest["timestamp"],
                        "backup_dir": str(backup_dir),
                        "file_count": len(manifest["files"]),
                        "project_root": manifest.get("project_root"),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to read backup manifest {manifest_path}: {e}")

        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)

    def _find_common_root(self, files: List[str]) -> Path:
        """Find common root directory for a list of files."""
        if not files:
            return Path.cwd()

        paths = [Path(f).absolute() for f in files]

        # Find common parent
        common_parts = []
        for parts in zip(*[p.parts for p in paths]):
            if len(set(parts)) == 1:  # All parts are the same
                common_parts.append(parts[0])
            else:
                break

        if common_parts:
            return Path(*common_parts)
        else:
            # No common root, use filesystem root
            return Path(paths[0].anchor)

    def _find_backup_by_operation_id(self, operation_id: str) -> Optional[Path]:
        """Find backup directory by operation ID."""
        if not self.backup_root.exists():
            return None

        for backup_dir in self.backup_root.iterdir():
            if backup_dir.is_dir() and operation_id in backup_dir.name:
                manifest_path = backup_dir / "manifest.json"
                if manifest_path.exists():
                    try:
                        with manifest_path.open() as f:
                            manifest = json.load(f)
                        if manifest.get("operation_id") == operation_id:
                            return backup_dir
                    except Exception:
                        continue

        return None


# Global backup manager instance
_backup_manager = BackupManager()


def get_backup_manager() -> BackupManager:
    """Get the global backup manager instance."""
    return _backup_manager


def create_backup(operation_id: str, files: List[str]) -> Path:
    """Create backup using global manager."""
    return _backup_manager.create_backup(operation_id, files)


def restore_backup(operation_id: str) -> bool:
    """Restore backup using global manager."""
    return _backup_manager.restore_backup(operation_id)


def cleanup_backup(operation_id: str) -> bool:
    """Cleanup backup using global manager."""
    return _backup_manager.cleanup_backup(operation_id)

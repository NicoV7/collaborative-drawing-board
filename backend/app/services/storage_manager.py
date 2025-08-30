"""
StorageManager - File system storage management with TTL cleanup.

This service manages file system storage for the collaborative drawing board:
- Expired file cleanup based on modification time and database TTL
- Storage usage calculation and reporting
- Orphaned file detection and cleanup
- File categorization (uploads, templates, exports, avatars)
- Storage optimization and cleanup prioritization

Features:
- Cross-platform file operations
- Safe deletion with backup/quarantine options
- Storage usage analytics by category
- Concurrent file operations
- Integration with database TTL policies
"""

import os
import shutil
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import mimetypes
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import FileUpload, UserAvatar, BoardTemplate


logger = logging.getLogger(__name__)


@dataclass
class StorageUsageStats:
    """
    Storage usage statistics by category.
    """
    total_bytes: int = 0
    uploads_bytes: int = 0
    templates_bytes: int = 0
    exports_bytes: int = 0
    avatars_bytes: int = 0
    orphaned_bytes: int = 0
    file_count: int = 0
    orphaned_count: int = 0
    last_calculated: datetime = None

    def __post_init__(self):
        if self.last_calculated is None:
            self.last_calculated = datetime.now(timezone.utc)


@dataclass
class CleanupOperationResult:
    """
    Result of a storage cleanup operation.
    """
    operation_type: str
    success: bool = False
    deleted_files_count: int = 0
    freed_bytes: int = 0
    orphaned_files_count: int = 0
    skipped_files_count: int = 0
    error_count: int = 0
    errors: List[str] = None
    execution_time_seconds: float = 0
    cleaned_paths: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.cleaned_paths is None:
            self.cleaned_paths = []


class StorageManager:
    """
    Service for managing file system storage with TTL cleanup.
    
    Handles file cleanup based on TTL policies, storage usage tracking,
    and orphaned file detection.
    """

    def __init__(self, base_path: str = None, db_session: Session = None):
        """
        Initialize StorageManager.
        
        Args:
            base_path: Base directory for file storage (uses default if None)
            db_session: Database session for orphaned file detection
        """
        self.base_path = Path(base_path) if base_path else self._get_default_base_path()
        self.db = db_session
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Storage paths by category
        self.storage_paths = {
            "uploads": self.base_path / "uploads",
            "templates": self.base_path / "templates", 
            "exports": self.base_path / "exports",
            "avatars": self.base_path / "avatars",
            "temp": self.base_path / "temp"
        }
        
        # Ensure directories exist
        self._ensure_directories()

    def _get_default_base_path(self) -> Path:
        """Get default base path for file storage."""
        # Use a storage directory in the project root
        current_dir = Path(__file__).parent.parent.parent
        storage_dir = current_dir / "storage"
        return storage_dir

    def _ensure_directories(self):
        """Ensure all storage directories exist."""
        for path in self.storage_paths.values():
            path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Ensured directory exists: {path}")

    def cleanup_expired_files(self, max_age_hours: int = 24, category: str = None) -> CleanupOperationResult:
        """
        Clean up files older than max_age_hours.
        
        Args:
            max_age_hours: Maximum age in hours before deletion
            category: File category to clean (None for all categories)
            
        Returns:
            CleanupOperationResult with cleanup metrics
        """
        start_time = datetime.now()
        result = CleanupOperationResult(
            operation_type=f"expired_cleanup_{category or 'all'}"
        )
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            paths_to_check = []
            
            if category:
                if category in self.storage_paths:
                    paths_to_check = [self.storage_paths[category]]
            else:
                paths_to_check = list(self.storage_paths.values())
            
            deleted_count = 0
            freed_bytes = 0
            
            for storage_path in paths_to_check:
                if not storage_path.exists():
                    continue
                    
                for file_path in storage_path.rglob("*"):
                    if not file_path.is_file():
                        continue
                    
                    try:
                        # Check file modification time
                        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if mod_time < cutoff_time:
                            file_size = file_path.stat().st_size
                            file_path.unlink()  # Delete file
                            
                            deleted_count += 1
                            freed_bytes += file_size
                            result.cleaned_paths.append(str(file_path))
                            
                            self.logger.debug(f"Deleted expired file: {file_path}")
                    
                    except Exception as e:
                        result.error_count += 1
                        result.errors.append(f"Failed to process {file_path}: {str(e)}")
                        self.logger.error(f"Failed to process file {file_path}: {e}")
            
            result.deleted_files_count = deleted_count
            result.freed_bytes = freed_bytes
            result.success = True
            
            self.logger.info(f"Cleanup completed: {deleted_count} files deleted, {freed_bytes} bytes freed")
            
        except Exception as e:
            result.success = False
            result.error_count += 1
            result.errors.append(f"Cleanup operation failed: {str(e)}")
            self.logger.error(f"Cleanup operation failed: {e}")
        
        result.execution_time_seconds = (datetime.now() - start_time).total_seconds()
        return result

    def cleanup_orphaned_files(self) -> CleanupOperationResult:
        """
        Clean up files that exist in filesystem but not referenced in database.
        
        Returns:
            CleanupOperationResult with orphaned file cleanup metrics
        """
        start_time = datetime.now()
        result = CleanupOperationResult(operation_type="orphaned_cleanup")
        
        if not self.db:
            result.success = False
            result.errors.append("Database session required for orphaned file cleanup")
            return result
        
        try:
            # Get all file references from database
            db_file_paths = set()
            
            # FileUpload references
            file_uploads = self.db.query(FileUpload).all()
            for upload in file_uploads:
                db_file_paths.add(upload.file_path)
            
            # UserAvatar references
            avatars = self.db.query(UserAvatar).all()
            for avatar in avatars:
                db_file_paths.add(avatar.file_path)
            
            # Check filesystem for orphaned files
            orphaned_count = 0
            freed_bytes = 0
            
            for storage_path in self.storage_paths.values():
                if not storage_path.exists():
                    continue
                    
                for file_path in storage_path.rglob("*"):
                    if not file_path.is_file():
                        continue
                    
                    try:
                        file_path_str = str(file_path)
                        
                        # Check if file is referenced in database
                        if file_path_str not in db_file_paths:
                            file_size = file_path.stat().st_size
                            
                            # Move to quarantine instead of immediate deletion for safety
                            quarantine_path = self._quarantine_file(file_path)
                            
                            orphaned_count += 1
                            freed_bytes += file_size
                            result.cleaned_paths.append(file_path_str)
                            
                            self.logger.debug(f"Quarantined orphaned file: {file_path} -> {quarantine_path}")
                    
                    except Exception as e:
                        result.error_count += 1
                        result.errors.append(f"Failed to process orphaned file {file_path}: {str(e)}")
                        self.logger.error(f"Failed to process orphaned file {file_path}: {e}")
            
            result.orphaned_files_count = orphaned_count
            result.freed_bytes = freed_bytes
            result.success = True
            
            self.logger.info(f"Orphaned file cleanup completed: {orphaned_count} files quarantined, {freed_bytes} bytes freed")
            
        except Exception as e:
            result.success = False
            result.error_count += 1
            result.errors.append(f"Orphaned file cleanup failed: {str(e)}")
            self.logger.error(f"Orphaned file cleanup failed: {e}")
        
        result.execution_time_seconds = (datetime.now() - start_time).total_seconds()
        return result

    def _quarantine_file(self, file_path: Path) -> Path:
        """
        Move file to quarantine directory instead of deleting immediately.
        
        Args:
            file_path: Path to file to quarantine
            
        Returns:
            Path where file was moved
        """
        quarantine_dir = self.base_path / "quarantine"
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique quarantine filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        quarantine_name = f"{timestamp}_{file_path.name}"
        quarantine_path = quarantine_dir / quarantine_name
        
        # Move file to quarantine
        shutil.move(str(file_path), str(quarantine_path))
        
        return quarantine_path

    def calculate_storage_usage(self) -> StorageUsageStats:
        """
        Calculate storage usage by category.
        
        Returns:
            StorageUsageStats with usage information
        """
        stats = StorageUsageStats()
        
        try:
            for category, path in self.storage_paths.items():
                if not path.exists():
                    continue
                
                category_bytes = 0
                category_files = 0
                
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        try:
                            file_size = file_path.stat().st_size
                            category_bytes += file_size
                            category_files += 1
                        except OSError:
                            # Skip files that can't be accessed
                            pass
                
                # Assign to appropriate category
                if category == "uploads":
                    stats.uploads_bytes = category_bytes
                elif category == "templates":
                    stats.templates_bytes = category_bytes
                elif category == "exports":
                    stats.exports_bytes = category_bytes
                elif category == "avatars":
                    stats.avatars_bytes = category_bytes
                
                stats.file_count += category_files
            
            # Calculate total
            stats.total_bytes = (stats.uploads_bytes + stats.templates_bytes + 
                               stats.exports_bytes + stats.avatars_bytes)
            
            # Check for orphaned files
            if self.db:
                orphaned_result = self._calculate_orphaned_storage()
                stats.orphaned_bytes = orphaned_result["size"]
                stats.orphaned_count = orphaned_result["count"]
            
            self.logger.info(f"Storage usage calculated: {stats.total_bytes} bytes across {stats.file_count} files")
            
        except Exception as e:
            self.logger.error(f"Failed to calculate storage usage: {e}")
        
        return stats

    def _calculate_orphaned_storage(self) -> Dict[str, int]:
        """
        Calculate size and count of orphaned files.
        
        Returns:
            Dictionary with size and count of orphaned files
        """
        if not self.db:
            return {"size": 0, "count": 0}
        
        try:
            # Get all file references from database
            db_file_paths = set()
            
            file_uploads = self.db.query(FileUpload).all()
            for upload in file_uploads:
                db_file_paths.add(upload.file_path)
            
            avatars = self.db.query(UserAvatar).all()
            for avatar in avatars:
                db_file_paths.add(avatar.file_path)
            
            # Count orphaned files
            orphaned_size = 0
            orphaned_count = 0
            
            for storage_path in self.storage_paths.values():
                if not storage_path.exists():
                    continue
                    
                for file_path in storage_path.rglob("*"):
                    if file_path.is_file():
                        file_path_str = str(file_path)
                        
                        if file_path_str not in db_file_paths:
                            try:
                                orphaned_size += file_path.stat().st_size
                                orphaned_count += 1
                            except OSError:
                                pass
            
            return {"size": orphaned_size, "count": orphaned_count}
            
        except Exception as e:
            self.logger.error(f"Failed to calculate orphaned storage: {e}")
            return {"size": 0, "count": 0}

    async def cleanup_expired_files_async(self, max_age_hours: int = 24, category: str = None) -> CleanupOperationResult:
        """
        Asynchronous version of cleanup_expired_files.
        
        Args:
            max_age_hours: Maximum age in hours before deletion
            category: File category to clean (None for all categories)
            
        Returns:
            CleanupOperationResult with cleanup metrics
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, 
            self.cleanup_expired_files, 
            max_age_hours, 
            category
        )
        return result

    async def cleanup_orphaned_files_async(self) -> CleanupOperationResult:
        """
        Asynchronous version of cleanup_orphaned_files.
        
        Returns:
            CleanupOperationResult with orphaned file cleanup metrics
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self.cleanup_orphaned_files
        )
        return result

    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information or None if file not found
        """
        try:
            path = Path(file_path)
            if not path.exists() or not path.is_file():
                return None
            
            stat = path.stat()
            
            return {
                "path": str(path),
                "name": path.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "mime_type": mimetypes.guess_type(str(path))[0],
                "category": self._get_file_category(path),
                "exists_in_db": self._check_file_in_database(str(path))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get file info for {file_path}: {e}")
            return None

    def _get_file_category(self, file_path: Path) -> Optional[str]:
        """
        Determine which category a file belongs to based on its path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Category name or None if not in a managed category
        """
        try:
            for category, category_path in self.storage_paths.items():
                if file_path.is_relative_to(category_path):
                    return category
        except:
            pass
        return None

    def _check_file_in_database(self, file_path: str) -> bool:
        """
        Check if file is referenced in database.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is referenced in database, False otherwise
        """
        if not self.db:
            return False
        
        try:
            # Check FileUpload table
            upload_exists = self.db.query(FileUpload).filter(
                FileUpload.file_path == file_path
            ).first()
            
            if upload_exists:
                return True
            
            # Check UserAvatar table
            avatar_exists = self.db.query(UserAvatar).filter(
                UserAvatar.file_path == file_path
            ).first()
            
            return avatar_exists is not None
            
        except Exception as e:
            self.logger.error(f"Failed to check file in database {file_path}: {e}")
            return False

    def optimize_storage(self) -> CleanupOperationResult:
        """
        Perform comprehensive storage optimization.
        
        Combines expired file cleanup, orphaned file cleanup, and other optimizations.
        
        Returns:
            CleanupOperationResult with optimization metrics
        """
        start_time = datetime.now()
        result = CleanupOperationResult(operation_type="storage_optimization")
        
        try:
            # Clean expired files (older than 24 hours for temp files)
            expired_result = self.cleanup_expired_files(max_age_hours=24, category="temp")
            result.deleted_files_count += expired_result.deleted_files_count
            result.freed_bytes += expired_result.freed_bytes
            result.error_count += expired_result.error_count
            result.errors.extend(expired_result.errors)
            
            # Clean orphaned files
            orphaned_result = self.cleanup_orphaned_files()
            result.orphaned_files_count += orphaned_result.orphaned_files_count
            result.freed_bytes += orphaned_result.freed_bytes
            result.error_count += orphaned_result.error_count
            result.errors.extend(orphaned_result.errors)
            
            # Clean old quarantine files (older than 7 days)
            quarantine_path = self.base_path / "quarantine"
            if quarantine_path.exists():
                cutoff_time = datetime.now() - timedelta(days=7)
                for file_path in quarantine_path.rglob("*"):
                    if file_path.is_file():
                        try:
                            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if mod_time < cutoff_time:
                                file_size = file_path.stat().st_size
                                file_path.unlink()
                                result.deleted_files_count += 1
                                result.freed_bytes += file_size
                        except Exception as e:
                            result.error_count += 1
                            result.errors.append(f"Failed to clean quarantine file {file_path}: {str(e)}")
            
            result.success = result.error_count == 0
            
            self.logger.info(f"Storage optimization completed: {result.deleted_files_count} files deleted, "
                           f"{result.orphaned_files_count} orphaned, {result.freed_bytes} bytes freed")
            
        except Exception as e:
            result.success = False
            result.error_count += 1
            result.errors.append(f"Storage optimization failed: {str(e)}")
            self.logger.error(f"Storage optimization failed: {e}")
        
        result.execution_time_seconds = (datetime.now() - start_time).total_seconds()
        return result

    def __del__(self):
        """Cleanup executor on destruction."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
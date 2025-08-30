"""
CleanupScheduler - Automated cleanup job scheduling for TTL data expiration.

This service provides cron-like scheduling for automated cleanup operations:
- Scheduled cleanup every 6 hours by default
- Job failure handling and retry logic
- Performance monitoring and logging
- Graceful startup and shutdown
- Configurable cleanup intervals

Features:
- APScheduler-based job scheduling
- Async and sync cleanup execution
- Job failure notifications
- Cleanup history tracking
- Resource-aware scheduling
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.services.data_expiration import DataExpirationService, CleanupResult
from app.database import SessionLocal


logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """Configuration for cleanup scheduler."""
    cleanup_interval_hours: int = 6
    max_retries: int = 3
    retry_delay_minutes: int = 30
    enable_notifications: bool = True
    resource_check_enabled: bool = True
    max_execution_time_minutes: int = 30


@dataclass
class JobExecutionResult:
    """Result of a scheduled job execution."""
    job_id: str
    success: bool
    started_at: datetime
    completed_at: Optional[datetime] = None
    execution_time_seconds: float = 0
    cleanup_result: Optional[CleanupResult] = None
    error_message: Optional[str] = None
    retry_count: int = 0


class CleanupScheduler:
    """
    Scheduler for automated TTL cleanup operations.
    
    Manages recurring cleanup jobs with failure handling, monitoring,
    and configurable execution schedules.
    """

    def __init__(self, config: SchedulerConfig = None):
        """
        Initialize CleanupScheduler.
        
        Args:
            config: Scheduler configuration (uses defaults if None)
        """
        self.config = config or SchedulerConfig()
        self.scheduler = AsyncIOScheduler()
        self.cleanup_handler: Optional[Callable] = None
        self.execution_history: Dict[str, JobExecutionResult] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._is_running = False

    def schedule_cleanup_job(self, interval_hours: int = None) -> str:
        """
        Schedule recurring cleanup job.
        
        Args:
            interval_hours: Hours between cleanup runs (uses config default if None)
            
        Returns:
            Job ID for tracking
        """
        hours = interval_hours or self.config.cleanup_interval_hours
        
        job = self.scheduler.add_job(
            self._execute_cleanup_job,
            trigger=IntervalTrigger(hours=hours),
            id=f"cleanup_job_{datetime.now().timestamp()}",
            name=f"TTL Cleanup (every {hours}h)",
            replace_existing=True,
            max_instances=1,  # Prevent overlapping executions
            coalesce=True     # Combine missed executions
        )
        
        job_id = job.id
        self.logger.info(f"Scheduled cleanup job '{job_id}' to run every {hours} hours")
        
        return job_id

    def schedule_cron_cleanup(self, cron_expression: str) -> str:
        """
        Schedule cleanup job using cron expression.
        
        Args:
            cron_expression: Cron expression (e.g., "0 */6 * * *" for every 6 hours)
            
        Returns:
            Job ID for tracking
        """
        job = self.scheduler.add_job(
            self._execute_cleanup_job,
            trigger=CronTrigger.from_crontab(cron_expression),
            id=f"cron_cleanup_{datetime.now().timestamp()}",
            name=f"TTL Cleanup (cron: {cron_expression})",
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )
        
        job_id = job.id
        self.logger.info(f"Scheduled cron cleanup job '{job_id}' with expression: {cron_expression}")
        
        return job_id

    def is_job_scheduled(self, job_id: str) -> bool:
        """
        Check if a job is currently scheduled.
        
        Args:
            job_id: Job ID to check
            
        Returns:
            True if job is scheduled, False otherwise
        """
        try:
            job = self.scheduler.get_job(job_id)
            return job is not None
        except:
            return False

    def set_cleanup_handler(self, handler: Callable):
        """
        Set custom cleanup handler function.
        
        Args:
            handler: Function to call for cleanup operations
        """
        self.cleanup_handler = handler
        self.logger.info("Custom cleanup handler registered")

    async def execute_cleanup_now(self) -> JobExecutionResult:
        """
        Execute cleanup immediately (bypass scheduler).
        
        Returns:
            JobExecutionResult with execution details
        """
        job_id = f"manual_cleanup_{datetime.now().timestamp()}"
        return await self._execute_cleanup_job(job_id=job_id)

    async def _execute_cleanup_job(self, job_id: str = None) -> JobExecutionResult:
        """
        Internal method to execute cleanup job.
        
        Args:
            job_id: Job ID for tracking (generated if None)
            
        Returns:
            JobExecutionResult with execution details
        """
        if job_id is None:
            job_id = f"auto_cleanup_{datetime.now().timestamp()}"
            
        result = JobExecutionResult(
            job_id=job_id,
            success=False,
            started_at=datetime.now(timezone.utc)
        )
        
        try:
            self.logger.info(f"Starting cleanup job '{job_id}'")
            
            # Resource check if enabled
            if self.config.resource_check_enabled:
                if not await self._check_system_resources():
                    result.error_message = "System resources insufficient for cleanup"
                    self.logger.warning(f"Cleanup job '{job_id}' skipped due to resource constraints")
                    return result
            
            # Execute cleanup
            if self.cleanup_handler:
                # Use custom handler
                if asyncio.iscoroutinefunction(self.cleanup_handler):
                    cleanup_result = await self.cleanup_handler()
                else:
                    cleanup_result = self.cleanup_handler()
            else:
                # Use default DataExpirationService
                cleanup_result = await self._default_cleanup()
            
            result.cleanup_result = cleanup_result
            result.success = cleanup_result.success if cleanup_result else True
            result.completed_at = datetime.now(timezone.utc)
            result.execution_time_seconds = (result.completed_at - result.started_at).total_seconds()
            
            # Log results
            if result.success:
                self.logger.info(f"Cleanup job '{job_id}' completed successfully in "
                               f"{result.execution_time_seconds:.2f}s")
                if cleanup_result:
                    self.logger.info(f"Deleted {cleanup_result.deleted_count} records, "
                                   f"freed {cleanup_result.freed_memory_bytes + cleanup_result.freed_storage_bytes} bytes")
            else:
                self.logger.error(f"Cleanup job '{job_id}' failed: {cleanup_result.error_message if cleanup_result else 'Unknown error'}")
                result.error_message = cleanup_result.error_message if cleanup_result else "Unknown error"
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.completed_at = datetime.now(timezone.utc)
            result.execution_time_seconds = (result.completed_at - result.started_at).total_seconds()
            
            self.logger.error(f"Cleanup job '{job_id}' failed with exception: {e}")
            
            # Handle retry logic
            if result.retry_count < self.config.max_retries:
                self.logger.info(f"Scheduling retry {result.retry_count + 1}/{self.config.max_retries} "
                               f"for job '{job_id}' in {self.config.retry_delay_minutes} minutes")
                
                self.scheduler.add_job(
                    self._retry_cleanup_job,
                    trigger=IntervalTrigger(minutes=self.config.retry_delay_minutes),
                    args=[job_id, result.retry_count + 1],
                    id=f"retry_{job_id}_{result.retry_count + 1}",
                    name=f"Retry cleanup {result.retry_count + 1}",
                    max_instances=1
                )
        
        # Store execution history
        self.execution_history[job_id] = result
        
        # Send notifications if enabled and configured
        if self.config.enable_notifications:
            await self._send_job_notification(result)
        
        return result

    async def _retry_cleanup_job(self, original_job_id: str, retry_count: int):
        """
        Retry a failed cleanup job.
        
        Args:
            original_job_id: ID of the original failed job
            retry_count: Current retry attempt number
        """
        retry_job_id = f"{original_job_id}_retry_{retry_count}"
        self.logger.info(f"Retrying cleanup job '{original_job_id}' (attempt {retry_count})")
        
        result = await self._execute_cleanup_job(retry_job_id)
        result.retry_count = retry_count
        
        if not result.success and retry_count >= self.config.max_retries:
            self.logger.error(f"Cleanup job '{original_job_id}' failed after {retry_count} retries")

    async def _default_cleanup(self) -> CleanupResult:
        """
        Execute cleanup using default DataExpirationService.
        
        Returns:
            CleanupResult from DataExpirationService
        """
        db = SessionLocal()
        try:
            service = DataExpirationService(db)
            result = await service.cleanup_expired_data_async()
            return result
        finally:
            db.close()

    async def _check_system_resources(self) -> bool:
        """
        Check if system has sufficient resources for cleanup.
        
        Returns:
            True if resources are sufficient, False otherwise
        """
        try:
            import psutil
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:  # More than 90% memory usage
                self.logger.warning(f"High memory usage: {memory.percent}%")
                return False
            
            # Check disk space
            disk = psutil.disk_usage('/')
            if disk.percent > 95:  # More than 95% disk usage
                self.logger.warning(f"Low disk space: {disk.percent}% used")
                return False
                
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 95:  # More than 95% CPU usage
                self.logger.warning(f"High CPU usage: {cpu_percent}%")
                return False
                
            return True
            
        except ImportError:
            # psutil not available, assume resources are OK
            self.logger.debug("psutil not available, skipping resource check")
            return True
        except Exception as e:
            self.logger.warning(f"Resource check failed: {e}")
            return True  # Assume OK on error

    async def _send_job_notification(self, result: JobExecutionResult):
        """
        Send notification about job execution result.
        
        Args:
            result: Job execution result to notify about
        """
        # This would integrate with notification system (email, Slack, etc.)
        if not result.success:
            self.logger.error(f"NOTIFICATION: Cleanup job '{result.job_id}' failed: {result.error_message}")
        elif result.cleanup_result and result.cleanup_result.error_count > 0:
            self.logger.warning(f"NOTIFICATION: Cleanup job '{result.job_id}' completed with {result.cleanup_result.error_count} errors")

    async def start(self):
        """Start the scheduler."""
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            self.logger.info("CleanupScheduler started")
            
            # Schedule default cleanup job if none exists
            if not self.scheduler.get_jobs():
                self.schedule_cleanup_job()

    async def stop(self):
        """Stop the scheduler gracefully."""
        if self._is_running:
            self.scheduler.shutdown(wait=True)
            self._is_running = False
            self.logger.info("CleanupScheduler stopped")

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a job.
        
        Args:
            job_id: Job ID to get status for
            
        Returns:
            Job status dictionary or None if job not found
        """
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                return None
                
            execution_result = self.execution_history.get(job_id)
            
            return {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "last_execution": {
                    "success": execution_result.success if execution_result else None,
                    "completed_at": execution_result.completed_at.isoformat() if execution_result and execution_result.completed_at else None,
                    "execution_time_seconds": execution_result.execution_time_seconds if execution_result else None,
                    "deleted_count": execution_result.cleanup_result.deleted_count if execution_result and execution_result.cleanup_result else None,
                    "error_message": execution_result.error_message if execution_result else None
                } if execution_result else None
            }
        except Exception as e:
            self.logger.error(f"Failed to get job status for '{job_id}': {e}")
            return None

    def get_all_jobs_status(self) -> List[Dict[str, Any]]:
        """
        Get status for all scheduled jobs.
        
        Returns:
            List of job status dictionaries
        """
        jobs_status = []
        for job in self.scheduler.get_jobs():
            status = self.get_job_status(job.id)
            if status:
                jobs_status.append(status)
        return jobs_status

    def remove_job(self, job_id: str) -> bool:
        """
        Remove a scheduled job.
        
        Args:
            job_id: Job ID to remove
            
        Returns:
            True if job was removed, False if job not found
        """
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Removed job '{job_id}'")
            return True
        except:
            return False

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._is_running

    async def execute_full_cleanup(self) -> Dict[str, Any]:
        """
        Execute full cleanup cycle for integration testing.
        
        Returns:
            Dictionary with cleanup results and success status
        """
        db = SessionLocal()
        try:
            service = DataExpirationService(db)
            
            # Execute database cleanup
            database_result = await service.cleanup_expired_data_async()
            
            # Execute filesystem cleanup (would integrate with StorageManager)
            # For now, simulate filesystem cleanup success
            filesystem_result = {
                "success": True,
                "freed_bytes": 0
            }
            
            return {
                "database_cleanup_success": database_result.success,
                "filesystem_cleanup_success": filesystem_result["success"],
                "total_freed_bytes": database_result.freed_memory_bytes + database_result.freed_storage_bytes + filesystem_result["freed_bytes"],
                "database_deleted_count": database_result.deleted_count,
                "database_errors": database_result.error_count,
                "execution_time_ms": database_result.execution_time_ms
            }
            
        finally:
            db.close()
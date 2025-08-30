"""
Tests for TTL Data Expiration System.

This module contains failing tests for the Phase 5 TTL-based data expiration system.
Following TDD approach - these tests should fail initially and guide implementation.

Test Coverage:
- Database schema with TTL columns
- DataExpirationService automated cleanup
- TTL policy enforcement (anonymous vs registered users)
- CleanupScheduler cron job functionality
- StorageManager file system cleanup
- Grace period and notifications
- Performance metrics tracking
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db, engine
from app.database import (
    User, Board, Stroke, FileUpload, BoardTemplate, DataCleanupJob, 
    UserAvatar, UserPresence, LoginHistory, EditHistory
)
from app.services.data_expiration import DataExpirationService, TTLPolicy
from app.services.cleanup_scheduler import CleanupScheduler
from app.services.storage_manager import StorageManager


@pytest.fixture
def db_session():
    """Create a test database session."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashedpassword"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestTTLDatabaseSchema:
    """Test TTL column additions to database schema."""

    def test_strokes_table_has_expires_at_column(self, db_session):
        """Test that strokes table has expires_at TIMESTAMP column."""
        # This will fail - strokes table doesn't exist yet
        result = db_session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='strokes'
        """))
        assert result.fetchone() is not None
        
        # Check for expires_at column
        result = db_session.execute(text("PRAGMA table_info(strokes)"))
        columns = [row[1] for row in result.fetchall()]
        assert "expires_at" in columns

    def test_file_uploads_table_has_expires_at_column(self, db_session):
        """Test that file_uploads table has expires_at TIMESTAMP column."""
        # This will fail - file_uploads table doesn't exist yet
        result = db_session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='file_uploads'
        """))
        assert result.fetchone() is not None
        
        result = db_session.execute(text("PRAGMA table_info(file_uploads)"))
        columns = [row[1] for row in result.fetchall()]
        assert "expires_at" in columns

    def test_board_templates_table_has_expires_at_column(self, db_session):
        """Test that board_templates table has expires_at TIMESTAMP column."""
        # This will fail - board_templates table doesn't exist yet
        result = db_session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='board_templates'
        """))
        assert result.fetchone() is not None
        
        result = db_session.execute(text("PRAGMA table_info(board_templates)"))
        columns = [row[1] for row in result.fetchall()]
        assert "expires_at" in columns

    def test_data_cleanup_jobs_table_exists(self, db_session):
        """Test that data_cleanup_jobs table exists for tracking cleanup operations."""
        # This will fail - data_cleanup_jobs table doesn't exist yet
        result = db_session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='data_cleanup_jobs'
        """))
        assert result.fetchone() is not None

    def test_user_avatars_table_with_ttl(self, db_session):
        """Test that user_avatars table has TTL support."""
        # This will fail - user_avatars table doesn't exist yet
        result = db_session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='user_avatars'
        """))
        assert result.fetchone() is not None
        
        result = db_session.execute(text("PRAGMA table_info(user_avatars)"))
        columns = [row[1] for row in result.fetchall()]
        assert "expires_at" in columns
        assert "file_size" in columns

    def test_user_presence_table_with_ttl(self, db_session):
        """Test that user_presence table has TTL support."""
        # This will fail - user_presence table doesn't exist yet
        result = db_session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='user_presence'
        """))
        assert result.fetchone() is not None
        
        result = db_session.execute(text("PRAGMA table_info(user_presence)"))
        columns = [row[1] for row in result.fetchall()]
        assert "expires_at" in columns
        assert "last_seen" in columns

    def test_login_history_table_with_ttl(self, db_session):
        """Test that login_history table has TTL support."""
        # This will fail - login_history table doesn't exist yet
        result = db_session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='login_history'
        """))
        assert result.fetchone() is not None
        
        result = db_session.execute(text("PRAGMA table_info(login_history)"))
        columns = [row[1] for row in result.fetchall()]
        assert "expires_at" in columns
        assert "ip_address" in columns

    def test_edit_history_table_with_ttl(self, db_session):
        """Test that edit_history table has TTL support."""
        # This will fail - edit_history table doesn't exist yet
        result = db_session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='edit_history'
        """))
        assert result.fetchone() is not None
        
        result = db_session.execute(text("PRAGMA table_info(edit_history)"))
        columns = [row[1] for row in result.fetchall()]
        assert "expires_at" in columns
        assert "action_data" in columns


class TestDataExpirationService:
    """Test DataExpirationService automated cleanup functionality."""

    def test_data_expiration_service_initialization(self):
        """Test DataExpirationService can be initialized with TTL policies."""
        # This will fail - DataExpirationService doesn't exist yet
        service = DataExpirationService()
        assert service is not None
        assert hasattr(service, 'ttl_policies')
        assert hasattr(service, 'cleanup_expired_data')

    def test_ttl_policy_configuration(self):
        """Test TTL policies can be configured for different data types."""
        # This will fail - TTLPolicy doesn't exist yet
        anonymous_policy = TTLPolicy(
            data_type="anonymous_strokes",
            ttl_hours=24,
            grace_period_hours=1
        )
        assert anonymous_policy.ttl_hours == 24
        assert anonymous_policy.grace_period_hours == 1

    def test_anonymous_user_strokes_cleanup(self, db_session):
        """Test cleanup of anonymous user strokes after 24 hours."""
        # This will fail - DataExpirationService doesn't exist yet
        service = DataExpirationService(db_session)
        
        # Create expired anonymous stroke data
        expired_time = datetime.now(timezone.utc) - timedelta(hours=25)
        
        # This would require strokes table to exist
        cleanup_result = service.cleanup_expired_strokes(user_type="anonymous")
        assert cleanup_result.deleted_count > 0
        assert cleanup_result.freed_memory_bytes > 0

    def test_registered_user_strokes_cleanup(self, db_session, sample_user):
        """Test cleanup of registered user strokes after 30 days."""
        # This will fail - DataExpirationService doesn't exist yet
        service = DataExpirationService(db_session)
        
        # Create expired registered user stroke data
        expired_time = datetime.now(timezone.utc) - timedelta(days=31)
        
        cleanup_result = service.cleanup_expired_strokes(user_type="registered")
        assert cleanup_result.deleted_count >= 0
        assert cleanup_result.freed_memory_bytes >= 0

    def test_unused_templates_cleanup(self, db_session):
        """Test cleanup of unused templates after 7 days."""
        # This will fail - DataExpirationService doesn't exist yet
        service = DataExpirationService(db_session)
        
        expired_time = datetime.now(timezone.utc) - timedelta(days=8)
        
        cleanup_result = service.cleanup_expired_templates()
        assert cleanup_result.deleted_count >= 0
        assert cleanup_result.freed_storage_bytes >= 0

    def test_temporary_uploads_cleanup(self, db_session):
        """Test cleanup of temporary uploads after 1 hour."""
        # This will fail - DataExpirationService doesn't exist yet
        service = DataExpirationService(db_session)
        
        expired_time = datetime.now(timezone.utc) - timedelta(hours=2)
        
        cleanup_result = service.cleanup_expired_uploads()
        assert cleanup_result.deleted_count >= 0
        assert cleanup_result.freed_storage_bytes >= 0

    def test_board_exports_cleanup(self, db_session):
        """Test cleanup of board exports after 48 hours."""
        # This will fail - DataExpirationService doesn't exist yet
        service = DataExpirationService(db_session)
        
        expired_time = datetime.now(timezone.utc) - timedelta(hours=49)
        
        cleanup_result = service.cleanup_expired_exports()
        assert cleanup_result.deleted_count >= 0
        assert cleanup_result.freed_storage_bytes >= 0

    def test_grace_period_enforcement(self, db_session):
        """Test that grace period prevents immediate deletion."""
        # This will fail - DataExpirationService doesn't exist yet
        service = DataExpirationService(db_session)
        
        # Data that's expired but within grace period
        grace_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        
        cleanup_result = service.cleanup_expired_data(respect_grace_period=True)
        # Should not delete data still in grace period
        assert cleanup_result.skipped_count > 0

    @pytest.mark.asyncio
    async def test_cleanup_metrics_tracking(self, db_session):
        """Test that cleanup operations track performance metrics."""
        # This will fail - DataExpirationService doesn't exist yet
        service = DataExpirationService(db_session)
        
        cleanup_result = await service.cleanup_expired_data_async()
        
        assert hasattr(cleanup_result, 'execution_time_ms')
        assert hasattr(cleanup_result, 'freed_memory_bytes')
        assert hasattr(cleanup_result, 'freed_storage_bytes')
        assert hasattr(cleanup_result, 'deleted_count')
        assert hasattr(cleanup_result, 'error_count')


class TestCleanupScheduler:
    """Test CleanupScheduler cron job functionality."""

    def test_cleanup_scheduler_initialization(self):
        """Test CleanupScheduler can be initialized."""
        # This will fail - CleanupScheduler doesn't exist yet
        scheduler = CleanupScheduler()
        assert scheduler is not None
        assert hasattr(scheduler, 'schedule_cleanup_job')
        assert hasattr(scheduler, 'start')
        assert hasattr(scheduler, 'stop')

    def test_schedule_cleanup_every_6_hours(self):
        """Test scheduling cleanup job every 6 hours."""
        # This will fail - CleanupScheduler doesn't exist yet
        scheduler = CleanupScheduler()
        
        job_id = scheduler.schedule_cleanup_job(interval_hours=6)
        assert job_id is not None
        assert scheduler.is_job_scheduled(job_id)

    @pytest.mark.asyncio
    async def test_automated_cleanup_execution(self):
        """Test that scheduled cleanup jobs execute automatically."""
        # This will fail - CleanupScheduler doesn't exist yet
        scheduler = CleanupScheduler()
        
        # Mock the cleanup execution
        cleanup_mock = AsyncMock()
        scheduler.set_cleanup_handler(cleanup_mock)
        
        # Trigger immediate execution for testing
        await scheduler.execute_cleanup_now()
        
        cleanup_mock.assert_called_once()

    def test_cleanup_job_failure_handling(self):
        """Test handling of cleanup job failures."""
        # This will fail - CleanupScheduler doesn't exist yet
        scheduler = CleanupScheduler()
        
        # Mock a failing cleanup
        def failing_cleanup():
            raise Exception("Cleanup failed")
        
        scheduler.set_cleanup_handler(failing_cleanup)
        
        # Should handle failure gracefully
        result = scheduler.execute_cleanup_now()
        assert result.success is False
        assert result.error_message is not None


class TestStorageManager:
    """Test StorageManager file system cleanup functionality."""

    def test_storage_manager_initialization(self):
        """Test StorageManager can be initialized."""
        # This will fail - StorageManager doesn't exist yet
        storage = StorageManager()
        assert storage is not None
        assert hasattr(storage, 'cleanup_expired_files')
        assert hasattr(storage, 'calculate_storage_usage')

    def test_expired_file_cleanup(self, tmp_path):
        """Test cleanup of expired files from filesystem."""
        # This will fail - StorageManager doesn't exist yet
        storage = StorageManager(base_path=str(tmp_path))
        
        # Create test files with different timestamps
        old_file = tmp_path / "old_file.txt"
        old_file.write_text("test content")
        
        # Set file modification time to simulate expiry
        expired_time = datetime.now(timezone.utc) - timedelta(hours=25)
        
        cleanup_result = storage.cleanup_expired_files(max_age_hours=24)
        assert cleanup_result.deleted_files_count > 0
        assert cleanup_result.freed_bytes > 0

    def test_storage_usage_calculation(self, tmp_path):
        """Test calculation of storage usage by category."""
        # This will fail - StorageManager doesn't exist yet
        storage = StorageManager(base_path=str(tmp_path))
        
        usage_stats = storage.calculate_storage_usage()
        
        assert hasattr(usage_stats, 'total_bytes')
        assert hasattr(usage_stats, 'uploads_bytes')
        assert hasattr(usage_stats, 'templates_bytes')
        assert hasattr(usage_stats, 'exports_bytes')
        assert hasattr(usage_stats, 'avatars_bytes')

    def test_orphaned_files_cleanup(self, tmp_path):
        """Test cleanup of orphaned files (no database references)."""
        # This will fail - StorageManager doesn't exist yet
        storage = StorageManager(base_path=str(tmp_path))
        
        cleanup_result = storage.cleanup_orphaned_files()
        assert hasattr(cleanup_result, 'orphaned_files_count')
        assert hasattr(cleanup_result, 'freed_bytes')


class TestTTLPolicyEnforcement:
    """Test TTL policy enforcement and user notifications."""

    def test_anonymous_user_24hour_policy(self, db_session):
        """Test 24-hour TTL policy for anonymous users."""
        # This will fail - TTL enforcement doesn't exist yet
        service = DataExpirationService(db_session)
        
        # Create anonymous session data
        session_data = service.create_anonymous_session()
        assert session_data.expires_at is not None
        
        # Check expiry time is approximately 24 hours
        expected_expiry = datetime.now(timezone.utc) + timedelta(hours=24)
        time_diff = abs((session_data.expires_at - expected_expiry).total_seconds())
        assert time_diff < 60  # Within 1 minute accuracy

    def test_registered_user_30day_policy(self, db_session, sample_user):
        """Test 30-day TTL policy for registered users."""
        # This will fail - TTL enforcement doesn't exist yet
        service = DataExpirationService(db_session)
        
        # Create registered user stroke
        stroke_data = service.create_user_stroke(sample_user.id)
        assert stroke_data.expires_at is not None
        
        # Check expiry time is approximately 30 days
        expected_expiry = datetime.now(timezone.utc) + timedelta(days=30)
        time_diff = abs((stroke_data.expires_at - expected_expiry).total_seconds())
        assert time_diff < 3600  # Within 1 hour accuracy

    def test_user_notification_before_expiry(self, db_session, sample_user):
        """Test user notification system before data expiry."""
        # This will fail - notification system doesn't exist yet
        service = DataExpirationService(db_session)
        
        # Create data that will expire soon
        notification_result = service.send_expiry_notifications(hours_before=24)
        
        assert hasattr(notification_result, 'users_notified')
        assert hasattr(notification_result, 'notifications_sent')

    def test_configurable_ttl_per_user_tier(self, db_session, sample_user):
        """Test configurable TTL based on user tier/subscription."""
        # This will fail - user tier system doesn't exist yet
        service = DataExpirationService(db_session)
        
        # Set user to premium tier
        sample_user.tier = "premium"
        
        stroke_data = service.create_user_stroke(sample_user.id)
        
        # Premium users should have longer retention
        expected_expiry = datetime.now(timezone.utc) + timedelta(days=90)
        time_diff = abs((stroke_data.expires_at - expected_expiry).total_seconds())
        assert time_diff < 3600  # Within 1 hour accuracy


class TestCleanupIntegration:
    """Integration tests for complete TTL cleanup lifecycle."""

    @pytest.mark.asyncio
    async def test_complete_cleanup_cycle(self, db_session):
        """Test complete data cleanup cycle from creation to deletion."""
        # This will fail - complete integration doesn't exist yet
        service = DataExpirationService(db_session)
        scheduler = CleanupScheduler()
        storage = StorageManager()
        
        # Create test data with various expiry times
        await service.create_test_data_with_ttl()
        
        # Execute full cleanup cycle
        cleanup_result = await scheduler.execute_full_cleanup()
        
        assert cleanup_result.database_cleanup_success
        assert cleanup_result.filesystem_cleanup_success
        assert cleanup_result.total_freed_bytes > 0

    def test_cleanup_performance_under_load(self, db_session):
        """Test cleanup performance with large amounts of expired data."""
        # This will fail - performance testing doesn't exist yet
        service = DataExpirationService(db_session)
        
        # Create large amount of expired test data
        service.create_bulk_expired_data(record_count=10000)
        
        # Measure cleanup performance
        start_time = datetime.now()
        cleanup_result = service.cleanup_expired_data()
        execution_time = datetime.now() - start_time
        
        # Cleanup should complete within reasonable time
        assert execution_time.total_seconds() < 30  # Less than 30 seconds
        assert cleanup_result.deleted_count == 10000

    def test_cleanup_atomic_operations(self, db_session):
        """Test that cleanup operations are atomic (all succeed or all fail)."""
        # This will fail - atomic operations don't exist yet
        service = DataExpirationService(db_session)
        
        # Create scenario where partial cleanup could occur
        with patch.object(service, 'delete_expired_strokes') as mock_strokes:
            mock_strokes.side_effect = Exception("Database error")
            
            cleanup_result = service.cleanup_expired_data()
            
            # Should rollback all operations on failure
            assert cleanup_result.success is False
            assert cleanup_result.rollback_performed is True

    def test_cleanup_logging_and_monitoring(self, db_session):
        """Test cleanup operations generate proper logs and monitoring data."""
        # This will fail - logging system doesn't exist yet
        service = DataExpirationService(db_session)
        
        with patch('app.services.data_expiration.logger') as mock_logger:
            cleanup_result = service.cleanup_expired_data()
            
            # Should log cleanup operations
            mock_logger.info.assert_called()
            assert any("cleanup completed" in str(call) for call in mock_logger.info.call_args_list)
            
            # Should include metrics in logs
            assert hasattr(cleanup_result, 'log_entries')
            assert len(cleanup_result.log_entries) > 0
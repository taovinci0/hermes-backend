"""Tests for BacktestService."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import date

from api.services.backtest_service import BacktestService
from api.utils.job_queue import JobStatus


class TestBacktestService:
    """Test BacktestService functionality."""
    
    @pytest.mark.asyncio
    async def test_start_backtest(self):
        """Test starting a backtest job."""
        service = BacktestService()
        
        with patch.object(service.job_queue, "create_job") as mock_create:
            with patch.object(service.job_queue, "run_job") as mock_run:
                mock_create.return_value = "test-job-id"
                
                job_id = await service.start_backtest(
                    start_date=date(2025, 11, 10),
                    end_date=date(2025, 11, 11),
                    stations=["EGLC"],
                )
                
                assert job_id == "test-job-id"
                assert mock_create.called
                assert mock_run.called
    
    @pytest.mark.asyncio
    async def test_get_job_status(self):
        """Test getting job status."""
        service = BacktestService()
        
        from api.utils.job_queue import Job
        
        mock_job = Job(
            job_id="test-job-id",
            job_type="backtest",
            status=JobStatus.RUNNING,
        )
        
        with patch.object(service.job_queue, "get_job", return_value=mock_job):
            status = await service.get_job_status("test-job-id")
            
            assert status is not None
            assert status["job_id"] == "test-job-id"
            assert status["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self):
        """Test getting status for non-existent job."""
        service = BacktestService()
        
        with patch.object(service.job_queue, "get_job", return_value=None):
            status = await service.get_job_status("non-existent")
            
            assert status is None
    
    @pytest.mark.asyncio
    async def test_get_job_results_completed(self):
        """Test getting results for completed job."""
        service = BacktestService()
        
        from api.utils.job_queue import Job
        
        mock_job = Job(
            job_id="test-job-id",
            job_type="backtest",
            status=JobStatus.COMPLETED,
            result={"output_path": "data/runs/backtest.csv", "summary": {}},
        )
        
        with patch.object(service.job_queue, "get_job", return_value=mock_job):
            results = await service.get_job_results("test-job-id")
            
            assert results is not None
            assert results["status"] == "completed"
            assert "result" in results
    
    @pytest.mark.asyncio
    async def test_get_job_results_pending(self):
        """Test getting results for pending job."""
        service = BacktestService()
        
        from api.utils.job_queue import Job
        
        mock_job = Job(
            job_id="test-job-id",
            job_type="backtest",
            status=JobStatus.PENDING,
        )
        
        with patch.object(service.job_queue, "get_job", return_value=mock_job):
            results = await service.get_job_results("test-job-id")
            
            assert results is not None
            assert results["status"] == "pending"


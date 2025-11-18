"""Service for running backtests via API."""

import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import date
import json

# Add project root to path to import agents
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.backtester import Backtester, BacktestSummary
from core.config import config
from ..utils.job_queue import JobQueue, JobStatus, job_queue


class BacktestService:
    """Service for running backtests via API."""
    
    def __init__(self):
        """Initialize backtest service."""
        self.job_queue = job_queue
    
    async def start_backtest(
        self,
        start_date: date,
        end_date: date,
        stations: list[str],
        bankroll_usd: Optional[float] = None,
        edge_min: Optional[float] = None,
        fee_bp: Optional[int] = None,
        slippage_bp: Optional[int] = None,
    ) -> str:
        """Start a backtest job.
        
        Args:
            start_date: Start date for backtest
            end_date: End date for backtest
            stations: List of station codes
            bankroll_usd: Optional bankroll override
            edge_min: Optional edge minimum override
            fee_bp: Optional fee override
            slippage_bp: Optional slippage override
            
        Returns:
            Job ID
        """
        # Create job
        job_id = await self.job_queue.create_job(
            job_type="backtest",
            metadata={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "stations": stations,
                "bankroll_usd": bankroll_usd,
                "edge_min": edge_min,
                "fee_bp": fee_bp,
                "slippage_bp": slippage_bp,
            },
        )
        
        # Run job in background
        asyncio.create_task(
            self.job_queue.run_job(
                job_id,
                self._run_backtest,
                start_date,
                end_date,
                stations,
                bankroll_usd,
                edge_min,
                fee_bp,
                slippage_bp,
            )
        )
        
        return job_id
    
    def _run_backtest(
        self,
        start_date: date,
        end_date: date,
        stations: list[str],
        bankroll_usd: Optional[float],
        edge_min: Optional[float],
        fee_bp: Optional[int],
        slippage_bp: Optional[int],
    ) -> Dict[str, Any]:
        """Run backtest (synchronous, called in background).
        
        Args:
            start_date: Start date
            end_date: End date
            stations: Station codes
            bankroll_usd: Optional bankroll
            edge_min: Optional edge minimum
            fee_bp: Optional fee
            slippage_bp: Optional slippage
            
        Returns:
            Result dictionary with output path and summary
        """
        # Initialize backtester with config or overrides
        backtester = Backtester(
            bankroll_usd=bankroll_usd or config.trading.daily_bankroll_cap,
            edge_min=edge_min or config.trading.edge_min,
            fee_bp=fee_bp or config.trading.fee_bp,
            slippage_bp=slippage_bp or config.trading.slippage_bp,
        )
        
        # Run backtest
        output_path = backtester.run(start_date, end_date, stations)
        
        # Read summary from output file
        summary = self._extract_summary(output_path)
        
        return {
            "output_path": str(output_path.relative_to(PROJECT_ROOT)),
            "summary": summary,
        }
    
    def _extract_summary(self, output_path: Path) -> Dict[str, Any]:
        """Extract summary from backtest output file.
        
        Args:
            output_path: Path to backtest results CSV
            
        Returns:
            Summary dictionary
        """
        summary = {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "pending": 0,
            "total_pnl": 0.0,
            "roi": 0.0,
        }
        
        if not output_path.exists():
            return summary
        
        try:
            import csv
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                trades = list(reader)
                
                summary["total_trades"] = len(trades)
                
                for trade in trades:
                    outcome = trade.get("outcome", "").lower()
                    if outcome == "win":
                        summary["wins"] += 1
                    elif outcome == "loss":
                        summary["losses"] += 1
                    elif outcome == "pending":
                        summary["pending"] += 1
                    
                    try:
                        pnl = float(trade.get("realized_pnl", 0))
                        summary["total_pnl"] += pnl
                    except (ValueError, TypeError):
                        pass
                
                # Calculate ROI
                total_risk = sum(
                    float(t.get("size_usd", 0))
                    for t in trades
                    if t.get("size_usd")
                )
                if total_risk > 0:
                    summary["roi"] = (summary["total_pnl"] / total_risk) * 100
                
                # Calculate hit rate
                resolved = summary["wins"] + summary["losses"]
                if resolved > 0:
                    summary["hit_rate"] = (summary["wins"] / resolved) * 100
                else:
                    summary["hit_rate"] = 0.0
        except Exception as e:
            summary["error"] = str(e)
        
        return summary
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status dictionary or None if not found
        """
        job = await self.job_queue.get_job(job_id)
        if not job:
            return None
        
        return {
            "job_id": job.job_id,
            "job_type": job.job_type,
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error": job.error,
            "progress": job.progress,
            "metadata": job.metadata,
        }
    
    async def get_job_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job results.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job results dictionary or None if not found/not completed
        """
        job = await self.job_queue.get_job(job_id)
        if not job:
            return None
        
        if job.status != JobStatus.COMPLETED:
            return {
                "status": job.status.value,
                "error": job.error,
            }
        
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "result": job.result,
        }


"""
CoinLink Parallel Processing Framework Integration

High-performance wrapper for the parallel processing framework,
optimized for CoinLink's multi-agent financial data processing needs.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
import time
import sys
import os

# Add parallel processing framework to path
framework_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'parallel-processing-framework')
sys.path.insert(0, framework_path)

from orchestrator.main import get_orchestrator, run_with_orchestrator
from core.interfaces import TaskPriority, TaskStatus
from core.circuit_breaker import get_circuit_breaker, CircuitBreakerConfig

logger = logging.getLogger(__name__)


class CoinLinkParallelProcessor:
    """
    CoinLink-optimized parallel processing wrapper
    
    Provides high-level methods for common CoinLink operations:
    - Multi-exchange price fetching
    - Portfolio calculations
    - Agent coordination
    - Real-time data streaming
    """
    
    def __init__(self, 
                 redis_url: Optional[str] = None,
                 min_workers: int = 4,
                 max_workers: int = 16,
                 use_uvloop: bool = True):
        self.orchestrator = get_orchestrator(
            redis_url=redis_url,
            min_workers=min_workers,
            max_workers=max_workers,
            use_uvloop=use_uvloop
        )
        self.is_running = False
        self.circuit_breakers = {}
        
        # Performance tracking
        self.operation_metrics = {
            'price_fetches': {'count': 0, 'avg_time': 0.0, 'errors': 0},
            'portfolio_calcs': {'count': 0, 'avg_time': 0.0, 'errors': 0},
            'agent_tasks': {'count': 0, 'avg_time': 0.0, 'errors': 0},
            'data_streams': {'count': 0, 'avg_time': 0.0, 'errors': 0}
        }
    
    async def start(self) -> None:
        """Start the parallel processing system"""
        if self.is_running:
            logger.warning("CoinLink parallel processor is already running")
            return
        
        logger.info("Starting CoinLink Parallel Processor...")
        await self.orchestrator.start()
        self.is_running = True
        
        # Initialize circuit breakers for external services
        await self._setup_circuit_breakers()
        
        logger.info("CoinLink Parallel Processor started successfully")
    
    async def stop(self) -> None:
        """Stop the parallel processing system"""
        if not self.is_running:
            return
        
        logger.info("Stopping CoinLink Parallel Processor...")
        await self.orchestrator.stop()
        self.is_running = False
        logger.info("CoinLink Parallel Processor stopped")
    
    async def _setup_circuit_breakers(self) -> None:
        """Initialize circuit breakers for external services"""
        # High-frequency, low-tolerance for price APIs
        self.circuit_breakers['binance'] = await get_circuit_breaker(
            "binance_api",
            CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30,
                half_open_max_calls=2
            )
        )
        
        # Standard tolerance for portfolio APIs
        self.circuit_breakers['coinbase'] = await get_circuit_breaker(
            "coinbase_api",
            CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60,
                half_open_max_calls=3
            )
        )
        
        # High tolerance for blockchain APIs (slower but more reliable)
        self.circuit_breakers['blockchain'] = await get_circuit_breaker(
            "blockchain_api",
            CircuitBreakerConfig(
                failure_threshold=10,
                recovery_timeout=120,
                half_open_max_calls=5
            )
        )
    
    async def fetch_multi_exchange_prices(self, 
                                        symbols: List[str],
                                        exchanges: List[str] = None,
                                        timeout: float = 2.0) -> Dict[str, Any]:
        """
        Fetch prices from multiple exchanges in parallel
        
        Args:
            symbols: List of trading pairs (e.g., ['BTC/USD', 'ETH/USD'])
            exchanges: List of exchanges to query (defaults to all supported)
            timeout: Maximum time to wait for results
            
        Returns:
            Dict with aggregated price data and metadata
        """
        start_time = time.time()
        
        try:
            if exchanges is None:
                exchanges = ['binance', 'coinbase', 'kraken']
            
            # Create tasks for each symbol-exchange combination
            tasks = []
            for symbol in symbols:
                for exchange in exchanges:
                    task_data = {'symbol': symbol, 'exchange': exchange}
                    tasks.append(task_data)
            
            # Submit with URGENT priority for real-time price data
            results = await self.orchestrator.map_async(
                self._fetch_single_price,
                tasks,
                priority=TaskPriority.URGENT,
                timeout=timeout
            )
            
            # Aggregate results
            aggregated = self._aggregate_price_data(results, symbols, exchanges)
            
            # Update metrics
            execution_time = time.time() - start_time
            self._update_metrics('price_fetches', execution_time, len(symbols) * len(exchanges))
            
            return aggregated
            
        except Exception as e:
            self.operation_metrics['price_fetches']['errors'] += 1
            logger.error(f"Multi-exchange price fetch failed: {e}")
            raise
    
    async def calculate_portfolio_values(self, 
                                       wallet_addresses: List[str],
                                       include_defi: bool = True,
                                       timeout: float = 10.0) -> Dict[str, Any]:
        """
        Calculate portfolio values across multiple wallets in parallel
        
        Args:
            wallet_addresses: List of wallet addresses to analyze
            include_defi: Whether to include DeFi positions
            timeout: Maximum time to wait for calculations
            
        Returns:
            Dict with portfolio analysis and totals
        """
        start_time = time.time()
        
        try:
            # Map: Fetch balances for each wallet
            balance_tasks = []
            for address in wallet_addresses:
                balance_tasks.append({
                    'address': address,
                    'include_defi': include_defi
                })
            
            balance_results = await self.orchestrator.map_async(
                self._fetch_wallet_balance,
                balance_tasks,
                priority=TaskPriority.HIGH,
                timeout=timeout
            )
            
            # Reduce: Calculate aggregated portfolio metrics
            portfolio_analysis = self._aggregate_portfolio_data(balance_results)
            
            # Update metrics
            execution_time = time.time() - start_time
            self._update_metrics('portfolio_calcs', execution_time, len(wallet_addresses))
            
            return portfolio_analysis
            
        except Exception as e:
            self.operation_metrics['portfolio_calcs']['errors'] += 1
            logger.error(f"Portfolio calculation failed: {e}")
            raise
    
    async def coordinate_multi_agent_analysis(self,
                                            agent_tasks: List[Dict[str, Any]],
                                            priority: TaskPriority = TaskPriority.HIGH,
                                            timeout: float = 30.0) -> List[Dict[str, Any]]:
        """
        Coordinate multiple AI agents for parallel analysis
        
        Args:
            agent_tasks: List of agent task configurations
            priority: Task priority level
            timeout: Maximum time to wait for all agents
            
        Returns:
            List of agent analysis results
        """
        start_time = time.time()
        
        try:
            # Submit agent tasks with specified priority
            results = await self.orchestrator.map_async(
                self._execute_agent_task,
                agent_tasks,
                priority=priority,
                timeout=timeout
            )
            
            # Extract successful results
            successful_results = []
            for result in results:
                if result.status == TaskStatus.COMPLETED:
                    successful_results.append(result.result)
                else:
                    logger.warning(f"Agent task failed: {result.error}")
            
            # Update metrics
            execution_time = time.time() - start_time
            self._update_metrics('agent_tasks', execution_time, len(agent_tasks))
            
            return successful_results
            
        except Exception as e:
            self.operation_metrics['agent_tasks']['errors'] += 1
            logger.error(f"Multi-agent coordination failed: {e}")
            raise
    
    async def stream_real_time_data(self,
                                  data_sources: List[Dict[str, Any]],
                                  callback: Callable,
                                  batch_size: int = 10) -> None:
        """
        Stream real-time data from multiple sources
        
        Args:
            data_sources: List of data source configurations
            callback: Function to call with each batch of results
            batch_size: Number of results to batch before calling callback
        """
        start_time = time.time()
        
        try:
            # Submit streaming tasks
            task_ids = []
            for source in data_sources:
                task_id = await self.orchestrator.submit_function(
                    self._stream_data_source,
                    source,
                    priority=TaskPriority.CRITICAL
                )
                task_ids.append(task_id)
            
            # Stream results and batch them
            batch = []
            async for result in self.orchestrator.stream_results(task_ids):
                if result.status == TaskStatus.COMPLETED:
                    batch.append(result.result)
                    
                    if len(batch) >= batch_size:
                        await callback(batch)
                        batch = []
                        
                        # Update metrics
                        self._update_metrics('data_streams', time.time() - start_time, len(batch))
                        start_time = time.time()
            
            # Process remaining batch
            if batch:
                await callback(batch)
                
        except Exception as e:
            self.operation_metrics['data_streams']['errors'] += 1
            logger.error(f"Real-time data streaming failed: {e}")
            raise
    
    def _fetch_single_price(self, task_data: Dict[str, str]) -> Dict[str, Any]:
        """Fetch price for a single symbol from a single exchange"""
        symbol = task_data['symbol']
        exchange = task_data['exchange']
        
        # This would integrate with actual exchange APIs
        # For now, simulate the structure
        return {
            'symbol': symbol,
            'exchange': exchange,
            'price': 50000.0,  # Placeholder
            'timestamp': datetime.utcnow().isoformat(),
            'volume_24h': 1000000.0
        }
    
    def _fetch_wallet_balance(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch balance for a single wallet"""
        address = task_data['address']
        include_defi = task_data['include_defi']
        
        # This would integrate with blockchain APIs
        # For now, simulate the structure
        return {
            'address': address,
            'total_usd_value': 10000.0,  # Placeholder
            'token_balances': [],
            'defi_positions': [] if include_defi else None,
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def _execute_agent_task(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single agent task"""
        agent_type = agent_config.get('type', 'analyst')
        task_data = agent_config.get('data', {})
        
        # This would integrate with the actual agent system
        # For now, simulate the structure
        return {
            'agent_type': agent_type,
            'analysis': "Placeholder analysis result",
            'confidence': 0.85,
            'execution_time': 1.5,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _stream_data_source(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Stream data from a single source"""
        source_type = source_config.get('type', 'websocket')
        endpoint = source_config.get('endpoint', '')
        
        # This would integrate with real data streams
        # For now, simulate the structure
        return {
            'source_type': source_type,
            'endpoint': endpoint,
            'data': {"price": 50000.0, "volume": 1000},
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _aggregate_price_data(self, results: List[Any], symbols: List[str], exchanges: List[str]) -> Dict[str, Any]:
        """Aggregate price data from multiple sources"""
        successful_results = [r.result for r in results if r.status == TaskStatus.COMPLETED]
        
        aggregated = {
            'symbols': {},
            'exchanges': exchanges,
            'total_queries': len(results),
            'successful_queries': len(successful_results),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Group by symbol
        for symbol in symbols:
            symbol_data = [r for r in successful_results if r['symbol'] == symbol]
            if symbol_data:
                aggregated['symbols'][symbol] = {
                    'prices': {r['exchange']: r['price'] for r in symbol_data},
                    'avg_price': sum(r['price'] for r in symbol_data) / len(symbol_data),
                    'price_spread': max(r['price'] for r in symbol_data) - min(r['price'] for r in symbol_data)
                }
        
        return aggregated
    
    def _aggregate_portfolio_data(self, results: List[Any]) -> Dict[str, Any]:
        """Aggregate portfolio data from multiple wallets"""
        successful_results = [r.result for r in results if r.status == TaskStatus.COMPLETED]
        
        total_value = sum(r['total_usd_value'] for r in successful_results)
        
        return {
            'total_portfolio_value': total_value,
            'wallet_count': len(successful_results),
            'wallets': successful_results,
            'avg_wallet_value': total_value / len(successful_results) if successful_results else 0,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _update_metrics(self, operation: str, execution_time: float, task_count: int) -> None:
        """Update performance metrics for an operation"""
        metrics = self.operation_metrics[operation]
        
        # Update average execution time
        total_time = metrics['avg_time'] * metrics['count'] + execution_time
        metrics['count'] += 1
        metrics['avg_time'] = total_time / metrics['count']
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        return {
            'framework_stats': self.orchestrator.get_stats(),
            'operation_metrics': self.operation_metrics,
            'circuit_breaker_status': {
                name: breaker.get_stats() 
                for name, breaker in self.circuit_breakers.items()
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        framework_health = await self.orchestrator.health_check()
        
        return {
            'status': 'healthy' if self.is_running else 'stopped',
            'framework': framework_health,
            'circuit_breakers': {
                name: breaker.get_state()
                for name, breaker in self.circuit_breakers.items()
            },
            'timestamp': datetime.utcnow().isoformat()
        }


# Global instance for easy access
_global_processor: Optional[CoinLinkParallelProcessor] = None


def get_coinlink_processor(**kwargs) -> CoinLinkParallelProcessor:
    """Get the global CoinLink parallel processor instance"""
    global _global_processor
    if _global_processor is None:
        _global_processor = CoinLinkParallelProcessor(**kwargs)
    return _global_processor


async def run_with_coinlink_processor(main_func: Callable, **kwargs):
    """Run a function with the CoinLink processor context"""
    processor = get_coinlink_processor(**kwargs)
    await processor.start()
    
    try:
        if asyncio.iscoroutinefunction(main_func):
            return await main_func(processor)
        else:
            return main_func(processor)
    finally:
        await processor.stop()
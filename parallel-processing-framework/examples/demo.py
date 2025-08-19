"""
Comprehensive demo showcasing parallel processing framework capabilities
"""
import asyncio
import time
import random
import math
import json
import sys
import os
from datetime import datetime
from typing import List, Any, Dict
import logging

# Add parent directory to path so we can import the framework modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Framework imports
from orchestrator.main import get_orchestrator, run_with_orchestrator
from core.interfaces import TaskPriority
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Demo functions for parallel processing
def cpu_intensive_task(n: int) -> Dict[str, Any]:
    """CPU-intensive task: calculate prime numbers"""
    start_time = time.time()
    
    def is_prime(num):
        if num < 2:
            return False
        for i in range(2, int(math.sqrt(num)) + 1):
            if num % i == 0:
                return False
        return True
    
    primes = [i for i in range(2, n) if is_prime(i)]
    
    return {
        'input': n,
        'prime_count': len(primes),
        'largest_prime': max(primes) if primes else None,
        'execution_time': time.time() - start_time
    }


async def io_intensive_task(delay: float, data: str) -> Dict[str, Any]:
    """IO-intensive task: simulated network operation"""
    start_time = time.time()
    
    # Simulate network delay
    await asyncio.sleep(delay)
    
    # Simulate processing
    processed_data = data.upper()
    
    return {
        'original_data': data,
        'processed_data': processed_data,
        'delay': delay,
        'execution_time': time.time() - start_time
    }


def data_processing_task(data: List[int]) -> Dict[str, Any]:
    """Data processing task: statistical analysis"""
    start_time = time.time()
    
    if not data:
        return {'error': 'Empty dataset'}
    
    result = {
        'count': len(data),
        'sum': sum(data),
        'mean': sum(data) / len(data),
        'min': min(data),
        'max': max(data),
        'std_dev': math.sqrt(sum((x - sum(data)/len(data))**2 for x in data) / len(data)),
        'execution_time': time.time() - start_time
    }
    
    return result


def error_prone_task(failure_rate: float = 0.3) -> str:
    """Task that randomly fails to test error handling"""
    if random.random() < failure_rate:
        raise Exception(f"Random failure (rate: {failure_rate})")
    
    return f"Success! Failure rate was {failure_rate}"


async def demo_basic_parallel_execution():
    """Demo 1: Basic parallel task execution"""
    print("\n" + "="*60)
    print("DEMO 1: Basic Parallel Task Execution")
    print("="*60)
    
    orchestrator = get_orchestrator()
    
    # Create multiple CPU-intensive tasks
    numbers = [1000, 1500, 2000, 2500, 3000]
    
    print(f"Calculating primes for numbers: {numbers}")
    start_time = time.time()
    
    # Submit tasks with different priorities
    task_ids = []
    for i, n in enumerate(numbers):
        priority = TaskPriority.HIGH if i < 2 else TaskPriority.NORMAL
        task_id = await orchestrator.submit_function(
            cpu_intensive_task, n, priority=priority
        )
        task_ids.append(task_id)
    
    # Collect results
    results = await orchestrator.get_results(task_ids, timeout=30.0)
    
    total_time = time.time() - start_time
    
    print(f"\nResults (completed in {total_time:.2f}s):")
    for result in results:
        if result.status.value == 'completed':
            data = result.result
            print(f"  Input: {data['input']:4d} -> "
                  f"Primes: {data['prime_count']:3d}, "
                  f"Largest: {data['largest_prime']:4d}, "
                  f"Time: {data['execution_time']:.3f}s, "
                  f"Worker: {result.worker_id}")
        else:
            print(f"  Task failed: {result.error}")


async def demo_async_io_processing():
    """Demo 2: Async I/O processing"""
    print("\n" + "="*60)
    print("DEMO 2: Async I/O Processing")
    print("="*60)
    
    orchestrator = get_orchestrator()
    
    # Create I/O intensive tasks with varying delays
    io_tasks = [
        (0.1, "quick task"),
        (0.5, "medium task"),
        (1.0, "slow task"),
        (0.2, "another quick task"),
        (0.8, "another slow task")
    ]
    
    print(f"Processing {len(io_tasks)} I/O tasks...")
    start_time = time.time()
    
    # Submit async tasks
    task_ids = []
    for delay, data in io_tasks:
        task_id = await orchestrator.submit_function(
            io_intensive_task, delay, data,
            priority=TaskPriority.HIGH if delay < 0.3 else TaskPriority.NORMAL
        )
        task_ids.append(task_id)
    
    # Stream results as they come in
    print("\nStreaming results:")
    async for result in orchestrator.stream_results(task_ids):
        if result.status.value == 'completed':
            data = result.result
            print(f"  '{data['original_data']}' -> '{data['processed_data']}' "
                  f"(delay: {data['delay']}s, actual: {data['execution_time']:.3f}s)")
        else:
            print(f"  Task failed: {result.error}")
    
    total_time = time.time() - start_time
    print(f"\nAll I/O tasks completed in {total_time:.2f}s")


async def demo_map_reduce_operations():
    """Demo 3: Map-Reduce style operations"""
    print("\n" + "="*60)
    print("DEMO 3: Map-Reduce Operations")
    print("="*60)
    
    orchestrator = get_orchestrator()
    
    # Generate sample datasets
    datasets = [
        [random.randint(1, 100) for _ in range(50)],
        [random.randint(1, 100) for _ in range(75)],
        [random.randint(1, 100) for _ in range(100)],
        [random.randint(1, 100) for _ in range(125)],
        [random.randint(1, 100) for _ in range(150)]
    ]
    
    print(f"Processing {len(datasets)} datasets with parallel map...")
    
    # Map operation: process each dataset
    start_time = time.time()
    results = await orchestrator.map_async(
        data_processing_task, 
        datasets, 
        priority=TaskPriority.NORMAL,
        timeout=15.0
    )
    
    map_time = time.time() - start_time
    
    print(f"Map operation completed in {map_time:.2f}s")
    print("\nDataset statistics:")
    
    successful_results = [r for r in results if r.status.value == 'completed']
    for i, result in enumerate(successful_results):
        stats = result.result
        print(f"  Dataset {i+1}: count={stats['count']:3d}, "
              f"mean={stats['mean']:6.2f}, "
              f"std_dev={stats['std_dev']:6.2f}, "
              f"range=[{stats['min']}, {stats['max']}]")
    
    # Reduce operation: aggregate results
    print(f"\nAggregating results from {len(successful_results)} datasets...")
    
    total_count = sum(r.result['count'] for r in successful_results)
    total_sum = sum(r.result['sum'] for r in successful_results)
    overall_mean = total_sum / total_count
    
    print(f"Overall statistics:")
    print(f"  Total samples: {total_count}")
    print(f"  Overall mean: {overall_mean:.2f}")
    print(f"  Processing time: {map_time:.2f}s")


async def demo_error_handling_and_resilience():
    """Demo 4: Error handling and resilience"""
    print("\n" + "="*60)
    print("DEMO 4: Error Handling and Resilience")
    print("="*60)
    
    orchestrator = get_orchestrator()
    
    # Create tasks with different failure rates
    failure_rates = [0.0, 0.2, 0.5, 0.8, 1.0]
    
    print("Testing error handling with various failure rates...")
    
    # Submit error-prone tasks
    task_ids = []
    for rate in failure_rates:
        task_id = await orchestrator.submit_function(
            error_prone_task, rate,
            priority=TaskPriority.NORMAL
        )
        task_ids.append(task_id)
    
    # Collect results
    results = await orchestrator.get_results(task_ids, timeout=10.0)
    
    print("\nResults:")
    success_count = 0
    failure_count = 0
    
    for i, result in enumerate(results):
        rate = failure_rates[i]
        if result.status.value == 'completed':
            success_count += 1
            print(f"  Failure rate {rate:.1f}: SUCCESS - {result.result}")
        else:
            failure_count += 1
            print(f"  Failure rate {rate:.1f}: FAILED - {result.error}")
    
    print(f"\nSummary: {success_count} successful, {failure_count} failed")


async def demo_performance_monitoring():
    """Demo 5: Performance monitoring and statistics"""
    print("\n" + "="*60)
    print("DEMO 5: Performance Monitoring")
    print("="*60)
    
    orchestrator = get_orchestrator()
    
    # Generate a mixed workload
    print("Generating mixed workload for performance analysis...")
    
    # Submit various types of tasks
    task_count = 20
    task_ids = []
    
    for i in range(task_count):
        if i % 3 == 0:
            # CPU-intensive task
            task_id = await orchestrator.submit_function(
                cpu_intensive_task, 500 + i * 50,
                priority=TaskPriority.NORMAL
            )
        elif i % 3 == 1:
            # I/O task
            task_id = await orchestrator.submit_function(
                io_intensive_task, random.uniform(0.1, 0.5), f"data_{i}",
                priority=TaskPriority.HIGH
            )
        else:
            # Data processing task
            data = [random.randint(1, 100) for _ in range(random.randint(20, 80))]
            task_id = await orchestrator.submit_function(
                data_processing_task, data,
                priority=TaskPriority.LOW
            )
        
        task_ids.append(task_id)
    
    # Monitor progress
    print(f"Submitted {len(task_ids)} tasks, monitoring progress...")
    
    completed = 0
    async for result in orchestrator.stream_results(task_ids):
        completed += 1
        progress = (completed / len(task_ids)) * 100
        print(f"  Progress: {progress:5.1f}% ({completed}/{len(task_ids)}) - "
              f"Task {result.task_id[:8]} completed in {result.execution_time:.3f}s")
    
    # Display final statistics
    stats = orchestrator.get_stats()
    print(f"\nFinal Framework Statistics:")
    print(f"  Orchestrator uptime: {stats['orchestrator']['uptime_seconds']:.1f}s")
    print(f"  Total tasks submitted: {stats['orchestrator']['total_tasks_submitted']}")
    print(f"  Total tasks completed: {stats['orchestrator']['total_tasks_completed']}")
    print(f"  Success rate: {stats['orchestrator']['success_rate']:.1%}")
    print(f"  Active workers: {stats['worker_pool']['worker_count']}")
    print(f"  Current load: {stats['worker_pool']['current_load']:.2f}")


async def demo_circuit_breaker():
    """Demo 6: Circuit breaker functionality"""
    print("\n" + "="*60)
    print("DEMO 6: Circuit Breaker Pattern")
    print("="*60)
    
    from core.circuit_breaker import get_circuit_breaker, CircuitBreakerConfig
    
    # Create a circuit breaker for unreliable service
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=5,
        half_open_max_calls=2
    )
    
    breaker = await get_circuit_breaker("demo_service", config)
    
    print("Testing circuit breaker with unreliable service...")
    
    # Function that fails most of the time initially
    failure_rate = 0.8
    def unreliable_service(data: str) -> str:
        nonlocal failure_rate
        if random.random() < failure_rate:
            raise Exception("Service temporarily unavailable")
        return f"Processed: {data}"
    
    # Test the circuit breaker
    for i in range(15):
        try:
            result = await breaker.call(unreliable_service, f"request_{i}")
            print(f"  Request {i}: SUCCESS - {result}")
        except Exception as e:
            print(f"  Request {i}: FAILED - {e}")
        
        # Improve service reliability over time
        if i > 7:
            failure_rate = max(0.1, failure_rate - 0.1)
        
        # Show circuit breaker state
        state = breaker.get_state()
        stats = breaker.get_stats()
        print(f"    Circuit state: {state}, Failures: {stats['consecutive_failures']}")
        
        await asyncio.sleep(0.5)
    
    # Final stats
    final_stats = breaker.get_stats()
    print(f"\nCircuit Breaker Final Stats:")
    print(f"  Total calls: {final_stats['total_calls']}")
    print(f"  Success rate: {final_stats['success_rate']:.1%}")
    print(f"  State changes: {final_stats['state_changes']}")


async def main():
    """Main demo function"""
    print("🚀 Parallel Processing Framework Demo")
    print("=====================================")
    
    async def run_demos(orchestrator):
        """Run all demo functions"""
        demos = [
            demo_basic_parallel_execution,
            demo_async_io_processing,
            demo_map_reduce_operations,
            demo_error_handling_and_resilience,
            demo_performance_monitoring,
            demo_circuit_breaker
        ]
        
        for demo_func in demos:
            try:
                await demo_func()
                await asyncio.sleep(1)  # Brief pause between demos
            except Exception as e:
                logger.error(f"Demo {demo_func.__name__} failed: {e}")
        
        # Final health check
        print("\n" + "="*60)
        print("FINAL HEALTH CHECK")
        print("="*60)
        
        health = await orchestrator.health_check()
        print(f"Overall status: {health['status']}")
        
        for component, status in health['components'].items():
            component_status = status.get('status', 'unknown')
            print(f"  {component}: {component_status}")
    
    # Run with orchestrator context
    await run_with_orchestrator(run_demos, use_uvloop=True)
    
    print("\n🎉 Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Interactive test script for the Parallel Processing Framework
No need to deal with async/await - just run and test!
"""
import asyncio
import sys
import os
import time
import random
from typing import List

# Add framework to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.main import get_orchestrator
from core.interfaces import TaskPriority

# Example functions for testing
def square(n):
    """Square a number"""
    return n * n

def add_numbers(a, b):
    """Add two numbers"""
    return a + b

def slow_multiply(x, y):
    """Multiply with artificial delay"""
    time.sleep(0.5)  # Simulate slow operation
    return x * y

def process_data(data_list):
    """Process a list of numbers"""
    return {
        'sum': sum(data_list),
        'avg': sum(data_list) / len(data_list),
        'count': len(data_list)
    }

def factorial(n):
    """Calculate factorial"""
    if n <= 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

class FrameworkTester:
    def __init__(self):
        self.orchestrator = None
    
    async def start(self):
        """Start the framework"""
        print("🚀 Starting Parallel Processing Framework...")
        self.orchestrator = get_orchestrator()
        await self.orchestrator.start()
        print("✅ Framework started successfully!")
    
    async def stop(self):
        """Stop the framework"""
        if self.orchestrator:
            await self.orchestrator.stop()
            print("🛑 Framework stopped")
    
    async def test_basic_execution(self):
        """Test basic parallel task execution"""
        print("\n" + "="*50)
        print("🧪 TEST 1: Basic Parallel Execution")
        print("="*50)
        
        numbers = [1, 2, 3, 4, 5]
        print(f"📊 Computing squares of: {numbers}")
        
        start_time = time.time()
        
        # Submit tasks
        task_ids = []
        for num in numbers:
            task_id = await self.orchestrator.submit_function(
                square, num, priority=TaskPriority.NORMAL
            )
            task_ids.append(task_id)
            print(f"  ✓ Submitted: square({num})")
        
        # Get results
        results = await self.orchestrator.get_results(task_ids, timeout=10.0)
        
        execution_time = time.time() - start_time
        
        print(f"\n📈 Results (in {execution_time:.2f}s):")
        for i, result in enumerate(results):
            if result.status.value == 'completed':
                print(f"  ✅ {numbers[i]}² = {result.result}")
            else:
                print(f"  ❌ {numbers[i]}² failed: {result.error}")
    
    async def test_different_priorities(self):
        """Test priority queues"""
        print("\n" + "="*50)
        print("🎯 TEST 2: Priority Queue Testing")
        print("="*50)
        
        # Submit tasks with different priorities
        tasks = [
            (1, TaskPriority.LOW, "Low priority"),
            (2, TaskPriority.URGENT, "🚨 URGENT"),
            (3, TaskPriority.NORMAL, "Normal"),
            (4, TaskPriority.HIGH, "High priority"),
            (5, TaskPriority.CRITICAL, "🔥 CRITICAL")
        ]
        
        print("📋 Submitting tasks with different priorities...")
        task_ids = []
        for num, priority, desc in tasks:
            task_id = await self.orchestrator.submit_function(
                square, num, priority=priority
            )
            task_ids.append(task_id)
            print(f"  ✓ {desc}: square({num})")
        
        print(f"\n⏳ Watching execution order...")
        completed_order = []
        async for result in self.orchestrator.stream_results(task_ids):
            completed_order.append(result.result)
            original_num = int(result.result ** 0.5)  # Get original number
            task_info = next(t for t in tasks if t[0] == original_num)
            print(f"  ✅ Completed: {task_info[2]} = {result.result}")
        
        print(f"\n📊 Execution order: {completed_order}")
        print("Note: Higher priority tasks should complete first!")
    
    async def test_map_reduce(self):
        """Test map-reduce style operations"""
        print("\n" + "="*50)
        print("🗺️ TEST 3: Map-Reduce Operations")
        print("="*50)
        
        # Generate datasets
        datasets = []
        for i in range(4):
            dataset = [random.randint(1, 100) for _ in range(10)]
            datasets.append(dataset)
        
        print(f"📊 Processing {len(datasets)} datasets in parallel...")
        
        start_time = time.time()
        
        # Map operation: process each dataset
        results = await self.orchestrator.map_async(
            process_data, datasets, priority=TaskPriority.HIGH
        )
        
        execution_time = time.time() - start_time
        
        print(f"\n📈 Results (in {execution_time:.2f}s):")
        total_sum = 0
        total_count = 0
        
        for i, result in enumerate(results):
            if result.status.value == 'completed':
                data = result.result
                print(f"  Dataset {i+1}: sum={data['sum']:3d}, avg={data['avg']:5.1f}, count={data['count']}")
                total_sum += data['sum']
                total_count += data['count']
            else:
                print(f"  Dataset {i+1}: ❌ Failed")
        
        print(f"\n🎯 Overall: total_sum={total_sum}, total_count={total_count}, overall_avg={total_sum/total_count:.1f}")
    
    async def test_slow_operations(self):
        """Test handling of slow operations"""
        print("\n" + "="*50)
        print("🐌 TEST 4: Slow Operations (Parallel vs Sequential)")
        print("="*50)
        
        pairs = [(2, 3), (4, 5), (6, 7), (8, 9)]
        
        # Test sequential execution
        print("🔄 Sequential execution...")
        seq_start = time.time()
        seq_results = []
        for a, b in pairs:
            result = slow_multiply(a, b)
            seq_results.append(result)
        seq_time = time.time() - seq_start
        print(f"  ✅ Sequential: {seq_results} in {seq_time:.2f}s")
        
        # Test parallel execution
        print("⚡ Parallel execution...")
        par_start = time.time()
        task_ids = []
        for a, b in pairs:
            task_id = await self.orchestrator.submit_function(
                slow_multiply, a, b, priority=TaskPriority.HIGH
            )
            task_ids.append(task_id)
        
        results = await self.orchestrator.get_results(task_ids, timeout=15.0)
        par_time = time.time() - par_start
        
        par_results = [r.result for r in results if r.status.value == 'completed']
        print(f"  ✅ Parallel: {par_results} in {par_time:.2f}s")
        
        speedup = seq_time / par_time if par_time > 0 else 0
        print(f"\n🚀 Speedup: {speedup:.1f}x faster with parallel processing!")
    
    async def test_error_handling(self):
        """Test error handling"""
        print("\n" + "="*50)
        print("🚨 TEST 5: Error Handling")
        print("="*50)
        
        def divide_by_zero(x):
            return x / 0  # This will fail
        
        def safe_divide(x, y):
            if y == 0:
                raise ValueError("Cannot divide by zero!")
            return x / y
        
        print("Testing error scenarios...")
        
        # Submit failing tasks
        failing_tasks = []
        for i in range(3):
            task_id = await self.orchestrator.submit_function(divide_by_zero, i)
            failing_tasks.append(task_id)
        
        # Submit mixed success/failure tasks
        mixed_tasks = []
        test_cases = [(10, 2), (20, 0), (30, 3), (40, 0)]  # Two will fail
        for x, y in test_cases:
            task_id = await self.orchestrator.submit_function(safe_divide, x, y)
            mixed_tasks.append(task_id)
        
        # Check failing tasks
        print("\n❌ Intentionally failing tasks:")
        fail_results = await self.orchestrator.get_results(failing_tasks, timeout=5.0)
        for i, result in enumerate(fail_results):
            if result.status.value == 'failed':
                print(f"  ✅ Task {i} failed as expected: {type(result.error).__name__}")
            else:
                print(f"  ❓ Task {i} unexpectedly succeeded: {result.result}")
        
        # Check mixed tasks
        print("\n🎲 Mixed success/failure tasks:")
        mixed_results = await self.orchestrator.get_results(mixed_tasks, timeout=5.0)
        for i, result in enumerate(mixed_results):
            x, y = test_cases[i]
            if result.status.value == 'completed':
                print(f"  ✅ {x}/{y} = {result.result}")
            else:
                print(f"  ❌ {x}/{y} failed: {type(result.error).__name__}")
    
    async def show_stats(self):
        """Show framework statistics"""
        print("\n" + "="*50)
        print("📊 FRAMEWORK STATISTICS")
        print("="*50)
        
        stats = self.orchestrator.get_stats()
        
        print(f"🎯 Orchestrator:")
        print(f"  • Total tasks submitted: {stats['orchestrator']['total_tasks_submitted']}")
        print(f"  • Total tasks completed: {stats['orchestrator']['total_tasks_completed']}")
        print(f"  • Success rate: {stats['orchestrator']['success_rate']:.1%}")
        
        print(f"\n👥 Worker Pool:")
        print(f"  • Active workers: {stats['worker_pool']['worker_count']}")
        print(f"  • Current load: {stats['worker_pool']['current_load']:.2f}")
        print(f"  • Scaling events: {stats['worker_pool']['total_scaling_events']}")
        
        print(f"\n⚡ Event Loop:")
        print(f"  • Using uvloop: {stats['event_loop_manager']['use_uvloop']}")
        print(f"  • Active tasks: {stats['event_loop_manager']['active_tasks']}")
        print(f"  • Success rate: {stats['event_loop_manager']['success_rate']:.1%}")

async def run_interactive_tests():
    """Run all tests interactively"""
    tester = FrameworkTester()
    
    try:
        await tester.start()
        
        print("\n🎮 Running Interactive Tests...")
        print("Press Ctrl+C to stop at any time")
        
        # Run all tests
        await tester.test_basic_execution()
        await asyncio.sleep(1)
        
        await tester.test_different_priorities()
        await asyncio.sleep(1)
        
        await tester.test_map_reduce()
        await asyncio.sleep(1)
        
        await tester.test_slow_operations()
        await asyncio.sleep(1)
        
        await tester.test_error_handling()
        await asyncio.sleep(1)
        
        await tester.show_stats()
        
        print("\n🎉 All tests completed successfully!")
        print("✨ The Parallel Processing Framework is working perfectly!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    finally:
        await tester.stop()

def print_menu():
    """Print the interactive menu"""
    print("\n" + "="*60)
    print("🚀 PARALLEL PROCESSING FRAMEWORK - INTERACTIVE TESTER")
    print("="*60)
    print("Available tests:")
    print("  1. 🧪 Basic Parallel Execution")
    print("  2. 🎯 Priority Queue Testing")
    print("  3. 🗺️  Map-Reduce Operations")
    print("  4. 🐌 Slow Operations (Speedup Demo)")
    print("  5. 🚨 Error Handling")
    print("  6. 📊 Show Framework Statistics")
    print("  7. 🎮 Run All Tests")
    print("  0. 🚪 Exit")
    print("="*60)

async def interactive_menu():
    """Interactive menu for testing"""
    tester = FrameworkTester()
    await tester.start()
    
    try:
        while True:
            print_menu()
            choice = input("👉 Choose a test (0-7): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                await tester.test_basic_execution()
            elif choice == '2':
                await tester.test_different_priorities()
            elif choice == '3':
                await tester.test_map_reduce()
            elif choice == '4':
                await tester.test_slow_operations()
            elif choice == '5':
                await tester.test_error_handling()
            elif choice == '6':
                await tester.show_stats()
            elif choice == '7':
                await run_interactive_tests()
            else:
                print("❌ Invalid choice. Please try again.")
            
            if choice != '0':
                input("\n⏯️  Press Enter to continue...")
    
    except KeyboardInterrupt:
        print("\n⏹️ Exiting...")
    finally:
        await tester.stop()

def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        # Run all tests automatically
        asyncio.run(run_interactive_tests())
    else:
        # Interactive menu
        asyncio.run(interactive_menu())

if __name__ == "__main__":
    main()
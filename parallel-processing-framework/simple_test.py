#!/usr/bin/env python3
"""
Simple test to verify the parallel processing framework is working
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.main import get_orchestrator
from core.interfaces import TaskPriority

# Define task function at module level so it can be pickled
def square_number(n):
    return n * n

async def simple_test():
    """Simple test of basic functionality"""
    print("🚀 Testing Parallel Processing Framework...")
    
    # Get orchestrator
    orchestrator = get_orchestrator()
    await orchestrator.start()
    
    try:
        
        print(f"📊 Submitting 5 tasks...")
        
        # Submit tasks
        task_ids = []
        for i in range(1, 6):
            task_id = await orchestrator.submit_function(
                square_number, i, 
                priority=TaskPriority.NORMAL
            )
            task_ids.append(task_id)
            print(f"  ✓ Submitted task {i}")
        
        print(f"⏳ Waiting for results...")
        
        # Get results with timeout
        results = await orchestrator.get_results(task_ids, timeout=10.0)
        
        print(f"📈 Results:")
        success_count = 0
        for i, result in enumerate(results):
            if result.status.value == 'completed':
                print(f"  ✅ {i+1}² = {result.result}")
                success_count += 1
            else:
                print(f"  ❌ Task {i+1} failed: {result.error}")
        
        print(f"\n🎉 Test completed: {success_count}/{len(results)} tasks successful!")
        
        # Get quick stats
        stats = orchestrator.get_stats()
        print(f"📊 Framework stats:")
        print(f"  • Workers: {stats['worker_pool']['worker_count']}")
        print(f"  • Total tasks: {stats['orchestrator']['total_tasks_submitted']}")
        print(f"  • Success rate: {stats['orchestrator']['success_rate']:.1%}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        await orchestrator.stop()
        print("🛑 Framework stopped")

if __name__ == "__main__":
    asyncio.run(simple_test())
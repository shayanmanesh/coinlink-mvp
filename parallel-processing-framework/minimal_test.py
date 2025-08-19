#!/usr/bin/env python3
"""
Minimal test to verify core components work
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test just the core components without full orchestrator
from core.task_queue import RedisTaskQueue
from core.result_store import RedisResultStore
from core.interfaces import Task, TaskPriority

def test_function(x):
    return x * 2

async def minimal_test():
    """Test core components directly"""
    print("🧪 Testing Core Components...")
    
    # Test task queue
    print("📋 Testing task queue...")
    queue = RedisTaskQueue()
    await queue.connect()
    
    # Create a simple task
    task = Task(
        id="test-001",
        func=test_function,
        args=(5,),
        priority=TaskPriority.NORMAL
    )
    
    # Test enqueue
    success = await queue.enqueue(task)
    print(f"  ✓ Enqueue: {success}")
    
    # Test size
    size = await queue.size()
    print(f"  ✓ Queue size: {size}")
    
    # Test dequeue
    dequeued_task = await queue.dequeue(timeout=5.0)
    if dequeued_task:
        print(f"  ✓ Dequeued task: {dequeued_task.id}")
        
        # Execute the task
        try:
            result = dequeued_task.func(*dequeued_task.args)
            print(f"  ✓ Task result: {result}")
        except Exception as e:
            print(f"  ❌ Task execution failed: {e}")
    else:
        print("  ❌ No task dequeued")
    
    await queue.disconnect()
    
    # Test result store
    print("💾 Testing result store...")
    store = RedisResultStore()
    await store.connect()
    
    from core.interfaces import TaskResult, TaskStatus
    from datetime import datetime
    
    result = TaskResult(
        task_id="test-001",
        status=TaskStatus.COMPLETED,
        result=10,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow()
    )
    
    # Store result
    stored = await store.store_result(result)
    print(f"  ✓ Store result: {stored}")
    
    # Retrieve result
    retrieved = await store.get_result("test-001")
    if retrieved:
        print(f"  ✓ Retrieved result: {retrieved.result}")
    else:
        print("  ❌ Failed to retrieve result")
    
    await store.disconnect()
    
    print("🎉 Core components test completed!")

if __name__ == "__main__":
    asyncio.run(minimal_test())
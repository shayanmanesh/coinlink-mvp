"""
Self-improvement engine for agent learning and adaptation
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import json
import pickle
import os

logger = logging.getLogger(__name__)

@dataclass
class LearningPoint:
    """Represents a single learning data point"""
    agent_name: str
    task_type: str
    parameters: Dict[str, Any]
    outcome: str  # success, failure, partial
    performance_delta: Dict[str, float]  # metric improvements/degradations
    execution_time: float
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationPattern:
    """Represents a learned optimization pattern"""
    pattern_id: str
    task_type: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    success_rate: float
    average_improvement: float
    usage_count: int
    last_used: datetime
    confidence_score: float

class SelfImprovementEngine:
    """Engine for agent self-improvement and learning"""
    
    def __init__(self, data_dir: str = "/tmp/agent_learning"):
        self.data_dir = data_dir
        self.learning_points: deque = deque(maxlen=10000)
        self.optimization_patterns: Dict[str, OptimizationPattern] = {}
        self.agent_performance_history: Dict[str, List[Dict]] = defaultdict(list)
        self.running = False
        
        # Learning parameters
        self.min_samples_for_pattern = 5
        self.pattern_confidence_threshold = 0.7
        self.learning_rate = 0.1
        self.memory_decay_factor = 0.95
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing learning data
        self.load_learning_data()
    
    async def start(self):
        """Start the self-improvement engine"""
        self.running = True
        logger.info("Self-improvement engine started")
        
        # Start learning loop
        asyncio.create_task(self.learning_loop())
    
    def stop(self):
        """Stop the self-improvement engine"""
        self.running = False
        self.save_learning_data()
        logger.info("Self-improvement engine stopped")
    
    async def learning_loop(self):
        """Main learning loop"""
        while self.running:
            try:
                # Discover new patterns
                await self.discover_patterns()
                
                # Update existing patterns
                await self.update_pattern_confidence()
                
                # Cleanup old data
                await self.cleanup_old_data()
                
                # Save learning data periodically
                self.save_learning_data()
                
                # Sleep for learning cycle interval
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in learning loop: {e}")
                await asyncio.sleep(60)
    
    def record_learning_point(self, 
                            agent_name: str,
                            task_type: str,
                            parameters: Dict[str, Any],
                            outcome: str,
                            performance_delta: Dict[str, float],
                            execution_time: float,
                            context: Dict[str, Any] = None):
        """Record a new learning point"""
        
        learning_point = LearningPoint(
            agent_name=agent_name,
            task_type=task_type,
            parameters=parameters,
            outcome=outcome,
            performance_delta=performance_delta,
            execution_time=execution_time,
            timestamp=datetime.now(),
            context=context or {}
        )
        
        self.learning_points.append(learning_point)
        
        # Update agent performance history
        self.agent_performance_history[agent_name].append({
            "timestamp": learning_point.timestamp.isoformat(),
            "task_type": task_type,
            "outcome": outcome,
            "performance_delta": performance_delta,
            "execution_time": execution_time
        })
        
        # Keep only recent history per agent
        if len(self.agent_performance_history[agent_name]) > 1000:
            self.agent_performance_history[agent_name] = self.agent_performance_history[agent_name][-1000:]
    
    async def discover_patterns(self):
        """Discover new optimization patterns from learning data"""
        
        # Group learning points by task type
        task_groups = defaultdict(list)
        for point in self.learning_points:
            if point.outcome == "success":
                task_groups[point.task_type].append(point)
        
        # Analyze each task type for patterns
        for task_type, points in task_groups.items():
            if len(points) >= self.min_samples_for_pattern:
                await self.analyze_task_patterns(task_type, points)
    
    async def analyze_task_patterns(self, task_type: str, points: List[LearningPoint]):
        """Analyze patterns for a specific task type"""
        
        # Group by similar parameters
        parameter_groups = defaultdict(list)
        
        for point in points:
            # Create a simplified key for grouping
            key_params = {}
            for param_key, param_value in point.parameters.items():
                if isinstance(param_value, (str, int, bool)):
                    key_params[param_key] = param_value
                elif isinstance(param_value, float):
                    # Round floats for grouping
                    key_params[param_key] = round(param_value, 2)
            
            key = json.dumps(key_params, sort_keys=True)
            parameter_groups[key].append(point)
        
        # Create patterns from groups with sufficient samples
        for param_key, group_points in parameter_groups.items():
            if len(group_points) >= self.min_samples_for_pattern:
                await self.create_optimization_pattern(task_type, param_key, group_points)
    
    async def create_optimization_pattern(self, 
                                        task_type: str, 
                                        param_key: str, 
                                        points: List[LearningPoint]):
        """Create an optimization pattern from a group of similar learning points"""
        
        # Calculate pattern statistics
        success_count = sum(1 for p in points if p.outcome == "success")
        success_rate = success_count / len(points)
        
        # Calculate average improvements
        improvements = defaultdict(list)
        for point in points:
            for metric, delta in point.performance_delta.items():
                if delta > 0:  # Only positive improvements
                    improvements[metric].append(delta)
        
        average_improvement = 0
        if improvements:
            all_improvements = [imp for imps in improvements.values() for imp in imps]
            average_improvement = statistics.mean(all_improvements) if all_improvements else 0
        
        # Calculate confidence score
        confidence_score = self.calculate_confidence_score(points, success_rate, average_improvement)
        
        if confidence_score >= self.pattern_confidence_threshold:
            # Create pattern
            pattern_id = f"{task_type}_{hash(param_key)}"
            
            # Extract common parameters
            common_params = json.loads(param_key)
            
            # Extract common actions (simplified)
            actions = {
                "parameters": common_params,
                "expected_improvement": average_improvement,
                "confidence": confidence_score
            }
            
            pattern = OptimizationPattern(
                pattern_id=pattern_id,
                task_type=task_type,
                conditions=common_params,
                actions=actions,
                success_rate=success_rate,
                average_improvement=average_improvement,
                usage_count=0,
                last_used=datetime.now(),
                confidence_score=confidence_score
            )
            
            self.optimization_patterns[pattern_id] = pattern
            logger.info(f"Created new optimization pattern: {pattern_id} (confidence: {confidence_score:.2f})")
    
    def calculate_confidence_score(self, 
                                 points: List[LearningPoint], 
                                 success_rate: float, 
                                 average_improvement: float) -> float:
        """Calculate confidence score for a pattern"""
        
        # Base confidence from success rate
        confidence = success_rate
        
        # Boost confidence for higher improvements
        improvement_factor = min(1.0, average_improvement / 50.0)  # Scale to improvement up to 50%
        confidence += improvement_factor * 0.2
        
        # Boost confidence for more data points
        sample_factor = min(1.0, len(points) / 20.0)  # Scale to 20 samples
        confidence += sample_factor * 0.1
        
        # Penalize for high variance in execution time
        execution_times = [p.execution_time for p in points]
        if len(execution_times) > 1:
            cv = statistics.stdev(execution_times) / statistics.mean(execution_times)
            variance_penalty = min(0.2, cv * 0.1)
            confidence -= variance_penalty
        
        return max(0.0, min(1.0, confidence))
    
    async def update_pattern_confidence(self):
        """Update confidence scores for existing patterns"""
        
        for pattern in self.optimization_patterns.values():
            # Find recent usage data
            recent_points = [
                p for p in self.learning_points
                if p.task_type == pattern.task_type
                and p.timestamp > datetime.now() - timedelta(days=7)
            ]
            
            if recent_points:
                # Recalculate confidence based on recent performance
                recent_success_rate = sum(1 for p in recent_points if p.outcome == "success") / len(recent_points)
                
                # Update confidence with decay
                pattern.confidence_score = (
                    pattern.confidence_score * self.memory_decay_factor +
                    recent_success_rate * (1 - self.memory_decay_factor)
                )
    
    def get_recommendation(self, 
                         agent_name: str, 
                         task_type: str, 
                         context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get optimization recommendation for a task"""
        
        # Find matching patterns
        matching_patterns = []
        for pattern in self.optimization_patterns.values():
            if pattern.task_type == task_type and pattern.confidence_score >= self.pattern_confidence_threshold:
                # Check if conditions match context
                match_score = self.calculate_match_score(pattern.conditions, context)
                if match_score > 0.7:  # 70% match threshold
                    matching_patterns.append((pattern, match_score))
        
        if not matching_patterns:
            return None
        
        # Sort by confidence and match score
        matching_patterns.sort(key=lambda x: x[0].confidence_score * x[1], reverse=True)
        
        best_pattern = matching_patterns[0][0]
        
        # Update usage
        best_pattern.usage_count += 1
        best_pattern.last_used = datetime.now()
        
        return {
            "pattern_id": best_pattern.pattern_id,
            "actions": best_pattern.actions,
            "expected_improvement": best_pattern.average_improvement,
            "confidence": best_pattern.confidence_score,
            "success_rate": best_pattern.success_rate
        }
    
    def calculate_match_score(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate how well conditions match the current context"""
        
        if not conditions:
            return 1.0
        
        matches = 0
        total = len(conditions)
        
        for key, value in conditions.items():
            if key in context:
                if context[key] == value:
                    matches += 1
                elif isinstance(value, (int, float)) and isinstance(context[key], (int, float)):
                    # For numeric values, consider close matches
                    diff = abs(value - context[key]) / max(abs(value), abs(context[key]), 1)
                    if diff < 0.2:  # Within 20%
                        matches += 0.8
                    elif diff < 0.5:  # Within 50%
                        matches += 0.5
        
        return matches / total if total > 0 else 0
    
    async def cleanup_old_data(self):
        """Clean up old learning data"""
        
        # Remove patterns with low confidence and low usage
        patterns_to_remove = []
        for pattern_id, pattern in self.optimization_patterns.items():
            if (pattern.confidence_score < 0.5 and 
                pattern.usage_count < 3 and 
                pattern.last_used < datetime.now() - timedelta(days=30)):
                patterns_to_remove.append(pattern_id)
        
        for pattern_id in patterns_to_remove:
            del self.optimization_patterns[pattern_id]
            logger.info(f"Removed low-confidence pattern: {pattern_id}")
    
    def save_learning_data(self):
        """Save learning data to disk"""
        try:
            # Save learning points
            learning_file = os.path.join(self.data_dir, "learning_points.pkl")
            with open(learning_file, "wb") as f:
                pickle.dump(list(self.learning_points), f)
            
            # Save patterns
            patterns_file = os.path.join(self.data_dir, "patterns.pkl")
            with open(patterns_file, "wb") as f:
                pickle.dump(self.optimization_patterns, f)
            
            # Save performance history
            history_file = os.path.join(self.data_dir, "performance_history.json")
            with open(history_file, "w") as f:
                # Convert to JSON-serializable format
                history_data = {}
                for agent, history in self.agent_performance_history.items():
                    history_data[agent] = history
                json.dump(history_data, f)
            
        except Exception as e:
            logger.error(f"Error saving learning data: {e}")
    
    def load_learning_data(self):
        """Load learning data from disk"""
        try:
            # Load learning points
            learning_file = os.path.join(self.data_dir, "learning_points.pkl")
            if os.path.exists(learning_file):
                with open(learning_file, "rb") as f:
                    points = pickle.load(f)
                    self.learning_points.extend(points)
            
            # Load patterns
            patterns_file = os.path.join(self.data_dir, "patterns.pkl")
            if os.path.exists(patterns_file):
                with open(patterns_file, "rb") as f:
                    self.optimization_patterns = pickle.load(f)
            
            # Load performance history
            history_file = os.path.join(self.data_dir, "performance_history.json")
            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    history_data = json.load(f)
                    for agent, history in history_data.items():
                        self.agent_performance_history[agent] = history
            
            logger.info(f"Loaded {len(self.learning_points)} learning points and {len(self.optimization_patterns)} patterns")
            
        except Exception as e:
            logger.error(f"Error loading learning data: {e}")
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        
        # Calculate agent performance stats
        agent_stats = {}
        for agent_name, history in self.agent_performance_history.items():
            if history:
                recent_history = [h for h in history 
                                if datetime.fromisoformat(h['timestamp']) > datetime.now() - timedelta(days=7)]
                
                success_rate = sum(1 for h in recent_history if h['outcome'] == 'success') / len(recent_history) if recent_history else 0
                avg_exec_time = statistics.mean([h['execution_time'] for h in recent_history]) if recent_history else 0
                
                agent_stats[agent_name] = {
                    "total_tasks": len(history),
                    "recent_tasks": len(recent_history),
                    "success_rate": success_rate,
                    "avg_execution_time": avg_exec_time
                }
        
        return {
            "total_learning_points": len(self.learning_points),
            "total_patterns": len(self.optimization_patterns),
            "high_confidence_patterns": sum(1 for p in self.optimization_patterns.values() if p.confidence_score >= 0.8),
            "agent_stats": agent_stats,
            "learning_rate": self.learning_rate,
            "pattern_confidence_threshold": self.pattern_confidence_threshold
        }


# Singleton instance
self_improvement_engine = SelfImprovementEngine()
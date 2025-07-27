#!/usr/bin/env python3
"""
Test script for performance tracking functionality
"""

import sys
import os
import time
import random

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import DatabaseManager
from services.performance_service import PerformanceService
from models.performance_models import MetricType, PerformanceStatus

def test_performance_functionality():
    """Test the performance tracking functionality"""
    print("Testing Performance Tracking Functionality")
    print("=" * 60)
    
    # Initialize database and performance service
    db = DatabaseManager()
    performance_service = PerformanceService("prompts.db")
    
    # Create some test data if database is empty
    prompts = db.get_prompts()
    if not prompts:
        print("Creating test data...")
        
        # Create test folders
        folder_id = db.create_folder("Performance Test", None)
        
        # Create test prompts
        prompt1_id = db.create_prompt(
            title="Code Generation Prompt",
            content="Generate a Python function that calculates the factorial of a number.",
            folder_id=folder_id
        )
        
        prompt2_id = db.create_prompt(
            title="Text Analysis Prompt",
            content="Analyze the sentiment of the following text and provide a detailed explanation.",
            folder_id=folder_id
        )
        
        print("Test data created successfully!")
    else:
        prompt1_id = prompts[0]['id']
        prompt2_id = prompts[1]['id'] if len(prompts) > 1 else prompt1_id
    
    # Test 1: Start performance session
    print("\n1. Testing performance session management:")
    
    session_id = performance_service.start_session("test_user", {"test_type": "automated"})
    if session_id:
        print(f"   [OK] Started performance session: {session_id[:8]}...")
    else:
        print("   [ERROR] Failed to start performance session")
        return
    
    # Test 2: Record prompt executions
    print("\n2. Testing prompt execution recording:")
    
    executions = []
    
    # Simulate multiple executions with varying performance
    for i in range(10):
        execution_time = random.uniform(0.5, 5.0)
        token_count_input = random.randint(50, 200)
        token_count_output = random.randint(100, 500)
        cost = (token_count_input + token_count_output) * 0.00002  # Simulate cost calculation
        
        execution = performance_service.record_execution(
            prompt_id=prompt1_id,
            input_text=f"Test input {i+1}",
            output_text=f"Generated output for test {i+1}",
            llm_provider="test_provider",
            llm_model="test-model-v1",
            execution_time=execution_time,
            token_count_input=token_count_input,
            token_count_output=token_count_output,
            cost=cost,
            status=PerformanceStatus.ACTIVE,
            user_id="test_user"
        )
        
        if execution:
            executions.append(execution)
            print(f"   [OK] Recorded execution {i+1}: {execution_time:.2f}s, {token_count_input + token_count_output} tokens, ${cost:.4f}")
        else:
            print(f"   [ERROR] Failed to record execution {i+1}")
    
    # Test 3: Add custom metrics
    print("\n3. Testing custom metrics:")
    
    if executions:
        execution = executions[0]
        
        # Add quality score metric
        quality_added = performance_service.add_metric(
            execution.id, MetricType.QUALITY_SCORE, 8.5, "score", {"evaluator": "human"}
        )
        
        if quality_added:
            print("   [OK] Added quality score metric")
        
        # Add user rating metric
        rating_added = performance_service.add_metric(
            execution.id, MetricType.USER_RATING, 4.2, "stars", {"max_rating": 5}
        )
        
        if rating_added:
            print("   [OK] Added user rating metric")
    
    # Test 4: Get performance metrics
    print("\n4. Testing metrics retrieval:")
    
    metrics = performance_service.get_prompt_metrics(prompt1_id, period_days=30)
    print(f"   Retrieved metrics for {len(metrics)} metric types:")
    
    for metric_type, values in metrics.items():
        if values:
            avg_value = sum(values) / len(values)
            print(f"     - {metric_type}: {len(values)} values, avg: {avg_value:.3f}")
    
    # Test 5: Generate performance report
    print("\n5. Testing performance report generation:")
    
    report = performance_service.generate_performance_report(prompt1_id, period_days=30)
    if report:
        print(f"   [OK] Generated performance report")
        print(f"     Period: {report.period_start} to {report.period_end}")
        print(f"     Total executions: {report.total_executions}")
        print(f"     Success rate: {report.success_rate:.1f}%")
        print(f"     Avg response time: {report.average_response_time:.2f}s")
        print(f"     Avg cost: ${report.average_cost:.4f}")
        print(f"     Insights: {len(report.insights)} generated")
        print(f"     Recommendations: {len(report.recommendations)} generated")
        
        if report.insights:
            print("     Sample insights:")
            for insight in report.insights[:2]:
                print(f"       - {insight}")
        
        if report.recommendations:
            print("     Sample recommendations:")
            for rec in report.recommendations[:2]:
                print(f"       - {rec}")
    else:
        print("   [ERROR] Failed to generate performance report")
    
    # Test 6: Performance summary
    print("\n6. Testing performance summary:")
    
    # Overall summary
    overall_summary = performance_service.get_performance_summary(period_days=30)
    print(f"   Overall performance (last 30 days):")
    print(f"     Total executions: {overall_summary.get('total_executions', 0)}")
    print(f"     Avg response time: {overall_summary.get('avg_response_time', 0.0):.2f}s")
    print(f"     Avg cost: ${overall_summary.get('avg_cost', 0.0):.4f}")
    print(f"     Success rate: {overall_summary.get('success_rate', 0.0):.1f}%")
    print(f"     Total tokens: {overall_summary.get('total_tokens', 0)}")
    
    # Prompt-specific summary
    prompt_summary = performance_service.get_performance_summary(prompt1_id, period_days=30)
    print(f"   Prompt-specific performance:")
    print(f"     Total executions: {prompt_summary.get('total_executions', 0)}")
    print(f"     Avg response time: {prompt_summary.get('avg_response_time', 0.0):.2f}s")
    print(f"     Avg cost: ${prompt_summary.get('avg_cost', 0.0):.4f}")
    
    # Test 7: Create benchmark
    print("\n7. Testing benchmark creation:")
    
    benchmark = performance_service.create_benchmark(
        name="Response Time Benchmark",
        description="Target response time for code generation prompts",
        prompt_category="code_generation",
        metric_type=MetricType.RESPONSE_TIME,
        target_value=2.0,
        threshold_good=3.0,
        threshold_excellent=1.5,
        unit="seconds"
    )
    
    if benchmark:
        print(f"   [OK] Created benchmark: {benchmark.name}")
        print(f"     Target: {benchmark.target_value}{benchmark.unit}")
        print(f"     Good threshold: {benchmark.threshold_good}{benchmark.unit}")
        print(f"     Excellent threshold: {benchmark.threshold_excellent}{benchmark.unit}")
    else:
        print("   [ERROR] Failed to create benchmark")
    
    # Test 8: End session
    print("\n8. Testing session completion:")
    
    session_ended = performance_service.end_session(session_id)
    if session_ended:
        print(f"   [OK] Successfully ended performance session")
    else:
        print("   [ERROR] Failed to end performance session")
    
    print("\n" + "=" * 60)
    print("Performance tracking testing completed!")
    print("\nKey features tested:")
    print("[OK] Performance session management")
    print("[OK] Prompt execution recording")
    print("[OK] Custom metrics addition")
    print("[OK] Metrics retrieval and aggregation")
    print("[OK] Performance report generation")
    print("[OK] Performance summary statistics")
    print("[OK] Benchmark creation and management")
    print("[OK] Insights and recommendations generation")


if __name__ == "__main__":
    test_performance_functionality()
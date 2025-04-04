import sys
import time
from task_system import Task, SystemTask
import matplotlib.pyplot as plt
import networkx as nx

def test_basic_sequential():
    print("\n--- TEST: Basic Sequential Execution ---")
    
    execution_order = []
    
    def create_task_fn(name):
        def task_fn():
            execution_order.append(name)
            time.sleep(0.1)  
            print(f"  Task {name} completed")
        return task_fn
    
    tasks = [
        Task("A", run=create_task_fn("A")),
        Task("B", run=create_task_fn("B")),
        Task("C", run=create_task_fn("C")),
        Task("D", run=create_task_fn("D")),
        Task("E", run=create_task_fn("E")),
    ]
    
    precedences = {
        "A": [],
        "B": ["A"],
        "C": ["B"],
        "D": ["C"],
        "E": ["D"]
    }
    
    system = SystemTask(tasks, precedences)
    
    system.draw()
    print("Generated dependency graph for basic sequential test")
    
    print("Running sequentially:")
    system.runSeq()
    
    print(f"Execution order: {execution_order}")
    assert execution_order == ["A", "B", "C", "D","E"], "Tasks were not executed in the correct order"
    
    execution_order.clear()
    
    print("Running with parallelism:")
    system.run()
    
    print(f"Execution order: {execution_order}")
    assert execution_order == ["A", "B", "C", "D","E"], "Tasks were not executed in the correct order"


def test_parallel_execution():
    print("\n--- TEST: Parallel Execution ---")
    
    execution_times = {}
    
    def create_task_fn(name, duration):
        def task_fn():
            start_time = time.time()
            print(f"  Task {name} started at {start_time}")
            time.sleep(duration)  
            end_time = time.time()
            execution_times[name] = (start_time, end_time)
            print(f"  Task {name} completed after {end_time - start_time:.2f} seconds")
        return task_fn
    
    tasks = [
        Task("A", run=create_task_fn("A", 0.2)),
        Task("B", run=create_task_fn("B", 0.3)),
        Task("C", run=create_task_fn("C", 0.2)),
        Task("D", run=create_task_fn("D", 0.1)),
        Task("E", run=create_task_fn("E", 0.2)),
    ]
    
    precedences = {
        "A": [],
        "B": ["A"],
        "C": ["A"],
        "D": ["B", "C"],
        "E": ["B", "C"]
    }
    
    system = SystemTask(tasks, precedences)
    
    system.draw()
    print("Generated dependency graph for parallel execution test")
    
    print("Running with parallelism:")
    system.run()
    
    b_start, b_end = execution_times["B"]
    c_start, c_end = execution_times["C"]
    overlap_bc = min(b_end, c_end) - max(b_start, c_start)
    print(f"B and C overlap: {overlap_bc:.2f} seconds")
    assert overlap_bc > 0, "B and C did not run in parallel"
    
    d_start, d_end = execution_times["D"]
    e_start, e_end = execution_times["E"]
    overlap_de = min(d_end, e_end) - max(d_start, e_start)
    print(f"D and E overlap: {overlap_de:.2f} seconds")
    assert overlap_de > 0, "D and E did not run in parallel"
    
    assert d_start >= max(b_end, c_end), "D started before dependencies completed"
    assert e_start >= max(b_end, c_end), "E started before dependencies completed"
    
    plt.figure(figsize=(12, 6))
    tasks = ["A", "B", "C", "D", "E"]
    
    for i, task in enumerate(tasks):
        start, end = execution_times[task]
        duration = end - start
        plt.barh(i, duration, left=start - min(execution_times.values())[0], height=0.5, 
                 color=plt.cm.viridis(i / len(tasks)), alpha=0.8)
        plt.text(start - min(execution_times.values())[0] + duration/2, i, 
                 f"{task}: {duration:.2f}s", ha='center', va='center')
    
    plt.yticks(range(len(tasks)), tasks)
    plt.xlabel('Time (seconds)')
    plt.title('Task Execution Timeline')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('parallel_execution_timeline.png', dpi=300)
    print("Generated execution timeline visualization")


def test_resource_interference():
    print("\n--- TEST: Resource Interference ---")
    
    execution_times = {}
    
    def create_task_fn(name, duration):
        def task_fn():
            start_time = time.time()
            print(f"  Task {name} started at {start_time}")
            time.sleep(duration)  
            end_time = time.time()
            execution_times[name] = (start_time, end_time)
            print(f"  Task {name} completed after {end_time - start_time:.2f} seconds")
            
        return task_fn
    
    tasks = [
        Task("A", writes=["x"], run=create_task_fn("A", 0.2)),
        Task("B", reads=["x"], run=create_task_fn("B", 0.3)),
        Task("C", reads=["y"], run=create_task_fn("C", 0.2)),
        Task("D", writes=["x", "y"], run=create_task_fn("D", 0.1))
    ]
    
    precedences = {
        "A": [],
        "B": [],
        "C": [],
        "D": []
    }
    
    system = SystemTask(tasks, precedences)
    
    print("Checking task interference:")
    print(f"A and B interfere: {system._are_tasks_interfering(tasks[0], tasks[1])}")
    print(f"A and C interfere: {system._are_tasks_interfering(tasks[0], tasks[2])}")
    print(f"A and D interfere: {system._are_tasks_interfering(tasks[0], tasks[3])}")
    print(f"B and C interfere: {system._are_tasks_interfering(tasks[1], tasks[2])}")
    print(f"B and D interfere: {system._are_tasks_interfering(tasks[1], tasks[3])}")
    print(f"C and D interfere: {system._are_tasks_interfering(tasks[2], tasks[3])}")
    
    plt.figure(figsize=(8, 8))
    G = nx.Graph()
    for task in tasks:
        G.add_node(task.name)
    
    for i, task1 in enumerate(tasks):
        for task2 in tasks[i+1:]:
            if system._are_tasks_interfering(task1, task2):
                G.add_edge(task1.name, task2.name)
    
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', 
            node_size=700, font_size=10, font_weight='bold',
            edge_color='red', width=2, alpha=0.7)
    plt.title("Task Interference Graph")
    plt.savefig("resource_interference.png", dpi=300)
    print("Generated resource interference graph")
    
    max_parallelism = system._build_max_parallelism()
    print("Max parallelism:")
    for task, deps in max_parallelism.items():
        print(f" {task}: {deps}")
    
    
    plt.figure(figsize=(8, 8))
    G_derived = nx.DiGraph()
    for task_name in system.tasks:
        G_derived.add_node(task_name)
        for dep in max_parallelism[task_name]:
            G_derived.add_edge(dep, task_name)
    
    pos = nx.spring_layout(G_derived, seed=42)
    nx.draw(G_derived, pos, with_labels=True, node_color='lightgreen', 
            node_size=700, font_size=10, font_weight='bold',
            edge_color='blue', width=2, alpha=0.7)
    plt.title("Derived Dependency Graph After Interference Analysis")
    plt.savefig("derived_dependencies.png", dpi=300)
    print("Generated derived dependency graph")
    
    
    print("Running sequentially:")
    execution_times.clear()
    
    system.runSeq()
    
    # Show sequential execution times
    for name, (start, end) in sorted(execution_times.items()):
        print(f"  {name}: {start:.2f} - {end:.2f}")


def test_error_cases():
    """Test various error conditions"""
    print("\n--- TEST: Error Cases ---")
    
    print("1. Testing duplicate task names")
    try:
        tasks = [
            Task("A"),
            Task("A")  # Duplicate name
        ]
        precedences = {
            "A": []
        }
        SystemTask(tasks, precedences)
        print("  ERROR: Should have raised ValueError for duplicate task names")
    except ValueError as e:
        print(f"  Correct error: {e}")
    
    print("2. Testing missing task in precedences")
    try:
        tasks = [
            Task("A"),
            Task("B")
        ]
        precedences = {
            "A": []
        }
        SystemTask(tasks, precedences)
        print("  ERROR: Should have raised ValueError for missing task in precedences")
    except ValueError as e:
        print(f"  Correct error: {e}")
    
    print("3. Testing non-existent dependency")
    try:
        tasks = [
            Task("A"),
            Task("B")
        ]
        precedences = {
            "A": [],
            "B": ["C"]  
        }
        SystemTask(tasks, precedences)
        print("  ERROR: Should have raised ValueError for non-existent dependency")
    except ValueError as e:
        print(f"  Correct error: {e}")
    
    print("4. Testing cyclic dependencies")
    try:
        tasks = [
            Task("A"),
            Task("B"),
            Task("C")
        ]
        precedences = {
            "A": ["C"],
            "B": ["A"],
            "C": ["B"]  
        }
        SystemTask(tasks, precedences)
        print("  ERROR: Should have raised ValueError for cyclic dependencies")
    except ValueError as e:
        print(f"  Correct error: {e}")


def test_complex_workflow():
    print("\n--- TEST: Complex Workflow ---")
    
    execution_order = []
    execution_times = {}
    
    def create_task_fn(name, duration):
        def task_fn():
            start = time.time()
            execution_order.append(name)
            print(f"  Task {name} started")
            time.sleep(duration)  # Simulate work
            end = time.time()
            execution_times[name] = (start, end)
            print(f"  Task {name} completed after {end - start:.2f} seconds")
        return task_fn
    
    tasks = [
        Task("LoadData", writes=["data"], run=create_task_fn("LoadData", 0.3)),
        Task("ProcessA", reads=["data"], writes=["resultA"], run=create_task_fn("ProcessA", 0.2)),
        Task("ProcessB", reads=["data"], writes=["resultB"], run=create_task_fn("ProcessB", 0.4)),
        Task("ProcessC", reads=["data"], writes=["resultC"], run=create_task_fn("ProcessC", 0.3)),
        Task("MergeAB", reads=["resultA", "resultB"], writes=["mergedAB"], run=create_task_fn("MergeAB", 0.2)),
        Task("MergeC", reads=["resultC"], writes=["processedC"], run=create_task_fn("MergeC", 0.1)),
        Task("FinalMerge", reads=["mergedAB", "processedC"], writes=["final"], run=create_task_fn("FinalMerge", 0.2))
    ]
    
    
    precedences = {
        "LoadData": [],
        "ProcessA": ["LoadData"],
        "ProcessB": ["LoadData"],
        "ProcessC": ["LoadData"],
        "MergeAB": ["ProcessA", "ProcessB"],
        "MergeC": ["ProcessC"],
        "FinalMerge": ["MergeAB", "MergeC"]
    }
    
    system = SystemTask(tasks, precedences)
    
    print("Drawing the dependency graph")
    system.draw("complex_workflow.png")
    print("Generated complex workflow dependency graph")
    
    print("Running sequentially:")
    execution_order.clear()
    execution_times.clear()
    start_time = time.time()
    system.runSeq()
    sequential_time = time.time() - start_time
    print(f"Sequential execution time: {sequential_time:.2f} seconds")
    print(f"Sequential execution order: {execution_order}")
    
    
    plt.figure(figsize=(12, 6))
    task_names = list(execution_times.keys())
    for i, task in enumerate(task_names):
        start, end = execution_times[task]
        relative_start = start - min(t[0] for t in execution_times.values())
        duration = end - start
        plt.barh(i, duration, left=relative_start, height=0.5, 
                 color=plt.cm.viridis(i / len(task_names)), alpha=0.8)
        plt.text(relative_start + duration/2, i, 
                 f"{task}: {duration:.2f}s", ha='center', va='center')
    
    plt.yticks(range(len(task_names)), task_names)
    plt.xlabel('Time (seconds)')
    plt.title('Sequential Execution Timeline')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    print("Running with parallelism:")
    execution_order.clear()
    execution_times.clear()
    start_time = time.time()
    system.run()
    parallel_time = time.time() - start_time
    print(f"Parallel execution time: {parallel_time:.2f} seconds")
    print(f"Parallel execution order: {execution_order}")
    
    plt.figure(figsize=(12, 6))
    task_names = list(execution_times.keys())
    for i, task in enumerate(task_names):
        start, end = execution_times[task]
        relative_start = start - min(t[0] for t in execution_times.values())
        duration = end - start
        plt.barh(i, duration, left=relative_start, height=0.5, 
                 color=plt.cm.viridis(i / len(task_names)), alpha=0.8)
        plt.text(relative_start + duration/2, i, 
                 f"{task}: {duration:.2f}s", ha='center', va='center')
    
    plt.yticks(range(len(task_names)), task_names)
    plt.xlabel('Time (seconds)')
    plt.title('Parallel Execution Timeline')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    print(f"Speedup: {sequential_time / parallel_time:.2f}x")
    print("Complex workflow test completed")


if __name__ == "__main__":
    print("=== RUNNING TESTS FOR SYSTEMTASK ===")
    
    try:
        test_basic_sequential()
        test_parallel_execution()
        test_resource_interference()
        test_error_cases()
        test_complex_workflow()

        
        print("\n=== ALL TESTS COMPLETED SUCCESSFULLY ===")
        
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        sys.exit(1)
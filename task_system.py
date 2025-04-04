import threading
import time
import networkx as nx
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor

class Task:
    def __init__(self, name=None, reads=None, writes=None, run=None):
        self.name = name
        self.reads = reads or []
        self.writes = writes or []
        self.run = run
    
    def __str__(self):
        return f"Task({self.name})"
    
    def __repr__(self):
        return f"Task({self.name}, reads={self.reads}, writes={self.writes})"

class SystemTask:
    def __init__(self, tasks, precedences):
        self._validate_tasks(tasks)
        self._validate_precedences(tasks, precedences)
        
        self.tasks = {task.name: task for task in tasks}
        self.initial_precedences = precedences.copy()
        
        self.max_parallelism = self._build_max_parallelism()
    
    def _validate_tasks(self, tasks):
        task_names = [task.name for task in tasks]
        if len(task_names) != len(set(task_names)):
            duplicate_names = [name for name in task_names if task_names.count(name) > 1]
            raise ValueError(f"Duplicate task names found: {duplicate_names}")
    
    def _validate_precedences(self, tasks, precedences):
        
        task_names = [task.name for task in tasks]
        
        missing_tasks = set(task_names) - set(precedences.keys())
        if missing_tasks:
            raise ValueError(f"Tasks missing from precedences: {missing_tasks}")
        
        for task, deps in precedences.items():
            for dep in deps:
                if dep not in task_names:
                    raise ValueError(f"Non-existent dependency '{dep}' for task '{task}'")
        
        G = nx.DiGraph()
        for task_name in task_names:
            G.add_node(task_name)
        
        for task, deps in precedences.items():
            for dep in deps:
                G.add_edge(dep, task)
        
        if not nx.is_directed_acyclic_graph(G):
            cycles = list(nx.simple_cycles(G))
            raise ValueError(f"Cyclic dependencies detected: {cycles}")
    
    def _are_tasks_interfering(self, task1, task2):
        
        if set(task1.writes).intersection(set(task2.writes)):
            return True
        
        if set(task1.writes).intersection(set(task2.reads)):
            return True
        
        if set(task1.reads).intersection(set(task2.writes)):
            return True
        
        return False
    
    def _build_max_parallelism(self):
        
        max_parallel = {name: list(deps) for name, deps in self.initial_precedences.items()}
        
        task_names = list(self.tasks.keys())
        for i, task1_name in enumerate(task_names):
            for task2_name in task_names[i+1:]:
                if task2_name in max_parallel[task1_name] or task1_name in max_parallel[task2_name]:
                    continue
                
                if self._are_tasks_interfering(self.tasks[task1_name], self.tasks[task2_name]):
                    max_parallel[task2_name].append(task1_name)
        
        G = nx.DiGraph()
        for task_name in task_names:
            G.add_node(task_name)
        
        for task, deps in max_parallel.items():
            for dep in deps:
                G.add_edge(dep, task)
        
        if not nx.is_directed_acyclic_graph(G):
            raise ValueError("Maximum parallelism graph has cycles, which shouldn't happen")
        
        return max_parallel
    
    def runSeq(self):
        
        G = nx.DiGraph()
        for task_name in self.tasks:
            G.add_node(task_name)
        
        for task, deps in self.max_parallelism.items():
            for dep in deps:
                G.add_edge(dep, task)
        
        execution_order = list(nx.topological_sort(G))
        
        for task_name in execution_order:
            task = self.tasks[task_name]
            if task.run:
                task.run()
        
        return True
    
    def run(self):
        G = nx.DiGraph()
        for task_name in self.tasks:
            G.add_node(task_name)
        
        for task, deps in self.max_parallelism.items():
            for dep in deps:
                G.add_edge(dep, task)
        
        completed = set()
        completed_lock = threading.Lock()
        
        def execute_task(task_name):
            task = self.tasks[task_name]
            if task.run:
                task.run()
            with completed_lock:
                completed.add(task_name)
        
        with ThreadPoolExecutor() as executor:
            while len(completed) < len(self.tasks):
                ready_tasks = []
                for task_name in self.tasks:
                    if task_name not in completed:
                        deps = self.max_parallelism[task_name]
                        if all(dep in completed for dep in deps):
                            ready_tasks.append(task_name)
                
                if ready_tasks:
                    futures = [executor.submit(execute_task, task_name) for task_name in ready_tasks]
                    for future in futures:
                        future.result()
                else:
                    if len(completed) < len(self.tasks):
                        raise RuntimeError("Deadlock detected: no ready tasks but not all tasks completed")
        
        return True
    
    def draw(self, filename=None):
        
        plt.figure(figsize=(10, 8))
        G = nx.DiGraph()
        
        for task_name in self.tasks:
            G.add_node(task_name)
        
        for task, deps in self.max_parallelism.items():
            for dep in deps:
                G.add_edge(dep, task)
        
        pos = nx.spring_layout(G, seed=42)  # Consistent layout
        nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                node_size=700, font_size=10, font_weight='bold',
                edge_color='blue', width=2, alpha=0.7, arrows=True)
        
        plt.title("Task Dependency Graph (Maximum Parallelism)")
        
        if filename:
            plt.savefig(filename, dpi=300)
        plt.show()
    
    def test_determinism_random(self, globals_dict, num_trials=5):
        
        initial_state = {k: v for k, v in globals_dict.items() if not k.startswith('__')}
        
        results = []
        for _ in range(num_trials):
            for k, v in initial_state.items():
                globals_dict[k] = v
                
            self.run()
            
            written_vars = set()
            for task in self.tasks.values():
                written_vars.update(task.writes)
            
            state = {k: globals_dict.get(k) for k in written_vars}
            results.append(state)
            
        is_deterministic = all(results[0] == result for result in results[1:])
        
        if not is_deterministic:
            print("WARNING: Task system appears to be non-deterministic!")
            print("Results from different runs:")
            for i, result in enumerate(results):
                print(f"Run {i+1}:", result)
        else:
            print("Task system appears to be deterministic.")
            
        return is_deterministic
    
    def par_cost(self, num_trials=5):
        
        seq_times = []
        par_times = []
        
        print(f"Running performance comparison ({num_trials} trials each)...")
        
        for i in range(num_trials):
            start_time = time.time()
            self.runSeq()
            seq_time = time.time() - start_time
            seq_times.append(seq_time)
            
            start_time = time.time()
            self.run()
            par_time = time.time() - start_time
            par_times.append(par_time)
            
            print(f"Trial {i+1}: Sequential: {seq_time:.4f}s, Parallel: {par_time:.4f}s")
        
        avg_seq_time = sum(seq_times) / len(seq_times)
        avg_par_time = sum(par_times) / len(par_times)
        speedup = avg_seq_time / avg_par_time if avg_par_time > 0 else 0
        
        print(f"\nAverage sequential time: {avg_seq_time:.4f} seconds")
        print(f"Average parallel time: {avg_par_time:.4f} seconds")
        print(f"Speedup: {speedup:.2f}x")
        
        plt.figure(figsize=(10, 6))
        
        plt.bar([0, 1], [avg_seq_time, avg_par_time], color=['blue', 'green'], alpha=0.7)
        plt.xticks([0, 1], ['Sequential', 'Parallel'])
        plt.ylabel('Execution Time (seconds)')
        plt.title('Performance Comparison: Sequential vs Parallel')
        
        for i, (seq_t, par_t) in enumerate(zip(seq_times, par_times)):
            plt.plot([0], [seq_t], 'ro', alpha=0.5)
            plt.plot([1], [par_t], 'ro', alpha=0.5)
        
        plt.text(0.5, max(avg_seq_time, avg_par_time) * 0.95, 
                 f"Speedup: {speedup:.2f}x", 
                 horizontalalignment='center', fontsize=12)
        
        plt.tight_layout()
        plt.show()
        
        return avg_seq_time, avg_par_time, speedup
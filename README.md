# ProjetProcessusPython - Automatic Task Parallelization

This project implements a Python library for automating maximum parallelization of task systems. The library allows users to specify interdependent tasks that interact through shared variables and enables:

1. Automatic construction of a maximally parallelized task dependency graph
2. Sequential execution of tasks while respecting precedence constraints
3. Parallel execution of tasks while respecting precedence constraints

## 🚀 Features

- **Task Definition**: Define tasks with their read/write dependencies and execution functions
- **Automatic Dependency Analysis**: Automatically determine task dependencies using Bernstein conditions
- **Maximum Parallelism**: Generate a task system with maximum possible parallelism
- **Execution Modes**: Execute tasks sequentially or in parallel
- **Visualization**: View dependency graphs to understand task relationships
- **Determinism Testing**: Test for system determinism using randomized execution
- **Performance Measurement**: Compare sequential and parallel execution times

## 📋 Requirements

- Python 3.x
- NetworkX
- Matplotlib
- Threading (Standard Library)
- Concurrent.futures (Standard Library)

To install dependencies:

```bash
pip install networkx matplotlib
```

## 🔧 Usage

### Basic Example

```python
from task_system import Task, SystemTask

# Define global variables
X = None
Y = None
Z = None

# Define task functions
def runT1():
    global X
    X = 1

def runT2():
    global Y
    Y = 2

def runTsomme():
    global X, Y, Z
    Z = X + Y

# Create tasks
t1 = Task("T1", writes=["X"], run=runT1)
t2 = Task("T2", writes=["Y"], run=runT2)
tSomme = Task("somme", reads=["X", "Y"], writes=["Z"], run=runTsomme)

# Define initial precedence constraints
precedences = {
    "T1": [],
    "T2": [],
    "somme": []
}

# Create task system with maximum parallelism
system = SystemTask([t1, t2, tSomme], precedences)

# Visualize the task dependency graph
system.draw()

# Run sequentially
system.runSeq()

# Run in parallel
system.run()

# Test determinism
system.test_determinism_random(globals())

# Measure performance
system.par_cost()
```

### Complex Workflow Example

```python
# Create a more complex task system
tasks = [
    Task("LoadData", writes=["data"], run=load_data),
    Task("ProcessA", reads=["data"], writes=["resultA"], run=process_a),
    Task("ProcessB", reads=["data"], writes=["resultB"], run=process_b),
    Task("ProcessC", reads=["data"], writes=["resultC"], run=process_c),
    Task("MergeAB", reads=["resultA", "resultB"], writes=["mergedAB"], run=merge_ab),
    Task("MergeC", reads=["resultC"], writes=["processedC"], run=merge_c),
    Task("FinalMerge", reads=["mergedAB", "processedC"], writes=["final"], run=final_merge)
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
```

## 🧪 Testing

The project includes a comprehensive test suite in `test.py` that tests:

- Basic sequential execution
- Parallel execution
- Resource interference
- Error cases
- Complex workflow execution

Run tests with:

```bash
python test.py
```

## 🔍 How It Works

### Task Definition

Tasks are defined with:
- A unique name
- A list of variables read by the task
- A list of variables written by the task
- A function to execute

### Maximum Parallelism Construction

The system determines which tasks can run in parallel by:
1. Starting with the initial precedence constraints
2. Analyzing task interference using Bernstein conditions (read/write conflicts)
3. Adding necessary dependencies to ensure correctness
4. Creating a directed acyclic graph (DAG) that represents task dependencies

### Execution Modes

- **Sequential**: Tasks are executed in topological order based on the dependency graph
- **Parallel**: Tasks are executed as soon as all their dependencies have completed, using thread pools

## 📝 Project Structure

- `task_system.py`: Main library file containing `Task` and `SystemTask` classes
- `test.py`: Test suite demonstrating various features and use cases

## 👥 Authors

- MOULAI HACENE Rania
- Terfi Mohammed Wassim
- Zeggane Walid

## 📚 Documentation

For more detailed information, please see the project documentation included with the source code.

## 📄 License

This project is available for educational and research purposes.

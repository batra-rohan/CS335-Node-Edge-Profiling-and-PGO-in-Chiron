# CS335: Compiler Design (2024-25 Spring) Project

## Project Title
**Node and Edge Profiling with Profile-Guided Optimization (PGO) in Chiron**

## Team Members
- **Anubhav Rana** (210162)  
- **Rohan Batra** (210868)

---

## Project Overview
This project involves collecting node and edge profiling data using the Chiron framework and implementing Profile-Guided Optimization (PGO). The work is divided into multiple milestones, each focusing on specific enhancements and functionalities.

---

## Milestones

### Milestone 1 (10<sup>th</sup> February 2025)
#### Work Done:
1. **Chiron Framework Setup**:
   - Installed and understood the working of the Chiron framework.

2. **New Instruction Commands**:
   - **Array Initialization**: Creates an integer array of a given size and initializes all elements to 0.  
     _Fields_: Array Name, Array Length.
   - **Array Increment**: Increments the value stored in a specific array element.  
     _Fields_: Array Name, Array Index of the element to be incremented.

3. **Profiling Section**:
   - Created `Instrumentation.py` to compute leader indices and add instrumentation code (counter initialization and increments) for each basic block.

4. **Command-Line Flag**:
   - Added `-prfl` flag to:
     - Add instrumentation code.
     - Print the augmented IR.
     - Execute the code and store profiling data (node counters) in a `.csv` file.

---

### Milestone 2 (19<sup>th</sup> March 2025)
#### Work Done:
1. **New Instruction Command**:
   - **Array Assignment**: Assigns a value to a specific array element.  
     _Fields_: Array Name, Array Index, Value to be assigned.

2. **IR Handler Augmentation**:
   - Enhanced the `Add` instruction to handle conditionals and update target offsets of other instructions correctly.

3. **Edge Profiling**:
   - Implemented instrumentation for edge profiling of critical (jump) edges.

4. **Output Enhancements**:
   - Wrote code to display profiling data for nodes and edges in a `.csv` file.
  
---

### Milestone 3 (2<sup>nd</sup> April 2025)
#### Work Done:
- Implemented arrays: Array Initialization and Array Arithmetic operations support in Chiron across frontend and backend.

---

### Final Submission (20<sup>th</sup> April 2025)
#### Work Done:
- Implemented the optimal algorithm for profiling from *Optimally Profiling and Tracing Programs* by Thomas Ball and James R. Larus.
- Provided functionality to collect profiling data for multiple inputs from an input file.
- Implemented a data visualizer that combines all the profiling data and presents it annotated to the IR (inspired by gprof's annotated source listing).

---

## Execution Instructions

### Collecting Profiling Data
#### Example Command for collecting data:
```bash
$ cd ChironCore
$ ./chiron.py -prfl ./example/example1.tl -input_file example1_input.text
```

#### Current Functionality:
1. **Control Flow Graphs**:
   - Generates and saves the control flow graph for the original (un-instrumented) IR as `control_flow_graph_$ProgName$.png`.
   - Generates and saves the control flow graph for the instrumented IR as `control_flow_graph_prfl_$ProgName$.png`.

2. **Instrumentation**:
   - Adds instrumentation code for node profiling and edge profiling of critical edges as per the optimal algorithm.

3. **Execution and Profiling**:
   - Executes the instrumented code for each set of input parameters in the input file, computes the profiling data, and dumps it.

4. **Output**:
   - Dumps the node profiling data into a `.csv` file named `{file_name}_run_*_node_counts.csv` for each input parameter set in the input file.
   - Dumps the edge profiling data into a `.csv` file named `{file_name}_run_*_edge_counts.csv` for each input parameter set in the input file.

---

## Output `.csv` File Format

### Node Data
The output `.csv` file for the node data contains the following columns:
1. **Node**: Leader indices (index position in the IR) of the basic block.
2. **Node Counter**: Node counters for the basic block.

### Edge Data
The output `.csv` file for the edge data contains the following columns:
1. **Source**: Leader index of the source node (basic block) of the edge.
2. **Target**: Leader index of the destination (target) node (basic block) of the edge.
3. **Fall Through Edge Counter**: Count value for that edge.

---

## Visualizing Collected Profile Data
#### Example Command for visualizing data:
```bash
$ cd ChironCore
$ ./chiron.py -vis ./example/example1.tl 
```

#### Current Functionality:
This feature automatically reads the profiling data for all the runs corresponding to the program (all the files with the file name format) and combines the complete data.

**Output**:
   - Dumps the combined node profiling data into a `.csv` file named `{file_name}_total_node_counts.csv`.
   - Dumps the combined edge profiling data into a `.csv` file named `{file_name}_total_edge_counts.csv`.
   - Prints the program IR annotated with the combined profiling data.

---

## Output Format

Annotated IR instructions are formatted as:
- **x, y, z --> IR Instruction**  
- **x, y --> IR Instruction**

The first instruction of all the basic blocks (instructions at leader indices) are annotated:
- `x`: Node count for the basic block.
- `y`: Edge count for the jump edge / the edge count for the control flow edge (always taken).
- `z` (if present): Edge count for the fall-through edge.

---

## Future Work
1. Implement Profile-Guided Optimizations (PGO) based on the collected profiling data.

---

## Supplementary Information: Profiling Algorithm

We have used the optimal `Eprfl(Ecnt)` from the paper: *Optimally Profiling and Tracing Programs* by Thomas Ball and James R. Larus.  
DOI: [https://dl.acm.org/doi/pdf/10.1145/183432.183527](https://dl.acm.org/doi/pdf/10.1145/183432.183527)  
Node counts have been inferred from the collected edge profiling data.

---




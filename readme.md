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

## Execution Instructions

### Example Command:
```bash
$ cd ChironCore
$ ./chiron.py -prfl ./example/example1.tl -d '{":x": 20, "y": 30, ":z": 20, ":p": 40}'
```

### Current Functionality:
1. **Control Flow Graphs**:
   - Generates and saves the control flow graph for the original (un-instrumented) IR as `control_flow_graph_$ProgName$.png`.
   - Generates and saves the control flow graph for the instrumented IR as `control_flow_graph_prfl_$ProgName$.png`.

2. **Instrumentation**:
   - Adds instrumentation code for node profiling and edge profiling of critical edges.

3. **Execution and Profiling**:
   - Executes the modified program, updates counters, and calculates profiling data.

4. **Output**:
   - Dumps profiling data into a `.csv` file named `Profiling_Data_$ProgName$.csv`.

---

## Output `.csv` File Format

The output `.csv` file contains the following columns:
1. **Leader Index of Basic Block**: Leader indices of all basic blocks.
2. **Node Counter**: Node counters for each basic block.
3. **Jump Target LI**: Leader index of the target node (basic block) for jump edges.
4. **Jump Edge Counter**: Counter for the edge between the current block and the jump target.
5. **Fall Through Edge Counter**: Counter for the fall-through edge (if any). Displays `-1` if no fall-through edge exists.

---

## Testing

- Test programs are available in the `Test_Progs` folder. These include examples with nested loops, conditionals, and complex jumps/fall-throughs.
- The correctness of the profiling functionality has been verified by:
  - Comparing output patterns generated using the `-r` and `-prfl` flags to ensure identical semantics and control flow.
  - Analyzing control flow graphs to verify profiling counters and matching them with output data.

---

## Future Work
1. Collect and analyze profiling data for various examples.
2. Implement Profile-Guided Optimizations (PGO).
3. Enable execution with random inputs and display combined profiling data.

---

## Supplementary Information: Profiling Algorithm

### Node Profiling
1. Compute leader indices of the program and build the control flow graph (CFG).
2. Initialize a node counter array (size = number of basic blocks) to zero.
3. Add a node counter at the start of each basic block to count executions.

### Edge Profiling
1. Create three arrays (size = number of edges in CFG) to store:
   - Counter values.
   - Source leader indices.
   - Target leader indices.
2. For each critical jump edge:
   - Modify the target to jump to an intermediate point where:
     - The counter is updated.
     - Source and target indices are set.
   - Jump to the originally intended target.
3. Profiling data for fall-through and unconditional edges is computed using node data and critical edge counters.

---




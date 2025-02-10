# CS335:Compiler Design (2024-25 Spring) Project
## Project Title:
To collect node and edge profiling data through Chiron and implement PGO.
## Team Members
Anubhav Rana (210162)<br>Rohan Batra (210868)
## Project Stages
## Milestone-1 (10 <sup> th</sup> February 2025)
### Work Done:
- Installed and understood the working of the Chiron Framework.
- Created new **Array Initialisation** and **Array Increment** Instruction Commands (definition in Chiron AST and handling in Interpreter) for the instrumentation code. Currently supported operations in arrays:
  - **Array Initialisation**: Create an (integer) array of a given size and initialise all its elements to 0.  
    _Fields_: Array Name, Array Length.
  - **Array Increment**: Increment the value stored in a particular array element.  
    _Fields_: Array Name, Array Index of element to be incremented.
- Created Profiling Section with `Instrumentation.py` that computes the leader indices, adds instrumentation code (counter initialisation and counter increments) corresponding to each basic block.
- Created `-prfl` command-line flag (operation mode) that:
  - Adds the instrumentation code.
  - Prints the augmented IR.
  - Runs the code and stores the obtained profiling data (node counters) to a `.csv` file.

### Execution Command for running an example:
```bash
$ cd ChironCore
$ ./chiron.py -prfl ./example/example1.tl -d '{":x": 20, "y": 30, ":z": 20, ":p": 40}'
```
### Current Functionality:
It adds suitable instrumentation code for node profiling into the IR , runs the programme , collects and stores the corresponding node profile counters in a .csv file.

### Future Work
- To implement Edge Profiling<br>
- To collect and analyse the profiling data for various examples <br>
- To impement Profile Guided Optimisations




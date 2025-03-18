from ChironAST import ChironAST
from ChironHooks import Chironhooks
import turtle
import csv
import os
import numpy as np
from bisect import bisect_left  # Import for binary search

Release="Chiron v5.3"

def addContext(s):
    return str(s).strip().replace(":", "self.prg.")

class Interpreter:
    # Turtle program should not contain variable with names "ir", "pc", "t_screen"
    ir = None
    pc = None
    t_screen = None
    trtl = None

    def __init__(self, irHandler, params):
        self.ir = irHandler.ir
        self.cfg = irHandler.cfg
        self.pc = 0
        self.t_screen = turtle.getscreen()
        self.trtl = turtle.Turtle()
        self.trtl.shape("turtle")
        self.trtl.color("blue", "yellow")
        self.trtl.fillcolor("green")
        self.trtl.begin_fill()
        self.trtl.pensize(4)
        self.trtl.speed(1) # TODO: Make it user friendly

        if params is not None:
            self.args = params
        else:
            self.args = None

        turtle.title(Release)
        turtle.bgcolor("white")
        turtle.hideturtle()

    def handleAssignment(self, stmt,tgt):
        raise NotImplementedError('Assignments are not handled!')

    def handleCondition(self, stmt, tgt):
        raise NotImplementedError('Conditions are not handled!')

    def handleMove(self, stmt, tgt):
        raise NotImplementedError('Moves are not handled!')

    def handlePen(self, stmt, tgt):
        raise NotImplementedError('Pens are not handled!')

    def handleGotoCommand(self, stmt, tgt):
        raise NotImplementedError('Gotos are not handled!')

    def handleNoOpCommand(self, stmt, tgt):
        raise NotImplementedError('No-Ops are not handled!')

    def handlePauseCommand(self, stmt, tgt):
        raise NotImplementedError('No-Ops are not handled!')

    def sanityCheck(self, irInstr):
        stmt, tgt = irInstr
        # if not a condition command, rel. jump can't be anything but 1
        if not isinstance(stmt, ChironAST.ConditionCommand):
            if tgt != 1:
                raise ValueError("Improper relative jump for non-conditional instruction", str(stmt), tgt)
    
    def interpret(self):
        pass

    def initProgramContext(self, params):
        pass

class ProgramContext:
    pass

# TODO: move to a different file
class ConcreteInterpreter(Interpreter):
    # Ref: https://realpython.com/beginners-guide-python-turtle
    cond_eval = None # used as a temporary variable within the embedded program interpreter
    prg = None

    def __init__(self, irHandler, params):
        super().__init__(irHandler, params)
        self.prg = ProgramContext()
        # Hooks Object:
        if self.args is not None and self.args.hooks:
            self.chironhook = Chironhooks.ConcreteChironHooks()
        self.pc = 0

    def interpret(self):
        print("Program counter : ", self.pc)
        stmt, tgt = self.ir[self.pc]
        print(stmt, stmt.__class__.__name__, tgt)

        self.sanityCheck(self.ir[self.pc])

        if isinstance(stmt, ChironAST.AssignmentCommand):
            ntgt = self.handleAssignment(stmt, tgt)
        elif isinstance(stmt, ChironAST.ConditionCommand):
            ntgt = self.handleCondition(stmt, tgt)
        elif isinstance(stmt, ChironAST.MoveCommand):
            ntgt = self.handleMove(stmt, tgt)
        elif isinstance(stmt, ChironAST.PenCommand):
            ntgt = self.handlePen(stmt, tgt)
        elif isinstance(stmt, ChironAST.GotoCommand):
            ntgt = self.handleGotoCommand(stmt, tgt)
        elif isinstance(stmt, ChironAST.NoOpCommand):
            ntgt = self.handleNoOpCommand(stmt, tgt)
        elif isinstance(stmt,ChironAST.ArrayInitialise):
            ntgt=self.handleArrayInit(stmt,tgt)
        elif isinstance(stmt,ChironAST.ArrayIncrement):
            ntgt=self.handleArrayIncr(stmt,tgt)
        elif isinstance(stmt,ChironAST.ArrayAssignment):
            ntgt=self.handleArrayAss(stmt,tgt)
        else:
            raise NotImplementedError("Unknown instruction: %s, %s."%(type(stmt), stmt))

        # TODO: handle statement
        self.pc += ntgt

        if self.pc >= len(self.ir):
            # This is the ending of the interpreter.
            self.trtl.write("End, Press ESC", font=("Arial", 15, "bold"))
            if self.args is not None and self.args.hooks:
                self.chironhook.ChironEndHook(self)
            return True
        else:
            return False
    
    def initProgramContext(self, params):
        # This is the starting of the interpreter at setup stage.
        if self.args is not None and self.args.hooks:
            self.chironhook.ChironStartHook(self)
        self.trtl.write("Start", font=("Arial", 15, "bold"))
        for key,val in params.items():
            var = key.replace(":","")
            exec("setattr(self.prg,\"%s\",%s)" % (var, val))
    
    def handleAssignment(self, stmt, tgt):
        print("  Assignment Statement")
        # print(stmt)
        lhs = str(stmt.lvar).replace(":","")
        rhs = addContext(stmt.rexpr)
        # print(lhs)
        # print(rhs)
        exec("setattr(self.prg,\"%s\",%s)" % (lhs,rhs))
        return 1

    def handleCondition(self, stmt, tgt):
        print("  Branch Instruction")
        condstr = addContext(stmt)
        exec("self.cond_eval = %s" % (condstr))
        return 1 if self.cond_eval else tgt

    def handleMove(self, stmt, tgt):
        print("  MoveCommand")
        exec("self.trtl.%s(%s)" % (stmt.direction,addContext(stmt.expr)))
        return 1

    def handleNoOpCommand(self, stmt, tgt):
        print("  No-Op Command")
        return 1

    def handlePen(self, stmt, tgt):
        print("  PenCommand")
        exec("self.trtl.%s()"%(stmt.status))
        return 1

    def handleGotoCommand(self, stmt, tgt):
        print(" GotoCommand")
        xcor = addContext(stmt.xcor)
        ycor = addContext(stmt.ycor)
        exec("self.trtl.goto(%s, %s)" % (xcor, ycor))
        return 1
    def handleArrayInit(self,stmt,tgt):
        print("Array Initialisation Command")
        n=stmt.len
        exec(f"setattr(self.prg, '{stmt.name}', [0] * {n})")
        return 1
    def handleArrayIncr(self,stmt,tgt):
        print("Array Increment Command")
        pos=stmt.idx
        exec(f"self.prg.{stmt.name}[{pos}] += 1")
        return 1
    def handleArrayAss(self,stmt,tgt):
        print("Array Assignemnt Command")
        pos=stmt.idx
        exec(f"self.prg.{stmt.name}[{pos}] = {stmt.value}")
        return 1
    
    # def DumpProfilingData(self, leaderIndices):
    #     file_path = self.args.progfl

    #     # Extracting the filename without the extension
    #     filename = os.path.splitext(os.path.basename(file_path))[0]

    #     # Obtain the node counters
    #     node_counter_array = getattr(self.prg, 'node_counters')

    #     # Obtain the edge-related arrays
    #     edge_counter_array = getattr(self.prg, 'edge_counters')
    #     edge_source_array = getattr(self.prg, 'edge_source')
    #     edge_target_array = getattr(self.prg, 'edge_target')

    #     # Initialize arrays for jump and fall-through counters
    #     jump_target_array = np.zeros(len(node_counter_array), dtype=int)
    #     jump_counter_array = np.zeros(len(node_counter_array), dtype=int)
    #     fall_through_counter_array = np.zeros(len(node_counter_array), dtype=int)

    #     # Compute jump and fall-through counters
    #     for idx, source in enumerate(edge_source_array):
    #         target = edge_target_array[idx]

    #         # Perform binary search to find the indices of source and target in leaderIndices
    #         source_idx = bisect_left(leaderIndices, source)
    #         if source != target:
    #             # Has Jump
    #             jump_target_array[source_idx] = target
    #             jump_counter_array[source_idx] += edge_counter_array[idx]


    #     # Compute fall-through counters as node counter minus jump counter
    #     for idx in range(len(node_counter_array)):
    #         fall_through_counter_array[idx] = node_counter_array[idx] - jump_counter_array[idx]

    #     # For nodes where jump counters are not updated, set them equal to node counters
    #     for idx in range(len(node_counter_array)):
    #         if jump_counter_array[idx] == 0:
    #             jump_counter_array[idx] = node_counter_array[idx]
    #             fall_through_counter_array[idx]=-1
                
    #     # Generate the output filename
    #     filename = f"Profiling_Data_{filename}.csv"

    #     # Write profiling data to CSV
    #     with open(filename, 'w', newline='') as file:
    #         fieldnames = [
    #             'Leader Index of Basic Block',
    #             'Node Counter',
    #             'Jump Target LI',
    #             'Jump Edge Counter',
    #             'Fall Through Edge Counter'
    #         ]
    #         writer = csv.writer(file)

    #         # Write the header
    #         writer.writerow(fieldnames)

    #         # Write each block and its counter value
    #         for idx, leader_index in enumerate(leaderIndices):
    #             node_counter = node_counter_array[idx]
    #             jump_target_li = jump_target_array[idx]
    #             jump_edge_counter = jump_counter_array[idx]
    #             fall_through_edge_counter = fall_through_counter_array[idx]

    #             writer.writerow([
    #                 leader_index,
    #                 node_counter,
    #                 jump_target_li,
    #                 jump_edge_counter,
    #                 fall_through_edge_counter
    #             ])

    def DumpProfilingData(self,leaderIndices):
        file_path = self.args.progfl

        # Extracting the filename without the extension
        filename = os.path.splitext(os.path.basename(file_path))[0]

        # Initialize the block_counters dictionary
        block_counters = {}

        # Obtainig the node counters
        counter_array = getattr(self.prg, 'node_counters')

        for idx, count in enumerate(counter_array):
            block_counters[leaderIndices[idx]] = count

        filename = f"Profiling_Data_{filename}.csv"

        # Write block_counters to CSV
        with open(filename, 'w', newline='') as file:
            fieldnames = ['Leader Index of Basic block', 'Node Counter']
            writer = csv.writer(file)

            # Write the header
            writer.writerow(fieldnames)

            # Write each block and its counter value
            for key, value in block_counters.items():
                writer.writerow([key, value])
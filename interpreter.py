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
        # elif isinstance(stmt,ChironAST.ArrayIncrement):
        #     ntgt=self.handleArrayIncr(stmt,tgt)
        # elif isinstance(stmt,ChironAST.ArrayAssignment):
        #     ntgt=self.handleArrayAss(stmt,tgt)
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
        print(lhs)
        print(rhs)
        if stmt.flag:
            exec(f"self.prg.{lhs} = {rhs}")
        else:
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
    # def handleArrayIncr(self,stmt,tgt):
    #     print("Array Increment Command")
    #     pos=stmt.idx
    #     exec(f"self.prg.{stmt.name}[{pos}] += 1")``
    #     return 1
    # def handleArrayAss(self,stmt,tgt):
    #     print("Array Assignemnt Command")
    #     pos=stmt.idx
    #     exec(f"self.prg.{stmt.name}[{pos}] = {stmt.value}")
    #     return 1
    
    def DumpProfilingData(self, leaderIndices):
        file_path = self.args.progfl

        # Extracting the filename without the extension
        filename = os.path.splitext(os.path.basename(file_path))[0]

        # Reconstruct edge list from prg attributes
        edge_source_array = getattr(self.prg, 'edge_source')
        edge_target_array = getattr(self.prg, 'edge_target')
        edge_instr_idx_array = getattr(self.prg, 'edge_instr_indices')
        edge_instr_values = getattr(self.prg, 'edge_counters')

        # Build actual edge tuples from indices
        ecnt_edges = []
        for i in edge_instr_idx_array:
            src = edge_source_array[i]
            tgt = edge_target_array[i]
            for e in self.cfg.edges():
                if e[0].irID == src and e[1].irID == tgt:
                    ecnt_edges.append(e)
                    break

        # Compute edge counters for all edges
        edge_counter_map = propagate_counts(self.cfg, ecnt_edges, edge_instr_values)

        # Map nodes to indices and back
        node_id_map = {node: idx for idx, node in enumerate(self.cfg.nodes())}
        node_counter_map = compute_node_counters(self.cfg, edge_counter_map)

        # Convert edge counters to arrays for dumping
        edge_counter_array = []
        edge_src_array = []
        edge_tgt_array = []
        for (u, v), count in edge_counter_map.items():
            edge_counter_array.append(count)
            edge_src_array.append(u.irID)
            edge_tgt_array.append(v.irID)

        # Convert node counters to array
        node_counter_array = [0] * len(self.cfg.nodes())
        for node, count in node_counter_map.items():
            node_counter_array[node_id_map[node]] = count

        # Generate the output filename
        filename = f"Profiling_Data_{filename}.csv"

        # Write profiling data to CSV
        with open(filename, 'w', newline='') as file:
            fieldnames = [
                'Edge Index',
                'Source Node',
                'Target Node',
                'Edge Counter',
                '',
                'Node Index',
                'Node Counter'
            ]
            writer = csv.writer(file)
            writer.writerow(fieldnames)

            max_len = max(len(edge_counter_array), len(node_counter_array))
            for i in range(max_len):
                edge_idx_data = [i, edge_src_array[i], edge_tgt_array[i], edge_counter_array[i]] if i < len(edge_counter_array) else ['', '', '', '']
                node_idx_data = [i, node_counter_array[i]] if i < len(node_counter_array) else ['', '']
                writer.writerow(edge_idx_data + [''] + node_idx_data)

def propagate_counts(cfg, ecnt_edges, edge_counters):
    """
    Given a set of edges `ecnt_edges` (those instrumented) and their counters,
    compute the frequencies for all other edges in the CFG using edge propagation algorithm.
    """
    all_edges = list(cfg.edges())
    cnt = {e: 0 for e in all_edges}

    # Initialize counters for instrumented edges
    for idx, e in enumerate(ecnt_edges):
        cnt[e] = edge_counters[idx]

    def dfs(v, incoming_edge):
        in_edges = [e for e in all_edges if e[1] == v]
        out_edges = [e for e in all_edges if e[0] == v]

        in_sum = 0
        for e in in_edges:
            if e != incoming_edge and e not in ecnt_edges:
                dfs(e[0], e)
            in_sum += cnt[e]

        out_sum = 0
        for e in out_edges:
            if e != incoming_edge and e not in ecnt_edges:
                dfs(e[1], e)
            out_sum += cnt[e]

        if incoming_edge is not None and incoming_edge not in ecnt_edges:
            cnt[incoming_edge] = max(in_sum, out_sum) - min(in_sum, out_sum)

    # Run DFS from the entry point of the CFG
    entry_node = cfg.graph['entry'] if 'entry' in cfg.graph else list(cfg.nodes)[0]
    dfs(entry_node, None)

    return cnt

def compute_node_counters(cfg, edge_counters):
    """
    Compute node counters from edge counters by summing the incoming edges for each node.
    Alternatively, summing outgoing edges is also valid if edge counts are consistent.
    """
    node_counters = {v: 0 for v in cfg.nodes()}
    for (u, v), count in edge_counters.items():
        node_counters[v] += count
    return node_counters

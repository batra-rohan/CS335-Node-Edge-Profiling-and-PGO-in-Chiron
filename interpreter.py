from ChironAST import ChironAST
from ChironHooks import Chironhooks
import turtle
import csv
import os
import numpy as np
from bisect import bisect_left  # Import for binary search

Release="Chiron v5.3"

def give_ir_ids(edge):
    a=-1 if edge[0].irID=="START" else edge[0].irID
    b=-1 if edge[1].irID=="START" else edge[1].irID
    return (a,b)
def give_node_ir(n):
    if(n.irID=="START"):
        return -1
    else:
        return n.irID
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
        cfg = irHandler.cfg
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
import csv
from collections import defaultdict, deque

class EdgePropagator:
    def __init__(self, cfg, edge_source_array, edge_target_array, edge_instr_values,instru_edges):
        self.cfg = cfg

        self.count_instr_edges = [(src,dst)for src, dst in zip(edge_source_array, edge_target_array)]
        self.known_counts = dict(zip(self.count_instr_edges, edge_instr_values))
        self.edge_list=[give_ir_ids(e) for e in instru_edges]
        self.all_edges =[give_ir_ids(e) for e in cfg.edges()]
        self.Ecnt = set(self.known_counts.keys())  # known edge frequencies
        self.cnt = {e: self.known_counts.get(e, 0) for e in self.all_edges}
        print(self.known_counts)
        print(self.cnt)

    def propogate_counts(self):
        for node in self.cfg.nodes():
            if node and node.irID == "START":
                start_node = node
                break
        self._dfs(start_node,None)
    
    def _dfs(self,v,parent_edge):
        in_edges = [(u, v) for u in self.cfg.predecessors(v)]
        out_edges = [(v, w) for w in self.cfg.successors(v)]

        in_sum=0
        for e in in_edges:
            e_irs=give_ir_ids(e)
            if(e!=parent_edge and e_irs not in self.edge_list):
                self._dfs(e[0],e,)
            in_sum=in_sum+self.cnt[e_irs]
        
        out_sum=0
        for e in out_edges:
            e_irs=give_ir_ids(e)
            if(e!=parent_edge and e_irs not in self.edge_list):
                self._dfs(e[1],e)
            out_sum=out_sum+self.cnt[e_irs]

        if parent_edge is not None:
            self.cnt[give_ir_ids(parent_edge)]=max(in_sum,out_sum)-min(in_sum,out_sum)


    def compute_node_counts(self):
        node_count=[]
        for node in self.cfg.nodes():
            out_edges = [(node, w) for w in self.cfg.successors(node)]
            n_count=0
            for edge in out_edges:
                n_count+=self.cnt[give_ir_ids(edge)]
            node_count.append((give_node_ir(node),n_count))
        return node_count


    def write_to_csv(self, edge_csv_path, node_csv_path):
        with open(edge_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Source", "Target", "Frequency"])
            for (u, v), freq in self.cnt.items():
                u=u if u=="END" else u+1
                v=v if v=="END" else v+1
                writer.writerow([u, v, freq])

        node_count = self.compute_node_counts()
        with open(node_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Node", "Count"])
            for items in node_count:
                node=items[0]
                node=node if node=="END" else node+1
                count=items[1]
                writer.writerow([node, count])

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

        # self.sanityCheck(self.ir[self.pc])

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
        return tgt

    def handleCondition(self, stmt, tgt):
        print("  Branch Instruction")
        condstr = addContext(stmt)
        exec("self.cond_eval = %s" % (condstr))
        return 1 if self.cond_eval else tgt

    def handleMove(self, stmt, tgt):
        print("  MoveCommand")
        exec("self.trtl.%s(%s)" % (stmt.direction,addContext(stmt.expr)))
        return tgt

    def handleNoOpCommand(self, stmt, tgt):
        print("  No-Op Command")
        return tgt

    def handlePen(self, stmt, tgt):
        print("  PenCommand")
        exec("self.trtl.%s()"%(stmt.status))
        return tgt

    def handleGotoCommand(self, stmt, tgt):
        print(" GotoCommand")
        xcor = addContext(stmt.xcor)
        ycor = addContext(stmt.ycor)
        exec("self.trtl.goto(%s, %s)" % (xcor, ycor))
        return tgt
    def handleArrayInit(self,stmt,tgt):
        print("Array Initialisation Command")
        n=stmt.len
        exec(f"setattr(self.prg, '{stmt.name}', [0] * {n})")
        return tgt
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
    
    def DumpProfilingData(self, cfg,instru_edges,filename):
        # Reconstruct edge list from prg attributes
        edge_source_array = getattr(self.prg, 'edge_source')
        edge_target_array = getattr(self.prg, 'edge_target')
        edge_instr_values = getattr(self.prg, 'edge_counters')
        propagator = EdgePropagator(cfg, edge_source_array, edge_target_array, edge_instr_values,instru_edges)
        propagator.propogate_counts()
        propagator.write_to_csv(f"{filename}_edge_frequencies.csv", f"{filename}_node_counts.csv")
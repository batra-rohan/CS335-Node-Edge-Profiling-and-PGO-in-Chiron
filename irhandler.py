import antlr4
import pickle
import numpy as np
from turtparse.parseError import *
from turtparse.tlangParser import tlangParser
from turtparse.tlangLexer import tlangLexer

from ChironAST import ChironAST


def getParseTree(progfl):
    input_stream = antlr4.FileStream(progfl)
    print(input_stream)
    try:
        lexer = tlangLexer(input_stream)
        stream = antlr4.CommonTokenStream(lexer)
        lexer._listeners = [SyntaxErrorListener()]
        tparser = tlangParser(stream)
        tparser._listeners = [SyntaxErrorListener()]
        tree = tparser.start()
    except Exception as e:
        print("\033[91m\n====================")
        print(e.__str__() + "\033[0m\n")
        exit(1)

    return tree


class IRHandler:
    def __init__(self, ir=None, cfg=None):
        # statement list
        self.ir = ir
        # control flow graph
        self.cfg = cfg

    def setIR(self, ir):
        self.ir = ir

    def setCFG(self, cfg):
        self.cfg = cfg

    def dumpIR(self, filename, ir):
        with open(filename, "wb") as f:
            pickle.dump(ir, f)

    def loadIR(self, filename):
        f = open(filename, "rb")
        ir = pickle.load(f)
        self.ir = ir
        return ir

    def updateJumpUpperCond(self, stmtList, index, pos, add_node_cnt):
        stmt, tgt = stmtList[index]
       # Update the conditional targets which point below the added instruction position
        if(add_node_cnt==0):
            if tgt > 0 and index + tgt >= pos:
                newTgt = tgt + 1
                # update curr conditional instruction's target
                stmtList[index] = (stmt, newTgt)
        else:
            # for the case when we adding the node counter instruction , we need one less increment
            # so that the jump happens to the correct position (node counter instruction)

            if tgt > 0 and index + tgt > pos:
                newTgt = tgt + 1
                # update curr conditional instruction's target
                stmtList[index] = (stmt, newTgt)
        

    def updateJumpLowerCond(self, stmtList, index, pos,add_node_cnt):
        # Update the conditional targets below the added instruction whose jump is above it
        stmt, tgt = stmtList[index]
        if(add_node_cnt==0):
            if tgt < 0 and index + tgt < pos:
                newTgt = tgt -1
                # update curr conditional instruction's target
                stmtList[index] = (stmt, newTgt)
        else:
            # similra to the above case, special case needed for node counter instruction
            if tgt < 0 and index + tgt <=pos:
                newTgt = tgt -1
                # update curr conditional instruction's target
                stmtList[index] = (stmt, newTgt)


    def addInstruction(self, stmtList, inst, pos, add_node_cnt=0, offset=1):
        """[summary]

        Args:
            stmtList ([List]): List of IR Statments
            inst ([ChironAST.Instruction type]): Instruction to be added. Should be of type Instruction(AST).
            pos ([int]): Position in IR List to add the instruction.
        """
        if pos >= len(stmtList):
            print("[error] POSITION given is past the instruction list.")
            return
        
        index = 0

        # We must consider the conditional jumps and targets of
        # instructions that appear before the position where the
        # instruction must be added. Other conditional statements
        # will just shift without change of labels since
        # all the jump target numbers are relative.

        # here offset is the target offset the instruction , 1 for non-conditonals
        # add_node_cnt is a flag to indicate if the instruction being added is a node counter instruction
        while index<pos:
            if stmtList[index][1]!=1:
                # Update the target of this conditional statement and the
                # target statment's target number accordingly.
                self.updateJumpUpperCond(stmtList, index, pos, add_node_cnt)
            index += 1
        while index<len(stmtList):
            if stmtList[index][1]!=1:
                # Update the target of this conditional statement and the
                # target statment's target number accordingly.
                    self.updateJumpLowerCond(stmtList, index, pos,add_node_cnt)
            index += 1
        stmtList.insert(pos, (inst, offset))

    def removeInstruction(self, stmtList, pos):
        """[summary]

        Replace by a no-op as of now. (Sumit: Kinda works)

        Args:
            stmtList ([List]): List of IR Statments
            pos ([int]): Position in IR List to remove the instruction.
        """
        if pos >= len(stmtList):
            print("[error] POSITION given is past the instruction list.")
            return

        inst = stmtList[pos][0]
        if isinstance(inst, ChironAST.ConditionCommand):
            print("[Skip] Instruction Type not supported for removal. \n")
            return

        if "__rep_counter_" in str(stmtList[pos][0]):
            print("[Skip] Instruction affecting loop counter. \n")
            return

        # We only allow non-jump/non-conditional statement removal as of now.
        stmtList[pos] = (ChironAST.NoOpCommand(), 1)

    def update_target(self,stmtlist,pos,new_target):
        stmtlist[pos]=(stmtlist[pos][0],new_target)

    def pretty_print(self, irList):
        """
            We pass a IR list and print it here.
        """
        print("\n========== Chiron IR ==========\n")
        print("The first label before the opcode name represents the IR index or label \non the control flow graph for that node.\n")
        print("The number after the opcode name represents the jump offset \nrelative to that statement.\n")
        for idx, item in enumerate(irList):
            print(f"[L{idx}]".rjust(5), item[0], f"[{item[1]}]")

    def pretty_print_profile_data(self, irList,edge_source,edge_target,edge_count,node_indices,node_counts):
        # Function to print the profiling data annotated to the IR
        node_data={}
        edge_data={}
        src_tgt={}
        node_li=[]
        for i,node_idx in enumerate(node_indices):
            node_data[node_idx]=node_counts[i]
            if node_idx!="END":
                node_li.append(int(node_idx))
        node_li.sort()
        for i,edge_src in enumerate(edge_source):
            edge_data[(edge_src,edge_target[i])]=edge_count[i]
            src_tgt[edge_src]=edge_target[i]
        for idx, item in enumerate(irList):
            if(node_data.get(str(idx)) is not None):
                pos=node_li.index(idx)
                if pos+1<len(node_li):
                    fall_through=node_li[pos+1]
                else:
                    fall_through=node_li[pos]+1
                jump=fall_through-1+irList[fall_through-1][1]
                if jump!=fall_through:
                    # For the case when there is jump and fall through (if-else)
                    print(f"{node_data.get(str(idx),0)},{edge_data.get((str(idx),str(jump)),0)},{edge_data.get((str(idx),str(fall_through)),0)}->[L{idx}]".rjust(5), item[0], f"[{item[1]}]")
                else:
                    # For the case when the edge if always taken (control flow edge)
                    print(f"{node_data.get(str(idx),0)},{edge_data.get((str(idx),str(jump)),0)}->[L{idx}]".rjust(5), item[0], f"[{item[1]}]")
            else:
                    # For the instructions within a basic block
                 print(f"       [L{idx}]".rjust(5), item[0], f"[{item[1]}]")
    
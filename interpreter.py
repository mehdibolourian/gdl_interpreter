#!/usr/bin/env python
# coding: utf-8

# ## 1- Required Libraries
import re
import os
import math
import networkx          as     nx
import matplotlib.pyplot as     plt
from   graphviz          import Digraph
from   IPython.display   import Image, display

class InterpreterError(Exception):
    pass

# ## 1) Block 1: Lexer
class Lexer:
    def __init__(self, program):
        self.tokens = re.findall(r"node|edge|target|\w+|<\[|\]>|,|\(|\)", program)   # List of expected tokens
        self.current = 0                                                             # Position of the token being processed

    def peek(self): # Used by the parser to 
        return self.tokens[self.current] if self.current < len(self.tokens) else None

    def advance(self):
        token = self.peek()
        self.current += 1
        return token

    def expect(self, expected):
        token = self.advance()
        if token != expected:
            raise InterpreterError(f"Expected '{expected}' but got '{token}'.") 


# ## 2) Block 2: Parser
class Parser:
    def __init__(self, lexer):
        self.lexer = lexer        # An object of the Lexer class
        self.ast_id_counter = 0   # AST node IDs

    def parse(self):
        ast = {"type": "GDL Program", "body": []}
        target_found = False  # Flag to track if the target has been encountered
        
        try:
            while self.lexer.peek():
                token = self.lexer.peek()
                
                if token == "node":
                    # If a target has been found, we cannot parse any more nodes or edges
                    if target_found:
                        raise InterpreterError("Nodes and edges cannot appear after the target node.")
                    ast["body"].append(self.parse_node())
                
                elif token == "edge":
                    # If a target has been found, we cannot parse any more edges
                    if target_found:
                        raise InterpreterError("Edges cannot appear after the target node.")
                    ast["body"].append(self.parse_edge())
                
                elif token == "target":
                    # If a target is found, no more nodes or edges can appear after it
                    if target_found:
                        raise InterpreterError("Only one target node is allowed, and it must appear last.")
                    ast["body"].append(self.parse_target())
                    target_found = True  # Mark that we've encountered the target
                
                else:
                    raise InterpreterError(f"Unexpected token: {self.lexer.peek()}")
        
        except InterpreterError as e:
            print(f"Parser Error: {e}")
            raise
        
        return ast

    def parse_node(self):
        self.lexer.expect("node")
        node_id = self.lexer.advance()
        
        lower = -math.inf
        upper = math.inf
    
        # Check if the next token is the start of a range
        if self.lexer.peek() == "<[":
            self.lexer.advance()  # Consume '<['
            
            # Parse lower bound (handle omitted lower bound)
            lower_token = self.lexer.peek()
            if lower_token == ",":
                self.lexer.advance()  # Skip the ',' indicating omitted lower bound
            elif lower_token not in {",", "]>"}:
                try:
                    lower = int(self.lexer.advance())
                except ValueError:
                    raise InterpreterError(f"Invalid lower bound in node definition: {lower_token}")
            else:
                raise InterpreterError("Malformed range: Missing ',' after lower bound.")
                
            
            # Parse upper bound (handle omitted upper bound)
            if self.lexer.peek() == "," or lower == -math.inf:
                self.lexer.advance()  # Consume ','
                upper_token = self.lexer.peek()
                if upper_token != "]>":  # Upper bound provided
                    try:
                        upper = int(self.lexer.advance())
                    except ValueError:
                        raise InterpreterError(f"Invalid upper bound in node definition: {upper_token}")
                else:  # Upper bound omitted, allow +inf
                    upper = math.inf
            else:
                raise InterpreterError("Malformed range: Missing ',' between bounds.")
            
            # Ensure range is closed properly
            if self.lexer.peek() != "]>":
                raise InterpreterError("Malformed range: Missing closing ']>' in node definition.")
            self.lexer.expect("]>")
        
        return {
            "type": "Node",
            "id": node_id,
            "label": (lower, upper)
        }



    def parse_edge(self):
        self.lexer.expect("edge")
        self.lexer.expect("(")
        source = self.lexer.advance()
        self.lexer.expect(",")
        target = self.lexer.advance()
        self.lexer.expect(")")
        
        lower = -math.inf
        upper = math.inf
    
        if self.lexer.peek() == "<[":
            self.lexer.advance()  # Consume '<['
            
            # Parse lower bound (handle omitted lower bound)
            lower_token = self.lexer.peek()
            if lower_token == ",":
                self.lexer.advance()  # Skip the ',' indicating omitted lower bound
            elif lower_token not in {",", "]>"}:
                try:
                    lower = int(self.lexer.advance())
                except ValueError:
                    raise InterpreterError(f"Invalid lower bound in edge definition: {lower_token}")
            else:
                raise InterpreterError("Malformed range: Missing ',' after lower bound.")
            
            # Parse upper bound (handle omitted upper bound)
            if self.lexer.peek() == "," or lower == -math.inf:
                self.lexer.advance()  # Consume ','
                upper_token = self.lexer.peek()
                if upper_token != "]>":  # Upper bound provided
                    try:
                        upper = int(self.lexer.advance())
                    except ValueError:
                        raise InterpreterError(f"Invalid upper bound in edge definition: {upper_token}")
                else:  # Upper bound omitted, allow +inf
                    upper = math.inf
            else:
                raise InterpreterError("Malformed range: Missing ',' between bounds.")
            
            # Ensure range is closed properly
            if self.lexer.peek() != "]>":
                raise InterpreterError("Malformed range: Missing closing ']>' in edge definition.")
            self.lexer.expect("]>")
        
        return {
            "type": "Edge",
            "source": source,
            "target": target,
            "weight": (lower, upper)
        }


    def parse_target(self):
        self.lexer.expect("target")
        if self.lexer.peek() == "graph":
            self.lexer.advance()
            return {"type": "Target", "id": "graph"}
        elif self.lexer.peek() == "node":
            self.lexer.advance()
            target_id = self.lexer.advance()
            return {"type": "Target", "id": target_id}
        elif self.lexer.peek() == "edge":
            self.lexer.advance()
            self.lexer.expect("(")
            source = self.lexer.advance()
            self.lexer.expect(",")
            target = self.lexer.advance()
            self.lexer.expect(")")
            return {"type": "Target", "id": f"{source}->{target}"}
        else:
            raise InterpreterError("Invalid target specification.")


# ## 3) Block 3: Semantic Analyzer
class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast = ast

    def analyze(self):
        try:
            nodes = {item["id"] for item in self.ast["body"] if item["type"] == "Node"}
            edges = [
                (item["source"], item["target"]) for item in self.ast["body"] if item["type"] == "Edge"
            ]
            targets = [item for item in self.ast["body"] if item["type"] == "Target"]

            # Ensure at least one node is defined
            if not nodes:
                raise InterpreterError("The graph must contain at least one node.")

            # Ensure edges connect only defined nodes
            for item in self.ast["body"]:
                if item["type"] == "Edge":
                    if item["source"] not in nodes:
                        raise InterpreterError(f"Edge source '{item['source']}' is not defined.")
                    if item["target"] not in nodes:
                        raise InterpreterError(f"Edge target '{item['target']}' is not defined.")

            # Ensure nodes and edges are defined in the correct order
            node_seen = False
            for item in self.ast["body"]:
                if item["type"] == "Node":
                    node_seen = True
                elif item["type"] == "Edge" and not node_seen:
                    raise InterpreterError("Edges must be defined after all nodes.")

            # Ensure a target is defined
            if not targets:
                raise InterpreterError("A target must be defined (node, edge, or graph).")

            # Validate targets
            for target in targets:
                target_id = target["id"]
                if target_id == "graph":
                    # Valid target: entire graph
                    continue
                elif target_id in nodes:
                    # Valid target: specific node
                    continue
                elif any(target_id == f"{src}->{dst}" for src, dst in edges):
                    # Valid target: specific edge
                    continue
                else:
                    raise InterpreterError(f"Target '{target_id}' is not defined as a node, edge, or graph.")
        except InterpreterError as e:
            print(f"Semantic Analysis Error: {e}")
            raise


# ## 4) AST and Output Graph Plot
class GraphGenerator:
    def __init__(self, ast):
        self.ast = ast

    def generate(self):
        G = nx.DiGraph()

        # Add nodes with labels
        for item in self.ast["body"]:
            if item["type"] == "Node":
                G.add_node(item["id"], label=item["label"])

        # Add edges with weights
        for item in self.ast["body"]:
            if item["type"] == "Edge":
                G.add_edge(item["source"], item["target"], label=item["weight"])

        return G

    def plot(self, G):
        pos = nx.spring_layout(G)
        
        # Draw the graph with empty labels to prevent duplication
        nx.draw(G, pos, with_labels=False, node_color='lightblue', node_size=2000, font_size=10)
    
        # Draw custom node labels
        node_labels = {node: f"{node}\n{data['label']}" for node, data in G.nodes(data=True)}
        nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8)
    
        # Draw edge labels
        edge_labels = {(u, v): f"{d['label']}" for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

        print("Interpreted Graph from the GDL Program:")
        
        plt.show()

class ASTVisualizer:
    def __init__(self, ast):
        self.ast = ast
        self.dot = Digraph(format='png')
        self.node_counter = 0

    def add_node(self, label):
        node_id = f"node{self.node_counter}"
        self.dot.node(node_id, label)
        self.node_counter += 1
        return node_id

    def add_edge(self, parent_id, child_id):
        self.dot.edge(parent_id, child_id)

    def traverse(self, node, parent_id=None):
        label = node["type"]
        node_id = self.add_node(label)

        if parent_id:
            self.add_edge(parent_id, node_id)

        for key, value in node.items():
            if key == "type":
                continue
            if isinstance(value, dict):
                self.traverse(value, node_id)
            elif isinstance(value, list):
                for child in value:
                    self.traverse(child, node_id)
            else:
                leaf_id = self.add_node(f"{key}: {value}")
                self.add_edge(node_id, leaf_id)

    def visualize(self, output_file='ast'):
        self.traverse(self.ast)

        print("Abstract Syntax Tree:")
        
        # Render the graph to a file
        file_path = self.dot.render(output_file)
        
        # Display the image inline
        display(Image(filename=f"{output_file}.png"))

        print(f"Saved to {file_path}\n")
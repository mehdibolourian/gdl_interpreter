#!/usr/bin/env python
# coding: utf-8

# ## 1- Required Libraries
import random


# ## 2- GDLProgram Class
class GDLProgram:
    """
    Represents a GDL program with text and a score.
    """
    def __init__(self, text, score):
        self.text = text
        self.score = score

    @staticmethod
    def generate_program(node_list):
        """
        Generate a random GDL program with nodes, edges, a target node,
        and randomly added ranges.
        
        Args:
            node_list (list): List of nodes in the graph.
        
        Returns:
            GDLProgram: A randomly generated GDL program with ranges.
        """
        num_nodes = random.randint(3, len(node_list))  # Select a random subset of nodes (at least 3)
        selected_nodes = random.sample(node_list, num_nodes)

        # Generate nodes with optional ranges
        nodes = [
            f"node {node} <[{GDLProgram._generate_range()}]>" if random.choice([True, False]) 
            else f"node {node}" 
            for node in selected_nodes
        ]

        # Generate edges with optional ranges
        edges = [
            f"edge ({random.choice(selected_nodes)},{random.choice(selected_nodes)}) <[{GDLProgram._generate_range()}]>" 
            if random.choice([True, False]) 
            else f"edge ({random.choice(selected_nodes)},{random.choice(selected_nodes)})"
            for _ in range(random.randint(2, 5))
        ]

        # Select a random target node
        target_node = random.choice(selected_nodes)
        text = (
            "\n".join(nodes) + "\n" +
            "\n".join(edges) + "\n" +
            f"target node {target_node}"
        )
        score = random.uniform(0, 1)  # Assign a random score between 0 and 1
        return GDLProgram(text=text, score=score)

    @staticmethod
    def _generate_range():
        """
        Generate a random complete or incomplete range.
        
        Returns:
            str: A range in the form 'low,high' or 'low,' or ',high'.
        """
        range_type = random.choice(["complete", "low_only", "high_only"])
        if range_type == "complete":
            low = random.randint(1, 10)
            high = random.randint(low, low + 10)
            return f"{low},{high}"
        elif range_type == "low_only":
            low = random.randint(1, 10)
            return f"{low},"
        else:  # high_only
            high = random.randint(1, 10)
            return f",{high}"

    @classmethod
    def generate_library(cls, size, node_list):
        """
        Generate a library of GDL programs ensuring each node is targeted at least once,
        with ranges included.
        
        Args:
            size (int): Total number of GDL programs to generate.
            node_list (list): List of nodes in the graph.
        
        Returns:
            list: List of GDLProgram instances.
        """
        if size < len(node_list):
            raise ValueError("The library size must be at least equal to the number of nodes to ensure coverage.")

        library = []

        # Ensure each node is targeted at least once
        for target_node in node_list:
            program = cls.generate_program(node_list)
            while f"target node {target_node}" not in program.text:
                program = cls.generate_program(node_list)
            library.append(program)

        # Generate the remaining programs
        remaining_size = size - len(node_list)
        for _ in range(remaining_size):
            library.append(cls.generate_program(node_list))

        return library

# ## 3- GDLModel Class
class GDLModel:
    """
    Represents a GDL-based model using a library of GDL programs.
    """
    def __init__(self):
        self.library = []  # The GDL library serving as the model

    def initialize(self, library_size, node_list):
        """
        Initialize the model with a library of GDL programs.
        
        Args:
            library_size (int): Total number of GDL programs to generate.
            node_list (list): List of nodes in the graph.
        
        Returns:
            None
        """
        self.library = GDLProgram.generate_library(
            size=library_size, node_list=node_list
        )

    def filter_by_target(self, target_node):
        """
        Filter programs from the library based on the target node.
        
        Args:
            target_node (str): The target node to filter by.
        
        Returns:
            list: Filtered GDL programs containing the target node.
        """
        filtered_programs = [program for program in self.library if f"target {target_node}" in program.text]

        return max(filtered_programs, key=lambda program: program.score)
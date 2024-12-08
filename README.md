# Description

This code implements the CS 842 project titled "Implementing an Interpreter for Graph Description Language." In this project, the goal is first to implement a graph description language (GDL)-based node/graph classifier that generates a GDL model (i.e., a set of pre-trained GDL programs) and a target component as inputs and outputs the GDL program with the highest score. In addition, a GDL interpreter is implemented where the resulting GDL program is interpreted to a graphical representation, which can also act as an independent block.

## Requirement

* python >= 3.8.8

## Required Packages
* re
* os
* math
* time
* random
* networkx
* matplotlib.pyplot
* graphviz
* IPython.display

## How to use

You need to simply run the Jupyter Notebook ``main.ipynb`` which includes both individual test cases for the interpreter (in ``interpreter.py``) and an integration test with the GDL model generator (in ``classifier.py``).

#!/usr/bin/env python
import re
import models
from copy import copy, deepcopy
import lispy

class StageReader:
  def __init__(self, file):
    self.graph = self.stages(models.Graph(), file) #initialize empty graph.
    self.graph.m = self.createAdjMatrix() #create the adjacency matrix.
    self.graph.mPrime = self.createPrimeMatrix() #create transitive closure matrix.
    #self.report();

  def stages(self, graph, file):
    name = ""
    nameCheck = False
    p = re.compile('#.*'); #compile a patttern to look for comments.
    for line in open(file, 'r'):
      line = p.sub('', line.strip())
      nodeName = re.match(r"(?P<name>(!)?\w+(.)?$)", line)
      outLine = re.match(r"^> (?P<next>(\()?\w+(\))?) (?P<description>.*)", line)
      addItems = re.match(r"^:add (?P<items>.*)", line)
      deleteItems = re.match(r"^:delete (?P<items>.*)", line)
      onEntry = re.match(r"^:OnEntry (?P<action>.*)", line)
      onExit = re.match(r"^:OnExit (?P<action>.*)", line)
      if line == "":
        continue
      if nodeName:
        if not nameCheck:
            name = nodeName.group("name")
            nameCheck = True
            graph.node(name) #create new node.
        else:
            graph.node(name).title = line
      elif addItems:
        graph.node(name).add.append(addItems.group("items"))
      elif deleteItems:
        graph.node(name).delete.append(deleteItems.group("items"))
      elif onEntry:
        graph.node(name).entry.append(onEntry.group("action"))
      elif onExit:
        graph.node(name).exit.append(onExit.group("action"))
      elif outLine:
        models.Edge(graph.node(name),graph.node(outLine.group("next")), outLine.group("description"))
        nameCheck = False
      else:
        graph.node(name).also(line) #add node description.
    return graph

  def createAdjMatrix(self):
    ln = len(self.graph.nodes)
    matrix = [[0 for col in range(ln)] for row in range(ln)] #create blank matrix
    for node in self.graph.nodes: #for each node in the graph
      for out in node.out: #for each way out in the node
        matrix[node.id][out.there.id] += 1
    return matrix

  def createPrimeMatrix(self):
    ln = len(self.graph.nodes)
    matrix = deepcopy(self.graph.m)
    for path in range(0,ln):
      for row in range(0,ln):
        for col in range(0,ln):
          matrix[row][col] = matrix[row][col] or (matrix[row][path] and matrix[path][col])
    return matrix

  def printMatrix(self, matrix):
    symbols=list("0123456789abcdefghojklmnopqrstuvwzyz=?+*-@$:;ABCDEFGHIJKLMNOPQRSTUVWYZ")
    ln = len(self.graph.nodes)
    for r in range(ln):
      print symbols[r+1],
    print "\n"
    for row in range(0,ln):
      for col in range(0,ln):
        print matrix[row][col],
      print "", symbols[row+1], self.graph.nodes[row].name,"\n"

  def report(self):
    ln = len(self.graph.nodes)
    startNodes, endNodes = [], []
    for node in self.graph.nodes:
      if re.match(r"^!\w+", node.name):
        startNodes.append(node)
      elif re.match(r"\w+(\.)$", node.name):
        endNodes.append(node)
    if len(startNodes) > 1:
      print "More than one start node!"
    if len(endNodes) > 1:
      print "More than one end node!"
    for end in endNodes:
      if end.out:
        print "End node can't have outgoing edges!"
    for row in range(0,ln):
      for col in range(0,ln):
        if self.graph.mPrime[row][col] != 0 and col == 0:
          print "Start node can't have incoming edges!"
        if self.graph.mPrime[row][col] == 0 and col > 0 and row == 0:
          print "Start node can't reach node", self.graph.nodes[col].name

def match(string, edges):
  words = [edge.there.name for edge in edges if(re.match("^"+string, edge.there.name))]
  return words, len(words)

stageFile = raw_input("Enter the stage text filename: ").strip()
reader = StageReader(stageFile)
reader.printMatrix(reader.graph.m)
#reader.printMatrix(reader.graph.mPrime)

current = reader.graph.nodes[0]
while True:
  outer = re.compile("\((.+)\)")
  conv = outer.search(current.description)
  if conv:
    for string in conv.groups():
        for part in lispy.sexp("("+string+")"):
            eval(lispy.parse(part))
  print "\n"+ current.description
  if len(current.out) > 0:
    for edge in current.out:
      print "(",edge.there.name,")", edge.description
    next = raw_input("\nWhat would you like to do next? > ").strip()
    matched, length = match(next, current.out)
    if length > 1 or length < 1:
      current = current
      print "\nThe name you entered matched", "none" if length < 1 else "more than one", "!"
    else:
      current = reader.graph.node(matched[0])
  else:
    print "Congratulations, you have finished the game!"
    break

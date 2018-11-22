from math import *

class PolyGraph:
    def __init__(self):
        self.nodes = []

    def addNode(self, node):
        self.nodes.append(node)

    def getNodes():
        return self.nodes

class PolyNode:
    prev = None
    next = None
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def setPrev(node):
        self.prev = node

    def __repr__(self):
        return repr((self.x, self.y))

class PolyEdge:
    def __init__(self, u, v):
        self.u = u;
        self.v = v;

    def __repr__(self):
        return repr((self.u, self.v))

'''
Takes an array of OpenCV contours and produces
a list of edges and a list of nodes.
Note: This works given that nodes in the contour are in sequence.
'''
def getEdgesFromContour(contours, gridSizeX = 1, gridSizeY = 1, minLen = -1):
    start = None
    prev = None
    curr = None
    edges = []
    nodes = []
    for index, cnt in enumerate(contours):
        #print cnt
        x = (cnt[0][0] / gridSizeX) * gridSizeX
        y = (cnt[0][1] / gridSizeY) * gridSizeY
        if index == 0:
            start = PolyNode(x, y)
            nodes.append(start)
            prev = start
            continue

        curr = PolyNode(x,y)
        nodes.append(curr)

        edge = PolyEdge(prev, curr)
        #print 'Length: '+ str(getEdgeLength(edge))
        #print 'Angle: ' + str(angleOfEdge(edge))

        length = getEdgeLength(edge)
        # Skip edges too short to be important.
        if length >= minLen:
            curr.prev = prev
            prev.next = curr
            edges.append(edge)
        prev = curr

    # Close the shape
    edge = PolyEdge(curr, start)
    length = getEdgeLength(edge)
    if length >= minLen:
        curr.next = start
        start.prev = curr
        edges.append(edge)

    return edges, nodes

'''
Takes an array of OpenCV contours and produces
a list of Nodes.
'''
def getNodesFromContour(contours):
    start = None
    prev = None
    curr = None
    nodes = []
    for index, cnt in enumerate(contours):
        #print cnt
        x = cnt[0][0]
        y = cnt[0][1]
        curr = PolyNode(x,y)

        nodes.append(curr)
    return nodes

'''
Returns a list of list of nodes where
each sublist contains all the nodes of
a single disconnected subgraph.
'''
def findDisconnectedSubgraphs(nodeList):
    graphs = []

    # Find the start of every disconnected graph
    # A node is considered a start if it nodes not have a prev reference
    starts = []
    for node in nodeList:
        if node.prev is None:
            starts.append(node)

    for node in starts:
        graph = PolyGraph()
        curr = node
        top =-1
        left =-1
        bottom = 0
        right = 0

        while curr:
            graph.addNode(curr)

            # Tack the boundries to get the bounding box
            if top == -1:
                top = curr.y
            elif curr.y < top:
                top = curr.y

            if left == -1:
                left = curr.x
            elif curr.x < left:
                left = curr.x

            if curr.x > right:
                right = curr.x

            if curr.y > bottom:
                bottom = curr.y


            curr = curr.next

        box = (left, top, right - left, bottom - top)
        graphs.append((graph,box))

    #print graphs
    return graphs

'''
Given an edge this function returns the angle
it makes with relation to the X axis
'''
def angleOfEdge(edge):
    u = edge.u
    v = edge.v
    angle = atan2(u.y - v.y, v.x - u.x) * 180 / pi
    return angle

def angleBetweenEdges(e1, e2):
    pass

def getEdgeLength(edge):
    return sqrt(pow(edge.u.x-edge.v.x, 2) + pow(edge.u.y - edge.v.y, 2))

def replaceInclinedEdges():
    pass

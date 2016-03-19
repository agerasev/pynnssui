#!/usr/bin/python3

from random import random
from math import sqrt
from copy import copy

class Graph:
	class Node:
		def __init__(self, name, pos):
			self.name = name
			if name == 'MatrixProduct':
				self.name = 'Matrix'
			self.rad = 30
			self.pos = pos
			
	class Path:
		def __init__(self, src, dst):
			self.src = src
			self.dst = dst
			
	def __init__(self, net):
		self.nodes = {}
		rf = 100*len(net.nodes)
		for key in net.nodes:
			self.nodes[key] = self.Node(type(net.nodes[key]).__name__, [rf*random(), rf*random()])
			
		self.inputs = {}
		self.outputs = {}
		self.paths = []
		for i in range(len(net.paths)):
			src = net.paths[i].src[0]
			dst = net.paths[i].dst[0]
			self.paths.append(self.Path(src, dst))
			if src < 0:
				self.inputs[dst] = self.nodes[dst]
			if dst < 0:
				self.outputs[src] = self.nodes[src]
			
		self.width = 0
		self.height = 0
		
		for i in range(100*len(self.nodes)):
			self.step(1e-1)

		self.truncate()
			
	def truncate(self):
		# determine bounds for scene
		bounds = [[None,None],[None,None]]
		border = 15
		for key, node in self.nodes.items():
			value = node.pos[0] - node.rad - border
			if bounds[0][0] is None or bounds[0][0] > value:
				bounds[0][0] = value
				
			value = node.pos[1] - node.rad - border
			if bounds[0][1] is None or bounds[0][1] > value:
				bounds[0][1] = value
				
			value = node.pos[0] + node.rad + border
			if bounds[1][0] is None or bounds[1][0] < value:
				bounds[1][0] = value
				
			value = node.pos[1] + node.rad + border
			if bounds[1][1] is None or bounds[1][1] < value:
				bounds[1][1] = value
		
		# move nodes to (0,0)
		for key, node in self.nodes.items():
			node.pos[0] -= bounds[0][0]
			node.pos[1] -= bounds[0][1]
		
		# set image size
		self.width = bounds[1][0] - bounds[0][0]
		self.height = bounds[1][1] - bounds[0][1]
		
	def step(self, rate):
		force = {}
		for key in self.nodes:
			force[key] = [0, 0]
		
		# iterate each pair of nodes
		fdist = 1.4
		for src, sn in self.nodes.items():
			for dst, dn in self.nodes.items():
				if src <= dst:
					continue
				
				# check nodes connected
				conn = False
				for i in range(len(self.paths)):
					path = self.paths[i]
					if (path.src == src and path.dst == dst) or (path.src == dst and path.dst == src):
						conn = True
						break

				# compute force
				d = [dn.pos[0] - sn.pos[0], dn.pos[1] - sn.pos[1]]
				l = sqrt(d[0]**2 + d[1]**2)
				d[0] /= l
				d[1] /= l
				m = l - fdist*(sn.rad + dn.rad)
				if not conn:
					m = min(m, 0)
				f = [d[0]*m, d[1]*m]
				force[src][0] += f[0]
				force[src][1] += f[1]
				force[dst][0] -= f[0]
				force[dst][1] -= f[1]
		
		# drag inputs and outputs
		drag = 20
		for key in self.inputs:
			force[key][0] -= drag
		for key in self.outputs:
			force[key][0] += drag

		# apply forces
		for key, node in self.nodes.items():
			node.pos[0] += force[key][0]*rate
			node.pos[1] += force[key][1]*rate
		

	def svg(self):
		s = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="%d" height="%d">' % (self.width, self.height)
		s += '''
		<marker id="Arrow" markerWidth="6" markerHeight="6" viewBox="-3 -3 6 6" refX="2" refY="0" markerUnits="strokeWidth" orient="auto">
		<polygon points="-1,0 -3,3 3,0 -3,-3" fill="gray"/>
		</marker>
		'''

		# draw nodes
		for key, node in self.nodes.items():
			s += '<circle cx="%f" cy="%f" r="%f" fill="orange"/>' % (node.pos[0], node.pos[1], node.rad)
			size = min(3.2*node.rad/len(node.name), 0.5*node.rad)
			s += '<text fill="white" font-size="%f" text-anchor="middle" font-family="Verdana" x="%f" y="%f">%s</text>' % (size, node.pos[0], node.pos[1] + 0.3*size, node.name)
		
		# draw paths
		fline = 1.1
		for i in range(len(self.paths)):
			path = self.paths[i]
			if path.src < 0 or path.dst < 0:
				continue
			src = self.nodes[path.src]
			dst = self.nodes[path.dst]
			sp = copy(src.pos)
			dp = copy(dst.pos)
			sr = src.rad
			dr = dst.rad
			d = [dp[0] - sp[0], dp[1] - sp[1]]
			l = sqrt(d[0]**2 + d[1]**2)
			d[0] /= l
			d[1] /= l
			sp[0] += d[0]*sr*fline
			sp[1] += d[1]*sr*fline
			dp[0] -= d[0]*dr*fline
			dp[1] -= d[1]*dr*fline
			s += '<line x1="%f" y1="%f" x2="%f" y2="%f" stroke="gray" stroke-width="2" marker-end="url(#Arrow)"/>' % (sp[0], sp[1], dp[0], dp[1])
		
		# draw inputs and outputs
		lioline = 10
		for key, node in self.inputs.items():
			s += '<line x1="%f" y1="%f" x2="%f" y2="%f" stroke="gray" stroke-width="2" marker-end="url(#Arrow)"/>' % (node.pos[0] - node.rad - lioline, node.pos[1], node.pos[0] - node.rad*fline, node.pos[1])
		for key, node in self.outputs.items():
			s += '<line x1="%f" y1="%f" x2="%f" y2="%f" stroke="gray" stroke-width="2" marker-end="url(#Arrow)"/>' % (node.pos[0] + node.rad*fline, node.pos[1], node.pos[0] + node.rad + lioline, node.pos[1])

		s += '</svg>'
		return s
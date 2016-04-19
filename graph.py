#!/usr/bin/python3

import numpy as np
from math import sqrt
from copy import copy
from pynn import Network, Loss


class Graph:
	class Node:
		def __init__(self, name, color, pos):
			self.name = name
			self.color = color
			self.rad = 30
			self.pos = pos

	class Path:
		def __init__(self, src, dst):
			self.src = src
			self.dst = dst

	def __init__(self, net):
		self.nodes = {}
		rf = 100*len(net.nodes)
		for key, node in enumerate(net.nodes):
			name = type(node).__name__
			color = 'orange'
			if isinstance(node, Network):
				color = 'blue'
			elif isinstance(node, Loss):
				name = node.nodetype().__name__
				color = 'red'
			self.nodes[key] = self.Node(
				name, color,
				rf*np.random.rand(2)
			)

		self.inputs = {}
		self.outputs = {}
		self.paths = []
		for path in net.paths:
			src = path.src[0]
			dst = path.dst[0]
			self.paths.append(self.Path(src, dst))
		for ipath in net.ipaths:
			dst = ipath.dst[0]
			self.paths.append(self.Path(-1, dst))
			self.inputs[dst] = self.nodes[dst]
		for opath in net.opaths:
			src = opath.src[0]
			self.paths.append(self.Path(src, -1))
			self.outputs[src] = self.nodes[src]

		self.width = 0
		self.height = 0

		for i in range(100*len(self.nodes)):
			self.step(1e-1, drag=True)
		for i in range(100*len(self.nodes)):
			self.step(1e-1)

		self.truncate()

	def truncate(self):
		# determine bounds for scene
		bounds = [np.zeros(2), np.zeros(2)]
		border = 15
		first = True
		for key, node in self.nodes.items():
			value = node.pos[0] - node.rad - border
			if first or bounds[0][0] > value:
				bounds[0][0] = value

			value = node.pos[1] - node.rad - border
			if first or bounds[0][1] > value:
				bounds[0][1] = value

			value = node.pos[0] + node.rad + border
			if first or bounds[1][0] < value:
				bounds[1][0] = value

			value = node.pos[1] + node.rad + border
			if first or bounds[1][1] < value:
				bounds[1][1] = value

			first = False

		# move nodes to (0,0)
		for key, node in self.nodes.items():
			node.pos -= bounds[0]

		# set image size
		self.size = bounds[1] - bounds[0]

	def step(self, rate, drag=False):
		force = {}
		for key in self.nodes:
			force[key] = np.zeros(2)

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
					fconn = (path.src == src and path.dst == dst)
					bconn = (path.src == dst and path.dst == src)
					if fconn or bconn:
						conn = True
						break

				# compute force
				d = dn.pos - sn.pos
				l = sqrt(np.dot(d, d))
				d /= l
				m = l - fdist*(sn.rad + dn.rad)
				if not conn:
					m = min(m, 0)
				f = d*m
				force[src] += f
				force[dst] -= f

		if drag:
			# drag inputs and outputs
			drag = 100
			for key in self.inputs:
				force[key][0] -= drag
			for key in self.outputs:
				force[key][0] += drag

		# apply forces
		for key, node in self.nodes.items():
			node.pos += force[key]*rate

	def svg(self):
		s = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="%d" height="%d">' % (self.size[0], self.size[1])
		s += '''
		<marker id="Arrow" markerWidth="6" markerHeight="6" viewBox="-3 -3 6 6" refX="2" refY="0" markerUnits="strokeWidth" orient="auto">
		<polygon points="-1,0 -3,3 3,0 -3,-3" fill="gray"/>
		</marker>
		'''

		# draw nodes
		for key, node in self.nodes.items():
			s += '<circle cx="%f" cy="%f" r="%f" fill="%s"/>' % (node.pos[0], node.pos[1], node.rad, node.color)
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
			d = dp - sp
			l = sqrt(np.dot(d, d))
			d /= l
			sp += d*sr*fline
			dp -= d*dr*fline
			s += '<line x1="%f" y1="%f" x2="%f" y2="%f" stroke="gray" stroke-width="2" marker-end="url(#Arrow)"/>' % (sp[0], sp[1], dp[0], dp[1])

		# draw inputs and outputs
		lioline = 10
		for key, node in self.inputs.items():
			s += '<line x1="%f" y1="%f" x2="%f" y2="%f" stroke="gray" stroke-width="2" marker-end="url(#Arrow)"/>' % (node.pos[0] - node.rad - lioline, node.pos[1], node.pos[0] - node.rad*fline, node.pos[1])
		for key, node in self.outputs.items():
			s += '<line x1="%f" y1="%f" x2="%f" y2="%f" stroke="gray" stroke-width="2" marker-end="url(#Arrow)"/>' % (node.pos[0] + node.rad*fline, node.pos[1], node.pos[0] + node.rad + lioline, node.pos[1])

		s += '</svg>'
		return s

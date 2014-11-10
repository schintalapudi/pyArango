import requests
import json

from theExceptions import (CreationError, DeletionError, UpdateError)
import collection as COL

class Graph_metaclass(type) :
	"""Keeps track of all graph classes and does basic validations on fields"""
	graphClasses = {}
	
	def __new__(cls, name, bases, attrs) :
		clsObj = type.__new__(cls, name, bases, attrs)
		if name != 'Graph' :
			try :
				if len(attrs['_edgeDefinitions']) < 1 :
					raise CreationError("Graph class '%s' has no edge definition" % name)
			except KeyError :
				raise CreationError("Graph class '%s' has no field _edgeDefinition" % name)

		Graph_metaclass.graphClasses[name] = clsObj
		return clsObj

	@classmethod
	def getGraphClass(cls, name) :
		"""return a graph class by its name"""
		try :
			return cls.graphClasses[name]
		except KeyError :
			raise KeyError("There's no child of Graph by the name of: %s" % name)

	@classmethod
	def isGraph(cls, name) :
		"""returns true/false depending if there is a graph called name"""
		return name in cls.graphClasses

def getGraphClass(name) :
	"""alias for Graph_metaclass.getGraphClass()"""
	return Graph_metaclass.getGraphClass(name)

def isGraph(name) :
	"""alias for Graph_metaclass.isGraph()"""
	return Graph_metaclass.isGraph(name)

class EdgeDefinition(object) :
	"""An edge definition for a graph"""

	def __init__(self, edgesCollection, fromCollections, toCollections) :
		self.edgesCollection = self.name = edgesCollection
		self.fromCollections = fromCollections
		self.toCollections = toCollections

	def toJson(self) :
		return { 'collection' : self.edgesCollection, 'from' : self.fromCollections, 'to' : self.toCollections }

class Graph(object) :
	"""The superclass fro witch all your graph types must derive"""

	__metaclass__ = Graph_metaclass

	_edgeDefinitions = {}
	_orphanedCollections = []

	def __init__(self, database, jsonInit) :
		self.database = database
		try :
			self._key = jsonInit["_key"]
		except KeyError :
			self._key = jsonInit["name"]
		except KeyError :
			raise KeyError("'jsonInit' must have a field '_key' or a field 'name'")

		self._rev = jsonInit["_rev"]
		self._id = jsonInit["_id"]
	
		defs = []
		# for e in jsonInit["edgeDefinitions"] :
		# 	if e["collection"] not in self._edgeDefinitions :
		# 		raise CreationError("Collection '%s' is not mentioned in the definition of graph '%s'" % (e["collection"], self.__class__,__name__))
		# 	if e["from"] != self._edgeDefinitions[e["collection"]]["from"] :
		# 		vals = (e["collection"], self.__class__,__name__, self._edgeDefinitions[e["collection"]]["from"], e["from"])
		# 		raise CreationError("Edge definition '%s' of graph '%s' mismatch for 'from':\npython:%s\narangoDB:%s" % vals)
		# 	if e["to"] != self._edgeDefinitions[e["collection"]]["to"] :
		# 		vals = (e["collection"], self.__class__,__name__, self._edgeDefinitions[e["collection"]]["to"], e["to"])
		# 		raise CreationError("Edge definition '%s' of graph '%s' mismatch for 'to':\npython:%s\narangoDB:%s" % vals )
		# 	defs.append(e["collection"])

		# if jsonInit["orphanCollections"] != self._orphanCollections :
		# 	raise CreationError("Orphan collection '%s' of graph '%s' mismatch:\npython:%s\narangoDB:%s" (e["collection"], self.__class__,__name__, self._orphanCollections, jsonInit["orphanCollections"]))
			
		self.URL = "%s/%s" % (self.database.graphsURL, self._key)

	def createVertex(self, collectionName, docAttributes) : #, waitForSync = False) :
		"""adds a vertex to the graph and returns it"""
		url = "%s/vertex/%s" % (self.URL, collectionName)
		col = COL.getCollectionClass(collectionName)
		col.validateDct(docAttributes)

		r = requests.post(url, params = docAttributes)#, params = {'waitForSync' : waitForSync})
		data = r.json()
		if r.status_code == 201 or r.status_code == 202 :
			return self.database['collectionName']["_key"]
		
		raise CreationError("Unable to create vertice, %s" % data["errorMessage"], data)

	def deleteVertex(self, document, waitForSync = False) :
		"""deletes a vertex from the graph as well as al linked edges"""
		url = "%s/vertex/%s" % (self.URL, document._key)
		
		r = requests.delete(url, params = {'waitForSync' : waitForSync})
		data = r.json()
		if r.status_code == 200 or r.status_code == 202 :
			return True
		raise DeletionError("Unable to delete vertice, %s" % _key, data)

	def createEdge(self, collectionName, _fromId, _toId, edgeAttributes = {}) : #, waitForSync = False) :
		"""created an edge between to documents"""
		url = "%s/edge/%s" % (self.URL, collectionName)
		col = COL.getCollectionClass(collectionName)
		col.validateDct(edgeAttributes)
		payload = edgeAttributes
		payload.update({'_from' : _fromId, '_to' : _toId})

		r = requests.post(url, data = payload, params = {'waitForSync' : waitForSync})
		data = r.json()
		if r.status_code == 201 or r.status_code == 202 :
			return col[r.json()["_key"]]
		raise CreationError("Unable to create vertice, %s" % r.json()["errorMessage"], data)

	def link(self, definition, doc1, doc2, edgeAttributes = {}) : #, waitForSync = False) :
		"A shorthand for createEdge that takes two documents as input"
		self.createEdge(definition, doc1._id, doc2._id, edgeAttributes, waitForSync)

	def deleteEdge(self, _key, waitForSync = False) :
		"""removes an edge from the graph"""
		url = "%s/edge/%s" % (self.URL, key)
		
		r = requests.delete(url, params = {'waitForSync' : waitForSync})
		if r.status_code == 200 or r.status_code == 202 :
			return True
		raise DeletionError("Unable to delete edge, %s" % _key, data)

	def delete(self) :
		"""deletes the graph"""
		r = requests.delete(self.URL)
		data = r.json()
		if not r.status_code == 200 or data["error"] :
			raise DeletionError(data["errorMessage"], data)

	def __str__(self) :
		return "ArangoGraph; %s" % self._key
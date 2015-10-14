#!/usr/bin/env python

# This was created and released into the
# Public Domain by Chris Warburton
#
# Due to the strains this is capable of putting on the Last.fm
# and AudioScrobbler systems it is recommended for use purely as
# experimental software.
#
# Keep in mind that the Last.fm web services server will block
# an IP address which accesses it more than once per second,
# thus lowering/removing the delays in downloading related artist
# information is not encouraged.

import urllib2
import pygame
import os
import time
import sys
import threading
import random
import xml.dom.minidom

pygame.init()

suicide = 0
netError = 0

class Simulation(object):

	def __init__(self, givenName, totalArtists, linkDepth, imagesEnabled, webEnabled, genresEnabled, physicsMethod):
		self.givenName = givenName
		self.artists = {}
		self.connections = {}
		self.genres = {}

		self.totalArtists = totalArtists
		self.linkDepth = linkDepth
		self.imagesEnabled = imagesEnabled
		self.webEnabled = webEnabled
		self.genresEnabled = genresEnabled

		self.physicsMethod = physicsMethod
		self.maxAttempts = 1000

		self.font = pygame.font.Font(None, 16)
		self.genreFont = pygame.font.Font(None, 28)

	def addArtist(self, name):
		pass

class ArtistNode(object):

	def __init__(self, simulation, name, position, range):
		self.name = name
		self.connections = []		# Keeping a local list of connections makes checking later on easier
		self.related = []		# Ditto
		self.genres = []		# Same again

		# Set values for the physics simulation
		self.position = [position[0] + random.randint((-1 * range), range), position[1] + random.randint((-1 * range), range)]		# This makes a random position around a related artist
		self.oldPosition = self.position
		self.velocity = [0, 0]
		self.force = [0, 0]
		self.mass = 1.0
		self.charge = 1.0

		self.text = font.render(self.name, True, (255, 255, 255), (0, 0, 0))
		self.text.get_rect().centerx = self.position[0]
		self.text.get_rect().centery = self.position[1]

		# These are needed to let the display pan around
		self.xIncrease = self.text.get_rect().width / 2.0
		self.yIncrease = self.text.get_rect().height / 2.0

		# Check if there is already an associated image saved for this artist
		if self.name.replace(' ', '_').replace('&', '_').replace(';', '_') in os.listdir(os.getcwd() + '/temp/images'):
			try:
				self.image = pygame.image.load(os.getcwd() + '/temp/images/' + self.name.replace(' ', '_').replace('&', '_').replace(';', '_'))
				if imagesEnabled:
					self.xIncrease = self.image.get_rect().width / 2.0
					self.xIncrease = self.image.get_rect().height / 2.0
				imagedArtists.append(self.name)
			except:
				print 'Warning: Could not assign image for ' + self.name
				self.image = self.text

		# If not then just use the name instead
		else:
			self.image = self.text
			needImage = True

		# Check if there is already a list of related artists saved
		if self.name.replace(' ', '_').replace('&', '_').replace(';', '_') in os.listdir(os.getcwd() + '/temp/related'):
			try:
				related = open(os.getcwd() + '/temp/related/' + self.name.replace(' ', '_').replace('&', '_').replace(';', '_'), 'r')
				for line in related.readlines():
					triple = line.split(',')
					if len(triple) == 3:
						while triple[2].endswith('\n'):
							triple[2] = triple[2][:-1]
						self.related.append((triple[2], triple[0]))
				related.close()
				isPending = True
			except:
				print 'Warning: Could not assign relationships for ' + self.name

		# If not then remember that we need to get them
		else:
			needsRelation = True

		# Check if there is already a list of associated genres saved
		if self.name.replace(' ', '_').replace('&', '_').replace(';', '_') in os.listdir(os.getcwd() + '/temp/genres'):
			try:
				genresFile = open(os.getcwd() + '/temp/genres/' + self.name.replace(' ', '_').replace('&', '_').replace(';', '_'), 'r')
			except:
				print 'Warning: Could not assign genres for ' + self.name
			else:
				try:
					self.parseGenres(genresFile)
				except UnicodeDecodeError:
					print 'Warning: Could not assign genres for ' + self.name

		# If not then remember that we need to get them
		else:
			needsGenre = True

		# This artist is now suitable for the following catagories, so add it
		usableArtists.append(self.name)
		unfinishedArtists.append(self.name)
		if isPending:
			pendingArtists.append(self.name)
		if needImage:
			imagePendingArtists.append(self.name)
		if needsGenre:
			genreNeedingArtists.append(self.name)
		if needsRelation:
			relationPendingArtists.append(self.name)

	def parseGenres(self, genresFile):
		try:
			doc = xml.dom.minidom.parse(genresFile)
		except:
			print "Error: Couldn't parse genres for " + self.name
		else:
			for tag in doc.getElementsByTagName("tag"):
				subTags = tag.childNodes
				for subTag in subTags:
					if subTag.nodeType != xml.dom.minidom.Node.TEXT_NODE:
						if subTag.localName == 'name':
							name = subTag.childNodes[0].data
						elif subTag.localName == 'count':
							count = int(subTag.childNodes[0].data)
				self.addGenre(name, count)

	def addConnection(self, toConnect, strengthString):
		strength = float(strengthString)
		if self.name + '_' + toConnect.name in edges:
			connections[self.name + '_' + toConnect.name].average(strength)
		elif toConnect.name + '_' + self.name in edges:
			connections[toConnect.name + '_' + self.name].average(strength)
		else:
			connections[self.name + '_' + toConnect.name] = Edge(self, toConnect, strength)
			edges.append(self.name + '_' + toConnect.name)

	def addRepulsion(self, toRepel):
		if self.name + '_' + toRepel.name in repels:
			pass
		elif toRepel.name + '_' + self.name in repels:
			pass
		else:
			repulsions[self.name + '_' + toRepel.name] = Edge(self, toRepel, 100.0)
			repels.append(self.name + '_' + toRepel.name)

	def assignConnections(self):
		try:
			os.popen('cd "' + os.getcwd() + '/temp/related" && wget -c -O ' + self.name.replace(' ', '_').replace('&', '_').replace(';', '_') + ' http://ws.audioscrobbler.com/1.0/artist/' + self.name.replace(' ', '+') + '/similar.txt')
			related = open(os.getcwd() + '/temp/related/' + self.name.replace(' ', '_').replace('&', '_').replace(';', '_'), 'r')
			for line in related.readlines():
				triple = line.split(',')
				if len(triple) == 3:
					while triple[2].endswith('\n'):
						triple[2] = triple[2][:-1]
					self.related.append((triple[2], triple[0]))
			related.close()
			pendingArtists.append(self.name)
		except:
			print 'Warning: Could not retrieve relationships for ' + self.name

	def assignImage(self):
		failed = False
		imageLine = 'None'
		try:
			for line in urllib2.urlopen('http://www.last.fm/music/' + self.name.replace(' ', '+')):
				if '" alt="' + self.name in line:
					imageLine = line
		except HTTPError:
			print 'Warning: Could not retrieve image for ' + self.name
			netError += 1
		if imageLine is not 'None':
			imageLocation = imageLine[imageLine.find('<img src="'):imageLine.find('" alt="' + self.name)]
			imageLocation = imageLocation[10:]
			wget = os.popen('cd "' + os.getcwd() + '/temp/images" && wget -c -O ' + self.name.replace(' ', '_').replace('&', '_').replace(';', '_') + ' ' + imageLocation, 'r')
			try:
				os.wait()
			except:
				pass
			for line in wget:
				if 'ERROR' in line or 'failed' in line:
					print 'Error getting picture'
					failed = True
		else:
			print 'Could not find image for ' + self.name
			failed = True
		if not failed:
			self.image = pygame.image.load(os.getcwd() + '/temp/images/' + self.name.replace(' ', '_').replace('&', '_').replace(';', '_'))
			if imagesEnabled:
				self.xIncrease = self.image.get_rect().width / 2.0
				self.yIncrease = self.image.get_rect().height / 2.0
			imagedArtists.append(self.name)

	def assignGenres(self):
		try:
			os.popen('cd "' + os.getcwd() + '/temp/genres" && wget -c -O ' + self.name.replace(' ', '_').replace('&', '_').replace(';', '_') + ' http://ws.audioscrobbler.com/1.0/artist/' + self.name.replace(' ', '+') + '/toptags.xml')
			genresFile = open(os.getcwd() + '/temp/genres/' + self.name.replace(' ', '_').replace('&', '_').replace(';', '_'), 'r')
		except:
			print 'Warning: Could not retrieve genres for ' + self.name
			netError += 1
		else:
			self.parseGenres(genresFile)

	def addGenre(self, genre, strength):
		if strength >= 50:
			if genre in usableGenres:
				if self.name in genres[genre].artists:
					pass
				else:
					genres[genre].connections.append((self.name, strength + 1))
					genres[genre].artists.append(self.name)
			else:
				genres[genre] = GenreNode(genre, self.position)
				genres[genre].connections.append((self.name, strength + 1))
				genres[genre].artists.append(self.name)

	def drawImage(self, screen, additional):
		screen.blit(self.image, (self.position[0] - self.xIncrease + additional[0], self.position[1] - self.yIncrease + additional[1]))

	def drawText(self, screen, additional, imagesOn=False):
		if imagesOn:
			screen.blit(self.text, (self.position[0] + - self.xIncrease + additional[0], self.position[1] - self.yIncrease + additional[1]))
		else:
			screen.blit(self.text, (self.position[0] + additional[0], self.position[1] + additional[1]))

	def move(self, bias):
		counter = [0, 0]
		for attempt in range(0, maxAttempts):
			choice = [random.random(), random.random()]
			bias = (bias[0] / 2, bias[1] / 2)
			choice[0] += bias[0]
			choice[1] += bias[1]
			if choice[0] < 0.5:
				counter[0] -= moveMagnitude
			elif choice[0] > 0.5:
				counter[0] += moveMagnitude
			else:
				counter += moveMagnitude * ((random.randint(0, 1) * 2) - 1)
			if choice[1] < 0.5:
				counter[1] -= moveMagnitude
			elif choice[1] > 0.5:
				counter[1] += moveMagnitude
			else:
				counter[1] += moveMagnitude * ((random.randint(0, 1) * 2) - 1)
		self.oldPosition = self.position
		self.position = (self.position[0] + (counter[0] / maxAttempts), self.position[1] + (counter[1] / maxAttempts))

class GenreNode:

	def __init__(self, name, position):
		self.name = name
		self.connections = []
		self.artists = []
		self.position = (position[0], position[1])
		self.velocity = (0, 0)
		self.force = (0, 0)
		self.text = genreFont.render(self.name, True, (255, 255, 255), (0, 0, 0))
		self.text.get_rect().centerx = self.position[0]
		self.text.get_rect().centery = self.position[1]
		self.xIncrease = self.text.get_rect().width / 2.0
		self.yIncrease = self.text.get_rect().height / 2.0
		usableGenres.append(self.name)

	def draw(self, screen, additional):
		screen.blit(self.text, (self.position[0] - self.xIncrease + additional[0], self.position[1] - self.yIncrease + additional[1]))

class Edge:

	def __init__(self, node1, node2, strength):
		self.node1 = node1
		self.node2 = node2
		self.strength = strength / 100.0

	def average(self, strength):
		secondStrength = strength / 100.0
		self.strength = (self.strength + secondStrength) / 2.0

class Button:

	def __init__(self, text, position, (width, height), initialValue):
		self.text = font.render(text, True, (255, 255, 255))
		self.value = initialValue
		if self.value:
			self.colour = (64, 192, 64)
		else:
			self.colour = (64, 64, 64)
		self.width = width
		self.height = height
		self.x = 0
		self.y = 0
		self.left = position[0]
		self.top = position[1]
		self.right = position[0] + self.width
		self.bottom = position[1] + self.height
		self.vivible = True

	def toggleValue(self):
		if self.value:
			self.value = False
			self.colour = (64, 64, 64)
		else:
			self.value = True
			self.colour = (64, 192, 64)

	def setPosition(self, (x, y)):
		self.x = x
		self.y = y

	def draw(self, screen):
		if self.visible:
			pygame.draw.rect(screen, self.colour, (self.x, self.y, self.width, self.height))
			screen.blit(self.text, (self.x + 2, self.y + 2))

	def click(self, position):
		if self.visible and self.left[0] < position < self.right and \
			self.bottom < self.position < self.top:
			return True
		else:
			return False


class LastFMFetchingThread(threading.Thread):

	def run(self, simulation):
		while True:
			

class Display(pygame.Surface, threading.Thread):

	def __init__(self, size):
		super(Display, self).__init__(size)
		threading.Thread.__init__(self)
		self.additional = [0, 0]
		self.leftMouseHeld = False

	def setupButtons(self):
		horizontalPosition = 0
		verticalPosition = 585
		self.buttons = []
		controlsEnabled = True
		controlButton = Button('Control', (45, 15), controlsEnabled)
		controlButton.setPosition((horizontalPosition, verticalPosition))
		buttonList.append(controlButton)
		horizontalPosition += controlButton.width + 2
		webButton = Button('Web', (30, 15), webEnabled)
		webButton.setPosition((horizontalPosition, verticalPosition))
		buttonList.append(webButton)
		horizontalPosition += webButton.width + 2
		textEnabled = True
		textButton = Button('Text', (30, 15), True)
		textButton.setPosition((horizontalPosition, verticalPosition))
		buttonList.append(textButton)
		horizontalPosition += textButton.width + 2
		imageButton = Button('Images', (45, 15), imagesEnabled)
		imageButton.setPosition((horizontalPosition, verticalPosition))
		buttonList.append(imageButton)
		artistEntrySelected = False
		artistEntry = Button('Artist:', (200, 15), False)
		artistEntry.setPosition((300, verticalPosition))
		artistEntryLabel = font.render('Artist:', True, (255, 255, 255), (64, 64, 64))
		artistEntryText = 'ENTER A BAND NAME HERE'
		artistEntryTextImage = font.render(artistEntryText, True, (255, 255, 255))
		horizontalPosition = 530
		linkDepthText = font.render(str(linkDepth), True, (255, 255, 255))
		linkDepthDownButton = Button('Down', (8, 15), False)
		linkDepthDownButton.setPosition((horizontalPosition, verticalPosition))
		horizontalPosition += linkDepthDownButton.width + 25
		linkDepthUpButton = Button('Up', (8, 15), False)
		linkDepthUpButton.setPosition((horizontalPosition, verticalPosition))
		horizontalPosition += linkDepthUpButton.width + 50
		totalArtistsDownButton = Button('Down', (8, 15), False)
		totalArtistsDownButton.setPosition((horizontalPosition, verticalPosition))
		horizontalPosition += totalArtistsDownButton.width + 25
		totalArtistsUpButton = Button('Up', (8, 15), False)
		totalArtistsUpButton.setPosition((horizontalPosition, verticalPosition))
		upText = font.render('^', True, (255, 255, 255))
		downText = font.render('^', True, (255, 255, 255))
		downText = pygame.transform.rotate(downText, 180)
		linkDepthUpButton.text = upText
		linkDepthDownButton.text = downText
		totalArtistsUpButton.text = upText
		totalArtistsDownButton.text = downText
		linkDepthLabelButton = Button('Link Depth:', (65, 12), False)
		linkDepthLabelButton.setPosition(((linkDepthDownButton.x + (linkDepthUpButton.x + linkDepthUpButton.width)) / 2.0 - (linkDepthLabelButton.width / 2.0), 573))
		#linkDepthLabel = font.render('Link Depth:', True, (255, 255, 255), (64, 64, 64))
		#totalArtistsLabel = font.render('Total Artists:', True, (255, 255, 255), (64, 64, 64))
		totalArtistsLabelButton = Button('TotalArtists:', (70, 12), False)
		totalArtistsLabelButton.setPosition((((totalArtistsDownButton.x + (totalArtistsUpButton.x + totalArtistsUpButton.width)) / 2.0) - (totalArtistsLabelButton.width / 2.0), 573))
		totalArtistsText = font.render(str(totalArtists), True, (255, 255, 255), (64, 64, 64))
		attractLabel = font.render('Attract:', True, (255, 255, 255), (64, 64, 64))
		repelLabel = font.render('Repel:', True, (255, 255, 255), (64, 64, 64))
		lengthLabel = font.render('Length:', True, (255, 255, 255), (64, 64, 64))

	def handleClick(self, event):
		if pygame.mouse.get_pressed()[0] == 1:
			mousePosition = pygame.mouse.get_pos()

			# Control buttons can only be clicked if visible

			if controlsEnabled:

				# Web button

				if webButton.x <= mousePosition[0] <= webButton.x + webButton.width and webButton.y <= mousePosition[1] <= webButton.y + webButton.height:
					artistEntrySelected = False
					webButton.toggleValue()

				# Images button

				elif imageButton.x <= mousePosition[0] <= imageButton.x + imageButton.width and imageButton.y <= mousePosition[1] <= imageButton.y + imageButton.height:
					artistEntrySelected = False
					imageButton.toggleValue()
					if imageButton.value:
						imagesEnabled = True
						for artist in imagedArtists:
							try:
								currentArtist = artists[artist]
								currentArtist.xIncrease = currentArtist.image.get_rect().center[0]
								currentArtist.yIncrease = currentArtist.image.get_rect().center[1]
							except KeyError:
								pass
					else:
						imagesEnabled = False
						for artist in imagedArtists:
							try:
								currentArtist = artists[artist]
								currentArtist.xIncrease = currentArtist.text.get_rect().center[0]
								currentArtist.yIncrease = currentArtist.text.get_rect().center[1]
							except KeyError:
								pass

				# Text button

				elif textButton.x <= mousePosition[0] <= textButton.x + textButton.x + textButton.width and textButton.y <= mousePosition[1] <= textButton.y + textButton.height:
					artistEntrySelected = False
					textButton.toggleValue()

					# Controls visibility button

				elif controlButton.x <= mousePosition[0] <= controlButton.x + controlButton.width and controlButton.y <= mousePosition[1] <= controlButton.y + controlButton.height:
					artistEntrySelected = False
					if controlsEnabled:
						controlsEnabled = False
						controlButtonColour = (64, 64, 64)
					else:
						controlsEnabled = True
						controlButtonColour = (64, 192, 64)

				# Artist entry field

				elif 299 < mousePosition[0] < 501 and 584 < mousePosition[1] < 601:
					artistEntrySelected = True
					if 'ENTER A BAND NAME HERE' in artistEntryText:
						artistEntryText = ''
						artistEntryTextImage = font.render(artistEntryText, True, (255, 255, 255))

					# Link depth down button

				elif linkDepthDownButton.x <= mousePosition[0] <= linkDepthDownButton.x + linkDepthDownButton.width and linkDepthDownButton.y <= mousePosition[1] <= linkDepthDownButton.y + linkDepthDownButton.y + linkDepthDownButton.height:
					if linkDepth < 1:
						pass
					elif linkDepth < 10:
						linkDepth -= 1
					elif linkDepth < 50:
						linkDepth -= 5
					else:
						linkDepth -= 10
					linkDepthText = font.render(str(linkDepth), True, (255, 255, 255))

				# Link depth up button

				elif linkDepthUpButton.x <= mousePosition[0] <= linkDepthUpButton.x + linkDepthUpButton.width and linkDepthUpButton.y <= mousePosition[1] <= linkDepthUpButton.y + linkDepthUpButton.height:
					if linkDepth < 10:
						linkDepth += 1
					elif linkDepth < 50:
						linkDepth += 5
					else:
						linkDepth += 10
					for artist in usableArtists:
						pendingArtists.append(artist)
					linkDepthText = font.render(str(linkDepth), True, (255, 255, 255))

					# Total artists down button

				elif totalArtistsDownButton.x <= mousePosition[0] <= totalArtistsDownButton.x + totalArtistsDownButton.width and totalArtistsDownButton.y <= mousePosition[1] <= totalArtistsDownButton.y + totalArtistsDownButton.height:
					if totalArtists < 1:
						pass
					elif totalArtists < 10:
						totalArtists -= 1
					elif totalArtists < 50:
						totalArtists -= 5
					else:
						totalArtists -= 10
					while len(usableArtists) > totalArtists:
						toRemove = usableArtists.pop()
						index = 0
						while index < len(edges):
							if toRemove + '_' in edges[index] or '_' + toRemove in edges[index]:
								edges.remove(index)
							else:
								index += 1
						index = 0
						while index < len(repels):
							if toRemove + '_' in entry or '_' + toRemove in entry:
								repels.remove(entry)
							else:
								index += 1
						if toRemove in imagedArtists:
							imagedArtists.remove(toRemove)
					totalArtistsText = font.render(str(totalArtists), True, (255, 255, 255), (64, 64, 64))

				# Total artists up button

				elif totalArtistsUpButton.x <= mousePosition[0] <= totalArtistsUpButton.x + totalArtistsUpButton.width and totalArtistsUpButton.y <= mousePosition[1] <= totalArtistsUpButton.y + totalArtistsUpButton.height:
					if totalArtists < 10:
						totalArtists += 1
					elif totalArtists < 50:
						totalArtists += 5
					else:
						totalArtists += 10
					for artist in usableArtists:
						pendingArtists.append(artist)
					totalArtistsText = font.render(str(totalArtists), True, (255, 255, 255), (64, 64, 64))

				# If nothing is selected then drag the display around

				else:
					leftMouseHeld = True

				# Controls visibility button

			elif -1 < mousePosition[0] < 46 and 584 < mousePosition[1] < 601:
				artistEntrySelected = False
				if controlsEnabled:
					controlsEnabled = False
					controlButtonColour = (64, 64, 64)
				else:
					controlsEnabled = True
					controlButtonColour = (64, 192, 64)

			# If nothing is selected then drag the display around

			else:
				artistEntrySelected = False
				leftMouseHeld = True


	def draw(self):
			# Handle any input events which have occured
			for event in pygame.event.get():
				# If the program as been told to exit then tell every thread to be emo
				if event.type == pygame.QUIT:
					suicide = 1

				# Handle any mouse clicks
				elif event.type == pygame.constants.MOUSEBUTTONDOWN:
					pass
				# Enter text if the text entry box is selected

				elif event.type == pygame.constants.KEYDOWN:
					if artistEntrySelected:
						shift = False
						keyPressed = str(pygame.key.name(event.key))
						if keyPressed == 'space':
							artistEntryText = artistEntryText + ' '
						elif keyPressed == 'backspace':
							artistEntryText = artistEntryText[:-1]
						elif keyPressed == 'left shift' or keyPressed == 'right shift':
							pass
						elif keyPressed == 'return':
							givenName = artistEntryText
						else:
							if pygame.key.get_mods() & pygame.constants.KMOD_LSHIFT or pygame.key.get_mods() & pygame.constants.KMOD_RSHIFT:
								artistEntryText = artistEntryText + keyPressed.upper()
							else:
								artistEntryText = artistEntryText + keyPressed
						artistEntryTextImage = font.render(artistEntryText, True, (255, 255, 255))

			# Handle dragging

			if pygame.mouse.get_pressed()[0] == 0:
				leftMouseHeld = False
			if leftMouseHeld:
				relativeMovement = pygame.mouse.get_rel()
				additional = (additional[0] + relativeMovement[0], additional[1] + relativeMovement[1])
			else:
				pygame.mouse.get_rel()

			screen.fill((0, 0, 0))		# Screen has a black background

			# Draw the web if selected

			if webButton.value:
				for edge in edges:
					connection = connections[edge]
					x1 = connection.node1.position[0] + additional[0]
					x2 = connection.node2.position[0] + additional[0]
					y1 = connection.node1.position[1] + additional[1]
					y2 = connection.node2.position[1] + additional[1]
					colour = 255 * connection.strength**5		# This large power differentiates strong and weak connections
					pygame.draw.line(screen, (colour, colour, colour), (x1, y1), (x2, y2), 1)
				if genresEnabled:
					for genre in usableGenres:
						for artist in genres[genre].artists:
							try:
								pygame.draw.line(screen, (128,0,0),(genres[genre].position[0]+additional[0],genres[genre].position[1]+additional[1]),(artists[artist].position[0]+additional[0],artists[artist].position[1]+additional[1]),1)
							except KeyError:
								print "Error: Couldn't draw genre link between " + artist + " and " + genre

			# Draw the artists if selected

			if imageButton.value or textButton.value:
				for artist in usableArtists:
					if imageButton.value:
						try:
							artists[artist].drawImage(screen, additional)
						except KeyError:
							print 'Error: Failed to draw artist ' + artist
					if textButton.value:
						try:
							artists[artist].drawText(screen, additional, imageButton.value)
						except KeyError:
							print 'Error: Failed to draw artist name ' + artist

			# Draw the genres (selection to be implemented)

			if genresEnabled:
				for genre in usableGenres:
					genres[genre].draw(screen, additional)

			# Draw the control buttons if selected

			if controlsEnabled:

				# Web button

				webButton.draw(screen)

				# Images button

				imageButton.draw(screen)

				# Text button

				textButton.draw(screen)

				# Artist entry field

				if artistEntrySelected != artistEntry.value:
					artistEntry.toggleValue()
				artistEntry.draw(screen)
				screen.blit(artistEntryLabel, (390, 573))
				screen.blit(artistEntryTextImage, (artistEntry.x + 35, 587))

				# Link depth down button

				linkDepthDownButton.draw(screen)

				# Link depth display

				pygame.draw.rect(screen, (64, 64, 64), (linkDepthDownButton.x + linkDepthDownButton.width, verticalPosition, 25, 15), 0)
				screen.blit(linkDepthText, (linkDepthDownButton.x + linkDepthDownButton.width + 1, 587))

				# Link depth up button

				linkDepthUpButton.draw(screen)

				# Link depth label

				linkDepthLabelButton.draw(screen)

				# Total artists label

				totalArtistsLabelButton.draw(screen)

				# Total artists down button

				totalArtistsDownButton.draw(screen)

				# Total artists label

				pygame.draw.rect(screen, (64, 64, 64), (totalArtistsDownButton.x + totalArtistsDownButton.width, 585, 25, 15))
				screen.blit(totalArtistsText, (totalArtistsDownButton.x + totalArtistsDownButton.width + 1, 587))

				# Total artists up button

				totalArtistsUpButton.draw(screen)

			# Controls visibility button

			controlButton.draw(screen)

			# Update the screen and wait

			pygame.display.update()
			time.sleep(1.0/fps)

if __name__ == '__main__':
	tasks = []
	
	screen = Display((800, 600))
	screen.start()

	givenName = ''
	if len(sys.argv) > 1:
		args = sys.argv[1:]
		givenName = ''
		for arg in args:
			givenName = givenName + arg + ' '
		givenName = givenName[:-1]
	def checkName():
		if givenName == '':
			return
		artists[givenName] = ArtistNode(givenName, (500, 400), 0)	# Make an arbitrary artist
		range = 1000

		def creation():
			"""Take care of any unprocessed artist entries"""
			if len(usableArtists) <= totalArtists:
				while len(pendingArtists) > 0:
					range /= random.randint(1, 3)
					range /= random.randint(20, 100)
					if (artists[pendingArtists[0]].related == 0):
						return
					currentArtist = artists[pendingArtists.pop(0)]
					current = 0
					while current < (self.linkDepth) and current < len(currentArtist.related) and len(usableArtists) <= totalArtists:
						relatedArtist = currentArtist.related[current]
						if not relatedArtist[0] in artists:
							artists[relatedArtist[0]] = ArtistNode(relatedArtist[0], currentArtist.position, range)
							#for artist in usableArtists:
							#	if artist is not relatedArtist[0]:
							#		artists[relatedArtist[0]].addRepulsion(artists[artist])
							currentArtist.addConnection(artists[relatedArtist[0]], relatedArtist[1])
						current += 1
		tasks.append(creation)
	tasks.append(checkName)
	
	def related():
		if len(unfinishedArtists) > 0:
			for currentArtist in unfinishedArtists:
				if len(artists[currentArtist].related) == 0:
					pass
				else:
					for relatedArtist in artists[currentArtist].related:
						if relatedArtist[0] in usableArtists:
							if relatedArtist[0] + '_' + currentArtist in edges or currentArtist + '_' + relatedArtist[0] in edges:
								pass
							else:
								try:
									artists[currentArtist].addConnection(artists[relatedArtist[0]], relatedArtist[1])
								except KeyError:
									pass
					unfinishedArtists.remove(currentArtist)
	tasks.append(related)

	def imageFetcher():
		if imagesEnabled and len(imagePendingArtists) > 0:
			try:
				currentArtist = artists[imagePendingArtists.pop(0)]
				currentArtist.assignImage()
			except:
				print "Error: Couldn't download image for " + currentArtist.name
				netError += 1
	tasks.append(imageFetcher)

	def lastFetcher():
		if len(relationPendingArtists) > 0:
			if len(relationPendingArtists) > 0:
				try:
					currentArtist = artists[relationPendingArtists.pop(0)]
					currentArtist.assignConnections()
				except:
					print "Error: Couldn't get relations for " + currentArtist.name
			if genresEnabled:
				if len(genreNeedingArtists) > 0:
					try:
						currentArtist = artists[genreNeedingArtists.pop(0)]
						currentArtist.assignGenres()
					except:
						print "Error: Couldn't get genres for " + currentArtist.name
	tasks.append(lastFetcher)
	
	while givenName == '':

	def force():
		def hooke_attract(self, node1, spring):
			try:
				# F=-kx
				node2 = artists[spring[0]]
				deltaX = node2.position[0] - node1.position[0]
				deltaY = node2.position[1] - node1.position[1]
				deltaR = (deltaX**2 + deltaY**2)**0.5		# Pythagoras
				direction = (deltaX / deltaR, deltaY / deltaR)		# unit vector
				magnitude = -1 * 1.0 * float(spring[1]) * deltaR
				return [magnitude * direction[0], magnitude * direction[1]]
			except:
				return [1.0, 1.0]

		def coulomb_repulsion(self, node1, node2):
			deltaX = node2.position[0] - node1.position[0]
			deltaY = node2.position[1] - node1.position[1]
			deltaR = (deltaX**2 + deltaY**2)**0.5		# Pythagoras
			direction = (deltaX / deltaR, deltaY / deltaR)		# unit vector
			magnitude = (node1.charge * node2.charge) / (1.0 * deltaR**2)
			return [magnitude * direction[0], magnitude * direction[1]]
	
		damping = 0.5
		#set up initial node velocities to (0,0)
		for currentArtist in usableArtists:
			artists[currentArtist].velocity = [0, 0]
		#set up initial node positions randomly // make sure no 2 nodes are in exactly the same position
		def phys():
			timestep = 1.0
			#total_kinetic_energy = 0		# running sum of total kinetic energy over all particles
			for artist in usableArtists:
				currentArtist = artists[artist]
	
				currentArtist.force = [0, 0]		# running sum of total force on this particular node
	
				for otherArtist in usableArtists:
					if otherArtist is not artist:
						repulsion = self.coulomb_repulsion(currentArtist, artists[otherArtist])
						currentArtist.force[0] += repulsion[0]
						currentArtist.force[1] += repulsion[1]
	
				for spring in currentArtist.related:
					attraction = self.hooke_attract(currentArtist, spring)
					currentArtist.force[0] += attraction[0]
					currentArtist.force[1] += attraction[1]
	
				# without damping, it moves forever
				currentArtist.velocity[0] += (timestep * currentArtist.force[0]) * damping
				currentArtist.velocity[1] += (timestep * currentArtist.force[1]) * damping
				currentArtist.position[0] += timestep * currentArtist.velocity[0]
				currentArtist.position[1] += timestep * currentArtist.velocity[0]
				#total_kinetic_energy += currentArtist.mass * (currentArtist.velocity[0]**2 + currentArtist.velocity[1]**2)
				#if total_kinetic_energy < 1.0:		# the simulation has stopped moving
				#	break
		tasks.append(phys)
	force()
	
	cockburn = LinearThread()
	cockburn.start()
	while True:
		time.sleep(1)
		if suicide == 1:
			time.sleep(1)
			sys.exit()

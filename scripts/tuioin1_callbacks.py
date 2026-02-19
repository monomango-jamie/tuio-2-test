# me - this DAT
#
# dat - the DAT receiving the TUIO messages
# events - a list of TUIOEvent objects in order of oldest to newest
#
#
# each TUIOEvent objects as the following members
#	timestamp - the TUIO timestamp of this event, in 'seconds since Jan 1, 1900'
#	source - TUIO source string.
#	width - sensor width, up to 65535, TUIO2 only.
#	height - sensor height, up to 65535, TUIO2 only.
# 	touchesStart - a list of touches that started this event
# 	touchesMove - a list of touches that moved this event
#	touchesEnd - a list of touches that ended this event
# 	touchesNoChange - a list of pre-existing touches that didn't move
#						or end this event
#
# each of those touches is a TUIOTouch object which has the following members
#	id
#	profile
#	u, v, w
#	angleX, angleY, angleZ
#	width, height, depth
#	area
#	volume
#	velocityX, velocityY, velocityZ
#	rotationX, rotationY, rotationZ
#	motionAccel
#	rotationAccel
#	classId
# Below are members of touch that are for TUIO2 only:
#	rotationAxisX, rotationAxisY, rotationAxisZ
#	shear
#	radius
#	pressure, pressureVel, pressureAccel
#	typeId, userId
#	symGroup, symData
#	convexHull
#	outerContour, innerContour
#	skeleton, skeletonVolume
#	areaGeometry
#	rawWidth, rawData
#	control
#	datMime, datData
#	sigComponent, sigSessions
#	coaSlot, coaSessions
#	liaType, liaSessions
#	llaType, llaSessions
#	ltaType, ltaSessions
#	(note TUIO2 3d will have rotation axis,
#	 and angle/rotation magnitude will be in angleX, rotationX)
def onTouches(dat, events):
	# Get the webserver DAT
	webserverDAT = parent().parent().op('./web_server/webserver1')

	# Get the streaming mode toggle
	streamConstant = parent().par.Streamconstant.eval()
	debug(streamConstant)
	# Loop through the events
	for event in events:
		# Check if we should skip frames with no changes
		if not streamConstant:
			hasChanges = (len(event.touchesStart) > 0 or
			              len(event.touchesMove) > 0 or
			              len(event.touchesEnd) > 0)
			if not hasChanges:
				continue  # Skip this frame

		# Determine which touches to send as "set" messages
		if streamConstant:
			# Send all active touches every frame
			changedTouches = event.touchesStart + event.touchesMove + event.touchesNoChange
		else:
			# Only send touches that actually changed
			changedTouches = event.touchesStart + event.touchesMove

		# Separate touches by profile type
		pointerTouches = []
		boundsTouches = []
		tokenTouches = []
		symbolTouches = []

		for touch in changedTouches:
			profile = touch.profile
			if "/tuio2/ptr" in profile or profile == "":
				pointerTouches.append(touch)
			elif "/tuio2/bnd" in profile:
				boundsTouches.append(touch)
			elif "/tuio2/tok" in profile:
				tokenTouches.append(touch)
			elif "/tuio2/sym" in profile:
				symbolTouches.append(touch)

		# All active touches for alive messages
		allActiveTouches = event.touchesStart + event.touchesMove + event.touchesNoChange

		# Send POINTER messages (fingers, stylus)
		activePtrIds = [t.id for t in allActiveTouches if "/tuio2/ptr" in t.profile or t.profile == ""]
		if activePtrIds:
			sendOSC(webserverDAT, "/tuio2/ptr", ["alive"] + activePtrIds)

			for touch in pointerTouches:
				sendOSC(webserverDAT, "/tuio2/ptr", [
					"set",
					touch.id,
					0,  # tu_id
					touch.classId,  # c_id
					touch.u,
					touch.v,
					touch.angleZ,
					0.0,  # shear
					0.0,  # radius
					0.0   # pressure
				])

		# Send BOUNDS messages (phones, tablets, objects)
		activeBndIds = [t.id for t in allActiveTouches if "/tuio2/bnd" in t.profile]
		if activeBndIds:
			sendOSC(webserverDAT, "/tuio2/bnd", ["alive"] + activeBndIds)

			for touch in boundsTouches:
				sendOSC(webserverDAT, "/tuio2/bnd", [
					"set",
					touch.id,
					0,  # tu_id
					touch.classId,  # c_id
					touch.u,
					touch.v,
					touch.angleZ,
					touch.width,
					touch.height,
					touch.area
				])

		# Send SYMBOL messages
		activeSymIds = [t.id for t in allActiveTouches if "/tuio2/sym" in t.profile]
		if activeSymIds:
			sendOSC(webserverDAT, "/tuio2/sym", ["alive"] + activeSymIds)

			for touch in symbolTouches:
				group = touch.symGroup if hasattr(touch, 'symGroup') else ""
				data = touch.symData if hasattr(touch, 'symData') else str(touch.classId)

				sendOSC(webserverDAT, "/tuio2/sym", [
					"set",
					touch.id,
					0,  # tu_id
					touch.classId,  # c_id
					group,
					data
				])

		# Send TOKEN messages
		activeTokIds = [t.id for t in allActiveTouches if "/tuio2/tok" in t.profile]
		if activeTokIds:
			sendOSC(webserverDAT, "/tuio2/tok", ["alive"] + activeTokIds)

			for touch in tokenTouches:
				sendOSC(webserverDAT, "/tuio2/tok", [
					"set",
					touch.id,
					0,  # tu_id
					touch.classId,  # c_id
					touch.u,
					touch.v,
					touch.angleZ
				])

		# Send frame message
		sendOSC(webserverDAT, "/tuio2/frm", [
			"frm",
			int(event.timestamp * 1000),
			event.timestamp,
			event.width if hasattr(event, 'width') else 0,
			event.height if hasattr(event, 'height') else 0
		])

	return


def sendOSC(webserverDAT, address, args):
	"""Send OSC message to all WebSocket clients"""
	import json

	msg = {
		"address": address,
		"args": args
	}

	msgJson = json.dumps(msg)
	debug(msgJson)

	# Send to all connected WebSocket clients
	for connection in webserverDAT.webSocketConnections:
		webserverDAT.webSocketSendText(msgJson, connection)

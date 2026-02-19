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
#						or end this event.
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

	for event in events:
		# Skip frames with no touch changes — only send on start/move/end
		hasChanges = (len(event.touchesStart) > 0 or
		              len(event.touchesMove) > 0 or
		              len(event.touchesEnd) > 0)
		if not hasChanges:
			continue

		# Only send touch data for touches that actually changed (never touchesNoChange)
		changedTouches = event.touchesStart + event.touchesMove

		# Separate touches by profile type
		pointerTouches = []
		boundsTouches = []
		tokenTouches = []
		symbolTouches = []

		touchesThatChanged = event.touchesStart + event.touchesMove + event.touchesEnd
		for touch in changedTouches:
			profile = touch.profile or ""

			# Debug: show u,v on any change (start, move, end) for cursor/ptr, bounds, token, symbol
			kind = "ptr" if "/tuio2/ptr" in profile or profile == "" else "bnd" if "/tuio2/bnd" in profile else "tok" if "/tuio2/tok" in profile else "sym"
			symGrp = getattr(touch, "symGroup", None)
			symDat = getattr(touch, "symData", None)
			symExtra = f" symGroup={symGrp!r} symData={symDat!r}" if (symGrp is not None or symDat is not None) else ""
			if touch in event.touchesStart:
				debug(f"[START] {kind} id={touch.id} u={touch.u} v={touch.v}{symExtra}")
			elif touch in event.touchesMove:
				debug(f"[MOVE]  {kind} id={touch.id} u={touch.u} v={touch.v}{symExtra}")

			# Debug (only on changes, not streaming): log any TUIO2-specific data present on this touch
			if hasChanges and touch in touchesThatChanged:
				hasTuio2Data = any([
					getattr(touch, 'shear', None),
					getattr(touch, 'radius', None),
					getattr(touch, 'pressure', None),
					getattr(touch, 'typeId', None),
					getattr(touch, 'userId', None),
					getattr(touch, 'symGroup', None),
					getattr(touch, 'symData', None),
				])
				if hasTuio2Data or profile:
					debug(f"[TUIO2 data] id={touch.id} profile={touch.profile!r} classId={touch.classId} typeId={getattr(touch,'typeId',None)} userId={getattr(touch,'userId',None)} symGroup={getattr(touch,'symGroup',None)} symData={getattr(touch,'symData',None)} shear={getattr(touch,'shear',None)} radius={getattr(touch,'radius',None)} pressure={getattr(touch,'pressure',None)}")

				# Debug: very obvious alert for bnd or tok touches (devices)
				if "/tuio2/bnd" in profile or "/tuio2/tok" in profile:
					debug(f"*** DEVICE ON TABLE *** profile={profile!r} id={touch.id} u={touch.u} v={touch.v} w={touch.width}x{touch.height} classId={touch.classId} symData={getattr(touch,'symData',None)}")

			# symData presence takes priority over profile — the real table sends
			# device touches with profile=None but symGroup/symData populated
			if getattr(touch, 'symData', None) is not None:
				symbolTouches.append(touch)
			elif "/tuio2/ptr" in profile or profile == "":
				pointerTouches.append(touch)
			elif "/tuio2/bnd" in profile:
				boundsTouches.append(touch)
			elif "/tuio2/tok" in profile:
				tokenTouches.append(touch)
			elif "/tuio2/sym" in profile:
				symbolTouches.append(touch)

		# Debug: touches that ended (u,v from last known position)
		for touch in event.touchesEnd:
			profile = touch.profile or ""
			kind = "ptr" if "/tuio2/ptr" in profile or profile == "" else "bnd" if "/tuio2/bnd" in profile else "tok" if "/tuio2/tok" in profile else "sym"
			symGrp = getattr(touch, "symGroup", None)
			symDat = getattr(touch, "symData", None)
			symExtra = f" symGroup={symGrp!r} symData={symDat!r}" if (symGrp is not None or symDat is not None) else ""
			debug(f"[END]   {kind} id={touch.id} u={touch.u} v={touch.v}{symExtra}")

		allActiveTouches = event.touchesStart + event.touchesMove + event.touchesNoChange

		# /tuio2/frm — args: [frameId, oscTime, dim, source]
		# dim packs sensor dimensions: (height << 16) | width
		width = int(event.width) if hasattr(event, 'width') else 0
		height = int(event.height) if hasattr(event, 'height') else 0
		dim = (height << 16) | width
		frameId = int(event.timestamp * 1000) & 0xFFFFFFFF
		oscTime = str(int(event.timestamp * (2**32)))
		source = str(event.source) if hasattr(event, 'source') else "TouchDesigner"
		sendOSC(webserverDAT, "/tuio2/frm", [frameId, oscTime, dim, source], verbose=False)

		# /tuio2/ptr — args: [sessionId, tuId, cId, x, y, angle, shear, radius, press]
		for touch in pointerTouches:
			sendOSC(webserverDAT, "/tuio2/ptr", [
				touch.id,
				touch.userId if hasattr(touch, 'userId') else 0,
				touch.classId,
				touch.u,
				touch.v,
				touch.angleZ,
				touch.shear if hasattr(touch, 'shear') else 0.0,
				touch.radius if hasattr(touch, 'radius') else 0.0,
				touch.pressure if hasattr(touch, 'pressure') else 0.0
			], verbose=hasChanges)

		# /tuio2/bnd — args: [sessionId, x, y, angle, sizeW, sizeH, area]
		for touch in boundsTouches:
			sendOSC(webserverDAT, "/tuio2/bnd", [
				touch.id,
				touch.u,
				touch.v,
				touch.angleZ,
				touch.width,
				touch.height,
				touch.area
			], verbose=hasChanges)

		# /tuio2/tok — args: [sessionId, tuId, cId, x, y, angle]
		for touch in tokenTouches:
			sendOSC(webserverDAT, "/tuio2/tok", [
				touch.id,
				touch.userId if hasattr(touch, 'userId') else 0,
				touch.classId,
				touch.u,
				touch.v,
				touch.angleZ
			], verbose=hasChanges)

		# /tuio2/sym — args: [sessionId, tuId, cId, group, data]
		for touch in symbolTouches:
			group = touch.symGroup if hasattr(touch, 'symGroup') else ""
			data = touch.symData if hasattr(touch, 'symData') else str(touch.classId)
			sendOSC(webserverDAT, "/tuio2/sym", [
				touch.id,
				touch.userId if hasattr(touch, 'userId') else 0,
				touch.classId,
				group,
				data
			], verbose=hasChanges)

		# /tuio2/alv — all active session IDs, sent last to trigger frame processing
		allActiveIds = [t.id for t in allActiveTouches]
		sendOSC(webserverDAT, "/tuio2/alv", allActiveIds, verbose=False)

	return

def sendOSC(webserverDAT, address, args, verbose=False):
	import json
	msg = {"address": address, "args": args}
	msgJson = json.dumps(msg)
	if verbose:
		debug(msgJson)
	for client in webserverDAT.webSocketConnections:
		webserverDAT.webSocketSendText(msgJson, client)

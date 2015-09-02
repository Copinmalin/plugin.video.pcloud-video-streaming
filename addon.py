import resources.lib.pcloudapi

import sys
import urllib
import urlparse
import xbmcplugin
import xbmcgui
import xbmcaddon
from datetime import datetime, timedelta
import time

myAddon = xbmcaddon.Addon()
#customSettingsPath = xbmc.translatePath( __addon__.getAddonInfo("profile") ).decode("utf-8")
#customSettingsFilename = customSettingsPath + "customSettings.xml"

base_url = sys.argv[0] 						# The base URL of your add-on, e.g. 'plugin://plugin.video.pcloud-video-streaming/'
addon_handle = int(sys.argv[1])				# The process handle for this add-on, as a numeric string
xbmcplugin.setContent(addon_handle, 'movies')

args = urlparse.parse_qs(sys.argv[2][1:])	# The query string passed to your add-on, e.g. '?foo=bar&baz=quux'

# Instance of PCloudApi
pcloud = resources.lib.pcloudapi.PCloudApi()

#DATE_EXPORT_FORMAT = "%Y-%m-%d %H:%M:%S"
'''
class MyXbmcMonitor( xbmc.Monitor ):
    def __init__( self, *args, **kwargs ):
		xbmc.Monitor.__init__(self)
    
    def onSettingsChanged( self ):
        xbmcgui.Dialog().notification("Info", "Settings changed", time=10000)		
'''
def IsAuthMissing():
	auth = myAddon.getSetting("auth")
	authExpiryStr = myAddon.getSetting("authExpiry")
	if authExpiryStr is None or authExpiryStr == "":
		return True
	authExpiryTimestamp = float(authExpiryStr)
	authExpiry = datetime.fromtimestamp(authExpiryTimestamp)
	if datetime.now() > authExpiry or auth == "":
		return True
	# If we're here it means there is valid auth saved in the config file
	pcloud.SetAuth(auth)
	return False

def AuthenticateToPCloud():
	yesNoDialog = xbmcgui.Dialog()
	wantToAuthenticate = yesNoDialog.yesno(
							"Log On",
							"Log on to PCloud?")
	if not wantToAuthenticate:
		return False
	usernameDialog = xbmcgui.Dialog()
	username = usernameDialog.input("PCloud username (email)")
	if username == "":
		return False
	passwordDialog = xbmcgui.Dialog()
	password = passwordDialog.input(
									"PCloud password",
									option=xbmcgui.ALPHANUM_HIDE_INPUT)
	if password == "":
		return False
	try:
		auth = pcloud.PerformLogon(username, password)
	except Exception as ex:
		xbmcgui.Dialog().notification(
			"Error", "Cannot log on to PCloud (see log)",
			icon=xbmcgui.NOTIFICATION_ERROR,
			time=5000)
		xbmc.log("ERROR: cannot logon to PCloud: " + `ex`, xbmc.LOGERROR)
		return False
	myAddon.setSetting("auth", auth)
	authExpiry = datetime.now() + timedelta(seconds = pcloud.TOKEN_EXPIRATION_SECONDS)
	authExpiryTimestamp = time.mktime(authExpiry.timetuple())
	myAddon.setSetting("authExpiry", `authExpiryTimestamp`)
	xbmcgui.Dialog().notification("Success", "Logon successful", time=5000)
	return True
	
folderID = None

# Mode is None when the plugin gets first invoked - Kodi does not pass a query string to our plugin's base URL
mode = args.get("mode", None)
if mode is None:
	mode = [ "folder" ]
	
if mode[0] == "folder":
	if IsAuthMissing():
		authResult = AuthenticateToPCloud()
		if authResult == False:
			exit()
	folderID = args.get("folderID", None)
	if folderID is None:
		folderID = 0
	else:
		folderID = int(folderID[0])
	
	folderContents = pcloud.ListFolderContents(folderID)
	for oneItem in folderContents["metadata"]["contents"]:
		if oneItem["isfolder"] == True:
			url = base_url + "?mode=folder&folderID=" + `oneItem["folderid"]`
			li = xbmcgui.ListItem(oneItem["name"], iconImage='DefaultFolder.png')
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
									listitem=li, isFolder=True)
		else:
			contentType = oneItem["contenttype"]
			if contentType != "video/mp4": #TODO: add more content types
				continue
			li = xbmcgui.ListItem(oneItem["name"], iconImage='DefaultVideo.png')
			li.addStreamInfo(
				"video", 
				{ 	"duration": int(float(oneItem["duration"])),
					"codec": oneItem["videocodec"],
					"width": oneItem["width"],
					"height": oneItem["height"]
				}
			)
			li.addStreamInfo(
				"audio",
				{ 	"codec", oneItem["audiocodec"] }
			)
			fileUrl = base_url + "?mode=file&fileID=" + `oneItem["fileid"]`
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=fileUrl, listitem=li)
			
	xbmcplugin.endOfDirectory(addon_handle)
	
elif mode[0] == "file":
	if IsAuthMissing():
		authResult = AuthenticateToPCloud()
		if authResult == False:
			exit()
	fileID = int(args["fileID"][0])
	# Get streaming URL from pcloud
	streamingUrl = pcloud.GetStreamingUrl(fileID)
	player = xbmc.Player()
	player.play(streamingUrl)
'''
elif mode[0] == "showSettings":
	previousUsername = myAddon.getSetting("username")
	previousPassword = myAddon.getSetting("password")
	myAddon.openSettings()
	newUsername = myAddon.getSetting("username")
	newPassword = myAddon.getSetting("password")
	if newUsername != previousUsername or newPassword != previousPassword:
		auth = pcloud.PerformLogon(newUsername, newPassword)
		myAddon.setSetting("auth", auth)
		authExpiry = datetime.now() + timedelta(seconds = pcloud.TOKEN_EXPIRATION_SECONDS)
		authExpiryTimestamp = time.mktime(authExpiry.timetuple())
		myAddon.setSetting("authExpiry", `authExpiryTimestamp`)
		#folderUrl = base_url + "?mode=folder"
		#xbmc.executebuiltin("RunPlugin('%s')" % (folderUrl))
		xbmcgui.Dialog().ok("Success", "Logon successful", "Please hit Back and then click again on this plugin.")
'''

# Needs a better name. Many functions obviously taken from YouTube API v3.
# Displays every combination of videos (not including repeats) from a 
# YouTube playlist for a given time that is specified by the user.

import argparse
import os
import copy
import json
import sys

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow


# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains

# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = 'client_secret.json'

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'


# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:
   %s
with information from the APIs Console
https://console.developers.google.com

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

# Authorize the request and store authorization credentials.
def get_authenticated_service():
  flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
  credentials = flow.run_console()
  return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

  storage = Storage("%s-oauth2.json" % sys.argv[0])
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run_flow(flow, storage, args)

  return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    http=credentials.authorize(httplib2.Http()))


def print_response(response):
  print(response)

# Build a resource based on a list of properties given as key-value pairs.
# Leave properties with empty values out of the inserted resource.
def build_resource(properties):
  resource = {}
  for p in properties:
    # Given a key like "snippet.title", split into "snippet" and "title", where
    # "snippet" will be an object and "title" will be a property in that object.
    prop_array = p.split('.')
    ref = resource
    for pa in range(0, len(prop_array)):
      is_array = False
      key = prop_array[pa]

      # For properties that have array values, convert a name like
      # "snippet.tags[]" to snippet.tags, and set a flag to handle
      # the value as an array.
      if key[-2:] == '[]':
        key = key[0:len(key)-2:]
        is_array = True

      if pa == (len(prop_array) - 1):
        # Leave properties without values out of inserted resource.
        if properties[p]:
          if is_array:
            ref[key] = properties[p].split(',')
          else:
            ref[key] = properties[p]
      elif key not in ref:
        # For example, the property is "snippet.title", but the resource does
        # not yet have a "snippet" object. Create the snippet object here.
        # Setting "ref = ref[key]" means that in the next time through the
        # "for pa in range ..." loop, we will be setting a property in the
        # resource's "snippet" object.
        ref[key] = {}
        ref = ref[key]
      else:
        # For example, the property is "snippet.description", and the resource
        # already has a "snippet" object.
        ref = ref[key]
  return resource

# Remove keyword arguments that are not set
def remove_empty_kwargs(**kwargs):
  good_kwargs = {}
  if kwargs is not None:
    for key, value in kwargs.items():
      if value:
        good_kwargs[key] = value
  return good_kwargs

# Gets all the info of the playlist as a dictionary response.
# From YouTube API
def playlist_items_list_by_playlist_id(client, **kwargs):
  kwargs = remove_empty_kwargs(**kwargs)

  response = client.playlistItems().list(
    **kwargs
  ).execute()

  return response

# Grabs from playlist's info. (Need to make it grab from video info)
def get_all_the_video_titles(response, numVideos, listOfTitles):
  if(numVideos != 0):
    for i in range(numVideos):
      something = response['items'][i]['snippet']['title']
      listOfTitles.append(something)

  return listOfTitles

# Grabs from playlist's info.
def get_all_the_videoIDs(response, numVideos, listOfIDs):
  if(numVideos != 0):
    for i in range(numVideos):
      somethingElse = response['items'][i]['snippet']['resourceId']['videoId']
      listOfIDs.append(somethingElse)

  return listOfIDs

# From YouTube API
def videos_list_multiple_ids(client, **kwargs):
  # See full sample for function
  kwargs = remove_empty_kwargs(**kwargs)

  response = client.videos().list(
    **kwargs
  ).execute()

  return response

# knapsack-based problem solved recursively, using nested lists.
# It does not use the current index its on when finding combos.
#
# I think if I were to save combination of a successful combination
# (e.g. videos 1 & 19 -> videos 19 & 1), that would possibly make
# this function be a little faster, as it would not have to check
# previous indices at all (I think)
def find_all_the_combinations_recursively(listOfTemps, listOfIndexesUsed, 
currentSecondsCombination, listOfSeconds, remainingTime, margin, 
listOfTitles, currentTitleCombination):
  if (remainingTime >= (-margin if margin > 0 else 0)) & (remainingTime <= margin):
    tempList = []
    # If you do not deep copy this thing, tempList will just point to the same
    # list that currentTitleCombination does and that messes everything up.
    tempList = copy.deepcopy(currentTitleCombination)
    #print('Found a combination!')
    return tempList
  elif remainingTime < margin:
    return []
  else:
    otherTempList = []
    lenOfListOfSeconds = len(listOfSeconds)
    for i in range(lenOfListOfSeconds):
      if i not in listOfIndexesUsed: # This is to not have the same video listed more than once.
        currentSecondsCombination.append(listOfSeconds[i])
        currentTitleCombination.append(listOfTitles[i])
        listOfIndexesUsed.append(i)
        otherTempList = find_all_the_combinations_recursively(listOfTemps,
        listOfIndexesUsed, currentSecondsCombination, listOfSeconds, 
        remainingTime-listOfSeconds[i], margin, listOfTitles, 
        currentTitleCombination)
        #otherTempList becomes listOfTemps if otherTempList has items
        #but is unable to find a correct set when the for loop finishes.
        #Trying to append listOfTemps to itself adds an empty list to it.
        if (otherTempList != []) & (otherTempList != listOfTemps):
          listOfTemps.append(otherTempList)
        index = len(currentSecondsCombination) - 1
        del currentSecondsCombination[index]
        del currentTitleCombination[index]
        del listOfIndexesUsed[index]
      #
    return listOfTemps


if __name__ == '__main__':
  print('Caution: If your playlist has many videos of a short duration and the video you made has a long duration, this program can take a long time.')
  pageNumber = 0
  maxResults = 50
  listOfTitles = []
  listOfIDs = []
  youtube = None
  # Get authenticated
  while youtube is None:
    try:
      youtube = get_authenticated_service()
    except (KeyboardInterrupt, SystemExit):
      raise
    except:
      print('\nIncorrect authorization code, try again.\n')
      youtube = get_authenticated_service()

  playlistID = input('Please enter the playlist ID (found in the URL after "list="): ')
  response = None
  #Get information of playlist from youtube using their api v3
  while response is None:
    try:
      response = playlist_items_list_by_playlist_id(youtube,
      part='snippet', # need to figure out how to receive more specific results
      maxResults=maxResults,
      playlistId=playlistID)
    except:
      print('Playlist incorrect or not found. Try again.')
      sys.exit(0)
      
  
  # Printing results collected.
  print('Retreived playlist information successfully!')
  print('Collecting video titles and video IDs now...')
  totalResults = response['pageInfo']['totalResults']
  print('Total amount of results should be: ', totalResults)
  totalPages = 1 + int(totalResults)//maxResults
  print('Total amount of pages: ', totalPages)
  remainderVideos = int(totalResults)%maxResults
  
  # Extracting titles and video IDs from response
  while pageNumber < totalPages:
    print('Page number: ', pageNumber)
    if pageNumber + 1 < totalPages:
      pageToken = response.get('nextPageToken')
      okToGetNextPage = True
    else:
      pageToken = None
      print('Current page number is the last page.')
      okToGetNextPage = False

    # Need to move getting listOfTitles from playlist info to video info to avoid private videos.
    listOfTitles = get_all_the_video_titles(response, maxResults if okToGetNextPage else remainderVideos, listOfTitles)
    listOfIDs = get_all_the_videoIDs(response, maxResults if okToGetNextPage else remainderVideos, listOfIDs)

    # Shouldn't be a need for this to be in a try-except
    response = playlist_items_list_by_playlist_id(youtube,
    part='snippet',
    maxResults=maxResults,
    pageToken=pageToken,
    playlistId=playlistID)

    pageNumber += 1

  print('Number of titles collected: ', len(listOfTitles))
  print('Number of IDs collected: ', len(listOfIDs))
  print('Now collecting video durations...')
  listOfTimes = []
  stringOfIDs = ""
  # So, the "id" parameter in the videos_list_multiple_ids function
  # needs a string of each video ID as: videoID1,videoID2,videoID3,...
  # all the way up to 50, so that's what this next part does and handles.
  if totalPages > 1:
    for i in range(0, 50*(totalPages-1), 50):
      for j in range(49):
        stringOfIDs = stringOfIDs + listOfIDs[i + j] + ','
      stringOfIDs = stringOfIDs + listOfIDs[i + 49]
      response = videos_list_multiple_ids(youtube,
        part='contentDetails',
        id=stringOfIDs)

      for k in range(50):
        # This is incase of a private video inside a playlist.
        try:
          listOfTimes.append(response['items'][k]['contentDetails']['duration'])
        except IndexError:
          pass
    
      stringOfIDs = ""
      print('Page ' + str(i//50) + ' completed')
      
    print('Getting remaining video durations on last page')
    for l in range(remainderVideos-1 if remainderVideos != 0 else 49):
      stringOfIDs = stringOfIDs + listOfIDs[50*(totalPages-1) + l] + ','
    stringOfIDs = stringOfIDs + listOfIDs[50*(totalPages-1) + remainderVideos-1 if remainderVideos != 0 else 49]
    
    # getting snippet information will allow me to get titles.
    response = videos_list_multiple_ids(youtube,
      part='contentDetails',
      id=stringOfIDs)

    for m in range(remainderVideos if remainderVideos != 0 else 50):
      # Also in case of a private video inside a playlist
      try:
        listOfTimes.append(response['items'][m]['contentDetails']['duration'])
      except IndexError:
        pass   

  #Only one page.
  else:
    for l in range(remainderVideos-1 if remainderVideos != 0 else 49):
      stringOfIDs = stringOfIDs + listOfIDs[50*(totalPages-1) + l] + ','
    stringOfIDs = stringOfIDs + listOfIDs[50*(totalPages-1) + remainderVideos-1 if remainderVideos != 0 else 49]
    response = videos_list_multiple_ids(youtube,
      part='contentDetails',
      id=stringOfIDs)

    for m in range(remainderVideos if remainderVideos != 0 else 50):
      listOfTimes.append(response['items'][m]['contentDetails']['duration'])     

  lenOfList = len(listOfTimes)
  print('Number of video durations collected: ', lenOfList)

  if(lenOfList != len(listOfTitles)):
    print('Error, 1 or more videos in the playlist given does not have a duration. Please remove that video(s) until I feel like making a work around.')
    sys.exit(0)
  
  totalSeconds = 0
  totalMinutes = 0
  totalHours = 0
  listOfSeconds = []
  # Youtube has the format of PT_H_M_S with blanks being one or two numbers
  for i in range(lenOfList):
    pt = listOfTimes[i].split('T')
    
    if 'H' in pt[1]:
      hours = pt[1].split('H')
      totalHours = int(hours[0])
      if 'M' in hours[1]:
        minutes = hours[1].split('M')
        totalMinutes = int(minutes[0])
        if 'S' in minutes[1]:
          seconds = minutes[1].split('S')
          totalSeconds = int(minutes[0])

    elif 'M' in pt[1]:
      minutes = pt[1].split('M')
      totalMinutes = int(minutes[0])
      if 'S' in minutes[1]:
        seconds = minutes[1].split('S')
        totalSeconds = int(seconds[0])

    elif 'S' in pt[1]:
      seconds = pt[1].split('S')
      totalSeconds = int(seconds[0])

    listOfSeconds.append(totalHours*360 + totalMinutes*60 + totalSeconds)
    
  print("Using the format HH:MM:SS for your video, please answer the following requests: ")
  userVideoDurationHours = input("Please enter the HH portion of your video's duration (HH:MM:SS). If 0, enter 0.\n")
  while (not userVideoDurationHours.isdigit()) | (len(userVideoDurationHours) < 1):
    print("The input given was not usable, please enter the amount of hours in the correct format.\n")
    userVideoDurationHours = input("Please enter the HH portion of your video's duration (HH:MM:SS). If 0, enter 0.\n")
  userVideoDurationMinutes = input("Please enter the MM portion of your video's duration (HH:MM:SS). If 0, enter 0.\n")
  while (not userVideoDurationMinutes.isdigit()) | (len(userVideoDurationMinutes) > 2) | (len(userVideoDurationMinutes) < 1):
    print("The input given was not usable, please enter the amount of minutes in the correct format.\n")
    userVideoDurationMinutes = input("Please enter the MM portion of your video's duration (HH:MM:SS). If 0, enter 0.\n")
  userVideoDurationSeconds = input("Please enter the SS portion of your video's duration (HH:MM:SS). If 0, enter 0.\n")
  while (not userVideoDurationSeconds.isdigit()) | (len(userVideoDurationSeconds) > 2) | (len(userVideoDurationMinutes) < 1):
    print("The input given was not usable, please enter the amount of seconds in the correct format.\n")
    userVideoDurationSeconds = input("Please enter the SS portion of your video's duration (HH:MM:SS). If 0, enter 0.\n")

  totalUserVideoDuration = int(userVideoDurationHours)*3600 + int(userVideoDurationMinutes)*60 + int(userVideoDurationSeconds)
  
  # I think a user should only need about at most a minute of wiggle room tbh.
  margin = input("If you would like to have a range of acceptable times, please enter a margin below 60 seconds, otherwise, enter 0:\n")
  while (not margin.isdigit()) | (len(margin) > 2) | (len(margin) < 1):
    if int(margin) > 60:
      print("The input given was not usable, please enter the amount of seconds in the correct format.\n")
      margin = input("If you would like to have a range of acceptable times for the length of the combination of videos to be, please enter an amount of seconds to be used as a margin (below 60), otherwise, enter 0:\n")
  
  totalPlaylistDuration = 0
  listOfSecondsLen = len(listOfSeconds)
  for i in range(listOfSecondsLen):
    totalPlaylistDuration += listOfSeconds[i]

  margin = int(margin)
  if (totalUserVideoDuration + margin <= totalPlaylistDuration):
    print("Now determining the combinations of songs that will fit into your video!")

    listOfCombinations = []
    currentSecondsCombination = []
    currentTitleCombination = []
    listOfTemps = []
    listOfIndexesUsed = []
    
    # This is a knapsack problem solved using lists. 
    for i in range(listOfSecondsLen):
      print('Analyzing song ' + str(i+1) + '/' + str(listOfSecondsLen) + '...')
      currentSecondsCombination.append(listOfSeconds[i])
      currentTitleCombination.append(listOfTitles[i])
      listOfIndexesUsed.append(i)
      listOfTemps = find_all_the_combinations_recursively(listOfTemps,
      listOfIndexesUsed, currentSecondsCombination, listOfSeconds,
      totalUserVideoDuration - listOfSeconds[i], margin, listOfTitles,
      currentTitleCombination)
      if listOfTemps != []:
        listOfCombinations.append(listOfTemps)
      # Using del on these made something weird happen, so this is how
      # I'm clearing them.
      listOfTemps = []
      currentSecondsCombination = []
      currentTitleCombination = []
      listOfIndexesUsed = []
      #print('Song ' + str(i+1) + '/' + str(listOfSecondsLen) + ' analyzed.')

    print("Formatting results...")

    # First time using json. Trying to only use .write didn't work since YouTube
    # titles can have special characters and json doesn't really care about those.
    if listOfCombinations != []:
      with open('videos.json', 'w') as outfile:
        j = 0
        for i in listOfCombinations:
          if len(listOfCombinations[j][0][0]) > 1:
            tempString = "List of videos starting with " + str(listOfCombinations[j][0][0] + ":")
            json.dump(tempString, outfile)
            outfile.write('\n')
          else: # Just one element
            tempString = "List of videos starting with " + str(listOfCombinations[j][0] + ":")
            json.dump(tempString, outfile)
            outfile.write('\n')
          json.dump(listOfCombinations[j], outfile)
          if j != (len(listOfCombinations) - 1):
            outfile.write('\n\n')
          j += 1

      print("The results have been put in a json file labeled videos.json in the same directory as this program is in.")

    else:
      print('No combinations of songs in your playlist fit the criteria you gave.')
  else:
    print('Error, duration + margin given exceeds duration of playlist. Try again with a smaller margin or a longer playlist.')

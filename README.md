# kTunes

Purpose: Use the iTunes Genre field to create playlists with a user defined percentage from each genre. The songs from each genre are merged together in a final playlist that also
tries to minimuze repeating of artist. For example an artist from the first genre choice can only be played every 15 songs. 

## Requirements: 
- You use the "Genre" field in iTunes is used to classify music by catagories
- You have enable iTunes to share the catalog with 3rd parties. Doing so creates an xml file of your iTunes catalog that this project reads in.
- You have apple script ImportM3U.vbs copied to your iTunes directory. This allows duplicates of songs to appear in a playlist. The basic iTunes interface will remove dups 
when you import a playlist. 
              
              
## Processing
- The existing iTunes xml file is copied to the project directory then loaded to a sqlite table. All songs are loaded into a table sorted by least recently played.
- A flask web app presents a screen where you provide:
  - Name of playlist, 
  - Total length in minutes of new playlist,
  - % to include of each genre(category).

- After you submit the flash form it will how how many total songs the new playlist contains and the # of songs from each genre(category)
- The process_db.py script will analyze the current itunes dictionary and parse out songs to
- Running a post script copies the new playlist to your iTunes direcory. 
- In Explorer you must drop the playlist on top of the ImportM3U.vbs apple script
## Flask app sample screen print
![kTunes screen](https://user-images.githubusercontent.com/107451552/192881760-4221c58a-b2de-4b18-a0b1-755aeb20f217.png)

## Note
This is my first Python project - it's quite rough. If your an experienced programmer, turn away now.

## Still needed
Batch mode - should be able to read a file with parms to create new playlist without having to go to the app to enter in data. process_db.py can be run
outside of the flask app but should be modified to read in a parm file.

Variable genre(category fields) - Currently it's hard-coded for my use with 5 genre's that meet my needs. Want to paramerterize the genre choices.

Variable artist repeat interval - Currently hard coded for each of the 5 genres (15,15,30,45,45). I want to paramertierize these. Here's more detail on how the repeat intermal works. Artist repeat also takes into consideration genre(category) the repeat interval for each of the 5 genre(categories). If artist an is in the first genre and in the 5th genre and a song for that artist coming from the first genre (which has a repeat of 15) is added to the playlist and then another song for that artist
is found but it is from 5th genre, it won't be added to the playlist till there's at least 44 other songs added.
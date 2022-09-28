# kTunes

Purpose: Provide an alternative to iTunes smartplaylist. Using the iTunes Genre field, create playlists with user defined percentages for each genre. The songs from each genre are merged together in a final playlist that also tries to minimuze repeating of artist. For example an artist from the first genre choice can only be played every 15 songs (see "Variable artist repeat interval" below for more detail). The final playlist will be ordered by least recently played per genre. The new playlist can be played with any app the reads *.m3u files but if you want to continue to make playlist based on least recently played date the playlist must be played through iTunes.

## Requirements: 
- You use the "Genre" field in iTunes to classify music by catagories
- You have enable iTunes to share the catalog with 3rd parties. Doing so creates an xml file of your iTunes catalog that this project reads in.
- You have apple script ImportM3U.vbs copied to your iTunes directory. This allows duplicates of songs to appear in a playlist. The basic iTunes interface will remove dups when you import a playlist
              
## Processing
- The existing iTunes xml file is copied to the project directory then loaded to a sqlite table. All songs are loaded into a table in least recently played order
- A flask web app presents a screen where you provide:
  - Name of playlist
  - Total length in minutes of new playlist
  - % to include for each genre(category)

- After you submit the flash form it will display how many total songs the new playlist contains and the # of songs from each genre(category)
- The process_db.py script will first build a placeholder playlist. It contains an entry for each song but only indicates what genre it will be. This is just trying to create a smooth mixtrue of the 5 genres. Next it will parse out songs from the loaded sqlite table to final playlist file.
- Running a post script copies the new playlist to your iTunes direcory
- In Explorer you must drop the playlist on top of the ImportM3U.vbs apple script

## Note
This is my first Python project - it's quite rough. If you're an experienced programmer turn away now.

## Still needed
- requirements.txt file
- variable to specify iTunes directory
- Batch mode - should be able to read a file with parms to create new playlist without having to go to the app to enter in data. "process_db.py" can be run
outside of the flask app but I'd like to modified it to read in a parm file.
- Variable genre(category) fields - Currently it's hard-coded with the 5 genres I use. I want to paramerterize the genre choices.

- Variable artist repeat interval - Currently hard coded for each of the 5 genres (15,15,30,45,45). I want to paramertierize these. Here's more detail on how the repeat intermal works. Artist repeat takes into consideration the artist and the repeat interval for each of the 5 genre(categories). If an artist has a song in the first genre and another in the 5th genre and a song for that artist coming from the first genre (which has a repeat of 15) is added to the playlist and then another song for that artist is found but it's from 5th genre, it won't be added to the playlist till there's at least 44 other songs added.

## Flask app sample screen print
![kTunes screen](https://user-images.githubusercontent.com/107451552/192881760-4221c58a-b2de-4b18-a0b1-755aeb20f217.png)


# kTunes

Purpose: Use the iTunes Genre field to create playlists with a user defined percentage from each genre.

## Requirements: 
- You use the "Genre" field in iTunes is used to classify music by catagories
- You have enable iTunes to share the catalog with 3rd parties. Doing so creates an xml file of your iTunes catalog that this project reads in.
- You have apple script ImportM3U.vbs (copied to your iTunes directory).
              
              
## Processing
- The existing iTunes xml file is copied to the project directory then loaded to a sqlite table.
- A flask web app presents a screen where you provide:
  Name of playlist, 
  Total length in minutes of new playlist,
  % to include of each genre(category).

- After you submit the flash form it will how how many total songs the new playlist contains and the # of songs from each genre(category)
- Running a post script copies the new playlist to your iTunes direcory. 
- In Explorer you must drop the playlist on top of the ImportM3U.vbs apple script
## Flask app sample screen print
![kTunes screen](https://user-images.githubusercontent.com/107451552/192881760-4221c58a-b2de-4b18-a0b1-755aeb20f217.png)


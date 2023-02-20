# kTunes - Creating a smarter playlist for iTunes

## Purpose

Create a playslist of all your songs spaced out based on user defined categories. kTunes uses iTunes Genre to define categories.
It expects 5 categories and you choose a percentage of each to include in your playlist. The songs selected for each category are ordered by least recently played. The final playlist merges all the genres together based on the percentages. The playlist also minimizes the repeating of artists. For example an artist should only be played every 30 songs. Each cagegory can have a different repeat interval (see "Variable artist repeat interval" below for more detail). 

An additional dynamic(on-the-fly) category can be created of your recently added songs from the "Latest" category.  If this option is selected on the web form you'll also need to choose a "recent add" date and a weighting of these songs as compared to the remaining "Latest" songs. This option allows your most recent songs to be heard just a little more frequently than others in the "Latest" category.

The new playlist can be played with any app that reads *.m3u files but if you want to continue to make playlist based on least recently played date the playlist must be played through iTunes.

## Requirements
- You use the "Genre" field in iTunes. You can have up to 5 genres that can be used for categories.
- You have enabled iTunes to share the catalog with 3rd parties. Doing so creates an xml file of your iTunes catalog that this project reads in.
- You have apple script ImportM3U.vbs copied to your iTunes directory. This allows duplicates of songs to appear in a playlist. The basic iTunes interface will remove dups when you import a playlist.

## Default Genres(Categories)
These are the categories I'm using in the genre field in my iTunes library. Since the python code has these hard coded I'll describe how I'm using them.
- Latest - Songs I'm currently really enjoying or newly discovering. My playlist will have a significant amount of these songs - maybe 30-50%. Using the "recent add" switch can give an even higher priority to the newest songs in this category.
- In Rotation - Songs that are still pretty new and want to be in pretty regular rotation but just not as much as they used to.
- Other - Songs I still like but have been around for a while.
- Old - These songs really date me.
- Album - Some deep cuts that I like to hear now and then.

## Processing
- The existing iTunes xml file is copied to the project directory then loaded to a sqlite table. All songs are inserted or updated into a table in least recently played order
- A flask web app presents a screen where you provide:
  - Name of playlist
  - Total desired length in minutes for new playlist
  - % to include for each genre(category)

- After you submit the flask form it will display how many total songs the new playlist contains and the # of songs from each genre(category)
- The process_db.py script has the algyrythn that evenly disperse songs from the different categories and manages the repeat interval of artist based on your criteria.
- Running a post script copies the new playlist to your iTunes direcory
- In Explorer you must drop the playlist on top of the ImportM3U.vbs apple script

## Note
This is my first Python project - it's quite rough. If you're an experienced programmer turn away now. 

I used VS Code(love it!) and virtualwrapper for my development environment.
Here's a couple extensions to VS code that were helpful:
- SQLite by alexcvzz
- SQLite Viewer by Florian Klampfer

## Still needed
- variable to specify iTunes directory
- An Auto execution mode. A single step that runs the entire process including updating your iTunes playlist with a new track list.
- A config file of parms. Currently the initial values of parms are hard coded in the script. The genres(categories) should also be user defined in this file. Currently its using the 5 categories I use. 
- Variable artist repeat interval - Currently hard coded for each of the 5 genres (15,20,30,50,50,50). I want to paramertierize these. Here's more detail on how the repeat intermal works. Artist repeat takes into consideration the artist and the repeat interval for each of the 5 categories. If an artist has a song in the first category and another in the 5th category and a song for that artist coming from the first category (which has a repeat of 15) is added to the playlist and then another song for that artist is found but it's from 5th category, it won't be added to the playlist till there's at least 44 other songs from that category added.

##  Files
- app.py - the flask app. Run this to create the DB, load the tables and run the flask app
- create_sqlite_tbls.py - creates the sqlite table - duh! Called by load_xml if database does not exit
- load_xml.py - loads the sqlite table with your itunes xml file. Called from app.py
- process_db.py - this is the gutts of the processing. Called from app.py

- workflow_pre.sh - shell script to copy your itunes xml file to project directory and run the flask app which will provide you with the local URL for the app.
- workflow_post.sh - Copies your playlist to your itunes directory were you can use ImportM3U.vbs to import it to your itunes catalog.

- requirements.txt - use **pip install -r requirements.txt** to install all packages required for this project.

## Flask app sample screen print
![kTunes v0 2](https://user-images.githubusercontent.com/107451552/214996103-66aac49f-fd82-4805-b94d-59b4182f977d.png)


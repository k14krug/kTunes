#import pandas as pd

import re # regular expresions
import xml.etree.ElementTree as ET ## XML parsing

#Reading itunes Library xml file. It contains a element tree called <dict> that contains all the tracks and after that an element tree
# also called <dict> that contains all the playlists.
#lib = r'C:\Users\nwkru\Music\iTunes\Libray.xml'
lib = "lib_1song.xml"

# kkrug 6/20/2022 - the library xml has three levels of the <dict> tag. Its only the 3rd (lowest) level we care about. At the third level, each
#                   <dict> tag represents a song and all the tags within it.
#                   The main_dict create an element list starting with the first <dict> tag (actually the first tag after the first <dict> tag)
#                   The for loop is traversing down the tags until it gets to the 2nd <dict> tag in the file
#                   Then tracklist is an element list of all tracks. I
tree = ET.parse(lib)
root = tree.getroot()
#main_dict=root.findall("./dict[1]") ken failed experiment
main_dict=root.findall('dict')
for item in list(main_dict[0]):    
    print(item.tag)
    if item.tag=="dict":
        tracks_dict=item
        break
tracklist=list(tracks_dict.findall('dict'))


#podcast=[] #All podcast elements
purchased=[] # All purchased music
apple_music=[] # Music added to lirary through subscription:


# Arrays containing list of all songs for each genre
genre_latest=[]       
genre_InRotation=[]   
genre_OtherThanNew=[] 
genre_Old=[]          
genre_Album=[]

all_songs=[]

regex_Latest       = re.compile('latest', re.IGNORECASE)
regex_InRotation   = re.compile('In Rotation',re.IGNORECASE)

regex_OtherThanNew = re.compile('Other than new', re.IGNORECASE)

regex_Old          = re.compile('Old', re.IGNORECASE)
regex_Album        = re.compile('Album', re.IGNORECASE)

songs_dict = {}
# kkrug 6/20/22 I believe tracklist contains a list of all the <dict> tags for each indevidual tracks, so "song" equats to all tags of one song 
for song in tracklist:
#    print(song.tag)
#    print(song.attrib)
    #genre=song.findall("./key/..[@name='Singapore']")
    x=list(song)
    #print(x.tag)
    #for neighbor in x.iter('neighbor'):
    #     print(neighbor.attrib)
    for i in range(len(x)): # iterate through the key pair incrementing by 2
        all_songs.append(list(song))
        #if x[i].text=="Kind" and x[i+1].text=="MPEG audio file":
        if x[i].text=="Track ID":
            song_id="song_id_" + x[i+1].text
            songs_dict[song_id] = {}
#            songs_dict[song_id] [2] = 5
            genre_InRotation.append(list(song))
 #       else:
        if x[i].text=="Genre":
                songs_dict[song_id] ["Genre"] =  x[i+1].text
                if re.match(regex_Latest, x[i+1].text): #          
                    genre_latest.append(list(song))
                if re.match(regex_InRotation, x[i+1].text):          
                    genre_InRotation.append(list(song))
                if re.match(regex_OtherThanNew, x[i+1].text):          
                    genre_OtherThanNew.append(list(song))
                if re.match(regex_Old, x[i+1].text):          
                    genre_Old.append(list(song))
                if re.match(regex_Album, x[i+1].text):          
                    genre_Album.append(list(song))
        if x[i].text=="Name":
            songs_dict[song_id] ["Name"] =  x[i+1].text
        if x[i].text=="Artist":
            songs_dict[song_id] ["Artist"] =  x[i+1].text
        
        #if x[i].text=="Kind" and x[i+1].text=="Apple Music AAC audio file":
        #    apple_music.append(list(song))
        #if x[i].text=="Kind" and x[i+1].text=="Purchased AAC audio file":
        #    purchased.append(list(song)) 

print ("Number of Latest         tracks: ",str(len(genre_latest)))
print ("Number of In Rotation    tracks: ",str(len(genre_InRotation)))
print ("Number of Other than New tracks: ",str(len(genre_OtherThanNew)))
print ("Number of Old            tracks: ",str(len(genre_Old)))
print ("Number of Album          tracks: ",str(len(genre_Album)))
print ("Total Number of tracks ========> ",str(len(all_songs)))
print ("Total tags in the last song====> ",str(len(song)))
print ("Song Dict is: ", songs_dict)

#print ("Number of tracks Purchased: ",str(len(purchased)))
#print ("Number of Music added thought Apple Music subscription: ",str(len(apple_music)))
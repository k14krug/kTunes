#!/bin/bash
echo "Enter playlist name from list below that you want copied to the iTunes directory"
ls  ./*m3u>junk;cat junk;rm junk
read playlist
if [ -f "$playlist" ]; then
   echo "File $playlist found, will covert unix to dos then copy to iTunes lib"
else
   echo "File $playlist not found. Here's a list of likely playlist in this directory"
   ls -l "*.m3u"
   exit
fi
unix2dos $playlist
echo "copying $1.m3u to /mnt/c/users/nwkru/music/itunes/"
cp -p  $playlist /mnt/c/users/nwkru/music/itunes/
#/mnt/c/users/nwkru/music/itunes/ImportM3U.vbs
echo "# # # # # # # # # # # # # # # # # # # #"
echo "# "
echo "# Now you must go to your itunes directory and drag $playlist on top of ImportM3U.vbs to import the playlist into itunes"
echo "# "
echo "# # # # # # # # # # # # # # # # # # # # "

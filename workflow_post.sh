#!/bin/bash
echo "Enter playlist name you created and want to copy to the iTunes directory"
ls -l ./*m3u
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


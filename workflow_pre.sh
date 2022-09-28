cp -p /mnt/c/users/nwkru/music/itunes/'iTunes Music Library.xml' iTunesMusicLibrary.xml
rm iTunes.2.0.sqlite
python /home/kkrug/python/itunes_local_2.0-2/01_create_sqlite_tbls.py
python /home/kkrug/python/itunes_local_2.0-2/02_load_sqlite.py
python /home/kkrug/python/itunes_local_2.0-2/app.py
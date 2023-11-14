import sqlite3
import argparse


def validate_playlist(playlist_nm, category_list, category_repeat_intervals):
    # Connect to the kTunes.sqlite database
    conn = sqlite3.connect('kTunes.sqlite')
    cursor = conn.cursor()

    last_play_time = {}
    last_play_time_in_category = {}
    prev_track_info = None
    prev_track_info_in_category = {}
    validation_errors = 0

    track_count = 0
    
    # Get a cursor of all the tracks for the given playlist, ordered by track_cnt
    sql = '''SELECT song, artist, track_cnt, category
             FROM playlist_tracks
             WHERE playlist_nm = ?
             ORDER BY track_cnt;'''
    cursor.execute(sql, (playlist_nm,))
    track_info_row = cursor.fetchone()
    if track_info_row is None:
        print(f"Playlist {playlist_nm} not found.")
    else:
        # Validate the playlist based on the two rules
        for track_info_row in cursor:
            track_count += 1
            song, artist, track_cnt, cat = track_info_row

            # Get the category index for the current track
            cat_index = category_list.index(cat)

            # Rule 1: No two tracks from an artist in a category repeat more frequently than its category repeat interval
            last_play_time_artist_in_category = last_play_time_in_category.get((artist, cat_index))
            if last_play_time_artist_in_category is not None:
                repeat_interval = category_repeat_intervals[cat_index]
                tracks_since_last_play = track_cnt - last_play_time_artist_in_category
                if tracks_since_last_play < repeat_interval:
                    validation_errors += 1
                    print(f"Track '{song}' by '{artist}' in category '{cat}' breaks Rule 1 (category repeat interval) at track_cnt {track_cnt}. ")
                    prev_track_info_cat = prev_track_info_in_category.get((artist, cat_index))
                    if prev_track_info_cat is not None:
                        print(f"Previous track '{prev_track_info_cat[0]}' by '{prev_track_info_cat[1]}' in category '{prev_track_info_cat[3]}' at track_cnt {prev_track_info_cat[2]}")

            # Rule 2: No song from an artist is played more frequently than the repeat interval for that category
            last_play_time_artist = last_play_time.get(artist)
            if last_play_time_artist is not None:
                artist_cat_index = last_play_time_artist[1]
                repeat_interval = category_repeat_intervals[artist_cat_index]
                tracks_since_last_play = track_cnt - last_play_time_artist[0]
                if tracks_since_last_play < repeat_interval:
                    validation_errors += 1
                    print(f"Track '{song}' by '{artist}' in category '{cat}' breaks Rule 2 (artist repeat interval) at track_cnt {track_cnt}. ")
                    prev_track_info_artist = prev_track_info.get(artist)
                    if prev_track_info_artist is not None and prev_track_info_artist[3] == cat:
                        print(f"Previous track '{prev_track_info_artist[0]}' by '{prev_track_info_artist[1]}' in category '{prev_track_info_artist[3]}' at track_cnt {prev_track_info_artist[2]}")

            # Update the last play time for the artist in the category and the artist in general
            last_play_time_in_category[(artist, cat_index)] = track_cnt
            last_play_time[artist] = (track_cnt, cat_index)
            prev_track_info_in_category[(artist, cat_index)] = (song, artist, track_cnt, cat)
            prev_track_info = {artist: (song, artist, track_cnt, cat)}
 
    # Close the database connection
    conn.close()

    print("Completed validating",track_count + 1, " tracks of ", playlist_nm)
    return(validation_errors) # Return the number of validation errors

if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="Validate a playlist")

    # Add an argument for the playlist name
    parser.add_argument("playlist", help="The name of the playlist to validate")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Hard coded parameters
    category_list = ['RecentAdd', 'Latest', 'In Rot', 'Other', 'Old', 'Album']
    category_repeat_intervals = [15, 20, 30, 50, 50, 50]

    validate_playlist(args.playlist, category_list, category_repeat_intervals)
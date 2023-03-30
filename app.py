from flask import Flask, render_template, request
from flask import jsonify
import configparser
import sqlite3
from process_db import main
import load_xml

app = Flask(__name__)

# Database
DATABASE = 'kTunes.sqlite'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Define the path to the config file
config_path = "ktunes.ini"
config = configparser.ConfigParser()
config.read(config_path)
if not config.has_section("misc"):
    print("config doesn't have misc section, gonna write out a default one")
    default_config = {
        "misc": {
            "playlist_name": "",
            "playlist_lgth": "",
            "recently_added_switch": "",
            "RA_weighting_factor": "",
            "RA_play_cnt": "",
            "create_playlist": "",
            "debug_lvl": ""
        },
        "categories": {
            "cat1": 'zed',
            "cat1_pct": '33',
            "cat1_repeat": 33
        }
    }
    print("before reading default_config")
    config.read_dict(default_config)
    with open(config_path, "w") as config_file:
        config.write(config_file)
else:
    print("config has misc section:",config["misc"])
    
# Define the default configuration

# Create the configuration file if it doesn't exist
#config.read(config_path)

# Function to search for tracks by artist, song and category and paginated the result set
def search_tracks(artist, song, category, page, per_page):
    db = get_db_connection()
    
    query = "SELECT Artist, song, category, Album, play_cnt, strftime('%Y-%m-%d', last_play_dt) AS last_play_dt, strftime('%Y-%m-%d', date_added) AS date_added FROM tracks WHERE 1=1"
    if song:
        query += " AND lower(song) LIKE '%" + song.lower() +  "%'"
    if artist:
        query += " AND lower(Artist) LIKE '%" + artist.lower() + "%'"
    if category:
        query += " AND category LIKE '%" + category.lower() + "%'"
    count_query = f"SELECT count(*) FROM ({query})"
    #print("count_query=:",count_query)
    cursor = db.execute(count_query)
    count = cursor.fetchone()[0]
    offset = (page - 1) * per_page
    limit = per_page
    query += ' ORDER BY artist, song  LIMIT ?, ?'
    cursor = db.execute(query,(offset, limit))
    #query= 'SELECT * FROM tracks WHERE artist LIKE ? AND song LIKE ? AND category LIKE ? ORDER BY artist, song, category LIMIT ?, ?'
    #cursor = db.execute(query, ('%{}%'.format(artist), '%{}%'.format(song), '%{}%'.format(category), offset, limit))
    tracks = cursor.fetchall()
    #print("tracks=",tracks)
    cursor.close()
    return tracks, count

'''
@app.route('/get_max_rows')
def get_max_rows():
    row_height = 30  # Set the height of a single row in pixels
    screen_height = request.args.get('screen_height', type=int)  # Get the user's screen height from the query parameters
    if not screen_height:
        return jsonify(error='screen_height parameter is missing')
    else:
        print("screen hight=",screen_height)
    max_rows = int(screen_height / row_height)  # Calculate the maximum number of rows that can be displayed on the user's screen
    return jsonify(max_rows=max_rows)
'''

@app.route("/config", methods=["GET", "POST"])
def create_playlist():
    # Read the configuration file
    config.read(config_path)

    if request.method == "POST":    # Update the configuration file with the new values
            # Read the category percentage values from the form
        form_data = request.form
        # display each field and its value
        for field, value in form_data.items():
            print(f"{field}: {value}") 
        pcts = [
        request.form["cat1_pct"],
        request.form["cat2_pct"],
        request.form["cat3_pct"],
        request.form["cat4_pct"],
        request.form["cat5_pct"]
       ]

        # Convert the percentage values to floats and compute the total
        total_pct = sum(float(pct) for pct in pcts)

        # Check if the total is 100, and if not, display an error message
        if total_pct != 100:
            error_msg = "# # # Category percentages must add up to 100 (current total is {}). Values reset. # # #.".format(total_pct)
            return render_template("config.html", config=config, error=error_msg)

        config["misc"]["playlist_name"] = request.form["playlist_name"]
        config["misc"]["playlist_lgth"] = request.form["playlist_lgth"]
        config["misc"]["recently_added_switch"] = request.form["recently_added_switch"]
        config["misc"]["RA_weighting_factor"] = request.form["RA_weighting_factor"]
        config["misc"]["RA_play_cnt"] = request.form["RA_play_cnt"]
        config["misc"]["create_playlist"] = request.form["create_playlist"]
        config["misc"]["debug_lvl"] = request.form["debug_lvl"]

        config.set("categories", "cat1", request.form["cat1"])
        config.set("categories", "cat1_pct", request.form["cat1_pct"])
        config.set("categories", "cat1_repeat", request.form["cat1_repeat"])

        config.set("categories", "cat2", request.form["cat2"])
        config.set("categories", "cat2_pct", request.form["cat2_pct"])
        config.set("categories", "cat2_repeat", request.form["cat2_repeat"])

        config.set("categories", "cat3", request.form["cat3"])
        config.set("categories", "cat3_pct", request.form["cat3_pct"])
        config.set("categories", "cat3_repeat", request.form["cat3_repeat"])

        config.set("categories", "cat4", request.form["cat4"])
        config.set("categories", "cat4_pct", request.form["cat4_pct"])
        config.set("categories", "cat4_repeat", request.form["cat4_repeat"])

        config.set("categories", "cat5", request.form["cat5"])
        config.set("categories", "cat5_pct", request.form["cat5_pct"])
        config.set("categories", "cat5_repeat", request.form["cat5_repeat"])


        # Write the updated configuration file
        with open(config_path, "w") as config_file:
            config.write(config_file)
        config_parser_dict = {s:dict(config.items(s)) for s in config.sections()}
        total_songs, nbr_of_genre_songs, dup_playlist = main(config_parser_dict)
    # Read the configuration file
    config.read(config_path)

    # Render the template with the configuration data
    return render_template("config.html", config=config)

# Route to display the paginated table of tracks
@app.route('/tracks', methods=['GET', 'POST'])
def tracks():
    print("start /Tracks")
    screen_height = request.args.get('screen_height', type=int)
    if screen_height:
        print("got a screen_height of",screen_height)
        max_rows_response = requests.get(f"{request.url_root}get_max_rows?screen_height={screen_height}")
        if max_rows_response.status_code == 200:
            max_rows = max_rows_response.json().get('max_rows')
            per_page = max_rows
        else:
            per_page = 20
    else:
        print("didn't get a screen height")
        per_page = request.args.get('per_page', 20, type=int)
    
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    
    search_artist = request.args.get('search_artist', '')
    search_song = request.args.get('search_song', '')
    search_category = request.args.get('search_category', '')
    #if search_artist or search_song or search_category:
    tracks, count = search_tracks(search_artist, search_song, search_category, page, per_page)
    #else:
    #    tracks, count = paginate(page, per_page)
    total_pages = (count + per_page - 1) // per_page     
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)  
    print("end_page=",end_page) 
    print(render_template('tracks.html', tracks=tracks, count=count, total_pages=total_pages, page=page, per_page=per_page, start_page=start_page, end_page=end_page, search_artist=search_artist, search_song=search_song, search_category=search_category))        
    return render_template('tracks.html', tracks=tracks, count=count, total_pages=total_pages, page=page, per_page=per_page, start_page=start_page, end_page=end_page, search_artist=search_artist, search_song=search_song, search_category=search_category)


if __name__ == "__main__":
   app.run(debug=True)

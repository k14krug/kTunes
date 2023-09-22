from flask import Flask, render_template, request
from flask import jsonify
import configparser
import sqlite3
import random
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
    
# List of background images
background_images = [
    'PiecesOfEight1.jpg',
    'PiecesOfEight2.jpg',
    'PiecesOfEight3.jpg',
    'PiecesOfEight4.jpg',
    'PiecesOfEight5.jpg',
    ]
# Select a random background image from the list
selected_image = random.choice(background_images)

# Generate the URL for the selected image
background_image_url = f"/static/images/{selected_image}"


# Function to query a table with filters and paginate the result set
def query_table(**kwargs):
    db = get_db_connection()
    count_query = f"SELECT count(*) FROM ({kwargs['query']})"
    #print("count_query=",count_query)
    cursor = db.execute(count_query)
    count = cursor.fetchone()[0]
    offset = (kwargs['page'] - 1) * kwargs['per_page']
    limit = kwargs['per_page']
    order_by_str = ', '.join(kwargs['order_by_cols'])
    query = f"{kwargs['query']} ORDER BY {order_by_str}  LIMIT ?, ?"
    cursor = db.execute(query, (offset, limit))
    tracks = cursor.fetchall()
    cursor.close()
    return tracks, count

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
        if "recently_added_switch" in request.form:
          config["misc"]["recently_added_switch"] = request.form["recently_added_switch"]
        else:
          config["misc"]["recently_added_switch"] = 'no'
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

# Route to display the paginated table of playlist
@app.route('/playlist', methods=['GET', 'POST'])
def playlist():
    q_dict = {}
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
    
    q_dict['playlist'] = request.args.get('playlist', 'kTunes_03')
    q_dict['artist'] = request.args.get('artist', '')
    q_dict['song'] = request.args.get('song', '')
    q_dict['category'] = request.args.get('category', '')
    
    query = "SELECT playlist_nm, track_cnt, artist, song, category, play_cnt, strftime('%Y-%m-%d', last_play_dt) AS last_play_dt FROM playlist_tracks WHERE lower(playlist_nm) like '" + q_dict['playlist'].lower() + "%'"
    if q_dict['artist']:
        query += " AND lower(Artist) LIKE '%" + q_dict['artist'].lower() + "%'"
    if q_dict['song']:
        query += " AND lower(song) LIKE '%" + q_dict['song'].lower() +  "%'"
    if q_dict['category']:
        query += " AND category LIKE '%" + q_dict['category'].lower() + "%'"
    
    q_dict['query'] = query
    q_dict['order_by_cols'] = ['track_cnt']
    q_dict['per_page'] = per_page
    q_dict['page'] = page    
    
    tracks, count = query_table(**q_dict)
    total_pages = (count + per_page - 1) // per_page     
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)
    endpoint = 'playlist' 
    template_name= 'playlist.html'
    print('background image=',background_image_url) 
    return render_template('table_templ.html', template_name=template_name, endpoint=endpoint, tracks=tracks, count=count, total_pages=total_pages, page=page, per_page=per_page, start_page=start_page, end_page=end_page, q_dict=q_dict)#, background_image_url=background_image_url)


# Route to display the paginated table of tracks
@app.route('/tracks', methods=['GET', 'POST'])
def tracks():
    q_dict = {}
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
        print("didn't get a screen height!")
        per_page = request.args.get('per_page', 20, type=int)
    
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    
    q_dict['artist'] = request.args.get('artist', '')
    q_dict['song'] = request.args.get('song', '')
    q_dict['category'] = request.args.get('category', '')
    
    query = "SELECT Artist, song, category, Album, play_cnt, strftime('%Y-%m-%d', last_play_dt) AS last_play_dt, strftime('%Y-%m-%d', date_added) AS date_added FROM tracks WHERE 1=1"
    if q_dict['artist']:
        query += " AND lower(Artist) LIKE '%" + q_dict['artist'].lower() + "%'"
    if q_dict['song']:
        query += " AND lower(song) LIKE '%" + q_dict['song'].lower() +  "%'"
    if q_dict['category']:
        query += " AND category LIKE '%" + q_dict['category'].lower() + "%'"
    
    q_dict['query'] = query
    q_dict['order_by_cols'] = ['artist', 'song']
    q_dict['per_page'] = per_page
    q_dict['page'] = page    
    
    tracks, count = query_table(**q_dict)
    total_pages = (count + per_page - 1) // per_page     
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)  
    template_name= 'tracks.html'
    endpoint='tracks'
    print('background image=',background_image_url) 
    return render_template('table_templ.html', template_name=template_name, endpoint=endpoint, tracks=tracks, count=count, total_pages=total_pages, page=page, per_page=per_page, start_page=start_page, end_page=end_page, q_dict=q_dict, background_image_url=background_image_url)


if __name__ == "__main__":
   app.run(debug=True)

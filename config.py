from flask import Flask, render_template, request
import configparser
from process_db import main

app = Flask(__name__)

# Define the path to the config file
config_path = "ktunes.ini"
config = configparser.ConfigParser()
config.read(config_path)
if not config.has_section("misc"):
    print("config doesn't have misc section, gonna write out a default one")
    default_config = {
        "misc": {
            "playlist_name": "",
            "recently_added_switch": "",
            "weighting_factor": ""
        },
        "categories": {
            "option1_category": 'abc',
            "option1_category_pct": '33',
            "option1_category_repeat": 33
        }
    }
    print("before reading default_config")
    config.read_dict(default_config)
    print("before writing config file with default values")
    with open(config_path, "w") as config_file:
        config.write(config_file)
else:
    print("config has misc section:",config["misc"])
    
# Define the default configuration

# Create the configuration file if it doesn't exist
#config.read(config_path)


@app.route("/config", methods=["GET", "POST"])
def config_file():
    # Read the configuration file
    config.read(config_path)

    if request.method == "POST":    # Update the configuration file with the new values
            # Read the category percentage values from the form
        category_pcts = [
        request.form["option1_category_pct"],
        request.form["option2_category_pct"],
        request.form["option3_category_pct"],
        request.form["option4_category_pct"],
        request.form["option5_category_pct"]
       ]

        # Convert the percentage values to floats and compute the total
        total_pct = sum(float(pct) for pct in category_pcts)

        # Check if the total is 100, and if not, display an error message
        if total_pct != 100:
            error_msg = "# # # Category percentages must add up to 100 (current total is {}). Values reset. # # #.".format(total_pct)
            return render_template("config.html", config=config, error=error_msg)

        config["misc"]["playlist_name"] = request.form["playlist_name"]
        config["misc"]["recently_added_switch"] = request.form["recently_added_switch"]
        config["misc"]["weighting_factor"] = request.form["weighting_factor"]

        config["categories"]["option1_category"] = request.form["option1_category"]
        #config["categories"]["option1"]["category"] = request.form["option1_category"]

        #config.set("categories", "option1_category", request.form["option1_category"])
        config.set("categories", "option1_category_pct", request.form["option1_category_pct"])
        config.set("categories", "option1_category_repeat", request.form["option1_category_repeat"])

        config.set("categories", "option2_category", request.form["option2_category"])
        config.set("categories", "option2_category_pct", request.form["option2_category_pct"])
        config.set("categories", "option2_category_repeat", request.form["option2_category_repeat"])

        config.set("categories", "option3_category", request.form["option3_category"])
        config.set("categories", "option3_category_pct", request.form["option3_category_pct"])
        config.set("categories", "option3_category_repeat", request.form["option3_category_repeat"])

        config.set("categories", "option4_category", request.form["option4_category"])
        config.set("categories", "option4_category_pct", request.form["option4_category_pct"])
        config.set("categories", "option4_category_repeat", request.form["option4_category_repeat"])

        config.set("categories", "option5_category", request.form["option5_category"])
        config.set("categories", "option5_category_pct", request.form["option5_category_pct"])
        config.set("categories", "option5_category_repeat", request.form["option5_category_repeat"])


        # Write the updated configuration file
        with open(config_path, "w") as config_file:
            print("writing config")
            config.write(config_file)
       
        total_songs, nbr_of_genre_songs, dup_playlist = main(config)
    # Read the configuration file
    config.read(config_path)

    # Render the template with the configuration data
    return render_template("config.html", config=config)

if __name__ == "__main__":
   app.run(debug=True)

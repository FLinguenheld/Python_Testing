import json
from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   flash,
                   url_for,
                   get_flashed_messages)


MAXIMUM_POINTS_PER_COMP = 12


def load_json(file_name):
    """ Open the file database/file_name.json, extract and return a list of dicts
        This list is itself in a dict, inside the field {file_name} """
    with open(f'database/{file_name}.json') as file:
        return json.load(file)[file_name]


def save_json(file_name, data):
    """ Open/create the file database/file_name.json with the list of dicts 'data'
        This list will be saved in a dict, in the field {file_name} """
    with open(f'database/{file_name}.json', 'w') as file:
        json.dump({file_name: data}, file)


def update_json(file_name, data):
    """ Update an entry in the '/database/file_name.json
        If the file already contains an entry with the field 'name', the latter will be erase.
        Otherwise, it just adds 'data' and save the file. """
    tab = load_json(file_name)
    for entry in tab:
        if entry['name'] == data['name']:
            tab.remove(entry)
            break

    tab.insert(0, data)
    save_json(file_name, tab)


def maximum_points_allowed(competition, club):
    """ Return the maximum avaliable places for this club and this competition """

    nb_authorised_places = MAXIMUM_POINTS_PER_COMP
    if club['id'] in competition:
        nb_authorised_places -= int(competition[club['id']])

    return min(int(competition['numberOfPlaces']), int(club['points']), nb_authorised_places)


def create_app(config):

    app = Flask(__name__)
    app.secret_key = 'something_special'
    app.jinja_env.globals['maximum_points_allowed'] = maximum_points_allowed

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/showSummary', methods=['POST'])
    def showSummary():
        club = [club for club in load_json('clubs') if club['email'] == request.form['email']][0]
        return render_template('welcome.html', club=club, competitions=load_json('competitions'))

    @app.route('/book/<competition>/<club>')
    def book(competition, club):
        foundClub = [c for c in load_json('clubs') if c['name'] == club][0]
        foundCompetition = [c for c in load_json('competitions') if c['name'] == competition][0]

        maximum = maximum_points_allowed(foundCompetition, foundClub)
        if maximum == 0:
            flash("You cannot book a new place", "flash_warning")

        if foundClub and foundCompetition:

            return render_template('booking.html',
                                   club=foundClub,
                                   competition=foundCompetition,
                                   maximum_allowed=maximum)
        else:
            flash("Something went wrong-please try again", 'flash_error')
            return render_template('welcome.html', club=club, competitions=load_json('competitions'))

    @app.route('/purchasePlaces', methods=['POST'])
    def purchasePlaces():
        competition = [c for c in load_json('competitions') if c['name'] == request.form['competition']][0]
        club = [c for c in load_json('clubs') if c['name'] == request.form['club']][0]

        try:
            placesRequired = int(request.form['places'])

            if placesRequired <= 0:
                raise ValueError

            elif placesRequired <= int(maximum_points_allowed(competition, club)):

                # Remove used points from club and competition
                competition['numberOfPlaces'] = int(competition['numberOfPlaces']) - placesRequired
                club['points'] = int(club['points']) - placesRequired

                # Also save the club id and its number of places to respect the limitation (MAXIMUM_POINTS_PER_COMP)
                if club['id'] in competition:
                    competition[club['id']] = int(competition[club['id']]) + placesRequired
                else:
                    competition[club['id']] = placesRequired

                # Save
                update_json('competitions', competition)
                update_json('clubs', club)

                flash('Great-booking complete!', 'flash_info')
                return render_template('welcome.html', club=club, competitions=load_json('competitions'))

            else:
                flash(f"You are allowed to book {maximum_points_allowed(competition, club)} places maximum",
                      'flash_warning')

        except ValueError:
            flash('Invalid value', 'flash_error')

        return render_template('welcome.html', club=club, competitions=load_json('competitions'))

    # TODO: Add route for points display

    @app.route('/logout')
    def logout():
        return redirect(url_for('index'))

    return app


# app = create_app({"TESTING": False})
app = create_app({"TESTING": True})


if __name__ == "__main__":
    app.run()

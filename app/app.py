import sqlite3
import requests
import time
from flask import Flask, render_template

# Configure application
app = Flask(__name__)


@app.route("/")
def index():
    qb_stats = load_stats('qb_stats')
    return render_template('qb.html', qb_stats_div1=qb_stats[0], qb_stats_div2=qb_stats[1])


@app.route("/wr")
def wr():
    wr_stats = load_stats('wr_stats')
    return render_template('wr.html', wr_stats_div1=wr_stats[0], wr_stats_div2=wr_stats[1])


@app.route("/rb")
def rb():
    rb_stats = load_stats('rb_stats')
    return render_template('rb.html', rb_stats_div1=rb_stats[0], rb_stats_div2=rb_stats[1])


@app.route("/db")
def db():
    db_stats = load_stats('db_stats')
    return render_template('db.html', db_stats_div1=db_stats[0], db_stats_div2=db_stats[1])


@app.route("/def")
def defender():
    def_stats = load_stats('defender_stats')
    return render_template('defender.html', def_stats_div1=def_stats[0], def_stats_div2=def_stats[1])


@app.route("/kicker")
def kicker():
    kicker_stats = load_stats('kicker_stats')
    return render_template('kicker.html', kicker_stats_div1=kicker_stats[0], kicker_stats_div2=kicker_stats[1])


@app.route('/stats/<username>')
def player_stats(username):
    d1_stats, d2_stats = load_player_stats(username)
    d1_game_stats, d2_game_stats = load_game_stats(username)
    d1_games_played, d2_games_played = load_games_played(username)
    has_played = (d1_games_played + d2_games_played) > 0
    player_avatar = get_player_avatar(username)
    print(f"Avatar for {username} successfully loaded.")
    return render_template(
        'player_profile.html',
        username=username,
        d1_stats=d1_stats,
        d2_stats=d2_stats,
        d1_game_stats=d1_game_stats,
        d2_game_stats=d2_game_stats,
        d1_games_played=d1_games_played,
        d2_games_played=d2_games_played,
        has_played=has_played,
        player_avatar=player_avatar
    )


# ─── helpers ────────────────────────────────────────────────────────────────

def _fetch_dict(cursor, table, where='', params=()):
    """Run a SELECT on *table*, return a list of row-dicts."""
    sql = f"SELECT * FROM {table}"
    if where:
        sql += f" WHERE {where}"
    cursor.execute(sql, params)
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _empty_row(cursor, table):
    """Return a zeroed-out dict with the same columns as *table*."""
    cursor.execute(f"SELECT * FROM {table} LIMIT 0")
    cols = [d[0] for d in cursor.description]
    return {col: 0 for col in cols}


def load_stats(category):
    sort_map = {
        'qb_stats':       'yards',
        'rb_stats':       'yards',
        'wr_stats':       'yards',
        'db_stats':       'interceptions',
        'defender_stats': 'tackles',
        'kicker_stats':   'attempts',
    }
    sort_by = sort_map.get(category, 'rowid')

    results = []
    for db_path in ('databases/s24_d1.db', 'databases/s24_d2.db'):
        with sqlite3.connect(db_path) as con:
            cur = con.cursor()
            rows = _fetch_dict(cur, category,
                               where=f'active = 1 ORDER BY {sort_by} DESC')
            results.append(rows)
    return results          # [d1_list, d2_list]


def load_player_stats(username):
    """
    Returns (d1_stats, d2_stats).
    Each is a dict keyed by position shortname ('qb','wr','rb','db','defender','kicker').
    Value is a single flat row-dict (not a list).
    """
    categories = ['qb', 'wr', 'rb', 'db', 'defender', 'kicker']

    def fetch_for_db(db_path):
        stats = {}
        with sqlite3.connect(db_path) as con:
            cur = con.cursor()
            for cat in categories:
                table = f'{cat}_stats'
                rows = _fetch_dict(cur, table, where='username = ?', params=(username,))
                stats[cat] = rows[0] if rows else _empty_row(cur, table)
        return stats

    return fetch_for_db('databases/s24_d1.db'), fetch_for_db('databases/s24_d2.db')


def load_game_stats(username):
    """
    Returns (d1_game_stats, d2_game_stats).
    Each is: { game_hash: { 'qb': row_dict, 'wr': row_dict, … } }
    Values are flat dicts (not lists).
    """
    categories = ['qb', 'wr', 'rb', 'db', 'defender', 'kicker']

    def fetch_for_logs(db_path):
        game_stats = {}
        with sqlite3.connect(db_path) as con:
            cur = con.cursor()
            cur.execute("SELECT game_hash FROM qb_stats WHERE username = ?", (username,))
            hashes = [r[0] for r in cur.fetchall()]
            for gh in hashes:
                game_stats[gh] = {}
                for cat in categories:
                    table = f'{cat}_stats'
                    rows = _fetch_dict(cur, table,
                                       where='username = ? AND game_hash = ?',
                                       params=(username, gh))
                    game_stats[gh][cat] = rows[0] if rows else _empty_row(cur, table)
        return game_stats

    return fetch_for_logs('databases/s24_d1_logs.db'), fetch_for_logs('databases/s24_d2_logs.db')


def load_games_played(username):
    """
    Returns (d1_games_played, d2_games_played) by counting logged games
    for the username in the hashed game logs DBs.
    """
    def count_for_logs(db_path):
        with sqlite3.connect(db_path) as con:
            cur = con.cursor()
            # Each logged game produces one qb_stats row per player, keyed by game_hash.
            cur.execute(
                "SELECT COUNT(*) FROM qb_stats WHERE username = ?",
                (username,),
            )
            row = cur.fetchone()
            return row[0] if row and row[0] is not None else 0

    return count_for_logs('databases/s24_d1_logs.db'), count_for_logs('databases/s24_d2_logs.db')

def get_player_avatar(username, max_retries=5):
    # Get user ID
    user_api = "https://users.roblox.com/v1/usernames/users"
    try:
        user_res = requests.post(user_api, json={"usernames": [username], "excludeBannedUsers": True})
        user_data = user_res.json().get('data')
        if not user_data:
            print(f"User data for {username} returned null.")
            return None
        user_id = user_data[0]['id']
    except:
        print(f"Request for user data failed. ({username})")
        return None

    thumb_url = (
        f"https://thumbnails.roblox.com/v1/users/avatar-headshot?"
        f"userIds={user_id}&size=420x420&format=Png&isCircular=false"
    )

    for attempt in range(max_retries):
        try:
            res = requests.get(thumb_url)
            if res.status_code == 200:
                data = res.json()["data"][0]

                # ✅ CRITICAL FIX
                if data["state"] == "Completed" and data["imageUrl"]:
                    # ✅ cache buster for Discord
                    return data["imageUrl"] + f"?cb={int(time.time())}"

        except:
            pass

        time.sleep(0.5 * (attempt + 1))  # shorter + smoother backoff

    return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


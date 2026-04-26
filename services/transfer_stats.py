from services.errors import InvalidDivisionError, ArgumentError
import sqlite3
import os

def transfer(old_acc: str, new_acc: str, division: str):
    if division.lower() not in ['d1', 'd2']:
        raise InvalidDivisionError('')
    
    else:
        # 1. Get the directory of THIS file (afg_bot/utility)
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 2. Go up one level to reach the 'afg_bot' folder
        # This is now your BASE PATH hardcoded to the project root
        BASE_PATH = os.path.abspath(os.path.join(current_dir, ".."))

        # 3. Define your sub-folders relative to the BASE_PATH
        DB_FOLDER = os.path.join(BASE_PATH, "app", "databases")

        division = division.lower()

        with sqlite3.connect(os.path.join(DB_FOLDER, f's24_{division}.db')) as connection:
            cursor = connection.cursor()
            
            cursor.execute("SELECT * FROM qb_stats WHERE username = ? ", (old_acc,))
            if cursor.fetchone() is None:
                raise ArgumentError(f"The old account you supplied is not present in the {division.upper()} statsheet.")
            
            cursor.execute("SELECT * FROM qb_stats WHERE username = ? ", (new_acc,))
            if cursor.fetchone() is None:
                raise ArgumentError(f"The new account you supplied is not present in the {division.upper()} statsheet.")
            
            # Dictionary to make the code cleaner i guess
            stat_rows = {
                'qb_stats': ['throws', 'completions', 'incompletions', 'touchdowns', 'interceptions', 'sacks_taken', 'yards'],
                'wr_stats': ['yards', 'targets', 'ints_allowed', 'catches', 'touchdowns', 'yards_after_catch'],
                'db_stats': ['interceptions', 'targets', 'swats', 'touchdowns', 'catches_allowed', 'yards_allowed', 'tds_allowed'],
                'rb_stats': ['attempts', 'yards', 'touchdowns'],
                'defender_stats': ['tackles', 'sacks', 'safeties'],
                'kicker_stats': ['attempts', 'kicks_made', 'kicks_missed']
            }

            for category, columns in stat_rows.items():
                try:
                    for stat in columns:
                        cursor.execute(f'UPDATE {category} SET {stat} = {stat} + (SELECT {stat} FROM {category} WHERE username = ?) WHERE username = ?', (old_acc, new_acc))

                    else:
                        cursor.execute(f'UPDATE {category} SET active = 0 WHERE username = ?', (old_acc,))
                except Exception as e:
                    raise e
                
            connection.commit()
            print(f"Stats transferred from {old_acc} to {new_acc}.")
            return 0
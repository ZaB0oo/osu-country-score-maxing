import os
import time
from dotenv import load_dotenv
import ossapi
from csv import DictReader

PERCENTAGE_LIMIT = 15
PROGRESS_FILE = "french_missing_score_progress.txt"
BEATMAPS_FILE = "french_missing_score.txt"

def main():

    load_dotenv()

    try:
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError("CLIENT_ID ou CLIENT_SECRET manquant dans le fichier .env.")

        api = ossapi.Ossapi(client_id, client_secret)
    except Exception as e:
        print(f"Erreur lors de la connexion à l'API : {e}")
        return

    total_diff_of_mapset_filtered, total_diff_filtered, total_added, total_difference = 0, 0, 0, 0
    try:
        if os.path.exists(BEATMAPS_FILE):
            os.remove(BEATMAPS_FILE)
        with open(BEATMAPS_FILE, "a") as f:
            f.write("Beatmap ID;Title + diffname;Date Ranked;Stars;BPM;AR;OD;CS;HP;Length;Missing score\n")
    except Exception as e:
        print(f"Erreur lors de la manipulation du fichier : {e}")
        return
    
    start_index = loadProgress()
    beatmaps = loadData()

    for beatmap in beatmaps:
        total_diff_of_mapset_filtered += 1
        try:
            if beatmap["stars"] < 8 and beatmap["circles"] + beatmap["sliders"] + beatmap["spinners"] > 400:
                total_diff_filtered += 1
                try:
                    time.sleep(1)
                    scores = api.beatmap_scores(beatmap["beatmap_id"], mode="osu", limit=100)
                except Exception as e:
                    print(f"Erreur lors de la récupération des scores de la beatmap {beatmap['beatmap_id']} : {e}")
                    continue

                if not scores.scores:
                    continue

                best_global_score = scores.scores[0]
                if best_global_score._user.country_code == "FR":
                    continue

                french_scores = [score for score in scores.scores if score._user.country_code == "FR"]

                if not french_scores:
                    try:
                        valid, difference = compare_scores(best_global_score.classic_total_score, scores.scores[-1].classic_total_score, PERCENTAGE_LIMIT)
                        if valid:
                            total_added += 1
                            total_difference += difference
                            add_beatmap(beatmap, difference, total_added)
                    except Exception as e:
                        print(f"Erreur lors de la comparaison des scores de la beatmap {beatmap['beatmap_id']} : {e}")
                    continue

                best_french_score = max(french_scores, key=lambda x: x.classic_total_score)
                try:
                    valid, difference = compare_scores(best_global_score.classic_total_score, best_french_score.classic_total_score, PERCENTAGE_LIMIT)
                    if valid:
                        total_added += 1
                        total_difference += difference
                        add_beatmap(beatmap, difference, total_added)
                except Exception as e:
                    print(f"Erreur lors de la comparaison des scores de la beatmap {beatmap['beatmap_id']} : {e}")
        except Exception as e:
            print(f"Erreur lors de l'analyse de la beatmap {beatmap['beatmap_id']} : {e}")

    os.remove(PROGRESS_FILE)
    try:
        with open(f"results.txt", "a") as f:
            f.write(f"Total des beatmaps analysées : {total_diff_of_mapset_filtered}\n")
            f.write(f"Total des beatmaps comparées : {total_diff_filtered}\n")
            f.write(f"Total des beatmaps récupérées : {total_added}\n")
            f.write(f"Total de score manquant : {'{:,}'.format(total_difference)}\n")
    except Exception as e:
        print(f"Erreur lors de l'écriture du fichier récapitulatif : {e}")

def loadProgress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            lines = f.readlines()
            start_index = int(lines[0].strip())
            return start_index
    return 0

def loadData(file_path="beatmaps.csv"):
    beatmaps = []
    with open(file_path, encoding="utf-8") as file:
        reader = DictReader(file)
        for row in reader:
            beatmaps.append({
                'beatmap_id': int(row['beatmap_id']),
                'title': row['title'],
                'diffname': row['diffname'],
                'stars': float(row['stars']),
                'ranked_date': row['approved_date'],
                'bpm': row['bpm'],
                'ar': float(row['ar']),
                'od': float(row['od']),
                'cs': float(row['cs']),
                'hp': float(row['hp']),
                'length': row['length'],
                'circles': int(row['circles']),
                'sliders': int(row['sliders']),
                'spinners': int(row['spinners']),
            })
    return beatmaps

def compare_scores(global_score, other_score, limit):
    try:
        difference = global_score - other_score
        percentage_difference = (difference / global_score) * 100
        valid = percentage_difference > limit or difference > 2000000
        return valid, difference
    except ZeroDivisionError:
        print("Erreur : Division par zéro lors du calcul du pourcentage.")
        return False, 0
    except Exception as e:
        print(f"Erreur inattendue lors de la comparaison des scores : {e}")
        return False, 0

def add_beatmap(beatmap, difference, total_added):
    try:
        with open(f"beatmaps.txt", "a") as f:
            f.write(f"{beatmap['beatmap_id']};{beatmap['title']} {beatmap['diffname']};{beatmap['ranked_date']};{beatmap['stars']}*;{beatmap['bpm']} BPM;{beatmap['ar']};{beatmap['od']};{beatmap['cs']};{beatmap['hp']};{beatmap['length']};{'{:,}'.format(difference)}\n")
        print(f"Beatmap n°{total_added} ajoutée : {beatmap['title']} - {beatmap['beatmap_id']}")
    except Exception as e:
        print(f"Erreur lors de l'écriture de la beatmap {beatmap['beatmap_id']} dans le fichier : {e}")

if __name__ == "__main__":
    main()
import os
import time
from dotenv import load_dotenv
import ossapi
from csv import DictReader

PERCENTAGE_LIMIT = 15
QUERY = "star>3 star<8 length>100 ranked<2025"

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
        if os.path.exists(f"beatmaps.txt"):
            os.remove(f"beatmaps.txt")
        with open(f"beatmaps.txt", "a") as f:
            f.write("Beatmap ID;Title + diffname;Date Ranked;Stars;BPM;AR;OD;CS;HP;Length;Missing score\n")
    except Exception as e:
        print(f"Erreur lors de la manipulation du fichier : {e}")
        return
    
    beatmaps = loadData()

    for beatmap in beatmaps:
        total_diff_of_mapset_filtered += 1
        try:
            if beatmap["stars"] < 8 and beatmap["circles"] + beatmap["sliders"] + beatmap["spinners"] > 400:
                total_diff_filtered += 1
                try:
                    time.sleep(1)
                    scores = api.beatmap_scores(beatmap["id"], mode="osu", limit=100)
                except Exception as e:
                    print(f"Erreur lors de la récupération des scores de la beatmap {beatmap["id"]} : {e}")
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
                        print(f"Erreur lors de la comparaison des scores de la beatmap {beatmap["id"]} : {e}")
                    continue

                best_french_score = max(french_scores, key=lambda x: x.classic_total_score)
                try:
                    valid, difference = compare_scores(best_global_score.classic_total_score, best_french_score.classic_total_score, PERCENTAGE_LIMIT)
                    if valid:
                        total_added += 1
                        total_difference += difference
                        add_beatmap(beatmap, difference, total_added)
                except Exception as e:
                    print(f"Erreur lors de la comparaison des scores de la beatmap {beatmap["id"]} : {e}")
        except Exception as e:
            print(f"Erreur lors de l'analyse de la beatmap {beatmap["id"]} : {e}")

    try:
        with open(f"results.txt", "a") as f:
            f.write(f"Total des beatmaps analysées : {total_diff_of_mapset_filtered}\n")
            f.write(f"Total des beatmaps comparées : {total_diff_filtered}\n")
            f.write(f"Total des beatmaps récupérées : {total_added}\n")
            f.write(f"Total de score manquant : {'{:,}'.format(total_difference)}\n")
    except Exception as e:
        print(f"Erreur lors de l'écriture du fichier récapitulatif : {e}")

def loadData(file_path="b5kctx.csv"): # Mettre à jour le fichier régulièrement pour avoir les dernières beatmaps
    beatmaps = []
    with open(file_path, encoding="utf-8") as file:
        reader = DictReader(file)
        for row in reader:
            beatmaps.append({
                "id": int(row["beatmap_id"]),
                "title": row["title"],
                "diffname": row["diffname"],
                "stars": float(row["stars"]),
                "ranked_date": row["approved_date"],
                "bpm": float(row["bpm"]),
                "ar": float(row["ar"]),
                "od": float(row["od"]),
                "cs": float(row["cs"]),
                "hp": float(row["hp"]),
                "length": int(row["length"]),
                "circles": int(row["count_circles"]),
                "sliders": int(row["count_sliders"]),
                "spinners": int(row["count_spinners"]),
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
            f.write(f"{beatmap["id"]};{beatmap["ranked_date"].strftime("%Y-%m-%d")};{beatmap["stars"]}*;{beatmap["bpm"]} BPM;{beatmap["ar"]};{beatmap["od"]};{beatmap["cs"]};{beatmap["hp"]};{beatmap["length"]};{'{:,}'.format(difference)}\n")
        print(f"Beatmap n°{total_added} ajoutée : {beatmap["title"]} - {beatmap["id"]}")
    except Exception as e:
        print(f"Erreur lors de l'écriture de la beatmap {beatmap["id"]} dans le fichier : {e}")

if __name__ == "__main__":
    main()
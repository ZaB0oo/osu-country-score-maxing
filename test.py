import os
import time
import datetime
from dotenv import load_dotenv
import ossapi

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

    total = 0
    total_filtered = 0
    total_added = 0
    total_difference = 0
    try:
        if os.path.exists(f"beatmaps.txt"):
            os.remove(f"beatmaps.txt")
        with open(f"beatmaps.txt", "a") as f:
            f.write("Beatmap Link;Beatmap ID;Date Ranked;Star Rating;BPM;AR;OD;CS;HP;Score manquant\n")
    except Exception as e:
        print(f"Erreur lors de la manipulation du fichier : {e}")
        return
    
    cursor = None
    while True:
        try:
            time.sleep(1)
            beatmapsets = api.search_beatmapsets(
                query=QUERY,
                mode=0,
                category="leaderboard",
                cursor=cursor
            )
        except Exception as e:
            print(f"Erreur lors de la récupération des beatmapsets à la page {cursor} : {e}")
            break

        for beatmapset in beatmapsets.beatmapsets:
            for beatmap in beatmapset.beatmaps:
                total += 1
                try:
                    if beatmap.mode_int == 0 and beatmap.difficulty_rating < 8 and beatmap.count_circles + beatmap.count_sliders + beatmap.count_spinners > 400:
                        total_filtered += 1
                        try:
                            time.sleep(1)
                            scores = api.beatmap_scores(beatmap.id, mode="osu", limit=100)
                        except Exception as e:
                            print(f"Erreur lors de la récupération des scores de la beatmap {beatmap.id} : {e}")
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
                                    add_beatmap(beatmapset, beatmap, difference, total_added)
                            except Exception as e:
                                print(f"Erreur lors de la comparaison des scores de la beatmap {beatmap.id} : {e}")
                            continue

                        best_french_score = max(french_scores, key=lambda x: x.classic_total_score)
                        try:
                            valid, difference = compare_scores(best_global_score.classic_total_score, best_french_score.classic_total_score, PERCENTAGE_LIMIT)
                            if valid:
                                total_added += 1
                                total_difference += difference
                                add_beatmap(beatmapset, beatmap, difference, total_added)
                        except Exception as e:
                            print(f"Erreur lors de la comparaison des scores de la beatmap {beatmap.id} : {e}")
                except Exception as e:
                    print(f"Erreur lors de l'analyse de la beatmap {beatmap.id} : {e}")

        # Page suivante
        cursor = beatmapsets.cursor
        if not cursor:
            print(f"Fin des résultats disponibles (curseur vide).")
            break

    print(f"Total des beatmaps analysées {total}")
    print(f"Total des beatmaps comparées {total_filtered}")
    print(f"Total des beatmaps récupérées {total_added}")
    print(f"Total de score manquant {total_difference}")

    now = datetime.datetime.now()
    try:
        with open(f"results {now.strftime('%Y-%m-%d')}.txt", "a") as f:
            f.write(f"Total des beatmaps analysées : {total}\n")
            f.write(f"Total des beatmaps comparées : {total_filtered}\n")
            f.write(f"Total des beatmaps récupérées : {total_added}\n")
            f.write(f"Total de score manquant : {total_difference}\n")
    except Exception as e:
        print(f"Erreur lors de l'écriture du fichier récapitulatif : {e}")

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

def add_beatmap(beatmapset, beatmap, difference, total_added):
    try:
        with open(f"beatmaps.txt", "a") as f:
            f.write(f"{beatmap.url};{beatmap.id};{beatmapset.ranked_date.strftime('%Y-%m-%d')};{beatmap.difficulty_rating}*;{beatmap.bpm} BPM;{beatmap.ar};{beatmap.accuracy};{beatmap.cs};{beatmap.drain};{'{:,}'.format(difference)}\n")
        print(f"Beatmap n°{total_added} : {beatmapset.title} - {beatmap.id}")
    except Exception as e:
        print(f"Erreur lors de l'écriture de la beatmap {beatmap.id} dans le fichier : {e}")

if __name__ == "__main__":
    main()
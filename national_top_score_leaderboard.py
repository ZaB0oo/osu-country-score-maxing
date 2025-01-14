import os
import time
from dotenv import load_dotenv
import ossapi
from csv import DictReader

COUNTRIES = {
    "US": "United States",
    "PL": "Poland",
    "DE": "Germany",
    "RU": "Russia",
    "FR": "France",
    "UK": "United Kingdom",
    "CA": "Canada",
    "JP": "Japan",
    "KR": "South Korea",
    "TW": "Taiwan",
}

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

    file_path = "national_top_score_leaderboard.txt"
    if os.path.exists(f"{file_path}"):
        os.remove(f"{file_path}")

    total = 0
    scores_by_country = {code: 0 for code in COUNTRIES.keys()}
    beatmaps = loadData()

    for beatmap in beatmaps:
        total += 1
        try:
            time.sleep(1)
            scores = api.beatmap_scores(beatmap['beatmap_id'], mode="osu", limit=100)
        except Exception as e:
            print(f"Erreur lors de la récupération des scores de la beatmap {beatmap['beatmap_id']} : {e}")
            continue

        if not scores.scores:
            continue

        countries_checked = set()
        for score in scores.scores:
            country = score._user.country.code
            if country in COUNTRIES and country not in countries_checked:
                scores_by_country[country] += score.classic_total_score
                countries_checked.add(country)

        # Ajout du dernier score de la liste si un pays n'est pas représenté
        for country in COUNTRIES:
            if country not in countries_checked and scores.scores:
                scores_by_country[country] += scores.scores[-1].classic_total_score
        
        # Mise à jour du fichier à chaque beatmap
        last_beatmap_added = f"Beatmap n°{total} : {beatmap['beatmap_id']} - {beatmap['title']} ({beatmap['diffname']}) - {beatmap['approved_date']}"
        save_scores_to_file(scores_by_country, last_beatmap_added, file_path)

    for code, total_score in scores_by_country.items():
        print(f"Total des scores pour {COUNTRIES[code]} ({code}) : {'{:,}'.format(total_score)}")

def loadData():
    beatmaps = []
    with open("b5kctx_v2.csv", encoding="utf-8") as file: # 2025/01/13 21:50:00
        reader = DictReader(file)
        for row in reader:
            beatmaps.append({
                "beatmap_id": row["beatmap_id"],
                "approved_date": row["approved_date"],
                "title": row["title"],
                "diffname": row["diffname"],
            })
    return beatmaps

def save_scores_to_file(scores_by_country, last_beatmap_added, file_path):
    try:
        with open(file_path, "w") as f:
            for code, total_score in scores_by_country.items():
                f.write(f"{code};{COUNTRIES[code]};{'{:,}'.format(total_score)};\n")
            f.write(f"\nDernière beatmap ajoutée : {last_beatmap_added}")
    except Exception as e:
        print(f"Erreur lors de la mise à jour du fichier : {e}")

if __name__ == "__main__":
    main()

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

PROGRESS_FILE = "national_top_score_progress.txt"
SCORES_FILE = "national_top_score_leaderboard.txt"

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

    start_index, scores_by_country = loadProgress()

    total = start_index
    beatmaps = loadData()

    for i, beatmap in enumerate(beatmaps[start_index:], start=start_index + 1):
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

        last_beatmap_added = f"Beatmap n°{i} : {beatmap['beatmap_id']} - {beatmap['title']} ({beatmap['diffname']}) - {beatmap['approved_date']}"
        save_scores_to_file(scores_by_country, last_beatmap_added, SCORES_FILE)
        save_progress(i, scores_by_country)

    os.remove(PROGRESS_FILE)
    try:
        with open(SCORES_FILE, "a") as f:
            for code, total_score in sorted(scores_by_country.items(), key=lambda item: item[1], reverse=True):
                f.write(f"\n{code};{COUNTRIES[code]};{'{:,}'.format(total_score)};")
    except Exception as e:
        print(f"Erreur lors de la mise à jour du fichier : {e}")

def loadData(file_path="beatmaps.csv"):
    beatmaps = []
    with open(file_path, encoding="utf-8") as file:
        reader = DictReader(file)
        for row in reader:
            beatmaps.append({
                "beatmap_id": row["beatmap_id"],
                "approved_date": row["approved_date"],
                "title": row["title"],
                "diffname": row["diffname"],
            })
    return beatmaps


def loadProgress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            lines = f.readlines()
            start_index = int(lines[0].strip())
            scores_by_country = eval(lines[1])
            return start_index, scores_by_country
    else:
        return 0, {code: 0 for code in COUNTRIES.keys()}


def save_progress(index, scores_by_country):
    try:
        with open(PROGRESS_FILE, "w") as f:
            f.write(f"{index}\n")
            f.write(f"{scores_by_country}\n")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la progression : {e}")


def save_scores_to_file(scores_by_country, last_beatmap_added, file_path):
    try:
        with open(file_path, "w") as f:
            for code, total_score in scores_by_country.items():
                f.write(f"{code};{COUNTRIES[code]};{'{:,}'.format(total_score)};\n")
            f.write(f"\n{last_beatmap_added}")
    except Exception as e:
        print(f"Erreur lors de la mise à jour du fichier : {e}")

if __name__ == "__main__":
    main()

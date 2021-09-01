import json
import re

import requests


class Scraper:
    def __init__(self, champion_name_id: str) -> None:
        self.champion = champion_name_id

    def get_wiki_text(self) -> str:
        return requests.get(
            f"https://leagueoflegends.fandom.com/wiki/{self.champion.replace(' ', '_')}/LoL/Audio?action=raw"
        ).text

    def get_all_quotes(self) -> list[str]:
        text = self.get_wiki_text()
        regex = r"{{sm2\|[^|]+\|''\"(.*)\"''"
        matches = []

        for match in re.finditer(regex, text, re.MULTILINE):
            if ".ogg" not in match.group(1):
                matches.append(match.group(1))

        return matches


if __name__ == "__main__":
    result = {}

    with open("name_id_dict.json", "r") as f:
        champion_json = json.load(f)["data"]

    for idx, champion in enumerate(champion_json.values()):
        print(f"{champion['name']} ({idx+1}/{len(champion_json)})")
        name_to_use = (
            champion["name_id"] if "&" in champion["name"] else champion["name"]
        )
        quotes = Scraper(name_to_use).get_all_quotes()
        result[champion["name"]] = {"quotes": quotes, "icon": champion["icon"]}

    with open("quotes_list_export.json", "w") as f:
        json.dump(result, f)
        f.truncate()

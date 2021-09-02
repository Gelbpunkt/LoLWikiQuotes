import json
import re

import requests


class Scraper:
    def __init__(self, champion_name_id: str) -> None:
        self.champion = champion_name_id

    @property
    def url(self) -> str:
        return f"https://leagueoflegends.fandom.com/wiki/{self.champion.replace(' ', '_')}/LoL/Audio?action=raw"

    def get_wiki_text(self) -> str:
        return requests.get(self.url).text

    def get_all_quotes(self) -> list[str]:
        text = self.get_wiki_text()
        #regex = r"({{sm2\|[^|]+\|''\"(.*)\"'')|({{sm2\|[^|]+}} ''\"(.*)\"'')"
        regex = r"''\"(.*)\"''"
        matches = []

        for match in re.finditer(regex, text, re.MULTILINE):
            for match in reversed(match.groups()):
                if match is not None and ".ogg" not in match and match != "GG!":
                    matches.append(match)
                    break

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
        scraper = Scraper(name_to_use)
        quotes = scraper.get_all_quotes()
        result[champion["name"]] = {"quotes": quotes, "icon": champion["icon"]}

        if not quotes:
            print(f"WARNING: No quotes found for {champion['name']} with {scraper.url}")

    with open("quotes_list_export.json", "w") as f:
        json.dump(result, f, indent=4)
        f.truncate()

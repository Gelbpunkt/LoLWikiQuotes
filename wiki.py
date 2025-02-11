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
        small_bold_caps_regex = r"{{sbc\|([^}]+)}}"
        text = re.sub(
            small_bold_caps_regex,
            lambda match: f"**{match.group(1).upper()}**",
            text,
            re.MULTILINE,
        )
        champion_inline_regex = (
            r"{{ci\|(?P<champion>[^}|]+)(?:\|(?P<custom_name>[^}]+))?}}"
        )
        text = re.sub(
            champion_inline_regex,
            lambda match: match.group("custom_name") or match.group("champion"),
            text,
        )
        link_regex = r"\[\[(?!(File:))(?P<page>[^]|]+)(?:\|(?P<link_text>[^]]+))?]]"
        text = re.sub(
            link_regex,
            lambda match: match.group("link_text") or match.group("page"),
            text,
        )
        image_regex = r" ?\[\[File:[^[]+]] ?"
        text = re.sub(image_regex, " ", text)
        ability_regex = r"{{ai\|(?P<ability>[^}|]+)(?:\|(?P<champion>[^}|]+))?(?:\|(?P<display_name>[^}]+))?}}"
        text = re.sub(
            ability_regex,
            lambda match: match.group("display_name") or match.group("ability"),
            text,
        )
        rp_regex = r"{{RP([^}]*)}}"
        text = re.sub(rp_regex, "RP", text)
        summoner_spell_regex = r"{{si\|([^}]+)}}"
        text = re.sub(summoner_spell_regex, lambda match: match.group(1), text)
        ccib_regex = r"{{[cC]cib?\|(?P<file>[^}|]+)\|(?P<link>[^}|]+)(?:\|(?P<display_name>[^}|]+))?}}"
        text = re.sub(
            ccib_regex,
            lambda match: match.group("display_name") or match.group("link"),
            text,
        )
        as_regex = r"{{[Aa]s\|([^}|]+)}}"
        text = re.sub(as_regex, lambda match: match.group(1), text)
        sti_regex = r"{{sti\|(?P<attribute>[^}|]+)(?:\|(?P<display_name>[^}|]+))?}}"
        text = re.sub(
            sti_regex,
            lambda match: match.group("display_name") or match.group("attribute"),
            text,
        )
        bi_regex = r"{{bi\|(?P<buff>[^}|]+)(?:\|(?P<display_name>[^}|]+))?}}"
        text = re.sub(
            bi_regex,
            lambda match: match.group("display_name") or match.group("buff"),
            text,
        )
        tt_regex = r"{{tt\|(?P<text>[^}|]+)\|(?P<hover>[^}|]+)}}"
        text = re.sub(tt_regex, lambda match: match.group("text"), text)
        ui_regex = r"{{ui\|(?P<unit>[^}|]+)(?:\|(?P<display_name>[^}|]+))?}}"
        text = re.sub(
            ui_regex,
            lambda match: match.group("display_name") or match.group("unit"),
            text,
        )
        csl_regex = r"{{csl\|(?P<champ>[^}|]+)(?:\|(?P<skin>[^}|]+))?(?:\|(?P<display_name>[^}|]+))?}}"
        text = re.sub(
            csl_regex,
            lambda match: match.group("display_name")
            or match.group("skin")
            or match.group("champ"),
            text,
        )
        fi_regex = r"{{fi\|(?P<faction>[^}|]+)(?:\|(?P<display_name>[^}|]+))?}}"
        text = re.sub(
            fi_regex,
            lambda match: match.group("display_name") or match.group("faction"),
            text,
        )

        # regex = r"({{sm2\|[^|]+\|''\"(.*)\"'')|({{sm2\|[^|]+}} ''\"(.*)\"'')"

        if self.champion != "Kindred":
            regex = r"''\"(.*)\"''"
            matches = []

            for match in re.finditer(regex, text, re.MULTILINE):
                for match in reversed(match.groups()):
                    if match is not None and ".ogg" not in match and match != "GG!":
                        # Fix the markdown
                        match = match.replace("'''", "**")

                        matches.append(match)
                        break

            return matches
        else:
            lines = text.splitlines()
            last_asterisk_count = 1
            regex = r"(Wolf|Lamb|Kindred): ''(?:\")?([^\"]+)?(?:\")?''"
            matches = []

            for line in lines:
                line = line.strip()

                asterisk_count_in_this_line = 0
                for letter in line:
                    if letter == "*":
                        asterisk_count_in_this_line += 1
                    else:
                        break

                maybe_matches = re.findall(regex, line)
                if maybe_matches:
                    match = maybe_matches[0]
                    match_text = f"{match[0]}: {match[1]}"
                    match_text = match_text.replace("'''", "**")

                    if asterisk_count_in_this_line == last_asterisk_count + 1:
                        matches[-1] += f"\n{match_text}"
                    else:
                        matches.append(match_text)

                    last_asterisk_count = asterisk_count_in_this_line

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

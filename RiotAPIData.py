import json

from riotwatcher import LolWatcher


class RiotAPIData:
    def __init__(self, args=None, my_region="na1"):
        self.args = args  # Print hidden exceptions if args.e
        self.my_region = my_region
        self.key = self.get_key()
        self.watcher = LolWatcher(self.key)

    def get_key(self):
        with open("config.json", "r") as file:
            dict_ = json.load(file)
        return dict_["riot_api_key"]

    def check_versions(self):
        versions = {}
        try:
            with open("name_id_dict.json", "r") as file:
                versions["local"] = json.load(file)["version"]
        except FileNotFoundError:
            versions["local"] = None
        try:
            versions["live"] = self.watcher.data_dragon.versions_for_region(
                self.my_region
            )["n"]["champion"]
        except Exception as e:
            if e.response.status_code == 401:
                print(
                    "No API key was supplied. Get a new key from:",
                    "https://developer.riotgames.com",
                )
            if e.response.status_code == 403:
                print(
                    "Invalid API key. Get a new key from:",
                    "https://developer.riotgames.com",
                )
            if self.args.e:
                print(e)
            versions["live"] = None
        return versions

    def download_champ_data(self):
        # https://developer.riotgames.com/docs/lol#data-dragon_data-assets
        versions = self.watcher.data_dragon.versions_for_region(self.my_region)
        champions_version = versions["n"]["champion"]
        champions_data = self.watcher.data_dragon.champions(champions_version)
        result = {
            "type": "champion",
            "version": champions_data["version"],
            "data": {},
        }
        for champion in champions_data["data"].values():
            result["data"][champion["key"]] = {
                "id": int(champion["key"]),
                "name_id": champion["id"],
                "name": champion["name"],
                "icon": f"https://ddragon.leagueoflegends.com/cdn/{champions_data['version']}/img/champion/{champion['id']}.png",
            }

        result["data"] = dict(sorted(result["data"].items(), key=lambda x: int(x[0])))
        with open("name_id_dict.json", "w") as file:
            json.dump(result, file, indent=4)


if __name__ == "__main__":
    riot_api_data = RiotAPIData()
    riot_api_data.download_champ_data()

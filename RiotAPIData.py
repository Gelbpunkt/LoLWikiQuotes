import json
from riotwatcher import LolWatcher


class RiotAPIData:
    def __init__(self, args=None, my_region="na1"):
        self.args = args  # Print hidden exceptions if args.e
        self.my_region = my_region
        self.key = self.get_key()
        self.watcher = LolWatcher(self.key)

    def get_key(self):
        try:
            with open("riot_api_key.json", "r") as file:
                dict_ = json.load(file)
            riot_api_key = dict_["riot_api_key"]
            if riot_api_key == "xxxxx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx":
                print(
                    "Replace the placeholder key of x's with your own"
                    " Riot API key in the 'riot_api_key.json' file."
                )
                return None
            return riot_api_key
        except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
            print(e)
            print(
                "The file, 'riot_api_key.json', was either missing or its"
                " data structure was corrupted. Generating a new file..."
            )
            with open("riot_api_key.json", "w") as file:
                dict_ = {"riot_api_key": "xxxxx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}
                json.dump(dict_, file, indent=4)
            print(
                "Replace the placeholder key of x's with your own"
                "Riot API key in the 'riot_api_key.json' file."
            )
            return None

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
                "name": champion["name"],
            }

        result["data"] = dict(sorted(result["data"].items(), key=lambda x: int(x[0])))
        with open("name_id_dict.json", "w") as file:
            json.dump(result, file, indent=4)


if __name__ == "__main__":
    riot_api_data = RiotAPIData()
    riot_api_data.download_champ_data()

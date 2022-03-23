import json


class Registry:
    def __init__(self, path: str):
        self.pels = self.loadJson(path)

    def loadJson(self, path: str):
        with open(path, "r") as f:
            load_dict = json.load(f)
            return load_dict["PELs"]

    def getErrorMessage(self, code: str):
        for pel in self.pels:
            if "ReasonCode" not in pel["SRC"] and code not in pel["SRC"]["ReasonCode"]:
                continue

            if "Words6To9" not in pel["SRC"]:
                continue

            for p in pel["SRC"]["Words6To9"]:
                if "MessageArgSources" in pel["Documentation"]:
                    return int(p), pel["SRC"]["Words6To9"][p]["AdditionalDataPropSource"], pel["SRC"]["Words6To9"][p]["Description"], pel["Documentation"]["Message"], pel["Documentation"]["MessageArgSources"]
                else:
                    return int(p), pel["SRC"]["Words6To9"][p]["AdditionalDataPropSource"], pel["SRC"]["Words6To9"][p]["Description"], pel["Documentation"]["Message"], []

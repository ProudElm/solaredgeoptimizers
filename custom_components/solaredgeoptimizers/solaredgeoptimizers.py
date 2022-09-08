""" My module """
import requests
import json
from jsonfinder import jsonfinder

# from requests.auth import HTTPBasicAuth


class solaredgeoptimizers:
    def __init__(self, siteid, username, password):
        self.siteid = siteid
        self.username = username
        self.password = password

    def check_login(self):
        url = "https://monitoring.solaredge.com/solaredge-apigw/api/sites/{}/layout/logical".format(
            self.siteid
        )

        kwargs = {}
        kwargs["auth"] = requests.auth.HTTPBasicAuth(self.username, self.password)
        r = requests.get(url, **kwargs)

        return r.status_code

    def requestLogicalLayout(self):
        url = "https://monitoring.solaredge.com/solaredge-apigw/api/sites/{}/layout/logical".format(
            self.siteid
        )

        kwargs = {}

        kwargs["auth"] = requests.auth.HTTPBasicAuth(self.username, self.password)
        r = requests.get(url, **kwargs)

        return r.text

    def requestListOfAllPanels(self):
        json_obj = json.loads(self.requestLogicalLayout())

        return SolarEdgeSite(json_obj)

    def requestSystemData(self, itemId):
        url = "https://monitoringpublic.solaredge.com/solaredge-web/p/publicSystemData?reporterId={}&type=panel&activeTab=0&fieldId={}&isPublic=true&locale=en_US".format(
            itemId, self.siteid
        )

        kwargs = {}
        kwargs["auth"] = requests.auth.HTTPBasicAuth(self.username, self.password)
        r = requests.get(url, **kwargs)

        if r.status_code == 200:

            return SolarEdgeOptimizerData(itemId, decodeResult(r.text))
        else:
            print("Fout bij verzenden. Status code: {}".format(r.status_code))
            print(r.text)
            raise Exception

    def requestAllData(self):

        solarsite = self.requestListOfAllPanels()

        data = []
        for inverter in solarsite.inverters:
            for string in inverter.strings:
                for optimizer in string.optimizers:
                    info = self.requestSystemData(optimizer.optimizerId)
                    data.append(info)
        return data


def decodeResult(result):
    json_result = ""
    for _, __, obj in jsonfinder(result, json_only=True):
        json_result = obj
        break
    else:
        raise ValueError("data not found")

    return json_result


class SolarEdgeSite:
    def __init__(self, json_obj):
        self.siteId = json_obj["siteId"]
        self.inverters = self.__GetAllInverters(json_obj)

    def __GetAllInverters(self, json_obj):

        inverters = []
        for i in range(len(json_obj["logicalTree"]["childIds"])):
            # inverters.append(SolarEdgeInverter(json_obj["logicalTree"]["children"][i]["data"]))
            inverters.append(SolarEdgeInverter(json_obj, i))

        return inverters

    def returnNumberOfOptimizers(self):
        i = 0

        for inverter in self.inverters:
            for string in inverter.strings:
                i = i + len(string.optimizers)

        return i

    def ReturnAllPanelsIds(self):

        panel_ids = []

        for inverter in self.inverters:
            for string in inverter.strings:
                for optimizer in string.optimizers:
                    panel_ids.append(
                        "{}|{}".format(optimizer.optimizerId, optimizer.serialNumber)
                    )

        return panel_ids


class SolarEdgeInverter:
    def __init__(self, json_obj, index):
        self.__index = index
        self.inverterId = json_obj["logicalTree"]["children"][index]["data"]["id"]
        self.serialNumber = json_obj["logicalTree"]["children"][index]["data"][
            "serialNumber"
        ]
        self.name = json_obj["logicalTree"]["children"][index]["data"]["name"]
        self.displayName = json_obj["logicalTree"]["children"][index]["data"][
            "displayName"
        ]
        self.relativeOrder = json_obj["logicalTree"]["children"][index]["data"][
            "relativeOrder"
        ]
        self.type = json_obj["logicalTree"]["children"][index]["data"]["type"]
        self.operationsKey = json_obj["logicalTree"]["children"][index]["data"][
            "operationsKey"
        ]
        self.strings = self.__GetStringInformation(json_obj)

    def __GetStringInformation(self, json_obj):

        strings = []

        for i in range(
            len(json_obj["logicalTree"]["children"][self.__index]["children"])
        ):
            strings.append(
                SolarEdgeString(
                    json_obj["logicalTree"]["children"][self.__index]["children"][i]
                )
            )

        return strings


class SolarEdgeString:
    def __init__(self, json_obj):
        self.stringId = json_obj["data"]["id"]
        self.serialNumber = json_obj["data"]["serialNumber"]
        self.name = json_obj["data"]["name"]
        self.displayName = json_obj["data"]["displayName"]
        self.relativeOrder = json_obj["data"]["relativeOrder"]
        self.type = json_obj["data"]["type"]
        self.operationsKey = json_obj["data"]["operationsKey"]
        self.optimizers = self.__GetOptimizers(json_obj)

    def __GetOptimizers(self, json_obj):

        optimizers = []

        for i in range(len(json_obj["children"])):
            optimizers.append(SolarlEdgeOptimizer(json_obj["children"][i]))

        return optimizers


class SolarlEdgeOptimizer:
    def __init__(self, json_obj):
        self.optimizerId = json_obj["data"]["id"]
        self.serialNumber = json_obj["data"]["serialNumber"]
        self.name = json_obj["data"]["name"]
        self.displayName = json_obj["data"]["displayName"]
        self.relativeOrder = json_obj["data"]["relativeOrder"]
        self.type = json_obj["data"]["type"]
        self.operationsKey = json_obj["data"]["operationsKey"]


class SolarEdgeOptimizerData:
    """boe"""

    def __init__(self, paneelid, json_object):
        self._json_obj = json_object

        # Atributen die we willen zien:
        self.serialnumber = json_object["serialNumber"]
        self.paneel_id = paneelid
        self.paneel_desciption = json_object["description"]
        self.lastmeasurement = json_object["lastMeasurementDate"]
        self.model = json_object["model"]
        self.manufacturer = json_object["manufacturer"]

        # Waarden
        self.current = json_object["measurements"]["Current [A]"]
        self.optimizer_voltage = json_object["measurements"]["Optimizer Voltage [V]"]
        self.power = json_object["measurements"]["Power [W]"]
        self.voltage = json_object["measurements"]["Voltage [V]"]

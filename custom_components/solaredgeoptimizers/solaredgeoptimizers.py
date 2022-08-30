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

        # r = requests.get(url, auth=HTTPBasicAuthHandler(password_mgr=pswd_mng))
        kwargs = {}
        kwargs["auth"] = requests.auth.HTTPBasicAuth(self.username, self.password)
        r = requests.get(url, **kwargs)

        return r.status_code

    def requestLogicalLayout(self):
        url = "https://monitoring.solaredge.com/solaredge-apigw/api/sites/{}/layout/logical".format(
            self.siteid
        )

        # r = requests.get(url, auth=HTTPBasicAuthHandler(password_mgr=pswd_mng))
        kwargs = {}
        # print(self.siteid)
        # print(self.username)
        # print(self.password)
        kwargs["auth"] = requests.auth.HTTPBasicAuth(self.username, self.password)
        r = requests.get(url, **kwargs)

        return r.text

    def requestListOfAllPanels(self):
        json_obj = json.loads(self.requestLogicalLayout())

        aantal_panelen = len(
            json_obj["logicalTree"]["children"][0]["children"][0]["children"]
        )
        # print(aantal_panelen)

        paneel_ids = []

        for paneel in json_obj["logicalTree"]["children"][0]["children"][0]["children"]:
            # print("id: {}".format(paneel["data"]["id"]))
            # print(paneel)
            # paneel_ids.append(paneel["data"]["id"])
            paneel_ids.append(
                "{}|{}".format(paneel["data"]["id"], paneel["data"]["serialNumber"])
            )

        return paneel_ids

    def requestSystemData(self, itemId):
        url = "https://monitoringpublic.solaredge.com/solaredge-web/p/publicSystemData?reporterId={}&type=panel&activeTab=0&fieldId={}&isPublic=true&locale=en_US".format(
            itemId, self.siteid
        )

        # print(url)
        kwargs = {}
        kwargs["auth"] = requests.auth.HTTPBasicAuth(self.username, self.password)
        r = requests.get(url, **kwargs)

        if r.status_code == 200:
            # print(r.text)
            # return decodeResult(r.text)["measurements"]
            return SolarEdgeOptimizerData(itemId, decodeResult(r.text))
        else:
            print("Fout bij verzenden. Status code: {}".format(r.status_code))
            print(r.text)
            raise Exception

    def requestAllData(self):

        panelen = self.requestListOfAllPanels()

        data = []
        for paneel in panelen:
            info = self.requestSystemData(paneel.split("|")[0])
            data.append(info)

        return data


def decodeResult(result):
    json_result = ""
    for _, __, obj in jsonfinder(result, json_only=True):
        json_result = obj
        break
    else:
        raise ValueError("data not found")

    # print(json_result)

    # print(json_result["lastMeasurementDate"])
    return json_result


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

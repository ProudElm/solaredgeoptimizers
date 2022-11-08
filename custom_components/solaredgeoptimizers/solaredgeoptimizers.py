""" My module """
import requests
import json
from jsonfinder import jsonfinder
import logging
from requests import Session
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)

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
            json_object = decodeResult(r.text)
            try:
                if json_object["lastMeasurementDate"] == "":
                    _LOGGER.info("Skipping optimizer %s without measurements", itemId)
                    return None
                else:
                    return SolarEdgeOptimizerData(itemId, json_object)
            except Exception as errortje:
                _LOGGER.error(errortje)
                return None
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
                    if info is not None:
                        data.append(info)

        return data

    def getLifeTimeEnergy(self):
        session = Session()
        session.head(
            "https://monitoring.solaredge.com/solaredge-apigw/api/sites/{}/layout/energy".format(
                self.siteid
            )
        )

        url = "https://monitoring.solaredge.com/solaredge-web/p/login"

        session.auth = (self.username, self.password)

        # request a login url the get the correct cookie
        r1 = session.get(url)

        # Fix the cookie to get a string.
        therightcookie = self.MakeStringFromCookie(session.cookies.get_dict())
        # The csrf-token is needed as a seperate header.
        thecrsftoken = self.GetThecsrfToken(session.cookies.get_dict())

        # Build up the request.
        response = session.post(
            url="https://monitoring.solaredge.com/solaredge-apigw/api/sites/{}/layout/energy?timeUnit=ALL".format(
                self.siteid
            ),
            headers={
                "authority": "monitoring.solaredge.com",
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9,nl;q=0.8",
                "content-type": "application/json",
                "cookie": therightcookie,
                "origin": "https://monitoring.solaredge.com",
                "referer": "https://monitoring.solaredge.com/solaredge-web/p/site/{}/".format(
                    self.siteid
                ),
                "sec-ch-ua": '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
                "x-csrf-token": thecrsftoken,
                "x-kl-ajax-request": "Ajax_Request",
                "x-requested-with": "XMLHttpRequest",
            },
        )

        if response.status_code == 200:
            return response.text
        else:
            return "ERROR001 - HTTP CODE: {}".format(response.status_code)

    def GetThecsrfToken(self, cookies):
        for cookie in cookies:
            if cookie == "CSRF-TOKEN":
                return cookies[cookie]

    def MakeStringFromCookie(self, cookies):

        maincookiestring = ""
        for cookie in cookies:
            if cookie == "CSRF-TOKEN":
                maincookiestring = (
                    maincookiestring + cookie + "=" + cookies[cookie] + ";"
                )
            elif cookie == "JSESSIONID":
                maincookiestring = (
                    maincookiestring + cookie + "=" + cookies[cookie] + ";"
                )

        maincookiestring = (
            maincookiestring
            + "SolarEdge_Locale=nl_NL; SolarEdge_Locale=nl_NL; solaredge_cookie_concent=1;SolarEdge_Field_ID={}".format(
                self.siteid
            )
        )

        return maincookiestring


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

        # Atributen die we willen zien:
        self.serialnumber = ""
        self.paneel_id = ""
        self.paneel_desciption = ""
        self.lastmeasurement = ""
        self.model = ""
        self.manufacturer = ""

        # Waarden
        self.current = ""
        self.optimizer_voltage = ""
        self.power = ""
        self.voltage = ""

        if paneelid is not None:
            self._json_obj = json_object

            # Atributen die we willen zien:
            self.serialnumber = json_object["serialNumber"]
            self.paneel_id = paneelid
            self.paneel_desciption = json_object["description"]
            rawdate = json_object["lastMeasurementDate"]
            # Tue Nov 01 16:53:41 GMT 2022
            self.lastmeasurement = datetime.strptime(
                rawdate, "%a %b %d %H:%M:%S GMT %Y"
            )
            self.model = json_object["model"]

            self.manufacturer = json_object["manufacturer"]

            # Waarden
            self.current = json_object["measurements"]["Current [A]"]
            self.optimizer_voltage = json_object["measurements"][
                "Optimizer Voltage [V]"
            ]
            self.power = json_object["measurements"]["Power [W]"]
            self.voltage = json_object["measurements"]["Voltage [V]"]

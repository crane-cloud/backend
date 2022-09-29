from logging import warning
import string
import requests

# Using kubecost allocation API
# https://guide.kubecost.com/hc/en-us/articles/4407595916823-Allocation-API


def get_ug_currency(usd_amount):
    """
    Get UGX from of USD
    """
    rate = 3600
    return round(rate * usd_amount, -2)


class CostModal:
    def __init__(self, base_url):
        self.base_url = base_url

    def set_respose(self, response, not_series, show_deployments, namespace):
        response.raise_for_status()
        res = response.json()
        warning = res.get('warning', False)
        if warning:
            return warning
        if len(res['data']) == 0:
            return {'message': 'No data available'}
        pricing_data = []
        if not_series:
            if show_deployments:
                items_list = res['data'][0]
                deployments_cost = []
                for deployment in items_list:
                    deployments_cost.append({
                        "name": items_list[deployment].get("name", None),
                        "cpuCost": items_list[deployment].get("cpuCost", None),
                        "networkCost": items_list[deployment].get("networkCost", None),
                        "ramCost": items_list[deployment].get("ramCost", None),
                        "pvCost": items_list[deployment].get("pvCost", None),
                        "totalCost": items_list[deployment].get("totalCost", None),
                        "start": items_list[deployment].get("start", None),
                        "end": items_list[deployment].get("end", None),
                        "ugxCost": get_ug_currency(items_list[deployment].get("totalCost", None))
                    })
                pricing_data = {
                    "namespace": namespace,
                    'deployments_costs': deployments_cost
                }
            else:
                for value in res['data'][0]:
                    bill = res['data'][0][value]
                    pricing_data = {
                        "name": bill.get("name", None),
                        "cpuCost": bill.get("cpuCost", None),
                        "networkCost": bill.get("networkCost", None),
                        "ramCost": bill.get("ramCost", None),
                        "pvCost": bill.get("pvCost", None),
                        "totalCost": bill.get("totalCost", None),
                        "start": bill.get("start", None),
                        "end": bill.get("end", None),
                        "ugxCost": get_ug_currency(bill.get("totalCost", None))
                    }
        else:
            for value in res['data'][0]:
                namespace_name = res['data'][0][value]['name']

            for value in res['data']:
                bill = value.get(namespace_name)
                pricing_data.append({
                    "name": bill.get("name", None),
                    "cpuCost": bill.get("cpuCost", None),
                    "networkCost": bill.get("networkCost", None),
                    "ramCost": bill.get("ramCost", None),
                    "pvCost": bill.get("pvCost", None),
                    "totalCost": bill.get("totalCost", None),
                    "start": bill.get("start", None),
                    "end": bill.get("end", None),
                    "ugxCost": get_ug_currency(bill.get("totalCost", None))
                })
        return pricing_data

    def get_namespace_cost(self, window, namespace, show_deployments=False, series=False):
        if show_deployments:
            series = False
        not_series = not series
        try:
            query = f"""{self.base_url}/model/allocation?
                window={window}
                &aggregate={'deployment' if show_deployments else 'namespace'}
                &idle=false
                &accumulate={not_series}
                &filterNamespaces={namespace}"""

            stripped_query = query.translate(
                str.maketrans("", "", string.whitespace))
            response = requests.get(stripped_query)
            return self.set_respose(response, not_series, show_deployments, namespace)
        except Exception as error:
            print(error)
            return False

    def get_deployment_cost(self, window, deployment):
        try:
            query = f"""{self.base_url}/model/allocation?
                window={window}
                &aggregate=deployment
                &idle=false
                &accumulate=true
                &filterDepoyments={deployment}"""
            stripped_query = query.translate(
                str.maketrans("", "", string.whitespace))
            response = requests.get(stripped_query)
            return self.set_respose(response)
        except requests.exceptions.HTTPError as error:
            print(error)
            return False

from logging import warning
import string
import requests

# Using kubecost allocation API
# https://guide.kubecost.com/hc/en-us/articles/4407595916823-Allocation-API

# TODO: Remove this url and add it to cluster
BASE_URL = 'https://netlabs-test.dev.cranecloud.io'


def set_respose(response, not_series, show_deployments, namespace):
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
            })
    return pricing_data


def get_namespace_cost(window, namespace, show_deployments=False, series=False):
    not_series = not series
    try:
        query = f"""{BASE_URL}/model/allocation?
            window={window}
            &aggregate={'deployment' if show_deployments else 'namespace'}
            &idle=false
            &accumulate={not_series}
            &filterNamespaces={namespace}"""

        stripped_query = query.translate(
            str.maketrans("", "", string.whitespace))
        response = requests.get(stripped_query)
        return set_respose(response, not_series, show_deployments, namespace)
    except Exception as error:
        print(error)
        return False


def get_deployment_cost(window, deployment):
    try:
        query = f"""{BASE_URL}/model/allocation?
            window={window}
            &aggregate=deployment
            &idle=false
            &accumulate=true
            &filterDepoyments={deployment}"""
        stripped_query = query.translate(
            str.maketrans("", "", string.whitespace))
        response = requests.get(stripped_query)
        return set_respose(response)
    except requests.exceptions.HTTPError as error:
        print(error)
        return False

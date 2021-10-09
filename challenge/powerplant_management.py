# -*- coding: utf-8 -*-
# 02/10/21 - Oscar L'Hopitault

# Packages
import math

""" This tool computes the optimal distribution of power among several powerplants for a given load. 
    It takes json data as input and returns a json structure. 
    It takes into account a strict priority order, if long-run marginal costs given in the statement are modified, 
    the algorithm does not work anymore. 
    No short-run marginal costs are given for studied cases. """


# Round each power value inside the payload to a multiple of 0.1 Mwh
def round_to_one_dec(payload):
    if math.fmod(payload["load"], 0.1) != 0:
        payload["load"] = round(payload["load"], 1)
    for powerplant in payload["powerplants"]:
        if math.fmod(powerplant["pmin"], 0.1) != 0:
            powerplant["pmin"] = round(powerplant["pmin"], 1)
        if math.fmod(powerplant["pmax"], 0.1) != 0:
            powerplant["pmax"] = round(powerplant["pmax"], 1)


# Sort the powerplants by priority orders to reduce the number of combinations for the unit-commitment problem
def priority_order(payload):
    # Round each power value to a multiple of 0.1 Mwh
    round_to_one_dec(payload)

    # Defines powerplants dictionaries to sort
    wind_turbines = {}
    others = {}

    # Browse the "powerplants" key of payload dictionnary
    for powerplant in payload["powerplants"]:
        p_type = powerplant['type']

        # Assign cost or power generated depending on the type of powerplant
        if p_type == "gasfired":
            p = payload["fuels"]["gas(euro/MWh)"]
            cost = p / powerplant['efficiency']  # euro / MWh
            # cost taking CO2 into account
            cost = cost + 0.3 * payload["fuels"]["co2(euro/ton)"] # euro / MWh
            others[powerplant["name"]] = cost
        elif p_type == "turbojet":
            p = payload["fuels"]["kerosine(euro/MWh)"]
            cost = p / powerplant['efficiency']  # euro / MWh
            others[powerplant["name"]] = cost
        elif p_type == "windturbine":
            w = payload["fuels"]["wind(%)"] / 100
            pwind = w * powerplant["pmax"]  # MWh
            wind_turbines[powerplant["name"]] = pwind
        else:
            raise TypeError("An incorrect type of powerplant was given as input.")

    # Sort power generated of wind turbines in descending order
    wind_turbines = dict(sorted(wind_turbines.items(), key=lambda item: item[1], reverse=True))
    # Sort cost in ascending order
    others = dict(sorted(others.items(), key=lambda item: item[1]))
    # Merge both dictionaries (wind turbines are priors to other powerplants since their cost is 0)
    wind_turbines.update(others)

    # Initialization of a new payload dictionary
    payload_new = []
    # Browse the "powerplants" key of wind_turbines dictionary (wind_turbines actually refers to sorted powerplants)
    for sorted_powerplant in wind_turbines:
        for powerplant in payload["powerplants"]:
            if powerplant["name"] == sorted_powerplant:
                payload_new.append(powerplant)

    return payload_new   # Returns the new powerplants sorted with 1 added item


# Unit commitment algorithm for a payload containing powerplants respecting strict priority orders
def unit_commitment(payload):
    # sort the powerplants by priority orders
    powerplants = priority_order(payload)
    a = 0
    n = 0
    res = []
    # Browse powerplants and sum their maximal power by ascending cost until exceeding the load
    for powerplant in powerplants:
        if a < payload["load"]:
            a += powerplant["pmax"]
            res.append({"name": powerplant["name"], "p": powerplant["pmax"]})
            n += 1
        else:
            res.append({"name": powerplant["name"], "p": 0})

    # Change the last non-zero powerplant power to exactly match the load (due to priority orders)
    if a > payload["load"]:
        # required power to match the load
        p_required = res[n-1]["p"] - (a - payload["load"])
        # minimal power of the last non-zero powerplant (gaz-fired powerplant)
        p_min = powerplants[n-1]["pmin"]
        # Set last powerplant power to required power
        res[n - 1]["p"] = p_required
        # If minimal power is higher than required power, compare cost value with other powerplants to select the best
        while p_min > p_required:
            # Set the cost of the last powerplant
            cost = powerplants[n - 1]["pmin"] * payload["fuels"]["gas(euro/MWh)"] / powerplants[n - 1]['efficiency']
            # Set the cost of the next powerplant by priority order
            if powerplants[n]["type"] == "gasfired":
                cost2 = powerplants[n]["pmin"] * payload["fuels"]["gas(euro/MWh)"] / powerplants[n]['efficiency']
            elif powerplants[n]["type"] == "turbojet":
                cost2 = powerplants[n]["pmin"] * payload["fuels"]["kerosine(euro/MWh)"] / powerplants[n]['efficiency']
            elif powerplants[n]["type"] == "windturbine":
                cost2 = 0
            else:
                raise TypeError("Wrong type of powerplant.")
            # Choose the next powerplant by priority order if the cost of the next one is lower
            if cost > cost2:
                res[n - 1]["p"] = 0
                p_min = powerplants[n]["pmin"]
                n += 1
            # Else keep the current one
            else:
                p_min = powerplants[n-1]["pmin"]
                break
        # Set the power to minimal power is the current powerplant is the less expensive than next ones
        if p_min > p_required:
            res[n - 1]["p"] = p_min
        # Set the power to required power if minimal power is lower than required power
        else:
            res[n - 1]["p"] = p_required

    return res

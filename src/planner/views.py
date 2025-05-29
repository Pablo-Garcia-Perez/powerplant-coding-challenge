import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

class ProductionPlanView(APIView):
    def post(self, request):
        try:
            load = request.data.get("load")
            fuels = request.data.get("fuels")
            powerplants = request.data.get("powerplants")

            if load is None or fuels is None or powerplants is None:
                return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

            # We will define an array in which we will append power plants in dict format with all their information
            processed_plants = []
            for plant in powerplants:
                if plant["type"] == "windturbine":
                    # We must take into account % of wind today to properly set the pmax
                    actual_pmax = plant["pmax"] * fuels["wind(%)"] / 100
                    processed_plant = {
                        **plant,
                        "pmax": round(actual_pmax, 1),
                        "pmin": 0,  
                        "cost": 0  
                    }
                else:
                    cost = self._calculate_cost(plant, fuels)
                    processed_plant = {
                        **plant,
                        "cost": cost
                    }
                processed_plants.append(processed_plant)

            # Sort by cost in order to then loop starting by cheaper systems
            merit_order = sorted(
                processed_plants,
                key=lambda p: p["cost"]
            )

            result = []
            remaining_load = load
            allocated_power = {plant["name"]: 0 for plant in processed_plants}

            # First allocate windturbines as they cost 0€/MWh
            for plant in merit_order:
                if plant["type"] == "windturbine":
                    power = min(plant["pmax"], remaining_load)
                    power = round(power, 1)
                    if power > 0:
                        allocated_power[plant["name"]] = power
                        remaining_load -= power
                        remaining_load = round(remaining_load, 1)

            # Once windturbines power is allocated, proceed with the rest
            for plant in merit_order:
                if plant["type"] == "windturbine":
                    continue
                    
                if remaining_load <= 0:
                    break

                pmin = plant["pmin"]
                pmax = plant["pmax"]
                
                if remaining_load >= pmin:
                    power = min(pmax, remaining_load)
                    if power < remaining_load:
                        next_plants = [p for p in merit_order if p["name"] != plant["name"] and p["type"] != "windturbine"]
                        min_next_p = sum(p["pmin"] for p in next_plants)
                        if remaining_load - power < min_next_p:
                            power = max(pmin, remaining_load - min_next_p)
                    
                    power = round(power, 1)
                    allocated_power[plant["name"]] = power
                    remaining_load -= power
                    remaining_load = round(remaining_load, 1)

            if abs(remaining_load) > 0.1:
                if not self._adjust_allocations(allocated_power, processed_plants, load):
                    return Response({"error": "Unable to meet the load with given constraints."}, 
                                  status=status.HTTP_400_BAD_REQUEST)

            response = [{"name": name, "p": allocated_power[name]} for name in sorted(allocated_power.keys(), 
                        key=lambda x: (not x.startswith("wind"), x))]
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Unexpected error during production plan calculation.")
            return Response({"error": "Internal server error."}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _calculate_cost(self, plant, fuels):
        if plant["type"] == "gasfired":
            cost = fuels["gas(euro/MWh)"] / plant["efficiency"]
            # Add CO2 cost: 0.3 ton/MWh * CO2 price
            cost += 0.3 * fuels["co2(euro/ton)"] / plant["efficiency"]
            return cost
        elif plant["type"] == "turbojet":
            return fuels["kerosine(euro/MWh)"] / plant["efficiency"]
        elif plant["type"] == "windturbine":
            return 0
        return float("inf")

    def _adjust_allocations(self, allocated_power, plants, target_load):
        """Try to adjust allocations to meet the exact target load"""
        current_load = sum(allocated_power.values())
        difference = round(target_load - current_load, 1)
        
        if difference == 0:
            return True
            
        adjustable_plants = []
        for plant in plants:
            name = plant["name"]
            current = allocated_power[name]
            pmin = plant["pmin"]
            pmax = plant["pmax"]
            
            if current > pmin and (difference > 0 or current < pmax):
                adjustable_plants.append(plant)
        
        # Try to distribute the difference
        for plant in adjustable_plants:
            name = plant["name"]
            current = allocated_power[name]
            pmin = plant["pmin"]
            pmax = plant["pmax"]
            
            adjustment = round(min( max(difference, pmin - current), pmax - current), 1)
            
            allocated_power[name] += adjustment
            difference -= adjustment
            difference = round(difference, 1)
            
            if difference == 0:
                return True
                
        return False
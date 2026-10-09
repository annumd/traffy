import os
import sys

# Help Python find SUMO's TraCI library.
if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))

import traci


CONFIG_FILE = "simulation/run.sumocfg"

# These are examples. Replace them with the IDs from your network.
TRAFFIC_LIGHT_ID = "J0"
NS_LANES = ["north_in_0", "south_in_0"]
EW_LANES = ["east_in_0", "west_in_0"]

# These phase numbers must match your traffic light in NetEdit:
# 0 = North-South green, 1 = North-South yellow,
# 2 = East-West green, 3 = East-West yellow.
NS_GREEN_PHASE = 0
EW_GREEN_PHASE = 2

MIN_GREEN = 10
MAX_GREEN = 45
GREEN_TIME_BUDGET = 40
SIMULATION_END = 3600


def count_waiting(lanes):
    """Count stopped cars on a group of lanes."""
    count = 0

    for lane_id in lanes:
        try:
            count += traci.lane.getLastStepHaltingNumber(lane_id)
        except traci.TraCIException:
            print("Lane ID not found:", lane_id)

    return count


def calculate_green_times(ns_count, ew_count):
    """Share green time according to the number of waiting cars."""
    total = ns_count + ew_count

    if total == 0:
        return 20, 20

    ns_time = round(GREEN_TIME_BUDGET * ns_count / total)
    ew_time = GREEN_TIME_BUDGET - ns_time

    ns_time = max(MIN_GREEN, min(MAX_GREEN, ns_time))
    ew_time = max(MIN_GREEN, min(MAX_GREEN, ew_time))

    return ns_time, ew_time


def main():
    # Use SUMO's windowed version. Change to "sumo" for no window.
    sumo_program = "sumo-gui"

    traci.start([
        sumo_program,
        "-c", CONFIG_FILE,
        "--start",
    ])

    try:
        while traci.simulation.getTime() < SIMULATION_END:
            traci.simulationStep()

            phase = traci.trafficlight.getPhase(TRAFFIC_LIGHT_ID)

            if phase == NS_GREEN_PHASE:
                ns_count = count_waiting(NS_LANES)
                ew_count = count_waiting(EW_LANES)
                ns_green, _ = calculate_green_times(ns_count, ew_count)

                traci.trafficlight.setPhaseDuration(
                    TRAFFIC_LIGHT_ID, ns_green
                )

                print(
                    f"North-South waiting: {ns_count}, "
                    f"East-West waiting: {ew_count}, "
                    f"North-South green: {ns_green} seconds"
                )

            elif phase == EW_GREEN_PHASE:
                ns_count = count_waiting(NS_LANES)
                ew_count = count_waiting(EW_LANES)
                _, ew_green = calculate_green_times(ns_count, ew_count)

                traci.trafficlight.setPhaseDuration(
                    TRAFFIC_LIGHT_ID, ew_green
                )

                print(
                    f"North-South waiting: {ns_count}, "
                    f"East-West waiting: {ew_count}, "
                    f"East-West green: {ew_green} seconds"
                )

    finally:
        traci.close()


if __name__ == "__main__":
    main()

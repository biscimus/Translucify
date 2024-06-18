import os
import subprocess
import pm4py
from pm4py.objects.petri_net.utils.initial_marking import discover_initial_marking
from pm4py.objects.petri_net.utils.final_marking import discover_final_marking

def discover_petri_net_split(file_path: str):

    os.chdir("splitminer")

    # Define the command as a list of strings
    command = [
        "java",
        "-cp",
        "splitminer.jar:./lib/*",
        "au.edu.unimelb.services.ServiceProvider",
        "SMPN",
        "0.1",  # Parameter 1
        "0.4",  # Parameter 2
        "false",  # Parameter 3
        file_path,  # Input file
        file_path  # Output directory
    ]

    # Run the command
    result = subprocess.run(command, text=True, capture_output=True)

    # Check if the command was successful
    if result.returncode == 0:
        net, im, fm = pm4py.read_pnml(f"{file_path}.pnml")
        im = discover_initial_marking(net)
        fm = discover_final_marking(net)
        return net, im, fm
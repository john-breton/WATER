import multiprocessing
import os

from backend.html_scraper import HTMLScraper

# CONSTANTS TO MODIFY
""" Specify the number of processes you want to have acting as scraper
agents here. The number will depend on your data size, hardware, and
internet situation. Be aware that no recommendation is provided
"""
NUM_PROCESSES = 3

""" Specify the path to the CSV containing the list of URLs that you
wish to analyze. These sites will first have their HTML scraped before
later being analyzed for the three target metrics, alongside 
retrieving the accessibility percentage

This CSV is expected to have the following format:
    1, example.com
    2, website.com
"""
PATH_TO_TARGET_URLS = os.path.join("CHANGE", "ME")

""" Specify the path to the directory where the final results will be
written to a CSV file. This file will be named "results.csv"
"""
PATH_TO_OUTPUT_DIRECTORY = os.path.join("CHANGE", "ME")

""" Specify whether to display output in the console as a sort of 
progress tracker for each process.
"""
VERBOSE = False

""" Main routine, run a full analysis and generate a 
single data CSV on completion
"""
if __name__ == "__main__":
    processes = {}
    try:
        os.mkdir("temp_for_measurements")
    except FileExistsError:
        pass

    for i in range(1, NUM_PROCESSES + 1):
        os.mkdir(os.path.join("temp_for_measurements", f"{i}"))

    with open(PATH_TO_TARGET_URLS, "r") as file:
        csv_file = file.readlines()
        total = len(csv_file)
        div_j = int(total / NUM_PROCESSES)

        filename = 1
        for j in range(0, total):
            if j % div_j == 0:
                open(os.path.join("temp_for_measurements", f"{filename}.csv"),
                     "w+").writelines(csv_file[j:j + div_j])
                filename += 1
                if filename == NUM_PROCESSES:
                    open(os.path.join("temp_for_measurements",
                                      f"{filename}.csv"), "w+").writelines(
                        csv_file[j + div_j:])
                    break

    for k in range(1, NUM_PROCESSES + 1):
        processes[f"p{k}"] = multiprocessing.Process(
            target=HTMLScraper,
            args=(os.path.join(
                "temp_for_measurements", f"{k}.csv"), os.path.join(
                "temp_for_measurements", f"{k}"), PATH_TO_OUTPUT_DIRECTORY,
                  VERBOSE))

    for p in processes.values():
        p.start()

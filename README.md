# Web Accessbility Threat Estimation Research (WATER)💧

This project contains a framework, known as WATER, that measures the threat landscape for a small subset of users that require accessibility tools to access the Internet.

## Development

### Tools

- Code editor: [PyCharm](https://www.jetbrains.com/pycharm/)
- Python: [3.9+](https://www.python.org/downloads/)

### Getting Started

1. Clone the repository

2. requirements.txt

   1. Install all packages contained in the requirements.txt file: [instructions](https://www.jetbrains.com/help/pycharm/managing-dependencies.html)
   2. Navigate to `startup.py` and modify the necessary constant values
   3. Run startup.py and await results!
   4. [Optional] Plot your data using the included Jupyter notebook (data_viz/data_analysis.ipynb)

3. To make changes to the code, open the project's root directory in PyCharm.

## Research Results
An upcoming published paper, title `Applying Accessibility Metrics to Measure the
Threat Landscape for Users with Disabilities` was written to go over the WATER framework and is included as part of this repository. In an effort to promote replication and reproducibility, the code used to gather the data mentioned in the paper, alongside the data itself is included within this repository. 

A high-level overview of the paper is provided below:

### Research Questions
The main questions that were being investigated included:
 - Can base metrics be used to determine if a webpage is accessible rather than using the full Web Content Accessibility Guidelines (WCAG) 2.1 standards? (open WCAG research question)
 - What is the Internet threat landscape for users that require accessibility tools to access the Internet?
 - Are the most popular websites significantly more accessible compared to the least popular websites? Are users that require accessibility tools to access the Internet at more risk if they visit websites with a lower popularity?

### Key Takeaways:
 - The data suggests that the collected base metrics cannot be used to determine the accessibility of the website (no trend exists between the metrics and the calculate accessibility percentage based on WCAG 2.1 guidelines)
   - This addresses an open W3C research question found [here](https://www.w3.org/WAI/RD/wiki/Benchmarking_Web_Accessibility_Metrics)
 - The threat landscape for users that require accessibility tools to access the Internet does not look promising, with a very high risk for these users to be subjected to **phishing attacks** and **information leakage**
 - The data suggests that the most popular websites are not significantly more or less accessible than the middle or least popular websites

## Author Contact
 - The main author of this work can be reached [here](mailto:john.breton@carleton.ca)

## Known issues

Currently, there are no known issues.

> If you notice a bug, please add it to the Issues tab. Make sure you include how to recreate the bug!
 

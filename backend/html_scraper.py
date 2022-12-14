import csv
import json
import multiprocessing
import os
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

from backend.metrics_calculator import MetricsCalculator, is_ready


class HTMLScraper:
    """The HTMLScraper class is responsible for scrapping the HTML of
    the home pages for every website listed in common/websites.txt

    In order to minimize the storage requirements of this application,
    only the specific HTML elements that are used for the metrics
    calculations are stored. Results for each website will be written
    to common/website_tag_data.json. Of note, a sample record will
    take the following form:
        entry = {
            "name": example.com,
            "alt-tags": [alt1, ..., altn],
            "href-tags": [alt1, ..., altn],
            "label-tags": [alt1, ..., altn],
            "input-tags": [alt1, ..., altn]
        }

    This class relies heavily on the BeautifulSoup and Selenium libraries
    for HTML scraping functionality. To learn more, please visit:
        https://beautiful-soup-4.readthedocs.io/en/latest/
        https://www.selenium.dev/documentation/webdriver/
    """

    HTTPS_PREFIX = "https://"
    JS_SCRIPT = "window.scrollTo(0, document.body.scrollHeight);"
    TIMEOUT_TIME = 60
    FAILURES = []

    def __init__(self, target_csv, output_path, csv_path, verbose=True):
        """Prepare our HTMLScraper object with class variables before
        running our scraper routine

        :param target_csv: The filename of the CSV that will be read. This is
                           acts as the source for the URLs to be scraped
        :param output_path: The path where the data will be written
        :param csv_path: The path where the final CSV will be written
        :param verbose: True for progress printouts, False otherwise
        """
        self.target_csv = target_csv
        self.output_path = output_path
        self.csv_path = csv_path
        self.verbose = verbose

        self._run_scraper()

    def _run_scraper(self):
        """Main scraper loop. Iteratively queries all URLs located with
        the target CSV file. Once all URLs have been queried, any failures
        due to timeouts will be written to a file known as failures.txt
        """
        count = 0
        with open(self.target_csv, "r") as file:
            csv_file = csv.reader(file)
            for line in csv_file:
                self._scrape_html(line[-1])
                count += 1
                if self.verbose and count % 50 == 0:
                    print(f"{multiprocessing.current_process().name}: {count}:"
                          f" {line[-1]}")
        with open("failures.txt", "w") as f:
            for fail in self.FAILURES:
                f.write(fail + "\n")
        MetricsCalculator(self.csv_path)

    def _scrape_html(self, link):
        """Scrape the raw HTML of the target URL, while trying to
        pass as a legitimate user using a headless Chrome instance

        Modern websites love JavaScript, which is a problem when
        trying to scrap the HTML of a website, because some content
        may not load unless JS is loaded. To get around this, instead
        of making a generic GET request, we use Selenium to run browser
        instances in order to get an accurate representation of a page

        :param link: The URL that is going to be scraped
        """
        try:
            # Set up our headless browser (Chrome is used here)
            options = webdriver.ChromeOptions()
            options.add_argument("headless")
            browser = webdriver.Chrome(options=options)

            # Load the page
            browser.get(self.HTTPS_PREFIX + link)
            WebDriverWait(browser, self.TIMEOUT_TIME).until(is_ready)

            # Scroll to the bottom of the page to trigger any JS loading
            browser.execute_script(self.JS_SCRIPT)
            time.sleep(1)
            WebDriverWait(browser, self.TIMEOUT_TIME).until(is_ready)

            # Grab the source and close the browser to save on resources
            source = browser.page_source
            browser.close()

            # Soup the page source
            soup = BeautifulSoup(source, "html.parser")
            self._parse_required_tags(soup, link)
        except WebDriverException:
            # Well we didn't get the webpage within the timeout
            print(f"[FAILURE]: Failed to get HTML from {link} "
                  f"within {self.TIMEOUT_TIME} seconds. Skipping...")
            self.FAILURES.append(link)

    def _parse_required_tags(self, soup, link):
        """Parses the required HTML tags for further accessibility measurement
        data analysis. These tags are the following:
            - All <img> tags
            - Any <a> tags that have an href attribute (hyperlinks)
            - All <label> tags
            - All <input> tags

        :param soup: The BeautifulSoup object containing the HTML
        :param link: The URL of the website that the HTML corresponds to
        """
        print(link)
        alt_tags = []
        for elem in soup.findAll('img'):
            alt_tags.append(str(elem))
        href_tags = []
        for elem in soup.findAll('a', href=True):
            href_tags.append(str(elem))
        label_tags = []
        for elem in soup.findAll('label'):
            label_tags.append(str(elem))
        input_tags = []
        for elem in soup.findAll('input'):
            input_tags.append(str(elem))
        self._add_to_json([link, alt_tags, href_tags, label_tags, input_tags])

    def _add_to_json(self, rows):
        """Prepare the data to conform to JSON standards, keeping only the
        data necessary for further accessibility analysis parsed from the HTML

        :param rows: The raw HTML data to be converted to JSON notation
        """
        entry = {
            "name": rows[0],
            "alt-tags": rows[1],
            "href-tags": rows[2],
            "label-tags": rows[3],
            "input-tags": rows[4]
        }

        self._write_to_json(entry, rows[0])

    def _write_to_json(self, entry, link):
        """Write the entry object to a JSON file

        :param entry: The JSON object to be written to a JSON file
        :param link: The URL that corresponds to the data in entry
        """
        with open(os.path.join(self.output_path, f"{link}.json"),
                  "w") as json_file:
            json.dump(entry, json_file, indent=4, separators=(',', ': '))

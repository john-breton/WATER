import csv
import json
import os
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait


def is_ready(browser):
    """Used to determine when a page has fully loaded.

    :return: True if the page is loaded, False otherwise
    """
    return browser.execute_script(
        "return document.readyState === 'complete'")


class MetricsCalculator:
    """The MetricsCalculator class is responsible for calculating three
    distinct metric scores for given HTML data. It will also query to
    retrieve the accessibility percentage of a website, based on its
    adherence to the WCAG 2.1.

    The net result will be a CSV file that stores the data in the
    following format:

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
    for AP querying. To learn more, please visit:
        https://beautiful-soup-4.readthedocs.io/en/latest/
        https://www.selenium.dev/documentation/webdriver/
    """

    FIXED_URL_LOOKUP = "MuiTypography-root MuiTypography-caption" \
                       " MuiTypography-colorTextSecondary"
    BASE_URL = "https://www.webaccessibility.com/results/?url=https%3A%2F%2F"

    def __init__(self, path):
        """Prepare our MetricsCalculator object with class variables
        before running our metrics routine

        :param path: The path with the JSON files containing the necessary
                     HTML data needed for analysis
        """
        self.directory_path = path
        self.row_data = []
        self.calculate_metrics()

    def calculate_metrics(self):
        """Routine to calculate all three target metrics and to
        retrieve the AP of each website to be evaluated
        """
        for file in os.listdir(self.directory_path):
            with open(os.path.join(self.directory_path, file), "r") as f:
                data = json.load(f)
                self.row_data.append(data["name"])
                self._calculate_alt_metric(data["alt-tags"])
                self._calculate_hyperlinks_metric(data["href-tags"])
                self._calculate_label_input_metric(data["label-tags"],
                                                   data["input-tags"])
                self._get_accessibility_percent(data["name"])
                with open(os.path.join(self.directory_path, "results.csv"),
                          "a", encoding='UTF8', newline='\n') as cf:
                    writer = csv.writer(cf)
                    writer.writerow(self.row_data)
                    self.row_data = []

    def _calculate_alt_metric(self, img_tags):
        """Image Tag Alt Adherence metric (ITAA)
        Measures the adherence to best practices in regard
        to image tags. Namely, any <img> should be associated
        with an alt attribute that describes the image in a meaningful
        capacity. This means that empty alt attributes or attributes
        that simply say e.g. "an image of" fail to be accessible.

        Of note, empty alt tags are not inherently bad, however the
        current recommendation is that if images are used just for
        decorative purposes, they should be made with CSS rather than
        being included as an <img> with an empty alt attribute:
        https://developer.mozilla.org/en-US/docs/Learn/Accessibility/HTML
        For this reason, empty alt attributes are treated as inaccessible

        The ITAA is calculated as follows, with 1 being the best score
        and 0 being the worst score:

            ITAA = number of <img> with meaningful alt attributes
                   / total number of <img> tags

        :param img_tags: A list of <img> tags to be analyzed
        """
        # Default case, no analysis can occur if there are no images
        if len(img_tags) == 0:
            self.row_data.append("No Data")
            return

        count_alt = 0
        for tag in img_tags:
            try:
                soup = BeautifulSoup(tag, "html.parser")
                alt_text = soup('img')[0]['alt']
                # Lazy check to see if the alt tag is meaningful
                if alt_text.lower() != "image" and alt_text != "" \
                        and "graphic of" not in alt_text.lower() \
                        and "image of" not in alt_text.lower() \
                        and "picture of" not in alt_text.lower() \
                        and "this is an image of" not in alt_text.lower():
                    count_alt = count_alt + 1
            except KeyError:
                # No alt tag exists in the img tag, do not add to count
                pass

        self.row_data.append(count_alt / len(img_tags))

    def _calculate_hyperlinks_metric(self, href_elements):
        """Hyperlink Astonishment Minimization metric (HAM)
        A metric that is used to express the proportion of hyperlinks
        with descriptive text that matches the url a user would be
        brought to upon clicking on the hyperlink. This check is simple
        enough, so long as the text associated with the <a> tag that
        contains the hyperlink appears in the hyperlink itself, it
        is considered accessible.

        HAM is calculated as follows, with 1 being the best score
        and 0 being the worst score:

            HAM = number of <a> with appropriate text for hrefs
                  / total number of <a> tags with hrefs

        :param href_elements: A list of <a> tags with hrefs to be analyzed
        """
        # Default case, no analysis can occur if there are no hrefs
        if len(href_elements) == 0:
            self.row_data.append("No Data")
            return

        count_href = 0
        flag = False

        for curr_href in href_elements:
            soup = BeautifulSoup(curr_href, "html.parser")
            # Grab the text associated with the hyperlink
            for curr_str in soup.text.split(" "):
                # Check if the title/text appears in the hyperlink path
                if curr_str in soup('a')[0]['href']:
                    flag = True
                    break
            if flag:
                count_href = count_href + 1
            flag = False

        self.row_data.append(count_href / len(href_elements))

    def _calculate_label_input_metric(self, label_tags, input_tags):
        """Label Input Mapping metric (LIM)
        A metric that is used to express the proportion of input tags
        that are unambiguously linked to a label tag. This is easily
        checked by comparing the id attribute of both an input and a
        label to see if they match. This is done for each <input> tag
        against every <label> tag until a match is found.

        LIM is calculated as follows, with 1 being the best score
        and 0 being the worst score:

            LIM = number of <input> tags with associating <label> tags
                  / total number of <input> tags

        :param label_tags: A list of <label> tags
        :param label_tags: A list of <input> tags
        """

        # Default case, no analysis can occur if there are no inputs
        if len(input_tags) == 0:
            self.row_data.append("No Data")
            return
        # Second case, only the label tags are empty,
        # implying unlabeled inputs
        elif len(label_tags) == 0:
            for curr_input in input_tags:
                soup = BeautifulSoup(curr_input, "html.parser")
                try:
                    # Make sure these are inputs that need to be checked
                    soup('input')[0]['hidden']
                except KeyError:
                    self.row_data.append(0.0)
                    return

        count_label_input = 0

        for curr_input in input_tags:
            soup = BeautifulSoup(curr_input, "html.parser")
            try:
                input_id = soup('input')[0]['id']
                for curr_label in label_tags:
                    soup_label = BeautifulSoup(curr_label, "html.parser")
                    if input_id in soup_label('label')[0]['for']:
                        try:
                            _ = soup('input')[0]['hidden']
                        except KeyError:
                            count_label_input = count_label_input + 1
                            break
            except KeyError:
                pass

        self.row_data.append(count_label_input / len(input_tags))

    def _get_accessibility_percent(self, target_url):
        """Get the Accessibility Percentage (AP) for a target URL. This
        is determined via a check performed by webaccessibility.com,
        which tests a URL for current adherence to WCAG 2.1.

        As this is a live website and it being queried, rate limiting
        is in place to avoid exhausting site resources. This could
        likely be done locally, however the package provided by the
        site for Python appears to currently be broken.

        Until that is resolved, this query-rate-limited approach
        will be used.

        :param target_url: The URL that will have its AP queried
        """
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("headless")
            browser = webdriver.Chrome(options=options)

            # Load the page
            browser.get(f"{self.BASE_URL}{target_url}/")
            WebDriverWait(browser, 60).until(is_ready)
            time.sleep(15)
            source = browser.page_source
            soup = BeautifulSoup(source, "html.parser")
            try:
                temp = soup.find("div", {"class": self.FIXED_URL_LOOKUP}).text
                self.row_data.append(temp)
            except Exception:
                time.sleep(15)
                source = browser.page_source
                soup = BeautifulSoup(source, "html.parser")
                try:
                    temp = soup.find("div",
                                     {"class": self.FIXED_URL_LOOKUP}).text
                    self.row_data.append(temp)
                except Exception:
                    self.row_data.append("-1%")
        except Exception:
            self.row_data.append("-1%")

"""
download course schedules
"""
import json
from concurrent.futures.thread import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By

class Course:
    """
    course
    """
    def __init__(self, url):
        self.driver = webdriver.Chrome()
        urls = url.split(" ")
        self.url = urls[1]
        self.code = urls[0]

    def run(self):
        """
        runs the page
        """
        driver = self.driver
        driver.get(self.url)
        course_title = driver.find_element(By.TAG_NAME, "h1").text
        rows = driver.find_elements(By.XPATH, "//table[@class='display']/tbody/tr[not(contains(@class,'first-element') or contains(@class, 'footer'))]")
        sections = []
        for row in rows: # Fill in the information for a single row
            section = row.find_element(By.CLASS_NAME, "Section").text.splitlines()[0].split(" ")[1]
            activity = {}
            activity["location"] = row.find_element(By.CLASS_NAME, "Place").text
            day_and_time = row.find_element(By.CLASS_NAME, "Day").text.split(" ")
            activity["day"] = day_and_time[0]
            activity["start"] = day_and_time[1]
            activity["end"] = day_and_time[3]
            activity["activity"] = row.find_element(By.CLASS_NAME, "Activity").text
            activity["section"] = section
            matching = [x for x in sections if x["section"] == section[0]]
            if matching:
                sections[sections.index(matching[0])]["activities"].append(activity)
            else:
                new_section = {}
                new_section["section"] = section[0]
                new_section["professor"] = row.find_element(By.CLASS_NAME, "Professor").text
                new_section["activities"] = []
                new_section["activities"].append(activity)
                sections.append(new_section)
        driver.close()

        return [self.code, {"course_title":course_title, "course_code":self.code, "sections":sections}]

LINKS = []
SCHEDULES = {}


def work(url):
    """
    run stuff
    """
    course = Course(url)
    return course.run()

with open("courses_mini.txt", "r") as courses_file:
    for line in courses_file.readlines():
        LINKS.append(line)

FUTURE = []
with ThreadPoolExecutor(max_workers=5) as executer:
    for link in LINKS:
        FUTURE.append(executer.submit(work, link))

for f in FUTURE:
    SCHEDULES[f.result()[0]] = f.result()[1]

with open("schedules.json", "w") as schedules_file:
    schedules_file.write(json.dumps(SCHEDULES))

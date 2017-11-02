"""
download course schedules
"""
import json
from concurrent.futures.thread import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By

class Course:
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
        course_sections = driver.find_elements(By.CSS_SELECTOR, "table.display")
        sections = []
        for course_section in course_sections:
            section = {}
            section["section"] = course_section.find_element(By.CLASS_NAME, "Section").text
            section["professor"] = course_section.find_element(By.CLASS_NAME, "Professor").text
            section["activity"] = course_section.find_element(By.CLASS_NAME, "Activity").text
            section["day"] = course_section.find_element(By.CLASS_NAME, "Day").text
            section["location"] = course_section.find_element(By.CLASS_NAME, "Place").text
            sections.append(section)
        driver.close()
        return [self.code, {"course_title":course_title, "sections":sections}]

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

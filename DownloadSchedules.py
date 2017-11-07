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
        self.url = url

    def run(self, url):
        """
        runs the page
        """
        urls = url.split(" ")
        url = urls[1]
        code = urls[0]
        try:
            driver = webdriver.Chrome()
            driver.get(url)
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
            driver.quit()
        except Exception:
            return (code, {"fail":True})

        return (code, {"course_title":course_title, "course_code":code, "sections":sections, "url":url})

LINKS = []
SCHEDULES = {}


def work(url):
    """
    run stuff
    """
    course = Course(url)
    return course.run(url)

def main():
    print("reading from file")
    with open("courses2181.txt", "r") as courses_file:
        for line in courses_file.readlines():
            LINKS.append(line)

    print("running selenium")
    with ThreadPoolExecutor(max_workers=20) as executer:
        for res in zip(LINKS, executer.map(work, LINKS)):
            SCHEDULES[res[1][0]] = res[1][1]
    print("writing to file")
    with open("schedules_winter_2018_3.json", "w") as schedules_file:
        schedules_file.write(json.dumps(SCHEDULES))

if __name__ == '__main__':
    main()

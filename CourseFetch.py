"""
a module to download all courses from the uottawa course timetable website
much more minimized version of https://github.com/morinted/schedule-generator
"""
from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures import as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
from itertools import product
from string import ascii_uppercase
import json
import re
import threading


DAY_MAP = {"Mo": "Monday", "Tu": "Tuesday", "We": "Wednesday",
           "Th": "Thursday", "Fr": "Friday", "Sa": "Saturday", "Su": "Sunday", "TBA": "TBA"}

URL = "https://uocampus.public.uottawa.ca/psc/csprpr9pub/EMPLOYEE/HRMS/c/UO_SR_AA_MODS.UO_PUB_CLSSRCH.GBL?languageCd=ENG&PortalActualURL=https%3a%2f%2fuocampus.public.uottawa.ca%2fpsc%2fcsprpr9pub%2fEMPLOYEE%2fHRMS%2fc%2fUO_SR_AA_MODS.UO_PUB_CLSSRCH.GBL%3flanguageCd%3dENG&PortalContentURL=https%3a%2f%2fuocampus.public.uottawa.ca%2fpsc%2fcsprpr9pub%2fEMPLOYEE%2fHRMS%2fc%2fUO_SR_AA_MODS.UO_PUB_CLSSRCH.GBL&PortalContentProvider=HRMS&PortalCRefLabel=Public%20Class%20Search&PortalRegistryName=EMPLOYEE&PortalServletURI=https%3a%2f%2fuocampus.public.uottawa.ca%2fpsp%2fcsprpr9pub%2f&PortalURI=https%3a%2f%2fuocampus.public.uottawa.ca%2fpsc%2fcsprpr9pub%2f&PortalHostNode=HRMS&NoCrumbs=yes&PortalKeyStruct=yes"


def getDriver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver


def executeTask(term, subject, year):
    driver = getDriver()
    print("STARTED: " + term + " " + subject + " " + str(year))
    res = main(term, subject, year, driver)
    driver.quit()
    print("COMPLETED: " + term + " " + subject + " " + str(year))
    return res


def main(term, subject, year, driver):
    """main"""

    wait = WebDriverWait(driver, 10)

    driver.get(
        URL
    )
    dp = driver.find_element(
        By.XPATH, '//select[@id="CLASS_SRCH_WRK2_STRM$35$"]')
    dropdown = Select(dp)
    dropdown.select_by_value(term)
    sub_elem = driver.find_element(By.ID, "SSR_CLSRCH_WRK_SUBJECT$0")
    while sub_elem.get_attribute("value") != subject:
        sub_elem.clear()
        sub_elem.click()
        for c in subject:
            sub_elem.send_keys(c)
    year_elem = driver.find_element(
        By.ID, "UO_PUB_SRCH_WRK_SSR_RPTCK_OPT_0" + str(year) + "$0"
    )
    year_elem.click()
    time.sleep(2)
    driver.execute_script(
        "submitAction_win0(document.win0,'CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH')")
    try:
        wait.until(lambda driver: driver.find_element(
            By.ID, "win0divSSR_CLSRSLT_WRK_GROUPBOX2$0"))
    except TimeoutException:
        return None
    return toJsonFormat(driver)


def toJsonFormat(driver):
    course_index = 0
    activity_index = 0
    courses = {}
    while True:
        try:
            # if element cannot be found we have reached end of the list
            groupbox = driver.find_element(
                By.ID, "win0divSSR_CLSRSLT_WRK_GROUPBOX2$" + str(course_index))
            course = {}
            sections = []
            while True:
                try:
                    activities = []
                    activity_row = groupbox.find_element(
                        By.ID, "trSSR_CLSRCH_MTG1$"+str(activity_index)+"_row1")
                    activity_row_section = activity_row.find_element(
                        By.ID, "MTG_CLASSNAME$" + str(activity_index)).text
                    activity_row_instructor = activity_row.find_element(
                        By.ID, "MTG_INSTR$" + str(activity_index)).text
                    activity_row_day_time = activity_row.find_element(
                        By.ID, "MTG_DAYTIME$" + str(activity_index)).text
                    activity_row_room = activity_row.find_element(
                        By.ID, "MTG_ROOM$" + str(activity_index)).text

                    activity_section, activity_type = activity_row_section.split("\n")[
                        0].split("-")

                    for time, room in zip(activity_row_day_time.split("\n"), activity_row_room.split("\n")):
                        activity_day, activity_start, _, activity_end = time.split(
                            " ")
                        activity = {}
                        activity["section"] = activity_section
                        activity["activity"] = activity_type
                        activity["day"] = DAY_MAP[activity_day]
                        activity["start"] = activity_start
                        activity["end"] = activity_end
                        activity["location"] = room
                        activities.append(activity)

                    instructor = activity_row_instructor.split("\n")[0]

                    section_letter = re.search(
                        "[A-Z]+", activity_section)[0]  # Z00, ZZ01, etc
                    matching = [
                        x for x in sections if x["section"] == section_letter]

                    if matching:
                        sections[sections.index(
                            matching[0])]["activities"].extend(activities)
                    else:
                        new_section = {}
                        new_section["section"] = section_letter
                        new_section["professor"] = instructor
                        new_section["activities"] = []
                        new_section["activities"].extend(activities)
                        sections.append(new_section)
                    activity_index = activity_index + 1
                except:
                    break

            course_code_title = groupbox.find_element(
                By.ID, "win0divSSR_CLSRSLT_WRK_GROUPBOX2GP$" + str(course_index)).text
            course_code, course_title = course_code_title.strip().split(" - ")
            course_code = course_code.replace(" ", "")
            course["course_code"] = course_code
            course["course_title"] = course_title
            course["sections"] = sections
            courses[course_code] = course
            course_index = course_index + 1
        except NoSuchElementException:
            break
    return courses


def getCourses():
    driver = getDriver()
    driver.get(URL)
    wait = WebDriverWait(driver, 10)
    # taken from https://github.com/morinted/schedule-generator
    driver.find_element(By.ID, 'CLASS_SRCH_WRK2_SSR_PB_SUBJ_SRCH$0').click()
    wait.until(lambda driver: driver.find_element(
        By.ID, "SSR_CLSRCH_WRK2_SSR_ALPHANUM_A"))
    codes = []
    for letter in ascii_uppercase:
        time.sleep(1)
        driver.find_element(
            By.ID, 'SSR_CLSRCH_WRK2_SSR_ALPHANUM_' + letter).click()
        html = driver.page_source
        current_codes = re.findall(
            '<span class="PSEDITBOX_DISPONLY" id="SSR_CLSRCH_SUBJ_SUBJECT\$\d+">([A-Z][A-Z][A-Z])</span>', html)
        codes.extend(current_codes)
    codes = list(set(codes))
    codes.sort()
    driver.quit()
    return codes


RESULT = {}

exit_flag = {}


def writer(term):
    while not exit_flag[term]:
        for x in as_completed(futures[term]):
            if x.result() is not None:
                RESULT[term] = {**RESULT[term], **x.result()}


def file_writer(sec, term):
    time.sleep(sec)
    exit_flag[term] = True


futures = {}

if __name__ == '__main__':
    start = time.time()
    print('\a')
    courses = getCourses()
    # courses = ["SEG", "CSI", "ADM"]
    print("got courses")
    print(courses)

    with ThreadPoolExecutor(max_workers=5) as executer:
        for term in ["2199", "2201"]:
            RESULT[term] = {}
            futures[term] = []
            exit_flag[term] = False
            write = threading.Thread(target=writer, args=(term,))
            write.start()
            for subject in courses:
                for year in [1, 2, 3, 4]:
                    futures[term].append(
                        executer.submit(executeTask, term, subject, year))
            file_write = threading.Thread(target=file_writer, args=(30, term))
            file_write.start()
            write.join()
            file_write.join()
            with open(term + ".json", "w") as schedules_file:
                schedules_file.write(json.dumps(RESULT[term]))
                print("written " + term + ".json")
                print('\a')
    end = time.time()
    print("Started: " + start)
    print("Ended: " + end)
    print("Completed in: " + end-start)
    print('\a')

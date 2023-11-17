import glob
import os
import sys

import traceback

import pandas
from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement as WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import pandas as pd
from datetime import datetime
import re
import logging
from selenium.webdriver.chrome.service import Service

# Classes to create Teams as an object
# Input:___________________________________
# team_name = Name of a Team (str)
# team_mood = 1 for home, 2 for away, 0 for other team (int)
# team_standing = team standing dictionary from Standing table if known (dict)
# Output:__________________________________
# An object of TEAM class - Contains all info about a team
# Methods:_________________________________
# str() method to print the name of the team
# __gr__ method to compare two teams' ranking
# __lt__ method to compare two teams' ranking
# __eq__ method to compare two teams' ranking
# __ne__ method to compare two teams' ranking
# Methods to get Standing - rank, GP, W, D, L, GF, GA, GD, PTS
# Methods to set Standing - rank, GP, W, D, L, GF, GA, GD, PTS
from selenium.webdriver.support.wait import WebDriverWait


class TEAM:

    def __init__(self, team_name: str, team_mood=3):
        self.RANK = self.PTS = self.GP = self.W = self.D = self.L = self.GF = self.GA = self.GD = 0
        self.team_name = team_name
        self.team_mood = team_mood

    # setter and getter for team standing

    def get_team_mood(self):
        if self.team_mood == 1:
            return "Home"
        elif self.team_mood == 2:
            return "Away"
        else:
            return "Opponent"

    def __str__(self):
        return self.team_name

    def get_rank(self):
        return self.RANK

    def add_rank(self, rank):
        self.RANK += rank

    def get_GP(self):
        return self.GP

    def add_GP(self, gp):
        self.GP += gp

    def get_W(self):
        return self.W

    def add_W(self, w):
        self.W += w

    def get_D(self):
        return self.D

    def add_D(self, d):
        self.D += d

    def get_L(self):
        return self.L

    def add_L(self, l):
        self.L += l

    def get_GF(self):
        return self.GF

    def add_GF(self, gf):
        self.GF += gf

    def get_GA(self):
        return self.GA

    def add_GA(self, ga):
        self.GA += ga

    def get_GD(self):
        return self.GD

    def add_GD(self, gd):
        self.GD += gd

    def get_PTS(self):
        return self.PTS

    def add_PTS(self, pts):
        self.PTS += pts

    def __gr__(self, other):
        return self.RANK > other.RANK

    def __lt__(self, other):
        return self.RANK < other.RANK

    def __eq__(self, other):
        return self.RANK == other.RANK

    def __ne__(self, other):
        return self.RANK != other.RANK


# Classes to create Matches as an object
# Input:___________________________________
# primary_team = Primary Team (TEAM)
# secondary_team = Secondary Team (TEAM)
# match_order = Order of the match
# p_score = Primary Team Score  (int)
# s_score = Secondary Team Score (int)
# Output:__________________________________
# An object of MATCH class - Contains all info about a match
# Methods:_________________________________
# str() method to print the tag of the Match
#         # 1 - primary_team == Home_Team and secondary_team == Opponent
#         # 2 - primary_team == Opponent and secondary_team == Home
#         # 3 - primary_team == Opponent and secondary_team == Away
#         # 4 - primary_team == Away and secondary_team == Opponent
# method to get primary team's and secondary team's stat difference
#       Thant is in rank, GP, W, D, L, GF, GA, GD, PTS
# get_match_status() method to get the status of the match
#       0 for draw, 1 for primary team win, 2 for secondary team win
# get_match_date() method to get the date of the match
# get_match_tag() method to get the tag of the match
class MATCH:

    def __init__(self, primary_team: TEAM, secondary_team: TEAM, match_order: int, p_score: int, s_score: int):
        self.primary_team = primary_team
        self.secondary_team = secondary_team
        self.match_order = match_order
        self.primary_score = int(p_score)
        self.secondary_score = int(s_score)

    def __str__(self):
        return str(self.match_order)

    def get_primary_team(self):
        return str(self.primary_team)

    def get_secondary_team(self):
        return str(self.secondary_team)

    def get_match_order(self):
        return self.match_order

    def get_primary_score(self):
        return self.primary_score

    def get_secondary_score(self):
        return self.secondary_score

    def get_goal_difference(self):
        return self.primary_score - self.secondary_score

    def get_rank_difference(self):
        return self.primary_team.get_rank() - self.secondary_team.get_rank()

    def get_PTS_difference(self):
        return self.primary_team.get_PTS() - self.secondary_team.get_PTS()

    def get_GP_difference(self):
        return self.primary_team.get_GP() - self.secondary_team.get_GP()

    def get_W_difference(self):
        return self.primary_team.get_W() - self.secondary_team.get_W()

    def get_D_difference(self):
        return self.primary_team.get_D() - self.secondary_team.get_D()

    def get_L_difference(self):
        return self.primary_team.get_L() - self.secondary_team.get_L()

    def get_GF_difference(self):
        return self.primary_team.get_GF() - self.secondary_team.get_GF()

    def get_GA_difference(self):
        return self.primary_team.get_GA() - self.secondary_team.get_GA()


# Class to Get a list of Matches from Forebet.com different pages and save output to a csv file
# Forebet.com pages: ['Yesterday', 'Today', 'Tomorrow', 'Weekend', 'Finished', 'Other']
#     Yesterday: https://www.forebet.com/en/football-predictions-from-yesterday
#     Today: https://www.forebet.com/en/football-tips-and-predictions-for-today
#     Tomorrow: https://www.forebet.com/en/football-tips-and-predictions-for-tomorrow
#     Weekend: https://www.forebet.com/en/football-tips-and-predictions-for-the-weekend
#     All Matches: https://www.forebet.com/en/football-predictions
#     Finished(Today): https://www.forebet.com/en/football-tips-and-predictions-for-today/finished
#     Other: Unknown links    
# Input:___________________________________
# url = type of page - ['Yesterday', 'Today', 'Tomorrow', 'Weekend', 'Finished'] - case insensitive (str)
# data_save_path = path to save the data (str) : Default = 'C:\\Users\\zelamay\\Desktop\\'
# Output:__________________________________
# Progress on the extraction of the data
# A csv file with all the matches from the page
# name of the csv file =  page_type + Date/Time page loaded + .csv'
# Method:.....................................
# Just initiate the class
class List_Matches:
    # INITIALIZING VARIABLES
    TODAY = 'https://www.forebet.com/en/football-tips-and-predictions-for-today'
    YESTERDAY = 'https://www.forebet.com/en/football-predictions-from-yesterday'
    TOMORROW = 'https://www.forebet.com/en/football-tips-and-predictions-for-tomorrow'
    WEEKEND = 'https://www.forebet.com/en/football-tips-and-predictions-for-the-weekend'
    FINISHED = 'https://www.forebet.com/en/football-tips-and-predictions-for-today/finished'
    ALL_MATCHES = 'https://www.forebet.com/en/football-predictions'

    def __init__(self, page_type='', data_save_path='C:\\Users\\zelamay\\PycharmProjects\\pythonProject\\Outputs\\'):

        page_type = page_type.capitalize()
        if page_type == 'TODAY':
            self.url = self.TODAY
        elif page_type == 'YESTERDAY':
            self.url = self.YESTERDAY
        elif page_type == 'TOMORROW':
            self.url = self.TOMORROW
        elif page_type == 'WEEKEND':
            self.url = self.WEEKEND
        elif page_type == 'FINISHED':
            self.url = self.FINISHED
        elif page_type == 'ALL_MATCHES':
            self.url = self.ALL_MATCHES
        else:
            self.url = self.TODAY

        self.matches_data = pd.DataFrame()
        self.logger = self.initiate_logger()
        page_driver = self.initiate_driver()
        matches_data = self.get_data(page_driver)

        # PREPARING DATA TO SAVE

        # Getting webpage title
        title = page_driver.title

        # Getting webpage type to save
        webpage_types = ['Today', 'Tomorrow', 'Yesterday', 'Weekend', 'Finished']
        save_name = 'Other'
        for value in webpage_types:
            if value in title:
                save_name = value

        # Getting current time to add to the name of the file
        current_time = time.strftime("%Y/%m/%d-%H:%M:%S")
        current_time = current_time.replace("/", "-").replace(":", "-")
        data_name_to_save = save_name + ' ' + current_time + '.csv'
        data_name_to_save = data_save_path + data_name_to_save
        # Adding Columns to the data
        data_column = ['Tag', 'Home Team', 'Away Team', 'Date', 'HPro', 'DPro', 'APro', 'HCor', 'ACor', 'AGol', 'Prog',
                       'HFull', 'AFull', 'Link']
        matches_data = matches_data.transpose()
        matches_data.columns = data_column

        # Saving Data
        self.logger.info("-" * 50)  # data logged
        self.logger.info("data logged")
        matches_data.to_csv(data_name_to_save, index=False)
        self.logger.info("data saved at " + data_name_to_save)

    # Method to Initiate Logger
    def initiate_logger(self):
        data_logger = logging.getLogger('data_logger')
        data_logger.setLevel(logging.INFO)  # INFO, DEBUG, WARNING, ERROR, CRITICAL
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        stdout_handler.setFormatter(formatter)
        data_logger.addHandler(stdout_handler)

        data_logger_handler = logging.FileHandler('data_logger.log')
        data_logger_handler.setLevel(logging.INFO)
        data_logger_handler.setFormatter(formatter)
        data_logger.addHandler(data_logger_handler)
        data_logger.info("Logger initiated")

        return data_logger

    # Method to Initiate Driver
    def initiate_driver(self):
        # Initiate driver
        s = Service("C:\\Users\\zelamay\\PycharmProjects\\pythonProject\\ChromeDriver\\chromedriver")
        page_driver = webdriver.Chrome(service=s)
        page_driver.maximize_window()
        self.logger.info("Driver initiated")

        return page_driver

    def get_data(self, page_driver):

        # Load Forebet Page and date/time page was loaded
        page_driver.get(self.url)
        time.sleep(5)

        current_time = time.strftime("%Y/%m/%d-%H:%M:%S")
        title = page_driver.title
        timed_title = current_time + " -- " + title

        webpage_types = ['Today', 'Tomorrow', 'Yesterday', 'Weekend', 'Finished']
        save_name = 'Other'
        for value in webpage_types:
            if value in title:
                save_name = value

        # Data logger title
        self.logger.info("Page loaded: " + timed_title)
        current_time = current_time.replace("/", "-").replace(":", "-")
        data_name_to_save = save_name + " " + current_time + ".csv"
        # data_name_to_save = data_save_path + data_name_to_save
        # data_logger.info("Data location: " + data_name_to_save)

        # OutPut Data
        data_column = ['Tag', 'Home Team', 'Away Team', 'Date', 'HPro', 'DPro', 'APro', 'HCor', 'ACor', 'AGol', 'Prog',
                       'HFull', 'AFull', 'Link']
        matches_dataframe = pd.DataFrame()
        self.logger.info("Dataframe created...")

        # Get all matches from the page
        matches_container = page_driver.find_element(By.CLASS_NAME, "schema")
        games = matches_container.find_elements(By.XPATH, "*")
        for each_game in games:
            each_game_detail = each_game.find_elements(By.XPATH, "*")
            temporary_list = []
            try:
                if each_game_detail is not None and len(each_game_detail) >= 4:

                    # GETTING Tag
                    game_tag = each_game_detail[0].text

                    # GETTING Home Team, Away Team, Game Date/Time, Link Address
                    link_div = each_game_detail[1].find_element(By.XPATH, "*").find_element(By.TAG_NAME, 'a')
                    link_address = link_div.get_attribute('href')
                    home_team = each_game_detail[1].text.partition('\n')[0]
                    away_team, game_date_time = each_game_detail[1].text.partition('\n')[2].split('\n')

                    # GETTING Probability
                    probability_text = each_game_detail[2].text
                    home_probability = probability_text[:2]
                    draw_probability = probability_text[2:4]
                    away_probability = probability_text[4:6]

                    # GETTING Correct Score
                    correct_score = each_game_detail[4].text
                    home_correct, _, away_correct = correct_score.partition(' - ')

                    # GETTING Average Goals
                    average_goals = each_game_detail[5].text

                    # GETTING Match Progress/Result if available
                    try:
                        match_progress = each_game_detail[8].text
                        match_result_full = each_game_detail[9].text.partition('\n')[0]
                        home_full = match_result_full.partition(' - ')[0]
                        away_full = match_result_full.partition(' - ')[2]

                        if match_progress != 'FT':
                            match_progress = re.findall(r'\d+', match_progress)
                            match_progress = match_progress.pop()
                        else:
                            pass

                        home_full = int(home_full)
                        away_full = int(away_full)

                    except IndexError or ValueError:
                        match_progress = '-'
                        home_full = away_full = -1

                    # CASTING OUTPUTS

                    # 1 casting date/time
                    try:
                        formatted_date_time = datetime.strptime(game_date_time, "%d/%m/%Y %H:%M")
                    except ValueError:
                        formatted_date_time = -1

                    # 2 casting probability
                    try:
                        home_probability = int(home_probability)
                        draw_probability = int(draw_probability)
                        away_probability = int(away_probability)
                    except ValueError:
                        home_probability = draw_probability = away_probability = -1

                    # 4 casting correct score
                    try:
                        home_correct = int(home_correct)
                        away_correct = int(away_correct)
                        average_goals = float(average_goals)
                    except ValueError:
                        home_correct = away_correct = average_goals = -1

                    # APPENDING TO TEMPORARY LIST
                    temporary_list.append(game_tag)
                    temporary_list.append(home_team)
                    temporary_list.append(away_team)
                    temporary_list.append(formatted_date_time)
                    temporary_list.append(home_probability)
                    temporary_list.append(draw_probability)
                    temporary_list.append(away_probability)
                    temporary_list.append(home_correct)
                    temporary_list.append(away_correct)
                    temporary_list.append(average_goals)
                    temporary_list.append(match_progress)
                    temporary_list.append(home_full)
                    temporary_list.append(away_full)
                    temporary_list.append(link_address)

                    # APPENDING TO DATAFRAME
                    self.logger.info("-" * 50)
                    self.logger.info(temporary_list)
                    match_series = pd.Series(temporary_list)
                    matches_dataframe = pd.concat([matches_dataframe, pd.DataFrame(match_series)], axis=1,
                                                  ignore_index=True)
                else:
                    self.logger.error("-" * 50)
                    self.logger.error("ERROR DETECT - No Game Details")  # ERROR DETECT - No Game Details
                    self.logger.error("+" * 50)
                    self.logger.error(each_game.text)  # printing game details
                    self.logger.error("+" * 50)
                    continue
            except Exception as e:
                self.logger.error("-" * 50)
                self.logger.error("ERROR DETECT - EXCEPTION")
                self.logger.error("+" * 50)
                self.logger.error(each_game.text)
                self.logger.error("+" * 50)
                self.logger.error("Error: ")
                self.logger.error(traceback.format_exc())
                self.logger.error("printing game details")
                self.logger.error("-" * 50)
                continue

        return matches_dataframe


# Class for getting stats from each match string

class MatchStats:
    def __init__(self, default_timeout=3,
                 database_folder="C:\\Users\\zelamay\\PycharmProjects\\pythonProject\\Outputs\\",
                 database_name="Today"):

        # Initiating logger
        data_logger = logging.getLogger('links logger')
        data_logger.setLevel(logging.INFO)  # INFO, DEBUG, WARNING, ERROR, CRITICAL
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        stdout_handler.setFormatter(formatter)
        data_logger.addHandler(stdout_handler)

        data_logger_handler = logging.FileHandler('links.log')
        data_logger_handler.setLevel(logging.INFO)
        data_logger_handler.setFormatter(formatter)
        data_logger.addHandler(data_logger_handler)
        data_logger.info("Logger initiated")
        self.logger = data_logger
        self.logger.info("Logger initiated")

        # Initiating default timeout
        self.default_timeout = default_timeout
        self.logger.info("Default timeout set to: " + str(default_timeout))

        # Initiating database folder
        self.database_folder = database_folder
        self.logger.info("Database folder set to: " + str(database_folder))

        # Initiating database name
        self.database_requested = database_name
        self.logger.info("Database name set to: " + str(database_name))

    def get_latest_csv(self):

        # Get all files in folder with .csv extension
        all_files = glob.glob(self.database_folder + "/*.csv")

        all_date_times = {}
        for each_file in all_files:

            csv_name = each_file.split('\\')[-1]
            first_word = csv_name.split()[0]

            if first_word == self.database_requested:
                last_word = csv_name.split()[-1][:-4]
                temp_date_time = datetime.strptime(last_word, '%Y-%m-%d-%H-%M-%S')

                all_date_times[temp_date_time] = each_file
            else:
                continue
        try:
            date_loaded = max(all_date_times.keys())
            csv_file_path = all_date_times[date_loaded]
            dataframe = pd.read_csv(csv_file_path)
        except Exception:
            dataframe = pd.DataFrame()
            date_loaded = ''
            self.logger.error("-" * 50)
            self.logger.error("COULD NOT LOAD DATAFRAME")
            self.logger.error("RETURNING EMPTY DATAFRAME")
            self.logger.error(traceback.format_exc())
            print("Error in reading csv file")

        return date_loaded, dataframe

    def get_stat_from_match_dataframe(self, match_dataframe: pd.DataFrame):

        if match_dataframe.empty:
            self.logger.info("No Dataframe: Returning empty dataframe")
            return pd.DataFrame()
        elif match_dataframe is None:
            self.logger.info("No Dataframe: Returning empty dataframe")
            return pd.DataFrame()

        # Initiate driver
        self.logger.info("Initiating driver")
        page_driver = webdriver.Chrome()
        page_driver.maximize_window()
        page_driver.set_page_load_timeout(self.default_timeout)
        self.logger.info("Driver initiated")
        self.logger.info("Going through each row in dataframe")

        for index, each_row in match_dataframe.iterrows():
            original_raw = each_row.tolist()
            link_address = original_raw[-1]
            game_tag = original_raw[0]
            home_team = original_raw[1]
            away_team = original_raw[2]
            self.logger.info("-" * 50)
            self.logger.info("Link address: " + str(link_address))
            try:
                page_driver.get(link_address)
            except TimeoutException:
                page_driver.execute_script("window.stop();")
                self.logger.info("Page loaded via timeout")

            # Get data from the page
            self.logger.info("Fetching data from page")
            try:
                standing_table, head_table, home_table, away_table, result_home, result_away, progress = self.get_data_from_page(
                    page_driver=page_driver)
            except:
                self.logger.info("ERROR LOADING - MOVING ON ...")
                continue
            self.logger.info("Data fetched from page")
            self.logger.info("Standing Table Empty: " + str(not standing_table.empty))
            self.logger.info("Head Table Empty: " + str(not head_table.empty))
            self.logger.info("Home Table Empty: " + str(not home_table.empty))
            self.logger.info("Away Table Empty: " + str(not away_table.empty))
            self.logger.info("Result Home: " + str(result_home))
            self.logger.info("Result Away: " + str(result_away))
            self.logger.info("Progress: " + str(progress))

            self.process_data(standing=standing_table, home_t=home_table, away_t=away_table,
                              home_name=home_team, away_name=away_team, tag=game_tag)

            break
        return None

    def get_data_from_page(self, page_driver):

        title = page_driver.title
        match_tag = page_driver.find_element(By.CLASS_NAME, 'shortTag').text
        self.logger.info("Title: " + str(title))
        self.logger.info("Match Tag: " + str(match_tag))

        result_home, result_away, progress = self.get_progress_and_result(page_driver=page_driver)

        standing_table = head_to_head_matches = home_matches = away_matches = pd.DataFrame()

        # Get All classes with name 'mptlt'
        mptlt_classes = page_driver.find_elements(By.CLASS_NAME, 'mptlt')
        for children in mptlt_classes:
            children_text = children.text

            if children_text == '':
                continue
            elif 'STANDINGS' in children_text:
                standing_table = self.fetch_standing_table(children)
            elif children_text == 'HEAD TO HEAD':
                head_to_head_matches = self.fetch_one_o_one_matches(children)
            elif ' 6 ' in children_text:
                home_matches, away_matches = self.fetch_home_away_matches(children)
            else:
                continue

        return standing_table, head_to_head_matches, home_matches, away_matches, result_home, result_away, progress

    def fetch_standing_table(self, children: WebElement):
        standing_columns = ['Rank', 'Team', 'PTS', 'GP', 'W', 'D', 'L', 'GF', 'GA', 'diff']
        if children is None:
            return pd.DataFrame()

        parent_element = children.find_element(By.XPATH, '..')
        # print(parent_element.text)
        all_children = parent_element.find_elements(By.XPATH, '*')
        tables_fetched = []

        for each_child in reversed(all_children):
            child_text = each_child.text

            if child_text == 'View all':
                each_child.click()
                time.sleep(self.default_timeout)
                continue

            if "STANDING" in child_text or '' == child_text:
                continue

            children_raw = each_child.find_elements(By.TAG_NAME, 'table')

            for children_raw_each in children_raw:
                tables_as_list = pd.read_html(children_raw_each.get_attribute('outerHTML'))
                tables_fetched.append(tables_as_list[0])

        standing_dataframe = pd.concat(tables_fetched, ignore_index=True)
        standing_dataframe.columns = standing_columns

        return standing_dataframe

    def fetch_one_o_one_matches(self, children: WebElement):
        if children is None:
            return pd.DataFrame()

        one_o_one_columns = ['Date', 'Home', 'Home_Score', 'Away_Score', 'Away', 'Tag']
        one_o_one_output = pd.DataFrame(columns=one_o_one_columns)

        # Get Super-Parent and Children
        parent_element = children.find_element(By.XPATH, '..')
        all_children = parent_element.find_elements(By.XPATH, '*')

        one_o_one_list = []

        # Go through children
        for each_child in all_children:
            child_text = each_child.text

            # Ignoring the first child
            if child_text == "HEAD TO HEAD":
                continue

            # Getting all the sub children of the second child of the Super-Parent
            # Containing both VISIBLE and HIDDEN data
            one_o_one_list = self.interior_extractor(each_child)
        # Cleaning list inputs
        for list_one in one_o_one_list:
            date_time = list_one[0] + '/' + list_one[1]
            date_time = datetime.strptime(date_time, '%d/%m/%Y')

            home_index = list_one[2].rfind(' - ')
            home_team = list_one[2][:home_index - 2]
            scores = list_one[2][home_index - 2:]
            home_score, _, away_score = scores.partition('-')

            away_index = list_one[4].rfind(' ')
            away_team = list_one[4][:away_index]
            match_tag = list_one[4][away_index:]

            one_o_one_output = pd.concat([one_o_one_output, pd.DataFrame([[date_time, home_team, home_score, away_score,
                                                                           away_team, match_tag]],
                                                                         columns=one_o_one_columns)])

        return one_o_one_output

    def interior_extractor(self, internal_children: WebElement):
        extracted_games = []

        all_rows = internal_children.find_elements(By.XPATH, '*')
        for _a_game in reversed(all_rows):
            raw_text = _a_game.text

            # Check if there are HIDDEN DATA - if there is click() to reveal and move on
            if raw_text == 'View all':
                _a_game.click()
                time.sleep(self.default_timeout)
                continue

            # Clean fetched data for empty and irrelevant data
            elif 'All' in raw_text or raw_text == '' or 'Draw' in raw_text:
                continue

            # Go through all VISIBLE and HIDDEN(if there is one)
            for _raw in _a_game.find_elements(By.XPATH, '*'):

                # Get attribute to check if data is HIDDEN or not
                attribute_name = _raw.get_attribute('class')

                # If HIDDEN(NOW REVEALED) break data
                if attribute_name == 'hidd_stat':
                    hidden_raw = _raw.find_elements(By.XPATH, '*')

                    for _hidden in hidden_raw:
                        # print('+' * 50)
                        extracted_games.append(_hidden.text.split('\n'))
                        # print('+' * 50)
                else:
                    # print('-' * 50)
                    extracted_games.append(_raw.text.split('\n'))
                    # print(_raw.text)
                    # print("-" * 50)
        return extracted_games

    def fetch_home_away_matches(self, children):

        parent_one = children.find_element(By.XPATH, '..')
        parent_two = parent_one.find_element(By.XPATH, '..')
        next_sibling = parent_two.find_element(By.XPATH, "following-sibling::*[1]")
        howe_team_table = next_sibling.find_elements(By.XPATH, '*')

        home_table = howe_team_table[0].find_element(By.XPATH, '*').find_elements(By.XPATH, '*')[1]
        away_table = howe_team_table[1].find_element(By.XPATH, '*').find_elements(By.XPATH, '*')[1]

        home_games = self.interior_extractor(home_table)
        home_games = self.clean_list_to_dataframe(home_games)

        away_games = self.interior_extractor(away_table)
        away_games = self.clean_list_to_dataframe(away_games)
        return home_games, away_games

    def clean_list_to_dataframe(self, home_games):

        one_o_one_columns = ['Date', 'Home', 'Home_Score', 'Away_Score', 'Away', 'Tag']
        one_o_one_output = pd.DataFrame(columns=one_o_one_columns)

        for list_one in home_games:
            date_time = list_one[0] + '/' + list_one[1]
            date_time = datetime.strptime(date_time, '%d/%m/%Y')

            home_index = list_one[2].rfind(' - ')
            home_team = list_one[2][:home_index - 2]
            scores = list_one[2][home_index - 2:]
            home_score, _, away_score = scores.partition('-')

            away_index = list_one[4].rfind(' ')
            away_team = list_one[4][:away_index]
            match_tag = list_one[4][away_index:]

            one_o_one_output = pd.concat([one_o_one_output, pd.DataFrame([[date_time, home_team, home_score, away_score,
                                                                           away_team, match_tag]],
                                                                         columns=one_o_one_columns)])
        return one_o_one_output

    def get_progress_and_result(self, page_driver):
        try:
            result_xpath = '//*[@id="1x2_table"]/div[3]/div[9]/div/span'
            profress_xpath = '//*[@id="1x2_table"]/div[3]/div[10]/span[1]/b'
            progress = page_driver.find_element(By.XPATH, result_xpath).text
            result = page_driver.find_element(By.XPATH, profress_xpath).text
            result_home, _, result_away = result.partition(' - ')
            result_home = int(result_home)
            result_away = int(result_away)
        except Exception:
            result_home = -1
            result_away = -1
            progress = -1

        return result_home, result_away, progress

    def excute(self, use_degalut=True):

        # Getting the latest csv file with correct type
        self.logger.info('Getting the latest csv file with correct type')
        date_csv, latest_csv = self.get_latest_csv()
        self.logger.info(f'Latest csv file is {date_csv}')

        # Extracting data from csv's links
        self.logger.info('Extracting data from csv\'s links')
        self.get_stat_from_match_dataframe(match_dataframe=latest_csv)

    def process_data(self, standing, home_t, away_t, home_name, away_name, tag):

        home_object = TEAM(team_name=home_name, team_mood=1)
        away_object = TEAM(team_name=away_name, team_mood=2)

        home_object = self.populate(home_object, standing)
        away_object = self.populate(away_object, standing)

        # total team in standing
        max_team = standing.index.values.max()

        # Filter based on Tag
        home_t = home_t[home_t["Tag"] == " " + tag]
        home_t = home_t.head(home_object.get_GP())

        away_t = away_t[away_t["Tag"] == " " + tag]
        away_t = away_t.head(away_object.get_GP())
        # away_set_filtered = away_set_filtered.head(away_object.get_GP())

        # Go through Home
        conta = []
        for indicator, set in home_t.iterrows():
            if set["Home"] == home_name:
                opponent_object = TEAM(team_name=set["Away"])
                opponent_object = self.populate(opponent_object, standing)
                match_object = MATCH(primary_team=home_object, secondary_team=opponent_object,
                                     match_order=1,p_score=set["Home_Score"], s_score=set["Away_Score"])
                print("_______")
                print(match_object.get_primary_team())
                print((match_object.get_secondary_team()))
                print(match_object.get_rank_difference())
                print(match_object.get_goal_difference())
                print(match_object.get_GP_difference())
                print(match_object.get_PTS_difference())
                print("/////////////////////")
            else:
                print("seconday")
                print(set["Home"])
                opponent_object = TEAM(team_name=set["Home"])
                opponent_object = self.populate(opponent_object, standing)
                # match_object = MATCH(primary_team=H`)

        print("/" * 85)
        print(standing)
        print("-" * 50)
        print(home_t)
        print("-" * 50)
        print(away_t)
        print("-" * 50)

        return

    def populate(self, team_object: TEAM, stans: pandas.DataFrame):

        for i, r_row in stans.iterrows():
            if r_row["Team"] == str(team_object):
                team_object.add_PTS(pts=int(r_row["PTS"]))
                team_object.add_rank(rank=int(r_row["Rank"]))
                team_object.add_GP(gp=int(r_row["GP"]))
                team_object.add_W(w=int(r_row["W"]))
                team_object.add_D(d=int(r_row["D"]))
                team_object.add_L(l=int(r_row["L"]))
                team_object.add_GF(gf=int(r_row["GF"]))
                team_object.add_GA(ga=int(r_row["GA"]))
                team_object.add_GD(gd=int(r_row["diff"]))
                continue

        return team_object


oo = MatchStats()
oo.excute()

# kk = List_Matches(page_type='today')

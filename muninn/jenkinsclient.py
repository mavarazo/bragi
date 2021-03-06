from dataclasses import dataclass
from logging import Logger
from typing import Tuple

import requests


@dataclass
class Job:
    name: str
    url: str
    healthy: bool
    status: bool


class JenkinsClient:

    API_PREFIX = '/api/json?pretty=true'

    def __init__(self, logger:Logger, username:str, token:str):
        self.logger = logger
        self.JENKINS_USERNAME = username
        self.JENKINS_TOKEN = token

    def fetch(self, job:Job):
        api = job.url + self.API_PREFIX
        self.response = self.__urlopen(api)

    def get_health(self) -> Tuple[bool, bool]:
        if self.response is None:
            return None

        last_build_number = self.__get_build_number_or_zero(self.response['lastBuild'])
        last_successful_build_number = self.__get_build_number_or_zero(self.response['lastSuccessfulBuild'])
        last_failed_build_number = self.__get_build_number_or_zero(self.response['lastFailedBuild'])

        return last_successful_build_number > last_failed_build_number and last_build_number != last_failed_build_number


    def get_status(self) -> bool:
        if self.response is None:
            return None

        last_build_number = self.__get_build_number_or_zero(self.response['lastBuild'])
        last_failed_build_number = self.__get_build_number_or_zero(self.response['lastFailedBuild'])

        return last_build_number != last_failed_build_number


    def __urlopen(self, url) -> dict:
        try:
            response = requests.get(url, auth=(self.JENKINS_USERNAME, self.JENKINS_TOKEN))
            if response.status_code == 401:
                self.logger.error(f"{response.status_code}: unauthorized ({self.JENKINS_USERNAME}/{self.JENKINS_TOKEN})")
                return None

            if response.status_code != 200:
                self.logger.error(f"{response.status_code}: not available")
                return None
            
            return response.json()
        except (requests.ConnectionError, requests.HTTPError) as e:
            self.logger.error(e)
            return None


    def __get_build_number_or_zero(self, last_build) -> int:
        number = 0
        if last_build and 'number' in last_build:
            number = last_build['number']
        return number

import os
import logging
from time import sleep

from git import Repo
from github import Github
from datetime import datetime

CLONING_REPO_PATH = './tmp'
GITHUB_URL = 'https://github.com'
GITHUB_API_TOKEN = 'ghp_TOKEN'


# producer task
def mine_gh_api(queue, range_stars, database_client):
    """
    Mine the GitHub API for repositories
    :param queue: Consumer queue
    :param range_stars: Range of stars to mine (Some may include dates)
    :param database_client: Database client
    :return: None
    """
    # Get the collection reference for repositories
    db_collection_repos = database_client.collection(u'repos')

    # Initialize the GitHub object
    g = Github(GITHUB_API_TOKEN)
    # Define the query - range of stars: 0..10, 11..20, 21..30, ... date_start..date_end and language: Python, Java
    query = f'{range_stars} language:"Python" language:"Java"'
    # try to trigger the request
    try:
        # verify rate limit in order to avoid GitHub API rate limit, it will sleep
        api_wait_search(g)
        # trigger the request with the query
        repositories_req = g.search_repositories(query, sort='stars', order='desc')
        # get the total count of page 0 (this should be the total count of the query)
        repositories_req.get_page(0)
        # get the total count of the query
        total_count = repositories_req.totalCount
        # Validate that there are more than 0 results
        if total_count > 0:
            # if the total count is lower than TOTAL_COUNT, we evaluate the repositories
            for repo in repositories_req:
                # check if the repository is already in the database
                repo_ref = db_collection_repos.document(repo.full_name.replace("/", "__")).get()
                if repo_ref.exists:
                    # if the repository already exists, skip it
                    continue
                else:
                    # clone the repository
                    path = clone_repository(repo.full_name)
                    # Check if the repository has been cloned
                    if path is not None:
                        # Define a tuple with the path and the language
                        info_repo = (path, repo.language.lower(), repo.full_name)
                        # add the repository to the queue
                        queue.put(info_repo)
                    else:
                        logging.error(f'{repo.full_name} has not been cloned')

            queue.put(None)
            logging.info('Producer finished - No more repositories to process')
        else:
            logging.info(f'No results for query: {query}')
            pass
    except Exception as e:
        logging.exception(f'Error while requesting the GitHub API: {e}')
        pass


def clone_repository(full_name):
    """
    Clone the repository from GitHub and return the path of the cloned repository
    :param full_name: Name of the repository including the owner
    :return: destination path of the cloned repository, if it does not exist it will return None
    """
    try:
        # Get the owner and the repository name and create the destination path
        destination_path = f'{CLONING_REPO_PATH}/{full_name.replace("/", "__")}'
        # Check if the repository already exists
        if not os.path.exists(destination_path):
            # Clone the repository if it does not exist
            Repo.clone_from(f'{GITHUB_URL}/{full_name}.git', destination_path)
            logging.info(f'{full_name} has been cloned')
            # return the path of the cloned repository
            return destination_path
        # If the repository already exists, return the path
        else:
            logging.info(f'{full_name} already exists')
            # return the path of the cloned repository
            return destination_path
    except Exception as e:
        # Log the error
        logging.exception(f'{full_name} has not been cloned')
        logging.exception(e)
        # return None because the repository has not been cloned
        return None


def api_wait_search(git):
    """
    Wait for the GitHub API to be available
    :param git: A GitHub object
    :return: None
    """
    # Get the rate limit
    limits = git.get_rate_limit()
    # If the remaining requests is 2 or less, wait for the reset time
    if limits.search.remaining <= 2:
        # Get the reset time in seconds
        seconds = (limits.search.reset - datetime.now()).total_seconds()
        print(f'Waiting for {seconds} seconds')
        logging.info(f'Waiting {seconds} seconds for the GitHub API')
        # Sleep and wait for the reset time
        sleep(seconds)
        logging.info('GitHub API ready')

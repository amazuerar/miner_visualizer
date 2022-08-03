import argparse
import shutil

import firebase_admin
from queue import Queue
from threading import Thread
from Inspector import Extractor
from Inspector import Processor
from datetime import timedelta, datetime
from firebase_admin import credentials, firestore
CLONING_REPO_PATH = './tmp'


def range_stars(start, stop, step):
    """
    Create a list of stars ranges and dates if needed
    :param start: start of the range
    :param stop: end of the range
    :param step: step of the range
    :return: list of stars ranges and dates when needed
    """

    # create a list of stars ranges
    star_range = []

    # Define the start and end date, start date is when github was founded (i.e., 2008)
    start_date = datetime(2008, 2, 8)
    # end date is today
    end_date = datetime.today()

    # yield the date range
    def date_range():
        """
        Yield the date range
        :return:
        """
        # for each date in the range
        for n in range(int((end_date - start_date).days)):
            # yield the date
            yield start_date + timedelta(n)

    # for each date in the range
    for single_date in date_range():
        # get the date in the format of YYYY-MM-DD
        star_range.append(f'stars:{1}..{start} created:{single_date.strftime("%Y-%m-%d")}')

    # iterate in star range
    for i in range(start, stop, step):
        # append the star range to the list
        star_range.append(f'stars:{i}..{i + step}')
        # when the star range is bigger than the upper bound
        if i + step >= stop:
            # append the open star range to the list
            star_range.append(f'stars:>{i + step}')

    # return reversed list of stars ranges because we want to start from the most popular
    return star_range[::-1]


def main():
    """
    Main function it contain the definition of the arguments and the main loop
    :return: None
    """
    parser = argparse.ArgumentParser(description='Extractor and Processor for most popular Java and Python repositories')
    parser.add_argument('-l', '--lower_bound', required=False, help='Lower bound of the range of stars', type=int, default=300)
    parser.add_argument('-u', '--upper_bound', required=False, help='Upper bound of the range of stars', type=int, default=6000)
    parser.add_argument('-s', '--step', required=False, help='Step of the range of stars', type=int, default=10)
    parser.add_argument('-j', '--java_parser', required=False, help='Select parser', type=str, default='javalang')
    args = parser.parse_args()

    ran_stars = range_stars(args.lower_bound, args.upper_bound, args.step)

    for ran_star in ran_stars:
        try:
            # create the shared queue
            queue = Queue(maxsize=10)
            # start the processor threads
            processors = [Thread(target=Processor.process_repo, args=(queue, i, args.java_parser, database_client)) for i in range(2)]
            for processor in processors:
                processor.start()
            # start the extractor thread
            extractor = Thread(target=Extractor.mine_gh_api, args=(queue, ran_star, database_client))
            extractor.start()
            # wait for all threads to finish
            extractor.join()
            for processor in processors:
                processor.join()
        except Exception as e:
            print(e)
            continue
        finally:
            shutil.rmtree(CLONING_REPO_PATH)


# call main function
if __name__ == '__main__':
    # Initialize Firebase credentials
    cred = credentials.Certificate("./api_key.json")
    # Initialize Firebase app
    firebase_admin.initialize_app(cred)
    # Get firestore client
    database_client = firestore.client()
    # Init extraction and processing
    main()


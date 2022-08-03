# consumer task
import shutil
from time import sleep
from firebase_admin import firestore
from Inspector import Parser


def process_repo(q, identifier, java_parser, database_client):
    """
    Function in order to process the repositories
    :param java_parser: selector parser
    :param q: The queue
    :param identifier: identifier of the thread
    :param database_client: database client object
    :return: None
    """

    # Get the collection reference for words
    db_collection_words = database_client.collection(u'words')
    # Get the collection reference for repositories
    db_collection_repos = database_client.collection(u'repos')
    # Open batch for updates words
    batch = database_client.batch()

    print(f'Consumer {identifier}: Running')
    # While the queue is not empty it continues to process the repositories
    while True:
        # get a unit of work, meaning the repository path
        item = q.get()
        # check for stop
        if item is None:
            # add the signal back for other consumers
            q.put(item)
            # stop running
            break
        # if the item is not None, we have a repository path
        # get the path of the repository
        path = item[0]
        # get the language of the repository
        language = item[1]

        # try to parse the repository
        try:
            # Get dictionary with the new words to be added
            word_dict = dict(Parser.parse_repository_given_language(path, language, java_parser))

            # if the dictionary is not empty
            if len(word_dict) > 0:
                # iterate through the dictionary
                for k, v in word_dict.items():
                    # check if the word is already in the database
                    doc_ref = db_collection_words.document(k).get()
                    # Update the word based on the language
                    match language:
                        case 'python':
                            # if the word is in the database, update the word
                            if doc_ref.exists:
                                batch.update(db_collection_words.document(k),
                                             {'value': firestore.Increment(v),
                                              'python_value': firestore.Increment(v)})
                            # if the word is not in the database, create the word
                            else:
                                batch.set(db_collection_words.document(k),
                                          {'name': k, 'value': v, 'python_value': v, 'java_value': 0})
                        case 'java':
                            # if the word is in the database, update the word
                            if doc_ref.exists:
                                batch.update(db_collection_words.document(k),
                                             {'value': firestore.Increment(v),
                                              'java_value': firestore.Increment(v)})
                            # if the word is not in the database, create the word
                            else:
                                batch.set(db_collection_words.document(k),
                                          {'name': k, 'value': v, 'java_value': v, 'python_value': 0})
                        case _:
                            continue

                    # add repository to the database in order to set the mined flag to true
                    batch.set(db_collection_repos.document(item[2].replace("/", "__")), {'name': item[2], 'cloned': True, 'words': True, 'language': language})
                    # commit the batch
                    batch.commit()
            else:
                # add repository to the database in order to set the mined flag to true
                batch.set(db_collection_repos.document(item[2].replace("/", "__")), {'name': item[2], 'cloned': True, 'words': False, 'language': language})
                # commit the batch
                batch.commit()
                print("*" * 100)
                print(f"Consumer {identifier} is done with {item[0]}")
                print("*" * 100)
        finally:
            # delete the repository
            delete_repository(f'{path}/')
            pass


def delete_repository(repo_path):
    """
    Function in order to delete the repository
    :param repo_path: repository path
    :return: None
    """
    shutil.rmtree(repo_path)

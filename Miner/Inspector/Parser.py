import ast
import glob
import io
import logging
import os
import re
import subprocess

import javalang
import collections
from inflection import camelize
from inflection import underscore


def parse_repository_given_language(repository_folder_path, language, java_parser):
    """
    Parse a repository and return a list of all the functions in the repository
    :param java_parser: java parser to use
    :param repository_folder_path: path to the repository folder
    :param language: language of the files to parse
    :return: list of functions
    """
    # Verify if the repository folder exists
    if os.path.isdir(repository_folder_path):
        match language:
            case "python":
                return parse_repository_given_extension(repository_folder_path, ".py", None)
            case "java":
                return parse_repository_given_extension(repository_folder_path, ".java", java_parser)
            case _:
                return "Unknown language"
    else:
        return "No repository found"


def parse_repository_given_extension(repository_folder_path, extension, java_parser):
    """
    Parse a repository and return a list of all the functions in the repository
    :param java_parser: java parser to use
    :param repository_folder_path: path to the repository folder
    :param extension: extension of the files to parse
    :return: list of functions
    """
    # Verify if the repository folder exists
    if os.path.isdir(repository_folder_path):
        # Get all files in the repository
        list_of_files = [file for file in glob.glob(f'{repository_folder_path}/**/*{extension}', recursive=True)]
        # Get all functions in the files
        list_of_words = []
        # Match the extension to the correct function
        match extension:
            case ".py":
                list_of_functions = []
                for file in list_of_files:
                    try:
                        # Get all functions in the file and append them to the list of functions (Python)
                        list_of_functions.extend(get_python_function_names(file))
                    except Exception as e:
                        pass
                for function_name in list_of_functions:
                    if is_snake_case(function_name):
                        list_of_words.extend(snake_case_split(function_name))
            case ".java":
                list_of_methods = []
                for file in list_of_files:
                    try:
                        # Get all functions in the file and append them to the list of functions (Java)
                        # select the correct parser
                        match java_parser:
                            case "javalang":
                                list_of_methods.extend(get_java_function_names_with_javalang(file))
                            case "srcml":
                                list_of_methods.extend(get_java_function_names_with_srcml(file))
                            case _:
                                return "Unknown java parser"
                    except javalang.parser.JavaSyntaxError:
                        pass
                for method_name in list_of_methods:
                    if is_camel_case(method_name):
                        list_of_words.extend(camel_case_split(method_name))
            case _:
                return "Unknown extension"
        # Return the list of words
        elements_count = collections.Counter(list_of_words)
        return elements_count
    else:
        return "No repository found"


def get_python_function_names(python_file):
    """
    Parse python source code with ast library and get function names
    :param python_file: path to the python file
    :return: list of function names
    """
    try:
        # Get source code from python file
        source_code = io.open(python_file, "r", encoding="utf-8")
        # Parse source code with ast library
        tree = ast.parse(source_code.read())

        # Get all function names
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    except Exception as e:
        logging.error(e)
        logging.error("Error parsing file: " + python_file)
        return []
    finally:
        source_code.close()


def get_java_function_names_with_javalang(java_file):
    """
    Parse Java source code with javalang library and get method names
    :param java_file: path to the java file
    :return: list of method names
    """
    try:
        # Get source code from java file
        source_code = io.open(java_file, "r", encoding="utf-8")
        # Parse source code with javalang library
        tree = javalang.parse.parse(source_code.read())
        # Get all method names
        return [node.name for path, node in tree.filter(javalang.tree.MethodDeclaration)]
    except Exception as e:
        print(e)
        logging.error("Error parsing file: " + java_file)
        return []
    finally:
        source_code.close()


def get_java_function_names_with_srcml(java_file):
    """
    Parse Java source code with srcml library and get method names
    :param java_file: path to the java file
    :return: list of method names
    """
    j_file = java_file
    x_file = java_file.replace(".java", ".xml")

    try:
        subprocess.run(f"srcml {j_file} -o  {x_file}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        xpath = subprocess.run(f"srcml --xpath '//src:function/src:name' {x_file}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        xpath_output = xpath.stdout.decode("utf-8")
        matches = re.findall(r'<name>(.+)</name>', xpath_output)
        return matches
    except Exception as e:
        print(e)
        logging.error("Error parsing file: " + java_file)
        return []


def is_camel_case(function_name):
    """
    Check if a function name is in camel case
    :param function_name: function name to check
    :return: True if the function name is in camel case, False otherwise
    """
    return function_name == camelize(function_name, False)


def is_snake_case(function_name):
    """
    Check if a function name is in snake case
    :param function_name: function name to check
    :return: True if the function name is in snake case, False otherwise
    """
    return function_name == underscore(function_name)


def camel_case_split(function_name):
    """
    Split a camel case function name into words
    :param function_name: function name to split
    :return: list of words in lowercase
    """
    # regex to split camel case function name
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', function_name)
    # return list with matches
    return [m.group(0).lower() for m in matches]


def snake_case_split(function_name):
    """
    Split a snake case function name into words
    :param function_name: function name to split
    :return: list of words in lowercase
    """
    # Split the function name into words
    # filtering out empty strings
    # lambda function to lowercase the words
    return map(lambda x: x.lower(), list(filter(None, function_name.split("_"))))


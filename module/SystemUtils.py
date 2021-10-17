from sys import stderr
from os import _exit as exit
from signal import SIGINT, signal


def sigintEvent(sig, frame):
    print('You pressed CTRL + C')
    exit(0)


signal(SIGINT, sigintEvent)


def error(message):
    """
    Throw an error message and then halt the script.
    :param message: A string that will be printed out to STDERR before exiting the script.
    """

    # Append our message with a newline character.
    stderr.write('[ERROR]: {0}\n'.format(message))

    # Halt the script right here, do not continue running the script after this point.
    exit(1)


def warn(message):
    """
    Throw a warning message without halting the script.
    :param message: A string that will be printed out to STDERR.
    """

    # Append our message with a newline character.
    stderr.write('[WARN] {0}\n'.format(message))

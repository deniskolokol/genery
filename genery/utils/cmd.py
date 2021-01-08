# -*- coding: utf-8 -*-

"""Command line and file operations."""

import subprocess
import tempfile
import errno
from contextlib import contextmanager


class CommandLineError(Exception):
    """
    The traceback of all CommandLineError's is supressed
    when the errors occur on the command line to provide
    a useful command line interface.
    """
    def render(self, msg):
        return msg % vars(self)


class MissingCommandException(CommandLineError):
    pass


class ShellError(CommandLineError):
    """
    Raised when a shell.run returns a non-zero exit code
    (i.e. command failed).
    """
    def __init__(self, command, exit_code, stdout, stderr):
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.executable = self.command.split()[0]

    def failed_message(self):
        return (
            "The command `%(command)s` failed with exit code %(exit_code)d\n"
            "------------- stdout -------------\n"
            "%(stdout)s"
            "------------- stderr -------------\n"
            "%(stderr)s"
        ) % vars(self)

    def render(self, msg):
        return msg % vars(self)

    def __str__(self):
        return self.failed_message()


def runcmd(*cmd, **kwargs):
    stdin = kwargs.get('stdin', None)
    try:
        pipe = subprocess.Popen(
            cmd,
            stdin=stdin,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except OSError as e:
        if e.errno == errno.ENOENT:
            # File not found.
            # This is equivalent to getting exitcode 127 from sh
            raise MissingCommandException(cmd[0])

    # pipe.wait() ends up hanging on large files. using
    # pipe.communicate appears to avoid this issue.
    stdout, stderr = pipe.communicate()

    if pipe.returncode != 0:
        raise ShellError(' '.join(cmd), pipe.returncode, stdout, stderr)

    return stdout


@contextmanager
def as_file(bytes_):
    """
    Yields a filename for a tempfile created from bytes.
    Useful when reading content from a certain URL.
    """
    with tempfile.NamedTemporaryFile() as tfile:
        tfile.write(bytes_)
        yield tfile.name

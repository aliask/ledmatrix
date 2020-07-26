#!/usr/bin/env python3
# Spinner to show progress on the CLI

import itertools, sys

class Spinner:

    currently_displayed = ''

    def spin(self):
        if(self.currently_displayed):
            sys.stdout.write('\r')
            sys.stdout.write(' ' * len(self.currently_displayed.encode('UTF-8')))
            sys.stdout.write('\r')
        self.currently_displayed = next(self.looper)
        sys.stdout.write(self.currently_displayed)
        sys.stdout.flush()
        sys.stdout.write('\b' * len(self.currently_displayed.encode('UTF-8')))

    def __init__(self, states = None):
        if(not states):
            hour = ('🕐', '🕜')
            states = []
            for i in range(12):
                states.append(chr(ord(hour[0]) + i))
                states.append(chr(ord(hour[1]) + i))
        self.looper = itertools.cycle(states)
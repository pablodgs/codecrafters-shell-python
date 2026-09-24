#!/usr/bin/python

import readline, sys
readline.parse_and_bind("tab: complete")

class VolcabCompleter:
    def __init__(self,volcab):
        self.volcab = volcab

    def complete(self,text,state):
        results =  [x for x in self.volcab if x.startswith(text)] + [None]
        return results[state]

words = ['dog','cat','rabbit','bird','slug','snail']
completer = VolcabCompleter(words)

readline.set_completer(completer.complete)

line = sys.stdin.readline()
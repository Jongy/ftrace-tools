#!/usr/bin/python
#
# graph_viewer generates a nicer view from the output of function_graph tracer.
# I still haven't decided how it should go, though.

import sys


def prepare_trace(tracefile):
    with open(tracefile, "r") as f:
        tracelines = f.readlines()

    if tracelines[0] != "# tracer: function_graph\n":
        raise ValueError("Invalid trace file, please give me the /sys/kernel/debug/tracing/trace file of"
                         " function_graph tracer")

    # strip comment lines
    tracelines = filter(lambda l: not l.startswith('#'), tracelines)
    # strip non-trace lines
    tracelines = filter(lambda l: '|' in l, tracelines)
    # remove the timestamp columns and all sorts of whitespace
    return ''.join(map(lambda l: l.split('|', 1)[1].replace('\n', '').replace(' ', ''), tracelines))


class FunctionCall(object):
    def __init__(self, name, calls):
        self.name = name
        self.calls = calls

    def __repr__(self):
        return "FunctionCall({0.name!r}, {0.calls!r})".format(self)


def parse_trace(trace):
    if len(trace) == 0:
        return None

    cur_name, rest = trace.split("()", 1)
    if rest[0] == ';':
        # no descendants, but perhaps siblings
        more = parse_trace(rest[1:])
        return (FunctionCall(cur_name, ()), ) + (more if more else ())
    else:
        assert rest[0] == '{'
        level = 0
        # find my closing brace
        for i, c in enumerate(rest):
            if c == '{':
                level += 1
            elif c == '}':
                level -= 1
                if level == 0:
                    break
        more = parse_trace(rest[i+1:])
        return (FunctionCall(cur_name, parse_trace(rest[1:i])), ) + (more if more else ())


def print_indented(s, indent):
    print((' ' * indent) + s)


def print_trace(parsed, indent=0):
    assert type(parsed) is tuple
    for call in parsed:
        print_indented(call.name, indent)
        print_trace(call.calls, indent + 2)


def main():
    if len(sys.argv) != 2:
        print("usage: {} tracefile".format(sys.argv[0]))

    trace = prepare_trace(sys.argv[1])
    parsed = parse_trace(trace)
    print_trace(parsed)

if __name__ == "__main__":
    main()

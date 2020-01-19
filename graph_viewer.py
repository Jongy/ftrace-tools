#!/usr/bin/python
#
# graph_viewer generates a nicer view from the output of function_graph tracer.
# it generates an html page allowing convenient view of call graphs.

import sys
from io import StringIO


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


def print_trace(buf, parsed):
    assert type(parsed) is tuple
    for call in parsed:
        buf.write('<li><a class="expand">' + call.name + " ({})".format(len(call.calls)) + "</a><ul>")
        print_trace(buf, call.calls)
        buf.write("</ul></li>")


def main():
    if len(sys.argv) != 2:
        print("usage: {} tracefile".format(sys.argv[0]))

    trace = prepare_trace(sys.argv[1])
    parsed = parse_trace(trace)

    buf = StringIO()
    buf.write("<ul>")
    print_trace(buf, parsed)
    buf.write("</ul>")

    with open("graph_template.html", "r") as f:
        graph_template = f.read()

    with open("output.html", "w") as f:
        f.write(graph_template.replace("GRAPH_HTML", buf.getvalue()))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import bottle
import os
import re
import subprocess
import sys
import tempfile
import time

def log_query(query, dirname):
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    elif os.path.isfile(dirname):
        print("Expected directory, found file '{}'".format(dirname))
        return
    fname = str(hash(query)).replace("-", "M") + ".txt"
    fpath = os.path.join(dirname, fname)
    if not os.path.exists(fpath):
        with open(fpath, "w") as f:
            f.write(query)

def run_fptaylor(query):
    try:
        f = tempfile.NamedTemporaryFile(mode="w", delete=True)
        f.write(query)
        f.flush()
    
        cmd = "FPTaylor/fptaylor {}".format(f.name)
    
        t0 = time.time()
        p = subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err  = p.communicate(timeout=10)
        out = out.decode('utf-8')
        err = err.decode('utf-8')
        retcode = p.returncode
        elapsed = time.time() - t0

        if "Potential exception detected: Sqrt of negative number at:" in err:
            return "SQRT_RANGE"
        
        match = re.search(r"Bounds \(floating-point\): \[([^,]*), ([^,]*)\]", out)
        lower_bound = match.group(1)
        upper_bound = match.group(2)
    
        match = re.search(r"Absolute error \(exact\): ([^\n]*)", out)
        error = match.group(1)

    except subprocess.TimeoutExpired:
        return "TIMEOUT"
        
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("ERROR: Unable to run command")
        print("\nquery:")
        print(query)
        print("python exception:")
        print(e)
        print(exc_type, fname, exc_tb.tb_lineno)
        try:
            print("\ncommand output: {}".format(out))
        except:
            pass
        try:
            print("\ncommand error: {}".format(err))
        except:
            pass
        return "INVALID_INPUT"
    
    return {
        "lower" : float(lower_bound),
        "upper" : float(upper_bound),
        "error" : float(error),
        "time" : elapsed,
    }


DEFAULT = \
"""
<!doctype html>
<html>
<title>FPTaylor output</title>
<body>
<h1>Input query</h1>
<pre>
{query}
</pre>
<h1>FPTaylor output</h1>
<h2>Analysis</h2>
<p><b>Absolute</b>: {error}</p>
<p><b>Bound</b>: [{lower}, {upper}]</p>
<p>Analysis took {time:.2f}s</p>
<pre>
FPTaylor is available on <a href=https://github.com/soarlab/FPTaylor.git>GitHub</a>
</pre>
</body>
</html>
"""

TIMEOUT = \
"""
<!doctype html>
<html>
<title>FPTaylor timed out</title>
<body>
<h1>Input query</h1>
<pre>
{query}
</pre>
<h1>FPTaylor output</h1>
FPTaylor timed out.
<pre>
FPTaylor is available on <a href=https://github.com/soarlab/FPTaylor.git>GitHub</a>
</pre>
</body>
</html>
"""

SQRT_RANGE = \
"""
<!doctype html>
<html>
<title>Domain error</title>
<body>
<h1>Input query</h1>
<pre>
{query}
</pre>
<h1>FPTaylor output</h1>
FPTaylor found a possible square root of a negative number.
</body>
<pre>
FPTaylor is available on <a href=https://github.com/soarlab/FPTaylor.git>GitHub</a>
</pre>
</html>
"""

INVALID_INPUT = \
"""
<!doctype html>
<html>
<title>Possible invalid input</title>
<body>
<h1>Input query</h1>
<pre>
{query}
</pre>
<h1>FPTaylor output</h1>
Possible invalid input.
<pre>
FPTaylor is available on <a href=https://github.com/soarlab/FPTaylor.git>GitHub</a>
</pre>
</body>
</html>
"""



@bottle.get('/api')
def get_api():
    return run_fptaylor(bottle.request.query['input'])

@bottle.get('/run')
def get_run():
    query = bottle.request.query['input']
    log_query(query, "query-logs")
    res = run_fptaylor(query)
    if res == "SQRT_RANGE":
        output = SQRT_RANGE.format(query=query)
    elif res == "TIMEOUT":
        output = TIMEOUT.format(query=query)
    elif res == "INVALID_INPUT":
        output = INVALID_INPUT.format(query=query)
    else:
        output = DEFAULT.format(query=query, **res)
    return output

if __name__ == "__main__":
    bottle.run(host='127.0.0.1', port=8080)

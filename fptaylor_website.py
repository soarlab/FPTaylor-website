#!/usr/bin/env python3

import bottle
import os
import re
import subprocess
import sys
import tempfile
import time

def run_fptaylor(query):
    try:
        f = tempfile.NamedTemporaryFile(mode="w", delete=True)
        f.write(query)
        f.flush()
    
        cmd = "FPTaylor/fptaylor {}".format(f.name)
    
        t0 = time.time()
        p = subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err  = p.communicate()
        out = out.decode('utf-8')
        err = err.decode('utf-8')
        retcode = p.returncode
        elapsed = time.time() - t0
    
        match = re.search(r"Bounds \(floating-point\): \[([^,]*), ([^,]*)\]", out)
        lower_bound = match.group(1)
        upper_bound = match.group(2)
    
        match = re.search(r"Absolute error \(exact\): ([^\n]*)", out)
        error = match.group(1)
    
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
        return "Invalid Input"
    
    return {
        "lower" : float(lower_bound),
        "upper" : float(upper_bound),
        "error" : float(error),
        "time" : elapsed,
    }



@bottle.get('/api')
def get_api():
    return run_fptaylor(bottle.request.query['input'])

@bottle.get('/run')
def get_run():
    query = bottle.request.query['input']
    res = run_fptaylor(query)
    output = """
<!doctype html>
<html>
<title>FPTaylor output</title>
<body>
<h1>FPTaylor output</h1>
<pre>
{query}
</pre>
<h2>Analysis</h2>
<p><b>Absolute</b>: {error}</p>
<p><b>Bound</b>: [{lower}, {upper}]</p>
<p>Analysis took {time:.2f}s</p>
</body>
</html>
""".format(query=query, **res)
    return output

if __name__ == "__main__":
    bottle.run(host='nimbus.cs.utah.edu', port=8080)

import sys, os, subprocess, time, signal
os.chdir(r'd:\ProyectoIG\wallasAPI')
sys.path.insert(0, r'd:\ProyectoIG')

print("[TEST] Starting api_server.py via subprocess...")
proc = subprocess.Popen(
    [r'd:\ProyectoIG\venv\Scripts\python.exe', 'api_server.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    env={**os.environ, 'PYTHONPATH': r'd:\ProyectoIG'}
)

time.sleep(5)

# Check if still running
if proc.poll() is None:
    print("[TEST] Server is still running after 5s (good)")
    # Read whatever output is available
    try:
        out, _ = proc.communicate(timeout=2)
        if out:
            print("[OUTPUT]", out[:2000])
    except:
        proc.kill()
        out, _ = proc.communicate()
        if out:
            print("[OUTPUT after kill]", out[:2000])
else:
    out, _ = proc.communicate()
    print(f"[TEST] Server exited early with code {proc.returncode}")
    print("[OUTPUT]", out[:4000])

# this scripts installs necessary requirements and launches main program in webui.py
import subprocess
import os
import sys
import importlib.util

dir_repos = "repositories"
dir_extensions = "extensions"
python = sys.executable
git = os.environ.get('GIT', "git")
index_url = os.environ.get('INDEX_URL', "")

def run(command, desc=None, errdesc=None, custom_env=None):
    if desc is not None:
        print(desc)

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, env=os.environ if custom_env is None else custom_env)

    if result.returncode != 0:

        message = f"""{errdesc or 'Error running command'}.
            Command: {command}
            Error code: {result.returncode}
            stdout: {result.stdout.decode(encoding="utf8", errors="ignore") if len(result.stdout)>0 else '<empty>'}
            stderr: {result.stderr.decode(encoding="utf8", errors="ignore") if len(result.stderr)>0 else '<empty>'}
            """
        raise RuntimeError(message)

    return result.stdout.decode(encoding="utf8", errors="ignore")



def check_run(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    return result.returncode == 0


def is_installed(package):
    try:
        spec = importlib.util.find_spec(package)
    except ModuleNotFoundError:
        return False

    return spec is not None


def repo_dir(name):
    return os.path.join(dir_repos, name)


def run_python(code, desc=None, errdesc=None):
    return run(f'"{python}" -c "{code}"', desc, errdesc)


def run_pip(args, desc=None):
    index_url_line = f' --index-url {index_url}' if index_url != '' else ''
    return run(f'"{python}" -m pip {args} --prefer-binary{index_url_line}', desc=f"Installing {desc}", errdesc=f"Couldn't install {desc}")


def check_run_python(code):
    return check_run(f'"{python}" -c "{code}"')


def prepare_enviroment():
    requirements_file = os.environ.get('REQS_FILE', "requirements.txt")
    run_pip(f"install -r {requirements_file}", "requirements for Web UI")

    if "--exit" in sys.argv:
        print("Exiting because of --exit argument")
        exit(0)

def start_webui():
    from cProfile import label
    import gradio as gr
    from generateTrack import generate_track_by_prompt
    from dotenv import load_dotenv
    load_dotenv()
    print(f"Launching Web UI with arguments: {' '.join(sys.argv[1:])}")
    ui_render = gr.Interface(
            fn=generate_track_by_prompt,
            inputs=[
                gr.Textbox(
                    label="email",
                    placeholder="Email here for API Token..."
                ),
                gr.Textbox(
                    label="prompt",
                    placeholder="piano, rock, jazz"
                ),
                gr.Slider(
                    minimum=0,
                    maximum=120,
                    step=10,
                    value=30,
                    label="How much do you want the music duration?",
                ),
                gr.Checkbox(),
            ],
            outputs=[
                gr.Audio(type="numpy", label="Generated Audio"),
                gr.Text(label="Result message"),
                gr.Text(label="Tags")
            ],
            title="Generate music from Mubert API🎵",
        )
    
    ui_render.launch()   

if __name__ == "__main__":
    prepare_enviroment()
    start_webui()


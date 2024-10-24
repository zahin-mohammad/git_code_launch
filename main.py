from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
import subprocess


class CodeGitExtension(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        code_command = extension.preferences["code_command"]
        project_hints = extension.preferences["project_hint"].split(',')
        project_anti_hints = extension.preferences["project_anti_hint"].split(',')
        root_folder = extension.preferences["root_folder"]
        
        # Returns the full path for a project such as /home/username/subfolder/project
        # example
        # find ~/Dev \( -type f -o -type d \) \( -name .git -o -name package.json -o -name cargo.toml \) -exec dirname {} \; | sort -u

        find_names = "\\( " + " -o ".join(f"-name {hint}" for hint in project_hints) + " \\)"
        anti_paths = " -and ".join(f"-not -path '*/{anti}/*'" for anti in project_anti_hints)
        search_command = f"find {root_folder} \\( -type f -o -type d \\) {anti_paths} {find_names} -exec dirname {"{}"} \\; | sort -u"

        projects = []
        items = []

        if event.get_argument():
            search_command += f" | grep {event.get_argument()}"
        try:
            result = subprocess.run(
                [
                    'sh',
                    '-c',
                    search_command
                ], capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            if output:
                projects = output.split('\n')
            if len(projects) > 10:
                projects = projects[:10]
        except subprocess.CalledProcessError as e:
            output = f"Error: {e.stderr.strip()}"
        except FileNotFoundError:
            output = "Error: Script not found"

        # Populate items with project names
        for project in projects:
            if project:  # Ensure the project name is not empty
                project_name = project.split('/')[-1]
                items.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name=project_name,
                    description=f'{project}',
                    on_enter=RunScriptAction(f"{code_command} {project}")
                ))
                
        if not projects:
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name='No projects found',
                description='No projects found in the root folder',
                on_enter=HideWindowAction()
            ))

        return RenderResultListAction(items)

if __name__ == '__main__':
    CodeGitExtension().run()
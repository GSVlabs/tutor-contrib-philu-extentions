from __future__ import annotations

import os
from glob import glob

# import click
import importlib_resources
from tutor import hooks

from .__about__ import __version__

########################################
# CONFIGURATION
########################################

hooks.Filters.CONFIG_DEFAULTS.add_items(
    [
        # Add your new settings that have default values here.
        # Each new setting is a pair: (setting_name, default_value).
        # Prefix your setting names with 'PHILU_EXTENSIONS_'.
        ("PHILU_EXTENSIONS_VERSION", __version__),
        ("PHILU_EXTENTIONS_BRAND_VERSION", "quince.main"),
        ("PHILU_EXTENTIONS_HEADER_VERSION", "quince.main"),
        ("PHILU_EXTENTIONS_FOOTER_VERSION", "quince.main"),
    ]
)

hooks.Filters.CONFIG_UNIQUE.add_items(
    [
        # Add settings that don't have a reasonable default for all users here.
        # For instance: passwords, secret keys, etc.
        # Each new setting is a pair: (setting_name, unique_generated_value).
        # Prefix your setting names with 'PHILU_EXTENSIONS_'.
        # For example:
        ### ("PHILU_EXTENSIONS_SECRET_KEY", "{{ 24|random_string }}"),
    ]
)

hooks.Filters.CONFIG_OVERRIDES.add_items(
    [
        # Danger zone!
        # Add values to override settings from Tutor core or other plugins here.
        # Each override is a pair: (setting_name, new_value). For example:
        ### ("PLATFORM_NAME", "My platform"),
    ]
)


########################################
# INITIALIZATION TASKS
########################################

# To add a custom initialization task, create a bash script template under:
# tutorphilu_extensions/templates/philu-extensions/tasks/
# and then add it to the MY_INIT_TASKS list. Each task is in the format:
# ("<service>", ("<path>", "<to>", "<script>", "<template>"))
MY_INIT_TASKS: list[tuple[str, tuple[str, ...]]] = [
    # For example, to add LMS initialization steps, you could add the script template at:
    # tutorphilu_extensions/templates/philu-extensions/tasks/lms/init.sh
    # And then add the line:
    ("lms", ("philu-extensions", "tasks", "lms", "init")),
]


# For each task added to MY_INIT_TASKS, we load the task template
# and add it to the CLI_DO_INIT_TASKS filter, which tells Tutor to
# run it as part of the `init` job.
for service, template_path in MY_INIT_TASKS:
    full_path: str = str(
        importlib_resources.files("tutorphilu_extensions")
        / os.path.join("templates", *template_path)
    )
    with open(full_path, encoding="utf-8") as init_task_file:
        init_task: str = init_task_file.read()
    hooks.Filters.CLI_DO_INIT_TASKS.add_item((service, init_task))


########################################
# DOCKER IMAGE MANAGEMENT
########################################


# Images to be built by `tutor images build`.
# Each item is a quadruple in the form:
#     ("<tutor_image_name>", ("path", "to", "build", "dir"), "<docker_image_tag>", "<build_args>")
hooks.Filters.IMAGES_BUILD.add_items(
    [
        # To build `myimage` with `tutor images build myimage`,
        # you would add a Dockerfile to templates/philu-extensions/build/myimage,
        # and then write:
        ### (
        ###     "myimage",
        ###     ("plugins", "philu-extensions", "build", "myimage"),
        ###     "docker.io/myimage:{{ PHILU_EXTENSIONS_VERSION }}",
        ###     (),
        ### ),
    ]
)


# Images to be pulled as part of `tutor images pull`.
# Each item is a pair in the form:
#     ("<tutor_image_name>", "<docker_image_tag>")
hooks.Filters.IMAGES_PULL.add_items(
    [
        (
            "credentials",
            "{{ CREDENTIALS_DOCKER_IMAGE }}",
        )
    ]
)

# Images to be pushed as part of `tutor images push`.
# Each item is a pair in the form:
#     ("<tutor_image_name>", "<docker_image_tag>")
hooks.Filters.IMAGES_PUSH.add_items(
    [
        (
            "credentials",
            "{{ CREDENTIALS_DOCKER_IMAGE }}",
        )
    ]
)


########################################
# TEMPLATE RENDERING
# (It is safe & recommended to leave
#  this section as-is :)
########################################

hooks.Filters.ENV_TEMPLATE_ROOTS.add_items(
    # Root paths for template files, relative to the project root.
    [
        str(importlib_resources.files("tutorphilu_extensions") / "templates"),
    ]
)

hooks.Filters.ENV_TEMPLATE_TARGETS.add_items(
    # For each pair (source_path, destination_path):
    # templates at ``source_path`` (relative to your ENV_TEMPLATE_ROOTS) will be
    # rendered to ``source_path/destination_path`` (relative to your Tutor environment).
    # For example, ``tutorphilu_extensions/templates/philu-extensions/build``
    # will be rendered to ``$(tutor config printroot)/env/plugins/philu-extensions/build``.
    [
        ("philu-extensions/build", "plugins"),
        ("philu-extensions/apps", "plugins"),
        ("philu-extensions/k8s", "plugins"),
    ],
)


########################################
# PATCH LOADING
# (It is safe & recommended to leave
#  this section as-is :)
########################################

# For each file in tutorphilu_extensions/patches,
# apply a patch based on the file's name and contents.
for path in glob(str(importlib_resources.files("tutorphilu_extensions") / "patches" / "*")):
    with open(path, encoding="utf-8") as patch_file:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))


hooks.Filters.ENV_PATCHES.add_items(
    [
        (
            "mfe-dockerfile-pre-npm-build-learner-record",
            "ENV USE_LR_MFE='true'"
        ),
        (
            "mfe-dockerfile-post-npm-instal-authn",
            "RUN npm i react-zendesk --save"
        ),
        (
            "mfe-dockerfile-post-npm-instal-learning",
            "RUN npm i react-zendesk --save"
        ),
        (
            "mfe-dockerfile-post-npm-instal-learner-record",
            "RUN npm i react-zendesk --save"
        ),
        (
            "mfe-dockerfile-post-npm-instal-discussions",
            "RUN npm i react-zendesk --save"
        ),
    ]
)


########################################
# CUSTOM JOBS (a.k.a. "do-commands")
########################################

# A job is a set of tasks, each of which run inside a certain container.
# Jobs are invoked using the `do` command, for example: `tutor local do importdemocourse`.
# A few jobs are built in to Tutor, such as `init` and `createuser`.
# You can also add your own custom jobs:


# To add a custom job, define a Click command that returns a list of tasks,
# where each task is a pair in the form ("<service>", "<shell_command>").
# For example:
### @click.command()
### @click.option("-n", "--name", default="plugin developer")
### def say_hi(name: str) -> list[tuple[str, str]]:
###     """
###     An example job that just prints 'hello' from within both LMS and CMS.
###     """
###     return [
###         ("lms", f"echo 'Hello from LMS, {name}!'"),
###         ("cms", f"echo 'Hello from CMS, {name}!'"),
###     ]


# Then, add the command function to CLI_DO_COMMANDS:
## hooks.Filters.CLI_DO_COMMANDS.add_item(say_hi)

# Now, you can run your job like this:
#   $ tutor local do say-hi --name="Max Sokolski"


#######################################
# CUSTOM CLI COMMANDS
#######################################

# Your plugin can also add custom commands directly to the Tutor CLI.
# These commands are run directly on the user's host computer
# (unlike jobs, which are run in containers).

# To define a command group for your plugin, you would define a Click
# group and then add it to CLI_COMMANDS:


### @click.group()
### def philu-extensions() -> None:
###     pass


### hooks.Filters.CLI_COMMANDS.add_item(philu-extensions)


# Then, you would add subcommands directly to the Click group, for example:


### @philu-extensions.command()
### def example_command() -> None:
###     """
###     This is helptext for an example command.
###     """
###     print("You've run an example command.")


# This would allow you to run:
#   $ tutor philu-extensions example-command

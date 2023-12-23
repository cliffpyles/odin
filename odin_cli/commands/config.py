import os
import yaml


def create_config(args, config):
    config_dir = os.path.expanduser("~/.config/odin")
    config_file = os.path.join(config_dir, "odin.yaml")

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        print(f"Config directory created: {config_dir}")
    else:
        print(f"Config directory already exists: {config_dir}")
    if not os.path.exists(config_file):
        # Create a default configuration
        default_config = {}
        with open(config_file, "w") as file:
            yaml.dump(default_config, file)
        print(f"Config file created: {config_file}")
    else:
        print(f"Config file already exists: {config_file}")


def setup_config_command(subparsers, config, plugins):
    parser_config = subparsers.add_parser("config", help="Manage app configurations")
    config_subparsers = parser_config.add_subparsers(help="Actions")
    config_create_parser = config_subparsers.add_parser(
        "create", help="Create config file in ~/.config/odin"
    )
    config_create_parser.set_defaults(func=create_config)

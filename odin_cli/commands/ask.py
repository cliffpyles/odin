def setup_ask_command(subparsers, config, plugins):
    # Subparser for the "ask" command
    parser_ask = subparsers.add_parser(
        "ask", help="Ask a question or interact with a service"
    )
    ask_subparsers = parser_ask.add_subparsers(help="Services")

    for plugin in plugins:
        if hasattr(plugin, "register_ask_args"):
            plugin.register_ask_args(ask_subparsers, config)

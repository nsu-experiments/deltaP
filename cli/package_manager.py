#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line interface for ΔP package management.
Main router that delegates to specialized command modules.
"""

import argparse
import sys

# Import command handlers
from .init_command import cmd_init
from .add_command import cmd_add
from .install_command import cmd_install
from .list_command import cmd_list
from .run_command import cmd_run
from .populate_command import cmd_populate
from .sync_command import cmd_sync
from .ink_command import cmd_ink 
from .import_command import cmd_import
from .data_command import cmd_data
from .join_command import cmd_join


def cmd_publish(args):
    """Publish package to registry (future feature)"""
    print("Error: Publishing to registry is not yet implemented.")
    print("This feature is planned for a future release.")
    return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="dp",
        description="ΔP package manager - manage probabilistic programming packages"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # dp init
    init_parser = subparsers.add_parser("init", help="Initialize a new project (interactive)")
    init_parser.set_defaults(func=cmd_init)
    init_parser.add_argument("name", nargs='?', help="Project name (optional, will prompt if omitted)")

    # dp add
    add_parser = subparsers.add_parser("add", help="Add a new analysis module")
    add_parser.add_argument("module_name", help="Name of the module to create")
    add_parser.add_argument("--template", "-t", help="Module template to use") 
    add_parser.set_defaults(func=cmd_add)
    
    # dp install
    install_parser = subparsers.add_parser("install", help="Install a package")
    install_parser.add_argument("package", help="Package name or git URL")
    install_parser.add_argument("--force", action="store_true", help="Reinstall if exists")
    install_parser.set_defaults(func=cmd_install)
    
    # dp list
    list_parser = subparsers.add_parser("list", help="List installed packages")
    list_parser.set_defaults(func=cmd_list)
    
    # dp run
    run_parser = subparsers.add_parser("run", help="Run a ΔP program")
    run_parser.add_argument("target", nargs='+', help="Mode and module name, or .dp file path")
    run_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    run_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    run_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress warnings")
    run_parser.set_defaults(func=cmd_run)
    run_parser.add_argument("--no-output", dest='output', action='store_false', default=True, help="Don't save output to results/")

    # dp populate
    populate_parser = subparsers.add_parser("populate", help="Generate synthetic test data")
    populate_parser.add_argument("module", nargs='?', help="Module name (omit to populate all)")
    populate_parser.set_defaults(func=cmd_populate)

    # dp import
    import_parser = subparsers.add_parser("import", help="Import real datasets into HDF5 database")
    import_parser.add_argument("module", help="Module name (e.g., logistics, finance)")
    import_parser.set_defaults(func=cmd_import)

    # dp sync
    sync_parser = subparsers.add_parser("sync", help="Sync CSV/JSON data to HDF5 database")
    sync_parser.add_argument("module", nargs='?', help="Module name (omit to sync all)")
    sync_parser.set_defaults(func=cmd_sync)

    # dp data
    data_parser = subparsers.add_parser("data", help="Inspect HDF5 database contents")
    data_parser.add_argument("--database", help="Path to HDF5 database (default: delta_db.h5)")
    data_parser.add_argument("--synthetic", "-s", action="store_true", 
                            help="Inspect synthetic database (delta_db_synthetic.h5)")
    data_parser.add_argument("--verbose", "-v", action="store_true", 
                            help="Show sample rows for each predicate")
    data_parser.add_argument("--samples", "-n", type=int, default=3,
                            help="Number of sample rows to show (default: 3)")
    data_parser.set_defaults(func=cmd_data)

    # dp ink
    ink_parser = subparsers.add_parser("ink", help="Generate visualizations from simulation results")
    ink_parser.add_argument("module_name", help="Name of the module to visualize")
    ink_parser.add_argument("mode", nargs='?', choices=['decision', 'simulation', 'd', 's'],
                           help="Mode to visualize (optional, will prompt if omitted)")
    ink_parser.add_argument("--eda", action="store_true", help="Enable full EDA report")
    ink_parser.add_argument("--output", metavar="DIR", help="Output directory for plots (default: results/plots)")
    ink_parser.set_defaults(func=cmd_ink)

    # dp join:
    join_parser = subparsers.add_parser('join', help='Join tier CSV files')
    join_parser.add_argument('module', help='Module name')
    join_parser.add_argument('mode', help='Mode (decision/simulation)')
    join_parser.set_defaults(func=cmd_join)
    
    # dp publish
    publish_parser = subparsers.add_parser("publish", help="Publish package (not implemented)")
    publish_parser.set_defaults(func=cmd_publish)
    
    # Parse and execute
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
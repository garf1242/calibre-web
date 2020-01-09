# -*- coding: utf-8 -*-

#  This file is part of the Calibre-Web (https://github.com/janeczku/calibre-web)
#    Copyright (C) 2012-2019 mutschler, cervinko, ok11, jkrehm, nanu-c, Wineliva,
#                            pjeby, elelay, idalin, Ozzieisaacs
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import division, print_function, unicode_literals


import os, sys
import pkgutil
import importlib

from . import logger, config

log = logger.create()
logger.setup(logger.LOG_TO_STDERR)

def import_module(name, full_name, plugin_paths):
    """Import module for python2 or python3"""
    if (sys.version_info > (3, 0)):
        return importlib.import_module(full_name)
    else:
        # python2 importlib.import_module has another behavior: if an
        # intermediate directory is not a package (does not contain a
        # __init__.py file), the module import fails (package/module is not
        # found).
        import imp
        f, pathname, description = imp.find_module(name, plugin_paths)
        return imp.load_module(full_name, f, pathname, description)

# Python2: need to inherit from object to have the __subclasses__ method.
# Not needed in python3
class Plugin(object):
    name = "the_name_that_identifies_the_plugin"
    title = "A fancy title that can be displayed"
    description = "Please change this"
    version = "Please change this"

    instance = None

    @classmethod
    def enable(cls):
        """Enable the plugin.
           Creates an instance of the plugin class and attach it.
           Basically, an enabled plugin is a plugin with a singleton
           instanced."""
        if not cls.instance:
            try:
                cls.instance = cls()
            except Exception as e:
                log.error(e)
                return False
        return True

    @classmethod
    def disable(cls):
        """Disable the plugin.
           Removes the plugin instance attached to the class."""
        cls.instance = None

    @classmethod
    def enabled(cls):
        """Check whether the plugin is enabled, aka has an instance"""
        if cls.instance:
            return True
        return False

    @classmethod
    def to_dict(cls):
        """Returns a dictionary representation of the plugin."""
        return {"name": cls.name,
                "title": cls.title,
                "description": cls.description,
                "version": cls.version,
                "enabled": cls.enabled()}

class PluginCategory:
    """Helps loading and listing all plugins of a same category."""
    # Default plugin directories to search into
    plugin_directories = ['plugins']
    # Plugin class that the category is refering to
    plugin_class = None
    # Directory that contains the plugins of that category.
    # When trying to load plugins, the code will look into any
    # plugin_directory/plugins_subdir for each plugin_directory in
    # plugin_directories.
    plugins_subdir = ''
    # Field name used to store enabled/disabled plugins in configuration
    # database.
    config_field = 'config_plugins_enabled_SOMETHING_TO_DECLARE_IN_CONFIG'

    @classmethod
    def get(cls, name):
        """Get an enabled plugin instance by its name"""
        for plugin in cls.list_enabled():
            if plugin.name == name:
                return plugin.instance
        return None

    @classmethod
    def list_available(cls):
        """List available plugins.
           Returns the plugin classes, as the instances can be empty if the
           plugin is not enabled"""
        return cls.plugin_class.__subclasses__()

    @classmethod
    def list_enabled(cls):
        """List enabled plugins.
           Returns the plugin instances, not the classes"""
        return [ plugin.instance for plugin in cls.list_available() if plugin.instance is not None ]

    @classmethod
    def enable_all(cls, use_config=False):
        """Enable all available plugins.
           If use_config is set to True, enable only plugins that are marked as
           enabled in configuration. Plugins that are not available will be
           ignored."""
        plugins_from_config = getattr(config, cls.config_field).split(',') if use_config else None
        for plugin in cls.list_available():
            if use_config and plugin.name not in plugins_from_config:
                continue
            log.info("Enabling plugin %s (%s)" % (plugin.name, plugin.description))
            plugin.enable()

    @classmethod
    def save_to_config(cls):
        """Save enabled plugins in config.
           This is a simple comma separated list of plugin name store in the
           config field."""
        to_save = ','.join([ plugin.name for plugin in cls.list_enabled() ])
        setattr(config, cls.config_field, to_save)
        config.save()

    @classmethod
    def load_available(cls):
        """Load available plugins. This class method will try to load all
           packages that are included in the specific plugin subdirectory.
           Every plugin is supposed to be a package that contains a class
           of the corresponding type.
           Plugin classes will have to be intanced (with the load_enabled
           method) to be used."""
        root_plugin_paths = []
        for directory in cls.plugin_directories:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), directory)
            root_plugin_paths.append(path)
            if path not in sys.path:
                log.info("Adding %s to plugins path" % path)
                sys.path.append(path)
        result = []
        # We will look at plugins in these directories
        plugin_paths = [ os.path.join(path, cls.plugins_subdir) for path in root_plugin_paths ]
        for _, name, ispkg in pkgutil.walk_packages(plugin_paths):
            if ispkg:
                try:
                    full_name = "%s.%s" % (cls.plugins_subdir, name)
                    log.info("Importing " + full_name)
                    result.append(import_module(name, full_name, plugin_paths))
                except Exception as e:
                    log.error(e)
        return result

# Metadata providers

class MetadataProvider(Plugin):
    name = "the_name_that_identifies_the_provider"
    description = "A cool description"

    def search_results(self, book):
        """Should return a list of dictionaries representing a book result.
        Book structure is:
        {
            'id': <string>,
            'title': <string>,
            'authors': [<string>],
            'description': <string>,
            'publisher': <string>,
            'publishedDate': <string formated in YYYY-MM-DD format>,
            'tags': [<string>],
            'rating': <float in [0.0 , 5.0]>,
            'series': <string>,
            'cover': <string, external or local url for picture>,
            'url': <string, the external link to the book description>,
            'source': {
                    'id': <string, provider name>,
                    'description': <string, provider description>,
                    'url': <string: provider url>
        }
        """
        raise Exception("SHOULD BE IMPLEMENTED")

class MetadataProviderCategory(PluginCategory):
    plugin_class = MetadataProvider
    plugins_subdir = 'metadata_providers'
    config_field = 'config_plugins_enabled_metadata_provider'

MetadataProviderCategory.load_available()
MetadataProviderCategory.enable_all(use_config=True)


How to make own slixmpp plugin for Message and IQ extension
===========================================================

Introduction and requirements
-----------------------------

* `'python3'`

Code used in tutorial is compatybile with python version 3.6+.

For backward compatybility with versions before, delete f-strings functionality and replace this with older string formatting `'"{}".format("content")'` or `'%s, "content"'`.

Ubuntu linux installation:

.. code-block:: bash

    sudo apt-get install python3.6

* `'slixmpp'` 
* `'argparse'`
* `'logging'`
* `'subprocess'`
* `'threading'`

Check if these libraries and proper python version are available at your environment. 
(all except slixmpp are in standard python library, this is very exceptionally situation to don't have it insalled with python)

.. code-block:: python

    python3 --version
    python3 -c "import slixmpp; print(slixmpp.__version__)"
    python3 -c "import argparse; print(argparse.__version__)"
    python3 -c "import logging; print(logging.__version__)"
    python3 -m subprocess
    python3 -m threading

My output:

.. code-block:: bash

    ~ $ python3 --version
    Python 3.8.0
    ~ $ python3 -c "import slixmpp; print(slixmpp.__version__)"
    1.4.2
    ~ $ python3 -c "import argparse; print(argparse.__version__)"
    1.1
    ~ $ python3 -c "import logging; print(logging.__version__)"
    0.5.1.2    
    ~ $ python3 -m subprocess #This should return nothing
    ~ $ python3 -m threading #This should return nothing

If some of libraries throws `'ImportError'` or `'no module named ...'`, try to install it with following example:

Ubuntu linux installation:

.. code-block:: bash

    pip3 install slixmpp
    #or
    easy_install slixmpp

If some of libraries throws NameError, reinstall package.

* `Jabber accounts`

For testing purposes, there will be required two private jabber accounts.
For creating new account, on web are many free available servers:

https://www.google.com/search?q=jabber+server+list

Clients testing runner
----------------------

Outside of project location we should create testing script to get fast output of our changes, with our credentials to avoid by accident send these for example to git repository.

At mine device I created at path `'/usr/bin'` file named `'test_slixmpp'` and let this file access to execute:

.. code-block:: bash

    /usr/bin $ chmod 711 test_slixmpp

This file contain:

.. code-block:: python

    #!/usr/bin/python3
    #File: /usr/bin/test_slixmpp & permissions rwx--x--x (711)

    import subprocess
    import threading
    import time
    
    def start_shell(shell_string):
        subprocess.run(shell_string, shell=True, universal_newlines=True)
    
    if __name__ == "__main__":
        #~ prefix = "x-terminal-emulator -e" # Separate terminal for every client, you can replace xterm with your terminal
        #~ prefix = "xterm -e" # Separate terminal for every client, you can replace xterm with your terminal
        prefix = ""
        #~ postfix = " -d" # Debug
        #~ postfix = " -q" # Quiet
        postfix = ""
    
        sender_path = "./example/sender.py"
        sender_jid = "SENDER_JID"
        sender_password = "SENDER_PASSWORD"
    
        example_file = "./test_example_tag.xml"
    
        responder_path = "./example/responder.py"
        responder_jid = "RESPONDER_JID"
        responder_password = "RESPONDER_PASSWORD"
    
        # Remember about rights to run your python files. (`chmod +x ./file.py`)
        SENDER_TEST = f"{prefix} {sender_path} -j {sender_jid} -p {sender_password}" + \
                       " -t {responder_jid} --path {example_file} {postfix}"
    
        RESPON_TEST = f"{prefix} {responder_path} -j {responder_jid}" + \
                       " -p {responder_password} {postfix}"
        
        try:
            responder = threading.Thread(target=start_shell, args=(RESPON_TEST, ))
            sender = threading.Thread(target=start_shell, args=(SENDER_TEST, ))
            responder.start()
            sender.start()
            while True:
                time.sleep(0.5)
        except:
           print ("Error: unable to start thread")

The `'subprocess.run()'` is compatybile with Python 3.5+. So if backward compatybility is needed, replace this with `'call'` method and adjust properly.

At next point I write there my credentials, get paths from `'sys.argv[...]'` or `'os.getcwd()'`, get parameter to debug, quiet or default info and mock mine testing xml file. Whichever parameter is used, it should be comfortable and fast to testing scripts without refactoring script again. Before closed, make it open till proper paths to file be created (about full jid later).

For larger manual testing application during development process there in my opinion should be used prefix with separate terminal for every client, then will be easier to find which client causes error for example.

Create client and plugin
------------------------

There should be created two clients to check if everything works fine. I created `'sender'` and `'responder'` clients. There is minimal code implementation for effictive testing code when we need to build plugin:

.. code-block:: python

    #File: $WORKDIR/example/sender.py
    import logging
    from argparse import ArgumentParser
    from getpass import getpass
    import time
    
    import slixmpp
    from slixmpp.xmlstream import ET
    
    import example_plugin
    
    class Sender(slixmpp.ClientXMPP):
        def __init__(self, jid, password, to, path):
            slixmpp.ClientXMPP.__init__(self, jid, password)
    
            self.to = to
            self.path = path
            
            self.add_event_handler("session_start", self.start)

    def start(self, event):
        # Two, not required methods, but allows another users to see us available, and receive that information.
        self.send_presence()
        self.get_roster()

    if __name__ == '__main__':
        parser = ArgumentParser(description=Sender.__doc__)
    
        parser.add_argument("-q", "--quiet", help="set logging to ERROR",
                            action="store_const", dest="loglevel",
                            const=logging.ERROR, default=logging.INFO)
        parser.add_argument("-d", "--debug", help="set logging to DEBUG",
                            action="store_const", dest="loglevel",
                            const=logging.DEBUG, default=logging.INFO)
    
        parser.add_argument("-j", "--jid", dest="jid",
                            help="JID to use")
        parser.add_argument("-p", "--password", dest="password",
                            help="password to use")
        parser.add_argument("-t", "--to", dest="to",
                            help="JID to send the message/iq to")
        parser.add_argument("--path", dest="path",
                            help="path to load example_tag content")
    
        args = parser.parse_args()
    
        logging.basicConfig(level=args.loglevel,
                            format=' %(name)s - %(levelname)-8s %(message)s')
    
        if args.jid is None:
            args.jid = input("Username: ")
        if args.password is None:
            args.password = getpass("Password: ")
    
        xmpp = Sender(args.jid, args.password, args.to, args.path)
        #xmpp.register_plugin('OurPlugin', module=example_plugin) # OurPlugin is a class name from example_plugin
    
        xmpp.connect()
        try:
            xmpp.process()
        except KeyboardInterrupt:
            try:
                xmpp.disconnect()
            except:
                pass

.. code-block:: python

    #File: $WORKDIR/example/responder.py
    import logging
    from argparse import ArgumentParser
    from getpass import getpass
    
    import slixmpp
    import example_plugin
    
    class Responder(slixmpp.ClientXMPP):
        def __init__(self, jid, password):
            slixmpp.ClientXMPP.__init__(self, jid, password)
            
            self.add_event_handler("session_start", self.start)
            
        def start(self, event):
            # Two, not required methods, but allows another users to see us available, and receive that information.
            self.send_presence()
            self.get_roster()

    if __name__ == '__main__':
        parser = ArgumentParser(description=Responder.__doc__)
    
        parser.add_argument("-q", "--quiet", help="set logging to ERROR",
                            action="store_const", dest="loglevel",
                            const=logging.ERROR, default=logging.INFO)
        parser.add_argument("-d", "--debug", help="set logging to DEBUG",
                            action="store_const", dest="loglevel",
                            const=logging.DEBUG, default=logging.INFO)
    
        parser.add_argument("-j", "--jid", dest="jid",
                            help="JID to use")
        parser.add_argument("-p", "--password", dest="password",
                            help="password to use")
        parser.add_argument("-t", "--to", dest="to",
                            help="JID to send the message to")
    
        args = parser.parse_args()
    
        logging.basicConfig(level=args.loglevel,
                            format=' %(name)s - %(levelname)-8s %(message)s')
    
        if args.jid is None:
            args.jid = input("Username: ")
        if args.password is None:
            args.password = getpass("Password: ")
    
        xmpp = Responder(args.jid, args.password)
        xmpp.register_plugin('OurPlugin', module=example_plugin) # OurPlugin is a class name from example_plugin
    
        xmpp.connect()
        try:
            xmpp.process()
        except KeyboardInterrupt:
            try:
                xmpp.disconnect()
            except:
                pass

Next file to create is `'example_plugin.py'` with path available to import from clients. There as default I put it into that same localization as clients.

.. code-block:: python

    #File: $WORKDIR/example/example plugin.py
    import logging
    
    from slixmpp.xmlstream import ElementBase, ET, register_stanza_plugin
    
    from slixmpp import Iq
    from slixmpp import Message
    
    from slixmpp.plugins.base import BasePlugin
    
    from slixmpp.xmlstream.handler import Callback
    from slixmpp.xmlstream.matcher import StanzaPath
    
    log = logging.getLogger(__name__)
    
    class OurPlugin(BasePlugin):
        def plugin_init(self):
            self.description = "OurPluginExtension"                 ##~ String data for Human readable and find plugin by another plugin with method.
            self.xep = "ope"                                        ##~ String data for Human readable and find plugin by another plugin with adding it into `slixmpp/plugins/__init__.py` to the `__all__` declaration with 'xep_OPE'. Otherwise it's just human readable annotation.
    
            namespace = ExampleTag.namespace


    class ExampleTag(ElementBase):
        name = "example_tag"                                        ##~ The name of the root XML element of that extension.
        namespace = "https://example.net/our_extension"             ##~ The namespace our stanza object lives in, like <example_tag xmlns={namespace} (...)</example_tag>. You should change it for your own namespace
    
        plugin_attrib = "example_tag"                               ##~ The name to access this type of stanza. In particular, given  a  registration  stanza,  the Registration object can be found using: stanza_object['example_tag'] now `'example_tag'` is name of ours ElementBase extension. And this should be that same as name.
        
        interfaces = {"boolean", "some_string"}                     ##~ A list of dictionary-like keys that can be used with the stanza object. For example `stanza_object['example_tag']` gives us {"another": "some", "data": "some"}, whenever `'example_tag'` is name of ours ElementBase extension.


If it isn't it that same directory, then create symbolic link to localization reachable by clients:

.. code-block:: bash

    ln -s $Path_to_example_plugin_py $Path_to_clients_destinations

Otherwise import it properly with dots to get correct import path.

First run and event handlers
----------------------------

To check if everything is okay, we can use start method, because right after client is ready, then event `'session_start'` should be raised.

In `'__init__'` method are created handler for event call `'session_start'` and when it is called, then our method `'def start(self, event):'` will be exected. At first run add following line: `'logging.info("I'm running")'` to both of clients (sender and responder) and use `'test_slixmpp'` command. 

Now method `'def start(self, event):'` should look like this:

.. code-block:: python

    def start(self, event):
        # Two, not required methods, but allows another users to see us available, and receive that information.
        self.send_presence()
        self.get_roster()

        #>>>>>>>>>>>>
        logging.info("I'm running")
        #<<<<<<<<<<<<

If everything works fine. Then we can comment this line and go to sending message at first example.

Build message object
--------------------

In this tutorial section, example sender class should get recipient (jid of responder) from command line arguments, stored in test_slixmpp. Access to this argument are stored in attribute `'self.to'`.

Code example:

.. code-block:: python

    #File: $WORKDIR/example/sender.py
    
    class Sender(slixmpp.ClientXMPP):
        def __init__(self, jid, password, to, path):
            slixmpp.ClientXMPP.__init__(self, jid, password)
    
            self.to = to
            self.path = path
            
            self.add_event_handler("session_start", self.start)

        def start(self, event):
            # Two, not required methods, but allows another users to see us available, and receive that information.
            self.send_presence()
            self.get_roster()
            #>>>>>>>>>>>>
            self.send_example_message(self.to, "example_message")
    
        def send_example_message(self, to, body):
            #~ make_message(mfrom=None, mto=None, mtype=None, mquery=None)
            # Default mtype == "chat"; 
            msg = self.make_message(mto=to, mbody=body)
            msg.send()
            #<<<<<<<<<<<<

In example below I using build-in method to make Message object with string "example_message" and I calling it right after `'start'` method.

To receive this message, responder should have proper handler to handle signal with message object, and method to decide what to do with this message. There is example below:

.. code-block:: python

    #File: $WORKDIR/example/responder.py
    
    class Responder(slixmpp.ClientXMPP):
        def __init__(self, jid, password):
            slixmpp.ClientXMPP.__init__(self, jid, password)
            
            self.add_event_handler("session_start", self.start)
            
            #>>>>>>>>>>>>
            self.add_event_handler("message", self.message)
            #<<<<<<<<<<<<

        def start(self, event):
            # Two, not required methods, but allows another users to see us available, and receive that information.
            self.send_presence()
            self.get_roster()
    
        #>>>>>>>>>>>>
        def message(self, msg):
            #Show all inside msg
            logging.info(msg)
            #Show only body attribute, like dictionary access
            logging.info(msg['body'])
        #<<<<<<<<<<<<

Extend message with our tags
++++++++++++++++++++++++++++

To extend our message object with specified tag with specified fields, our plugin should be registred as extension for message object:

.. code-block:: python

    #File: $WORKDIR/example/example plugin.py
    
    class OurPlugin(BasePlugin):
        def plugin_init(self):
            self.description = "OurPluginExtension"                 ##~ String data for Human readable and find plugin by another plugin with method.
            self.xep = "ope"                                        ##~ String data for Human readable and find plugin by another plugin with adding it into `slixmpp/plugins/__init__.py` to the `__all__` declaration with 'xep_OPE'. Otherwise it's just human readable annotation.
    
            namespace = ExampleTag.namespace
            #>>>>>>>>>>>>
            register_stanza_plugin(Message, ExampleTag)             ##~ Register tags extension for Message object, otherwise message['example_tag'] will be string field instead container where we can manage our fields and create sub elements.
            #<<<<<<<<<<<<

    class ExampleTag(ElementBase):
        name = "example_tag"                                        ##~ The name of the root XML element of that extension.
        namespace = "https://example.net/our_extension"             ##~ The namespace our stanza object lives in, like <example_tag xmlns={namespace} (...)</example_tag>. You should change it for your own namespace
    
        plugin_attrib = "example_tag"                               ##~ The name to access this type of stanza. In particular, given  a  registration  stanza,  the Registration object can be found using: stanza_object['example_tag'] now `'example_tag'` is name of ours ElementBase extension. And this should be that same as name.
        
        interfaces = {"boolean", "some_string"}                     ##~ A list of dictionary-like keys that can be used with the stanza object. For example `stanza_object['example_tag']` gives us {"another": "some", "data": "some"}, whenever `'example_tag'` is name of ours ElementBase extension.

        #>>>>>>>>>>>>
        def set_boolean(self, boolean):
            self.xml.attrib['boolean'] = str(boolean)
    
        def set_some_string(self, some_string):
            self.xml.attrib['some_string'] = some_string
        #<<<<<<<<<<<<

Now with registred object we can extend our message.

.. code-block:: python

    #File: $WORKDIR/example/sender.py
    
    class Sender(slixmpp.ClientXMPP):
        def __init__(self, jid, password, to, path):
            slixmpp.ClientXMPP.__init__(self, jid, password)
    
            self.to = to
            self.path = path
            
            self.add_event_handler("session_start", self.start)

        def start(self, event):
            # Two, not required methods, but allows another users to see us available, and receive that information.
            self.send_presence()
            self.get_roster()
            self.send_example_message(self.to, "example_message")
    
        def send_example_message(self, to, body):
            #~ make_message(mfrom=None, mto=None, mtype=None, mquery=None)
            # Default mtype == "chat"; 
            msg = self.make_message(mto=to, mbody=body)
            #>>>>>>>>>>>>
            msg['example_tag'].set_some_string("Work!")
            logging.info(msg)
            #<<<<<<<<<<<<
            msg.send()

Now after running, following message from logging should show `'example_tag'` included inside <message><example_tag/></message> with our string, and namespace.

Catch extended message with different event handler
+++++++++++++++++++++++++++++++++++++++++++++++++++

To get difference between extended messages and basic messages (or Iq), we can register handler for our namespace and tag to make unique combination and handle only these required messages.

.. code-block:: python

    #File: $WORKDIR/example/example plugin.py
    
    class OurPlugin(BasePlugin):
        def plugin_init(self):
            self.description = "OurPluginExtension"                 ##~ String data for Human readable and find plugin by another plugin with method.
            self.xep = "ope"                                        ##~ String data for Human readable and find plugin by another plugin with adding it into `slixmpp/plugins/__init__.py` to the `__all__` declaration with 'xep_OPE'. Otherwise it's just human readable annotation.
    
            namespace = ExampleTag.namespace
            
            self.xmpp.register_handler(
                        Callback('ExampleMessage Event:example_tag',##~ Name of this Callback
                        StanzaPath(f'message/{{{namespace}}}example_tag'),          ##~ Handle only Message with example_tag
                        self.__handle_message))                     ##~ Method which catch proper Message, should raise proper event for client.
            register_stanza_plugin(Message, ExampleTag)             ##~ Register tags extension for Message object, otherwise message['example_tag'] will be string field instead container where we can manage our fields and create sub elements.

        def __handle_message(self, msg):
            # Do something with received message
            self.xmpp.event('example_tag_message', msg)          ##~ Call event which can be handled by clients to send or something other what you want.

StanzaPath object should be initialized in proper way, this is as follows:
`'OBJECT_NAME[@type=TYPE_OF_OBJECT][/{NAMESPACE}[TAG]]'`

* For OBJECT_NAME we can use `'message'` or `'iq'`.
* For TYPE_OF_OBJECT if we specify iq, we can precise `'get, set, error or result'`
* For NAMESPACE it always should be namespace from our tag extension class.
* For TAG it should contain our tag, `'example_tag'` in this case.

Now we catching all types of message with proper namespace inside `'example_tag'`, there we can do something with this message before we send this message stright to client with our own "example_tag_message" event. 

.. code-block:: python

    #File: $WORKDIR/example/sender.py
    
    class Sender(slixmpp.ClientXMPP):
        def __init__(self, jid, password, to, path):
            slixmpp.ClientXMPP.__init__(self, jid, password)
    
            self.to = to
            self.path = path
            
            self.add_event_handler("session_start", self.start)

        def start(self, event):
            # Two, not required methods, but allows another users to see us available, and receive that information.
            self.send_presence()
            self.get_roster()
            #>>>>>>>>>>>>
            self.send_example_message(self.to, "example_message", "example_string")
    
        def send_example_message(self, to, body, some_string=""):
            #~ make_message(mfrom=None, mto=None, mtype=None, mquery=None)
            # Default mtype == "chat"; 
            msg = self.make_message(mto=to, mbody=body)
            if some_string:
                msg['example_tag'].set_some_string(some_string)
            msg.send()
            #<<<<<<<<<<<<

Next, remember line: `'self.xmpp.event('example_tag_message', msg)'`.

There is event name to handle from responder `'example_tag_message'`.

.. code-block:: python

    #File: $WORKDIR/example/responder.py
    
    class Responder(slixmpp.ClientXMPP):
        def __init__(self, jid, password):
            slixmpp.ClientXMPP.__init__(self, jid, password)
            
            self.add_event_handler("session_start", self.start)
            #>>>>>>>>>>>>
            self.add_event_handler("example_tag_message", self.example_tag_message)
            #<<<<<<<<<<<<

        def start(self, event):
            # Two, not required methods, but allows another users to see us available, and receive that information.
            self.send_presence()
            self.get_roster()
    
        #>>>>>>>>>>>>
        def example_tag_message(self, msg):
            logging.info(msg) # Message is standalone object, it can be replied, but no error arrives if not.
        #<<<<<<<<<<<<

There we can reply the message, but nothing will happen if we don't do this. But next object used in most cases are Iq. Iq object always should be replied if received, otherwise client had error typed reply due timeout if target of iq client don't answer this iq.


Useful methods and others
-------------------------

Ways to access elements
+++++++++++++++++++++++

* -ToDo-

Setup message from XML files, strings and other objects
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

* -ToDo-

Dev friendly methods for plugin usage
+++++++++++++++++++++++++++++++++++++

* -ToDo-

Tags and strings nested inside our tag
++++++++++++++++++++++++++++++++++++++

* -ToDo-

Complete code from tutorial
---------------------------

* -ToDo-

Sources and references
----------------------

* -ToDo-



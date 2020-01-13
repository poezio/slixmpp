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

Modify `Message` object example to `Iq`.
++++++++++++++++++++++++++++++++++++++++

To adjust example from Message object to Iq object, needed is to register new handler for iq like with message at chapter `,,Extend message with our tags''`. This time example contains several types with separate types to catch, this is useful to get difference between received iq request and iq response. Because all Iq messages should be repeated with that same ID to sender with response, otherwise sender get back iq with timeout error.

.. code-block:: python

    #File: $WORKDIR/example/example plugin.py
    
    class OurPlugin(BasePlugin):
        def plugin_init(self):
            self.description = "OurPluginExtension"                 ##~ String data for Human readable and find plugin by another plugin with method.
            self.xep = "ope"                                        ##~ String data for Human readable and find plugin by another plugin with adding it into `slixmpp/plugins/__init__.py` to the `__all__` declaration with 'xep_OPE'. Otherwise it's just human readable annotation.
    
            namespace = ExampleTag.namespace
            #>>>>>>>>>>>>
            self.xmpp.register_handler(
                        Callback('ExampleGet Event:example_tag',    ##~ Name of this Callback
                        StanzaPath(f"iq@type=get/{{{namespace}}}example_tag"),      ##~ Handle only Iq with type get and example_tag
                        self.__handle_get_iq))                      ##~ Method which catch proper Iq, should raise proper event for client.
    
            self.xmpp.register_handler(
                        Callback('ExampleResult Event:example_tag', ##~ Name of this Callback
                        StanzaPath(f"iq@type=result/{{{namespace}}}example_tag"),   ##~ Handle only Iq with type result and example_tag
                        self.__handle_result_iq))                   ##~ Method which catch proper Iq, should raise proper event for client.
    
            self.xmpp.register_handler(
                        Callback('ExampleError Event:example_tag',  ##~ Name of this Callback
                        StanzaPath(f"iq@type=error/{{{namespace}}}example_tag"),    ##~ Handle only Iq with type error and example_tag
                        self.__handle_error_iq))                    ##~ Method which catch proper Iq, should raise proper event for client.
    
            self.xmpp.register_handler(
                        Callback('ExampleMessage Event:example_tag',##~ Name of this Callback
                        StanzaPath(f'message/{{{namespace}}}example_tag'),          ##~ Handle only Message with example_tag
                        self.__handle_message))                     ##~ Method which catch proper Message, should raise proper event for client.
    
            register_stanza_plugin(Iq, ExampleTag)                  ##~ Register tags extension for Iq object, otherwise iq['example_tag'] will be string field instead container where we can manage our fields and create sub elements.
            #<<<<<<<<<<<<
            register_stanza_plugin(Message, ExampleTag)             ##~ Register tags extension for Message object, otherwise message['example_tag'] will be string field instead container where we can manage our fields and create sub elements.
            
            #>>>>>>>>>>>>
        # All iq types are: get, set, error, result
        def __handle_get_iq(self, iq):
            # Do something with received iq
            self.xmpp.event('example_tag_get_iq', iq)           ##~ Call event which can be handled by clients to send or something other what you want.
            
        def __handle_result_iq(self, iq):
            # Do something with received iq
            self.xmpp.event('example_tag_result_iq', iq)        ##~ Call event which can be handled by clients to send or something other what you want.
    
        def __handle_error_iq(self, iq):
            # Do something with received iq
            self.xmpp.event('example_tag_error_iq', iq)         ##~ Call event which can be handled by clients to send or something other what you want.
    
        def __handle_message(self, msg):
            # Do something with received message
            self.xmpp.event('example_tag_message', msg)          ##~ Call event which can be handled by clients to send or something other what you want.
            #<<<<<<<<<<<<

Events called from handlers, can be catched like with `'example_tag_message'` example. 
    
.. code-block:: python

    #File: $WORKDIR/example/responder.py
    
    class Responder(slixmpp.ClientXMPP):
        def __init__(self, jid, password):
            slixmpp.ClientXMPP.__init__(self, jid, password)
            
            self.add_event_handler("session_start", self.start)
            self.add_event_handler("example_tag_message", self.example_tag_message)
            #>>>>>>>>>>>>
            self.add_event_handler("example_tag_get_iq", self.example_tag_get_iq)
            #<<<<<<<<<<<<
    
            #>>>>>>>>>>>>
        def example_tag_get_iq(self, iq): # Iq stanza always should have a respond. If user is offline, it call an error.
            logging.info(str(iq))
            reply = iq.reply(clear=False)
            reply.send()
            #<<<<<<<<<<<<

Default parameter `'clear'` for `'Iq.reply'` is set to True, then content inside Iq object should be fulfilled, omitting ID and recipient, this information Iq holding even when `'clear'` is set to True.

.. code-block:: python

    #File: $WORKDIR/example/sender.py
    
    class Sender(slixmpp.ClientXMPP):
        def __init__(self, jid, password, to, path):
            slixmpp.ClientXMPP.__init__(self, jid, password)
    
            self.to = to
            self.path = path
    
            self.add_event_handler("session_start", self.start)
            #>>>>>>>>>>>>
            self.add_event_handler("example_tag_result_iq", self.example_tag_result_iq)
            self.add_event_handler("example_tag_error_iq", self.example_tag_error_iq)
            #<<<<<<<<<<<<
            
        def start(self, event):
            # Two, not required methods, but allows another users to see us available, and receive that information.
            self.send_presence()
            self.get_roster()

            #>>>>>>>>>>>>        
            self.send_example_iq(self.to)
            # <iq to=RESPONDER/RESOURCE xml:lang="en" type="get" id="0" from="SENDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" some_string="Another_string" boolean="True">Info_inside_tag</example_tag></iq>
            #<<<<<<<<<<<<
            
            #>>>>>>>>>>>>        
        def send_example_iq(self, to):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get")
            iq['example_tag']['boolean'] = "True"
            iq['example_tag']['some_string'] = "Another_string"
            iq['example_tag'].text = "Info_inside_tag"
            iq.send()
            #<<<<<<<<<<<<
            
            #>>>>>>>>>>>>
        def example_tag_result_iq(self, iq):
            logging.info(str(iq))
    
        def example_tag_error_iq(self, iq):
            logging.info(str(iq))
            #<<<<<<<<<<<<

Ways to access elements
+++++++++++++++++++++++

To access elements inside Message or Iq stanza are several ways, at first from clients is like access to dictionary:

.. code-block:: python

    #File: $WORKDIR/example/sender.py
    
    class Sender(slixmpp.ClientXMPP):
        #...
        def example_tag_result_iq(self, iq):
            logging.info(str(iq))
            #>>>>>>>>>>>>
            logging.info(iq['id'])
            logging.info(iq.get('id'))
            logging.info(iq['example_tag']['boolean'])
            logging.info(iq['example_tag'].get('boolean'))
            logging.info(iq.get('example_tag').get('boolean'))
            #<<<<<<<<<<<<

From ExampleTag extension, access to elements is similar there is example getter and setter for specific field:

.. code-block:: python

    #File: $WORKDIR/example/example plugin.py

    class ExampleTag(ElementBase):
        name = "example_tag"                                        ##~ The name of the root XML element of that extension.
        namespace = "https://example.net/our_extension"             ##~ The namespace our stanza object lives in, like <example_tag xmlns={namespace} (...)</example_tag>. You should change it for your own namespace
    
        plugin_attrib = "example_tag"                               ##~ The name to access this type of stanza. In particular, given  a  registration  stanza,  the Registration object can be found using: stanza_object['example_tag'] now `'example_tag'` is name of ours ElementBase extension. And this should be that same as name.
        
        interfaces = {"boolean", "some_string"}                     ##~ A list of dictionary-like keys that can be used with the stanza object. For example `stanza_object['example_tag']` gives us {"another": "some", "data": "some"}, whenever `'example_tag'` is name of ours ElementBase extension.
        
            #>>>>>>>>>>>>
        def get_some_string(self):
            return self.xml.attrib.get("some_string", None)
            
        def get_text(self, text):
            return self.xml.text
            
        def set_some_string(self, some_string):
            self.xml.attrib['some_string'] = some_string
    
        def set_text(self, text):
            self.xml.text = text
            #<<<<<<<<<<<<

Attribute `'self.xml'` is inherited from ElementBase and means exactly that same like `'Iq['example_tag']'` from client namespace. 

When proper setters and getters are used, then code can be cleaner and more object-like, like example below:

.. code-block:: python

    #File: $WORKDIR/example/sender.py
    
    class Sender(slixmpp.ClientXMPP):
        def __init__(self, jid, password, to, path):
            slixmpp.ClientXMPP.__init__(self, jid, password)
    
            self.to = to
            self.path = path
    
            self.add_event_handler("session_start", self.start)
            self.add_event_handler("example_tag_result_iq", self.example_tag_result_iq)
            self.add_event_handler("example_tag_error_iq", self.example_tag_error_iq)
               
        def send_example_iq(self, to):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get")
            iq['example_tag']['boolean'] = "True"
            #>>>>>>>>>>>>
            iq['example_tag'].set_some_string("Another_string")
            iq['example_tag'].set_text("Info_inside_tag")
            #<<<<<<<<<<<<
            iq.send()

Setup message from XML files, strings and other objects
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

To setup previously defined xml from string, from file containing this xml string or lxml (ElementTree) there are many ways to dump data. One of this is parse strings to lxml object, pass atributes and other info:

.. code-block:: python

    #File: $WORKDIR/example/example plugin.py

    #...
    from slixmpp.xmlstream import ElementBase, ET, register_stanza_plugin
    #...

    class ExampleTag(ElementBase):
        name = "example_tag"                                        ##~ The name of the root XML element of that extension.
        namespace = "https://example.net/our_extension"             ##~ The namespace our stanza object lives in, like <example_tag xmlns={namespace} (...)</example_tag>. You should change it for your own namespace
    
        plugin_attrib = "example_tag"                               ##~ The name to access this type of stanza. In particular, given  a  registration  stanza,  the Registration object can be found using: stanza_object['example_tag'] now `'example_tag'` is name of ours ElementBase extension. And this should be that same as name.
        
        interfaces = {"boolean", "some_string"}                     ##~ A list of dictionary-like keys that can be used with the stanza object. For example `stanza_object['example_tag']` gives us {"another": "some", "data": "some"}, whenever `'example_tag'` is name of ours ElementBase extension.
        
            #>>>>>>>>>>>>
        def setup_from_string(self, string):
            """Initialize tag element from string"""
            et_extension_tag_xml = ET.fromstring(string)
            self.setup_from_lxml(et_extension_tag_xml)
    
        def setup_from_file(self, path):
            """Initialize tag element from file containing adjusted data"""
            et_extension_tag_xml = ET.parse(path).getroot()
            self.setup_from_lxml(et_extension_tag_xml)
    
        def setup_from_lxml(self, lxml):
            """Add ET data to self xml structure."""
            self.xml.attrib.update(lxml.attrib)
            self.xml.text = lxml.text
            self.xml.tail = lxml.tail
            for inner_tag in lxml:
                self.xml.append(inner_tag)
            #<<<<<<<<<<<<

To test this, we need example file with xml, example xml string and example ET object:

.. code-block:: xml

    #File: $WORKDIR/test_example_tag.xml

    <example_tag xmlns="https://example.net/our_extension" some_string="StringFromFile">Info_inside_tag<inside_tag first_field="3" secound_field="4" /></example_tag>

.. code-block:: python

    #File: $WORKDIR/example/sender.py

    #...
    from slixmpp.xmlstream import ET
    #...
 
    class Sender(slixmpp.ClientXMPP):
        def __init__(self, jid, password, to, path):
            slixmpp.ClientXMPP.__init__(self, jid, password)
    
            self.to = to
            self.path = path
    
            self.add_event_handler("session_start", self.start)
            self.add_event_handler("example_tag_result_iq", self.example_tag_result_iq)
            self.add_event_handler("example_tag_error_iq", self.example_tag_error_iq)
    
        def start(self, event):
            # Two, not required methods, but allows another users to see us available, and receive that information.
            self.send_presence()
            self.get_roster()
    
            #>>>>>>>>>>>>
            self.disconnect_counter = 3 # This is only for disconnect when we receive all replies for sended Iq
            
            self.send_example_iq_tag_from_file(self.to, self.path)
            # <iq from="SENDER/RESOURCE" xml:lang="en" id="2" type="get" to="RESPONDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" some_string="Another_string">Info_inside_tag<inside_tag first_field="1" secound_field="2" /></example_tag></iq>
    
            string = '<example_tag xmlns="https://example.net/our_extension" some_string="Another_string">Info_inside_tag<inside_tag first_field="1" secound_field="2" /></example_tag>'
            et = ET.fromstring(string)
            self.send_example_iq_tag_from_element_tree(self.to, et)
            # <iq to="RESPONDER/RESOURCE" id="3" xml:lang="en" from="SENDER/RESOURCE" type="get"><example_tag xmlns="https://example.net/our_extension" some_string="Reply_string" boolean="True">Info_inside_tag<inside_tag secound_field="2" first_field="1" /></example_tag></iq>
            
            self.send_example_iq_tag_from_string(self.to, string)
            # <iq to="RESPONDER/RESOURCE" id="5" xml:lang="en" from="SENDER/RESOURCE" type="get"><example_tag xmlns="https://example.net/our_extension" some_string="Reply_string" boolean="True">Info_inside_tag<inside_tag secound_field="2" first_field="1" /></example_tag></iq>   

        def example_tag_result_iq(self, iq):
            self.disconnect_counter -= 1
            logging.info(str(iq))
            if not self.disconnect_counter:
                self.disconnect() # Example disconnect after first received iq stanza extended by example_tag with result type.
    
        def send_example_iq_tag_from_file(self, to, path):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=2)
            iq['example_tag'].setup_from_file(path)
    
            iq.send()
            
        def send_example_iq_tag_from_element_tree(self, to, et):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=3)
            iq['example_tag'].setup_from_lxml(et)
    
            iq.send()
    
        def send_example_iq_tag_from_string(self, to, string):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=5)
            iq['example_tag'].setup_from_string(string)
    
            iq.send()
            #<<<<<<<<<<<<

If Responder return our `'Iq'` with reply, then all is okay and Sender should be disconnected.

Dev friendly methods for plugin usage
+++++++++++++++++++++++++++++++++++++

Any plugin should have some sort of object-like methods, setup for our element, getters, setters and signals to make it easy for use for other developers.
During handling, data should be checked if is correct or return an error for sender. 

There is example followed by these rules:


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
            self.description = "OurPluginExtension"   ##~ String data for Human readable and find plugin by another plugin with method.
            self.xep = "ope"                          ##~ String data for Human readable and find plugin by another plugin with adding it into `slixmpp/plugins/__init__.py` to the `__all__` declaration with 'xep_OPE'. Otherwise it's just human readable annotation.
    
            namespace = ExampleTag.namespace
            self.xmpp.register_handler(
                        Callback('ExampleGet Event:example_tag',    ##~ Name of this Callback
                        StanzaPath(f"iq@type=get/{{{namespace}}}example_tag"),      ##~ Handle only Iq with type get and example_tag
                        self.__handle_get_iq))                      ##~ Method which catch proper Iq, should raise proper event for client.
    
            self.xmpp.register_handler(
                        Callback('ExampleResult Event:example_tag', ##~ Name of this Callback
                        StanzaPath(f"iq@type=result/{{{namespace}}}example_tag"),   ##~ Handle only Iq with type result and example_tag
                        self.__handle_result_iq))                   ##~ Method which catch proper Iq, should raise proper event for client.
    
            self.xmpp.register_handler(
                        Callback('ExampleError Event:example_tag',  ##~ Name of this Callback
                        StanzaPath(f"iq@type=error/{{{namespace}}}example_tag"),    ##~ Handle only Iq with type error and example_tag
                        self.__handle_error_iq))                    ##~ Method which catch proper Iq, should raise proper event for client.
    
            self.xmpp.register_handler(
                        Callback('ExampleMessage Event:example_tag',##~ Name of this Callback
                        StanzaPath(f'message/{{{namespace}}}example_tag'),          ##~ Handle only Message with example_tag
                        self.__handle_message))                     ##~ Method which catch proper Message, should raise proper event for client.
    
            register_stanza_plugin(Iq, ExampleTag)                  ##~ Register tags extension for Iq object, otherwise iq['example_tag'] will be string field instead container where we can manage our fields and create sub elements.
            register_stanza_plugin(Message, ExampleTag)             ##~ Register tags extension for Message object, otherwise message['example_tag'] will be string field instead container where we can manage our fields and create sub elements.
    
        # All iq types are: get, set, error, result
        def __handle_get_iq(self, iq):
            if iq.get_some_string is None:
                error = iq.reply(clear=False)
                error["type"] = "error"
                error["error"]["condition"] = "missing-data"
                error["error"]["text"] = "Without some_string value returns error."
                error.send()
            # Do something with received iq
            self.xmpp.event('example_tag_get_iq', iq)           ##~ Call event which can be handled by clients to send or something other what you want.
            
        def __handle_result_iq(self, iq):
            # Do something with received iq
            self.xmpp.event('example_tag_result_iq', iq)        ##~ Call event which can be handled by clients to send or something other what you want.
    
        def __handle_error_iq(self, iq):
            # Do something with received iq
            self.xmpp.event('example_tag_error_iq', iq)         ##~ Call event which can be handled by clients to send or something other what you want.
    
        def __handle_message(self, msg):
            # Do something with received message
            self.xmpp.event('example_tag_message', msg)          ##~ Call event which can be handled by clients to send or something other what you want.
    
    class ExampleTag(ElementBase):
        name = "example_tag"                                        ##~ The name of the root XML element of that extension.
        namespace = "https://example.net/our_extension"             ##~ The namespace our stanza object lives in, like <example_tag xmlns={namespace} (...)</example_tag>. You should change it for your own namespace
    
        plugin_attrib = "example_tag"                               ##~ The name to access this type of stanza. In particular, given  a  registration  stanza,  the Registration object can be found using: stanza_object['example_tag'] now `'example_tag'` is name of ours ElementBase extension. And this should be that same as name.
        
        interfaces = {"boolean", "some_string"}                     ##~ A list of dictionary-like keys that can be used with the stanza object. For example `stanza_object['example_tag']` gives us {"another": "some", "data": "some"}, whenever `'example_tag'` is name of ours ElementBase extension.
    
        def setup_from_string(self, string):
            """Initialize tag element from string"""
            et_extension_tag_xml = ET.fromstring(string)
            self.setup_from_lxml(et_extension_tag_xml)
    
        def setup_from_file(self, path):
            """Initialize tag element from file containing adjusted data"""
            et_extension_tag_xml = ET.parse(path).getroot()
            self.setup_from_lxml(et_extension_tag_xml)
    
        def setup_from_lxml(self, lxml):
            """Add ET data to self xml structure."""
            self.xml.attrib.update(lxml.attrib)
            self.xml.text = lxml.text
            self.xml.tail = lxml.tail
            for inner_tag in lxml:
                self.xml.append(inner_tag)

        def setup_from_dict(self, data):
            #There keys from dict should be also validated
            self.xml.attrib.update(data)
    
        def get_boolean(self):
            return self.xml.attrib.get("boolean", None)
    
        def get_some_string(self):
            return self.xml.attrib.get("some_string", None)
            
        def get_text(self, text):
            return self.xml.text
    
        def set_boolean(self, boolean):
            self.xml.attrib['boolean'] = str(boolean)
    
        def set_some_string(self, some_string):
            self.xml.attrib['some_string'] = some_string
    
        def set_text(self, text):
            self.xml.text = text
    
        def fill_interfaces(self, boolean, some_string):
            #Some validation if it is necessary
            self.set_boolean(boolean)
            self.set_some_string(some_string)

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
            self.add_event_handler("example_tag_get_iq", self.example_tag_get_iq)
            self.add_event_handler("example_tag_message", self.example_tag_message)
    
        def start(self, event):
            # Two, not required methods, but allows another users to see us available, and receive that information.
            self.send_presence()
            self.get_roster()
            
        def example_tag_get_iq(self, iq): # Iq stanza always should have a respond. If user is offline, it call an error.
            logging.info(iq)
            reply = iq.reply()
            reply["example_tag"].fill_interfaces(True, "Reply_string")
            reply.send()
    
        def example_tag_message(self, msg):
            logging.info(msg) # Message is standalone object, it can be replied, but no error arrives if not.
    
    
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
            self.add_event_handler("example_tag_result_iq", self.example_tag_result_iq)
            self.add_event_handler("example_tag_error_iq", self.example_tag_error_iq)
    
        def start(self, event):
            # Two, not required methods, but allows another users to see us available, and receive that information.
            self.send_presence()
            self.get_roster()
    
            self.disconnect_counter = 5 # This is only for disconnect when we receive all replies for sended Iq
            
            self.send_example_iq(self.to)
            # <iq to=RESPONDER/RESOURCE xml:lang="en" type="get" id="0" from="SENDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" some_string="Another_string" boolean="True">Info_inside_tag</example_tag></iq>
            
            self.send_example_message(self.to)
            # <message to="RESPONDER" xml:lang="en" from="SENDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" boolean="True" some_string="Message string">Info_inside_tag_message</example_tag></message>
            
            self.send_example_iq_tag_from_file(self.to, self.path)
            # <iq from="SENDER/RESOURCE" xml:lang="en" id="2" type="get" to="RESPONDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" some_string="Another_string">Info_inside_tag<inside_tag first_field="1" secound_field="2" /></example_tag></iq>
    
            string = '<example_tag xmlns="https://example.net/our_extension" some_string="Another_string">Info_inside_tag<inside_tag first_field="1" secound_field="2" /></example_tag>'
            et = ET.fromstring(string)
            self.send_example_iq_tag_from_element_tree(self.to, et)
            # <iq to="RESPONDER/RESOURCE" id="3" xml:lang="en" from="SENDER/RESOURCE" type="get"><example_tag xmlns="https://example.net/our_extension" some_string="Reply_string" boolean="True">Info_inside_tag<inside_tag secound_field="2" first_field="1" /></example_tag></iq>
    
            self.send_example_iq_to_get_error(self.to)
            # <iq type="get" id="4" from="SENDER/RESOURCE" xml:lang="en" to="RESPONDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" boolean="True" /></iq>
            # OUR ERROR <iq to="RESPONDER/RESOURCE" id="4" xml:lang="en" from="SENDER/RESOURCE" type="error"><example_tag xmlns="https://example.net/our_extension" boolean="True" /><error type="cancel"><feature-not-implemented xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" /><text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas">Without boolean value returns error.</text></error></iq>
            # OFFLINE ERROR <iq id="4" from="RESPONDER/RESOURCE" xml:lang="en" to="SENDER/RESOURCE" type="error"><example_tag xmlns="https://example.net/our_extension" boolean="True" /><error type="cancel" code="503"><service-unavailable xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" /><text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" xml:lang="en">User session not found</text></error></iq>
            
            self.send_example_iq_tag_from_string(self.to, string)
            # <iq to="RESPONDER/RESOURCE" id="5" xml:lang="en" from="SENDER/RESOURCE" type="get"><example_tag xmlns="https://example.net/our_extension" some_string="Reply_string" boolean="True">Info_inside_tag<inside_tag secound_field="2" first_field="1" /></example_tag></iq>
    
    
        def example_tag_result_iq(self, iq):
            self.disconnect_counter -= 1
            logging.info(str(iq))
            if not self.disconnect_counter:
                self.disconnect() # Example disconnect after first received iq stanza extended by example_tag with result type.
    
        def example_tag_error_iq(self, iq):
            self.disconnect_counter -= 1
            logging.info(str(iq))
            if not self.disconnect_counter:
                self.disconnect() # Example disconnect after first received iq stanza extended by example_tag with result type.
    
        def send_example_iq(self, to):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get")
            iq['example_tag'].set_boolean(True)
            iq['example_tag'].set_some_string("Another_string")
            iq['example_tag'].set_text("Info_inside_tag")
            iq.send()
    
        def send_example_message(self, to):
            #~ make_message(mfrom=None, mto=None, mtype=None, mquery=None)
            msg = self.make_message(mto=to)
            msg['example_tag'].set_boolean(True)
            msg['example_tag'].set_some_string("Message string")
            msg['example_tag'].set_text("Info_inside_tag_message")
            msg.send()
    
        def send_example_iq_tag_from_file(self, to, path):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=2)
            iq['example_tag'].setup_from_file(path)
    
            iq.send()
    
        def send_example_iq_tag_from_element_tree(self, to, et):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=3)
            iq['example_tag'].setup_from_lxml(et)
    
            iq.send()
    
        def send_example_iq_to_get_error(self, to):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=4)
            iq['example_tag'].set_boolean(True) # For example, our condition to receive error respond is example_tag without boolean value.
            iq.send()
    
        def send_example_iq_tag_from_string(self, to, string):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=5)
            iq['example_tag'].setup_from_string(string)
    
            iq.send()
        
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
        xmpp.register_plugin('OurPlugin', module=example_plugin) # OurPlugin is a class name from example_plugin
    
        xmpp.connect()
        try:
            xmpp.process()
        except KeyboardInterrupt:
            try:
                xmpp.disconnect()
            except:
                pass
    


Tags and strings nested inside our tag
++++++++++++++++++++++++++++++++++++++

To make nested element inside our IQ tag, consider our field `self.xml` as Element from ET (ElementTree).

Adding nested element then, is just append Element to our Element.

    
.. code-block:: python

    #File: $WORKDIR/example/example_plugin.py

    #(...)
    
    class ExampleTag(ElementBase):
        
    #(...)
    
        def add_inside_tag(self, tag, attributes, text=""):
            #If we want to fill with additionaly tags our element, then we can do it that way for example:
            itemXML = ET.Element("{{{0:s}}}{1:s}".format(self.namespace, tag)) #~ Initialize ET with our tag, for example: <example_tag (...)> <inside_tag namespace="https://example.net/our_extension"/></example_tag>
            itemXML.attrib.update(attributes) #~ There we add some fields inside tag, for example: <inside_tag namespace=(...) inner_data="some"/>
            itemXML.text = text #~ Fill field inside tag, for example: <inside_tag (...)>our_text</inside_tag>
            self.xml.append(itemXML) #~ Add that all what we set, as inner tag inside `example_tag` tag.

There is way to do this with dictionary and name for nested element tag, but inside function fields should be transfered to ET element.

Complete code from tutorial
---------------------------

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


.. code-block:: python

    #File: $WORKDIR/example/example_plugin.py

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
            self.description = "OurPluginExtension"   ##~ String data for Human readable and find plugin by another plugin with method.
            self.xep = "ope"                          ##~ String data for Human readable and find plugin by another plugin with adding it into `slixmpp/plugins/__init__.py` to the `__all__` declaration with 'xep_OPE'. Otherwise it's just human readable annotation.
    
            namespace = ExampleTag.namespace
            self.xmpp.register_handler(
                        Callback('ExampleGet Event:example_tag',    ##~ Name of this Callback
                        StanzaPath(f"iq@type=get/{{{namespace}}}example_tag"),      ##~ Handle only Iq with type get and example_tag
                        self.__handle_get_iq))                      ##~ Method which catch proper Iq, should raise proper event for client.
    
            self.xmpp.register_handler(
                        Callback('ExampleResult Event:example_tag', ##~ Name of this Callback
                        StanzaPath(f"iq@type=result/{{{namespace}}}example_tag"),   ##~ Handle only Iq with type result and example_tag
                        self.__handle_result_iq))                   ##~ Method which catch proper Iq, should raise proper event for client.
    
            self.xmpp.register_handler(
                        Callback('ExampleError Event:example_tag',  ##~ Name of this Callback
                        StanzaPath(f"iq@type=error/{{{namespace}}}example_tag"),    ##~ Handle only Iq with type error and example_tag
                        self.__handle_error_iq))                    ##~ Method which catch proper Iq, should raise proper event for client.
    
            self.xmpp.register_handler(
                        Callback('ExampleMessage Event:example_tag',##~ Name of this Callback
                        StanzaPath(f'message/{{{namespace}}}example_tag'),          ##~ Handle only Message with example_tag
                        self.__handle_message))                     ##~ Method which catch proper Message, should raise proper event for client.
    
            register_stanza_plugin(Iq, ExampleTag)                  ##~ Register tags extension for Iq object, otherwise iq['example_tag'] will be string field instead container where we can manage our fields and create sub elements.
            register_stanza_plugin(Message, ExampleTag)             ##~ Register tags extension for Message object, otherwise message['example_tag'] will be string field instead container where we can manage our fields and create sub elements.
    
        # All iq types are: get, set, error, result
        def __handle_get_iq(self, iq):
            if iq.get_some_string is None:
                error = iq.reply(clear=False)
                error["type"] = "error"
                error["error"]["condition"] = "missing-data"
                error["error"]["text"] = "Without some_string value returns error."
                error.send()
            # Do something with received iq
            self.xmpp.event('example_tag_get_iq', iq)           ##~ Call event which can be handled by clients to send or something other what you want.
            
        def __handle_result_iq(self, iq):
            # Do something with received iq
            self.xmpp.event('example_tag_result_iq', iq)        ##~ Call event which can be handled by clients to send or something other what you want.
    
        def __handle_error_iq(self, iq):
            # Do something with received iq
            self.xmpp.event('example_tag_error_iq', iq)         ##~ Call event which can be handled by clients to send or something other what you want.
    
        def __handle_message(self, msg):
            # Do something with received message
            self.xmpp.event('example_tag_message', msg)          ##~ Call event which can be handled by clients to send or something other what you want.
    
    class ExampleTag(ElementBase):
        name = "example_tag"                                        ##~ The name of the root XML element of that extension.
        namespace = "https://example.net/our_extension"             ##~ The namespace our stanza object lives in, like <example_tag xmlns={namespace} (...)</example_tag>. You should change it for your own namespace
    
        plugin_attrib = "example_tag"                               ##~ The name to access this type of stanza. In particular, given  a  registration  stanza,  the Registration object can be found using: stanza_object['example_tag'] now `'example_tag'` is name of ours ElementBase extension. And this should be that same as name.
        
        interfaces = {"boolean", "some_string"}                     ##~ A list of dictionary-like keys that can be used with the stanza object. For example `stanza_object['example_tag']` gives us {"another": "some", "data": "some"}, whenever `'example_tag'` is name of ours ElementBase extension.
    
        def setup_from_string(self, string):
            """Initialize tag element from string"""
            et_extension_tag_xml = ET.fromstring(string)
            self.setup_from_lxml(et_extension_tag_xml)
    
        def setup_from_file(self, path):
            """Initialize tag element from file containing adjusted data"""
            et_extension_tag_xml = ET.parse(path).getroot()
            self.setup_from_lxml(et_extension_tag_xml)
    
        def setup_from_lxml(self, lxml):
            """Add ET data to self xml structure."""
            self.xml.attrib.update(lxml.attrib)
            self.xml.text = lxml.text
            self.xml.tail = lxml.tail
            for inner_tag in lxml:
                self.xml.append(inner_tag)
    
        def setup_from_dict(self, data):
            #There should keys should be also validated
            self.xml.attrib.update(data)
    
        def get_boolean(self):
            return self.xml.attrib.get("boolean", None)
    
        def get_some_string(self):
            return self.xml.attrib.get("some_string", None)
            
        def get_text(self, text):
            return self.xml.text
    
        def set_boolean(self, boolean):
            self.xml.attrib['boolean'] = str(boolean)
    
        def set_some_string(self, some_string):
            self.xml.attrib['some_string'] = some_string
    
        def set_text(self, text):
            self.xml.text = text
    
        def fill_interfaces(self, boolean, some_string):
            #Some validation if it is necessary
            self.set_boolean(boolean)
            self.set_some_string(some_string)
        
        def add_inside_tag(self, tag, attributes, text=""):
            #If we want to fill with additionaly tags our element, then we can do it that way for example:
            itemXML = ET.Element("{{{0:s}}}{1:s}".format(self.namespace, tag)) #~ Initialize ET with our tag, for example: <example_tag (...)> <inside_tag namespace="https://example.net/our_extension"/></example_tag>
            itemXML.attrib.update(attributes) #~ There we add some fields inside tag, for example: <inside_tag namespace=(...) inner_data="some"/>
            itemXML.text = text #~ Fill field inside tag, for example: <inside_tag (...)>our_text</inside_tag>
            self.xml.append(itemXML) #~ Add that all what we set, as inner tag inside `example_tag` tag.
    

~

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
            self.add_event_handler("example_tag_result_iq", self.example_tag_result_iq)
            self.add_event_handler("example_tag_error_iq", self.example_tag_error_iq)
    
        def start(self, event):
            # Two, not required methods, but allows another users to see us available, and receive that information.
            self.send_presence()
            self.get_roster()
    
            self.disconnect_counter = 6 # This is only for disconnect when we receive all replies for sended Iq
            
            self.send_example_iq(self.to)
            # <iq to=RESPONDER/RESOURCE xml:lang="en" type="get" id="0" from="SENDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" some_string="Another_string" boolean="True">Info_inside_tag</example_tag></iq>
            
            self.send_example_iq_with_inner_tag(self.to)
            # <iq from="SENDER/RESOURCE" to="RESPONDER/RESOURCE" id="1" xml:lang="en" type="get"><example_tag xmlns="https://example.net/our_extension" some_string="Another_string">Info_inside_tag<inside_tag first_field="1" secound_field="2" /></example_tag></iq>
            
            self.send_example_message(self.to)
            # <message to="RESPONDER" xml:lang="en" from="SENDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" boolean="True" some_string="Message string">Info_inside_tag_message</example_tag></message>
            
            self.send_example_iq_tag_from_file(self.to, self.path)
            # <iq from="SENDER/RESOURCE" xml:lang="en" id="2" type="get" to="RESPONDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" some_string="Another_string">Info_inside_tag<inside_tag first_field="1" secound_field="2" /></example_tag></iq>
    
            string = '<example_tag xmlns="https://example.net/our_extension" some_string="Another_string">Info_inside_tag<inside_tag first_field="1" secound_field="2" /></example_tag>'
            et = ET.fromstring(string)
            self.send_example_iq_tag_from_element_tree(self.to, et)
            # <iq to="RESPONDER/RESOURCE" id="3" xml:lang="en" from="SENDER/RESOURCE" type="get"><example_tag xmlns="https://example.net/our_extension" some_string="Reply_string" boolean="True">Info_inside_tag<inside_tag secound_field="2" first_field="1" /></example_tag></iq>
    
            self.send_example_iq_to_get_error(self.to)
            # <iq type="get" id="4" from="SENDER/RESOURCE" xml:lang="en" to="RESPONDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" boolean="True" /></iq>
            # OUR ERROR <iq to="RESPONDER/RESOURCE" id="4" xml:lang="en" from="SENDER/RESOURCE" type="error"><example_tag xmlns="https://example.net/our_extension" boolean="True" /><error type="cancel"><feature-not-implemented xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" /><text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas">Without boolean value returns error.</text></error></iq>
            # OFFLINE ERROR <iq id="4" from="RESPONDER/RESOURCE" xml:lang="en" to="SENDER/RESOURCE" type="error"><example_tag xmlns="https://example.net/our_extension" boolean="True" /><error type="cancel" code="503"><service-unavailable xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" /><text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" xml:lang="en">User session not found</text></error></iq>
            
            self.send_example_iq_tag_from_string(self.to, string)
            # <iq to="RESPONDER/RESOURCE" id="5" xml:lang="en" from="SENDER/RESOURCE" type="get"><example_tag xmlns="https://example.net/our_extension" some_string="Reply_string" boolean="True">Info_inside_tag<inside_tag secound_field="2" first_field="1" /></example_tag></iq>
    
    
        def example_tag_result_iq(self, iq):
            self.disconnect_counter -= 1
            logging.info(str(iq))
            if not self.disconnect_counter:
                self.disconnect() # Example disconnect after first received iq stanza extended by example_tag with result type.
    
        def example_tag_error_iq(self, iq):
            self.disconnect_counter -= 1
            logging.info(str(iq))
            if not self.disconnect_counter:
                self.disconnect() # Example disconnect after first received iq stanza extended by example_tag with result type.
    
        def send_example_iq(self, to):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get")
            iq['example_tag'].set_boolean(True)
            iq['example_tag'].set_some_string("Another_string")
            iq['example_tag'].set_text("Info_inside_tag")
            iq.send()
    
        def send_example_iq_with_inner_tag(self, to):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=1)
            iq['example_tag'].set_some_string("Another_string")
            iq['example_tag'].set_text("Info_inside_tag")
            
            inner_attributes = {"first_field": "1", "secound_field": "2"}
            iq['example_tag'].add_inside_tag(tag="inside_tag", attributes=inner_attributes)
    
            iq.send()
    
        def send_example_message(self, to):
            #~ make_message(mfrom=None, mto=None, mtype=None, mquery=None)
            msg = self.make_message(mto=to)
            msg['example_tag'].set_boolean(True)
            msg['example_tag'].set_some_string("Message string")
            msg['example_tag'].set_text("Info_inside_tag_message")
            msg.send()
    
        def send_example_iq_tag_from_file(self, to, path):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=2)
            iq['example_tag'].setup_from_file(path)
    
            iq.send()
    
        def send_example_iq_tag_from_element_tree(self, to, et):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=3)
            iq['example_tag'].setup_from_lxml(et)
    
            iq.send()
    
        def send_example_iq_to_get_error(self, to):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=4)
            iq['example_tag'].set_boolean(True) # For example, our condition to receive error respond is example_tag without boolean value.
            iq.send()
    
        def send_example_iq_tag_from_string(self, to, string):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=5)
            iq['example_tag'].setup_from_string(string)
    
            iq.send()
        
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
        xmpp.register_plugin('OurPlugin', module=example_plugin) # OurPlugin is a class name from example_plugin
    
        xmpp.connect()
        try:
            xmpp.process()
        except KeyboardInterrupt:
            try:
                xmpp.disconnect()
            except:
                pass

~

.. code-block:: python

    #File: $WORKDIR/example/responder.py

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
            self.add_event_handler("example_tag_result_iq", self.example_tag_result_iq)
            self.add_event_handler("example_tag_error_iq", self.example_tag_error_iq)
    
        def start(self, event):
            # Two, not required methods, but allows another users to see us available, and receive that information.
            self.send_presence()
            self.get_roster()
    
            self.disconnect_counter = 6 # This is only for disconnect when we receive all replies for sended Iq
            
            self.send_example_iq(self.to)
            # <iq to=RESPONDER/RESOURCE xml:lang="en" type="get" id="0" from="SENDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" some_string="Another_string" boolean="True">Info_inside_tag</example_tag></iq>
            
            self.send_example_iq_with_inner_tag(self.to)
            # <iq from="SENDER/RESOURCE" to="RESPONDER/RESOURCE" id="1" xml:lang="en" type="get"><example_tag xmlns="https://example.net/our_extension" some_string="Another_string">Info_inside_tag<inside_tag first_field="1" secound_field="2" /></example_tag></iq>
            
            self.send_example_message(self.to)
            # <message to="RESPONDER" xml:lang="en" from="SENDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" boolean="True" some_string="Message string">Info_inside_tag_message</example_tag></message>
            
            self.send_example_iq_tag_from_file(self.to, self.path)
            # <iq from="SENDER/RESOURCE" xml:lang="en" id="2" type="get" to="RESPONDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" some_string="Another_string">Info_inside_tag<inside_tag first_field="1" secound_field="2" /></example_tag></iq>
    
            string = '<example_tag xmlns="https://example.net/our_extension" some_string="Another_string">Info_inside_tag<inside_tag first_field="1" secound_field="2" /></example_tag>'
            et = ET.fromstring(string)
            self.send_example_iq_tag_from_element_tree(self.to, et)
            # <iq to="RESPONDER/RESOURCE" id="3" xml:lang="en" from="SENDER/RESOURCE" type="get"><example_tag xmlns="https://example.net/our_extension" some_string="Reply_string" boolean="True">Info_inside_tag<inside_tag secound_field="2" first_field="1" /></example_tag></iq>
    
            self.send_example_iq_to_get_error(self.to)
            # <iq type="get" id="4" from="SENDER/RESOURCE" xml:lang="en" to="RESPONDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" boolean="True" /></iq>
            # OUR ERROR <iq to="RESPONDER/RESOURCE" id="4" xml:lang="en" from="SENDER/RESOURCE" type="error"><example_tag xmlns="https://example.net/our_extension" boolean="True" /><error type="cancel"><feature-not-implemented xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" /><text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas">Without boolean value returns error.</text></error></iq>
            # OFFLINE ERROR <iq id="4" from="RESPONDER/RESOURCE" xml:lang="en" to="SENDER/RESOURCE" type="error"><example_tag xmlns="https://example.net/our_extension" boolean="True" /><error type="cancel" code="503"><service-unavailable xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" /><text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" xml:lang="en">User session not found</text></error></iq>
            
            self.send_example_iq_tag_from_string(self.to, string)
            # <iq to="RESPONDER/RESOURCE" id="5" xml:lang="en" from="SENDER/RESOURCE" type="get"><example_tag xmlns="https://example.net/our_extension" some_string="Reply_string" boolean="True">Info_inside_tag<inside_tag secound_field="2" first_field="1" /></example_tag></iq>
    
    
        def example_tag_result_iq(self, iq):
            self.disconnect_counter -= 1
            logging.info(str(iq))
            if not self.disconnect_counter:
                self.disconnect() # Example disconnect after first received iq stanza extended by example_tag with result type.
    
        def example_tag_error_iq(self, iq):
            self.disconnect_counter -= 1
            logging.info(str(iq))
            if not self.disconnect_counter:
                self.disconnect() # Example disconnect after first received iq stanza extended by example_tag with result type.
    
        def send_example_iq(self, to):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get")
            iq['example_tag'].set_boolean(True)
            iq['example_tag'].set_some_string("Another_string")
            iq['example_tag'].set_text("Info_inside_tag")
            iq.send()
    
        def send_example_iq_with_inner_tag(self, to):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=1)
            iq['example_tag'].set_some_string("Another_string")
            iq['example_tag'].set_text("Info_inside_tag")
            
            inner_attributes = {"first_field": "1", "secound_field": "2"}
            iq['example_tag'].add_inside_tag(tag="inside_tag", attributes=inner_attributes)
    
            iq.send()
    
        def send_example_message(self, to):
            #~ make_message(mfrom=None, mto=None, mtype=None, mquery=None)
            msg = self.make_message(mto=to)
            msg['example_tag'].set_boolean(True)
            msg['example_tag'].set_some_string("Message string")
            msg['example_tag'].set_text("Info_inside_tag_message")
            msg.send()
    
        def send_example_iq_tag_from_file(self, to, path):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=2)
            iq['example_tag'].setup_from_file(path)
    
            iq.send()
    
        def send_example_iq_tag_from_element_tree(self, to, et):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=3)
            iq['example_tag'].setup_from_lxml(et)
    
            iq.send()
    
        def send_example_iq_to_get_error(self, to):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=4)
            iq['example_tag'].set_boolean(True) # For example, our condition to receive error respond is example_tag without boolean value.
            iq.send()
    
        def send_example_iq_tag_from_string(self, to, string):
            #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
            iq = self.make_iq(ito=to, itype="get", id=5)
            iq['example_tag'].setup_from_string(string)
    
            iq.send()
        
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
        xmpp.register_plugin('OurPlugin', module=example_plugin) # OurPlugin is a class name from example_plugin
    
        xmpp.connect()
        try:
            xmpp.process()
        except KeyboardInterrupt:
            try:
                xmpp.disconnect()
            except:
                pass

~

.. code-block:: python

    #File: $WORKDIR/test_example_tag.xml
.. code-block:: xml

    <example_tag xmlns="https://example.net/our_extension" some_string="StringFromFile">Info_inside_tag<inside_tag first_field="3" secound_field="4" /></example_tag>


Sources and references
----------------------

Slixmpp project description:

* https://pypi.org/project/slixmpp/

Official web documentation:

* https://slixmpp.readthedocs.io/ 


Official pdf documentation:

* https://buildmedia.readthedocs.org/media/pdf/slixmpp/latest/slixmpp.pdf

Note: Web and PDF Documentation have differences and some things aren't mention in the another one (Both ways).



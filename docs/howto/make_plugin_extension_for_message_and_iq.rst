How to make own slixmpp plugin for Message and IQ extension
===========================================================

At first to create a plugin, we need two jabber accounts and two minimal custom slixmpp clients for proper testing. There we create two minimal implementations. In this tutorial I'll call the first one ''client server'', second just ''client'', both I'll call ''clients''. Next step is to create autorun which improves our testing, and lets us test it fast with command arguments without sending our login and password by accident in `__name__ == "__main__"` when we end our plugin and send it with client

About libraries used there:
---------------------------

Minimal implementations are being used here and they contain a few additional features which are very useful for learning about slixmpp and making plugins for that library.

* ``logging``: 

Whenever we use our implementation, we should use logging to receive information which client prints and what it prints.

* ``argparse``: 

To make argument parse easy, and full of possibilites which we are using there for testing.

* ``slixmpp``: 

This lib deosn't need to be explained I think, we are here to learn how to use it to make plugins for it.

If some errors occured, try to install package with pip.

Minimal implementations code:
-----------------------------
Both clients at the beginning are exactly the same. My base implementation is just shortened version of official EchoBOT implementation drawed from official tutorial. So, there is a code, and after you paste it into a second window, you can read my explainations. 

Minimal `Client` and `ResponseClient` implementations:
++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: python

    import logging
    from argparse import ArgumentParser
    from getpass import getpass
    
    import slixmpp
    
    class ResponseClient(slixmpp.ClientXMPP):
        def __init__(self, cmd_args):
            slixmpp.ClientXMPP.__init__(self, cmd_args.jid, cmd_args.password)
            
    
    if __name__ == '__main__':
        parser = ArgumentParser(description=ResponseClient.__doc__)
    
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
        parser.add_argument("-u", "--url", dest="url",
                            help="url name to check")
        parser.add_argument("-r", "--res", dest="res",
                            help="res type to check")
    
        args = parser.parse_args()
    
        logging.basicConfig(level=args.loglevel,
                            format=' %(name)s - %(levelname)-8s %(message)s')
    
        if args.jid is None:
            args.jid = input("Username: ")
        if args.password is None:
            args.password = getpass("Password: ")
    
        try:
            xmpp = ResponseClient(args)
            #xmpp.register_plugin('our_plugin_name', module=our_plugin)
    
            xmpp.connect()
            xmpp.process()
        except KeyboardInterrupt:
            xmpp.disconnect()
            exit(0)

Now, we can create secound file with changing just Class name to Client.
I named them as client.py and response.py. First one should send 'IQ' or 'Message', second one respond with different stanza. 

There we extend base ClientXMPP in slixmpp module and we can add our extensions. But before it, we should create base running script for faster testing, there is a ready script with shell running command with two threads.

Simple running script
+++++++++++++++++++++

.. code-block:: python

    import subprocess
    import _thread
    import time
    import sys
    
    def start_client(threadName, delay):
        subprocess.run("python client.py --debug -j JID -p PASSWORD", shell=True, universal_newlines=True)
    
    def start_server(threadName, delay):
        subprocess.run("python server.py --debug -j JID -p PASSWORD", shell=True, universal_newlines=True)
    
    if __name__ == "__main__":
        sys.path.insert(0, './tutorial_plugin/') #Change secound parameters if path is different, and Clients not in that subfolder
    
        try:
            # Create two threads as follows
            _thread.start_new_thread( start_client, ("Thread-1", 0, ) )
            _thread.start_new_thread( start_server, ("Thread-2", 0, ) )
            while True:
                time.sleep(0.2)
        except:
           print ("Error: unable to start thread")

JID parameter is our 'login' for jabber. And there we can recognise it as shortened JID for example: `slixmpp_plugin@jabber.at` and another one which is called as full JID: `slixmpp_plugin@jabber.at/41327421879132`. For sending IQ stanzas, we should know what recipient full jid are, for message we can freely use shortened one.

PASSWORD parameter is our password for that jabber account.

That way, if our folder with both clients is in github or some other platform, when we send just data in `tutorial_plugin/`, we don't send it with our jid and password by accident. Additionaly, we can test if it is working fast, just with calling our script without loging in every time.

Plugin base code
----------------

Now, we can start to create our plugin, at first we should create some another python file, for tutorial i'll create `base_plugin.py`. I let mine commentary to code still there, to get you more informations about every line.


.. code-block:: python
    
    import logging
    
    from slixmpp.xmlstream import ElementBase, ET, register_stanza_plugin
    
    from slixmpp.stanza import Message
    from slixmpp import Iq
    
    from slixmpp.plugins.base import BasePlugin
    
    from slixmpp.xmlstream.handler import Callback
    from slixmpp.xmlstream.matcher import StanzaPath
    
    log = logging.getLogger(__name__)
    
    class Ope(BasePlugin):
        def plugin_init(self):
            """Plugin init is called one time, when plugins are initialized and independent of another plugins. If some function depends of another module, to make sure if depended module is loaded succesfully, then this feature should be placed in post_init. post_init are called right after plugin_init, then secound time after all another plugins are started. This allows two plugins depended of each other, and initialized with random order."""
            self.description = "OurPluginExtension"                             ##~ String data for Human readable and find plugin by another plugin with method.
            self.xep = "ope"                                            ##~ String data for Human readable and find plugin by another plugin with adding it into `slixmpp/plugins/__init__.py` to the `__all__` declaration with 'xep_OPE'. Otherwise it's just human readable annotation.
            #~ self.is_extension = True                                    ##~ Information if this plugin extend something, default False
            
            BasePlugin.post_init(self)                                  ##~ Initialize base plugin post init, to achieve this method and be sure to registred handlers and tags extension be saved.
            self.xmpp.register_handler( 
                Callback('request',
                         StanzaPath('iq/{{{ns}}}ope'.format(ns=ExampleTag.namespace)),
                         self.__handle_iq))                             ##~ Register handler where to transfer iq stanzas, to check if is extended and fullfilled by DNSPlugin, and raise correct event for client extended by plugin.

            self.xmpp.register_handler(
                Callback('request',
                        StanzaPath('message/{{{ns}}}ope'.format(ns=ExampleTag.namespace)),
                        self.__handle_message))

            register_stanza_plugin(Iq, ExampleTag)                       ##~ Register tags extension for Iq object, otherwise iq['example_tag'] will be string field instead container where we can manage our fields and create sub elements.
            register_stanza_plugin(Message, ExampleTag)
    
        def post_init(self):
            """Post init is called two times, one after plugin_init, and secound time after all plugins do its own post_init. There should be placed function with dependency of another plugin. Two calls of post_init allows to init plugins in random order even depended of each other. Make sure you not place there functions which called two times make your module two times do that same things all along client use that module."""
            pass
    
        def __handle_iq(self, iq):
            """Catch iq stanzas and filter which are extended by our plugin, the next step is to raise correct event and/or build respond for that event if important for plugin logic elements are valid.
            :arg Iq iq: iq stanza which can be extended by filled plugin tag, otherwise no one event will be raised || Required"""
            #~ Do some stuff
            # new_iq = Iq.make_iq(ito=iq['from'], itype="get")
            logging.debug(iq) #~ Call info for us to testing and see it in console log.
            self.xmpp.event('ope_iq', new_iq) #~ Call event which can be handled by clients to send or something other what you want.
    
        def __handle_message(self, msg):
            """Catch Message objects and filter which are extended by our plugin, the next step is to raise correct event and/or build respond for that event if important for plugin logic elements are valid.
            :arg Message msg: Message which can be extended by filled plugin tag, otherwise no one event will be raised || Required"""
            #~ Do some stuff
            logging.debug(msg) #~ Call info for us to testing and see it in console log.
            self.xmpp.event('ope_message', msg) #~ Call event which can be handled by clients to send or something other what you want.
    
    """Note: There are not many differences about __handle_iq and __handle_message, but Iq to send back must be rebuilded, message we can freely modify and send back without creating new object. Iq have limited lifetime."""
    
    class ExampleTag(ElementBase):
        name = "example_tag"                                                 ##~ The name of the root XML element of that extension.
        namespace = "https://example.net/our_extension"                   ##~ The namespace our stanza object lives in, like <example_tag xmlns={namespace} (...)</example_tag>
    
        plugin_attrib = "example_tag"                                        ##~ The name to access this type of stanza. In particular, given  a  registration  stanza,  the Registration object can be found using: stanza_object['example_tag'] now `'example_tag'` is name of ours ElementBase extension.
        
        interfaces = {"another", "data"}                                ##~ A list of dictionary-like keys that can be used with the stanza object. For example `stanza_object['example_tag']` gives us {"another": "some", "data": "some"}, whenever `'example_tag'` is name of ours ElementBase extension.
    
        def fill_interfaces(self, another, data):
            #Some validation if it is necessary
            self.xml.attrib.update({'another': another})                      ##~ Add/update name parameter
            self.xml.attrib.update({'data': data})                        ##~ Add/update res parameter
        
        def add_field(self, tag, dictionary_with_elements, text):
            #If we want to fill with additionaly tags our element, then we can do it that way for example:
            itemXML = ET.Element("{{{0:s}}}{1:s}".format(self.namespace, tag)) #~ Initialize ET with our tag, for example: <example_tag (...)> <inside_tag namespace="https://example.net/our_extension"/></example_tag>
            itemXML.attrib.update(dictionary_with_elements) #~ There we add some fields inside tag, for example: <inside_tag namespace=(...) inner_data="some"/>
            itemXML.text = text #~ Fill field inside tag, for example: <inside_tag (...)>our_text</inside_tag>
            self.xml.append(itemXML) #~ Add that all what we set, as inner tag inside `example_tag` tag.

Adding plugin to Clients:
+++++++++++++++++++++++++

Now if we had our plugin, we should add it to our class.

At first, we should import our plugin, we can do this with line as follows, in import section:

.. code-block:: python

    import base_plugin
    
Next step is to register our plugin, to be visible and used in our Client. For do this, find this fragment:

.. code-block:: python

        try:
            xmpp = ResponseClient(args)
            #xmpp.register_plugin('Ope', module=base_plugin)


Now, the last line from that fragment, should be uncommented and changed.

First parameter is the name of our plugin class, there will be replaced by `'OurPlugin'`.

Keyword paramter `module` is a source, how our file with plugin is represented, we import our plugin as `base_plugin` and this should be passed as argument for `module`.

Now we have registred our plugin for clients. Do the same in both of them.

Now we want to send a message from our Client, to ResponseClient, to do it, we should remember a few things.

Message object must have some body, otherwise base protocol doesn't allow us to send it to our recipient.

At `__init__` method, we can't send message, because already we aren't sure our Client is fully connected and started. So at first, we should add handler to our Client which will catch start signal from slixmpp.ClientXMPP.

Get started with signals:
-------------------------

Let's look at the code below:

.. code-block:: python

    class Client(slixmpp.ClientXMPP):
        def __init__(self, cmd_args):
            slixmpp.ClientXMPP.__init__(self, cmd_args.jid, cmd_args.password)
            
            self.add_event_handler("session_start", self.start)
    
        def start(self, event):
            pass

`add_event_handler` is a method from ClientXMPP which catches signals for us, and lets us handle our signal with our code when signal is called.

First parameter is a name of the signal, let's take a look backwards at our plugin for these lines:

.. code-block:: python

            self.xmpp.event('ope_iq', new_iq)
    (...)
            self.xmpp.event('ope_message', msg)
    
There we can find our signals names and objects which we pass with signals, which we after can handle.

Secound parameter is function with which we process our handled signal.

In this case, we want after "session_start" signal send extended message with our plugin. To do so, at first we should make Message object with buildin method, and extend it with our plugin. It's simple and clear, if you know how this should look. Check this method as an example, and try to understand it before you paste it into your Client:

Start signal with extended message sending:
+++++++++++++++++++++++++++++++++++++++++++

.. code-block:: python

    def start(self, event):
        # Two, not required methods, but allows another users to see us available, and receive that information.
        self.send_presence()
        self.get_roster()

        # Create at first standard Message object.
        msg_object = self.make_message( mto="RECIPIENT_JID", # There is login/mail/jid whatever you like to call it, of our recipient. Let use jid name, for proper terminology connected with jabber. (JID - Jabber Id)
                                        mbody="OUR_MESSAGE", # There is body of our message, which basicaly our recipient see if we send it. There body can't be empty in messages, otherwise, our recipient don't ever receive it. 
                                        mtype="chat") # Default is chat, so we can avoid specify it. But we can call another type, then we should look to documentation about allowed types.
        # Now we want to extend message with our tags. To do it, we can just call it as extended message:
        msg_object['example_tag'].fill_interfaces(another="some", data="stuff")

        #Last thing to do, is do something with our message. I think you know what to do with messages, just send it :).
        msg_object.send()

Catching our signal from plugin:
++++++++++++++++++++++++++++++++

Now, if our Client is ready to send Message, we should adapt our ResponseClient to receive and show our success.

You remember when I was talking about `add_event_handler`. Find your signal's name, and read code below:

.. code-block:: python

    class ResponseClient(slixmpp.ClientXMPP):
        def __init__(self, cmd_args):
            slixmpp.ClientXMPP.__init__(self, cmd_args.jid, cmd_args.password)
            
            self.add_event_handler("ope_message", self.receive_plugin_message)
    
        def receive_plugin_message(self, msg):
            print("SUCCESS!!")
            print(msg)
            print("SUCCESS!!")

Test and fit message extension on your own:
-------------------------------------------

Now, there is your job to edit JID and PASSWORD for proper log in for both clients with your running script. And, test your first plugin message.

If you do so, and they are all working, you can go into the next step.

Otherwise, stop for a moment, check if anything you rewrite or copy/paste isn't missing something. If everything is working fine, and you haven't adjusted your base_plugin code yet, do it on your own, and test it. For example, if you want to send some hidden data, then make message to look like this:

.. code-block:: xml

    <message type="chat" from=YOU xml:lang="en" to=RECIPIENT><example_tag xmlns="https://example.net/our_extension" another="some" data="stuff"/><body>OUR_MESSAGE</body></message>

#Tip: I show how to add text into subtags, if you want to do this example, you should consider how logically achieve `text` field inside your main tag. It's simple, but if you want to consider it little more, and try to resolve it on your own, don't read any further before you solve it or give up. It can be possible to achieve it inside plugin, and with client. With client, it is simple after we call `msg_object['plugin'].fill_interfaces`, we can edit text by Object attribute of Message Class, like this: `msg_object['plugin'].text = "some text"`. Or inside fill_interfaces function, with editing our self.xml object like in add_field method, so just by adding `self.xml.text = "some_text"`. This is simple way of editing our xml to hold any information we want.

With some text inside, should look like this:

.. code-block:: xml

    <message type="chat" from=YOU xml:lang="en" to=RECIPIENT><example_tag xmlns="https://example.net/our_extension" another="some" data="stuff">SOME_TEXT</example_tag><body>OUR_MESSAGE</body></message>

Access to Message object
++++++++++++++++++++++++

There, you should have some personalized example of plugin, great. Remember or describe elsewhere what names you changed to your own names.

With Iq stanza there is not many changes to adapt this example. There is just a few names to change and instead of using shortened jid, we have to use full jid of our recipient to send the iq.

So, we make our server now responsible. We want to get data from custom message, and send back Iq stanza from ResponseClient to Client.

To do it, at first we have to withdraw some data, for example, there we want to get text inside our plugin tag, one field of our tag, body from message and information who is the recipient of ResponseClient Iq. At first step, we can consider handling `'session_start'` but, if our session hasen't already started. Then we don't receive message, so our ResponseClient still doesn't need to have start method.

Let's get information from our message, We can easly have an access to Message attributes like with dictionary: ['element_name']

Before we start, we should look how it is accessible:

.. code-block:: python

    def receive_plugin_message(self, msg):
        print("SUCCESS!!")
        print(msg['body'])
        print(msg['example_tag']['data'])
        print("SUCCESS!!")

Run it with these changes (applying your changed names, if you changed them) and you should see body of your previous message, and that what you declare with fill_interfaces on Client side as `'data'` field for plugin message.

Start with Iq Stanza objects
----------------------------

Now, you should know how to access message elements, you can assign it to variables. It will always be as string type which you can edit, parse or do some else. For Iq is also necessary to get this user online, because, if you log in with the same bare (jid before slash, user and domain) to your jabber on many devices, full jid will be different for all of them. The difference concerns only a part of jid after slash, for example, look at this jids, two from different devices, had different resources: `slixmpp_plugin@jabber.at/41327421879132`, `slixmpp_plugin@jabber.at/7893241740109` but log in are with that same bare `slixmpp_plugin@jabber.at` and that same password. If you want to force constant jid, you can log in with your full jid using this shema: [user@]domain[/resource]. But, two devices can't be logged at the same time, with that same JID and resource. 

Okay, I think now you understand what is bare and resource in full jid. Now, we can start to extend our Iq stanza. After we collect data interesting for us from Message, then we can send back Iq to our client. Like last time, we should create eligible object and send it to another user, in this case this user will be a sender and our Client.

At first, we should create another function for our ResponseClient with a proper name to sending Iq.

Method to extract data from message to our Iq
+++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: python

    def send_iq_response(self, to, mbody, **kwargs):
        iq_to = to
        iq_type = kwargs.pop("type", "result")
        plugin_data = kwargs.pop("pdata", "")
        plugin_another = kwargs.pop("panother", "")
        plugin_text = mbody

* iq_to: This is full jid of recipient.
* iq_type: There are four types of iq stanzas: get, set, result, or error.
* plugin_data: We want to get pdata key from kwargs.
* plugin_another: We want to get panother key from kwargs.
* plugin_text: There we use mbody as plugin text field.

To send that arguments, we should modify `receive_plugin_message` and there call method. Or change parameters, call signal and give whole msg_object instead of selected elements. I choose first way to do it:

Calling our method which extract data
+++++++++++++++++++++++++++++++++++++

.. code-block:: python

    def receive_plugin_message(self, msg):
        print("RECEIVED:", msg)
        send_iq_response(   to=msg["from"],
                            mbody=msg["body"],
                            type="result",
                            pdata=msg["example_tag"]["data"],
                            panother=msg["example_tag"]["another"])

Okay, we are calling now our method with send_iq_response, now we have to build iq, and by doing it is almost the same way like in message object, but there are differences in name of parameters, instead 'm` we are calling parameters with 'i' prefix.

Build our Iq Stanza object
++++++++++++++++++++++++++

.. code-block:: python

    def send_iq_response(self, to, mbody, **kwargs):
        iq_to = to
        iq_type = kwargs.pop("type", "result")
        plugin_data = kwargs.pop("pdata", "")
        plugin_another = kwargs.pop("panother", "")
        plugin_text = mbody
        iq = Iq.make_iq(ito=iq_to, itype=iq_type)
        iq['example_tag'].fill_interfaces(plugin_another, plugin_data, text=plugin_text)

But there, we will have an error. Because our fill_interfaces last time when I showed it had only two arguments. Then we should extend it a litte, with backward compatibility. And additionaly, text is our optional argument. So, go back to our basic_plugin.py and find fill_interfaces method, and correct it like in example below:

Little extension for plugin method
++++++++++++++++++++++++++++++++++

.. code-block:: python

    def fill_interfaces(self, another, data, **kwargs):
        #Some validation if it is necessary
        self.xml.attrib.update({'another': another})
        self.xml.attrib.update({'data': data})
        text = kwargs.get("text", "")
        if text:
            self.xml.text = text

Now our fill_interfaces shouldn't call an error when called, we can go back to our send_iq_response in ResponseClient. Only one line is still missing: `iq.send()`. When we are sending our Iq, we can handle receiving it inside our Client. We should handle signal, as we desired in __handle_iq method. In my example, it is `"event_name_iq"`. When we know the signal's name, we should create a method to handle our signal and register this method for that signal with `'add_event_handler'` method in __init__. Now our Client should look like this:

Catch signal with Iq stanza
+++++++++++++++++++++++++++

Client should look like:

.. code-block:: python

    class Client(slixmpp.ClientXMPP):
        def __init__(self, cmd_args):
            slixmpp.ClientXMPP.__init__(self, cmd_args.jid, cmd_args.password)
            
            self.add_event_handler("session_start", self.start)
            self.add_event_handler("ope_iq", self.receive_plugin_iq)
    
        def start(self, event):
            self.send_presence()
            self.get_roster()
    
            msg_object = self.make_message( mto="RECIPIENT_JID",
                                            mbody="OUR_MESSAGE",
                                            mtype="chat")
            msg_object['example_tag'].fill_interfaces(another="some", data="stuff")
            msg_object.send()
            
        def receive_plugin_iq(self, iq):
            print("SUCCESS!!")
            print(iq)
            print("SUCCESS!!")
            self.disconnect()
        
ResponseClient should look like:

.. code-block:: python

    class ResponseClient(slixmpp.ClientXMPP):
        def __init__(self, cmd_args):
            slixmpp.ClientXMPP.__init__(self, cmd_args.jid, cmd_args.password)
            
            self.add_event_handler("ope_msg", self.receive_plugin_message)
    
        def receive_plugin_message(self, msg):
            print("RECEIVED:", msg)
            send_iq_response(   to=msg["from"],
                                mbody=msg["body"],
                                type="result",
                                pdata=msg["example_tag"]["data"],
                                panother=msg["example_tag"]["another"])
    
        def send_iq_response(self, to, mbody, **kwargs):
            iq_to = to
            iq_type = kwargs.pop("type", "result")
            plugin_data = kwargs.pop("pdata", "")
            plugin_another = kwargs.pop("panother", "")
            plugin_text = mbody
            iq = Iq.make_iq(ito=iq_to, itype=iq_type)
            iq['example_tag'].fill_interfaces(plugin_another, plugin_data, text=plugin_text)
            iq.send()
            self.disconnect()


Test it, if something is calling an error, return to previous steps and make sure you don't rewrite something wrong or don't make any typo.

At the end, I think you should know and understand how to extend iq stanzas and messages. Now, it is your idea how to extend it, what to add inside `#doing some stuff` etc.

For example you can send with xmpp data from numpy to server, server will process this and send you a respond after doing some work. But elements like this, should be processed inside plugin, Clients implementation just have to decide what to do with this, who is confidental to receive that information etc. For example, you can set a password, create permission table, and authorize only people which have sent proper password :)

Usefull reference:
------------------

In this link, you should find another useful methods: https://slixmpp.readthedocs.io/api/basexmpp.html

There, you should find reference to many different tricks with slixmpp and additional explainations: https://buildmedia.readthedocs.org/media/pdf/slixmpp/latest/slixmpp.pdf

If I do some mistakes or something isn't readable, please tell me about that, there is my jabber: maciej.pawlowski@jabber.at



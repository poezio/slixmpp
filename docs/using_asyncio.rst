.. _using_asyncio:

=============
Using asyncio
=============

Block on IQ sending
~~~~~~~~~~~~~~~~~~~

:meth:`.Iq.send` now returns a :class:`~.Future` so you can easily block with:

.. code-block:: python

    result = yield from iq.send()

.. warning::

    If the reply is an IQ with an ``error`` type, this will raise an
    :class:`.IqError`, and if it timeouts, it will raise an
    :class:`.IqTimeout`. Don't forget to catch it.

You can still use callbacks instead.

XEP plugin integration
~~~~~~~~~~~~~~~~~~~~~~

The same changes from the SleekXMPP API apply, so you can do:

.. code-block:: python

    iq_info = yield from self.xmpp['xep_0030'].get_info(jid)

But the following will only return a Future:

.. code-block:: python

    iq_info = self.xmpp['xep_0030'].get_info(jid)


Callbacks, Event Handlers, and Stream Handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

IQ callbacks and :term:`Event Handlers <event handler>` can be coroutine
functions; in this case, they will be scheduled in the event loop using
:meth:`.asyncio.async` and not ran immediately.

A :class:`.CoroutineCallback` class has been added as well for
:term:`Stream Handlers <stream handler>`, which will use
:meth:`.asyncio.async` to schedule the callback.

Running the event loop
~~~~~~~~~~~~~~~~~~~~~~

You can handle the event loop in any way you like, either forever, until an
event, only for a specific duration, in conjonction with another asyncio user,
anything goes.  But remember slixmpp will only process events and send messages
when its event loop is running.


Examples
~~~~~~~~

Blocking until the session is established
-----------------------------------------

This code blocks until the XMPP session is fully established, which
can be useful to make sure external events aren’t triggering XMPP
callbacks while everything is not ready.

.. code-block:: python

    import asyncio, slixmpp

    client = slixmpp.ClientXMPP('jid@example', 'password')
    client.connected_event = asyncio.Event()
    callback = lambda _: client.connected_event.set()
    client.add_event_handler('session_start', callback)
    client.connect()
    loop.run_until_complete(event.wait())
    # do some other stuff before running the event loop, e.g.
    # loop.run_until_complete(httpserver.init())
    asyncio.get_event_loop().run_forever()


Use with other asyncio-based libraries
--------------------------------------

This code interfaces with aiohttp to retrieve two pages asynchronously
when the session is established, and then send the HTML content inside
a simple <message>.

.. code-block:: python

    import asyncio, aiohttp, slixmpp

    @asyncio.coroutine
    def get_pythonorg(event):
        req = yield from aiohttp.request('get', 'http://www.python.org')
        text = yield from req.text
        client.send_message(mto='jid2@example', mbody=text)

    @asyncio.coroutine
    def get_asyncioorg(event):
        req = yield from aiohttp.request('get', 'http://www.asyncio.org')
        text = yield from req.text
        client.send_message(mto='jid3@example', mbody=text)

    client = slixmpp.ClientXMPP('jid@example', 'password')
    client.add_event_handler('session_start', get_pythonorg)
    client.add_event_handler('session_start', get_asyncioorg)
    client.connect()
    asyncio.get_event_loop().run_forever()


Blocking Iq
-----------

This client checks (via XEP-0092) the software used by every entity it
receives a message from. After this, it sends a message to a specific
JID indicating its findings.

.. code-block:: python

    import asyncio, slixmpp

    class ExampleClient(slixmpp.ClientXMPP):
        def __init__(self, *args, **kwargs):
            slixmpp.ClientXMPP.__init__(self, *args, **kwargs)
            self.register_plugin('xep_0092')
            self.add_event_handler('message', self.on_message)

        @asyncio.coroutine
        def on_message(self, event):
            # You should probably handle IqError and IqTimeout exceptions here
            # but this is an example.
            version = yield from self['xep_0092'].get_version(message['from'])
            text = "%s sent me a message, he runs %s" % (message['from'],
                                                         version['software_version']['name'])
            self.send_message(mto='master@example.tld', mbody=text)

    client = ExampleClient('jid@example', 'password')
    client.connect()
    asyncio.get_event_loop().run_forever()



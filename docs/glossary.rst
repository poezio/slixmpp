.. _glossary:

Glossary
========

.. glossary::
    :sorted:

    stream handler
        A callback function that accepts stanza objects pulled directly
        from the XML stream. A stream handler is encapsulated in a
        object that includes a :class:`Matcher <.MatcherBase>` object, and
        which provides additional semantics. For example, the
        :class:`.Waiter` handler wrapper blocks thread execution until a
        matching stanza is received.

    event handler
        A callback function that responds to events raised by
        :meth:`.XMLStream.event`.

    stanza object
        Informally may refer both to classes which extend :class:`.ElementBase`
        or :class:`.StanzaBase`, and to objects of such classes.

        A stanza object is a wrapper for an XML object which exposes :class:`dict`
        like interfaces which may be assigned to, read from, or deleted.

    stanza plugin
        A :term:`stanza object` which has been registered as a potential child
        of another stanza object. The plugin stanza may accessed through the
        parent stanza using the plugin's ``plugin_attrib`` as an interface.

    substanza
        See :term:`stanza plugin`

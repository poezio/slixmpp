Event Index
===========

.. glossary::
    :sorted:

    connected
        - **Data:** ``{}``
        - **Source:** :py:class:`~slixmpp.xmlstream.XMLstream`

        Signal that a connection has been made with the XMPP server, but a session
        has not yet been established.

    connection_failed
        - **Data:** ``{}`` or ``Failure Stanza`` if available
        - **Source:** :py:class:`~slixmpp.xmlstream.XMLstream`

        Signal that a connection can not be established after number of attempts.

    changed_status
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.roster.item.RosterItem`

        Triggered when a presence stanza is received from a JID with a show type
        different than the last presence stanza from the same JID.

    changed_subscription
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.BaseXMPP`

        Triggered whenever a presence stanza with a type of ``subscribe``,
        ``subscribed``, ``unsubscribe``, or ``unsubscribed`` is received.

        Note that if the values ``xmpp.auto_authorize`` and ``xmpp.auto_subscribe``
        are set to ``True`` or ``False``, and not ``None``, then Slixmpp will
        either accept or reject all subscription requests before your event handlers
        are called. Set these values to ``None`` if you wish to make more complex
        subscription decisions.

    chatstate_active
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0085.xep_0085`

    chatstate_composing
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0085.xep_0085`

    chatstate_gone
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0085.xep_0085`

    chatstate_inactive
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0085.xep_0085`

    chatstate_paused
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0085.xep_0085`

    disco_info
        - **Data:** :py:class:`~slixmpp.plugins.xep_0030.stanza.DiscoInfo`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0030.disco.xep_0030`

        Triggered whenever a ``disco#info`` result stanza is received.

    disco_items
        - **Data:** :py:class:`~slixmpp.plugins.xep_0030.stanza.DiscoItems`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0030.disco.xep_0030`

        Triggered whenever a ``disco#items`` result stanza is received.

    disconnected
        - **Data:** ``{}``
        - **Source:** :py:class:`~slixmpp.xmlstream.XMLstream`

        Signal that the connection with the XMPP server has been lost.

    entity_time
        - **Data:**
        - **Source:**

    failed_auth
        - **Data:** ``{}``
        - **Source:** :py:class:`~slixmpp.ClientXMPP`, :py:class:`~slixmpp.plugins.xep_0078.xep_0078`

        Signal that the server has rejected the provided login credentials.

    gmail_notify
        - **Data:** ``{}``
        - **Source:** :py:class:`~slixmpp.plugins.gmail_notify.gmail_notify`

        Signal that there are unread emails for the Gmail account associated with the current XMPP account.

    gmail_messages
        - **Data:** :py:class:`~slixmpp.Iq`
        - **Source:** :py:class:`~slixmpp.plugins.gmail_notify.gmail_notify`

        Signal that there are unread emails for the Gmail account associated with the current XMPP account.

    got_online
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.roster.item.RosterItem`

        If a presence stanza is received from a JID which was previously marked as
        offline, and the presence has a show type of '``chat``', '``dnd``', '``away``',
        or '``xa``', then this event is triggered as well.

    got_offline
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.roster.item.RosterItem`

        Signal that an unavailable presence stanza has been received from a JID.

    groupchat_invite
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0045.XEP_0045`

    groupchat_direct_invite
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0249.direct`

    groupchat_message
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0045.xep_0045`

        Triggered whenever a message is received from a multi-user chat room.

    groupchat_presence
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0045.xep_0045`

        Triggered whenever a presence stanza is received from a user in a multi-user chat room.

    groupchat_subject
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0045.xep_0045`

        Triggered whenever the subject of a multi-user chat room is changed, or announced when joining a room.

    killed
        - **Data:**
        - **Source:**

    last_activity
        - **Data:**
        - **Source:**

    message
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`BaseXMPP <slixmpp.BaseXMPP>`

        Makes the contents of message stanzas available whenever one is received. Be
        sure to check the message type in order to handle error messages.

    message_error
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`BaseXMPP <slixmpp.BaseXMPP>`

        Makes the contents of message stanzas available whenever one is received.
        Only handler messages with an ``error`` type.

    message_form
        - **Data:** :py:class:`~slixmpp.plugins.xep_0004.Form`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0004.xep_0004`

        Currently the same as :term:`message_xform`.

    message_xform
        - **Data:** :py:class:`~slixmpp.plugins.xep_0004.Form`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0004.xep_0004`

        Triggered whenever a data form is received inside a message.

    muc::[room]::got_offline
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0045.XEP_0045`

    muc::[room]::got_online
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0045.XEP_0045`

    muc::[room]::message
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0045.XEP_0045`

    muc::[room]::presence
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0045.XEP_0045`

    presence_available
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.BaseXMPP`

        A presence stanza with a type of '``available``' is received.

    presence_error
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.BaseXMPP`

        A presence stanza with a type of '``error``' is received.

    presence_form
        - **Data:** :py:class:`~slixmpp.plugins.xep_0004.Form`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0004.xep_0004`

        This event is present in the XEP-0004 plugin code, but is currently not used.

    presence_probe
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.BaseXMPP`

        A presence stanza with a type of '``probe``' is received.

    presence_subscribe
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.BaseXMPP`

        A presence stanza with a type of '``subscribe``' is received.

    presence_subscribed
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.BaseXMPP`

        A presence stanza with a type of '``subscribed``' is received.

    presence_unavailable
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.BaseXMPP`

        A presence stanza with a type of '``unavailable``' is received.

    presence_unsubscribe
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.BaseXMPP`

        A presence stanza with a type of '``unsubscribe``' is received.

    presence_unsubscribed
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.BaseXMPP`

        A presence stanza with a type of '``unsubscribed``' is received.

    roster_update
        - **Data:** :py:class:`~slixmpp.stanza.Roster`
        - **Source:** :py:class:`~slixmpp.ClientXMPP`

        An IQ result containing roster entries is received.

    sent_presence
        - **Data:** ``{}``
        - **Source:** :py:class:`~slixmpp.roster.multi.Roster`

        Signal that an initial presence stanza has been written to the XML stream.

    session_end
        - **Data:** ``{}``
        - **Source:** :py:class:`~slixmpp.xmlstream.XMLstream`

        Signal that a connection to the XMPP server has been lost and the current
        stream session has ended. Currently equivalent to :term:`disconnected`, but
        implementations of `XEP-0198: Stream Management <http://xmpp.org/extensions/xep-0198.html>`_
        distinguish between the two events.

        Plugins that maintain session-based state should clear themselves when
        this event is fired.

    session_start
        - **Data:** ``{}``
        - **Source:** :py:class:`ClientXMPP <slixmpp.ClientXMPP>`,
          :py:class:`ComponentXMPP <slixmpp.ComponentXMPP>`
          :py:class:`XEP-0078 <slixmpp.plugins.xep_0078>`

        Signal that a connection to the XMPP server has been made and a session has been established.

    socket_error
        - **Data:** ``Socket`` exception object
        - **Source:** :py:class:`~slixmpp.xmlstream.XMLstream`

    stream_error
        - **Data:** :py:class:`~slixmpp.stanza.StreamError`
        - **Source:** :py:class:`~slixmpp.BaseXMPP`

    reactions
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0444.XEP_0444`

    carbon_received
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0280.XEP_0280`

    carbon_sent
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0280.XEP_0280`

    marker
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0333.XEP_0333`

    marker_received
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0333.XEP_0333`

    marker_displayed
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0333.XEP_0333`

    marker_acknowledged
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0333.XEP_0333`

    attention
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0224.XEP_0224`

    message_correction
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0308.XEP_0308`

    receipt_received
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0184.XEP_0184`

    jingle_message_propose
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0353.XEP_0353`

    jingle_message_retract
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0353.XEP_0353`

    jingle_message_accept
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0353.XEP_0353`

    jingle_message_proceed
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0353.XEP_0353`

    jingle_message_reject
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0353.XEP_0353`

    room_activity
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0437.XEP_0437`

    room_activity_bare
        - **Data:** :py:class:`~slixmpp.Presence`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0437.XEP_0437`

    sm_enabled
        - **Data:** :py:class:`~slixmpp.plugins.xep_0198.stanza.Enabled`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0198.XEP_0198`

    sm_disabled
        - **Data:**
        - **Source:** :py:class:`~slixmpp.plugins.xep_0198.XEP_0198`

    ibb_stream_start
        - **Data:** :py:class:`~slixmpp.plugins.xep_0047.stream.IBBBytestream`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0047.XEP_0047`

    ibb_stream_end
        - **Data:** :py:class:`~slixmpp.plugins.xep_0047.stream.IBBBytestream`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0047.XEP_0047`

    ibb_stream_data
        - **Data:** :py:class:`~slixmpp.plugins.xep_0047.stream.IBBBytestream`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0047.XEP_0047`

    stream:[stream id]:[peer jid]
        - **Data:** :py:class:`~slixmpp.plugins.xep_0047.stream.IBBBytestream`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0047.XEP_0047`

    command
        - **Data:** :py:class:`~slixmpp.Iq`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0050.XEP_0050`

    command_[action]
        - **Data:** :py:class:`~slixmpp.Iq`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0050.XEP_0050`

    pubsub_publish
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0060.XEP_0060`

    pubsub_retract
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0060.XEP_0060`

    pubsub_purge
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0060.XEP_0060`

    pubsub_delete
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0060.XEP_0060`

    pubsub_config
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0060.XEP_0060`

    pubsub_subscription
        - **Data:** :py:class:`~slixmpp.Message`
        - **Source:** :py:class:`~slixmpp.plugins.xep_0060.XEP_0060`

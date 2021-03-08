# Slixmpp: The Slick XMPP Library
# Copyright (C) 2012 Nathanael C. Fritz, Lance J.T. Stout
# This file is part of Slixmpp.
# See the file LICENSE for copying permissio
from datetime import datetime
from typing import (
    Any,
    Iterable,
    List,
    Optional,
    Set,
    Union,
)

from slixmpp.stanza import Message
from slixmpp.jid import JID
from slixmpp.xmlstream import ElementBase, ET
from slixmpp.plugins import xep_0082


class MAM(ElementBase):
    """A MAM Query element.

    .. code-block:: xml

        <iq type='set' id='juliet1'>
          <query xmlns='urn:xmpp:mam:2'>
            <x xmlns='jabber:x:data' type='submit'>
              <field var='FORM_TYPE' type='hidden'>
                <value>urn:xmpp:mam:2</value>
              </field>
              <field var='with'>
                <value>juliet@capulet.lit</value>
              </field>
            </x>
          </query>
        </iq>

    """
    name = 'query'
    namespace = 'urn:xmpp:mam:2'
    plugin_attrib = 'mam'
    #: Available interfaces:
    #:
    #: - ``queryid``: The MAM query id
    #: - ``start`` and ``end``: Temporal boundaries of the query
    #: - ``with``: JID of the other entity the conversation is with
    #: - ``after_id``: Fetch stanzas after this specific ID
    #: - ``before_id``: Fetch stanzas before this specific ID
    #: - ``ids``: Fetch the stanzas matching those IDs
    #: - ``results``: pseudo-interface used to accumulate MAM results during
    #:   fetch, not relevant for the stanza itself.
    interfaces = {
        'queryid', 'start', 'end', 'with', 'results',
        'before_id', 'after_id', 'ids',
    }
    sub_interfaces = {'start', 'end', 'with', 'before_id', 'after_id', 'ids'}

    def setup(self, xml=None):
        ElementBase.setup(self, xml)
        self._results: List[Message] = []

    def _setup_form(self):
        found = self.xml.find(
                '{jabber:x:data}x/'
                '{jabber:x:data}field[@var="FORM_TYPE"]/'
                "{jabber:x:data}value[.='urn:xmpp:mam:2']"
        )
        if found is None:
            self['form']['type'] = 'submit'
            self['form'].add_field(
                var='FORM_TYPE', ftype='hidden', value='urn:xmpp:mam:2'
            )

    def get_fields(self):
        form = self.get_plugin('form', check=True)
        if not form:
            return {}
        return form.get_fields()

    def get_start(self) -> Optional[datetime]:
        fields = self.get_fields()
        field = fields.get('start')
        if field:
            return xep_0082.parse(field['value'])
        return None

    def set_start(self, value: Union[str, datetime]):
        self._setup_form()
        if isinstance(value, datetime):
            value = xep_0082.format_datetime(value)
        self.set_custom_field('start', value)

    def get_end(self) -> Optional[datetime]:
        fields = self.get_fields()
        field = fields.get('end')
        if field:
            return xep_0082.parse(field['value'])
        return None

    def set_end(self, value: Union[str, datetime]):
        if isinstance(value, datetime):
            value = xep_0082.format_datetime(value)
        self.set_custom_field('end', value)

    def get_with(self) -> Optional[JID]:
        fields = self.get_fields()
        field = fields.get('with')
        if field:
            return JID(field['value'])
        return None

    def set_with(self, value: JID):
        self.set_custom_field('with', value)

    def set_custom_field(self, fieldname: str, value: Any):
        self._setup_form()
        fields = self.get_fields()
        field = fields.get(fieldname)
        if field:
            field['value'] = str(value)
        else:
            field = self['form'].add_field(var=fieldname)
            field['value'] = str(value)

    def get_custom_field(self, fieldname: str) -> Optional[str]:
        fields = self.get_fields()
        field = fields.get(fieldname)
        if field:
            return field['value']
        return None

    def set_before_id(self, value: str):
        self.set_custom_field('before-id', value)

    def get_before_id(self):
        self.get_custom_field('before-id')

    def set_after_id(self, value: str):
        self.set_custom_field('after-id', value)

    def get_after_id(self):
        self.get_custom_field('after-id')

    def set_ids(self, value: List[str]):
        self._setup_form()
        fields = self.get_fields()
        field = fields.get('ids')
        if field:
            field['ids'] = value
        else:
            field = self['form'].add_field(var='ids')
            field['value'] = value

    def get_ids(self):
        self.get_custom_field('id')

    # The results interface is meant only as an easy
    # way to access the set of collected message responses
    # from the query.

    def get_results(self) -> List[Message]:
        return self._results

    def set_results(self, values: List[Message]):
        self._results = values

    def del_results(self):
        self._results = []


class Preferences(ElementBase):
    """MAM Preferences payload.

    .. code-block:: xml

        <iq type='set' id='juliet3'>
          <prefs xmlns='urn:xmpp:mam:2' default='roster'>
            <always>
              <jid>romeo@montague.lit</jid>
            </always>
            <never>
              <jid>montague@montague.lit</jid>
            </never>
          </prefs>
        </iq>

    """
    name = 'prefs'
    namespace = 'urn:xmpp:mam:2'
    plugin_attrib = 'mam_prefs'
    #: Available interfaces:
    #:
    #: - ``default``: Default MAM policy (must be one of 'roster', 'always',
    #:   'never'
    #: - ``always``  (``List[JID]``): list of JIDs to always store
    #:   conversations with.
    #: - ``never``  (``List[JID]``): list of JIDs to never store
    #:   conversations with.
    interfaces = {'default', 'always', 'never'}
    sub_interfaces = {'always', 'never'}

    def get_always(self) -> Set[JID]:
        results = set()

        jids = self.xml.findall('{%s}always/{%s}jid' % (
            self.namespace, self.namespace))

        for jid in jids:
            results.add(JID(jid.text))

        return results

    def set_always(self, value: Iterable[JID]):
        self._set_sub_text('always', '', keep=True)
        always = self.xml.find('{%s}always' % self.namespace)
        always.clear()

        if not isinstance(value, (list, set)):
            value = [value]

        for jid in value:
            jid_xml = ET.Element('{%s}jid' % self.namespace)
            jid_xml.text = str(jid)
            always.append(jid_xml)

    def get_never(self) -> Set[JID]:
        results = set()

        jids = self.xml.findall('{%s}never/{%s}jid' % (
            self.namespace, self.namespace))

        for jid in jids:
            results.add(JID(jid.text))

        return results

    def set_never(self, value: Iterable[JID]):
        self._set_sub_text('never', '', keep=True)
        never = self.xml.find('{%s}never' % self.namespace)
        never.clear()

        if not isinstance(value, (list, set)):
            value = [value]

        for jid in value:
            jid_xml = ET.Element('{%s}jid' % self.namespace)
            jid_xml.text = str(jid)
            never.append(jid_xml)


class Fin(ElementBase):
    name = 'fin'
    namespace = 'urn:xmpp:mam:2'
    plugin_attrib = 'mam_fin'

class Result(ElementBase):
    name = 'result'
    namespace = 'urn:xmpp:mam:2'
    plugin_attrib = 'mam_result'
    interfaces = {'queryid', 'id'}

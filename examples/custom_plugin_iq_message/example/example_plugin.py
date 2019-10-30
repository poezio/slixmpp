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

        #~ ns = "https://example.net/our_extension"
        self.xmpp.register_handler(
                    Callback('ExampleGet Event:example_tag',    ##~ Name of this Callback
                    StanzaPath("iq@type=get/{{{ns}}}example_tag".format(ns="https://example.net/our_extension")),      ##~ Handle only Iq with type get and example_tag
                    self.__handle_get_iq))                      ##~ Method which catch proper Iq, should raise proper event for client.

        self.xmpp.register_handler(
                    Callback('ExampleResult Event:example_tag', ##~ Name of this Callback
                    StanzaPath("iq@type=result/{{{ns}}}example_tag".format(ns="https://example.net/our_extension")),   ##~ Handle only Iq with type get and example_tag
                    self.__handle_result_iq))                   ##~ Method which catch proper Iq, should raise proper event for client.

        self.xmpp.register_handler(
                    Callback('ExampleError Event:example_tag',  ##~ Name of this Callback
                    StanzaPath("iq@type=error/{{{ns}}}example_tag".format(ns="https://example.net/our_extension")),    ##~ Handle only Iq with type get and example_tag
                    self.__handle_error_iq))                    ##~ Method which catch proper Iq, should raise proper event for client.

        self.xmpp.register_handler(
                    Callback('ExampleMessage Event:example_tag',##~ Name of this Callback
                    StanzaPath('message/example_tag'),          ##~ Handle only Iq with type get and example_tag
                    self.__handle_message))                     ##~ Method which catch proper Iq, should raise proper event for client.

        register_stanza_plugin(Iq, ExampleTag)                  ##~ Register tags extension for Iq object, otherwise iq['example_tag'] will be string field instead container where we can manage our fields and create sub elements.
        register_stanza_plugin(Message, ExampleTag)                  ##~ Register tags extension for Iq object, otherwise iq['example_tag'] will be string field instead container where we can manage our fields and create sub elements.

    # All iq types are: get, set, error, result
    def __handle_get_iq(self, iq):
        # Do something with iq
        self.xmpp.event('example_tag_get_iq', iq)           ##~ Call event which can be handled by clients to send or something other what you want.
        
    def __handle_result_iq(self, iq):
        # Do something with iq
        self.xmpp.event('example_tag_result_iq', iq)        ##~ Call event which can be handled by clients to send or something other what you want.

    def __handle_error_iq(self, iq):
        # Do something with iq
        self.xmpp.event('example_tag_error_iq', iq)         ##~ Call event which can be handled by clients to send or something other what you want.

    def __handle_message(self, msg):
        # Do something with message
        self.xmpp.event('example_tag_message', msg)          ##~ Call event which can be handled by clients to send or something other what you want.

class ExampleTag(ElementBase):
    name = "example_tag"                                        ##~ The name of the root XML element of that extension.
    namespace = "https://example.net/our_extension"             ##~ The namespace our stanza object lives in, like <example_tag xmlns={namespace} (...)</example_tag>. You should change it for your own namespace

    plugin_attrib = "example_tag"                               ##~ The name to access this type of stanza. In particular, given  a  registration  stanza,  the Registration object can be found using: stanza_object['example_tag'] now `'example_tag'` is name of ours ElementBase extension. And this should be that same as name.
    
    interfaces = {"boolean", "some_string"}                     ##~ A list of dictionary-like keys that can be used with the stanza object. For example `stanza_object['example_tag']` gives us {"another": "some", "data": "some"}, whenever `'example_tag'` is name of ours ElementBase extension.

    def setup_from_string(self, string):
        et_extension_tag_xml = ET.fromstring(string)
        self.setup_from_lxml(et_extension_tag_xml)

    def setup_from_file(self, path):
        et_extension_tag_xml = ET.parse(path).getroot()
        self.setup_from_lxml(et_extension_tag_xml)

    def setup_from_lxml(self, lxml):
        self.xml.attrib.update(lxml.attrib)
        self.xml.text = lxml.text
        for inner_tag in lxml:
            self.xml.append(inner_tag)

    def get_boolean(self):
        return self.xml.attrib["boolean"]

    def get_some_string(self):
        return self.xml.attrib["some_string"]
        
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

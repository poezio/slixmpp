Jak stworzyć własny plugin rozszerzający obiekty Message i Iq w Slixmpp
=======================================================================

Wstęp i wymagania
-----------------

* `'python3'`

Kod użyty w tutorialu jest kompatybilny z pythonem w wersji 3.6+.

Dla wstecznej kompatybilności z wcześniejszymi wersjami, wystarczy zastąpić f-strings starszym formatowaniem napisów `'"{}".format("content")'` lub `'%s, "content"'`.

Instalacja dla Ubuntu linux:

.. code-block:: bash

    sudo apt-get install python3.6

* `'slixmpp'` 
* `'argparse'`
* `'logging'`
* `'subprocess'`
* `'threading'`

Sprawdź czy powyżej wymienione bibliteki są dostępne w twoim środowisku wykonawczym. (Wszystkie z wyjątkiem slixmpp są w standardowej bibliotece pythona, jednak czasem kompilując źródła samodzielnie, część ze standardowych bibliotek może nie być zainstalowana z pythonem.


.. code-block:: python

    python3 --version
    python3 -c "import slixmpp; print(slixmpp.__version__)"
    python3 -c "import argparse; print(argparse.__version__)"
    python3 -c "import logging; print(logging.__version__)"
    python3 -m subprocess
    python3 -m threading

Mój wynik komend:

.. code-block:: bash

    ~ $ python3 --version
    Python 3.8.0
    ~ $ python3 -c "import slixmpp; print(slixmpp.__version__)"
    1.4.2
    ~ $ python3 -c "import argparse; print(argparse.__version__)"
    1.1
    ~ $ python3 -c "import logging; print(logging.__version__)"
    0.5.1.2    
    ~ $ python3 -m subprocess #To nie powinno nic zwrócić
    ~ $ python3 -m threading #To nie powinno nic zwrócić

Jeśli któraś z bibliotek zwróci `'ImportError'` lub `'no module named ...'`, dla potrzeb tutorialu powinny zostać zainstalowane jak na przykładzie poniżej:

Instalacja na Ubuntu linux:

.. code-block:: bash

    pip3 install slixmpp
    #or
    easy_install slixmpp

Jeśli jakaś biblioteka zwróci NameError, zainstaluj pakiet ponownie.

* `Konta dla Jabber`

Do testowania, na potrzeby tutorialu będą niezbędne dwa prywatne konta jabbera.
Aby stworzyć nowe konto, w sieci istnieje dużo dostępnych darmowych serwerów: 

https://www.google.com/search?q=jabber+server+list

Skrypt uruchamiający klientów
-----------------------------

Poza lokalizacją projektu, powinniśmy stworzyć skrypt uruchamiający klientów testowo aby szybko móc sprawdzić czy rezultat jest prawidłowy. Ważne aby skrypt był poza projektem aby na przykład uniknąć przypadkowego wysłania na platformę gita swoich danych logowania.

Na moim urządzeniu stworzyłem w ścieżce `'/usr/bin'` plik o nazwie `'test_slixmpp'` i dodałem uprawnienia do wykonywania go:

.. code-block:: bash

    /usr/bin $ chmod 711 test_slixmpp

Ten plik w tej formie powinniśmy móc edytować i czytać wyłącznie z uprawnieniami superuser. Plik zawiera prostą strukturę która pozwoli nam zapisać swoje dane logowania.

.. code-block:: python

    #!/usr/bin/python3
    #File: /usr/bin/test_slixmpp & permissions rwx--x--x (711)

    import subprocess
    import threading
    import time
    
    def start_shell(shell_string):
        subprocess.run(shell_string, shell=True, universal_newlines=True)
    
    if __name__ == "__main__":
        #~ prefix = "x-terminal-emulator -e" # Oddzielny terminal dla każdego klienta, można zastąpić własnym emulatorem terminala
        #~ prefix = "xterm -e" # Oddzielny terminal dla każdego klienta, można zastąpić własnym emulatorem terminala
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

Funkcja `'subprocess.run()'` jest kompatybilna z Pythonem 3.5+. Więc dla jeszcze wcześniejszej kompatybilności można dopasować argumenty i podmienić na metodę `'subprocess.call()'`.

Skrypt uruchomieniowy powinien być dopasowany do naszych potrzeb, można pobierać ścieżki do projektu z linii komend, wybierać z jaką flagą mają zostać uruchomione programy i wiele innych rzeczy które będą nam potrzebne. W tym punkcie musimy dostosować skrypt do swoich potrzeb co zaoszczędzi nam masę czasu w trakcie pracy.

Dla testowania większych aplikacji podczas tworzenia pluginu, w mojej opinii szczególnie użyteczne są osobne linie poleceń dla każdego klienta aby zachować czytelność który i co zwraca, bądź który powoduje błąd.

Stworzenie klienta i pluginu
----------------------------

W stosownej dla nas lokalizacji powinniśmy stworzyć dwa klienty slixmpp, aby sprawdzić czy nasz skrypt uruchomieniowy działa poprawnie. I stworzyłem klientów: `'sender'` i `'responder'`. Poniżej minimalna implementacja dla efektywnego testowania gdzie będziemy testować nasz plugin w trakcie jego projektowania:

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
		# Dwie niewymagane metody, pozwalające innym użytkownikom zobaczyć że jesteśmy online i wyświetlić tą informację
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
        #xmpp.register_plugin('OurPlugin', module=example_plugin) # OurPlugin jest nazwą klasy naszego example_plugin
            
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
			# Dwie niewymagane metody, pozwalające innym użytkownikom zobaczyć że jesteśmy online i wyświetlić tą informację
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
        xmpp.register_plugin('OurPlugin', module=example_plugin) # OurPlugin jest nazwą klasy naszego example_plugin
    
        xmpp.connect()
        try:
            xmpp.process()
        except KeyboardInterrupt:
            try:
                xmpp.disconnect()
            except:
                pass

Następny plik który powinniśmy stworzyć to `'example_plugin'` ze ścieżką dostępną dla importu z poziomu klientów. Domyślnie umieszczam w tej samej lokalizacji co klientów.

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
            self.description = "OurPluginExtension"                 ##~ Napis czytelny dla człowieka i dla znalezienia pluginu przez inny plugin
            self.xep = "ope"                                        ##~ Napis czytelny dla człowieka i dla znalezienia pluginu przez inny plugin dodając to do `slixmpp/plugins/__init__.py` do pola `__all__` z prefixem xep 'xep_OPE'. W innym wypadku jest to tylko notka czytelna dla ludzi
    
            namespace = ExampleTag.namespace


    class ExampleTag(ElementBase):
        name = "example_tag"                                        ##~ Nazwa naszego głównego taga dla XML w tym rozszerzeniu.
        namespace = "https://example.net/our_extension"             ##~ Namespace dla naszego obiektu jest definiowana w tym miejscu, powinna się odnosić do naszego portalu, w wiadomości wygląda tak: <example_tag xmlns={namespace} (...)</example_tag>
    
        plugin_attrib = "example_tag"                               ##~ Nazwa pod którą będziemy odwoływać się do danych zawartych w tym pluginie. Bardziej szczegółowo, tutaj rejestrujemy nazwę naszego obiektu by móc się do niego odwoływać z zewnątrz. Będziemy mogli się do niego odwoływać na przykład jak do słownika: stanza_object['example_tag']. `'example_tag'` staje się naszą nazwą pluginu i powinno być takie samo jak name.
        
        interfaces = {"boolean", "some_string"}                     ##~ Zbiór kluczy dla słownika atrybutów naszego elementu które mogą być użyte w naszym elemencie. Na przykład `stanza_object['example_tag']` poda nam informacje o: {"boolean": "some", "some_string": "some"}, tam gdzie `'example_tag'` jest nazwą naszego elementu.

Jeżeli powyższy plugin nie jest w naszej lokalizacji a klienci powinni pozostać poza repozytorium, możemy w miejscu klientów dodać dowiązanie symboliczne do lokalizacji pluginu aby był dostępny z poziomu klientów:
.. code-block:: bash

    ln -s $Path_to_example_plugin_py $Path_to_clients_destinations

Jeszcze innym wyjściem jest import relatywny z użyciem kropek aby dostać się do właściwej ścieżki.

Pierwsze uruchomienie i przechwytywanie eventów
-----------------------------------------------

Aby sprawdzić czy wszystko działa prawidłowo, możemy użyć metody `'start'`, ponieważ przypiszemy do niego event `'session_start'`, ten sygnał zostanie wywołany zaraz po tym gdy klient będzie gotów do działania, a własna metoda pozwoli nam zdefiniować odpowiednią czynność dla tego sygnału.

W metodzie `'__init__'` tworzymy przekierowanie dla wywołania eventu `'session_start'` i kiedy zostanie wywołany, nasza metoda `'def start(self, event):'` będzie wykonana. Na pierwszy krok, dodajmy linię  `'logging.info("I'm running")'` dla obu klientów (sender i responder) i użyjmy naszej komendy `'test_slixmpp'`.

Teraz metoda `'def start(self, event):'` powinna wyglądać tak:

.. code-block:: python

    def start(self, event):
        self.send_presence()
        self.get_roster()

        #>>>>>>>>>>>>
        logging.info("I'm running")
        #<<<<<<<<<<<<

Jeśli oba klienty uruchomiły się poprawnie, możemy zakomentować te linię i wysłać naszą pierwszą wiadomość z pomocą następnego rozdziału.

Budowanie obiektu Message 
-------------------------

W tym rozdziale, wysyłający powinien dostać informację do kogo należy wysłać wiadomość z linii komend za pomocą naszego skryptu testowego.
W poniższym przykładzie, dostęp do tej informacji mamy za pośrednictwem atrybutu `'selt.to'`:

.. code-block:: python

    #File: $WORKDIR/example/sender.py
    
    class Sender(slixmpp.ClientXMPP):
        def __init__(self, jid, password, to, path):
            slixmpp.ClientXMPP.__init__(self, jid, password)
    
            self.to = to
            self.path = path
            
            self.add_event_handler("session_start", self.start)

        def start(self, event):
            self.send_presence()
            self.get_roster()
            #>>>>>>>>>>>>
            self.send_example_message(self.to, "example_message")
    
        def send_example_message(self, to, body):
            #~ make_message(mfrom=None, mto=None, mtype=None, mquery=None)
            # Domyślnie mtype == "chat" if None; 
            msg = self.make_message(mto=to, mbody=body)
            msg.send()
            #<<<<<<<<<<<<

W przykładzie, używamy wbudowanej metody `'make_message'` która tworzy dla nas wiadomość o treści `'example_message'` i wysyła ją pod koniec działania metody start. Czyli wyśle ją raz, zaraz po uruchomieniu. 

Aby otrzymać tą wiadomość, responder powinien wykorzystać odpowiedni event którego wywołanie jest wbudowane. Ta metoda decyduje co zrobić gdy dotrze do nas wiadomość której nie został przypisany inny event (na przykład naszej rozszerzonej w dalszej części) oraz posiada treść.
Przykład kodu:

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
            self.send_presence()
            self.get_roster()
    
        #>>>>>>>>>>>>
        def message(self, msg):
            #Pokazuje cały XML naszej wiadomości
            logging.info(msg)
            #Pokazuje wyłącznie pole 'body' wiadomości, podobnie jak dostęp do słownika
            logging.info(msg['body'])
        #<<<<<<<<<<<<

Rozszerzenie Message o nasz tag
+++++++++++++++++++++++++++++++

Aby rozszerzyć obiekt Message wybranym tagiem ze specjalnymi polami, plugin powinien zostać zarejestrowany jako rozszerzenie dla obiektu Message.

.. code-block:: python

    #File: $WORKDIR/example/example plugin.py
    
    class OurPlugin(BasePlugin):
        def plugin_init(self):
            self.description = "OurPluginExtension"
            self.xep = "ope"
    
            namespace = ExampleTag.namespace
            #>>>>>>>>>>>>
            register_stanza_plugin(Message, ExampleTag)             ##~ Rejetrujemy rozszerzony tag dla obiektu Message, w innym wypadku  message['example_tag'] będzie polem napisowym, zamiast rozszerzeniem które będzie mogło zawierać swoje atrybuty i pod-elementy.
            #<<<<<<<<<<<<

    class ExampleTag(ElementBase):
        name = "example_tag"
        namespace = "https://example.net/our_extension"
    
        plugin_attrib = "example_tag"
        
        interfaces = {"boolean", "some_string"}

        #>>>>>>>>>>>>
        def set_boolean(self, boolean):
            self.xml.attrib['boolean'] = str(boolean)
    
        def set_some_string(self, some_string):
            self.xml.attrib['some_string'] = some_string
        #<<<<<<<<<<<<

Teraz dzięki rejestracji tagu, możemy rozszerzyć naszą wiadomość.

.. code-block:: python

    #File: $WORKDIR/example/sender.py
    
    class Sender(slixmpp.ClientXMPP):
        def __init__(self, jid, password, to, path):
            slixmpp.ClientXMPP.__init__(self, jid, password)
    
            self.to = to
            self.path = path
            
            self.add_event_handler("session_start", self.start)

        def start(self, event):
            self.send_presence()
            self.get_roster()
            self.send_example_message(self.to, "example_message")
    
        def send_example_message(self, to, body):
            msg = self.make_message(mto=to, mbody=body)
            #>>>>>>>>>>>>
            msg['example_tag'].set_some_string("Work!")
            logging.info(msg)
            #<<<<<<<<<<<<
            msg.send()

Teraz po uruchomieniu, logging powinien pokazać nam Message wraz z tagiem `'example_tag'` zawartym w środku <message><example_tag/></message>, wraz z naszym napisem `'Work'` oraz nadanym namespace.

Nadanie oddzielnego sygnału dla rozszerzonej wiadomości
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

Jeśli nie sprecyzujemy swojego eventu, zarówno rozszerzona jak i podstawowa wiadomość będą przechwytywane przez sygnał `'message'`. Aby nadać im oddzielny event, musimy zarejestrować odpowiedni handler dla naszego namespace oraz tagu aby stworzyć unikalną kombinację, która pozwoli nam przechwycić wyłącznie pożądane wiadomości (lub Iq object).

.. code-block:: python

    #File: $WORKDIR/example/example plugin.py
    
    class OurPlugin(BasePlugin):
        def plugin_init(self):
            self.description = "OurPluginExtension"
            self.xep = "ope"
    
            namespace = ExampleTag.namespace
            #>>>>>>>>>>>>
            self.xmpp.register_handler(
                        Callback('ExampleMessage Event:example_tag',	##~ Nazwa tego Callback
                        StanzaPath(f'message/{{{namespace}}}example_tag'),          ##~ Przechwytujemy wyłącznie Message z tagiem example_tag i namespace takim jaki zdefiniowaliśmy w ExampleTag
                        self.__handle_message))                     ##~ Metoda do której przypisujemy przechwycony odpowiedni obiekt, powinna wywołać odpowiedni event dla klienta.
            #<<<<<<<<<<<<
            register_stanza_plugin(Message, ExampleTag)

            #>>>>>>>>>>>>
        def __handle_message(self, msg):
            # Tu możemy coś zrobić z przechwyconą wiadomością zanim trafi do klienta.
            self.xmpp.event('example_tag_message', msg)          ##~ Wywołuje event, który może zostać przechwycony i obsłużony przez klienta, jako argument przekazujemy obiekt który chcemy dopiąć do eventu.
            #<<<<<<<<<<<<

Obiekt StanzaPath powinien być poprawnie zainicjalizowany, oto schemat aby zrobić to poprawnie:
`'NAZWA_OBIEKTU[@type=TYP_OBIEKTU][/{NAMESPACE}[TAG]]'`

* Dla NAZWA_OBIEKTU możemy użyć `'message'` lub `'iq'`.
* Dla TYP_OBIEKTU jeśli obiektem jest message, możemy sprecyzować typ dla message, np. `'chat'`
* Dla TYP_OBIEKTU jeśli obiektem jest iq, możemy sprecyzować typ spośród: `'get, set, error or result'`
* Dla NAMESPACE zawsze to powinien być namespace z naszego rozszerzenia tagu.
* Dla TAG powinno zawierać nasz tag, `'example_tag'` w tym przypadku.

Teraz, przechwytujemy wszystkie message które zawierają nasz namespace wewnątrz `'example_tag'`, możemy jak w programowaniu agentowym sprawdzić co zawiera, czy na pewno posiada wymagane pola itd. przed wysłaniem do klienta za pośrednictwem eventu `'example_tag_message'`.

.. code-block:: python

    #File: $WORKDIR/example/sender.py
    
    class Sender(slixmpp.ClientXMPP):
        def __init__(self, jid, password, to, path):
            slixmpp.ClientXMPP.__init__(self, jid, password)
    
            self.to = to
            self.path = path
            
            self.add_event_handler("session_start", self.start)

        def start(self, event):
            self.send_presence()
            self.get_roster()
            #>>>>>>>>>>>>
            self.send_example_message(self.to, "example_message", "example_string")
    
        def send_example_message(self, to, body, some_string=""):
            msg = self.make_message(mto=to, mbody=body)
            if some_string:
                msg['example_tag'].set_some_string(some_string)
            msg.send()
            #<<<<<<<<<<<<
            
Powinniśmy zapamiętać linię z naszego pluginu: `'self.xmpp.event('example_tag_message', msg)'`

W tej linii zdefiniowaliśmy nazwę eventu aby go przechwycić wewnątrz pliku responder.py. Jest nim `'example_tag_message'`.

.. code-block:: python

    #File: $WORKDIR/example/responder.py
    
    class Responder(slixmpp.ClientXMPP):
        def __init__(self, jid, password):
            slixmpp.ClientXMPP.__init__(self, jid, password)
            
            self.add_event_handler("session_start", self.start)
            #>>>>>>>>>>>>
            self.add_event_handler("example_tag_message", self.example_tag_message) # Rejestracja handlera
            #<<<<<<<<<<<<

        def start(self, event):
            self.send_presence()
            self.get_roster()
    
        #>>>>>>>>>>>>
        def example_tag_message(self, msg):
            logging.info(msg) # Message jest obiektem który nie wymaga wiadomości zwrotnej. Może zostać zwrócona odpowiedź, ale nie jest to sposób komunikacji maszyn, więc żaden timeout error nie zostanie wywołany gdy nie zostanie zwrócona. (W przypadku Iq już tak)
        #<<<<<<<<<<<<

Teraz możemy odesłać wiadomość, ale nic się nie stanie jeśli tego nie zrobimy. Natomiast kolejny obiekt do komunikacji (Iq) wymaga odpowiedzi jeśli został wysłany, więc obydwaj klienci powinni być online. W innym wypadku, klient otrzyma automatyczny error z powodu timeout jeśli cel Iq nie odpowie za pomocą Iq o tym samym Id.

Użyteczne metody i inne
-----------------------

Modyfikacja przykładowego obiektu `Message` na `Iq`.
++++++++++++++++++++++++++++++++++++++++++++++++++++

Aby przerobić przykładowy obiekt Message na obiekt Iq, musimy zarejestrować nowy handler dla Iq podobnie jak dla wiadomości w rozdziale `,,Rozszerzenie Message o nasz tag''`. Tym razem, przykład będzie zawierał kilka typów Iq z oddzielnymi typami, jest to użyteczne aby kod był czytelny, oraz odpowiednia weryfikacja lub działanie zostało podjęte pomijając sprawdzanie typu. Wszystkie Iq powinny odesłać odpowiedź z tym samym Id do wysyłającego wraz z odpowiedzią, inaczej wysyłający dostanie Iq zwrotne typu error, zawierające informacje o przekroczonym czasie oczekiwania (timeout). Dlatego jest to bardziej wymiana informacji pomiędzy maszynami niż ludźmi którzy mogą zareagować zbyt wolno i stracić szansę na odpowiedź.

.. code-block:: python

    #File: $WORKDIR/example/example plugin.py
    
    class OurPlugin(BasePlugin):
        def plugin_init(self):
            self.description = "OurPluginExtension"
            self.xep = "ope"
    
            namespace = ExampleTag.namespace
            #>>>>>>>>>>>>
            self.xmpp.register_handler(
                        Callback('ExampleGet Event:example_tag',
                        StanzaPath(f"iq@type=get/{{{namespace}}}example_tag"),
                        self.__handle_get_iq))
    
            self.xmpp.register_handler(
                        Callback('ExampleResult Event:example_tag',
                        StanzaPath(f"iq@type=result/{{{namespace}}}example_tag"),
                        self.__handle_result_iq))
    
            self.xmpp.register_handler(
                        Callback('ExampleError Event:example_tag',
                        StanzaPath(f"iq@type=error/{{{namespace}}}example_tag"),
                        self.__handle_error_iq))
            #<<<<<<<<<<<<
            self.xmpp.register_handler(
                        Callback('ExampleMessage Event:example_tag',
                        StanzaPath(f'message/{{{namespace}}}example_tag'),
                        self.__handle_message))
    
            #>>>>>>>>>>>>
            register_stanza_plugin(Iq, ExampleTag)
            #<<<<<<<<<<<<
            register_stanza_plugin(Message, ExampleTag)
            
            #>>>>>>>>>>>>
        # Wszystkie możliwe typy Iq to: get, set, error, result
        def __handle_get_iq(self, iq):
            self.xmpp.event('example_tag_get_iq', iq)
            
        def __handle_result_iq(self, iq):
            self.xmpp.event('example_tag_result_iq', iq)
    
        def __handle_error_iq(self, iq):
            self.xmpp.event('example_tag_error_iq', iq)
            #<<<<<<<<<<<<
    
        def __handle_message(self, msg):
            self.xmpp.event('example_tag_message', msg)

Eventy wywołane przez powyższe handlery, mogą zostać przechwycone jak w przypadku eventu `'example_tag_message'`.
    
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
        def example_tag_get_iq(self, iq): # Iq stanza powinno zawsze zostać zwrócone, w innym wypadku wysyłający dostanie informacje z błędem że odbiorca jest offline.
            logging.info(str(iq))
            reply = iq.reply(clear=False)
            reply.send()
            #<<<<<<<<<<<<

Domyślnie parametr `'clear'` dla `'Iq.reply'` jest ustawiony na True, wtedy to co jest zawarte wewnątrz Iq (z kilkoma wyjątkami) powinno zostać zdefiniowane ponownie. Jedyne informacje które zostaną w Iq po metodzie reply, nawet gdy parametr clean jest ustawiony na True, to ID tego Iq oraz JID wysyłającego.

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

Dostęp do elementów
+++++++++++++++++++

Aby dostać się do pól wewnątrz Message lub Iq, jest kilka możliwości. Po pierwsze, z poziomu klienta, można dostać zawartość jak ze słownika:

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

Z rozszerzenia ExampleTag, dostęp do elementów jest podobny, tyle że nie musimy już precyzować tagu którego dotyczy. Dodatkową zaletą jest fakt niejednolitego dostępu, na przykład do parametru `'text'` między rozpoczęciem a zakończeniem tagu, co obrazuje poniższy przykład, ujednolicając metody do obiektowych getterów i setterów.

.. code-block:: python

    #File: $WORKDIR/example/example plugin.py

    class ExampleTag(ElementBase):
        name = "example_tag"
        namespace = "https://example.net/our_extension"
    
        plugin_attrib = "example_tag"
        
        interfaces = {"boolean", "some_string"}
        
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

Atrybut `'self.xml'` jest dziedziczony z klasy `'ElementBase'` i jest to dosłownie `'Element'` z pakietu `'ElementTree'`. 

Kiedy odpowiednie gettery i settery są stworzone, umożliwia sprawdzenie czy na pewno podany argument spełnia normy pluginu lub konwersję na pożądany typ. Dodatkowo kod staje się bardziej przejrzysty w standardach programowania obiektowego, jak na poniższym przykładzie:
	
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
            iq = self.make_iq(ito=to, itype="get")
            iq['example_tag']['boolean'] = "True"  #Przypisanie wprost
            #>>>>>>>>>>>>
            iq['example_tag'].set_some_string("Another_string") #Przypisanie poprzez setter
            iq['example_tag'].set_text("Info_inside_tag")
            #<<<<<<<<<<<<
            iq.send()

Wczytanie ExampleTag ElementBase z pliku XML, łańcucha znaków i innych obiektów
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Żeby wczytać wcześniej zdefiniowany napis, z pliku albo lxml (ElementTree) jest dużo możliwości, tutaj pokażę przykład wykorzystując parsowanie typu napisowego do lxml (ElementTree) i przekazanie atrybutów.

.. code-block:: python

    #File: $WORKDIR/example/example plugin.py

    #...
    from slixmpp.xmlstream import ElementBase, ET, register_stanza_plugin
    #...

    class ExampleTag(ElementBase):
        name = "example_tag"
        namespace = "https://example.net/our_extension"
    
        plugin_attrib = "example_tag"
        
        interfaces = {"boolean", "some_string"}
        
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

Do przetestowania tej funkcjonalności, będziemy potrzebować pliku zawierającego xml z naszym tagiem, przykładowy napis z xml oraz przykładowy lxml (ET):
	
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
            self.send_presence()
            self.get_roster()
    
            #>>>>>>>>>>>>
            self.disconnect_counter = 3 # Ta zmienna jest tylko do rozłączenia klienta po otrzymaniu odpowiedniej ilości odpowiedzi z Iq. 
            
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
                self.disconnect() # Przykład rozłączania się aplikacji po uzyskaniu odpowiedniej ilości odpowiedzi.
    
        def send_example_iq_tag_from_file(self, to, path):
            iq = self.make_iq(ito=to, itype="get", id=2)
            iq['example_tag'].setup_from_file(path)
    
            iq.send()
            
        def send_example_iq_tag_from_element_tree(self, to, et):
            iq = self.make_iq(ito=to, itype="get", id=3)
            iq['example_tag'].setup_from_lxml(et)
    
            iq.send()
    
        def send_example_iq_tag_from_string(self, to, string):
            iq = self.make_iq(ito=to, itype="get", id=5)
            iq['example_tag'].setup_from_string(string)
    
            iq.send()
            #<<<<<<<<<<<<

Jeśli Responder zwróci nasze wysłane Iq, a Sender wyłączy się po trzech odpowiedziach, wtedy wszystko działa jak powinno.

Łatwość użycia pluginu dla programistów 
+++++++++++++++++++++++++++++++++++++++

Każdy plugin powinien posiadać pewne obiektowe metody, wczytanie danych jak w przypadku metod `setup` z poprzedniego rozdziału, gettery, settery, czy wywoływanie odpowiednich eventów.
Potencjalne błędy powinny być przechwytywane z poziomu pluginu i zwracane z odpowiednim opisem błędu w postaci odpowiedzi Iq o tym samym id do wysyłającego, aby uniknąć sytuacji kiedy plugin nie robi tego co powinien, a wiadomość zwrotna nigdy nie nadchodzi, zamiast tego wysyłający dostaje error z komunikatem timeout.

Poniżej przykład kodu podyktowanego tymi zasadami:

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
            self.description = "OurPluginExtension"
            self.xep = "ope"
    
            namespace = ExampleTag.namespace
            self.xmpp.register_handler(
                        Callback('ExampleGet Event:example_tag',
                        StanzaPath(f"iq@type=get/{{{namespace}}}example_tag"),
                        self.__handle_get_iq))
    
            self.xmpp.register_handler(
                        Callback('ExampleResult Event:example_tag',
                        StanzaPath(f"iq@type=result/{{{namespace}}}example_tag"),
                        self.__handle_result_iq))
    
            self.xmpp.register_handler(
                        Callback('ExampleError Event:example_tag',
                        StanzaPath(f"iq@type=error/{{{namespace}}}example_tag"),
                        self.__handle_error_iq))
    
            self.xmpp.register_handler(
                        Callback('ExampleMessage Event:example_tag',
                        StanzaPath(f'message/{{{namespace}}}example_tag'),
                        self.__handle_message))
    
            register_stanza_plugin(Iq, ExampleTag)
            register_stanza_plugin(Message, ExampleTag)
    
        def __handle_get_iq(self, iq):
            if iq.get_some_string is None:
                error = iq.reply(clear=False)
                error["type"] = "error"
                error["error"]["condition"] = "missing-data"
                error["error"]["text"] = "Without some_string value returns error."
                error.send()
            self.xmpp.event('example_tag_get_iq', iq)
            
        def __handle_result_iq(self, iq):
            self.xmpp.event('example_tag_result_iq', iq)
    
        def __handle_error_iq(self, iq):
            # Do something with received iq
            self.xmpp.event('example_tag_error_iq', iq)
    
        def __handle_message(self, msg):
            self.xmpp.event('example_tag_message', msg)
    
    class ExampleTag(ElementBase):
        name = "example_tag"
        namespace = "https://example.net/our_extension"
    
        plugin_attrib = "example_tag"
        
        interfaces = {"boolean", "some_string"}
    
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
            self.send_presence()
            self.get_roster()
            
        def example_tag_get_iq(self, iq):
            logging.info(iq)
            reply = iq.reply()
            reply["example_tag"].fill_interfaces(True, "Reply_string")
            reply.send()
    
        def example_tag_message(self, msg):
            logging.info(msg)
    
    
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
        xmpp.register_plugin('OurPlugin', module=example_plugin)
    
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
            self.send_presence()
            self.get_roster()
    
            self.disconnect_counter = 5
            
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
                self.disconnect()
                
        def example_tag_error_iq(self, iq):
            self.disconnect_counter -= 1
            logging.info(str(iq))
            if not self.disconnect_counter:
                self.disconnect()
                
        def send_example_iq(self, to):
            iq = self.make_iq(ito=to, itype="get")
            iq['example_tag'].set_boolean(True)
            iq['example_tag'].set_some_string("Another_string")
            iq['example_tag'].set_text("Info_inside_tag")
            iq.send()
    
        def send_example_message(self, to):
            msg = self.make_message(mto=to)
            msg['example_tag'].set_boolean(True)
            msg['example_tag'].set_some_string("Message string")
            msg['example_tag'].set_text("Info_inside_tag_message")
            msg.send()
    
        def send_example_iq_tag_from_file(self, to, path):
            iq = self.make_iq(ito=to, itype="get", id=2)
            iq['example_tag'].setup_from_file(path)
    
            iq.send()
    
        def send_example_iq_tag_from_element_tree(self, to, et):
            iq = self.make_iq(ito=to, itype="get", id=3)
            iq['example_tag'].setup_from_lxml(et)
    
            iq.send()
    
        def send_example_iq_to_get_error(self, to):
            iq = self.make_iq(ito=to, itype="get", id=4)
            iq['example_tag'].set_boolean(True)
            iq.send()
    
        def send_example_iq_tag_from_string(self, to, string):
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
        xmpp.register_plugin('OurPlugin', module=example_plugin)
    
        xmpp.connect()
        try:
            xmpp.process()
        except KeyboardInterrupt:
            try:
                xmpp.disconnect()
            except:
                pass
    


Tagi i atrybuty zagnieżdżone wewnątrz głównego elementu
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

Aby stworzyć zagnieżdżony tag, wewnątrz naszego głównego tagu, rozważmy nasz atrybut `'self.xml'` jako Element z ET (ElementTree).

Można powtórzyć poprzednie działania, inicjalizować nowy element jak główny (ExampleTag). Jednak jeśli nie potrzebujemy dodatkowych metod czy walidacji, a jest to wynik dla innego procesu który i tak będzie parsował xml, wtedy możemy zagnieździć zwyczajny Element z ElementTree z pomocą metody `'append'`. Jeśli przetwarzamy typ napisowy, można to zrobić nawet dzięki parsowaniu napisu na Element i kolejne zagnieżdżenia już będą w dodanym Elemencie do głównego. By nie powtarzać metody setup, tu pokażę bardziej ręczne dodanie zagnieżdżonego taga konstruując ET.Element samodzielnie.
    
.. code-block:: python

    #File: $WORKDIR/example/example_plugin.py

    #(...)
    
    class ExampleTag(ElementBase):
        
    #(...)
    
        def add_inside_tag(self, tag, attributes, text=""):
            #Gdy chcemy dodać tagi wewnętrzne do naszego taga, to jest prosty przykład jak to zrobić:
            itemXML = ET.Element("{{{0:s}}}{1:s}".format(self.namespace, tag)) #~ Inicjalizujemy Element z naszym wewnętrznym tagiem, na przykład: <example_tag (...)> <inside_tag namespace="https://example.net/our_extension"/></example_tag>
            itemXML.attrib.update(attributes) #~ Przypisujemy zdefiniowane atrybuty, na przykład: <inside_tag namespace=(...) inner_data="some"/>
            itemXML.text = text #~ Dodajemy text wewnątrz tego tagu: <inside_tag (...)>our_text</inside_tag>
            self.xml.append(itemXML) #~ I tak skonstruowany Element po prostu dodajemy do elementu z naszym tagiem `example_tag`.

Kompletny kod z tutorialu
-------------------------

Do kompletnego kodu pozostawione zostały angielskie komentarze, tworząc własny plugin za pierwszym razem, jestem przekonany że będą przydatne:

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


Źródła i bibliogarfia
---------------------

Slixmpp project description:

* https://pypi.org/project/slixmpp/

Official web documentation:

* https://slixmpp.readthedocs.io/ 


Official pdf documentation:

* https://buildmedia.readthedocs.org/media/pdf/slixmpp/latest/slixmpp.pdf

Note: Dokumentacje w formie Web i PDF mają pewne różnice, pewne szczegóły potrafią być wspomniane tylko w jednej z dwóch.



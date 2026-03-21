import sys
import json
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QListWidget, QListWidgetItem
from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel

# ---------- BEÁLLÍTÁSOK ----------
WEB_URL = "https://nexus-crypto-cloud.github.io/nexus-site/"  # ← Cseréld ki a saját címedre!

class Bridge:
    """ JavaScript-Python kommunikációhoz """
    def __init__(self, window):
        self.window = window

    def userLoggedIn(self, userData):
        """ A weboldal hívja meg, amikor a felhasználó bejelentkezett. """
        data = json.loads(userData)
        print("Bejelentkezés sikeres:", data.get("displayName"))
        self.window.userData = data
        self.window.afterLogin()

class NexusLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nexus Launcher")
        self.setGeometry(100, 100, 900, 700)

        # Központi widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Böngésző widget
        self.browser = QWebEngineView()
        layout.addWidget(self.browser)

        # Letöltési lista (kezdetben rejtve)
        self.downloadList = QListWidget()
        self.downloadList.setVisible(False)
        layout.addWidget(self.downloadList)

        self.userData = None

        # Beállítjuk a kommunikációs csatornát
        self.channel = QWebChannel()
        self.bridge = Bridge(self)
        self.channel.registerObject("bridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)

        # Betöltjük a weboldalt
        self.browser.setUrl(QUrl(WEB_URL))
        self.browser.loadFinished.connect(self.injectScript)

    def injectScript(self, ok):
        if not ok:
            return
        # Beágyazott JavaScript, amely figyeli a bejelentkezési állapotot
        js_code = """
        (function() {
            // Várjuk, amíg a Firebase Auth elérhetővé válik
            function checkAuth() {
                if (window.firebaseAuth) {
                    window.firebaseAuth.onAuthStateChanged(function(user) {
                        if (user) {
                            var userData = {
                                uid: user.uid,
                                displayName: user.displayName,
                                email: user.email,
                                photoURL: user.photoURL
                            };
                            // Python Bridge hívása
                            new QWebChannel(qt.webChannelTransport, function(channel) {
                                var bridge = channel.objects.bridge;
                                bridge.userLoggedIn(JSON.stringify(userData));
                            });
                        }
                    });
                } else {
                    setTimeout(checkAuth, 200);
                }
            }
            checkAuth();
        })();
        """
        self.browser.page().runJavaScript(js_code)

    def afterLogin(self):
        """ Bejelentkezés után elrejtjük a böngészőt, megjelenítjük a letöltési listát. """
        self.browser.setVisible(False)
        self.downloadList.setVisible(True)

        # Letöltési lista feltöltése (a fájlokat itt adhatod meg)
        files = [
            ("TEST_BUTTON_V1.rar", "https://github.com/NEXUS-crypto-cloud/nexus-site/raw/refs/heads/main/TEST_BUTTON_V1.rar"),
            ("Nexus_Launcher_Beta.zip", "https://github.com/NEXUS-crypto-cloud/nexus-site/raw/refs/heads/main/Nexus_Launcher_Beta.zip")
        ]

        for name, url in files:
            item = QListWidgetItem(name)
            item.setData(1, url)   # URL tárolása
            self.downloadList.addItem(item)

        self.downloadList.itemClicked.connect(self.downloadFile)

    def downloadFile(self, item):
        url = item.data(1)
        filename = item.text()
        try:
            print(f"Letöltés: {filename} ...")
            response = requests.get(url, stream=True)
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Letöltve: {filename}")
            item.setText(f"{filename} (letöltve)")
        except Exception as e:
            print(f"❌ Hiba: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NexusLauncher()
    window.show()
    sys.exit(app.exec_())

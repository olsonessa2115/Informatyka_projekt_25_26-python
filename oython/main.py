import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QSlider
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath

# --- 1. Klasa Rura ---
class Rura:
    def __init__(self, punkty, grubosc=14, kolor=Qt.darkGray):
        self.punkty = [QPointF(float(p[0]), float(p[1])) for p in punkty]
        self.grubosc = grubosc
        self.kolor_rury = kolor
        self.kolor_cieczy = QColor(0, 180, 255)
        self.czy_plynie = False

    def ustaw_przeplyw(self, plynie):
        self.czy_plynie = plynie

    def draw(self, painter):
        if len(self.punkty) < 2:
            return

        path = QPainterPath()
        path.moveTo(self.punkty[0])
        for p in self.punkty[1:]:
            path.lineTo(p)

        # Rysowanie obudowy rury
        pen_rura = QPen(self.kolor_rury, self.grubosc, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen_rura)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # Rysowanie cieczy w srodku
        if self.czy_plynie:
            pen_ciecz = QPen(self.kolor_cieczy, self.grubosc - 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen_ciecz)
            painter.drawPath(path)


# --- 2. Klasa Zbiornik (Nowy Kształt) ---
class Zbiornik:
    def __init__(self, x, y, width, height, nazwa=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.nazwa = nazwa

        self.pojemnosc = 100.0
        self.aktualna_ilosc = 0.0
        self.poziom = 0.0
        self.nastawa_poziomu = None 

    def dodaj_ciecz(self, ilosc):
        wolne = self.pojemnosc - self.aktualna_ilosc
        dodano = min(ilosc, wolne)
        self.aktualna_ilosc += dodano
        self.aktualizuj_poziom()
        return dodano

    def usun_ciecz(self, ilosc):
        usunieto = min(ilosc, self.aktualna_ilosc)
        self.aktualna_ilosc -= usunieto
        self.aktualizuj_poziom()
        return usunieto

    def aktualizuj_poziom(self):
        self.poziom = self.aktualna_ilosc / self.pojemnosc

    def czy_pusty(self):
        return self.aktualna_ilosc <= 0.1

    def czy_pelny(self):
        return self.aktualna_ilosc >= self.pojemnosc - 0.1

    # Punkty zaczepienia rur (dostosowane do zaokrągleń)
    def punkt_wyjscia(self):
        return (self.x + self.width / 2, self.y + self.height)

    def punkt_wejscia(self):
        return (self.x + self.width / 2, self.y)

    def draw(self, painter):
        promien = 20.0 # Promień zaokrąglenia rogów
        
        # 1. Tło zbiornika (Pusty w środku)
        rect = QRectF(float(self.x), float(self.y), float(self.width), float(self.height))
        painter.setPen(QPen(Qt.white, 3))
        painter.setBrush(QColor(60, 60, 60)) # Ciemnoszare tło wnętrza
        painter.drawRoundedRect(rect, promien, promien)

        # 2. Rysowanie cieczy (Przycinanie do kształtu)
        if self.poziom > 0:
            h_cieczy = self.height * self.poziom
            y_start = self.y + self.height - h_cieczy
            
            # Rysujemy ciecz jako osobny zaokrąglony prostokąt na dole
            # Sztuczka wizualna: Rysujemy prostokąt cieczy
            rect_ciecz = QRectF(float(self.x + 4), float(y_start), float(self.width - 8), float(h_cieczy - 4))
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 140, 255, 200)) # Niebieski
            
            # Jeśli ciecz jest niska, zaokrąglamy mocniej dół, mniej górę (uproszczenie: zaokrąglamy wszystko)
            painter.drawRoundedRect(rect_ciecz, promien/2, promien/2)

        # 3. Ponowne obrysowanie ramki (żeby przykryć ewentualne niedoskonałości cieczy)
        painter.setPen(QPen(QColor(220, 220, 220), 4)) # Srebrna ramka
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, promien, promien)

        # 4. Linia Nastawy (SP)
        if self.nastawa_poziomu is not None:
            h_linii = self.height * (self.nastawa_poziomu / 100.0)
            y_linii = self.y + self.height - h_linii
            
            pen_nastawa = QPen(QColor("red"), 2, Qt.DashLine)
            painter.setPen(pen_nastawa)
            painter.drawLine(int(self.x), int(y_linii), int(self.x + self.width), int(y_linii))
            
            painter.setPen(Qt.red)
            painter.drawText(int(self.x + self.width + 5), int(y_linii + 5), f"SP")

        # 5. Podpis
        painter.setPen(Qt.white)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(int(self.x), int(self.y - 10), self.nazwa)


# --- 3. Główna Klasa Symulacji ---
class SymulacjaKaskady(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCADA v2.0 - Nowy Layout")
        self.setFixedSize(1000, 750) 
        self.setStyleSheet("background-color: #2b2b2b;")

        # --- KONFIGURACJA ZBIORNIKÓW (NOWE POZYCJE I WYMIARY) ---
        
        # Z1: Szeroki na górze (Główny)
        self.z1 = Zbiornik(300, 30, 400, 80, nazwa="Z1 Główny")
        
        # Z2: Wąski wysoki po lewej (Silos A)
        self.z2 = Zbiornik(150, 200, 100, 200, nazwa="Z2 Silos A")
        
        # Z3: Wąski wysoki po prawej (Silos B)
        self.z3 = Zbiornik(750, 200, 100, 200, nazwa="Z3 Silos B")
        
        # Z4: Szeroki na dole (Zlewowy)
        self.z4 = Zbiornik(300, 480, 400, 80, nazwa="Z4 Mieszalnik")

        # Ustawienia początkowe
        self.z1.aktualna_ilosc = 100.0
        self.z1.aktualizuj_poziom()
        self.z4.nastawa_poziomu = 60 

        self.zbiorniki = [self.z1, self.z2, self.z3, self.z4]

        # --- KONFIGURACJA RUR (RĘCZNE PROWADZENIE) ---
        self.rury = []
        
        # Rura 1: Z1 (dół środek) -> Z2 (góra)
        p1_out = self.z1.punkt_wyjscia()
        p2_in = self.z2.punkt_wejscia()
        # Ścieżka: W dół, w lewo, w dół
        self.rura1 = Rura([
            p1_out,
            (p1_out[0], p1_out[1] + 40),      # W dół trochę
            (p2_in[0], p1_out[1] + 40),       # W lewo do poziomu Z2
            p2_in                             # W dół do Z2
        ])

        # Rura 2: Z2 (dół) -> Z3 (góra) -- DŁUGI PRZEPŁYW POZIOMY
        p2_out = self.z2.punkt_wyjscia()
        p3_in = self.z3.punkt_wejscia()
        # Ścieżka: W dół, w prawo przez cały ekran, do góry (!), do Z3
        # Uwaga: woda nie płynie do góry grawitacyjnie, ale załóżmy, że jest tu pompa :)
        # Dla realizmu zrobimy przepływ grawitacyjny: Z2 musi być wyżej niż Z3? 
        # W tym layoucie są na równi, więc zróbmy rurę łączącą dołem w kształcie U (syfon) lub górą.
        # Zróbmy prosto: Z2 -> rura pozioma -> Z3 (jakby pompa tłoczyła)
        mid_y = p2_out[1] + 20
        self.rura2 = Rura([
            p2_out,
            (p2_out[0], mid_y),
            (p3_in[0], mid_y), # Poziomo pod zbiornikami? Nie, lepiej nad Z4.
            (p3_in[0], p3_in[1] - 20), # Podejście od dołu? Nie, wlewamy górą
             p3_in 
        ])
        # Korekta trasy Rury 2 dla estetyki: Z2 dół -> w prawo -> Z3 góra (trochę dziwne fizycznie, ale ok w SCADA)
        # Zmienimy trasę: Z2 dół -> Z4 dół? Nie, logika mówi Z2->Z3.
        # OK, poprowadźmy rurę: Z2 dół -> pod Z1 -> Z3 góra.
        self.rura2 = Rura([
            p2_out,
            (p2_out[0], p2_out[1] + 10),
            (p2_out[0] + 60, p2_out[1] + 10), # kawałek w prawo
            (p2_out[0] + 60, p3_in[1] - 20),  # w górę do poziomu wlotu Z3
            (p3_in[0], p3_in[1] - 20),        # w prawo do Z3
            p3_in
        ])


        # Rura 3: Z3 (dół) -> Z4 (góra)
        p3_out = self.z3.punkt_wyjscia()
        p4_in = self.z4.punkt_wejscia()
        # Ścieżka: W dół, w lewo, w dół
        self.rura3 = Rura([
            p3_out,
            (p3_out[0], p3_out[1] + 20),
            (p4_in[0], p3_out[1] + 20),
            p4_in
        ])

        self.rury = [self.rura1, self.rura2, self.rura3]

        # --- TIMER ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.logika_przeplywu)
        self.running = False
        self.flow_speed = 0.8

        # --- PANEL STEROWANIA ---
        self.panel_tlo = QLabel(self)
        self.panel_tlo.setGeometry(0, 580, 1000, 170)
        self.panel_tlo.setStyleSheet("background-color: #1e1e1e; border-top: 3px solid #0078d7;")

        # Przycisk START
        self.btn_start = QPushButton("START\nPROCESU", self)
        self.btn_start.setGeometry(20, 600, 120, 120)
        self.btn_start.setStyleSheet("""
            QPushButton { background-color: #222; color: #00ff00; border: 2px solid #00ff00; border-radius: 60px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #113311; }
        """)
        self.btn_start.clicked.connect(self.przelacz_symulacje)

        # Generowanie przycisków
        offset_start = 180  
        step_x = 170        

        for i, z in enumerate(self.zbiorniki):
            x_pos = offset_start + (i * step_x)
            self.stworz_panel_dla_zbiornika(z, x_pos, 600)

        # Suwak Z4
        pos_z4_panel = offset_start + (3 * step_x) + 90
        self.lbl_nastawa = QLabel("SP", self)
        self.lbl_nastawa.setGeometry(pos_z4_panel, 600, 30, 20)
        self.lbl_nastawa.setStyleSheet("color: white; font-weight: bold;")

        self.slider = QSlider(Qt.Vertical, self)
        self.slider.setGeometry(pos_z4_panel + 5, 625, 30, 90)
        self.slider.setRange(0, 100)
        self.slider.setValue(60)
        self.slider.valueChanged.connect(self.zmiana_nastawy)
        
        self.lbl_val = QLabel("60%", self)
        self.lbl_val.setGeometry(pos_z4_panel, 720, 50, 20)
        self.lbl_val.setStyleSheet("color: red; font-weight: bold;")


    def stworz_panel_dla_zbiornika(self, zbiornik, x, y):
        lbl = QLabel(zbiornik.nazwa.split(" ")[0], self) 
        lbl.setGeometry(x, y, 80, 20)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #fff; font-weight: bold; font-size: 14px; background-color: #333; border-radius: 5px;")

        style_fill = "QPushButton { background-color: #333; color: #4CAF50; border: 1px solid #4CAF50; border-radius: 5px; font-weight: bold; }" \
                     "QPushButton:pressed { background-color: #4CAF50; color: white; }"
        
        style_empty = "QPushButton { background-color: #333; color: #F44336; border: 1px solid #F44336; border-radius: 5px; font-weight: bold; }" \
                      "QPushButton:pressed { background-color: #F44336; color: white; }"

        btn_fill = QPushButton("WLEW (+)", self)
        btn_fill.setGeometry(x, y + 30, 80, 35)
        btn_fill.setStyleSheet(style_fill)
        btn_fill.clicked.connect(lambda: self.napelnij_zbiornik(zbiornik))

        btn_empty = QPushButton("SPUST (-)", self)
        btn_empty.setGeometry(x, y + 75, 80, 35)
        btn_empty.setStyleSheet(style_empty)
        btn_empty.clicked.connect(lambda: self.oproznij_zbiornik(zbiornik))


    def zmiana_nastawy(self):
        val = self.slider.value()
        self.z4.nastawa_poziomu = val
        self.lbl_val.setText(f"{val}%")
        self.update()

    def napelnij_zbiornik(self, zbiornik):
        zbiornik.aktualna_ilosc = zbiornik.pojemnosc
        zbiornik.aktualizuj_poziom()
        self.update()

    def oproznij_zbiornik(self, zbiornik):
        zbiornik.aktualna_ilosc = 0.0
        zbiornik.aktualizuj_poziom()
        self.update()

    def przelacz_symulacje(self):
        if self.running:
            self.timer.stop()
            self.btn_start.setStyleSheet("""
            QPushButton { background-color: #222; color: #00ff00; border: 2px solid #00ff00; border-radius: 60px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #113311; }
            """)
            self.btn_start.setText("START\nPROCESU")
        else:
            self.timer.start(20)
            self.btn_start.setStyleSheet("""
            QPushButton { background-color: #222; color: #ff0000; border: 2px solid #ff0000; border-radius: 60px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #331111; }
            """)
            self.btn_start.setText("STOP")
        self.running = not self.running

    def logika_przeplywu(self):
        # 1. Z1 -> Z2
        plynie_1 = False
        if not self.z1.czy_pusty() and not self.z2.czy_pelny():
            ilosc = self.z1.usun_ciecz(self.flow_speed)
            self.z2.dodaj_ciecz(ilosc)
            plynie_1 = True
        self.rura1.ustaw_przeplyw(plynie_1)

        # 2. Z2 -> Z3
        plynie_2 = False
        if self.z2.aktualna_ilosc > 5.0 and not self.z3.czy_pelny():
            ilosc = self.z2.usun_ciecz(self.flow_speed)
            self.z3.dodaj_ciecz(ilosc)
            plynie_2 = True
        self.rura2.ustaw_przeplyw(plynie_2)

        # 3. Z3 -> Z4 (z Nastawą)
        plynie_3 = False
        limit_z4 = self.z4.pojemnosc * (self.z4.nastawa_poziomu / 100.0)
        
        if self.z3.aktualna_ilosc > 5.0 and self.z4.aktualna_ilosc < limit_z4:
            ilosc = self.z3.usun_ciecz(self.flow_speed)
            self.z4.dodaj_ciecz(ilosc)
            plynie_3 = True
            
        self.rura3.ustaw_przeplyw(plynie_3)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        for r in self.rury:
            r.draw(p)

        for z in self.zbiorniki:
            z.draw(p)

if __name__ == '__main__':
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    okno = SymulacjaKaskady()
    okno.show()
    
    try:
        sys.exit(app.exec_())
    except SystemExit:
        pass
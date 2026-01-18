from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QSlider
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter

from rura import Rura
from zbiornik import Zbiornik

class SymulacjaKaskady(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCADA v2.0 - Modułowa")
        self.setFixedSize(1000, 750) 
        self.setStyleSheet("background-color: #2b2b2b;")

        self.z1 = Zbiornik(300, 30, 400, 80, nazwa="Z1 Główny")
        self.z2 = Zbiornik(150, 200, 100, 200, nazwa="Z2 Silos A")
        self.z3 = Zbiornik(750, 200, 100, 200, nazwa="Z3 Silos B")
        self.z4 = Zbiornik(300, 480, 400, 80, nazwa="Z4 Mieszalnik")

        self.z1.aktualna_ilosc = 100.0
        self.z1.aktualizuj_poziom()
        self.z4.nastawa_poziomu = 60 

        self.zbiorniki = [self.z1, self.z2, self.z3, self.z4]

        self.rury = []
        
        p1_out = self.z1.punkt_wyjscia()
        p2_in = self.z2.punkt_wejscia()
        self.rura1 = Rura([
            p1_out,
            (p1_out[0], p1_out[1] + 40),
            (p2_in[0], p1_out[1] + 40),
            p2_in
        ])

        p2_out = self.z2.punkt_wyjscia()
        p3_in = self.z3.punkt_wejscia()
        self.rura2 = Rura([
            p2_out,
            (p2_out[0], p2_out[1] + 10),
            (p2_out[0] + 60, p2_out[1] + 10),
            (p2_out[0] + 60, p3_in[1] - 20),
            (p3_in[0], p3_in[1] - 20),
            p3_in
        ])

        p3_out = self.z3.punkt_wyjscia()
        p4_in = self.z4.punkt_wejscia()
        self.rura3 = Rura([
            p3_out,
            (p3_out[0], p3_out[1] + 20),
            (p4_in[0], p3_out[1] + 20),
            p4_in
        ])

        self.rury = [self.rura1, self.rura2, self.rura3]

        self.timer = QTimer()
        self.timer.timeout.connect(self.logika_przeplywu)
        self.running = False
        self.flow_speed = 0.8

        self.setup_ui()

    def setup_ui(self):
        self.panel_tlo = QLabel(self)
        self.panel_tlo.setGeometry(0, 580, 1000, 170)
        self.panel_tlo.setStyleSheet("background-color: #1e1e1e; border-top: 3px solid #0078d7;")

        self.btn_start = QPushButton("START\nPROCESU", self)
        self.btn_start.setGeometry(20, 600, 120, 120)
        self.btn_start.setStyleSheet("""
            QPushButton { background-color: #222; color: #00ff00; border: 2px solid #00ff00; border-radius: 60px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #113311; }
        """)
        self.btn_start.clicked.connect(self.przelacz_symulacje)

        offset_start = 180  
        step_x = 170        
        for i, z in enumerate(self.zbiorniki):
            x_pos = offset_start + (i * step_x)
            self.stworz_panel_dla_zbiornika(z, x_pos, 600)

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
        plynie_1 = False
        if not self.z1.czy_pusty() and not self.z2.czy_pelny():
            ilosc = self.z1.usun_ciecz(self.flow_speed)
            self.z2.dodaj_ciecz(ilosc)
            plynie_1 = True
        self.rura1.ustaw_przeplyw(plynie_1)

        plynie_2 = False
        if self.z2.aktualna_ilosc > 5.0 and not self.z3.czy_pelny():
            ilosc = self.z2.usun_ciecz(self.flow_speed)
            self.z3.dodaj_ciecz(ilosc)
            plynie_2 = True
        self.rura2.ustaw_przeplyw(plynie_2)

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
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QPen

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

    def punkt_wyjscia(self):
        return (self.x + self.width / 2, self.y + self.height)

    def punkt_wejscia(self):
        return (self.x + self.width / 2, self.y)

    def draw(self, painter):
        promien = 20.0
        
        rect = QRectF(float(self.x), float(self.y), float(self.width), float(self.height))
        painter.setPen(QPen(Qt.white, 3))
        painter.setBrush(QColor(60, 60, 60))
        painter.drawRoundedRect(rect, promien, promien)

        if self.poziom > 0:
            h_cieczy = self.height * self.poziom
            y_start = self.y + self.height - h_cieczy
            
            rect_ciecz = QRectF(float(self.x + 4), float(y_start), float(self.width - 8), float(h_cieczy - 4))
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 140, 255, 200))
            painter.drawRoundedRect(rect_ciecz, promien/2, promien/2)

        painter.setPen(QPen(QColor(220, 220, 220), 4))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, promien, promien)

        if self.nastawa_poziomu is not None:
            h_linii = self.height * (self.nastawa_poziomu / 100.0)
            y_linii = self.y + self.height - h_linii
            
            pen_nastawa = QPen(QColor("red"), 2, Qt.DashLine)
            painter.setPen(pen_nastawa)
            painter.drawLine(int(self.x), int(y_linii), int(self.x + self.width), int(y_linii))
            
            painter.setPen(Qt.red)
            painter.drawText(int(self.x + self.width + 5), int(y_linii + 5), f"SP")

        painter.setPen(Qt.white)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(int(self.x), int(self.y - 10), self.nazwa)
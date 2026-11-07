"""Ek setler: satranç, ızgara bulmacaları, regex, karakter işlemleri.

Her modül istem(satir) ve puanla(satir, metin) verir; kaynak kodları ek_setler/<set>/puanla.py ile aynı.
satranc python-chess (pip install chess) gerektirir; yalnız satranç satırı puanlanırken içe aktarılır.
"""
import importlib

EK_SETLER = ("satranc", "izgara_bulmaca", "regex", "karakter_islemleri")


def modul(kaynak):
    return importlib.import_module(f".{kaynak}", __name__)

# -*- coding: utf-8 -*-
"""XML uretimi -- orta (duz obje) / zor (ic ice obje+dizi), LLM YOK. entities.py'deki
AYNI dict'ten XML uretilir. Kendi kendine dogrulama: uretilen XML tekrar parse edilip
orijinal dict ile TAM ESLESIYOR mu diye round-trip kontrolu yapilir (turler -- int/
float/bool/str -- korunarak); uyusmazsa AssertionError firlatir, yanlis kayit hic
yazilmaz."""
import argparse
import random
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

from common import Writer
from entities import ORTA_ENTITIES, ZOR_ENTITIES

ITEM_TAG_MAP = {"urunler": "urun", "ogrenciler": "ogrenci"}

TALIMATLAR = [
    "Aşağıdaki bilgiyi XML dokümanı olarak ifade ediniz.",
    "Verilen bilgileri uygun etiketlerle bir XML dokümanına dönüştürünüz.",
    "Bu metindeki bilgiyi XML formatında yapılandırınız.",
]


def infer_shape(obj):
    if isinstance(obj, dict):
        return {k: infer_shape(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [infer_shape(obj[0])] if obj else []
    return type(obj)


def scalar_to_text(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def cast_value(text: str, typ):
    if typ is bool:
        return text == "true"
    if typ is int:
        return int(text)
    if typ is float:
        return float(text)
    return text


def dict_to_xml(tag: str, value) -> ET.Element:
    el = ET.Element(tag)
    for k, v in value.items():
        if isinstance(v, list):
            wrapper = ET.SubElement(el, k)
            item_tag = ITEM_TAG_MAP.get(k, k)
            for item in v:
                wrapper.append(dict_to_xml(item_tag, item))
        elif isinstance(v, dict):
            el.append(dict_to_xml(k, v))
        else:
            child = ET.SubElement(el, k)
            child.text = scalar_to_text(v)
    return el


def xml_to_obj(elem, shape):
    out = {}
    for k, sub in shape.items():
        if isinstance(sub, dict):
            out[k] = xml_to_obj(elem.find(k), sub)
        elif isinstance(sub, list):
            wrapper = elem.find(k)
            item_shape = sub[0] if sub else None
            out[k] = [xml_to_obj(c, item_shape) for c in (list(wrapper) if wrapper is not None else [])]
        else:
            out[k] = cast_value(elem.find(k).text, sub)
    return out


def pretty(el: ET.Element) -> str:
    raw = ET.tostring(el, encoding="unicode")
    lines = [l for l in minidom.parseString(raw).toprettyxml(indent="  ").split("\n") if l.strip()]
    return "\n".join(lines[1:])  # ilk satir <?xml ...?> bildirimi, atiliyor


def gen_one(rng, entity_fn):
    cumle, obj, _schema, etiket = entity_fn(rng)
    root = dict_to_xml(etiket, obj)
    xml_str = pretty(root)

    # kendi kendine round-trip dogrulama: uretilen XML'i tekrar parse edip
    # orijinal dict ile birebir (tur-duyarli) eslesiyor mu kontrol et.
    reparsed = xml_to_obj(ET.fromstring(xml_str), infer_shape(obj))
    assert reparsed == obj, f"XML round-trip uyusmadi: {reparsed} != {obj}"

    soru = f"{rng.choice(TALIMATLAR)}\n\n\"{cumle}\""
    return soru, xml_str, xml_str


def run(n_per_alt_tip: int, seed: int = 71):
    rng = random.Random(seed)
    w = Writer("xml_uretimi", seed=seed)
    for zorluk, grup in (("orta", ORTA_ENTITIES), ("zor", ZOR_ENTITIES)):
        for alt_tip, fn in grup:
            tries, added = 0, 0
            while added < n_per_alt_tip and tries < n_per_alt_tip * 10:
                tries += 1
                soru, cevap, kanonik = gen_one(rng, fn)
                if w.add(alt_tip, zorluk, soru, cevap, kanonik, dogrulama_yontemi="xml_roundtrip_validation"):
                    added += 1
    w.close()
    print(w.summary())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-per-alt-tip", type=int, default=250)
    ap.add_argument("--seed", type=int, default=71)
    args = ap.parse_args()
    run(args.n_per_alt_tip, args.seed)

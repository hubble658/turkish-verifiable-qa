"""Scoring core: safe matching, regex equivalence (greenery DFA) and counterexamples.

Task semantics (fixed for the whole dataset):
  - full match (`regex.fullmatch`), flag ASCII (\\d \\w \\s are ASCII; Turkish letters must be written explicitly),
  - strings never contain a newline,
  - an outermost ^...$ / \\A...\\Z is allowed and stripped (greenery has no anchors).
Every T1 item is first tried by DFA equivalence (a candidate that just lists the hidden positives fails): `_dil` turns a
regex into an automaton, including outer lookaheads (intersection / complement) and `(?!.*(.)\\1)`. Whatever cannot be
turned into an automaton exactly (lookbehind, other backreferences, inner anchors, flags) falls back to the hidden tests;
`via` records which path decided. Items whose gold uses the undefined "special characters" set stay on the tests, see OZEL.
A "wrong" verdict is believed only if the regex engine confirms the counterexample, and an automaton is used only if it
agrees with the engine on the item's strings, so a translation bug cannot silently change a score.

This file started as a copy of the source's core.py; the automaton part and strip_anchors were changed on 5 Nov 2026
(ek_setler/regex/kaynak stays as received).

IMPORTANT: the equivalence timeout uses SIGALRM, which only works in the MAIN thread. Score in the main thread or in
forked processes (sweep.py does), never in a thread pool: there every checkable item would silently fall back to the
hidden tests (a real bug we had once).
"""
from __future__ import annotations

import re as _re
import signal
import string
import threading
from collections import deque
from contextlib import contextmanager

import greenery  # noqa: F401  zorunlu (greenery==4.2.3): yoksa her oge sessizce gizli testlere duserdi (2026-11-06)
import regex

TURKISH = "çğıöşüÇĞİÖŞÜ"
POOL = string.ascii_letters + string.digits + " .,-_/:@+()#" + TURKISH
MATCH_TIMEOUT = 0.5   # seconds per fullmatch; longer = catastrophic backtracking
EQUIV_TIMEOUT = 30    # seconds per equivalence check; long literal alternations need ~4 s on an idle machine
# Equivalence is decided over printable ASCII + Turkish letters (no newline/control chars): counterexamples are readable.
UNIVERSE = [chr(c) for c in range(32, 127)] + list(TURKISH)
# StructuredRegex's "special characters": tarifs never list this set, so a model may fairly read it as ASCII punctuation. The
# hidden tests accept that reading, an equivalence check would not; these items stay on the tests.
OZEL = "[-,;.+:!@#_$%&*=^]"


def _kacisli(s: str, i: int) -> bool:
    """Is s[i] escaped, i.e. preceded by an odd number of backslashes?"""
    n = 0
    while i - n - 1 >= 0 and s[i - n - 1] == "\\":
        n += 1
    return n % 2 == 1


def strip_anchors(rx: str) -> str:
    s = rx
    if s.startswith("^"):
        s = s[1:]
    elif s.startswith(r"\A"):
        s = s[2:]
    if s.endswith(r"\Z") and not _kacisli(s, len(s) - 2):
        s = s[:-2]
    elif s.endswith("$") and not _kacisli(s, len(s) - 1):
        s = s[:-1]
    return s


def compile_rx(rx: str):
    return regex.compile(strip_anchors(rx), flags=regex.ASCII | regex.V0)


def fullmatch(pat, s: str) -> bool | None:
    """True/False, or None on timeout (catastrophic backtracking)."""
    try:
        return pat.fullmatch(s, timeout=MATCH_TIMEOUT) is not None
    except TimeoutError:
        return None


class _Timeout(Exception):
    pass


@contextmanager
def _alarm(sec: int):
    if threading.current_thread() is not threading.main_thread():
        yield  # no timeout available off the main thread (see module docstring)
        return

    def handler(*_):
        raise _Timeout()
    old = signal.signal(signal.SIGALRM, handler)
    signal.alarm(sec)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class _Cevrilemez(Exception):
    """The regex has no exact automaton here; the caller falls back to the hidden tests."""


def _sinif(rx: str, i: int) -> tuple[str, int]:
    """Character class at rx[i] == '[' -> (the same class in greenery's syntax, index after it)."""
    j, cik = i + 1, "["
    if rx[j:j + 1] == "^":
        cik, j = "[^", j + 1
    ogeler = []  # (text for greenery, is it a single character)
    ilk = True
    while True:
        if j >= len(rx):
            raise _Cevrilemez("sinif")
        c = rx[j]
        if c == "]" and not ilk:
            break
        ilk = False
        if c == "\\":
            n = rx[j + 1:j + 2]
            if n in tuple("dwsDWS"):
                ogeler.append(("\\" + n, False))
            elif n in tuple("tnrfv"):
                ogeler.append(("\\" + n, True))
            elif n == "x" or n.isalnum() or not n:  # \b is a backspace here, \p{..} and friends are not greenery's
                raise _Cevrilemez("sinif kacisi")
            else:
                ogeler.append(("\\" + n if n in "\\[]^-" else n, True))
            j += 2
            continue
        if c == "[" and rx[j + 1:j + 2] == ":":
            raise _Cevrilemez("posix")
        if c == "-":
            ogeler.append(("-", None))
        else:
            ogeler.append(("\\" + c if c in "[]^" else c, True))
        j += 1
    out, k = [], 0
    while k < len(ogeler):
        m, tek = ogeler[k]
        if k + 2 < len(ogeler) and tek and ogeler[k + 1][1] is None and ogeler[k + 2][1] is True:  # range: a-z
            out.append(f"{m}-{ogeler[k + 2][0]}")
            k += 3
        else:
            out.append("\\-" if tek is None else m)
            k += 1
    return cik + "".join(out) + "]", j + 1


def _greenery(rx: str) -> str:
    """The same regex in greenery's dialect, or _Cevrilemez when greenery would read it differently from the regex engine.
    Unescaped ^ and $ are the dangerous case: greenery takes them as literal characters."""
    out, i = [], 0
    while i < len(rx):
        c = rx[i]
        if c == "\\":
            n = rx[i + 1:i + 2]
            if n in tuple("dwsDWStnrfv"):
                out.append("\\" + n)
            elif n == "x":
                out.append("\\x")
            elif not n or n.isalnum():  # \b \Z \A \1 \p \h ...
                raise _Cevrilemez("kacis")
            elif n in "\\[]|().?*+{}":
                out.append("\\" + n)
            else:
                out.append({"^": "[\\^]", "$": "[$]"}.get(n, n))
            i += 2
        elif c == "[":
            m, i = _sinif(rx, i)
            out.append(m)
        elif c in "^$":
            raise _Cevrilemez("ic capa")
        elif c == "(" and rx[i + 1:i + 2] == "?":
            if rx[i + 2:i + 3] == ":":
                out.append("(?:")
                i += 3
            elif rx[i + 2:i + 4] == "P<":
                out.append("(")
                i = rx.index(">", i) + 1
            else:
                raise _Cevrilemez("grup")
        elif c == "{" and rx[i + 1:i + 2] == ",":  # a{,3}
            out.append("{0,")
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _kapanis(rx: str, i: int) -> int:
    """Index of the parenthesis closing the one at rx[i]."""
    d, j = 0, i
    while j < len(rx):
        c = rx[j]
        if c == "\\":
            j += 2
            continue
        if c == "[":
            j = _sinif(rx, j)[1]
            continue
        d += c == "("
        d -= c == ")"
        if d == 0:
            return j
        j += 1
    raise _Cevrilemez("parantez")


def _ust_duzey_veya(rx: str) -> bool:
    d, j = 0, 0
    while j < len(rx):
        c = rx[j]
        if c == "\\":
            j += 2
            continue
        if c == "[":
            j = _sinif(rx, j)[1]
            continue
        d += c == "("
        d -= c == ")"
        if c == "|" and d == 0:
            return True
        j += 1
    return False


def _duz(rx: str):
    from greenery import parse
    return ("duz", parse(_greenery(rx)).to_fsm())


TEKRAR = _re.compile(r"\.\*\??\((\.|\[(?:\\.|[^\]\\])+\])\)\\1(?:\.\*\??)?")


def _bakis(ic: str):
    """Language of the strings on which a lookahead's body matches, from position 0."""
    m = TEKRAR.fullmatch(ic)
    if m:
        p = regex.compile(m.group(1), flags=regex.ASCII | regex.V0)
        return ("tekrar", frozenset(c for c in UNIVERSE if p.fullmatch(c)))
    if ic.endswith(r"\Z") and not _kacisli(ic, len(ic) - 2) or ic.endswith("$") and not _kacisli(ic, len(ic) - 1):
        if _ust_duzey_veya(ic):
            raise _Cevrilemez("capali veya")  # a|b\Z: only b is anchored
        return _dil(ic[:-2] if ic.endswith(r"\Z") else ic[:-1])
    return _duz(f"(?:{ic}).*")  # a lookaround inside is refused here: it would see the text after the group


def _dil(rx: str):
    """Language of `rx` under fullmatch, as a tree of ("duz", fsm) | ("tekrar", chars) | ("ve", a, b) | ("degil", a).
    Only lookaheads at position 0 are translated, so they see the whole string."""
    rx = strip_anchors(rx)
    if rx.startswith(("(?=", "(?!")):
        j = _kapanis(rx, 0)
        ic, kalan = rx[3:j], rx[j + 1:]
        if kalan[:1] in tuple("?*+{"):
            raise _Cevrilemez("nicelikli bakis")
        L, R = _bakis(ic), _dil(kalan)
        return ("ve", L if rx[2] == "=" else ("degil", L), R)
    if rx.startswith("(?:") and rx[3:6] in ("(?=", "(?!") and _kapanis(rx, 0) == len(rx) - 1:
        return _dil(rx[3:-1])
    return _duz(rx)


class _Otomat:
    """Lazy product of the languages' pieces over UNIVERSE. greenery only builds the plain pieces: its own product over a large
    alphabet takes tens of seconds, a table walk here takes milliseconds.

    Letters of a cell of all the pieces' classes are interchangeable. A repeat constraint (`.*(.)\1.*`) only asks whether
    neighbours are equal, so any string can be rewritten with 2 letters per cell keeping every membership: two languages
    differ on the universe exactly when they differ on these representatives. Without a repeat constraint 1 letter is enough."""

    def __init__(self, *agaclar):
        self.yaprak = []
        self.agac = [self._duzle(a) for a in agaclar]
        self.hucre = {c: [] for c in UNIVERSE}
        for y in self.yaprak:
            for c in UNIVERSE:
                self.hucre[c].append(c in y[1] if y[0] == "tekrar" else y[2][c])
        hucreler = {}
        for c in [*POOL, *UNIVERSE]:
            h = hucreler.setdefault(tuple(self.hucre[c]), [])
            if c not in h:
                h.append(c)
        self.hucreler = list(hucreler.values())
        n = 2 if any(y[0] == "tekrar" for y in self.yaprak) else 1
        self.temsil = [c for h in self.hucreler for c in h[:n]]
        self.bas = tuple(y[1].initial if y[0] == "duz" else None for y in self.yaprak)

    def _duzle(self, a):
        if a[0] in ("duz", "tekrar"):
            if a[0] == "duz":
                f = a[1]
                self.yaprak.append(("duz", f, {c: next(cc for cc in f.alphabet if cc.accepts(c)) for c in UNIVERSE}))
            else:
                self.yaprak.append(("tekrar", a[1]))
            return ("y", len(self.yaprak) - 1)
        return (a[0], *(self._duzle(x) for x in a[1:]))

    def adim(self, d, c):
        out = []
        for y, q in zip(self.yaprak, d):
            if y[0] == "duz":
                out.append(y[1].map[q][y[2][c]])
            else:
                out.append(True if q is True or q == c else (c if c in y[1] else None))
        return tuple(out)

    def _degerle(self, a, d):
        if a[0] == "y":
            y, q = self.yaprak[a[1]], d[a[1]]
            return q in y[1].finals if y[0] == "duz" else q is True
        if a[0] == "degil":
            return not self._degerle(a[1], d)
        return self._degerle(a[1], d) and self._degerle(a[2], d)

    def kabul(self, i, d):
        return self._degerle(self.agac[i], d)

    def kabul_eder(self, i, s):
        """Membership of s in language i; None if s has a character outside the universe."""
        d = self.bas
        for c in s:
            if c not in self.hucre:
                return None
            d = self.adim(d, c)
        return self.kabul(i, d)

    def en_kisa_fark(self):
        """Shortest representative string on which languages 0 and 1 disagree; None if they never do."""
        gor, q = {self.bas: ""}, deque([self.bas])
        while q:
            d = q.popleft()
            if self.kabul(0, d) != self.kabul(1, d):
                return gor[d]
            for c in self.temsil:
                n = self.adim(d, c)
                if n not in gor:
                    gor[n] = gor[d] + c
                    q.append(n)
        return None


def _otomat(*rxs) -> _Otomat:
    return _Otomat(*(_dil(rx) for rx in rxs))


def counterexample(gold: str, cand: str, ornekler=()) -> dict | None:
    """Shortest universe string on which gold and cand disagree; None if equivalent.
    Raises ValueError if either side cannot be checked (unsupported construct, too slow, or an automaton that disagrees with
    the regex engine on `ornekler` or on the counterexample itself)."""
    pg, pc = compile_rx(gold), compile_rx(cand)
    try:
        with _alarm(EQUIV_TIMEOUT):
            o = _otomat(gold, cand)
            s = o.en_kisa_fark()
            for t in ornekler:
                for i, p in ((0, pg), (1, pc)):
                    v = o.kabul_eder(i, t)
                    if v is not None and v != fullmatch(p, t):
                        raise ValueError("automaton disagrees with the engine")
    except _Timeout:
        raise ValueError("equivalence check timed out")
    except Exception as ex:
        raise ValueError(f"not checkable: {type(ex).__name__}")
    if s is None:
        return None
    a, b = fullmatch(pg, s), fullmatch(pc, s)
    if a is None or b is None or a == b:
        raise ValueError("counterexample not confirmed by the engine")
    return {"string": s, "should_match": a}


def dfa_uygun(item: dict) -> bool:
    return OZEL not in item["regex"]


def score(item: dict, cand: str) -> dict:
    """-> {ok, kind, via, counterexample?}. kind: correct | syntax | timeout | wrong. via: dfa | tests.
    Falls back to the hidden tests when gold or candidate has no exact automaton, or when the equivalence check exceeds
    EQUIV_TIMEOUT (e.g. a long alternation of literal strings); `via` records which path decided."""
    try:
        pat = compile_rx(cand)
    except regex.error as ex:
        return {"ok": False, "kind": "syntax", "detail": str(ex)}
    if dfa_uygun(item):
        try:
            ce = counterexample(item["regex"], cand, (*item["pos_hidden"], *item["neg_hidden"]))
            return {"ok": ce is None, "kind": "correct" if ce is None else "wrong", "via": "dfa", "counterexample": ce}
        except ValueError:
            pass
    for pool in ("pos_hidden", "neg_hidden"):
        for s in item[pool]:
            r = fullmatch(pat, s)
            if r is None:
                return {"ok": False, "kind": "timeout", "via": "tests", "detail": s}
            if r != (pool == "pos_hidden"):
                return {"ok": False, "kind": "wrong", "via": "tests", "counterexample": None, "failed_on": s}
    return {"ok": True, "kind": "correct", "via": "tests"}


def ceviri_denetle(item: dict) -> str | None:
    """altin_sinama: the gold's automaton must agree with the engine on all the item's strings. None when fine or when the
    gold has no automaton (tests decide); otherwise the first string they disagree on."""
    try:
        with _alarm(EQUIV_TIMEOUT):
            o = _otomat(item["regex"])
    except Exception:
        return None
    pat = compile_rx(item["regex"])
    for s in (*item["pos_hidden"], *item["neg_hidden"], *(x for x, _ in item.get("feedback_pool", []))):
        v = o.kabul_eder(0, s)
        if v is not None and v != fullmatch(pat, s):
            return s
    return None


def partial(item: dict, cand: str | None) -> float:
    """Diagnostic only: share of hidden strings the candidate classifies correctly (0 if it does not compile)."""
    if not cand:
        return 0.0
    try:
        pat = compile_rx(cand)
    except regex.error:
        return 0.0
    tests = [(s, True) for s in item["pos_hidden"]] + [(s, False) for s in item["neg_hidden"]]
    return sum(fullmatch(pat, s) is want for s, want in tests) / len(tests) if tests else 0.0


def feedback_example(item: dict, cand: str, shown: list[str]) -> dict | None:
    """Counterexample shown to the model: DFA difference when checkable, else the first misclassified string of the
    separate feedback pool (never the hidden tests)."""
    try:
        pat = compile_rx(cand)
    except regex.error:
        return None
    if dfa_uygun(item):
        try:
            return counterexample(item["regex"], cand)
        except ValueError:
            pass
    for s, should in item["feedback_pool"]:
        if s not in shown and fullmatch(pat, s) != should:
            return {"string": s, "should_match": should}
    return None


# ---------------------------------------------------------------- T3: extraction from customer-service messages
def compile_find(rx: str):
    return regex.compile(rx, flags=regex.ASCII | regex.V0)


def find_all(pat, text: str) -> list[str] | None:
    try:
        return [m.group(0) for m in pat.finditer(text, timeout=MATCH_TIMEOUT)]
    except TimeoutError:
        return None


def score_extract(item: dict, cand: str) -> dict:
    try:
        pat = compile_find(cand)
    except regex.error as ex:
        return {"ok": False, "kind": "syntax", "detail": str(ex)}
    for row in item["hidden"]:
        got = find_all(pat, row["text"])
        if got is None:
            return {"ok": False, "kind": "timeout"}
        if got != row["gold"]:
            return {"ok": False, "kind": "wrong"}
    return {"ok": True, "kind": "correct"}


def partial_extract(item: dict, cand: str | None) -> float:
    if not cand:
        return 0.0
    try:
        pat = compile_find(cand)
    except regex.error:
        return 0.0
    return sum(find_all(pat, r["text"]) == r["gold"] for r in item["hidden"]) / len(item["hidden"])


def feedback_extract(item: dict, cand: str) -> dict | None:
    try:
        pat = compile_find(cand)
    except regex.error:
        return None
    for row in item["feedback_pool"]:
        got = find_all(pat, row["text"])
        if got != row["gold"]:
            return {"text": row["text"], "expected": row["gold"], "got": got}
    return None

"""RAMAYAN: the epic in about 85 seconds.

One board in the charcoal look: a map of India and Lanka in the middle, the cold open (Ravana, the
bridge, Rama) out on the board east of Lanka, Ayodhya's prints to the north-east, the forest to the
west beside Panchavati, the search by Kishkindha, the war below Lanka. The camera travels along the
route the story takes: Ayodhya, the forest, Kishkindha, the sea, Lanka, and home again.

Every time comes from the voiceover (doc.L line start, doc.E line end, doc.W spoken word), so a new
voice re-times the whole film. World units are 4K pixels at zoom 1.
"""
from engine import (HILITE, MUSTARD, RUST, WHITE, BigText, Counter, Film, GeoMap, PenMark, Print,
                    RegionFill, Route, Stamp, StringLine, XMarker)

K = 30000                      # map scale: India about 15,000 world px tall
LBL = dict(size=3.0, label_size=170)
GOLD = (238, 196, 92)
DARK = (30, 26, 22)

# clusters (world px)
OX, OY = 12700, 5600           # cold open, east of Lanka
AX, AY = 14000, -5400          # Ayodhya, north-east
FX, FY = -12600, -1600         # the forest, west of Panchavati
SX, SY = -11800, 4600          # the search, beside Kishkindha
BX, BY = 9600, 10600           # the war, below Lanka


def build_film(doc):
    L, E, W = doc.L, doc.E, doc.W
    film = Film(doc.duration, fps=30, look="charcoal")
    cam, foc, cue = film.cam, film.focus, film.cue

    india = film.add(GeoMap(doc.map("india"), K, look="explainer"))
    ayo, pan, kis = india.place("Ayodhya"), india.place("Panchavati"), india.place("Kishkindha")
    ram, lanka = india.place("Rameswaram"), india.place("Lanka")

    # ============================================================ COLD OPEN (1-3)
    film.add(RegionFill(india, ["Sri Lanka"], RUST, W(1, "island"), to_rgb=MUSTARD, t_change=L(16)))
    film.add(XMarker(*lanka, "LANKA", t_in=W(1, "fortress"), side="right", **LBL))
    ravana = film.add(Print("P01", OX - 3300, OY - 300, 2100, rot=-1.4, t_in=W(1, "king") - 0.1,
                            label="RAVANA", label_t=W(1, "heads")))
    film.add(StringLine(lanka, (OX - 4350, OY - 1900), t_in=W(1, "king"), dur=0.7, sag=0.03, width=18, persist=True))
    bridge = film.add(Print("P02", OX, OY - 200, 1700, rot=1.2, t_in=L(2) + 0.05))
    rama = film.add(Print("P03", OX + 3300, OY - 300, 2300, rot=-0.8, t_in=L(3) + 0.05,
                          label="RAMA", label_t=W(3, "prince")))
    (rx, ry) = doc.on(rama, 0.47, 0.36)
    film.add(PenMark("ellipse", rx, ry, 1100, 1250, t_in=W(3, "prince") - 0.1, dur=0.6, width=26, seed=4, rgb=GOLD))

    title_t = E(3) + 0.4
    film.add(BigText("RAMAYAN", OX, OY - 3300, 1100, title_t, rgb=WHITE, hit=None))
    film.add(PenMark("underline", OX, OY - 2650, 5200, 60, t_in=title_t + 0.35, dur=0.6, width=34, seed=2, rgb=GOLD))
    cue("boom", title_t, 0.55)

    cam(0.0, lanka[0] + 600, lanka[1] - 300, 0.62, -0.6)
    cam(W(1, "fortress") + 0.2, lanka[0] + 900, lanka[1], 0.55, -0.3)
    cam(W(1, "king") - 0.45, lanka[0] + 1300, lanka[1] - 100, 0.55, -0.2)       # hold on Lanka, then whip to Ravana
    cam(W(1, "king") + 0.3, OX - 3300, OY - 300, 0.78, 0.4)
    cam(E(1) + 0.1, OX - 3200, OY - 200, 0.82, 0.6)
    cam(L(2) + 0.35, OX, OY - 200, 0.76, -0.4)
    cam(E(2) + 0.1, OX + 80, OY - 100, 0.8, -0.6)
    cam(L(3) + 0.35, OX + 3300, OY - 400, 0.82, 0.3)
    cam(E(3) + 0.1, OX + 3300, OY - 600, 0.86, 0.5)
    cam(title_t + 0.6, OX, OY - 1400, 0.4, 0.0)                     # pull back: title over the three prints
    cam(title_t + 1.2, OX, OY - 1300, 0.38, -0.2)
    foc(0.0, lanka[0] + 600, lanka[1], 3400, 0.3)
    foc(W(1, "king") + 0.2, OX - 3300, OY - 300, 1900, 0.6)
    foc(L(2) + 0.3, OX, OY - 200, 1700, 0.62)
    foc(L(3) + 0.3, OX + 3300, OY - 300, 1900, 0.6)
    foc(title_t + 0.3, OX, OY - 1300, 6000, 0.35)

    # ============================================================ AYODHYA (4-7)
    film.add(StringLine((OX + 3300, OY - 2000), ayo, t_in=L(4) + 0.1, dur=1.3, sag=0.02, width=22))
    film.add(XMarker(*ayo, "AYODHYA", t_in=W(4, "Ayodhya") - 0.1, side="right", **LBL))
    film.add(StringLine(ayo, (AX - 4300, AY - 1500), t_in=W(4, "throne"), dur=0.6, sag=0.03, width=16, persist=True))
    bow = film.add(Print("P04", AX - 3000, AY, 2000, rot=-1.6, t_in=W(5, "won") - 0.1,
                         label="SITA", label_t=W(5, "Sita")))
    (bx, by) = doc.on(bow, 0.24, 0.12)
    film.add(PenMark("strike", bx, by + 200, 700, 0, t_in=W(5, "snapped") - 0.1, dur=0.3, width=30, rot=-60, rgb=GOLD))
    film.add(Print("P05", AX, AY + 100, 2100, rot=1.3, t_in=W(6, "Queen") - 0.25,
                   label="KAIKEYI", label_t=W(6, "Kaikeyee")))
    film.add(Counter(AX + 3000, AY - 700, 760, 14, W(7, "fourteen") - 0.1, dur=0.9, suffix=" YEARS", caption="IN THE FOREST"))
    film.add(Stamp("EXILED", AX + 3000, AY + 1100, size=360, rot=-8, t_in=W(7, "forest") - 0.05))

    cam(L(4) + 0.5, (OX + ayo[0]) / 2 + 1500, (OY + ayo[1]) / 2, 0.24, 0.0)   # wide: the string races north
    cam(W(4, "Ayodhya") + 0.1, ayo[0] + 1200, ayo[1] - 200, 0.42, 0.2)
    cam(W(5, "won") + 0.3, AX - 3000, AY - 100, 0.78, -0.4)
    cam(W(5, "snapped") + 0.2, bx + 300, by + 400, 0.95, -0.6)
    cam(E(5) + 0.1, AX - 2800, AY - 200, 0.8, -0.4)
    cam(W(6, "Queen") + 0.1, AX, AY + 100, 0.8, 0.4)
    cam(E(6) + 0.1, AX + 50, AY + 200, 0.84, 0.6)
    cam(W(7, "fourteen") + 0.2, AX + 3000, AY, 0.62, 0.0)
    cam(E(7) + 0.2, AX + 2950, AY + 150, 0.6, -0.3)
    foc(L(4) + 0.4, ayo[0] + 3000, ayo[1], 9000, 0.25)
    foc(W(4, "Ayodhya") - 0.2, ayo[0] + 1200, ayo[1] - 200, 3200, 0.35)
    foc(W(5, "won") + 0.2, AX - 3000, AY, 1800, 0.6)
    foc(W(6, "Queen"), AX, AY + 100, 1800, 0.6)
    foc(W(7, "fourteen") + 0.1, AX + 3000, AY, 1800, 0.6)

    # ============================================================ THE FOREST (8-11)
    cue("riser", L(8) - 1.0, 0.4, dur=1.0)
    film.add(Route(ayo, pan, t_in=L(8) + 0.3, dur=1.8, bend=-0.2, width=60))
    film.add(XMarker(*pan, "PANCHAVATI", t_in=L(8) + 1.9, side="left", **LBL))
    film.add(BigText("LAKSHMANA", pan[0] - 2600, pan[1] - 1500, 400, W(8, "Lakshmana") - 0.1,
                     bar=HILITE, bar_h=0.92, rgb=DARK, shadow=False))
    film.add(Print("P06", FX + 3000, FY, 1700, rot=1.8, t_in=W(9, "golden") - 0.15))
    abd = film.add(Print("P07", FX - 300, FY + 100, 2400, rot=-1.2, t_in=W(10, "Raavan") - 0.15,
                         label="RAVANA", label_t=W(10, "holy")))
    film.add(Stamp("TAKEN", FX - 300, FY + 1300, size=380, rot=7, t_in=W(10, "sky") - 0.05))
    (jx, jy) = doc.on(abd, 0.28, 0.28)
    film.add(PenMark("ellipse", jx, jy, 1500, 1300, t_in=W(11, "Jataayu") - 0.2, dur=0.6, width=26, seed=9, rot=-12, rgb=GOLD))
    film.add(BigText("JATAYU", FX - 2700, jy, 340, W(11, "Jataayu"), bar=HILITE, bar_h=0.92, rgb=DARK, shadow=False))

    cam(L(8) + 0.6, (ayo[0] + pan[0]) / 2 - 800, (ayo[1] + pan[1]) / 2, 0.3, 0.0)
    cam(W(8, "Lakshmana") + 0.2, pan[0] - 2000, pan[1] - 1000, 0.5, -0.2)
    cam(W(9, "golden") + 0.2, FX + 3000, FY, 0.85, 0.4)
    cam(E(9) + 0.1, FX + 3050, FY + 100, 0.9, 0.6)
    cam(W(10, "Raavan") + 0.3, FX - 300, FY + 100, 0.72, -0.4)
    cam(W(10, "sky") + 0.2, FX - 300, FY + 600, 0.76, -0.6)
    cam(W(11, "Jataayu") + 0.1, jx - 900, jy, 0.82, -0.8)
    cam(E(11) + 0.2, jx - 850, jy + 100, 0.85, -1.0)
    foc(L(8) + 0.5, (ayo[0] + pan[0]) / 2, (ayo[1] + pan[1]) / 2, 8000, 0.25)
    foc(W(9, "golden"), FX + 3000, FY, 1600, 0.6)
    foc(W(10, "Raavan") + 0.2, FX - 300, FY + 100, 2100, 0.6)
    foc(W(11, "Jataayu"), jx, jy, 1400, 0.6)

    # ============================================================ THE SEARCH (12-14)
    film.add(Route(pan, kis, t_in=L(12) + 0.1, dur=1.0, bend=0.2, width=50))
    film.add(XMarker(*kis, "KISHKINDHA", t_in=L(12) + 0.9, side="left", **LBL))
    meet = film.add(Print("P08", SX, SY, 3200, rot=1.0, t_in=W(12, "allies") - 0.1))
    (hx, hy) = doc.on(meet, 0.72, 0.5)
    film.add(StringLine(kis, (SX + 1600, SY - 1100), t_in=W(12, "allies"), dur=0.5, sag=0.03, width=16, persist=True))
    film.add(BigText("SUGRIVA", SX - 900, SY + 1500, 300, W(12, "Sugreeva") - 0.05, bar=HILITE, bar_h=0.92, rgb=DARK, shadow=False))
    film.add(BigText("HANUMAN", hx, SY + 1500, 300, W(12, "Hanuman") - 0.05, bar=HILITE, bar_h=0.92, rgb=DARK, shadow=False))
    film.add(Route(kis, lanka, t_in=W(13, "leapt") - 0.1, dur=1.1, bend=-0.35, width=60))
    film.add(Print("P09", BX - 4300, BY - 400, 2000, rot=-1.5, t_in=W(13, "Lanka") - 0.6))
    film.add(StringLine(lanka, (BX - 4300, BY - 1800), t_in=W(13, "Lanka") - 0.4, dur=0.5, sag=0.03, width=16, persist=True))
    film.add(Route(ram, lanka, t_in=L(14) + 0.2, dur=1.0, bend=0.05, width=90, rgb=GOLD))       # the bridge on the map

    cam(L(12) + 0.4, (pan[0] + kis[0]) / 2 - 2000, (pan[1] + kis[1]) / 2 + 600, 0.36, 0.2)
    cam(W(12, "allies") + 0.3, SX, SY, 0.6, 0.4)
    cam(W(12, "Hanuman") + 0.2, SX + 700, SY + 300, 0.66, 0.6)
    cam(W(13, "leapt") + 0.2, (kis[0] + lanka[0]) / 2, (kis[1] + lanka[1]) / 2 + 600, 0.3, 0.0)
    cam(W(13, "burning") + 0.1, BX - 4300, BY - 400, 0.62, -0.4)
    cam(L(14) + 0.5, (ram[0] + lanka[0]) / 2 + 300, (ram[1] + lanka[1]) / 2, 0.55, 0.0)
    cam(W(14, "crossed") + 0.1, OX, OY - 200, 0.7, 0.4)                                     # back to the bridge folio
    cam(E(14) + 0.3, OX + 50, OY - 150, 0.72, 0.6)
    foc(L(12) + 0.3, (pan[0] + kis[0]) / 2, (pan[1] + kis[1]) / 2, 7000, 0.25)
    foc(W(12, "allies") + 0.2, SX, SY, 2600, 0.5)
    foc(W(13, "leapt") + 0.1, (kis[0] + lanka[0]) / 2, (kis[1] + lanka[1]) / 2, 8000, 0.25)
    foc(W(13, "burning"), BX - 4300, BY - 400, 1900, 0.6)
    foc(L(14) + 0.4, (ram[0] + lanka[0]) / 2, (ram[1] + lanka[1]) / 2, 2600, 0.4)
    foc(W(14, "crossed"), OX, OY - 200, 1700, 0.6)

    # ============================================================ CLOSE (15-19)
    cue("riser", L(15) - 1.0, 0.5, dur=1.0)
    war = film.add(Print("P10", BX, BY, 3600, rot=0.8, t_in=L(15) + 0.05))
    film.add(Stamp("FALLEN", BX + 600, BY + 300, size=380, rot=-7, t_in=W(15, "fell") - 0.05))
    film.add(Route(lanka, ayo, t_in=L(16) + 0.2, dur=1.6, bend=0.25, width=60, rgb=GOLD))   # home again
    film.add(Print("P11", AX + 7000, AY, 2100, rot=-1.0, t_in=W(16, "lamps") - 0.35))
    film.add(BigText("DIWALI", AX + 7000, AY + 2400, 620, W(17, "Diwali") - 0.1, bar=HILITE, bar_h=0.92, rgb=DARK, shadow=False))
    film.add(Counter(AX + 1500, AY + 4300, 640, 24000, L(18) + 0.15, dur=W(18, "thousand") - L(18), suffix=" VERSES", caption="VALMIKI"))

    cam(L(15) + 0.4, BX, BY, 0.62, 0.3)
    cam(W(15, "fell") + 0.2, BX + 500, BY + 250, 0.72, 0.6)
    cam(L(16) + 0.6, (lanka[0] + ayo[0]) / 2 + 2500, (lanka[1] + ayo[1]) / 2, 0.21, 0.0)    # wide: the flight home
    cam(W(16, "lamps") + 0.1, AX + 7000, AY, 0.72, -0.3)
    cam(E(16) + 0.1, AX + 7000, AY + 300, 0.74, -0.4)
    cam(W(17, "Diwali") + 0.1, AX + 7000, AY + 1300, 0.62, 0.0)
    cam(E(17) + 0.1, AX + 6000, AY + 1600, 0.58, 0.2)
    cam(L(18) + 0.5, AX + 1500, AY + 4400, 0.6, 0.3)
    cam(E(18) + 0.1, AX + 1500, AY + 4450, 0.6, 0.2)
    cam(W(19, "thousand") + 0.3, 4000, 1500, 0.15, 0.0)
    cam(film.duration, 4000, 2600, 0.104, 0.0)                                                # the whole board
    foc(L(15) + 0.3, BX, BY, 2800, 0.55)
    foc(L(16) + 0.5, (lanka[0] + ayo[0]) / 2, (lanka[1] + ayo[1]) / 2, 9000, 0.2)
    foc(W(16, "lamps"), AX + 7000, AY, 1900, 0.6)
    foc(W(17, "Diwali"), AX + 7000, AY + 1300, 2400, 0.55)
    foc(L(18) + 0.4, AX + 1500, AY + 4300, 2400, 0.55)
    foc(W(19, "thousand") + 0.2, 4000, 2500, 24000, 0.1)

    film.fade_in, film.fade_out = 0.9, 2.2
    return film

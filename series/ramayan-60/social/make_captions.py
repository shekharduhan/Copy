"""Build captions for YouTube Shorts, TikTok, Instagram Reels and Facebook Reels for all 60 episodes,
as a copy-paste PDF (Ramayan_60_Captions.pdf) and a plain-text twin (captions.txt).

  python3 make_captions.py
"""
import json
import pathlib
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SERIES = "Ramayan in 60 Seconds"

pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

CHAR_TAGS = [  # name as written in the scripts -> hashtag
    ("Rama", "Rama"), ("Sita", "Sita"), ("Lakshmana", "Lakshman"), ("Hanuman", "Hanuman"), ("Ravana", "Ravana"),
    ("Bharata", "Bharat"), ("Dasharatha", "Dasharatha"), ("Sugriva", "Sugriva"), ("Vibhishana", "Vibhishan"),
    ("Jatayu", "Jatayu"), ("Shabari", "Shabari"), ("Kumbhakarna", "Kumbhakarna"), ("Indrajit", "Indrajit"),
    ("Vali", "Bali"), ("Angada", "Angad"), ("Surpanakha", "Surpanakha"), ("Parashurama", "Parshuram"),
    ("Ahalya", "Ahalya"), ("Kaikeyi", "Kaikeyi"), ("Manthara", "Manthara"), ("Janaka", "Janak"),
    ("Vishwamitra", "Vishwamitra"), ("Jambavan", "Jambavan"), ("Garuda", "Garuda"), ("Maricha", "Maricha"),
    ("Kabandha", "Kabandha"), ("Guha", "Guha"), ("Agastya", "Agastya"), ("Anasuya", "Anasuya"),
    ("Sampati", "Sampati"), ("Surasa", "Surasa"), ("Lankini", "Lankini"), ("Vasishtha", "Vasishtha"),
]
EXTRA_TAGS = {20: ["Paduka"], 39: ["JaiShriRam"], 45: ["LankaDahan"], 49: ["RamSetu"], 54: ["Sanjeevani"], 59: ["AgniPariksha"], 60: ["Diwali", "JaiShriRam"]}
QUESTIONS = [
    "Did you know this part of the story?",
    "Who is your favourite character so far?",
    "What would you have done in their place?",
    "Which moment hit you the hardest?",
    "Have you heard this story from your grandparents?",
]


def chars(ep):
    text = " ".join(b["text"] + " " + b["visual"] for b in ep["beats"])
    return [tag for name, tag in CHAR_TAGS if re.search(r"\b" + name + r"\b", text)]


def summary(ep, limit=260):
    s = ""
    for b in ep["beats"]:
        nxt = (s + " " + b["text"]).strip()
        if len(nxt) > limit and s:
            break
        s = nxt
    return s


def build(eps, hooks):
    out = []
    for i, ep in enumerate(eps):
        n, title, hook = ep["ep"], ep["title"], hooks[str(ep["ep"])]
        nxt = eps[i + 1] if i + 1 < len(eps) else None
        cs = chars(ep)[:4] + EXTRA_TAGS.get(n, [])
        story = summary(ep)
        follow = f"Next: Part {n + 1}, {nxt['title']}." if nxt else "The final part. Thank you for watching all 60."
        yt_title = f"{title} | Ramayan Ep {n} of 60 #Shorts"
        if len(yt_title) > 100:
            yt_title = f"{title} | Ramayan Ep {n} #Shorts"
        yt_desc = (f"{hook}\n\n{story}\n\nEpisode {n} of 60 in the {SERIES} series. {follow}\n\n"
                   "Story based on Valmiki's Ramayana (M.N. Dutt's public-domain English translation) and popular later retellings. "
                   "Narration and images are AI-generated.\n\n"
                   + " ".join("#" + t for t in ["Shorts", "Ramayan", "Ramayana"] + cs + ["HinduMythology", "IndianMythology"]))
        tiktok = (f"{hook} Ramayan Part {n}/60: {title}. "
                  + ("Follow for Part %d." % (n + 1) if nxt else "The end.")
                  + "\n" + " ".join("#" + t.lower() for t in ["Ramayan", "Ramayana"] + cs[:2] + ["HinduMythology", "Mythology", "StoryTime"]))
        insta = (f"{hook}\n\n{story}\n\n{SERIES}, Part {n} of 60: {title}.\n"
                 + (f"Follow so you don't miss Part {n + 1}, and save this to watch the series in order." if nxt else "That's the whole Ramayan. Save it and share it with someone who loves this story.")
                 + "\n.\n.\n"
                 + " ".join("#" + t.lower() for t in ["Ramayan", "Ramayana", "RamayanStory", "JaiShriRam"] + cs[:4]
                            + ["HinduMythology", "IndianMythology", "MythologyStories", "SanatanDharma", "ReelsIndia", "AnimatedStory"]))
        fb = (f"{hook}\n\n{story}\n\nPart {n} of 60 of our {SERIES} series. {QUESTIONS[(n - 1) % len(QUESTIONS)]} Tell us in the comments.\n\n"
              + " ".join("#" + t for t in ["Ramayan", "Ramayana"] + cs[:2] + ["IndianMythology"]))
        out.append({"ep": n, "title": title, "youtube_title": yt_title, "youtube_description": yt_desc,
                    "tiktok": tiktok, "instagram": insta, "facebook": fb})
    return out


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")


def pdf(caps, path):
    ink, accent, panel = colors.HexColor("#22201c"), colors.HexColor("#b4532a"), colors.HexColor("#f6f1e8")
    H1 = ParagraphStyle("h1", fontName="DVB", fontSize=20, leading=25, textColor=ink, spaceAfter=4)
    H2 = ParagraphStyle("h2", fontName="DVB", fontSize=15, leading=19, textColor=ink, spaceAfter=6)
    LBL = ParagraphStyle("lbl", fontName="DVB", fontSize=9.5, leading=12, textColor=accent, spaceBefore=6, spaceAfter=2)
    SUB = ParagraphStyle("sub", fontName="DVB", fontSize=8, leading=10, textColor=colors.HexColor("#6b655c"))
    BODY = ParagraphStyle("body", fontName="DV", fontSize=9, leading=12.5, textColor=ink, alignment=TA_LEFT)
    NOTE = ParagraphStyle("note", fontName="DV", fontSize=9.5, leading=13.5, textColor=ink, spaceAfter=5)

    def box(text):
        t = Table([[Paragraph(esc(text), BODY)]], colWidths=[174 * mm])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), panel), ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9cfbf")),
                               ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                               ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        return t

    story = [Paragraph(f"{SERIES}: captions for all 60 episodes", H1),
             Paragraph("Copy each box straight into the app. Every episode has its own page.", NOTE), Spacer(1, 6),
             Paragraph("How to post", H2)]
    tips = [
        "<b>YouTube Shorts.</b> Paste the title into Title and the description into Description. Add every episode to one playlist, "
        "\"Ramayan in 60 Seconds\", in order. After posting, pin a comment with the link to the next episode.",
        "<b>TikTok.</b> Paste the caption. Under More options, turn on <b>AI-generated content</b>. Add each video to a TikTok playlist (series) so viewers can binge in order.",
        "<b>Instagram Reels.</b> Paste the caption. Under Advanced settings, turn on <b>AI label</b> (\"Add AI info\"). Use a cover frame showing the episode title. Share each Reel to your Story to push it.",
        "<b>Facebook Reels.</b> Paste the caption. Turn on the <b>AI info</b> label if offered. Reply to the first few comments; the question at the end is there to get people talking.",
        "<b>AI labels.</b> The narration and images are AI-generated. TikTok and Meta ask creators to label AI content; YouTube asks only for realistic-looking content, so this animated style does not strictly need it there, but each description already says it.",
        "<b>Consistency.</b> Post in order, at the same time every day. Part numbers (\"Part 12/60\") make people go back and watch the earlier ones.",
        "<b>Sources.</b> The stories follow Valmiki's Ramayana; scenes from later retellings (the Lakshman Rekha, Shabari's tasted berries, the stones marked 'Ram', the nectar in Ravana's navel) are told as such in the narration.",
    ]
    story += [Paragraph(t, NOTE) for t in tips]
    for c in caps:
        story.append(PageBreak())
        story.append(Paragraph(f"Episode {c['ep']}: {esc(c['title'])}", H2))
        story.append(Paragraph(f"Video file: Ramayan_Ep{c['ep']:02d}.mp4", SUB))
        for label, key, sub in (("YOUTUBE SHORTS: TITLE", "youtube_title", ""), ("YOUTUBE SHORTS: DESCRIPTION", "youtube_description", ""),
                                ("TIKTOK: CAPTION", "tiktok", ""), ("INSTAGRAM REELS: CAPTION", "instagram", ""),
                                ("FACEBOOK REELS: CAPTION", "facebook", "")):
            story.append(KeepTogether([Paragraph(label, LBL), box(c[key])]))

    def footer(cv, doc):
        cv.saveState(); cv.setFont("DV", 7.5); cv.setFillColor(colors.HexColor("#8a8378"))
        cv.drawString(18 * mm, 10 * mm, f"{SERIES}: captions"); cv.drawRightString(192 * mm, 10 * mm, f"Page {doc.page}"); cv.restoreState()

    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
                      title=f"{SERIES}: captions", author="Ramayan series").build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    eps = json.loads((ROOT / "episodes_60s.json").read_text())
    hooks = json.loads((HERE / "hooks.json").read_text())
    caps = build(eps, hooks)
    (HERE / "captions.json").write_text(json.dumps(caps, ensure_ascii=False, indent=1))
    txt = []
    for c in caps:
        txt.append(f"===== EPISODE {c['ep']}: {c['title']} =====\n\n[YouTube title]\n{c['youtube_title']}\n\n[YouTube description]\n{c['youtube_description']}\n\n"
                   f"[TikTok]\n{c['tiktok']}\n\n[Instagram]\n{c['instagram']}\n\n[Facebook]\n{c['facebook']}\n")
    (HERE / "captions.txt").write_text("\n".join(txt))
    pdf(caps, HERE / "Ramayan_60_Captions.pdf")
    print("ok:", len(caps), "episodes; longest YouTube title", max(len(c["youtube_title"]) for c in caps), "chars;",
          "longest TikTok", max(len(c["tiktok"]) for c in caps), "chars")

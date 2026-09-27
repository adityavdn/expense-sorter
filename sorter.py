"""Expense sorter: categorises bank-statement transactions and learns from your corrections.
Pure Python, offline. What it learns is kept in brain.json next to this file.

  python3 sorter.py statement.csv            sort (asks about ones it's unsure of)
  python3 sorter.py statement.csv --no-ask   sort without questions
  python3 sorter.py learn statement_sorted.csv   learn from a sorted CSV you fixed by hand
"""
import csv
import json
import math
import os
import re
import sys

BRAIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brain.json")
ASK_BELOW = 0.6          # ask you when it's less sure than this
NOISE = set("""card payment to from on at purchase pos debit contactless ltd limited uk gb
www com co the and direct dd so fp bgc tfr ref visa gbp plc online mandate no""".split())

SEED = {  # starter knowledge; your corrections quickly outweigh it
    "Groceries": "tesco sainsburys asda aldi lidl morrisons waitrose coop iceland ocado",
    "Eating out": "mcdonalds kfc nandos greggs starbucks costa pret subway dominos deliveroo ubereats justeat pizza cafe restaurant",
    "Transport": "uber bolt tfl trainline gwr arriva stagecoach shell bp esso parking railway",
    "Subscriptions": "netflix spotify prime disney icloud youtube chatgpt openai adobe",
    "Shopping": "amazon argos primark ebay asos zara boots superdrug ikea currys",
    "Bills": "rent council tax gas octopus edf water vodafone ee o2 virgin bt sky licence",
    "Transfers": "transfer revolut wise paypal",
    "Cash": "atm cash withdrawal",
}


def tokens(text):
    return [w for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 1 and w not in NOISE]


def merchant(text):
    return " ".join(tokens(text)[:3])


class Brain:
    """Two ways of knowing:
    1. exact memory: a merchant you've labelled before gets the same label (confidence 1.0)
    2. naive Bayes over words, so a new merchant like 'TESCO EXPRESS' is guessed from
       similar ones it has seen, with a confidence score."""

    def __init__(self, path=BRAIN):
        self.path = path
        if os.path.exists(path):
            with open(path) as f:
                d = json.load(f)
            self.merchants, self.words, self.docs = d["merchants"], d["words"], d["docs"]
        else:
            self.merchants, self.words, self.docs = {}, {}, {}
            for cat, words in SEED.items():
                for w in words.split():
                    self._count(cat, [w])

    def _count(self, cat, toks):
        self.docs[cat] = self.docs.get(cat, 0) + 1
        counts = self.words.setdefault(cat, {})
        for t in toks:
            counts[t] = counts.get(t, 0) + 1

    def learn(self, desc, cat):
        if merchant(desc):
            self.merchants[merchant(desc)] = cat
        self._count(cat, tokens(desc))

    def guess(self, desc):
        if merchant(desc) in self.merchants:
            return self.merchants[merchant(desc)], 1.0
        toks = [t for t in tokens(desc) if any(t in c for c in self.words.values())]
        if not toks:
            return None, 0.0                             # never seen any of these words
        vocab = len({w for c in self.words.values() for w in c})
        scores = {}
        for cat in self.docs:            # no class prior: a category you've used twice still counts
            counts = self.words.get(cat, {})
            size = sum(counts.values())
            scores[cat] = sum(
                math.log((counts.get(t, 0) + 1) / (size + vocab)) for t in toks)
        best = max(scores, key=scores.get)
        confidence = 1 / sum(math.exp(s - scores[best]) for s in scores.values())
        return best, confidence

    def categories(self):
        return sorted(self.docs)

    def save(self):
        with open(self.path, "w") as f:
            json.dump({"merchants": self.merchants, "words": self.words, "docs": self.docs}, f, indent=1)


def money(text):
    text = (text or "").replace("£", "").replace(",", "").strip()
    return float(text) if text else 0.0


def read_statement(path):
    """Returns (rows, fieldnames, description column, signed amounts; negative = money out)."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows, headers = list(reader), reader.fieldnames or []

    def find(*names):
        return next((h for n in names for h in headers if h and n in h.lower()), None)

    desc = find("description", "memo", "narrative", "details", "payee", "merchant", "name", "reference")
    money_out, money_in = find("paid out", "money out", "debit"), find("paid in", "money in", "credit")
    amount = find("amount", "value")
    if not desc or not ((money_out and money_in) or amount):
        sys.exit(f"Couldn't spot the description/amount columns. Found: {', '.join(headers)}")
    if money_out and money_in:
        amounts = [money(r[money_in]) - money(r[money_out]) for r in rows]
    else:
        amounts = [money(r[amount]) for r in rows]
    return rows, headers, desc, amounts


def ask(desc, spent, guess, cats):
    print(f"\n  {desc}   £{spent:.2f}")
    print("  " + "   ".join(f"{i}.{c}" for i, c in enumerate(cats, 1)))
    while True:
        hint = f"Enter = {guess}" if guess else "type a number or new category"
        ans = input(f"  Category? [{hint}]: ").strip()
        if not ans and guess:
            return guess
        if ans.isdigit() and 1 <= int(ans) <= len(cats):
            return cats[int(ans) - 1]
        if ans and not ans.isdigit():
            return ans


def sort_statement(path, brain, interactive=True):
    rows, headers, desc_col, amounts = read_statement(path)
    asked = 0
    for row, amt in zip(rows, amounts):
        if amt > 0:
            row["Category"] = "Income"   # ponytail: refunds count as income; learn signs per merchant if that bites
            continue
        cat, conf = brain.guess(row[desc_col])
        if interactive and conf < ASK_BELOW:
            cat = ask(row[desc_col], -amt, cat, brain.categories())
            brain.learn(row[desc_col], cat)       # learns instantly, so repeats aren't asked again
            brain.save()
            asked += 1
        row["Category"] = cat or "Uncategorised"

    out = os.path.splitext(path)[0] + "_sorted.csv"
    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, [h for h in headers if h != "Category"] + ["Category"])
        writer.writeheader()
        writer.writerows(rows)

    spend = {}
    for row, amt in zip(rows, amounts):
        if amt < 0:
            spend[row["Category"]] = spend.get(row["Category"], 0) - amt
    total = sum(spend.values()) or 1
    print(f"\nSpending by category  ({len(rows)} transactions, asked you about {asked})\n")
    for cat, amt in sorted(spend.items(), key=lambda kv: -kv[1]):
        print(f"  {cat:<15} £{amt:>9.2f}  {'█' * round(30 * amt / total)}")
    print(f"  {'TOTAL':<15} £{sum(spend.values()):>9.2f}")
    print(f"  {'Income':<15} £{sum(a for a in amounts if a > 0):>9.2f}")
    print(f"\nSaved {out}")
    return out


def learn_file(path, brain):
    rows, _, desc_col, amounts = read_statement(path)
    n = 0
    for row, amt in zip(rows, amounts):
        cat = (row.get("Category") or "").strip()
        if amt <= 0 and cat and cat != "Uncategorised":
            brain.learn(row[desc_col], cat)
            n += 1
    brain.save()
    print(f"Learned from {n} transactions.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    if args[0] == "learn" and len(args) > 1:
        learn_file(args[1], Brain())
    else:
        sort_statement(args[0], Brain(), interactive="--no-ask" not in sys.argv and sys.stdin.isatty())

import csv
import os
import tempfile

from sorter import Brain, read_statement, sort_statement

d = tempfile.mkdtemp()
brain = Brain(os.path.join(d, "brain.json"))

# starter knowledge generalises to new merchant names
assert brain.guess("CARD PAYMENT TO TESCO STORES 3321")[0] == "Groceries"
assert brain.guess("SAINSBURYS LOCAL")[0] == "Groceries"
assert brain.guess("XYZ UNKNOWN") == (None, 0.0)          # unknown -> will ask

# learns from a correction: exact merchant is remembered...
brain.learn("PUREGYM LTD", "Fitness")
assert brain.guess("PUREGYM LTD") == ("Fitness", 1.0)
# ...and its words generalise to similar merchants
brain.learn("THE GYM GROUP", "Fitness")
assert brain.guess("GYM BOX SOHO")[0] == "Fitness"

# learning survives a restart
brain.save()
assert Brain(brain.path).guess("PUREGYM LTD") == ("Fitness", 1.0)

# split money-in / money-out columns (e.g. Barclays, Lloyds)
p = os.path.join(d, "s.csv")
with open(p, "w", newline="") as f:
    csv.writer(f).writerows([["Date", "Memo", "Paid out", "Paid in"],
                             ["1/9", "TESCO STORES", "£1,020.50", ""], ["2/9", "WAGES", "", "900"]])
_, _, desc, amounts = read_statement(p)
assert desc == "Memo" and amounts == [-1020.50, 900.0]

out = sort_statement(p, brain, interactive=False)
with open(out) as f:
    assert [r["Category"] for r in csv.DictReader(f)] == ["Groceries", "Income"]
print("ok")

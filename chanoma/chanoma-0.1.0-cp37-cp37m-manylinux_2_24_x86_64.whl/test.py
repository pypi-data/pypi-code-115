from chanoma import Table, Chanoma, NormalizedResult, Item, Correspondence
import chanoma

table = Table(preset=True)
c = Chanoma(table=table)
print(c.normalize("ＡＢＣＤＥ").text)

table = Table(csv="/app/examples/file/table.csv")
c = Chanoma(table=table)
print(c.normalize("ＡＢＣＤＥ").text)

table = Table()
table.add(chanoma.characters_set.Alphabets())
c = Chanoma(table=table)
print(c.normalize("ＡＢＣＤＥ").text)

corr = Correspondence([ Item("Ａ", "A"), Item("Ｂ", "B"), Item("Ｃ", "C"), Item("Ｄ", "D"), Item("Ｅ", "E") ])
print(corr)
table = Table()
table.add(corr)
c = Chanoma(table=table)
print(c.normalize("ＡＢＣＤＥ").text)

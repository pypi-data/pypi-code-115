from aiscpy.design import SelectByCriteria


def test_select_by_criteria():
    s1 = SelectByCriteria('W', 'A', 35, 'min')
    assert s1.query.queryToList == ['W', 'W18X119', 35.1,  19,  0.655,  11.3,  1.06,  1.46,  1.9375,  1.1875,  15.125,  5.5,
                                    119, 5.31,  24.5,  2190,  231,  7.9,  262,  253,  44.9,  2.69,  69.1,  3.13,  17.9,  10.6,  20300,  50.7,  152,  50.6,  131]


    s2 = SelectByCriteria('C', 'x(bar)', 0.6, 'max')
    assert s2.query.toDict() == {'A': 4.41, 'Cw': 31.0, 'H': 0.882, 'Ix': 51.0,  'Iy': 1.91,  'J': 0.208,  'Shape': 'C9X15', 'Sx': 11.3, 'Sy': 1.01, 'T': 7,  'Type': 'C', 'Zx': 13.6, 'Zy': 2.04,  'bf': 2.49,  'd': 9,  'eo': 0.681,  'gage': 1.375,  'ho': 8.59,  'k': 1, 'ro(bar)': 3.69,  'rts': 0.824,  'rx': 3.4,  'ry': 0.659,  'tf': 0.413,  'tw': 0.285,  'wt./ft.': 15.0,  'x(bar)': 0.586, 'xp': 0.245}

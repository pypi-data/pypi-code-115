from aiscpy.core import ascOrDesc, selectTable, strForOrdered, strForSelect, strForWhere

def test_select_table():
    table1 = selectTable('W')
    table2 = selectTable('M')
    table3 = selectTable('S')
    table4 = selectTable('HP')
    table5 = selectTable('C')
    table6 = selectTable('MC')
    
    assert table1 == '`W-M-S-HP_shapes_AISC`'
    assert table2 == '`W-M-S-HP_shapes_AISC`'
    assert table3 == '`W-M-S-HP_shapes_AISC`'
    assert table4 == '`W-M-S-HP_shapes_AISC`'
    assert table5 == '`C-MC_shapes_AISC`'
    assert table6 == '`C-MC_shapes_AISC`'
    
def test_instruction():
    instruction1 = strForSelect(selectTable('W'), all=True)
    testing1 = "SELECT * FROM `W-M-S-HP_shapes_AISC` "
    
    instruction2 = strForSelect(selectTable('C'), name= 'A')
    testing2 = "SELECT `A` FROM `C-MC_shapes_AISC` "
    
    assert instruction1 == testing1
    assert instruction2 == testing2
    
def test_asc_or_desc():
    a1 = ascOrDesc('min')
    a1_test = True
    a2 = ascOrDesc('max')
    a2_test = False
    
    assert a1 == a1_test
    assert a2 == a2_test
    
def test_strForWhere():
    w1 = strForWhere('Sy', 25,'min')
    w1_str = "WHERE `Sy` >= 25 "
    w2 = strForWhere('Sx', 35, 'max')
    w2_str = "WHERE `Sx` <= 35 "
    w3 = strForWhere('A', 55, 'equal')
    w3_str = "WHERE `A` = 55 "
    
    assert w1 == w1_str
    assert w2 == w2_str
    assert w3 == w3_str
    
def test_strForOrdered():
    o1 = strForOrdered('A', ascOrDesc('min'))
    o2 = strForOrdered('Shape', True)
    o3 = strForOrdered('t', ascOrDesc('max'))
    o4 = strForOrdered('Sx', False)
    
    o1_test = "ORDER BY `A` ASC "
    o2_test = "ORDER BY `Shape` ASC "
    o3_test = "ORDER BY `t` DESC "
    o4_test = "ORDER BY `Sx` DESC "
    
    assert o1 == o1_test
    assert o2 == o2_test
    assert o3 == o3_test
    assert o4 == o4_test
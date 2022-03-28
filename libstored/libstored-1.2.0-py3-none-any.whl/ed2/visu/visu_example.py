# Resource object code (Python 3)
# Created by: object code
# Created by: The Resource Compiler for Qt version 6.2.4
# WARNING! All changes made in this file will be lost!

from PySide6 import QtCore

qt_resource_data = b"\
\x00\x00\x08\x8d\
/\
*\x0a * libstored, \
distributed debu\
ggable data stor\
es.\x0a * Copyright\
 (C) 2020-2022  \
Jochem Rutgers\x0a \
*\x0a * This progra\
m is free softwa\
re: you can redi\
stribute it and/\
or modify\x0a * it \
under the terms \
of the GNU Lesse\
r General Public\
 License as publ\
ished by\x0a * the \
Free Software Fo\
undation, either\
 version 3 of th\
e License, or\x0a *\
 (at your option\
) any later vers\
ion.\x0a *\x0a * This \
program is distr\
ibuted in the ho\
pe that it will \
be useful,\x0a * bu\
t WITHOUT ANY WA\
RRANTY; without \
even the implied\
 warranty of\x0a * \
MERCHANTABILITY \
or FITNESS FOR A\
 PARTICULAR PURP\
OSE.  See the\x0a *\
 GNU Lesser Gene\
ral Public Licen\
se for more deta\
ils.\x0a *\x0a * You s\
hould have recei\
ved a copy of th\
e GNU Lesser Gen\
eral Public Lice\
nse\x0a * along wit\
h this program. \
 If not, see <ht\
tps://www.gnu.or\
g/licenses/>.\x0a *\
/\x0a\x0aimport QtQuic\
k 2.12\x0aimport Qt\
Quick.Layouts 1.\
15\x0aimport QtQuic\
k.Window 2.2\x0aimp\
ort QtQuick.Cont\
rols 2.5\x0a\x0aWindow\
 {\x0a\x0a    id: root\
\x0a    visible: tr\
ue\x0a    width: 40\
0\x0a    height: 30\
0\x0a\x0a    readonly \
property int fon\
tSize: 10\x0a\x0a    C\
omponent.onCompl\
eted: {\x0a        \
var text = \x22Visu\
\x22\x0a\x0a        var i\
d = client.ident\
ification()\x0a    \
    if(id && id \
!== \x22?\x22)\x0a       \
 {\x0a            t\
ext += \x22: \x22 + id\
\x0a\x0a            va\
r v = client.ver\
sion()\x0a         \
   if(v && v !==\
 \x22?\x22)\x0a          \
      text += \x22 \
(\x22 + v + \x22)\x22\x0a   \
     }\x0a\x0a        \
root.title = tex\
t\x0a    }\x0a\x0a    Col\
umnLayout {\x0a    \
    anchors.fill\
: parent\x0a       \
 anchors.margins\
: 5\x0a\x0a        Tex\
tField {\x0a       \
     id: req\x0a   \
         Layout.\
preferredHeight:\
 root.fontSize *\
 2\x0a            f\
ont.pixelSize: r\
oot.fontSize\x0a   \
         Layout.\
fillWidth: true\x0a\
            plac\
eholderText: \x22en\
ter command\x22\x0a   \
         backgro\
und.antialiasing\
: true\x0a         \
   topPadding: 0\
\x0a            bot\
tomPadding: 0\x0a\x0a \
           onAcc\
epted: {\x0a       \
         rep.tex\
t = client.req(t\
ext)\x0a           \
 }\x0a        }\x0a\x0a  \
      ScrollView\
 {\x0a            L\
ayout.fillWidth:\
 true\x0a          \
  Layout.fillHei\
ght: true\x0a      \
      clip: true\
\x0a\x0a            Te\
xtArea {\x0a       \
         id: rep\
\x0a               \
 readOnly: true\x0a\
                \
font.pixelSize: \
root.fontSize\x0a  \
          }\x0a\x0a   \
         backgro\
und: Rectangle {\
\x0a               \
 antialiasing: t\
rue\x0a            \
    border.color\
: \x22#c0c0c0\x22\x0a    \
        }\x0a      \
  }\x0a    }\x0a}\x0a\
\x00\x00\x00p\
m\
odule Libstored.\
Components\x0aInput\
 1.0 Input.qml\x0aM\
easurement 1.0 M\
easurement.qml\x0aS\
toreObject 1.0 S\
toreObject.qml\x0a\
\x00\x00\x08\x84\
/\
*\x0a * libstored, \
distributed debu\
ggable data stor\
es.\x0a * Copyright\
 (C) 2020-2022  \
Jochem Rutgers\x0a \
*\x0a * This progra\
m is free softwa\
re: you can redi\
stribute it and/\
or modify\x0a * it \
under the terms \
of the GNU Lesse\
r General Public\
 License as publ\
ished by\x0a * the \
Free Software Fo\
undation, either\
 version 3 of th\
e License, or\x0a *\
 (at your option\
) any later vers\
ion.\x0a *\x0a * This \
program is distr\
ibuted in the ho\
pe that it will \
be useful,\x0a * bu\
t WITHOUT ANY WA\
RRANTY; without \
even the implied\
 warranty of\x0a * \
MERCHANTABILITY \
or FITNESS FOR A\
 PARTICULAR PURP\
OSE.  See the\x0a *\
 GNU Lesser Gene\
ral Public Licen\
se for more deta\
ils.\x0a *\x0a * You s\
hould have recei\
ved a copy of th\
e GNU Lesser Gen\
eral Public Lice\
nse\x0a * along wit\
h this program. \
 If not, see <ht\
tps://www.gnu.or\
g/licenses/>.\x0a *\
/\x0a\x0aimport QtQuic\
k\x0a\x0aItem {\x0a    id\
: comp\x0a\x0a    requ\
ired property va\
r ref\x0a    proper\
ty var obj: null\
\x0a    property st\
ring name: obj ?\
 obj.name : \x22\x22\x0a \
   property real\
 pollInterval: 2\
\x0a    property bo\
ol autoReadOnIni\
t: true\x0a\x0a    onR\
efChanged: {\x0a   \
     if(typeof(r\
ef) != \x22string\x22)\
 {\x0a            o\
bj = ref\x0a       \
 } else if(typeo\
f(client) == \x22un\
defined\x22) {\x0a    \
        obj = nu\
ll\x0a        } els\
e {\x0a            \
obj = client.obj\
(ref)\x0a        }\x0a\
    }\x0a\x0a    onObj\
Changed: {\x0a     \
   if(obj) {\x0a   \
         value =\
 obj.value\x0a\x0a    \
        if(!obj.\
polling) {\x0a     \
           if(po\
llInterval > 0)\x0a\
                \
    obj.poll(pol\
lInterval)\x0a     \
           else \
if(autoReadOnIni\
t)\x0a             \
       obj.async\
Read()\x0a         \
   } else if(pol\
lInterval > 0 &&\
 obj.pollInterva\
l > pollInterval\
) {\x0a            \
    // Prefer th\
e faster setting\
, if there are m\
ultiple.\x0a       \
         obj.pol\
l(pollInterval)\x0a\
            }\x0a  \
      } else {\x0a \
           value\
 = null\x0a        \
}\x0a    }\x0a\x0a    pro\
perty string val\
ueString: obj ? \
obj.valueString \
: ''\x0a    propert\
y var value: nul\
l\x0a\x0a    property \
bool refreshed: \
false\x0a\x0a    Timer\
 {\x0a        id: u\
pdatedTimer\x0a    \
    interval: 11\
00\x0a        onTri\
ggered: comp.ref\
reshed = false\x0a \
   }\x0a\x0a    onValu\
eStringChanged: \
{\x0a        if(obj\
)\x0a            va\
lue = obj.value\x0a\
\x0a        comp.re\
freshed = true\x0a \
       updatedTi\
mer.restart()\x0a  \
  }\x0a\x0a    functio\
n set(x) {\x0a     \
   if(obj)\x0a     \
       obj.value\
String = x\x0a    }\
\x0a}\x0a\
\x00\x00\x08\x12\
/\
*\x0a * libstored, \
distributed debu\
ggable data stor\
es.\x0a * Copyright\
 (C) 2020-2022  \
Jochem Rutgers\x0a \
*\x0a * This progra\
m is free softwa\
re: you can redi\
stribute it and/\
or modify\x0a * it \
under the terms \
of the GNU Lesse\
r General Public\
 License as publ\
ished by\x0a * the \
Free Software Fo\
undation, either\
 version 3 of th\
e License, or\x0a *\
 (at your option\
) any later vers\
ion.\x0a *\x0a * This \
program is distr\
ibuted in the ho\
pe that it will \
be useful,\x0a * bu\
t WITHOUT ANY WA\
RRANTY; without \
even the implied\
 warranty of\x0a * \
MERCHANTABILITY \
or FITNESS FOR A\
 PARTICULAR PURP\
OSE.  See the\x0a *\
 GNU Lesser Gene\
ral Public Licen\
se for more deta\
ils.\x0a *\x0a * You s\
hould have recei\
ved a copy of th\
e GNU Lesser Gen\
eral Public Lice\
nse\x0a * along wit\
h this program. \
 If not, see <ht\
tps://www.gnu.or\
g/licenses/>.\x0a *\
/\x0a\x0aimport QtQuic\
k.Controls\x0aimpor\
t QtQuick\x0a\x0aTextF\
ield {\x0a    id: c\
omp\x0a\x0a    backgro\
und.antialiasing\
: true\x0a\x0a    topP\
adding: 0\x0a    bo\
ttomPadding: 0\x0a \
   leftPadding: \
0\x0a    horizontal\
Alignment: TextI\
nput.AlignRight\x0a\
    readOnly: tr\
ue\x0a\x0a    property\
 string unit: ''\
\x0a\x0a    property a\
lias ref: o.ref\x0a\
    property ali\
as obj: o.obj\x0a  \
  property alias\
 pollInterval: o\
.pollInterval\x0a  \
  property alias\
 refreshed: o.re\
freshed\x0a    prop\
erty alias value\
: o.value\x0a    pr\
operty bool conn\
ected: o.obj !==\
 null\x0a    proper\
ty alias autoRea\
dOnInit: o.autoR\
eadOnInit\x0a\x0a    p\
roperty var o: S\
toreObject {\x0a   \
     id: o\x0a    }\
\x0a\x0a    // Specify\
 a (lambda) func\
tion, which will\
 be used to conv\
ert the value\x0a  \
  // to a string\
. If null, the v\
alueString of th\
e object is used\
.\x0a    property v\
ar formatter: nu\
ll\x0a\x0a    property\
 string valueFor\
matted: {\x0a      \
  var s;\x0a\x0a      \
  if(!connected)\
\x0a            s =\
 '';\x0a        els\
e if(formatter)\x0a\
            s = \
formatter(o.valu\
e);\x0a        else\
\x0a            s =\
 o.valueString;\x0a\
\x0a        return \
s\x0a    }\x0a\x0a    pro\
perty string _te\
xt: {\x0a        va\
r s = '';\x0a      \
  if(!connected)\
\x0a            s =\
 '?';\x0a        el\
se\x0a            s\
 = valueFormatte\
d;\x0a\x0a        if(u\
nit != '')\x0a     \
       s += ' ' \
+ unit\x0a\x0a        \
return s\x0a    }\x0a \
   text: _text\x0a\x0a\
    color: !conn\
ected ? \x22gray\x22 :\
 refreshed ? \x22bl\
ue\x22 : \x22black\x22\x0a}\x0a\
\x0a\
\x00\x00\x08/\
/\
*\x0a * libstored, \
distributed debu\
ggable data stor\
es.\x0a * Copyright\
 (C) 2020-2022  \
Jochem Rutgers\x0a \
*\x0a * This progra\
m is free softwa\
re: you can redi\
stribute it and/\
or modify\x0a * it \
under the terms \
of the GNU Lesse\
r General Public\
 License as publ\
ished by\x0a * the \
Free Software Fo\
undation, either\
 version 3 of th\
e License, or\x0a *\
 (at your option\
) any later vers\
ion.\x0a *\x0a * This \
program is distr\
ibuted in the ho\
pe that it will \
be useful,\x0a * bu\
t WITHOUT ANY WA\
RRANTY; without \
even the implied\
 warranty of\x0a * \
MERCHANTABILITY \
or FITNESS FOR A\
 PARTICULAR PURP\
OSE.  See the\x0a *\
 GNU Lesser Gene\
ral Public Licen\
se for more deta\
ils.\x0a *\x0a * You s\
hould have recei\
ved a copy of th\
e GNU Lesser Gen\
eral Public Lice\
nse\x0a * along wit\
h this program. \
 If not, see <ht\
tps://www.gnu.or\
g/licenses/>.\x0a *\
/\x0a\x0aimport QtQuic\
k.Controls\x0aimpor\
t QtQuick\x0a\x0aMeasu\
rement {\x0a    rea\
dOnly: false\x0a   \
 pollInterval: 0\
\x0a\x0a    property b\
ool editing: act\
iveFocus && disp\
layText != value\
Formatted\x0a\x0a    p\
roperty bool _ed\
ited: false\x0a    \
onEditingChanged\
 : {\x0a        if(\
!editing) {\x0a    \
        _edited \
= true\x0a         \
   Qt.callLater(\
function() { _ed\
ited: false })\x0a \
       }\x0a    }\x0a\x0a\
    property boo\
l valid: true\x0a  \
  property color\
 validBackground\
Color: \x22white\x22\x0a \
   property colo\
r invalidBackgro\
undColor: \x22#ffe0\
e0\x22\x0a    palette.\
base: valid ? va\
lidBackgroundCol\
or : invalidBack\
groundColor\x0a\x0a   \
 color: editing \
? \x22red\x22 : !conne\
cted ? \x22gray\x22 : \
refreshed && !_e\
dited ? \x22blue\x22 :\
 \x22black\x22\x0a    tex\
t: \x22\x22\x0a\x0a    onAcc\
epted: {\x0a       \
 o.set(displayTe\
xt)\x0a        Qt.c\
allLater(functio\
n() { text = val\
ueFormatted })\x0a \
   }\x0a\x0a    onActi\
veFocusChanged: \
{\x0a        if(act\
iveFocus)\x0a      \
      text = val\
ueFormatted\x0a    \
    else\x0a       \
     text = _tex\
t\x0a    }\x0a\x0a    on_\
TextChanged: {\x0a \
       if(!editi\
ng)\x0a            \
text = _text\x0a   \
 }\x0a\x0a    Keys.for\
wardTo: decimalP\
ointConversion\x0a \
   Item {\x0a      \
  id: decimalPoi\
ntConversion\x0a   \
     Keys.onPres\
sed: (event) => \
{\x0a            if\
(obj !== null &&\
 event.key == Qt\
.Key_Period && (\
event.modifiers \
& Qt.KeypadModif\
ier)) {\x0a        \
        event.ac\
cepted = true\x0a  \
              ob\
j.injectDecimalP\
oint(parent)\x0a   \
         }\x0a     \
   }\x0a    }\x0a}\x0a\x0a\
"

qt_resource_name = b"\
\x00\x08\
\x08\x01Z\x5c\
\x00m\
\x00a\x00i\x00n\x00.\x00q\x00m\x00l\
\x00\x09\
\x09\xab\xcdT\
\x00L\
\x00i\x00b\x00s\x00t\x00o\x00r\x00e\x00d\
\x00\x0a\
\x07n\x093\
\x00C\
\x00o\x00m\x00p\x00o\x00n\x00e\x00n\x00t\x00s\
\x00\x06\
\x07\x84+\x02\
\x00q\
\x00m\x00l\x00d\x00i\x00r\
\x00\x0f\
\x06\xb2\x90\xfc\
\x00S\
\x00t\x00o\x00r\x00e\x00O\x00b\x00j\x00e\x00c\x00t\x00.\x00q\x00m\x00l\
\x00\x0f\
\x0d\x0f\x0a\xbc\
\x00M\
\x00e\x00a\x00s\x00u\x00r\x00e\x00m\x00e\x00n\x00t\x00.\x00q\x00m\x00l\
\x00\x09\
\x07\xc7\xf8\x9c\
\x00I\
\x00n\x00p\x00u\x00t\x00.\x00q\x00m\x00l\
"

qt_resource_struct = b"\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x01\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\
\x00\x00\x01\x7f\xd0\xcc7s\
\x00\x00\x00\x16\x00\x02\x00\x00\x00\x01\x00\x00\x00\x03\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00.\x00\x02\x00\x00\x00\x04\x00\x00\x00\x04\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00Z\x00\x00\x00\x00\x00\x01\x00\x00\x09\x05\
\x00\x00\x01\x7f\xd0\xcc7s\
\x00\x00\x00H\x00\x00\x00\x00\x00\x01\x00\x00\x08\x91\
\x00\x00\x01\x7f\xd0\xcc7s\
\x00\x00\x00\xa2\x00\x00\x00\x00\x00\x01\x00\x00\x19\xa3\
\x00\x00\x01\x7f\xd0\xcc7s\
\x00\x00\x00~\x00\x00\x00\x00\x00\x01\x00\x00\x11\x8d\
\x00\x00\x01\x7f\xd0\xcc7s\
"

def qInitResources():
    QtCore.qRegisterResourceData(0x03, qt_resource_struct, qt_resource_name, qt_resource_data)

def qCleanupResources():
    QtCore.qUnregisterResourceData(0x03, qt_resource_struct, qt_resource_name, qt_resource_data)

qInitResources()

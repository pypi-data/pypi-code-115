import json
import re
def convert(infile,jsonfile):
    fin = open(infile, "r")
    lines = fin.readlines()
    lines = lines[7:]
    with open(jsonfile, 'r') as f:
        json_data = json.load(f)

    preset_list = []

    for i in range(len(lines)):
        # print(i,lines[i])
        jogak = re.findall(r'([-+a-zA-Z0-9."]*)', lines[i])
        # print (jogak)
        for item in jogak:
            while True:
                try:
                    jogak.remove('')
                except ValueError:
                    break

        del jogak[0]
        if (len(jogak) != 1) and (jogak[0] in json_data['keys']):
            preset_list.append(jogak)

    features = []
    values = []

    for i in range(len(preset_list)):
        features.append(preset_list[i][0])
        value = preset_list[i][1]
        value = value[1:-1]
        try:
            if "." not in value:
                value = int(value)
            else:
                value = float(value)
        except ValueError:
            pass
        values.append(value)

    for feat in json_data['keys']:
        if feat not in features:
            features.append(feat)
            values.append(json_data['p_default'][feat])

    dic = dict(zip(features, values))
    js = json.dumps(dic)

    return js
import novauniverse as nova

"""
player = nova.Player("THEGOLDENPRO")

print(player.is_online)
"""

"""
license = nova.License(key=nova.KEYS.TOURNAMENT_DEMO_KEY)

print(license.owner)
"""

server = nova.Server()

for player in server.players:
    print(player.name)

player = nova.Player(player_name="THEGOLDENPRO")
print(player.sessions)
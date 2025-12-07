"""
Mesaj formatları ve protokol tanımları
"""
import json

class MessageType:
    # Discovery
    DISCOVER = "discover"
    ANNOUNCE = "announce"
    
    # Lobby
    INVITE = "invite"
    INVITE_ACCEPT = "invite_accept"
    INVITE_REJECT = "invite_reject"
    
    # Game
    GAME_START = "game_start"
    GAME_COUNTDOWN = "game_countdown"
    PLAYER_MOVE = "player_move"
    GAME_END = "game_end"

def create_message(msg_type, data=None):
    """Mesaj oluştur"""
    return json.dumps({
        "type": msg_type,
        "data": data or {}
    })

def parse_message(msg_str):
    """Mesaj parse et"""
    try:
        msg = json.loads(msg_str)
        return msg.get("type"), msg.get("data", {})
    except:
        return None, None

# Mesaj şablonları
def discover_message():
    return create_message(MessageType.DISCOVER)

def announce_message(player_name, tcp_port):
    return create_message(MessageType.ANNOUNCE, {
        "name": player_name,
        "tcp_port": tcp_port
    })

def invite_message(from_name, from_ip, map_id, from_tcp_port=37021):
    return create_message(MessageType.INVITE, {
        "from": from_name,
        "from_ip": from_ip,
        "map_id": map_id,
        "from_tcp_port": from_tcp_port
    })

def invite_response_message(accepted, player_name):
    msg_type = MessageType.INVITE_ACCEPT if accepted else MessageType.INVITE_REJECT
    return create_message(msg_type, {"name": player_name})

def game_start_message(map_id, player1_pos, player2_pos):
    return create_message(MessageType.GAME_START, {
        "map_id": map_id,
        "player1_pos": player1_pos,
        "player2_pos": player2_pos
    })

def countdown_message(count):
    return create_message(MessageType.GAME_COUNTDOWN, {"count": count})

def player_move_message(player_id, row, col, move_count):
    return create_message(MessageType.PLAYER_MOVE, {
        "player_id": player_id,
        "row": row,
        "col": col,
        "move_count": move_count
    })

def game_end_message(winner_id, move_count):
    return create_message(MessageType.GAME_END, {
        "winner_id": winner_id,
        "move_count": move_count
    })

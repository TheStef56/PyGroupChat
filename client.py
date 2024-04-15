import _curses as curses
import socket, threading, time, ast, sys

HOSTNAME = "127.0.0.1"
MESSAGE_PORT = 8080
INFO_PORT = 8081
ONLINE_PEOPLE = []
CHAT = []
MAX_CHAT = 1000
CONNECION_CLOSED = False

class KeyCodes:
    if sys.platform == "win32":
        BACK_SPACE       = [8]
        ENTER            = [10]
        ARROW_DOWN       = [456, 258]
        ARROW_UP         = [450, 259]
        ARROW_LEFT       = [452, 260]
        ARROW_RIGHT      = [454, 261]
        ALT_ARROW_UP     = [490]
        ALT_ARROW_DOWN   = [491]
        ALT_ARROW_LEFT   = [493]
        ALT_ARROW_RIGHT  = [492]
        CTRL_ARROW_LEFT  = [511]
        CTRL_ARROW_RIGHT = [513]
        CTRL_BACKSPACE   = [23, 127]
        TAB              = [9]
        A_ACCENT         = [530]
    elif sys.platform == "linux":
        BACK_SPACE       = [263]
        ENTER            = [10]
        ARROW_DOWN       = [258]
        ARROW_UP         = [259]
        ARROW_LEFT       = [260]
        ARROW_RIGHT      = [261]
        ALT_ARROW_UP     = [565]
        ALT_ARROW_DOWN   = [524]
        ALT_ARROW_LEFT   = [544]
        ALT_ARROW_RIGHT  = [559]
        CTRL_ARROW_LEFT  = [546]
        CTRL_ARROW_RIGHT = [561]
        CTRL_BACKSPACE   = [8]
        TAB              = [9]

def try_exec(f) -> callable:
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except:
            pass
    return wrapper

def win_border_padded (main_win :curses.window, border_height,
                                                border_width,
                                                border_sy,
                                                border_sx,
                                                padding_x,
                                                padding_y,
                                                internal_border=False, external_border=True) -> curses.window:
    
    window_border = main_win.subpad(border_height, border_width, border_sy, border_sx)
    window_border.clear()
    if external_border:
        window_border.border()
    window_border.refresh()

    win = main_win.subpad(border_height - 2*padding_y, border_width - 2*padding_x, border_sy + padding_y, border_sx + padding_x)
    win.clear()
    if internal_border:
        win.border()
    return win

def process_input(ch, max_pad_off, input_chars, cursor_pos_offset, chat_focus, m_soc, onl_w_c_off, main_w_c_off, w_pad_off) -> tuple[list, int, bool, int, int]:
    if ch in KeyCodes.A_ACCENT:
        ch = ord('à')

    if ch in KeyCodes.BACK_SPACE and input_chars:
            input_chars.pop(-(cursor_pos_offset + 1))
    
    elif ch in KeyCodes.ENTER:
        m_soc.sendall("".join(input_chars).encode())
        input_chars = []
    
    elif ch in KeyCodes.CTRL_BACKSPACE:
        while len(input_chars) - cursor_pos_offset > 0:
            if input_chars[-(cursor_pos_offset + 1)] != ' ':
                input_chars.pop(-(cursor_pos_offset + 1))
            else:
                input_chars.pop(-(cursor_pos_offset + 1))
                break
    
    elif ch in KeyCodes.ARROW_DOWN:
        if not chat_focus:
            onl_w_c_off = onl_w_c_off - 1 if onl_w_c_off > 0 else 0 
        else:
            main_w_c_off = main_w_c_off - 1 if main_w_c_off > 0 else 0 
    
    elif ch in KeyCodes.ARROW_UP:
        if not chat_focus:
            onl_w_c_off += 1
        else:
            main_w_c_off += 1
    
    elif ch in KeyCodes.ARROW_LEFT:
        if  cursor_pos_offset < len(input_chars):
            cursor_pos_offset += 1
    
    elif ch in KeyCodes.ARROW_RIGHT:
        if cursor_pos_offset > 0:
            cursor_pos_offset-=1
    
    elif ch in KeyCodes.ALT_ARROW_LEFT:
        if chat_focus:
            w_pad_off = w_pad_off - 1 if w_pad_off > 0 else 0
    
    elif ch in KeyCodes.ALT_ARROW_RIGHT:
        w_pad_off = w_pad_off + 1 if w_pad_off < max_pad_off else max_pad_off
    
    elif ch in KeyCodes.ALT_ARROW_UP:
        if not chat_focus:
            onl_w_c_off += 10
        else:
            main_w_c_off += 10
    
    elif ch in KeyCodes.ALT_ARROW_DOWN:
        if not chat_focus:
            onl_w_c_off = onl_w_c_off - 10 if onl_w_c_off - 10 > 0 else 0 
        else:
            main_w_c_off = main_w_c_off - 10 if main_w_c_off - 10 > 0 else 0 
    
    elif ch in KeyCodes.CTRL_ARROW_LEFT:
        while len(input_chars) - cursor_pos_offset > 0:
            if input_chars[-(cursor_pos_offset + 1)] != ' ':
                cursor_pos_offset += 1
            else:
                cursor_pos_offset += 1
                break
    
    elif ch in KeyCodes.CTRL_ARROW_RIGHT:
        while cursor_pos_offset > 0:
            if input_chars[-(cursor_pos_offset)] != ' ':
                cursor_pos_offset -= 1
            else:
                cursor_pos_offset -= 1
                break
    
    elif ch in KeyCodes.TAB:
        chat_focus = not chat_focus
    
    elif ch != 0 and ch != curses.KEY_RESIZE and ch >= 32 and chat_focus:
        if cursor_pos_offset == 0:
            input_chars.append(chr(ch))
        else:
            input_chars.insert(-cursor_pos_offset, chr(ch))
    else:
        pass
    return input_chars, cursor_pos_offset, chat_focus, onl_w_c_off, main_w_c_off, w_pad_off

def unblock_win(win) -> None:
    win.timeout(1)
    time.sleep(0.1)
    win.timeout(-1)

def message_thread(s, main_win: curses.window) -> None:
    global CHAT, MAX_CHAT, CONNECION_CLOSED
    while True:
        try:
            msg = s.recv(8256).decode()
            if msg == "":
                s.close()
                CONNECION_CLOSED = True
                unblock_win(main_win)
                break
            CHAT.append(msg)
            main_win.timeout(1)
            time.sleep(0.1)
            main_win.timeout(-1)
            if len(CHAT) > MAX_CHAT:
                MAX_CHAT = MAX_CHAT[MAX_CHAT//5:]
        except ConnectionError:
            s.close()
            CONNECION_CLOSED = True
            main_win.timeout(1)
            time.sleep(0.1)
            main_win.timeout(-1)
            break
        except:
            s.close()
            break

def info_thread(s, main_win: curses.window) -> None:
    global ONLINE_PEOPLE, CHAT, CONNECION_CLOSED
    buffer_str = ""
    s.sendall(b"\x01")
    while True:
        try:
            msg = s.recv(8192)
            if msg[-1] == 1:
                buffer_str += msg[:-1].decode()
                break
            elif msg == b' ':
                break
            elif msg == b'':
                s.close()
                CONNECION_CLOSED = True
                unblock_win(main_win)
                break
            else:
                buffer_str += msg.decode()
        except ConnectionError:
            CONNECION_CLOSED = True
            main_win.timeout(1)
            time.sleep(0.1)
            main_win.timeout(-1)
            s.close()
            break
    if buffer_str:
        messages = ast.literal_eval(buffer_str)
        for x in messages:
            CHAT.append(x)
        buffer_str = ""
    while True:
        try:
            s.sendall(b'\x00')
            msg = s.recv(8192)
            if msg[-1] == 0:
                msg = msg[:-1]
                buffer_str += msg.decode()
            elif msg == b'':
                CONNECION_CLOSED = True
                unblock_win(main_win)
                break
            elif msg == b' ':
                time.sleep(3)
                continue
            else:
                buffer_str += msg.decode()
                continue
            ONLINE_PEOPLE = ast.literal_eval(buffer_str)
            main_win.timeout(1)
            time.sleep(0.1)
            main_win.timeout(-1)
            buffer_str = ""
            time.sleep(3)
        except ConnectionError:
            CONNECION_CLOSED = True
            main_win.timeout(1)
            time.sleep(0.1)
            main_win.timeout(-1)
            s.close()
            break
        except:
            s.close()
            break

def show_online_clients(container_onl_win, online_win, online_border_width, max_y, onl_w_c_off) -> None:
    global ONLINE_PEOPLE
    online_peole_tostr = f"online: {len(ONLINE_PEOPLE)}"
    try_exec(container_onl_win.addstr)(0, online_border_width // 2 - len(online_peole_tostr)//2 - 2, online_peole_tostr)
    container_onl_win.refresh()
    online_peole = len(ONLINE_PEOPLE)
    if online_peole == 0:
        try_exec(online_win.addstr)((max_y -10) // 2 - 2,(online_border_width - 13)//2,"online\n")
        try_exec(online_win.addstr)((max_y -10) // 2 - 1,(online_border_width - 13)//2,"people\n")
        try_exec(online_win.addstr)((max_y -10) // 2 + 0,(online_border_width - 14)//2,"will be\n")
        try_exec(online_win.addstr)((max_y -10) // 2 + 1,(online_border_width - 13)//2,"shown\n")
        try_exec(online_win.addstr)((max_y -10) // 2 + 2,(online_border_width - 11)//2,"here")
    else:
        offset = 0 if len(ONLINE_PEOPLE) < max_y - 8 else len(ONLINE_PEOPLE) - (max_y - 9)
        if offset > 0 and onl_w_c_off > 0:
            if onl_w_c_off > offset:
                onl_w_c_off = offset
            offset -= onl_w_c_off
            if onl_w_c_off < 1:
                offset = 0

        for ind, x in enumerate(ONLINE_PEOPLE[offset: offset + max_y - 9]):
            p_ind = f"{ind + offset}: "
            final_str = p_ind + x
            if len(final_str) >= online_border_width - 7:
                final_str = final_str[:-(len(final_str) - (online_border_width - 10) + 1)]
                final_str += "..."
            final_str += '\n' 
            try_exec(online_win.addstr)(final_str)
    online_win.refresh()
    return onl_w_c_off

def show_messages(chat_win: curses.window, client_name, main_w_c_off) -> int:
    global CHAT
    text_rows = []

    max_chat_y, max_chat_x = chat_win.getmaxyx()
    max_chat_y -= 1
    max_chat_x -= 1
    wrapping_x = max_chat_x//2
    tmp = CHAT.copy()
    tmp.reverse()
    is_my_message = "\00"
    for message in tmp:
        message = ast.literal_eval(message)
        if message[1] == client_name:
            is_my_message = "\00"
        else:
            is_my_message = ""
        message_text = message[2]
        text_rows.append(" ")
        if len(message_text) < wrapping_x:
            text_rows.append(is_my_message + message_text)
        else:
            chunked_message = [message_text[i:i+wrapping_x] for i in range(0, len(message_text), wrapping_x)]
            chunked_message.reverse()

            for line in chunked_message:
                text_rows.append(is_my_message + line)

        offset = 0
        header_len = len(f"{message[0]} {message[1]}")
        if  header_len > max_chat_x:
            offset =  header_len - max_chat_x

        if is_my_message == "":
            if offset != 0:
                text_rows.append(f"{is_my_message + message[0]} {message[1]}"[:-(offset + 3)]+"...")
            else:
                text_rows.append(f"{is_my_message + message[0]} {message[1]}")
        else:
            if offset != 0:
                text_rows.append(f"{is_my_message + message[1]} {message[0]}"[:-(offset + 3)]+"...")
            else:
                text_rows.append(f"{is_my_message + message[1]} {message[0]}")
        
    text_rows.reverse()
    off = 0
    if len(text_rows) > max_chat_y:
        off = len(text_rows) - max_chat_y
    if main_w_c_off and len(text_rows) > max_chat_y:
        if off - main_w_c_off <= 0:
            main_w_c_off = off
        text_rows = text_rows[off - main_w_c_off:-main_w_c_off]
    else:
        text_rows = text_rows[off:]

    for line in text_rows:
        if line.startswith("\00"):
            line = line[1:]
            if len(line) < max_chat_x:
                curs_y, _ = chat_win.getyx()
                try_exec(chat_win.addstr)(curs_y, max_chat_x - 1 - len(line), line + "\n")
            else:
                try_exec(chat_win.addstr)(line + "\n")
        else:
            try_exec(chat_win.addstr)(line + "\n")
    chat_win.refresh()
    return main_w_c_off

def draw_win(main_win, max_y, max_x, chat_border_width, online_border_width, chat_focus) -> tuple[curses.window,
                                                                                                  curses.window,
                                                                                                  curses.window,
                                                                                                  curses.window,
                                                                                                  curses.window]: 
    container_chat_win = win_border_padded(main_win        = main_win,
                                           border_height   = max_y - 1,
                                           border_width    = chat_border_width - 1,
                                           border_sy       = 1,
                                           border_sx       = max_x - chat_border_width,
                                           padding_x       = 1,
                                           padding_y       = 1,
                                           internal_border = False,
                                           external_border = chat_focus)
                                                
    container_onl_win  = win_border_padded(main_win        = main_win,
                                           border_height   = max_y - 4,
                                           border_width    = online_border_width - 1,
                                           border_sy       = 1,
                                           border_sx       = 1,
                                           padding_x       = 1,
                                           padding_y       = 1,
                                           internal_border = False,
                                           external_border = not chat_focus)

    chat_win           = win_border_padded(main_win        = main_win,
                                           border_height   = max_y - 7,
                                           border_width    = chat_border_width - 3,
                                           border_sy       = 3,
                                           border_sx       = max_x - chat_border_width + 1,
                                           padding_x       = 1,
                                           padding_y       = 1,
                                           internal_border = False,
                                           external_border = True)
        
    text_win           = win_border_padded(main_win        = main_win,
                                           border_height   = 3,
                                           border_width    = chat_border_width - 3,
                                           border_sy       = max_y - 4,
                                           border_sx       = max_x - chat_border_width + 1,
                                           padding_x       = 1,
                                           padding_y       = 1,
                                           internal_border = False,
                                           external_border = True)

    online_win         = win_border_padded(main_win        = main_win,
                                           border_height   = max_y - 7,
                                           border_width    = online_border_width - 5,
                                           border_sy       = 3,
                                           border_sx       = 3,
                                           padding_x       = 1,
                                           padding_y       = 1,
                                           internal_border = False,
                                           external_border = True)
    
    return container_chat_win, container_onl_win, chat_win, text_win, online_win

def init_socekts(name, main_win) -> tuple[socket.socket, socket.socket]:
    global HOSTNAME, MESSAGE_PORT, INFO_PORT
    m_s = socket.socket()
    i_s = socket.socket()
    m_s.connect((HOSTNAME, MESSAGE_PORT))
    i_s.connect((HOSTNAME, INFO_PORT))
    m_s.sendall(name.encode())
    threading.Thread(target=info_thread, args=[i_s, main_win]).start()
    threading.Thread(target=message_thread, args=[m_s, main_win]).start() 
    return m_s, i_s

def init_curses() -> curses.window:
    main_win = curses.initscr()
    curses.noecho()
    curses.cbreak()
    main_win.keypad(1)
    return main_win

def uninit_curses(main_win: curses.window) -> None:
    main_win.keypad(0)
    curses.echo()
    curses.nocbreak()
    curses.endwin()

def main() -> None:
    global CONNECION_CLOSED, ONLINE_PEOPLE
    
    try:
        name = input("ENTER YOUR NAME: ")
    except KeyboardInterrupt:
        exit()

    main_win = init_curses()

    input_chars = []
    cursor_pos_offset = 0
    chat_focus = True
    online_win_cursor_offset = 0
    main_win_cursor_offset = 0
    windows_padding_offset = 0

    try:
        m_s, i_s = init_socekts(name, main_win)
        client_name = f"{name} ({m_s.getsockname()[1]})"

        while True:
            max_y, max_x = main_win.getmaxyx()

            max_pad_off = max_x // 5 * 4 - 10
            chat_border_width = max_x // 5 * 4 - windows_padding_offset
            online_border_width = max_x // 5 + windows_padding_offset

            main_win.clear()
            main_win.refresh()

            (container_chat_win,
            container_onl_win,
            chat_win,
            text_win,
            online_win) = draw_win(main_win,
                                   max_y,
                                   max_x,
                                   chat_border_width,
                                   online_border_width,
                                   chat_focus)
            
            
            text_win.refresh()
            chat_win.refresh()
            online_win.refresh()

            try_exec(container_chat_win.addstr)(0, chat_border_width//2 - 5, "PyChat 1.1")
            container_chat_win.refresh()
            

            online_win_cursor_offset = show_online_clients(container_onl_win,
                                                           online_win,
                                                           online_border_width,
                                                           max_y,
                                                           online_win_cursor_offset)
            
            main_win_cursor_offset = show_messages(chat_win,
                                                   client_name,
                                                   main_win_cursor_offset)

            if len(input_chars) >= chat_border_width - 6:
                text_win.addstr("".join(input_chars)[len(input_chars) - chat_border_width + 6:])
            else:
                text_win.addstr("".join(input_chars))

            text_win.refresh()
            main_y, main_x = text_win.getparyx() 
            off_y, off_x = text_win.getyx()
            if chat_focus:
                curses.curs_set(1)
                main_win.move(main_y + off_y, main_x + off_x - cursor_pos_offset)
            else:
                curses.curs_set(0)

            ch = try_exec(main_win.get_wch)()
            if ch == None:
                ch = 0
            elif type(ch) == str:
                ch = ord(ch)

            if CONNECION_CLOSED:
                raise Exception("Connection closed by the server")

            (input_chars,
            cursor_pos_offset,
            chat_focus,
            online_win_cursor_offset,
            main_win_cursor_offset,
            windows_padding_offset) = process_input(ch,
                                                    max_pad_off,
                                                    input_chars,
                                                    cursor_pos_offset,
                                                    chat_focus,
                                                    m_s,
                                                    online_win_cursor_offset,
                                                    main_win_cursor_offset,
                                                    windows_padding_offset)
                
    except KeyboardInterrupt:
        uninit_curses(main_win)
        try_exec(i_s.close)()
        try_exec(m_s.close)()
        exit()
    except curses.error as e:
        uninit_curses(main_win)
        print(e)
        try_exec(i_s.close)()
        try_exec(m_s.close)()
        exit()
    except ConnectionRefusedError:
        uninit_curses(main_win)
        print("Unable to connect to server, retry:")
        main()
    except Exception as e:
        uninit_curses(main_win)
        try_exec(i_s.close)()
        try_exec(m_s.close)()
        print(e)
        if CONNECION_CLOSED:
            CONNECION_CLOSED = False
            main()
        exit()

if __name__ == "__main__":
    main()

#TODO: create a table for specific key-codes depending on platform 
#TODO: find a way to avoid a client crash on excessive resize
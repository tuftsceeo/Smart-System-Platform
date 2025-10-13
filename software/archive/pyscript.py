from pyscript import document, when, window
import upython_board
import json, asyncio, time
from js import setTimeout, setInterval, clearInterval, console
import js

# ---------------------------------- GLOBALS ----------------------------------
list_files = document.getElementById('list_files')
python = document.getElementById('mpCode')
connect = document.getElementById('connect')
uboard = upython_board.uRepl()

read_code = """
f = open('%s', "rb")
result = f.read().decode('utf-8')
f.close()
result
"""

module_dict = {}
wpeers_buffer = ''
wpeers_buffer_count = 0
wpeers_buffer_time = 0
device_ms = 0
timeticks_ms_offset = 0
auto_refresh = True
gui_init = False
admin_mac = ""
admin_apmac = ""


# -------------------------------- BUTTONS ------------------------------------
@when("click", "#connect")
async def on_connect(event):
    if uboard.connected:
        await uboard.board.disconnect()
        await on_disconnect()
    else:
        stop = document.getElementById('freshStart').checked
        await uboard.board.connect('repl', stop)
        for _ in range(100):
            if uboard.connected:
                break
            await asyncio.sleep(0.1)
        if uboard.connected:
            connect.innerText = 'disconnect'
            buttons = document.querySelectorAll("#btndiv button")
            for btn in buttons:
                btn.disabled = False
                btn.style.opacity = "1"
                btn.style.cursor = "pointer"
            if stop:
                await re_list(None)
            # await on_init(None)
            await refresh(None)


async def on_disconnect():
    connect.innerText = 'reconnect'
    buttons = document.querySelectorAll("#btndiv button")
    for btn in buttons:
        btn.disabled = True
        btn.style.opacity = "0.5"
        btn.style.cursor = "not-allowed"
    list_files.options.length = 0
    document.getElementById('title').value = ''
    uboard.buffer = ''


@when("click", "#download")
async def on_download(event):
    if uboard.connected:
        result = await uboard.eval(read_code % list_files.value, hidden=True)
        python.code = result


@when("click", "#clear")
def on_clear(event):
    if uboard.connected:
        uboard.board.terminal.clear()


@when("click", "#CtrlC")
async def send_ctrl_c(event):
    if uboard.connected:
        await uboard.board.write('\x03')


@when("click", "#CtrlD")
async def send_ctrl_d(event):
    if uboard.connected:
        await uboard.board.write('\x04')


hub = ''


@when("click", "#re_list")
async def re_list(event):
    global hub
    if uboard.connected:
        hub = await uboard.getList(list_files, 'hubname')
        if hub:
            result = await uboard.eval(read_code % hub, hidden=True)
            document.getElementById('title').value = result


@when("click", "#delete")
async def delete_code(event):
    await uboard.paste(f"import os; os.remove({json.dumps(list_files.value)})")
    await uboard.getList(list_files)


@when("click", "#run")
async def on_run(event):
    if uboard.connected:
        await uboard.paste(python.code)
        uboard.focus()


@when("click", "#run_main")
async def on_run_main(event):
    if uboard.connected:
        await uboard.board.upload('main.py', python.code)
        await uboard.board.reset()
        uboard.focus()


@when("click", "#reset")
async def on_reset(event):
    if uboard.connected:
        await uboard.board.reset()
        uboard.focus()


@when("click", "#upload")
async def on_upload(event):
    if uboard.connected:
        code = python.code
        path = window.prompt('Save filename?', list_files.value)
        if path:
            name = path if '.' in path else path + '.py'
            await uboard.board.upload(name, code)
            await uboard.getList(list_files)
            list_files.value = f'/{name}'
        uboard.focus()


@when('change', "#title")
async def on_title(event):
    global hub
    if uboard.connected:
        name = event.target.value
        if window.confirm(f'Rename device to {name}?'):
            if hub:
                await uboard.board.upload(hub, name)
            else:
                await uboard.board.upload('./hubname', name)
            await re_list(None)


@when("click", "#init")
async def on_init(event):
    with open("am1.py") as f:
        code = f.read()
    await uboard.board.write('\x04')
    await uboard.board.write('\x03')
    await uboard.paste(code)
    uboard.focus()


@when("click", "#reset")
async def on_init(event):
    await uboard.board.write('\x04')
    await uboard.board.write('\x03')
    await uboard.paste("machine.reset()")
    uboard.focus()


@when("click", "#refresh")
async def refresh(event):
    if (auto_refresh or event is not None) and uboard.connected:
        await on_wpeers_init()
        if event is None:
            setTimeout(lambda: refresh(None), 5000)


# -------------------------------- SLIDER -------------------------------------
@when("mousedown", "#resizer")
def on_resize(event):
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'


@when("mousemove", "#REPL")
def movebar(event):
    parent = document.getElementById('REPL')
    if document.body.style.cursor == 'col-resize':
        rect = parent.getBoundingClientRect()
        left = ((event.clientX - rect.left) / rect.width) * 100
        right = 100 - left
        parent.style.gridTemplateColumns = f'{left}% 10px {right}%'


@when("mouseleave", "#REPL")
@when("mouseup", "#REPL")
def stopbar(event):
    document.body.style.cursor = ''
    document.body.style.userSelect = ''


# -------------------------------- NETWORK ------------------------------------
async def on_wpeers_init():
    uboard.newData_callback = on_wpeers
    await uboard.paste('networking.wpeers()')
    uboard.focus()


def on_wpeers(chunk):
    global wpeers_buffer, wpeers_buffer_count, wpeers_buffer_time, timeticks_ms_offset, device_ms
    chunk = wpeers_buffer + chunk
    if wpeers_buffer_count == 0:
        wpeers_buffer_time = time.ticks_ms()

    if 'networking_peers_info_start' in chunk and 'networking_peers_info_end' in chunk:
        uboard.newData_callback = None
        wpeers_buffer = ''
        wpeers_buffer_count = 0
        wpeers_buffer_time = 0

        time_marker = 'Networking Info: time.ticks_ms():'
        if time_marker in chunk:
            device_ms = eval(chunk.split(time_marker)[1].split()[0])
            timeticks_ms_offset = time.ticks_ms() - int(device_ms)

        data = chunk.split('networking_peers_info_start')[1].split('networking_peers_info_end')[0].strip()
        peer_dict = eval(data)
        asyncio.create_task(build_html(peer_dict))
        return

    wpeers_buffer = chunk
    wpeers_buffer_count += 1
    if wpeers_buffer_count > 1000 or time.ticks_ms() - wpeers_buffer_time > 1000:
        uboard.newData_callback = None
        wpeers_buffer = ''
        wpeers_buffer_count = 0
        wpeers_buffer_time = 0


# -------------------------------- GUI ----------------------------------------
def mac_to_bytestr(mac: str) -> str:
    parts = mac.strip().split(":")
    byte_str = "".join(f"\\x{part.lower()}" for part in parts)
    return f"b'{byte_str}'"


def mac_to_bytes(mac):
    return bytes(int(b, 16) for b in mac.split(':'))


def highlight_matrix_row_col(peer_mac: str, highlight: bool):
    matrix = document.getElementById("peer-matrix-container")
    if not matrix: return
    cells = matrix.querySelectorAll("td,th")
    for cell in cells:
        if cell.dataset.get("sender") == peer_mac or cell.dataset.get("recipient") == peer_mac:
            cell.classList.toggle("highlighted", highlight)


peerBoxes = []


def create_peer_box(mac, ap_mac, name, id, configuration, version, ap_channel, sta_channel, rssi, rssi_time, last_ping,
                    ping):
    container = document.getElementById("peer-container")
    box = document.createElement("div")
    if not gui_init:
        global admin_mac, admin_apmac
        admin_mac = mac
        admin_apmac = ap_mac
        box.className = "peer-box admin-peer-box"
        box_content_innerHTML = admin_peer_box_html(mac, ap_mac, name, id, configuration, version, sta_channel,
                                                    ap_channel)
    else:
        box.className = "peer-box"
        box_content_innerHTML = peer_box_html(mac, ap_mac, name, id, configuration, version, sta_channel, ap_channel,
                                              rssi, rssi_time, last_ping, ping)
    box.innerHTML = f"""
        <div class="peer-box-header">
            <div class="peer-box-handle" title="Drag to move"></div>
            <button class="peer-box-config" title="Configure"></button>
        </div>

        <div class="peer-box-content">
            {box_content_innerHTML}
        </div>

        <div class="peer-box-footer">
            <button id="configBtn{id}" title="Set">Set</button>
            <button id="cancelBtn{id}" title="Cancel">Cancel</button>
            <button id="advBtn{id}" title="Advanced">Advanced</button>
        </div>
    """
    box.dataset.mac = mac
    box.id = id

    # call JS drag setup
    window.setupPeerBoxDrag(box)
    peerBoxes.append(box)
    container.appendChild(box)
    position_peer_boxes()
    window.setupPeerBoxHighlighting(id)
    console.log("created box")


@when("click", "#reAlignBtn")
def realign():
    position_peer_boxes()


@when("click", "#matrixBtn")
def toggleMatrix():
    mtrx = document.getElementById("MATRIX")
    mtrxbtn = document.getElementById("matrixBtn")
    if mtrx.style.display == "none" or mtrx.style.display == "":
        mtrx.style.display = "block"
        mtrxbtn.innerText = 'Hide Matrix'
    else:
        mtrx.style.display = "none"
        mtrxbtn.innerText = 'Show Matrix'


def position_peer_boxes():
    import math
    container = document.getElementById("peer-container")
    center_x = container.offsetWidth / 2
    center_y = container.offsetHeight / 2
    radius = min(center_x, center_y) - 40

    n = len(peerBoxes)
    for i, box in enumerate(peerBoxes):
        theta = -math.pi / 2 + (i) * (2 * math.pi / (n))
        x = center_x + radius * math.cos(theta) - box.offsetWidth / 2
        y = center_y + radius * math.sin(theta) - box.offsetHeight / 2
        box.style.left = f"{x}px"
        box.style.top = f"{y}px"
        window.redraw(box.id)


def update_peer_box(mac, ap_mac, name, id, configuration, version, sta_channel, ap_channel, rssi, rssi_time, last_ping,
                    ping):
    box = document.getElementById(id)
    if not box:
        console.warn(f"Element with id '{id}' not found")
        return
    global admin_mac
    if mac == admin_mac:
        box_content_innerHTML = admin_peer_box_html(mac, ap_mac, name, id, configuration, version, sta_channel,
                                                    ap_channel)
    else:
        box_content_innerHTML = peer_box_html(mac, ap_mac, name, id, configuration, version, sta_channel, ap_channel,
                                              rssi, rssi_time, last_ping, ping)
    box.querySelector(".peer-box-content").innerHTML = box_content_innerHTML
    console.log(f"updated box for {mac}")


existing_recs = []
existing_senders = []


def peer_box_html(mac, ap_mac, name, id, configuration, version, sta_channel, ap_channel, rssi, rssi_time, last_ping,
                  ping_value):
    global device_ms, timeticks_ms_offset
    # console.log(f"RSSI: {rssi}, time: {rssi_time}, last ping: {last_ping}, ping value: {ping_value}, offset: {timeticks_ms_offset}, device: {device_ms}")
    if last_ping is None or timeticks_ms_offset == 0:
        ping_text = "NA"
    else:
        # last_relative_ping = (device_ms - last_ping) / 1000
        last_relative_ping = (time.ticks_ms() - (last_ping + timeticks_ms_offset)) / 1000

        ping_ms_text = f"{ping_value}ms"
        ping_s_text = f"{last_relative_ping:.1f}s"

        try:
            if ping_value < 50:
                ping_ms_colour = "green"
            elif ping_value < 100:
                ping_ms_colour = "orange"
            else:
                ping_ms_colour = "red"
        except (ValueError, TypeError):
            ping_ms_text = "NA"
            ping_ms_colour = "black"

        if last_ping > rssi_time:
            ping_ms_text = "NR"
            ping_ms_colour = "red"

        try:
            if last_relative_ping < 5:
                ping_s_colour = "green"
            elif last_relative_ping < 30:
                ping_s_colour = "orange"
            else:
                ping_s_colour = "red"
        except (ValueError, TypeError):
            ping_s_text = "NA"
            ping_s_colour = "black"

        ping_text = f'<span style="color:{ping_ms_colour}">{ping_ms_text}</span> <span style="color:{ping_s_colour}">{ping_s_text}</span> ago'

    if rssi_time is None or timeticks_ms_offset == 0:
        rssi_text = "NA"
    else:
        # last_relative_ping = (device_ms - rssi_time) / 1000
        last_rssi = (time.ticks_ms() - (rssi_time + timeticks_ms_offset)) / 1000

        rssi_value_text = f"{rssi}"
        rssi_s_text = f"{last_rssi:.1f}s"

        try:
            if rssi > -40:
                rssi_value_colour = "green"
            elif rssi > -70:
                rssi_value_colour = "orange"
            else:
                rssi_value_colour = "red"
        except (ValueError, TypeError):
            rssi_value_text = "NA"
            rssi_value_colour = "black"

        try:
            if last_rssi < 5:
                rssi_s_colour = "green"
            elif last_rssi < 30:
                rssi_s_colour = "orange"
            else:
                rssi_s_colour = "red"
        except (ValueError, TypeError):
            rssi_s_text = "NA"
            rssi_s_colour = "black"

        rssi_text = f'<span style="color:{rssi_value_colour}">{rssi_value_text}</span> <span style="color:{rssi_s_colour}">{rssi_s_text}</span> ago'

    return f"""
            <div class='peer-inner peer-name'><strong>{name}</strong></div>
            <div class='peer-inner peer-mac'>{mac}</div>
            <div class='peer-inner peer-config'>Config: {configuration}</div>
            <div class='peer-inner peer-version'>Ver: {version}</div>
            <div class='peer-inner peer-ping'>Ping: {ping_text}</div>
            <div class='peer-inner peer-rssi'>RSSI: {rssi_text}</div>
    """


def admin_peer_box_html(mac, ap_mac, name, id, configuration, version, sta_channel, ap_channel):
    return f"""
            <div class='peer-inner peer-name'><strong>{name}</strong></div>
            <div class='peer-inner peer-mac'>{mac}</div>
            <div class='peer-inner peer-config'>Config: {configuration}</div>
            <div class='peer-inner peer-version'>Ver: {version}</div>
    """


def mac_to_id(mac: str) -> str | None:
    """Return the ID for the given MAC address, or None if not found."""
    return module_dict.get(mac, {}).get("id")


def build_matrix(peers):
    """Create/update peer matrix. FF:FF:FF:FF:FF:FF always last, no checkbox for self cells."""
    container = document.getElementById("peer-matrix-container")
    broadcast = "ff:ff:ff:ff:ff:ff"
    peers_no_broadcast = [p for p in peers if p.lower() != broadcast]
    sorted_peers = peers_no_broadcast + ([broadcast] if broadcast in peers else [])

    # Check if table exists
    table = container.querySelector("table")
    if not table:
        table = document.createElement("table")
        table.setAttribute("style", "border-collapse: collapse; width: max-content;")
        table.id = "peer-matrix"
        container.appendChild(table)
    else:
        table.innerHTML = ""  # reset existing rows

    # --- header row ---
    header = document.createElement("tr");
    topLeftCell = document.createElement("th");
    topLeftCell.innerHTML = "Sender &#8594;<br>Recipients &#8595;";
    topLeftCell.style.border = "1px solid #333";
    topLeftCell.style.padding = "4px";
    header.appendChild(topLeftCell);
    for sender in sorted_peers:
        if sender.lower() == broadcast:
            continue
        th = document.createElement("th")
        th.classList.add("rotate-header")
        th.textContent = sender
        th.dataset.senderMac = sender
        th.dataset.sender = mac_to_id(sender)
        th.setAttribute("style", "border:1px solid #333;padding:4px;text-align:left;")
        th.id = "cell_" + mac_to_id(sender) + "-ff"
        header.appendChild(th)
    table.appendChild(header)
    for sender in sorted_peers:
        if sender.lower() == broadcast:
            continue
        # window.setupMatrixHighlighting("cell_" + mac_to_id(sender) + "-ff")

    # --- rows ---
    for rec in sorted_peers:
        tr = document.createElement("tr")
        th = document.createElement("th")
        th.textContent = rec
        th.dataset.recipientMac = rec
        if rec.lower() == broadcast:
            th.dataset.recipient = "ffffffffffff"
            th.id = "cell_ff-" + "ffffffffffff"
        else:
            th.id = "cell_ff-" + mac_to_id(rec)
            th.dataset.recipient = mac_to_id(rec)
        th.setAttribute("style", "border:1px solid #333;padding:4px;text-align:left;")
        tr.appendChild(th)

        for sender in sorted_peers:
            if sender.lower() == broadcast:
                continue
            td = document.createElement("td")
            td.dataset.sender = sender
            td.dataset.recipient = rec
            td.setAttribute("style", "border:1px solid #333;padding:4px;text-align:left;")
            td.id = f"cell_{mac_to_id(sender)}-{mac_to_id(rec)}"

            # skip checkbox if sender == recipient
            if sender != rec:
                checkbox = document.createElement("input")
                checkbox.type = "checkbox"
                checkbox.className = "input"
                checkbox.id = f"{mac_to_id(sender)}-{mac_to_id(rec)}"
                checkbox.dataset.sender = mac_to_id(sender)
                checkbox.dataset.recipient = mac_to_id(rec)
                checkbox.dataset.senderMac = sender
                checkbox.dataset.recipientMac = rec
                td.appendChild(checkbox)
                # attach handlers
                if rec.lower() == broadcast:
                    checkbox.addEventListener("change", on_broadcast_checkbox)
                else:
                    checkbox.addEventListener("change", on_peer_checkbox)
            tr.appendChild(td)
        table.appendChild(tr)

        # window.setupMatrixHighlighting("cell_ff-" + mac_to_id(rec))
        for sender in sorted_peers:
            if sender.lower() == broadcast:
                continue
            # window.setupMatrixHighlighting(f"cell_{mac_to_id(sender)}-{mac_to_id(rec)}")

    console.log("matrix built/updated")


def on_peer_checkbox(event):
    global admin_mac, admin_apmac
    checkbox = event.target
    sender = checkbox.dataset.sender
    recipient = checkbox.dataset.recipient
    senderMac = checkbox.dataset.senderMac
    recipientMac = checkbox.dataset.recipientMac
    console.log(f"Peer checkbox changed: {sender} -> {recipient}, checked={checkbox.checked}")
    window.drawLine(sender, recipient, checkbox.checked)
    # send config command
    rec_list = []
    for mac, info in module_dict.items():
        rec = mac
        if rec.lower() == "ffffffffffff" or rec == senderMac:
            continue
        cb = document.getElementById(f"{sender}-{mac_to_id(rec)}")
        if cb.checked:
            rec_list.append(mac_to_bytes(mac))
    config = {'recipients': rec_list}
    # console.log(config)

    if senderMac == admin_mac or senderMac == admin_apmac:
        asyncio.create_task(admin_hive_configure(senderMac, config))
    else:
        asyncio.create_task(hive_configure(mac_to_bytes(senderMac), config))


def on_broadcast_checkbox(event):
    checkbox = event.target
    sender = checkbox.dataset.sender
    recipient = checkbox.dataset.recipient
    senderMac = checkbox.dataset.senderMac
    recipientMac = checkbox.dataset.recipientMac
    checked = checkbox.checked
    console.log(f"Broadcast checkbox changed: {sender} -> {recipient}, checked={checked}")

    table = document.getElementById("peer-matrix")

    for mac, info in module_dict.items():
        rec = mac
        if rec.lower() == "ffffffffffff" or rec == senderMac:
            continue
        cb = document.getElementById(f"{sender}-{mac_to_id(rec)}")
        if cb:
            cb.checked = checkbox.checked
            cb.disabled = checkbox.checked
            window.drawLine(sender, mac_to_id(rec), checkbox.checked)

    # Send config command
    if checked:
        config = {'recipients': [mac_to_bytes(recipientMac)]}
    else:
        config = {'recipients': []}
    # console.log(config)

    if senderMac == admin_mac or senderMac == admin_apmac:
        asyncio.create_task(admin_hive_configure(senderMac, config))
    else:
        asyncio.create_task(hive_configure(mac_to_bytes(senderMac), config))


async def on_command(code):
    console.log(f'Command "{code}" sent')
    await uboard.paste(code)
    # TODO: add callback to await success/fail message


async def hive_configure(sen, hive_config):
    # hive_config example:
    # {'hive': True, 'recipients': [b'd\xe83\x84\xd8\x18'], 'sender_sensor_list': [[b'd\xe83\x84\xd8\x18', 'None']], 'refreshrate': 200, 'mode': 'None'}
    code = f"networking.hive_configure({sen}, {hive_config}, channel=None, ifidx=None, sudo=True)"
    await on_command(code)


async def admin_hive_configure(rec, hive_config):
    # hive_config example:
    # {'hive': True, 'recipients': [b'd\xe83\x84\xd8\x18'], 'sender_sensor_list': [[b'd\xe83\x84\xd8\x18', 'None']], 'refreshrate': 200, 'mode': 'None'}
    code = f"""
try:
    from config import hive_config
    hive_config.update({hive_config})
    file_path = "config.py"
    with open(file_path, "r") as f:
        lines = f.readlines()
    with open(file_path, "w") as f:
        for line in lines:
            if line.startswith('hive_config = '):
                f.write(f'hive_config = {{hive_config}}\\n')
            else:
                f.write(line)
    print("Success!")
    machine.reset()
except Exception as e:
    print(f"Error: {{e}}")
"""
    await on_command(code)


@when("mouseenter", ".peer-box")
def on_peer_hover_enter(event):
    highlight_matrix_row_col(event.target.dataset.mac, True)


@when("mouseleave", ".peer-box")
def on_peer_hover_leave(event):
    highlight_matrix_row_col(event.target.dataset.mac, False)


# -------------------------------- BUILD HTML ---------------------------------
async def build_html(peer_dict):
    global gui_init, module_dict
    if not gui_init:
        result = await uboard.eval(read_code % "config.py", hidden=True)
        cfg = {}
        exec(result, cfg)
        c = cfg["config"]
        mac = c["sta_mac"]
        create_peer_box(mac, c["ap_mac"], c["name"], c["id"], c["configuration"], c["version"], c["sta_channel"],
                        c["ap_channel"], None, None, None, None)
        module_dict[mac] = c
        peers = list(module_dict.keys()) + ["ff:ff:ff:ff:ff:ff"]

        build_matrix(peers)
        gui_init = True

    for key, info in peer_dict.items():
        mac = ":".join(f"{x:02x}" for x in key)
        if mac not in module_dict:
            # console.log("Create box for " + mac)
            create_peer_box(mac, info.get("ap_mac", "?"), info.get("name", "?"),
                            info.get("id", "?"), info.get("configuration", "?"),
                            info.get("version", "?"), info.get("sta_channel", "?"),
                            info.get("ap_channel", "?"),
                            info.get("rssi", "?"), info.get("time", "?"),
                            info.get("last_ping", "?"), info.get("ping", "NA")
                            )
            module_dict[mac] = info
            peers = list(module_dict.keys()) + ["ff:ff:ff:ff:ff:ff"]
            build_matrix(peers)
        else:
            # console.log("Update box for " + mac)
            update_peer_box(mac, info.get("ap_mac", "?"), info.get("name", "?"),
                            info.get("id", "?"), info.get("configuration", "?"),
                            info.get("version", "?"), info.get("sta_channel", "?"),
                            info.get("ap_channel", "?"),
                            info.get("rssi", "?"), info.get("time", "?"),
                            info.get("last_ping", "?"), info.get("ping", "NA")
                            )

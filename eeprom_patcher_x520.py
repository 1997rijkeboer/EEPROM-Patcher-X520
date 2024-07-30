import subprocess
import sys
import os

# Globals

lib = [   
    ['0x32a', 0x12, 0x0a, 0x06, 0x11],
    ['0x32b', 0x72, 0x00, 0x00, 0x7b], 
    ['0x32c', 0xb8, 0x86, 0x86, 0x86], 
    ['0x32d', 0x16, 0x80, 0x80, 0x80], 
    ['0x34a', 0xfb, 0xfb, 0xfb, 0x4d], 
    ['0x34b', 0x10, 0x10, 0x10, 0x15], 
    ['0x356', 0xfb, 0xfb, 0xfb, 0x4d], 
    ['0x357', 0x10, 0x10, 0x10, 0x15]
    ]

interface = ''

# Functions

def format_hex(value):
    return "0x{:02x}".format(value)

def init():
    try:
        with open("/sys/class/net/%s/device/vendor" % interface) as f:
            vendor_id = f.read().strip()

        with open("/sys/class/net/%s/device/device" % interface) as f:
            device_id = f.read().strip()
    except IOError:
        print(f"Can't read interface {interface}")
        sys.exit(1)

    if vendor_id not in ('0x8086') or device_id not in ('0x10fb', '0x154d'):
        print("This card is not recognized as Intel X520.")
        sys.exit(1)

    magic = "%s%s" % (device_id, vendor_id[2:])
    return magic

def read_eeprom(address):
    output = subprocess.check_output(['ethtool', '-e', interface, 'offset', address, 'length', '1']).decode('utf-8')
    val = output.strip().split('\n')[-1].split()[-1]
    return val

def write_eeprom(magic, address, value):
    cmd = ['ethtool', '-E', interface, 'magic', magic, 'offset', address, 'value', hex(value), 'length', 1]
    cmd = ' '.join(map(str, cmd))
    os.system(cmd)

def flash (type, unlock):
    error = 0
    for i in lib:
        output = read_eeprom(i[0])
        if '0x' + output == format_hex(i[type]):
            print(f"read address = {i[0]} is as expected = {format_hex(i[type])}")
        else:
            print(f"read address = {i[0]} is as not expected = 0x{output}")
            error = 1

    if (error == 1):
        print ("Executing a write....")
        for i in lib:
            write_eeprom(magic, i[0], i[type])
            print(f"write address = {i[0]}, write = {hex(i[type])}")

    if (error == 1):
        print ("Checking written values")
        for i in lib:
            output = read_eeprom(i[0])
            if '0x' + output == format_hex(i[type]):
                print(f"read address = {i[0]} is as expected = {format_hex(i[type])}")
            else:
                print(f"read address = {i[0]} is as not expected = {output}")
                error = 1

    if (type == 1):
        val = read_eeprom('0x58')
        val_bin = int(val, 16)
        if val_bin & 0b00000001 == 1:
            print("Card is already unlocked for all SFP modules. Nothing to do.")
        if val_bin & 0b00000001 == 0:
            print("Card is locked to Intel only SFP modules. Patching EEPROM...")
            new_val = val_bin | 0b00000001
            write_eeprom(magic, '0x58', new_val)
            print("New EEPROM Value at 0x58 will be %s (%s)" % (hex(new_val), bin(new_val)))

    print("Finished!...")

def get_interface():
    print("Which interface? (ifconfig)")
    user_input = input("Please enter: ")
    print(f"You entered: {user_input}")
    return(user_input)

def get_type():
    options = ['Sonnet (for Mac OS)', 'SmallTree (for Mac OS)', 'Intel (genuine)',  'Dell (original)']
    print("To which of the below versions do you want to flash the card?")
    for j_idx, j in enumerate(options):
        print(j_idx+1, j)
    user_input = input("Please enter [1-4]: ")
    print(f"You entered: {user_input}")
    return(int(user_input))

def get_unlock():
    print("Do you want to unlock the card for all SPF versions?")
    print ("1 : Yes")
    print ("0 : No")
    user_input = input("Please enter [0-1]: ")
    print(f"You entered: {user_input}")
    return(int(user_input))

# Main

if __name__ == "__main__":
    interface = get_interface()
    magic = init()
    type = get_type()
    unlock = get_unlock()
    flash (type, unlock)


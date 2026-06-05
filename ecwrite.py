import os
import sys
import subprocess
from PySide6.QtWidgets import QMessageBox

# EC_IO_FILE = '/sys/kernel/debug/ec/ec0/io'
EC_IO_FILE = '/dev/ec' if os.system('ls /sys/kernel/debug/ec/ec0/io 2> /dev/null > /dev/null') else '/sys/kernel/debug/ec/ec0/io'


def show_error(title, text):
    QMessageBox.critical(None, title, text)


##------------------------------##
##----Class to read/write EC----##
class ECWrite:
    def __init__(self):
        self.ec_path = EC_IO_FILE
        print("Setting up EC access..." + self.ec_path)
        self.buffer = b''
        self.ec_file = None
        self.setupEC()

    def setupEC(self):
        try:
            self.ec_file = open(self.ec_path, 'rb+')
            return True

        except PermissionError:

            reply = QMessageBox.question(
                None,
                "Privileges Required",
                "Root privileges are required to access the EC.\n\n"
                "Do you want to restart the application with administrator rights?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                try:
                    subprocess.Popen([
                        "kdesu",
                        "-t",
                        f"{sys.executable} {' '.join(sys.argv)}"
                    ])
                except Exception as e:
                    show_error(
                        "Authentication Error",
                        f"Unable to start kdesu:\n\n{e}"
                    )

            return False

        except FileNotFoundError:

            try:
                result = subprocess.run(
                    ["modprobe", "acpi_ec"],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    try:
                        self.ec_file = open(self.ec_path, 'rb+')
                        return True
                    except Exception:
                        pass

            except Exception as e:
                show_error(
                    "Module Load Error",
                    f"Failed to execute modprobe:\n\n{e}"
                )

            show_error(
                "ACPI EC Error",
                "ACPI EC module cannot load!\n\n"
                "Check module or reinstall dkms-acpi_ec package."
            )

            return False

        except Exception as e:

            show_error(
                "EC Error",
                f"Unexpected error:\n\n{e}"
            )

            return False

    def ec_write(self, address, value):

        if self.ec_file is None:
            show_error(
                "EC Error",
                "EC device is not initialized."
            )
            return False

        try:
            self.ec_file.seek(address)
            self.ec_file.write(bytearray([value]))
            return True

        except Exception as e:
            show_error(
                "EC Write Error",
                f"Address: 0x{address:02X}\nValue: {value}\n\n{e}"
            )
            return False

    def ec_refresh(self):

        if self.ec_file is None:
            show_error(
                "EC Error",
                "EC device is not initialized."
            )
            return False

        try:
            self.ec_file.seek(0)
            self.buffer = self.ec_file.read()

            if self.buffer == b'':
                show_error(
                    "EC Error",
                    "EC returned an empty buffer."
                )
                return False

            return True

        except Exception as e:
            show_error(
                "EC Refresh Error",
                str(e)
            )
            return False

    def ec_read(self, address):

        try:

            if self.buffer == b'':
                show_error(
                    "EC Error",
                    "EC buffer is empty.\nCall ec_refresh() first."
                )
                #return 0
                exit(1)

            return self.buffer[address]

        except IndexError:
            show_error(
                "EC Read Error",
                f"Address out of range: 0x{address:02X}"
            )
            return 0

        except Exception as e:
            show_error(
                "EC Read Error",
                str(e)
            )
            return 0

    def shutdownEC(self):

        try:
            if self.ec_file:
                self.ec_file.close()

        except Exception as e:
            show_error(
                "EC Shutdown Error",
                str(e)
            )

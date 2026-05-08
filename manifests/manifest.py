freeze('../internal_filesystem/', 'main.py') # Hardware initialization
freeze('../internal_filesystem/lib', '') # Additional libraries
freeze('../freezeFS/', 'freezefs_mount_builtin.py') # Built-in apps
package("usb", base_path="../lvgl_micropython/lib/micropython/lib/micropython-lib/micropython/usb/usb-device")
package("usb", base_path="../lvgl_micropython/lib/micropython/lib/micropython-lib/micropython/usb/usb-device-midi")

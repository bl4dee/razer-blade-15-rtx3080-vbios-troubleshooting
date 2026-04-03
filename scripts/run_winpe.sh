#\!/bin/bash
qemu-system-x86_64 -enable-kvm -m 2048 -cdrom /home/blink/Downloads/HBCD_PE_x64.iso -boot d -vga std 2>/tmp/qemu_err.log

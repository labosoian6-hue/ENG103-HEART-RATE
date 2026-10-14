cp src/health_monitor/max30102.py src/health_monitor/max30102.py.bak
python3 - <<'EOF'
p = "src/health_monitor/max30102.py"
lines = open(p).read().split("\n")
out = []
i = 0
while i < len(lines):
    line = lines[i]
    if "GPIO.input(self.interrupt)" in line and line.strip().startswith("while"):
        indent = line[:len(line) - len(line.lstrip())]
        j = i + 1
        while j < len(lines) and (lines[j].strip() == "" or len(lines[j]) - len(lines[j].lstrip()) > len(indent)):
            j += 1
        out += [
            indent + "# wait for a new sample by polling the FIFO pointers (no INT pin needed)",
            indent + "while True:",
            indent + "    wr = self.bus.read_i2c_block_data(self.address, 0x04, 1)[0]",
            indent + "    rd = self.bus.read_i2c_block_data(self.address, 0x06, 1)[0]",
            indent + "    if wr != rd:",
            indent + "        break",
            indent + "    sleep(0.01)",
            "",
        ]
        i = j
    else:
        out.append(line)
        i += 1
open(p, "w").write("\n".join(out))
print("patched")
EOF
grep -n "interrupt" src/health_monitor/max30102.py
